from contextlib import closing
from jurialmunkey.futils import FileUtils
from tmdbhelper.lib.addon.tmdate import get_timestring_zulu_now
from tmdbhelper.lib.files.dbdata import Database
from tmdbhelper.lib.sync.datasync import SyncData


class HistoryFileUtils(FileUtils):
    addondata = 'special://profile/addon_data/script.module.tmdbhelper.sync.kodi/'


class HistoryDatabase(Database):
    _basefolder = ''
    _fileutils = HistoryFileUtils()
    columns = (
        'id', 'item_type', 'tmdb_id', 'season_number', 'episode_number',
        'plays', 'last_watched_at', 'position', 'total', 'paused_at',
    )
    database_tables = {
        'history': {
            'id': {'data': 'TEXT PRIMARY KEY'},
            'item_type': {'data': 'TEXT NOT NULL', 'indexed': True},
            'tmdb_id': {'data': 'INTEGER NOT NULL', 'indexed': True},
            'season_number': {'data': 'INTEGER'},
            'episode_number': {'data': 'INTEGER'},
            'plays': {'data': 'INTEGER NOT NULL DEFAULT 0'},
            'last_watched_at': {'data': 'TEXT'},
            'position': {'data': 'REAL NOT NULL DEFAULT 0'},
            'total': {'data': 'REAL NOT NULL DEFAULT 0'},
            'paused_at': {'data': 'TEXT'},
        },
    }

    def __init__(self):
        super().__init__(folder='history', filename='history.db')

    def create_database_execute(self, connection):
        with connection:
            return super().create_database_execute(connection)

    def get_items(self, item_type):
        return self.get_rows('item_type=?', (item_type,))

    def get_rows(self, conditions, values):
        with closing(self.get_database(read_only=True)) as connection:
            return [dict(item) for item in connection.execute(
                f'SELECT {", ".join(self.columns)} FROM history WHERE {conditions}', values)]

    @staticmethod
    def get_identity(tmdb_type, tmdb_id, season=None, episode=None):
        return {
            'id': SyncData.get_name(tmdb_type, tmdb_id, season, episode),
            'item_type': 'movie' if tmdb_type == 'movie' else 'episode',
            'tmdb_id': tmdb_id, 'season_number': season, 'episode_number': episode,
        }

    def get_targets(self, tmdb_type, tmdb_id, season=None, episode=None):
        if tmdb_type == 'movie' or episode is not None:
            identity = self.get_identity(tmdb_type, tmdb_id, season, episode)
            return self.get_rows('id=?', (identity['id'],)) or [identity]
        conditions = 'item_type=? AND tmdb_id=?'
        values = ('episode', tmdb_id)
        if season is not None:
            conditions += ' AND season_number=?'
            values = (*values, season)
        return self.get_rows(conditions, values)

    def insert_history_item(self, connection, item):
        keys = ('id', 'item_type', 'tmdb_id', 'season_number', 'episode_number')
        connection.execute(
            'INSERT INTO history ({}) VALUES ({}) ON CONFLICT(id) DO NOTHING'.format(
                ', '.join(keys), ', '.join('?' for key in keys)), tuple(item[key] for key in keys))

    def set_watched(self, item, remove=False):
        with closing(self.get_database()) as connection, connection:
            self.insert_history_item(connection, item)
            connection.execute(
                'UPDATE history SET plays=CASE WHEN ? THEN 0 ELSE MAX(1, plays) END, '
                'last_watched_at=CASE WHEN ? THEN NULL ELSE COALESCE(last_watched_at, ?) END, '
                'position=0, total=0, paused_at=NULL WHERE id=?',
                (remove, remove, get_timestring_zulu_now(), item['id']))
        return True

    def remove_progress(self, item):
        with closing(self.get_database()) as connection, connection:
            connection.execute('UPDATE history SET position=0, total=0, paused_at=NULL WHERE id=?', (item['id'],))
        return True

    def import_item(self, item, get_values):
        with closing(self.get_database()) as connection, connection:
            # Serialize the merge with playback writes so importing cannot lose a newly recorded play.
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT * FROM history WHERE id=?', (item['id'],)).fetchone()
            current = dict(row) if row is not None else {
                **item, 'plays': 0, 'last_watched_at': None,
                'position': 0, 'total': 0, 'paused_at': None}
            values = get_values(current)
            if not values:
                return False
            self.insert_history_item(connection, item)
            connection.execute(
                'UPDATE history SET {} WHERE id=?'.format(', '.join(f'{key}=?' for key in values)),
                (*values.values(), item['id']))
        return True

    def record_playback(self, item, position, total, completed, starting_plays):
        timestamp = get_timestring_zulu_now()
        with closing(self.get_database()) as connection, connection:
            # Serialize the read/update so concurrent requests cannot lose a recorded play.
            self.insert_history_item(connection, item)
            plays = connection.execute('SELECT plays FROM history WHERE id=?', (item['id'],)).fetchone()['plays']
            updated_plays = max(plays, starting_plays + 1) if completed else plays
            connection.execute(
                'UPDATE history SET plays=?, '
                'last_watched_at=CASE WHEN ? THEN ? ELSE last_watched_at END, '
                'position=?, total=?, paused_at=? WHERE id=?',
                (updated_plays, completed, timestamp, 0 if completed else position, total,
                 None if completed or position <= 0 else timestamp, item['id']))
        return completed and updated_plays > plays

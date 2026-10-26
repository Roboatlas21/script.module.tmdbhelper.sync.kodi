from contextlib import closing
from jurialmunkey.futils import FileUtils
from tmdbhelper.lib.addon.tmdate import get_timestring_zulu_now
from tmdbhelper.lib.files.dbdata import Database
from tmdbhelper.lib.sync.datasync import SyncData
from tmdbhelper_sync_kodi.dates import normalize_zulu_date


class WatchlistFileUtils(FileUtils):
    addondata = 'special://profile/addon_data/script.module.tmdbhelper.sync.kodi/'


class WatchlistDatabase(Database):
    _basefolder = ''
    _fileutils = WatchlistFileUtils()
    columns = ('id', 'tmdb_type', 'tmdb_id', 'season_number', 'episode_number', 'mediatype', 'listed_at')
    database_tables = {
        'watchlist': {
            'id': {'data': 'TEXT PRIMARY KEY'},
            'tmdb_type': {'data': 'TEXT NOT NULL'},
            'tmdb_id': {'data': 'INTEGER NOT NULL'},
            'season_number': {'data': 'INTEGER'},
            'episode_number': {'data': 'INTEGER'},
            'mediatype': {'data': 'TEXT NOT NULL', 'indexed': True},
            'listed_at': {'data': 'TEXT NOT NULL'},
        },
    }

    def __init__(self):
        super().__init__(folder='watchlist', filename='watchlist.db')

    def create_database_execute(self, connection):
        with connection:
            return super().create_database_execute(connection)

    @staticmethod
    def get_mediatype(tmdb_type, season, episode):
        if tmdb_type == 'movie':
            return 'movie'
        if episode is not None:
            return 'episode'
        if season is not None:
            return 'season'
        return 'tvshow'

    def get_items(self, item_type):
        mediatype = 'tvshow' if item_type == 'show' else item_type
        return [dict(item) for item in self.get_list_values(
            table='watchlist', keys=self.columns,
            values=(mediatype,), conditions='mediatype=?')]

    def add(self, tmdb_type, tmdb_id, season=None, episode=None):
        values = (
            SyncData.get_name(tmdb_type, tmdb_id, season, episode),
            tmdb_type, tmdb_id, season, episode,
            self.get_mediatype(tmdb_type, season, episode), get_timestring_zulu_now(),
        )
        with closing(self.get_database()) as connection, connection:
            # Repeated adds preserve the original listing date; remove/add starts a new listing.
            connection.execute(
                'INSERT INTO watchlist ({}) VALUES ({}) ON CONFLICT(id) DO NOTHING'.format(
                    ', '.join(self.columns), ', '.join('?' for key in self.columns)), values)
        return True

    def remove(self, tmdb_type, tmdb_id, season=None, episode=None):
        with closing(self.get_database()) as connection, connection:
            connection.execute('DELETE FROM watchlist WHERE id=?', (
                SyncData.get_name(tmdb_type, tmdb_id, season, episode),))
        return True

    def remove_watched(self, watched):
        values = [(item_id, normalize_zulu_date(watched_at)) for item_id, watched_at in watched.items()]
        with closing(self.get_database()) as connection, connection:
            # Compare again when deleting so a concurrent re-add cannot lose a newer listing.
            cursor = connection.executemany('DELETE FROM watchlist WHERE id=? AND listed_at < ?', values)
            return cursor.rowcount > 0

    def remove_played(self, tmdb_type, tmdb_id, watched_at, season=None, episode=None):
        item_ids = [SyncData.get_name(tmdb_type, tmdb_id)]
        if season is not None:
            item_ids.append(SyncData.get_name(tmdb_type, tmdb_id, season))
        if episode is not None:
            item_ids.append(SyncData.get_name(tmdb_type, tmdb_id, season, episode))
        return self.remove_watched(dict.fromkeys(item_ids, watched_at))

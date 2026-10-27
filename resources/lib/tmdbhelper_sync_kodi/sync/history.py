from collections import defaultdict
from sqlite3 import Error as DatabaseError
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper_sync_kodi.library import KodiLibraryError
from tmdbhelper_sync_kodi.sync.datatype import KodiDataType
from tmdbhelper_sync_kodi.sync.itemdata import KodiSyncItemData
from tmdbhelper_sync_kodi.sync.snapshot import KodiSyncSnapshot


class KodiHistorySnapshot(KodiSyncSnapshot):
    def __init__(self, library, item_type, history):
        super().__init__(library, item_type)
        self.history = history

    @staticmethod
    def get_item_key(item):
        return KodiSyncItemData(item, item['item_type']).item_id

    def get_items(self):
        # Library state wins, including explicit unwatched state and cleared resume.
        library_items = super().get_items()
        history_type = 'movie' if self.item_type == 'movie' else 'episode'
        records = {item['id']: self.get_history_item(item) for item in self.history.get_items(history_type)}
        records.update((self.get_item_key(item), item) for item in library_items)
        if history_type == 'episode':
            self.configure_watched_parents(records)
        return list(records.values())

    def get_history_item(self, item):
        record = {
            'item_type': item['item_type'], 'tmdb_id': item['tmdb_id'],
            'season_number': item['season_number'], 'episode_number': item['episode_number'],
            'plays': item['plays'], 'last_watched_at': item['last_watched_at'],
            'runtime': item['total'] / 60 if item['total'] > 0 else None, 'premiered': None,
        }
        if item['position'] > 0 and item['total'] > 0:
            record.update(
                progress=min(100, item['position'] * 100 / item['total']),
                paused_at=item['paused_at'], id=item['id'],
            )
        return record

    def configure_watched_parents(self, records):
        groups = defaultdict(list)
        for item in list(records.values()):
            if item['item_type'] != 'episode':
                continue
            groups[(item['tmdb_id'], item['season_number'])].append(item)
            regular = groups[(item['tmdb_id'], None)]
            if item['season_number'] > 0:
                regular.append(item)
        for (tmdb_id, season), episodes in groups.items():
            parent = {'item_type': 'show' if season is None else 'season', 'tmdb_id': tmdb_id, 'season_number': season}
            key = self.get_item_key(parent)
            parent = records.setdefault(key, parent)
            self.configure_watched_parent(parent, episodes)

    def configure_watched_parent(self, parent, episodes):
        watched = [item for item in episodes if item['plays'] > 0]
        available = [item for item in episodes if self.is_available_episode(item)]
        parent['plays'] = min((item['plays'] for item in available), default=0)
        parent['watched_episodes'] = 0 if parent.get('season_number') == 0 else len(watched)
        parent['last_watched_at'] = max((item['last_watched_at'] for item in watched), default=None)


class KodiHistoryDataType(KodiDataType):
    def get_response_sync(self, *args, **kwargs):
        try:
            return KodiHistorySnapshot(self.provider.library, self.item_type, self.provider.history).items
        except (KodiLibraryError, DatabaseError) as exc:
            # Neither an incomplete library nor failed history read may clear synced state.
            kodi_log(f'Kodi history sync: {exc}', 1)
            return

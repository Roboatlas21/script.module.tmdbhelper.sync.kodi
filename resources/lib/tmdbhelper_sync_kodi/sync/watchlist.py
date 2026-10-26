from tmdbhelper.lib.sync.datatype import DataType
from tmdbhelper_sync_kodi.sync.datasync import KodiSyncDataGetterWatchlistWatched
from tmdbhelper_sync_kodi.sync.itemdata import KodiSyncItem, KodiSyncItemData


class KodiWatchlistSyncItem(KodiSyncItem):
    _additional_keys = ('item_type', 'tmdb_type', 'tmdb_id', 'season_number', 'episode_number')

    def get_items(self):
        return [KodiSyncItemData(item, 'show' if item['mediatype'] == 'tvshow' else item['mediatype'])
                for item in self.meta]


class SyncWatchlist(DataType):
    keys = ('rank', 'listed_at', 'notes')
    key_prefix = 'watchlist'
    method = 'watchlist'
    last_activities_key = 'watchlisted_at'
    expiry_time = 60

    def get_response_sync(self, *args, **kwargs):
        database = self.provider.watchlist
        items = database.get_items(self.item_type)
        if not items or self.instance_syncdata.get_sync_class('SyncWatched') is None:
            return items
        getter = self.instance_syncdata.get_item_type_getter(KodiSyncDataGetterWatchlistWatched, self.item_type)
        item_ids = {item['id'] for item in items}
        watched = {item['id']: item['last_watched_at'] for item in getter.items if item['id'] in item_ids}
        database.remove_watched(watched)
        return database.get_items(self.item_type)

    def get_syncitem(self, meta):
        return KodiWatchlistSyncItem(self.item_type, meta, self.keys, key_prefix=self.key_prefix)

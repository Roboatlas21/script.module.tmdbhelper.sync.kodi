from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.addon.tmdate import get_datetime_now, get_timedelta, get_timestring_zulu_now
from tmdbhelper.lib.sync.datatype import DataType, DataTypeEpisodesInShows
from tmdbhelper_sync_kodi.library import KodiLibraryError
from tmdbhelper_sync_kodi.sync.activity import KodiLastActivities
from tmdbhelper_sync_kodi.sync.itemdata import KodiSyncItem
from tmdbhelper_sync_kodi.sync.snapshot import KodiSyncSnapshot


class KodiDataType(DataTypeEpisodesInShows, DataType):
    def get_last_activities(self):
        return KodiLastActivities(self.instance_syncdata, self.provider)

    def get_activity_expiry(self):
        now = get_datetime_now()
        boundary = now.replace(hour=now.hour // 6 * 6, minute=0, second=0, microsecond=0)
        boundary += get_timedelta(hours=6)
        # Activity queries include the expiry second, so end at the last second before the boundary.
        return int(boundary.timestamp()) - 1

    def sync_data(self, **kwargs):
        # Changes arriving during the snapshot must remain newer than its stored activity.
        self.sync_timestamp = get_timestring_zulu_now()
        self.sync_expiry = self.get_activity_expiry()
        return super().sync_data(**kwargs)

    def store_last_activity(self):
        self.cache.set_activity(
            self.item_type, self.cache_method, self.sync_timestamp, self.sync_expiry)

    def get_response_sync(self, *args, **kwargs):
        try:
            return KodiSyncSnapshot(self.provider.library, self.item_type).items
        except KodiLibraryError as exc:
            # A failed snapshot must never clear previously synced columns.
            kodi_log(f'Kodi sync: {exc}', 1)
            return

    def get_syncitem(self, meta):
        return KodiSyncItem(self.item_type, meta, self.keys, key_prefix=self.key_prefix)

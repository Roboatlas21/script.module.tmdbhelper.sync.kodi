from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.sync.datatype import DataType, DataTypeEpisodesInShows
from tmdbhelper_sync_kodi.library import KodiLibraryError
from tmdbhelper_sync_kodi.sync.itemdata import KodiSyncItem
from tmdbhelper_sync_kodi.sync.snapshot import KodiSyncSnapshot


class KodiDataType(DataTypeEpisodesInShows, DataType):
    expiry_time = 60

    def get_response_sync(self, *args, **kwargs):
        try:
            return KodiSyncSnapshot(self.provider.library, self.item_type).items
        except KodiLibraryError as exc:
            # A failed snapshot must never clear previously synced columns.
            kodi_log(f'Kodi sync: {exc}', 1)
            return

    def get_syncitem(self, meta):
        return KodiSyncItem(self.item_type, meta, self.keys, key_prefix=self.key_prefix)

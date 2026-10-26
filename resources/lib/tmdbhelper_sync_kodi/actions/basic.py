from tmdbhelper.lib.script.sync.actions import ItemWatched as BasicItemWatched, ItemUnwatched as BasicItemUnwatched
from tmdbhelper_sync_kodi.actions.item import ItemSync
from tmdbhelper_sync_kodi.dates import get_kodi_date_now


class ItemWatched(ItemSync, BasicItemWatched):
    def update_item(self, item):
        return self.library.set_details(
            item, self.media_type,
            playcount=0 if self.remove else max(1, item['playcount']),
            lastplayed='' if self.remove else item['lastplayed'] or get_kodi_date_now(),
            resume={'position': 0, 'total': 0},
        )


class ItemUnwatched(ItemWatched, BasicItemUnwatched):
    pass

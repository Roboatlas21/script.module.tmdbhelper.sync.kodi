from tmdbhelper.lib.script.sync.progress import ItemProgress as BasicItemProgress
from tmdbhelper_sync_kodi.actions.item import ItemSync


class ItemProgress(ItemSync, BasicItemProgress):
    allow_shows = False

    def update_item(self, item):
        return self.library.set_details(item, self.media_type, resume={'position': 0, 'total': 0})

from tmdbhelper.lib.addon.plugin import get_localized
from tmdbhelper.lib.script.sync.actions import ItemWatchlist as BasicItemWatchlist


class ItemWatchlist(BasicItemWatchlist):
    allow_seasons = True
    allow_episodes = True

    def get_sync_value(self):
        return self.syncdata.get_value(
            self.tmdb_type, self.tmdb_id, self.season, self.episode,
            key=self.sync_key, item_type=self.item_type)

    def get_item_id(self):
        return self.syncdata.get_name(self.tmdb_type, self.tmdb_id, self.season, self.episode)

    def get_sync_response(self):
        database = self.sync_provider.watchlist
        action = database.remove if self.remove else database.add
        return action(self.tmdb_type, self.tmdb_id, self.season, self.episode)

    def get_is_successful_sync(self):
        return self.sync_response

    def get_dialog_message(self):
        if self.is_successful_sync and not self.confirm_success:
            return
        message = get_localized(32297 if self.is_successful_sync else 32296)
        return message.format(self.dialog_header, self.item_name, self.tmdb_type, self.item_id)

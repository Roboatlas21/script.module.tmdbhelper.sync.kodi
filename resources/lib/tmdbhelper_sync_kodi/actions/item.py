from sqlite3 import Error as DatabaseError
from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.plugin import get_localized
from tmdbhelper.lib.script.sync.provider import ItemSync as ProviderItemSync
from tmdbhelper_sync_kodi.library import KodiLibraryError


class ItemSync(ProviderItemSync):
    @property
    def library(self):
        return self.sync_provider.library

    @property
    def history(self):
        return self.sync_provider.history

    @property
    def media_type(self):
        return 'movie' if self.tmdb_type == 'movie' else 'episode'

    @cached_property
    def targets(self):
        return self.get_targets()

    def get_targets(self):
        return self.library.get_targets(self.tmdb_type, self.tmdb_id, self.season, self.episode)

    def get_history_targets(self, targets):
        identities = {
            self.history.get_identity(
                self.tmdb_type, self.tmdb_id,
                item['season'] if self.media_type == 'episode' else None,
                item['episode'] if self.media_type == 'episode' else None)['id']
            for item in targets
        }
        return [item for item in self.history.get_targets(self.tmdb_type, self.tmdb_id, self.season, self.episode)
                if item['id'] not in identities]

    def get_self(self):
        if not self.is_allowed_type:
            return
        if not self.targets and not self.get_history_targets(self.targets):
            return
        return super().get_self()

    def get_sync_response(self):
        try:
            # Fetch again at write time to account for library changes since menu creation.
            targets = self.get_targets()
            history_targets = self.get_history_targets(targets)
            results = [self.update_item(item) for item in targets]
            results.extend(self.update_history_item(item) for item in history_targets)
            return bool(results) and all(results)
        except (KodiLibraryError, DatabaseError) as exc:
            self.kodi_log(f'Kodi sync action: {exc}', 1)
            return False

    def update_item(self, item):
        raise NotImplementedError

    def update_history_item(self, item):
        raise NotImplementedError

    def get_is_successful_sync(self):
        return self.sync_response

    def get_dialog_message(self):
        if self.is_successful_sync and not self.confirm_success:
            return
        message = get_localized(32297 if self.is_successful_sync else 32296)
        return message.format(self.dialog_header, self.item_name, self.tmdb_type, self.item_id)

from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.sync.providers.base import SyncProvider
from tmdbhelper_sync_kodi.library import KodiLibraryClient
from tmdbhelper_sync_kodi.sync import synctype, datasync
from tmdbhelper_sync_kodi.actions.basic import ItemWatched, ItemUnwatched
from tmdbhelper_sync_kodi.actions.progress import ItemProgress
from tmdbhelper_sync_kodi.scrobbler import ProviderScrobbler


class Provider(SyncProvider):
    interface_version = 3
    provider_id = 'kodi'
    display_name = 'Kodi'
    sync_classes = {
        'SyncCollection': synctype.SyncCollection,
        'SyncWatched': synctype.SyncWatched,
        'SyncPlayback': synctype.SyncPlayback,
        'SyncAiredEpisodes': synctype.SyncAiredEpisodes,
        'SyncNextEpisodes': synctype.SyncNextEpisodes,
        'SyncAllNextEpisodes': synctype.SyncAllNextEpisodes,
    }
    action_classes = {
        'watched': ItemWatched,
        'unwatched': ItemUnwatched,
        'progress': ItemProgress,
    }
    getter_classes = {
        'movies_to_watch': datasync.KodiSyncDataGetterMoviesToWatch,
        'shows_to_watch': datasync.KodiSyncDataGetterShowsToWatch,
        'shows_in_progress': datasync.KodiSyncDataGetterShowsInProgress,
    }
    scrobbler_class = ProviderScrobbler

    @cached_property
    def library(self):
        return self.get_library()

    def get_library(self):
        return KodiLibraryClient()

    def is_authorized(self):
        return True

    def get_last_activities(self):
        # Kodi has no change feed. Concrete sync classes expire their snapshots.
        return {}

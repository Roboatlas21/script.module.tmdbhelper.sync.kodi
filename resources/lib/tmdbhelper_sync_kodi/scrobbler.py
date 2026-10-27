from sqlite3 import Error as DatabaseError
from jurialmunkey.ftools import cached_property
from jurialmunkey.window import get_property
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.addon.tmdate import get_timestring_zulu_now, set_timestamp
from tmdbhelper.lib.monitor.scrobble import ScrobbleRequest, ScrobbleResult
from tmdbhelper.lib.sync.invalidator import SyncInvalidatorWatchlist
from tmdbhelper_sync_kodi.dates import get_kodi_date_now
from tmdbhelper_sync_kodi.library import KodiLibraryError


class ProviderScrobbler(ScrobbleRequest):
    completed = False
    watchlist_completed = False
    native_playback = False

    @property
    def library(self):
        return self.provider.library

    @property
    def media_type(self):
        return 'movie' if self.player.tmdb_type == 'movie' else 'episode'

    @cached_property
    def target(self):
        return self.get_target()

    def get_target(self):
        player = self.player
        targets = self.library.get_targets(
            player.tmdb_type, player.tmdb_id,
            None if self.media_type == 'movie' else player.season,
            None if self.media_type == 'movie' else player.episode,
        )
        if not targets:
            return
        playing_item = self.library.get_playing_item()
        target = next((item for item in targets if self.library.is_native_playback(item, self.media_type, playing_item)), None)
        self.native_playback = target is not None
        return target if target is not None else next(iter(targets), None)

    @cached_property
    def history_target(self):
        return self.get_history_target()

    def get_history_target(self):
        player = self.player
        return self.provider.history.get_targets(
            player.tmdb_type, player.tmdb_id,
            None if self.media_type == 'movie' else player.season,
            None if self.media_type == 'movie' else player.episode,
        )[0]

    def scrobble(self, method):
        try:
            result = self.get_scrobble_result(method)
        except (KodiLibraryError, DatabaseError) as exc:
            kodi_log(f'Kodi scrobble: {exc}', 1)
            return ScrobbleResult(False, False)
        if result.successful and method == 'stop' and self.player.progress >= 80 and not self.watchlist_completed:
            self.remove_watchlisted()
            self.watchlist_completed = True
        return result

    def remove_watchlisted(self):
        player = self.player
        removed = self.provider.watchlist.remove_played(
            player.tmdb_type, player.tmdb_id, get_timestring_zulu_now(),
            None if self.media_type == 'movie' else player.season,
            None if self.media_type == 'movie' else player.episode,
        )
        selected = player.syncdata.registry.get_selected_provider('watchlist')
        if not removed or selected is None or selected.provider_id != self.provider.provider_id:
            return
        invalidator = SyncInvalidatorWatchlist()
        invalidator.syncdata = player.syncdata
        invalidator.notification = False
        invalidator.run(sync=True)
        get_property('Widgets.Reload', set_property=str(set_timestamp(0, True)))

    def get_scrobble_result(self, method):
        if self.media_type == 'episode' and (self.player.season < 0 or self.player.episode <= 0):
            return ScrobbleResult(False, False)
        # Resolve the starting state before playback changes it.
        target = self.target
        if target is None:
            target = self.history_target
        if method == 'start':
            return ScrobbleResult(True, False)
        if method != 'stop':
            return ScrobbleResult(False, False)
        if self.completed or self.native_playback:
            # Kodi already persists the playcount and resume point for native playback.
            return ScrobbleResult(True, False)
        if self.target is None:
            return self.record_history_playback(target)
        return self.record_playback()

    def record_history_playback(self, target):
        completed = self.player.progress >= 80
        changed = self.provider.history.record_playback(
            target, self.player.current_time, self.player.total_time, completed, target.get('plays', 0),
        )
        self.completed = completed
        return ScrobbleResult(True, changed)

    def record_playback(self):
        completed = self.player.progress >= 80
        current = self.library.get_details(self.target, self.media_type)
        plays = current['playcount']
        if completed:
            # An already-recorded play must not be incremented again.
            plays = max(plays, self.target['playcount'] + 1)
        self.library.set_details(
            self.target, self.media_type, playcount=plays, lastplayed=get_kodi_date_now(),
            resume={'position': 0 if completed else self.player.current_time, 'total': self.player.total_time},
        )
        self.completed = completed
        return ScrobbleResult(True, completed and plays > current['playcount'])

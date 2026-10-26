from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.monitor.scrobble import ScrobbleRequest, ScrobbleResult
from tmdbhelper_sync_kodi.dates import get_kodi_date_now
from tmdbhelper_sync_kodi.library import KodiLibraryError


class ProviderScrobbler(ScrobbleRequest):
    completed = False

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
        if self.media_type == 'episode' and (player.season < 0 or player.episode <= 0):
            return
        targets = self.library.get_targets(
            player.tmdb_type, player.tmdb_id,
            None if self.media_type == 'movie' else player.season,
            None if self.media_type == 'movie' else player.episode,
        )
        playing_item = self.library.get_playing_item()
        target = next((item for item in targets if self.library.is_native_playback(item, self.media_type, playing_item)), None)
        self.native_playback = target is not None
        return target if target is not None else next(iter(targets), None)

    def scrobble(self, method):
        try:
            return self.get_scrobble_result(method)
        except KodiLibraryError as exc:
            kodi_log(f'Kodi scrobble: {exc}', 1)
            return ScrobbleResult(False, False)

    def get_scrobble_result(self, method):
        if self.target is None:
            return ScrobbleResult(False, False)
        if method == 'start':
            return ScrobbleResult(True, False)
        if method != 'stop':
            return ScrobbleResult(False, False)
        if self.completed or self.native_playback:
            # Kodi already persists the playcount and resume point for native playback.
            return ScrobbleResult(True, False)
        return self.record_playback()

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

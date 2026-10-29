from jurialmunkey.ftools import cached_property
from tmdbhelper_sync_kodi.dates import normalize_zulu_date, kodi_date_to_zulu, zulu_date_to_kodi


class ImportedHistoryItem:
    """Merge a source record with current watched/resume state, preserving newer events."""

    unknown_date = '1970-01-01T00:00:00.000000Z'

    def __init__(self, item):
        self.item = item

    @cached_property
    def watched_at(self):
        return self.get_watched_at()

    def get_watched_at(self):
        value = self.item.get('last_watched_at')
        if value:
            return self.get_date(value)
        return self.unknown_date if self.item.get('plays', 0) else None

    def get_date(self, value):
        return normalize_zulu_date(value)

    @cached_property
    def paused_at(self):
        return self.get_paused_at()

    def get_paused_at(self):
        value = self.item.get('playback_paused_at')
        if self.item.get('playback_progress') and value:
            return self.get_date(value)

    def get_values(self, current, total):
        values = {}
        watched_at = current.get('last_watched_at') or ''
        paused_at = current.get('paused_at') or ''
        if self.watched_at and self.watched_at > watched_at:
            values.update(
                plays=max(current.get('plays', 0), self.item.get('plays') or 1),
                last_watched_at=self.watched_at)
            watched_at = self.watched_at
            if self.watched_at >= paused_at:
                values.update(position=0, total=0, paused_at=None)
        if total > 0 and self.paused_at and self.paused_at > max(watched_at, paused_at):
            progress = self.item['playback_progress']
            if not 0 < progress <= 100:
                raise ValueError(f'Invalid imported playback percentage: {progress}')
            values.update(position=total * progress / 100, total=total, paused_at=self.paused_at)
        return values

    def get_history_values(self, current):
        # A percentage needs a denominator even when the source has no runtime.
        total = current.get('total') or (self.item.get('runtime') or 0) * 60 or 100
        return self.get_values(current, total)


class ImportedLibraryItem(ImportedHistoryItem):
    progress_unavailable = False

    def get_date(self, value):
        # Kodi stores only whole seconds: retain idempotence for fractional source dates.
        return f'{normalize_zulu_date(value)[:19]}.000000Z'

    def get_library_values(self, current):
        timestamp = kodi_date_to_zulu(current['lastplayed'])
        state = {
            'plays': current['playcount'],
            'last_watched_at': (timestamp or self.unknown_date) if current['playcount'] else None,
            # Kodi does not expose a separate resume-modified date.
            'paused_at': timestamp,
        }
        total = current['resume']['total'] or current['runtime'] or (self.item.get('runtime') or 0) * 60
        latest = max(state['last_watched_at'] or '', timestamp or '', self.watched_at or '')
        self.progress_unavailable = bool(not total and self.paused_at and self.paused_at > latest)
        values = self.get_values(state, total)
        result = {}
        if 'plays' in values:
            result.update(playcount=values['plays'], lastplayed=zulu_date_to_kodi(values['last_watched_at']))
        if 'position' in values:
            result['resume'] = {'position': values['position'], 'total': values['total']}
            if values['paused_at']:
                result['lastplayed'] = zulu_date_to_kodi(values['paused_at'])
        return result

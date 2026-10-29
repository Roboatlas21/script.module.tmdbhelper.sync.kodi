from collections import defaultdict
from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.sync.invalidator import SyncInvalidatorWatchedProgress, SyncInvalidatorWatchlist
from tmdbhelper_sync_kodi.sync.import_item import ImportedHistoryItem, ImportedLibraryItem


class HistoryImporter:
    def __init__(self, provider):
        self.provider = provider
        self.changed = 0
        self.missing_runtime = 0

    @cached_property
    def library_targets(self):
        return self.get_library_targets()

    def get_library_targets(self):
        library = self.provider.library
        targets = defaultdict(list)
        for item in library.get_items('movie'):
            tmdb_id = library.get_tmdb_id(item, 'movie')
            if tmdb_id:
                targets[('movie', int(tmdb_id), None, None)].append(item)
        shows = {
            item['tvshowid']: library.get_tmdb_id(item, 'tvshow')
            for item in library.get_items('tvshow')}
        for item in library.get_items('episode'):
            tmdb_id = shows.get(item['tvshowid'])
            if tmdb_id:
                targets[('episode', int(tmdb_id), item['season'], item['episode'])].append(item)
        return targets

    def import_item(self, item):
        item_type = item['item_type']
        tmdb_id = int(item['tmdb_id'])
        season = item['season_number'] if item_type == 'episode' else None
        episode = item['episode_number'] if item_type == 'episode' else None
        if tmdb_id <= 0 or (item_type == 'episode' and (season < 0 or episode <= 0)):
            raise ValueError(f'Invalid imported identity: {item}')
        targets = self.library_targets.get((item_type, tmdb_id, season, episode))
        if targets:
            return self.import_library_items(targets, item_type, ImportedLibraryItem(item))
        identity = self.provider.history.get_identity(
            'movie' if item_type == 'movie' else 'tv', tmdb_id, season, episode)
        if self.provider.history.import_item(identity, ImportedHistoryItem(item).get_history_values):
            self.changed += 1

    def import_library_items(self, targets, item_type, imported):
        changed = False
        for target in targets:
            current = self.provider.library.get_details(target, item_type)
            values = imported.get_library_values(current)
            if imported.progress_unavailable:
                self.missing_runtime += 1
            if values:
                self.provider.library.set_details(target, item_type, **values)
                if not changed:
                    self.changed += 1
                changed = True
        return changed

    def run(self, items):
        # Read the complete library before any writes; a failed read cannot create false non-library matches.
        self.library_targets
        for item in items:
            self.import_item(item)
        return self.changed

    def refresh(self):
        if not self.changed:
            return
        invalidator = SyncInvalidatorWatchedProgress()
        invalidator.notification = False
        invalidator.run(sync=True)
        watchlist = SyncInvalidatorWatchlist()
        watchlist.notification = False
        watchlist.run(sync=True)

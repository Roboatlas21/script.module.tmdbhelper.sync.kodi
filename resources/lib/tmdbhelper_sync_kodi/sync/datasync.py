from tmdbhelper.lib.sync.datasync import (
    SyncDataGetterAll, SyncDataGetterAllMoviesToWatch, SyncDataGetterAllShowsToWatch,
)


class KodiSyncDataGetterMoviesToWatch(SyncDataGetterAllMoviesToWatch):
    pass


class KodiSyncDataGetterShowsToWatch(SyncDataGetterAllShowsToWatch):
    pass


class KodiSyncDataGetterShowsInProgress(SyncDataGetterAll):
    query_clauses = ('item_type=?', 'last_watched_at IS NOT NULL')
    clause_keys = ('next_episode_id',)

    @property
    def query_values(self):
        return ('show',)

    def get_keys(self):
        return (*super().get_keys(), 'last_watched_at')

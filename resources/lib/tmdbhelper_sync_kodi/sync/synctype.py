from tmdbhelper_sync_kodi.sync.datatype import KodiDataType


class SyncCollection(KodiDataType):
    keys = ('last_collected_at', 'last_updated_at')
    key_prefix = 'collection'
    method = 'library/collection'
    last_activities_key = 'collected_at'


class SyncWatched(KodiDataType):
    keys = ('plays', 'last_watched_at', 'watched_episodes')
    method = 'library/watched'
    last_activities_key = 'watched_at'


class SyncPlayback(KodiDataType):
    keys = ('progress', 'paused_at', 'id')
    key_prefix = 'playback'
    method = 'library/playback'
    last_activities_key = 'paused_at'


class SyncAiredEpisodes(KodiDataType):
    keys = ('aired_episodes',)
    method = 'library/episodes'
    last_activities_key = 'collected_at'


class SyncNextEpisodes(KodiDataType):
    keys = ('next_episode_id', 'next_episode_aired_at')
    method = 'library/next'
    last_activities_key = 'watched_at'


class SyncAllNextEpisodes(KodiDataType):
    keys = ('upnext_episode_id',)
    method = 'library/upnext'
    last_activities_key = 'watched_at'

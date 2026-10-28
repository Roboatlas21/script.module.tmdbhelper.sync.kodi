from tmdbhelper.lib.sync.activity import SyncLastActivities


class KodiLastActivities(SyncLastActivities):
    def get_json(self):
        # The monitor's local stamp is cheap to read and must not wait for cache expiry.
        return self.provider.get_last_activities()

from xbmc import executebuiltin


if __name__ == '__main__':
    executebuiltin(
        'RunScript(plugin.video.themoviedb.helper,configure_sync_provider,'
        'addon_id=script.module.tmdbhelper.sync.kodi)')

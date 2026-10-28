# TMDbHelper Sync - Kodi

Standalone interface-v3 provider for the active Kodi profile's video library,
with separate local storage for non-library history/progress and watchlist entries.
Install alongside `plugin.video.themoviedb.helper` and choose **Kodi** separately
for collection, history/progress, watchlist, and/or scrobbling in TMDbHelper's provider selectors.
No account or authentication is required. Installation does not change selections.

## Data and actions

- Library movies, shows, seasons, and episodes become collected items. Collection
  is read-only: the provider does not scan, add, delete, or remove library content.
- History uses the stored playcount and latest played date. Kodi does not expose
  a full record of each past play through these library fields.
- Non-library movies and episodes store playcounts, UTC watched/progress dates,
  and resume positions separately in
  `special://profile/addon_data/script.module.tmdbhelper.sync.kodi/history/history.db`.
  Watched and playback sync combine these records with the library by TMDb identity
  and episode coordinates. Library state wins on duplicates, including unwatched
  state or cleared resume. Stored history is retained if an item enters the library,
  but is ignored while that library item exists. Plays from both stores are not added.
- Resume positions become playback percentages. Kodi does not provide a separate
  resume-modified timestamp; playback sorting uses the file's last-played date.
- Show/season counts and next episodes come from local episodes, not the complete
  TMDb catalogue. Watched counts and parent watched dates additionally include tracked
  non-library episodes. Parent playcounts describe the known episodes, not completion
  of the full TMDb catalogue. Collection, available episode counts, and next-episode
  discovery remain library-only. Show counts and next episodes exclude season zero.
  Future-dated library episodes are excluded from available counts and next episodes.
  Episode playcounts remain independent of parent summary rows. A library episode
  resume also starts next-up tracking; the In progress show list requires a watched episode.
- Mark watched ensures a playcount of at least one and clears resume. Repeating
  the action does not add plays. Mark unwatched clears playcount, last played, and
  resume. Library matches update the library as usual; non-library movies and episodes
  update the separate history database. Show/season actions update their matching
  library episodes and already tracked non-library episodes, without fetching or
  creating the full TMDb episode catalogue.
- Remove progress clears the matching movie/episode resume point in its owning store.
- The watchlist starts empty and supports movies, shows, seasons, and episodes,
  including items outside the Kodi library. Add/remove uses the standard watchlist
  action. Entries are stored separately in
  `special://profile/addon_data/script.module.tmdbhelper.sync.kodi/watchlist/watchlist.db`,
  with TMDb identity, Kodi media type, and the UTC date added.
- Watchlist sync checks the selected watched provider, which can be Kodi or another
  module. An entry is removed only when its stored last-watched date is later than
  the date added. Disabled watched sync skips this check. Watching an episode also
  removes an older listing of its season/show using their aggregated last-watched
  values. Repeated adds preserve the original date; removing and re-adding starts
  a new listing.

Identity comes from movie/show `uniqueid.tmdb`, falling back to the core cached
IMDb/TVDb-to-TMDb lookup. Episodes use the parent show's identity and their season
and episode numbers; an episode's own TMDb ID is never treated as the show's ID.
Items without a resolvable external identity are skipped with a diagnostic log.
No title-only matching is used for writes.

Library snapshots refresh after video-library update/removal notifications or a
completed scan/clean received by TMDbHelper's UpdateMonitor. Starting the monitor
also records a new activity stamp. Snapshot activities expire at the next local
12am, 6am, 12pm, or 6pm boundary, so changes from other clients or missed
notifications are picked up on the next sync request after that boundary.
Watchlist snapshots retain their 60-second expiry and watched-provider cleanup.
Snapshots read afresh through JSON-RPC, avoiding the core Kodi identity cache's
three-hour lifetime. A failed or incomplete snapshot
does not clear previously synced values. Successful empty snapshots clear removed
items. Actions use the standard invalidation/resync pipeline.
Kodi's local timestamps are converted to UTC with the timezone offset applicable
to that date. Library membership or watched state lacking its associated date uses
the Unix epoch as an unknown-date marker, rather than inventing a recent event.
Consequently these undated watched items do not contribute to recent daily/monthly
history statistics. Kodi cannot disambiguate repeated local times at a DST rollback.

## Scrobbling

Only the selected scrobbling provider receives TMDbHelper's start/stop requests.
Core no longer independently increments Kodi's playcount.

For another playback source matching a library item, the Kodi scrobbler records
one play at TMDbHelper's 80% completion threshold, updates last played, and clears
resume. An early stop stores resume without changing the playcount. The starting
playcount and current playcount prevent repeated stop requests from adding plays
that were already recorded. When several local versions match an identity, the
actively playing library entry wins; otherwise the first matching entry is used.
Explicit watched/unwatched actions apply to every matching library entry.

When no library item matches, the scrobbler records the same watched/resume state in
the separate history database. A completed playback adds one play and clears resume;
an early stop stores resume and its UTC update date without changing the playcount
or last-watched date. Repeated completion requests do not add another play, while
a new playback can record a rewatch. Streams are tracked by TMDb identity rather
than their potentially transient file paths.

At successful watched completion, the Kodi scrobbler also removes the movie or
episode and any older watchlisted season/show immediately. Partial playback does
not remove entries. This cleanup runs once per playback, preserving entries added
again after completion, and refreshes the selected Kodi watchlist independently
of the selected watched provider.

Playback identified as the same library database item or file is persisted by
Kodi itself, using Kodi's native watched threshold and resume behavior. The provider
does not increment it again. Selecting Trakt or MDbList for scrobbling does not
disable Kodi's natural persistence when actually playing a Kodi library item.

The provider-owned history database does not create synthetic library files or
write unscanned Kodi file records. A failed library or history read leaves the
previously synced watched/progress values intact.

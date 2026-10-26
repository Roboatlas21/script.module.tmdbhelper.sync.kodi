# TMDbHelper Sync - Kodi

Standalone interface-v3 provider for the active Kodi profile's video library.
Install alongside `plugin.video.themoviedb.helper` and choose **Kodi** separately
for collection, history/progress, watchlist, and/or scrobbling in TMDbHelper's provider selectors.
No account or authentication is required. Installation does not change selections.

## Data and actions

- Library movies, shows, seasons, and episodes become collected items. Collection
  is read-only: the provider does not scan, add, delete, or remove library content.
- History uses the stored playcount and latest played date. Kodi does not expose
  a full record of each past play through these library fields.
- Resume positions become playback percentages. Kodi does not provide a separate
  resume-modified timestamp; playback sorting uses the file's last-played date.
- Show/season counts and next episodes come from local episodes, not the complete
  TMDb catalogue. Show counts and next episodes exclude season zero. Future-dated
  episodes are excluded from available counts and next episodes. Episode playcounts
  remain independent of parent summary rows. An episode resume also starts next-up
  tracking; the In progress show list requires a watched episode.
- Mark watched ensures a playcount of at least one and clears resume. Repeating
  the action does not add plays. Mark unwatched clears playcount, last played, and
  resume. Show/season actions update their matching local episodes.
- Remove progress clears the matching movie/episode resume point.
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

Snapshots expire after 60 seconds and read afresh through JSON-RPC, avoiding the
core Kodi identity cache's three-hour lifetime. A failed or incomplete snapshot
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

At successful watched completion, the Kodi scrobbler also removes the movie or
episode and any older watchlisted season/show immediately. Partial playback does
not remove entries. This cleanup runs once per playback, preserving entries added
again after completion, and refreshes the selected Kodi watchlist independently
of the selected watched provider.

Playback identified as the same library database item or file is persisted by
Kodi itself, using Kodi's native watched threshold and resume behavior. The provider
does not increment it again. Selecting Trakt or MDbList for scrobbling does not
disable Kodi's natural persistence when actually playing a Kodi library item.

## Non-library tracking investigation

Kodi's `Files.SetFileDetails` accepts playcount, lastplayed, and resume for a video
path. Its implementation can create a file record without a scanned movie/episode,
but checks file existence and remote-access permission first. A persistent local
file can therefore retain watched state without entering the scanned collection.

This is path-keyed storage, not an external-ID history store. Transient stream
URLs do not give reliable identity across plays, and library movie/episode queries
do not enumerate these unscanned records. General non-library sync would require
a separate persistent TMDb-to-path index or provider-owned history storage. This
initial provider only writes matching library entries and does not create synthetic
library files or unscanned history records.

References:
- https://kodi.wiki/view/JSON-RPC_API/v13#Files.SetFileDetails
- https://github.com/xbmc/xbmc/blob/Omega/xbmc/interfaces/json-rpc/FileOperations.cpp#L204-L243

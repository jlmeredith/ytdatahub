# Channel & Playlist Persistence Workflow

## Overview
This document describes how channel and playlist data from the YouTube Data API is extracted, validated, displayed, and persisted in the database. It covers the full workflow, including UI, data mapping, and database schema, with a focus on ensuring all public API fields are stored and retrievable.

---

## Key Changes (see CHANGELOG.md)
- All channel and playlist fields from the YouTube API are now mapped and saved to the database.
- The playlists table schema has been expanded to include all public fields (see below).
- Nested/complex fields (e.g., thumbnails, localizations) are stored as JSON.
- UI improvements: summary cards and collapsible explorers for reviewing data.
- Full API responses are saved in both main and history tables for channels and playlists.
- All changes are TDD-driven and documented for future maintainability.

---

## Playlists Table Schema (Expanded)

The `playlists` table now includes the following columns (in addition to previous fields):

- `kind` (TEXT)
- `etag` (TEXT)
- `snippet_publishedAt` (TEXT)
- `snippet_channelId` (TEXT)
- `snippet_title` (TEXT)
- `snippet_description` (TEXT)
- `snippet_thumbnails` (TEXT, JSON)
- `snippet_channelTitle` (TEXT)
- `snippet_defaultLanguage` (TEXT)
- `snippet_localized_title` (TEXT)
- `snippet_localized_description` (TEXT)
- `status_privacyStatus` (TEXT)
- `contentDetails_itemCount` (INTEGER)
- `player_embedHtml` (TEXT)
- `localizations` (TEXT, JSON)

All nested fields are flattened using dot-to-underscore mapping. Complex objects are serialized as JSON.

---

## Data Mapping & Storage Logic

- All fields from the API response are recursively flattened.
- Dot notation keys are mapped to underscores to match DB columns.
- Numeric fields are converted to `int` where appropriate.
- Dict/list fields (e.g., thumbnails, localizations) are serialized as JSON.
- The full API response is also saved in the `playlists_history` table for time series/history.

---

## UI & Validation

- The UI displays a summary card and a collapsible field explorer for all channel and playlist data.
- All fields are validated and shown to the user before saving.
- Delta reports compare API and DB data for transparency.

---

## Testing & Context Preservation

- All changes are covered by tests that verify field mapping, type conversion, and persistence.
- This document is referenced in the README and onboarding guide for future contributors.
- The changelog is updated for every significant change.

---

## References
- [CHANGELOG.md](../../../../CHANGELOG.md)
- [README.md](../../../../README.md)
- [YouTube Data API v3 Playlists: list](https://developers.google.com/youtube/v3/docs/playlists/list) 
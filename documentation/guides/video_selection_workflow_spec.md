# Video Selection Workflow: Analytics-Driven Specification

## User Stories
- As a user, I want to:
  1. See all available videos in a sortable, filterable table with all relevant metrics (views, likes, comments, publish date, etc.).
  2. Select/deselect videos individually, by page, or "select all" (with clear feedback on what's selected).
  3. Sort and filter by any metric (e.g., most comments, most recent, least views, etc.).
  4. Search by title, description, or tags.
  5. See a preview/thumbnail and basic info for each video.
  6. Save and persist selections across pagination and filtering.
  7. Export or queue selected videos for import, tracking, or further analysis.
  8. Quickly see which videos are already imported/tracked (if applicable).

## UI/UX Requirements
- Table-based UI (not cards), with:
  - Columns: Checkbox, Thumbnail, Title, Views, Likes, Comments, Published Date, [other relevant metrics].
  - Sortable columns (click to sort ascending/descending).
  - Filter row (text search, min/max for numeric columns, date range for publish date).
  - Pagination with page size selector.
  - Select all on page and select all matching filter.
  - Sticky selection: Selections persist as you paginate/filter.
  - Summary bar: "X of Y videos selected."
  - Bulk actions: Import, queue, export, etc.

## Technical/Implementation Plan
1. **Backend**: Ensure all video metrics are available and passed to the UI in a flat, easily consumable format.
2. **UI**: Use a robust table/grid component (e.g., Streamlit AgGrid, or a custom DataFrame-based table with full interactivity).
3. **State Management**: Use session state or a dedicated selection manager to persist selections across UI actions.
4. **Performance**: Use lazy loading/pagination for large channels.
5. **Extensibility**: Design so new metrics/columns can be added easily.

## Next Steps
- Prototype the new table-based selection UI using AgGrid or similar, with sorting/filtering and persistent selection.
- Integrate with backend to ensure all metrics are available.
- Replace the current video selection step with the new workflow.
- Test with real channels and edge cases (large channels, missing data, etc.).
- Document for users and contributors. 
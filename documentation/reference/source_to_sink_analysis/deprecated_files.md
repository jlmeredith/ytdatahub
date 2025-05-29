# Deprecated Files & Code

This document tracks files and code blocks that are deprecated and candidates for removal in future versions of YTDataHub. This list should be reviewed during each major release cycle.

## Files Ready for Removal

These files can be safely removed in the next major version update:

| File | Status | Notes |
|------|--------|-------|
| `src/utils/quota_estimation.py` | Deprecated | Fully replaced by `src.services.youtube.quota_management_service.quota_management_service` |
| `src/utils/helpers.py` | Deprecated | All functions moved to specialized modules |

## UI Legacy Wrappers

These wrapper files should be maintained until we've verified all imports have been updated:

| File | Status | Notes |
|------|--------|-------|
| `src/ui/data_collection.py` | Legacy Wrapper | Redirects to `src/ui/data_collection/main.py` |
| `src/ui/data_analysis.py` | Legacy Wrapper | Redirects to `src/ui/data_analysis/main.py` |
| `src/ui/bulk_import.py` | Legacy Wrapper | Redirects to `src/ui/bulk_import/render.py` |

## Dependency Tracking

We need to ensure the following modules are updated to no longer depend on deprecated modules:

### Primary Files to Update

1. `tests/ui/pages/test_tab_navigation.py` - ✅ Updated
2. `tests/ui/components/test_debug_panel.py` - ✅ Updated
3. `tests/ui/pages/test_data_conversion.py` - ✅ Updated
4. `tests/ui/pages/test_comparison_view.py` - Need to update imports
5. `tests/ui/pages/test_api_data_display.py` - Need to update imports
6. `tests/ui/pages/test_channel_selection_ui.py` - Need to update imports

### Fixed Import Paths

When updating imports, use these reference paths:

| Old Import | New Import |
|------------|------------|
| `from src.ui.data_collection import render_data_collection_tab` | `from src.ui.data_collection.main import render_data_collection_tab` |
| `from src.ui.data_analysis import render_data_analysis_tab` | `from src.ui.data_analysis.main import render_data_analysis_tab` |
| `from src.ui.bulk_import import render_bulk_import_tab` | `from src.ui.bulk_import.render import render_bulk_import_tab` |
| `from src.ui.data_collection import convert_db_to_api_format` | `from src.ui.data_collection.utils.data_conversion import convert_db_to_api_format` |
| `from src.ui.data_collection import render_debug_panel` | `from src.ui.data_collection.debug_ui import render_debug_panel` |
| `from src.ui.data_collection import render_api_db_comparison` | `from src.ui.data_collection.comparison_ui import render_api_db_comparison` |
| `from src.utils.quota_estimation import estimate_quota_usage` | `from src.services.youtube.quota_management_service import quota_management_service` |

## Removal Process

1. Verify all dependencies have been updated
2. Add deprecation warnings for 1-2 minor versions
3. Remove in next major version update
4. Update documentation to reflect changes

## Current Plan

- **Next Minor Release (1.x)**: Complete updating all imports in test files
- **Next Major Release (2.0)**: Remove deprecated files 
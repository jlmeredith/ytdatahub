# Deprecated Modules

This document lists modules that are deprecated and scheduled for removal in future versions of YTDataHub. If you're using any of these modules directly, please update your code to use the recommended alternatives.

## Immediate Deprecation (Target: Next Release)

| Module | Status | Replacement | Notes |
|--------|--------|-------------|-------|
| `src/utils/quota_estimation.py` | Deprecated | `src.services.youtube.quota_management_service.quota_management_service` | Currently just delegates to the centralized service |
| `src/utils/helpers.py` | Deprecated | Import directly from specialized modules | All functionality has been moved to specialized modules |

## UI Legacy Wrappers (Target: Major Version Upgrade)

| Module | Status | Replacement | Notes |
|--------|--------|-------------|-------|
| `src/ui/data_collection.py` | Legacy Wrapper | `src.ui.data_collection.main.render_data_collection_tab` | Only exists for backward compatibility |
| `src/ui/data_analysis.py` | Legacy Wrapper | `src.ui.data_analysis.main.render_data_analysis_tab` | Only exists for backward compatibility |
| `src/ui/bulk_import.py` | Legacy Wrapper | `src.ui.bulk_import.render.render_bulk_import_tab` | Only exists for backward compatibility |

## Migration Instructions

### Replacing Quota Estimation

Replace:
```python
from src.utils.quota_estimation import estimate_quota_usage

# Usage
quota = estimate_quota_usage(fetch_channel=True, fetch_videos=True)
```

With:
```python
from src.services.youtube.quota_management_service import quota_management_service

# Usage
quota = quota_management_service.estimate_quota_usage(fetch_channel=True, fetch_videos=True)
```

### Replacing UI Legacy Wrappers

Replace:
```python
from src.ui.data_collection import render_data_collection_tab
from src.ui.data_analysis import render_data_analysis_tab
from src.ui.bulk_import import render_bulk_import_tab
```

With:
```python
from src.ui.data_collection.main import render_data_collection_tab
from src.ui.data_analysis.main import render_data_analysis_tab
from src.ui.bulk_import.render import render_bulk_import_tab
```

## Other Functions That Have Moved

| Function | Old Location | New Location |
|----------|-------------|--------------|
| `convert_db_to_api_format` | `src.ui.data_collection` | `src.ui.data_collection.utils.data_conversion.convert_db_to_api_format` |

## Timeline

- **Next Minor Release**: Deprecation warnings will be displayed when using these modules
- **Next Major Release**: Legacy wrapper modules will be removed entirely 
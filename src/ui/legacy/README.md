# Legacy UI Components

This directory contains UI components that have been superseded by newer implementations but are maintained for backward compatibility.

## ⚠️ Important Notes for Developers

1. **Do not add new features** to these legacy components
2. **Do not fix bugs directly** in these components unless absolutely necessary
3. **Prefer migrating functionality** to the current architecture when possible
4. **All new UI development** should use the modern component structure:
   - `src/ui/data_analysis/` for data analysis components
   - `src/ui/data_collection/` for data collection components
   - `src/ui/bulk_import/` for bulk import components

## Legacy Component Inventory

The following components are maintained for backward compatibility:

- **Original data analysis components** - Superseded by `src/ui/data_analysis/`
- **Original UI utilities** - Superseded by specialized modules in modern components

## Migration Status

These components are part of a larger UI modernization effort. See the complete migration status in the [UI Components Documentation](../../../documentation/reference/ui_components.md).

## Deprecation Timeline

These components will be maintained for backward compatibility until version 2.0, at which point they may be removed entirely. 
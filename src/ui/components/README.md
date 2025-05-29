# UI Components Directory

## ⚠️ LEGACY COMPONENTS WARNING

This directory contains legacy UI utilities that have been superseded by specialized components in the modern UI architecture.

## Current Status

Most functionality from this directory has been migrated to the following modern directories:

- `src/ui/data_analysis/components/` - For data analysis components
- `src/ui/data_collection/components/` - For data collection components
- `src/ui/bulk_import/components/` - For bulk import components

## Remaining Components

The only component still in use from this directory is:

- `ui_utils.py` - Contains utility functions that are still referenced by some parts of the codebase

## Developer Guidelines

1. **Do not add new components** to this directory
2. **Do not modify existing components** unless absolutely necessary
3. **Consider migrating remaining utilities** to the modern architecture
4. **Reference the [UI Components Documentation](../../../documentation/reference/ui_components.md)** for a complete overview of the UI architecture 
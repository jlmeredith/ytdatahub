# YTDataHub Refactor & Cleanup TODOs

This document lists all recommended refactoring and cleanup actions for the YTDataHub codebase, based on the comprehensive source-to-sink analysis. Each item references specific files, describes the issue, and provides a clear, actionable step. **Work through these in order for maximum impact and maintainability.**

---

## Highest Priority Refactors (Start Here)

### 1. [x] **Consolidate Queue Management Utilities**
- **Files:**
  - [`src/utils/queue_manager.py`](../../../src/utils/queue_manager.py)
  - [`src/utils/queue_tracker.py`](../../../src/utils/queue_tracker.py)
  - All service files using both
- **Issue:** Both modules provide overlapping queue management and tracking logic, leading to confusion, duplicated state, and inconsistent usage.
- **Action:**
  - Merge all queue management and tracking logic into a single, unified module (preferably `queue_manager.py`).
  - Remove redundant or legacy functions from `queue_tracker.py`.
  - Update all imports and usages throughout the codebase to use the unified interface.
- **Rationale:** Reduces confusion, eliminates bugs from state desync, and simplifies future maintenance.

### 2. [x] **Remove Deprecated Utility Re-Exports**
- **Files:**
  - [`src/utils/helpers.py`](../../../src/utils/helpers.py)
  - [`src/utils/__init__.py`](../../../src/utils/__init__.py)
- **Issue:** `helpers.py` is deprecated but still re-exports many functions, masking dead code and legacy usage.
- **Action:**
  - Remove all deprecated re-exports from `helpers.py` and `__init__.py`.
  - Update all code to import directly from specialized modules (e.g., `debug_utils`, `validation`, `formatters`).
  - Delete `helpers.py` if no longer needed.
- **Rationale:** Clarifies code dependencies, surfaces dead code, and enforces modularity.

### 3. [x] **Clarify Error Handling and Quota Management Responsibilities**
- **Files:**
  - [`src/services/youtube/service_impl/error_handling.py`](../../../src/services/youtube/service_impl/error_handling.py)
  - [`src/api/youtube/base.py`](../../../src/api/youtube/base.py)
  - [`src/utils/logging_utils.py`](../../../src/utils/logging_utils.py)
  - [`src/services/youtube/channel_service.py`](../../../src/services/youtube/channel_service.py)
  - [`src/services/youtube/service_impl/data_collection.py`](../../../src/services/youtube/service_impl/data_collection.py)
- **Issue:** Error handling and quota management logic is duplicated across service mixins, API base classes, and utility modules.
- **Action:**
  - Centralize error handling logic in a single mixin or utility module.
  - Centralize quota tracking and reporting in a dedicated service or utility.
  - Refactor all usages to call the centralized logic.
- **Rationale:** Prevents inconsistent error handling, reduces code duplication, and makes quota management auditable.

### 4. [x] **Remove Legacy/Unused Imports and Code**
- **Files:**
  - All modules flagged in the analysis as having unused imports or legacy code (see each section's "Inconsistencies, Unused Imports, and Issues").
- **Issue:** Defensive or legacy imports and code paths remain in many modules, increasing cognitive load and risk of bugs.
- **Action:**
  - Remove all unused imports, legacy variables, and dead code from each module.
  - Ensure all code paths are exercised by current workflows or are clearly marked as deprecated.
- **Rationale:** Reduces codebase size, improves readability, and prevents accidental use of outdated logic.

### 5. [x] **Document and Isolate Legacy UI Components**
- **Files:**
  - [`src/ui/data_analysis.py`](../../../src/ui/data_analysis.py)
  - [`src/ui/components/`](../../../src/ui/components/)
- **Issue:** Both legacy and refactored UI components are present, making the call graph ambiguous.
- **Action:**
  - Clearly document which UI components are legacy and which are current.
  - Move legacy components to a dedicated `legacy/` subdirectory or mark with comments.
  - Update documentation and code references accordingly.
- **Rationale:** Makes it clear which components are safe to modify or remove, and which are still in use.

---

## Medium Priority Refactors

### 6. [x] **Consolidate Redundant Validation and Data Transformation Logic**
- **Files:**
  - [`src/utils/validation.py`](../../../src/utils/validation.py)
  - [`src/services/youtube/channel_service.py`](../../../src/services/youtube/channel_service.py)
  - [`src/api/youtube/base.py`](../../../src/api/youtube/base.py)
- **Issue:** Validation and transformation logic is implemented in multiple places.
- **Action:**
  - Move all validation logic to `validation.py` and import as needed.
  - Ensure all data transformation utilities are in a single location.
- **Rationale:** Prevents bugs from inconsistent validation and makes future changes easier.

### 7. [x] **Review and Refactor Architectural Patterns for Consistency**
- **Files:**
  - [`src/storage/factory.py`](../../../src/storage/factory.py)
  - [`src/services/youtube_service.py`](../../../src/services/youtube_service.py)
  - [`src/analysis/`](../../../src/analysis/)
- **Issue:** Factory, service, and repository patterns are implemented in multiple places, sometimes inconsistently.
- **Action:**
  - Review all architectural pattern implementations for consistency.
  - Refactor to ensure each pattern is applied in a standard way across the codebase.
- **Rationale:** Improves maintainability and makes onboarding new developers easier.

---

## Lower Priority / Ongoing Maintenance

### 8. [x] **Remove or Clearly Mark Deprecated/Transitional Modules**
- **Files:**
  - [`src/utils/quota_estimation.py`](../../../src/utils/quota_estimation.py)
  - [`src/utils/helpers.py`](../../../src/utils/helpers.py)
  - UI Legacy Wrappers (`src/ui/data_collection.py`, `src/ui/data_analysis.py`, `src/ui/bulk_import.py`)
- **Issue:** Deprecated or transitional modules still exist, causing confusion.
- **Action:**
  - [x] Created comprehensive documentation of deprecated modules in [`documentation/reference/deprecated_modules.md`](../deprecated_modules.md) and [`documentation/reference/source_to_sink_analysis/deprecated_files.md`](deprecated_files.md)
  - [x] Updated key imports in core application files to use modernized modules
  - [x] Updated several test files to use correct import paths
  - [x] Completely removed deprecated files (quota_estimation.py, helpers.py, legacy UI wrappers)
  - [x] Updated all remaining test files with proper import paths
- **Rationale:** Prevents accidental use and clarifies the current state of the codebase.

### 9. [ ] **Update Documentation to Reflect Refactored Codebase**
- **Files:**
  - All documentation in `/documentation/` and `/documentation/reference/source_to_sink_analysis/`
- **Issue:** Documentation may become outdated as refactors are performed.
- **Action:**
  - Update all relevant documentation after each major refactor.
  - Ensure diagrams, tables, and cross-references are accurate.
- **Rationale:** Keeps the team aligned and ensures new contributors have up-to-date information.

---

## Notes
- Work through these TODOs in order for best results.
- Check off each item as it is completed.
- If you encounter additional issues during refactoring, add them to this document.

--- 
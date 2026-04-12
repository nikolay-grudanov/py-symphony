# Bug: TASK-004-BUG-001 - Deprecated Jira Search Endpoint

## Bug Details

| Field | Value |
|-------|-------|
| **Bug ID** | TASK-004-BUG-001 |
| **Title** | Jira adapter uses deprecated /rest/api/3/search endpoint |
| **Priority** | HIGH |
| **Type** | Bug |
| **Status** | FIXED |

## Description

The built-in Jira adapter (`runtime/tracker/jira.py`) uses the **deprecated** `/rest/api/3/search` endpoint in the `fetch_issues` method (line 244).

This endpoint was deprecated in **May 2025**. The current recommended endpoint is `/rest/api/3/search/jql`.

## Affected Components

| Component | Details |
|-----------|---------|
| **Affected File** | `runtime/tracker/jira.py` |
| **Affected Method** | `fetch_issues()` |
| **Affected Line** | 244 |
| **Deprecated Endpoint** | `/rest/api/3/search` |
| **Current Endpoint** | `/rest/api/3/search/jql` |

## Root Cause

The Jira adapter was implemented using the old `/rest/api/3/search` endpoint which was deprecated by Atlassian in May 2025. The new endpoint `/rest/api/3/search/jql` should be used for JQL-based searches.

## Impact

1. **Future Compatibility**: The deprecated endpoint may stop working in future Jira Cloud updates
2. **Best Practices Violation**: Using deprecated APIs violates integration best practices
3. **Potential Service Disruption**: Future Jira Cloud releases may remove support for the old endpoint

## Fix Applied

**Date**: April 12, 2026

**Change**: Replaced deprecated endpoint in `runtime/tracker/jira.py`

```diff
- "/rest/api/3/search"
+ "/rest/api/3/search/jql"
```

**Location**: Line 244 in `fetch_issues()` method

## Verification

- [x] No remaining references to `/rest/api/3/search` endpoint
- [x] All references now use `/rest/api/3/search/jql`
- [x] Error handling preserved
- [x] Pagination logic intact

## Test Status

The fix enables the following test to pass:
- `test_uses_deprecated_endpoint` (if previously failing due to deprecated endpoint usage)
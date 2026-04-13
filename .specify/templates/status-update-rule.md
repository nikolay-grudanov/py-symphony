---
description: "Rules and workflow for updating status documents"
---

# Status Update Rules

**Purpose:** Define the workflow and requirements for updating status documents across the project.

**Version:** 1.0.0
**Last Updated:** 2026-04-13
**Owner:** build-orchestrator

## State Machine

All status updates follow this state machine:

```
pending → in_progress → completed
                   ↓
               blocked / retry_on_error / failed
                   ↓
                 escalation
```

## When to Update Status

**Mandatory Updates Required:**

1. **After Phase Completion:**
   - plan.md: After Phase 0 (research), Phase 1 (design), Phase 2 (implementation)
   - tasks.md: After completing Setup, Foundational, each User Story
   - spec.md: After draft, review, approval stages
   - checklist.md: After each category completion or critical checkpoint

2. **After Code Review:**
   - Update status to reflect review results (approved/needs_changes)
   - Document any issues found

3. **After Verification:**
   - Update status to reflect verification results (ready/needs_fixes)
   - Document any blockers

4. **After Blocking Issues:**
   - Immediately update status to `blocked` with details
   - Add escalation information if needed

## Update Format

All status updates MUST follow this format:

| Field | Description | Example |
|-------|-------------|---------|
| Date | YYYY-MM-DD when update was made | 2026-04-13 |
| Agent | Agent who made the update | build-orchestrator |
| Status | State from state machine | in_progress |
| Changes | What was changed or accomplished | "Completed Phase 1 research" |
| Artifacts | Links to files created/modified | `[plan.md](#link)` |
| Next Steps | Action items or next phase | "Proceed to Phase 2 design" |

## Agent Responsibilities

### build-orchestrator
- Coordinating status updates across all agents
- Updating Status Index (docs/STATUS.md)
- Ensuring all agents follow update rules
- Tracking overall project status

### implementation-engineer
- Updating status in plan.md, tasks.md
- Documenting implementation progress
- Marking tasks as completed

### test-engineer
- Updating status in checklist.md
- Documenting test results
- Marking checkpoints as passed/failed

### verification-agent
- Updating status after verification
- Documenting verification results
- Marking artifacts as production-ready

### code-reviewer
- Updating status after code review
- Documenting review findings
- Marking code as approved/needs_changes

## Update Workflow

1. **Before Work:** Read existing status in the document
2. **During Work:** Track progress mentally
3. **After Work:** Add status update entry immediately
4. **Review:** Verify entry follows format and includes all fields
5. **Commit:** Commit the status update along with the work

## Escalation Conditions

Escalate to build-orchestrator if:
- Status has been `blocked` for more than 30 minutes
- Multiple consecutive `retry_on_error` or `failed` states
- Critical bug in main component
- Timeline deadline exceeded

## Examples

### Example 1: Phase Completion
| Date | Agent | Status | Changes | Artifacts | Next Steps |
|------|-------|--------|---------|-----------|-----------|
| 2026-04-13 | implementation-engineer | completed | Completed Phase 1 research and initial design | `[research.md](#link), [data-model.md](#link)` | Proceed to Phase 2 design |

### Example 2: Blocking Issue
| Date | Agent | Status | Changes | Artifacts | Next Steps |
|------|-------|--------|---------|-----------|-----------|
| 2026-04-13 | implementation-engineer | blocked | Database schema change required; waiting for architecture decision | `[issue-123](#link)` | Escalate to platform-architect |

### Example 3: Code Review
| Date | Agent | Status | Changes | Artifacts | Next Steps |
|------|-------|--------|---------|-----------|-----------|
| 2026-04-13 | code-reviewer | in_progress | Code review found 3 issues: 2 minor, 1 major | `[review.md](#link)` | Fix issues and resubmit |

## Compliance

All agents MUST:
- ✅ Update status immediately after work completion
- ✅ Use correct state from state machine
- ✅ Include all required fields (Date, Agent, Status, Changes, Artifacts, Next Steps)
- ✅ Follow update workflow
- ❌ Skip status updates (this is a violation)
- ❌ Leave status in `in_progress` for extended periods without updates
- ❌ Escalate without first updating status

## References

- Status Index: [docs/STATUS.md](../../docs/STATUS.md)
- State Machine Design: [docs/state-machines/](../../docs/state-machines/)
- Build Orchestrator Workflow: [agents/build-orchestrator/WORKFLOW.md](../../agents/build-orchestrator/WORKFLOW.md)
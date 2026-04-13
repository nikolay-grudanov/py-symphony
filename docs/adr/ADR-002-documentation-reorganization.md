# Architecture Decision Record: Documentation Reorganization

**Status**: Accepted | **Date**: 2026-04-13 | **Authors**: Build Orchestrator

---

## Table of Contents

1. [Context and Problem Statement](#context-and-problem-statement)
2. [Decision Drivers](#decision-drivers)
3. [Considered Alternatives](#considered-alternatives)
4. [Decision](#decision)
5. [Consequences](#consequences)
6. [Architecture Design](#architecture-design)
7. [Implementation Guidance](#implementation-guidance)
8. [Migration Strategy](#migration-strategy)
9. [References](#references)

---

## Context and Problem Statement

### Current State (Before Reorganization)

The documentation structure prior to reorganization had several structural issues:

- All status, planning, and report files in `docs/` root directory
- No centralized status tracking system
- No YAML Front Matter in status documents
- Templates have no status tracking sections
- No workflow for updating status documents
- Build Orchestrator workflow lacks status update coordination

### Problems

The following problems were identified with the existing documentation structure:

1. **Poor Navigation**: Status, reports, and planning files mixed together in docs/ root
2. **No Centralized Status**: No single place to see overall project status
3. **No Status Tracking**: No formal workflow for tracking status updates
4. **Template Inconsistency**: Templates lack standardized status tracking sections
5. **No Agent Coordination**: No clear responsibility for status updates
6. **No Escalation Rules**: No defined escalation procedures for status issues

---

## Decision Drivers

### Functional Requirements

1. **Organized Structure**: Status, reports, and planning documents in separate subdirectories
2. **Centralized Status**: Single Status Index for quick overview
3. **Status Tracking**: Formal workflow for tracking status updates across all documents
4. **Template Standardization**: All templates have consistent status tracking sections
5. **Agent Coordination**: Clear responsibilities for status updates
6. **Escalation Procedures**: Defined rules for handling status issues

### Non-Functional Requirements

1. **Human-Readable**: Status Index should be readable by humans
2. **Machine-Processable**: Status Index should be parseable by tools (YAML Front Matter)
3. **GitHub-Friendly**: Documents should render well on GitHub
4. **Backward Compatible**: Existing documents should remain accessible
5. **Low Maintenance**: Status updates should be simple and automated

### Constraints

1. **Constitution Compliance**: Must follow project constitution invariants
2. **Quality Gates**: All changes must pass code review and verification
3. **Agent Boundaries**: No agent violates their role boundaries
4. **File Invariants**: No changes to runtime/, plugins/, agents/ (except build-orchestrator)

---

## Considered Alternatives

### Alternative 1: Move status documents to `.specify/memory/`

**Description:** Move all status documents to `.specify/memory/` directory

**Pros:**
- Centralized with other specification documents

**Cons:**
- Violates separation of concerns (spec vs. status)
- All consultants recommended against it

**Verdict:** ❌ Not suitable

---

### Alternative 2: Create new top-level directories (status/, reports/, planning/)

**Description:** Create new directories at repository root

**Pros:**
- Clear separation at top level

**Cons:**
- Clutters repository root
- Violates "docs/ for documentation" convention

**Verdict:** ❌ Not suitable

---

### Alternative 3: Keep files in docs/ root but add tags/categories

**Description:** Use YAML tags or categories to organize files

**Pros:**
- No file movement required

**Cons:**
- Requires tooling to filter tags
- Not human-friendly navigation

**Verdict:** ❌ Not suitable

---

### Alternative 4: Create subdirectories in docs/ (CHOSEN)

**Description:** Create `docs/status/`, `docs/reports/`, `docs/planning/`

**Pros:**
- Clean organization
- Follows convention
- Human-friendly
- GitHub preview works

**Cons:**
- Requires updating links

**Verdict:** ✅ **Recommended** - Best balance of organization and usability

---

## Decision

**Chosen Approach:** Alternative 4 - Create subdirectories in docs/

### Implementation

1. Create directory structure: `docs/status/`, `docs/reports/`, `docs/planning/`
2. Move files to appropriate directories
3. Create Status Index (`docs/STATUS.md`) with YAML Front Matter
4. Update all broken links
5. Add status tracking sections to all templates
6. Create `status-update-rule.md` template
7. Update build-orchestrator WORKFLOW.md with status update logic

---

## Consequences

### Positive Consequences

- ✅ Organized documentation structure (3 subdirectories)
- ✅ Centralized status tracking (Status Index with YAML Front Matter)
- ✅ Standardized status tracking (all templates have status sections)
- ✅ Clear agent responsibilities (coordination matrix)
- ✅ Defined escalation procedures (30-minute timeout rules)
- ✅ Human-readable and machine-processable (Markdown + YAML)
- ✅ GitHub-friendly (renders well with preview)

### Negative Consequences

- ⚠️ Required updating 10+ links
- ⚠️ Required updating 4 templates
- ⚠️ Required updating build-orchestrator workflow
- ⚠️ Slight overhead of status update workflow

### Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Broken links remain | Medium | Comprehensive link audit and fixes |
| Agents don't update status | Medium | Build Orchestrator monitors compliance |
| Status Index becomes stale | Low | Mandatory updates after each phase |
| YAML Front Matter errors | Low | Build Orchestrator validates format |

---

## Architecture Design

### New Documentation Structure

```
docs/
├── STATUS.md                    # Central status index with YAML Front Matter
├── status/                      # Status documents
│   └── tracker-implementation-status.md
├── reports/                     # Final reports
│   └── build-team-package-final-report.md
├── planning/                    # Planning documents
│   ├── implementation-roadmap.md
│   └── tracker-next-steps.md
└── adr/                         # Architecture Decision Records
    ├── ADR-001-pluggable-tracker-adapters.md
    └── ADR-002-documentation-reorganization.md
```

### Template Status Tracking Structure

All templates (plan.md, tasks.md, spec.md, checklist.md) now include:

```markdown
## Status Updates

| Date | Agent | Status | Changes | Artifacts | Next Steps |
|------|-------|--------|---------|-----------|-----------|
| [DATE] | [agent-name] | [state] | [description] | [links to files] | [action items] |
```

### State Machine

```
pending → in_progress → completed
                   ↓
               blocked / retry_on_error / failed
                   ↓
                 escalation
```

### Agent Responsibility Matrix

| Agent | Updates | When |
|-------|---------|------|
| implementation-engineer | plan.md, tasks.md | After phases |
| test-engineer | checklist.md | After tests |
| verification-agent | All docs | After verification |
| code-reviewer | All docs | After code review |
| build-orchestrator | Status Index | After project phase |

---

## Implementation Guidance

### Phase 1: Directory Structure & Status Index

- Create subdirectories: `docs/status/`, `docs/reports/`, `docs/planning/`
- Move 4 files to appropriate directories
- Create `docs/STATUS.md` with YAML Front Matter
- Update 10+ links across the project

### Phase 2: Update Spec Kit Templates

- Add status tracking sections to 4 templates
- Create `status-update-rule.md` with comprehensive workflow
- Fix 5 code review issues (column mismatch, state machine descriptions)

### Phase 3: Update Build Orchestrator Workflow

- Add Step 6: Status Document Management
- Add status update workflow to existing Step 4
- Add 2 items to final verification checklist
- Renumber sections (Step 6 → Step 7)

---

## Migration Strategy

### Backward Compatibility

- All existing documents remain accessible (moved, not deleted)
- All links updated to new paths
- No breaking changes to existing workflows

### Forward Path

1. Agents update status documents after completing work
2. Build Orchestrator monitors compliance
3. Status Index updated after each project phase
4. Escalation procedures followed for status issues

---

## References

### Specification Documents

1. **SPEC.md** - Symphony Service Specification
2. **.specify/memory/constitution.md** - Project constitution
3. **.specify/templates/status-update-rule.md** - Status update rules

### External References

1. **YAML Front Matter** - https://jekyllrb.com/docs/front-matter/
2. **Markdown Tables** - https://github.github.com/gfm/#tables-extension-

### Internal Documents

1. **ADR-001** - Pluggable Issue Tracker Adapter Architecture
2. **docs/status/tracker-implementation-status.md** - Tracker status
3. **docs/reports/build-team-package-final-report.md** - Build team report

---

**Document Version**: 1.0
**Last Updated**: 2026-04-13
**Status**: Accepted
**Next Review**: 6 months or after significant changes
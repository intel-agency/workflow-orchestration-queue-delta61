# Workflow Execution Plan: project-setup

## 1. Overview

- **Workflow Name:** project-setup
- **Workflow File:** `ai_instruction_modules/ai-workflow-assignments/dynamic-workflows/project-setup.md`
- **Project Name:** workflow-orchestration-queue (OS-APOW)
- **Project Description:** Headless agentic orchestration platform that transforms GitHub Issues into automated Execution Orders, enabling AI agents to autonomously develop, test, and submit PRs without human intervention.
- **Total Assignments:** 6 main assignments + 1 pre-script event + 2 post-assignment events + 1 post-script event
- **High-Level Summary:** This workflow initializes a fresh repository cloned from the workflow-orchestration-queue-delta61 template, creates an application plan from seeded plan documents, establishes the Python project structure, creates AGENTS.md, generates a debrief report, and merges the setup PR.

## 2. Project Context Summary

### Key Facts from plan_docs/

| Category | Details |
|----------|---------|
| **Project Name** | workflow-orchestration-queue (OS-APOW) |
| **Tech Stack** | Python 3.12+, FastAPI, Uvicorn, Pydantic, HTTPX, uv |
| **Key Components** | Sentinel Orchestrator (polling service), Notifier Service (webhook receiver) |
| **Containerization** | Docker, DevContainers, Docker Compose |
| **Repository** | intel-agency/workflow-orchestration-queue-delta61 |
| **Architecture Pattern** | Event-driven, shell-bridge execution, Markdown-as-Database |

### Technology Stack Details

- **Language:** Python 3.12+
- **Package Manager:** uv (Rust-based, fast dependency resolution)
- **Web Framework:** FastAPI with Uvicorn ASGI server
- **Validation:** Pydantic for data schemas
- **HTTP Client:** HTTPX (async)
- **CLI/Shell:** PowerShell Core (pwsh), Bash
- **Container Runtime:** Docker, DevContainers

### Special Constraints

- All GitHub Actions must be pinned to full commit SHA (no version tags)
- Self-approval allowed for setup PR
- CI remediation: up to 3 fix cycles before escalating
- Branch protection ruleset must be imported from `.github/protected-branches_ruleset.json`
- Labels must be imported from `.github/.labels.json`

### Known Risks

1. **GitHub API Rate Limiting** - Mitigated by using GitHub App tokens (5,000 req/hr)
2. **Concurrency Collisions** - Mitigated by assign-then-verify pattern
3. **Container Drift** - Mitigated by stopping worker containers between tasks

## 3. Assignment Execution Plan

### Pre-Script Event: create-workflow-plan

| Field | Content |
|---|---|
| **Assignment** | `create-workflow-plan`: Create Workflow Plan |
| **Goal** | Create a comprehensive workflow execution plan for the dynamic workflow |
| **Key Acceptance Criteria** | - Dynamic workflow file read and understood<br>- All assignments traced and read<br>- All plan_docs/ files read<br>- Workflow execution plan produced and approved<br>- Plan committed to plan_docs/workflow-plan.md |
| **Project-Specific Notes** | This document serves as the output of this assignment |
| **Prerequisites** | None (first step) |
| **Dependencies** | None |
| **Risks / Challenges** | None identified |
| **Events** | None |

---

### Assignment 1: init-existing-repository

| Field | Content |
|---|---|
| **Assignment** | `init-existing-repository`: Initiate Existing Repository |
| **Goal** | Set up the repository with labels, branch protection, GitHub Project, and initial configuration |
| **Key Acceptance Criteria** | - New branch created (dynamic-workflow-project-setup)<br>- Branch protection ruleset imported<br>- GitHub Project created with columns<br>- Labels imported from .github/.labels.json<br>- Workspace/devcontainer files renamed<br>- PR created from branch to main |
| **Project-Specific Notes** | Repository is the template itself; branch already created; need to import labels and create project |
| **Prerequisites** | GitHub authentication with repo, project, administration scopes |
| **Dependencies** | None (first main assignment) |
| **Risks / Challenges** | - Branch protection requires administration:write scope<br>- Project creation requires project scope |
| **Events** | post-assignment-complete: validate-assignment-completion, report-progress |

---

### Assignment 2: create-app-plan

| Field | Content |
|---|---|
| **Assignment** | `create-app-plan`: Create Application Plan |
| **Goal** | Create a comprehensive application plan documented in a GitHub Issue |
| **Key Acceptance Criteria** | - Application template analyzed<br>- Plan documented in issue using template<br>- Milestones created and linked<br>- Issue added to GitHub Project<br>- Appropriate labels applied |
| **Project-Specific Notes** | Plan docs in plan_docs/ include Development Plan v4.2, Architecture Guide v3.2, Implementation Spec v1.2; these serve as the application template |
| **Prerequisites** | init-existing-repository completed (labels available) |
| **Dependencies** | Labels from init-existing-repository |
| **Risks / Challenges** | - Need to synthesize multiple plan docs into single plan issue<br>- Must follow application-plan.md template |
| **Events** | pre-assignment-begin: gather-context<br>on-assignment-failure: recover-from-error<br>post-assignment-complete: report-progress |

---

### Assignment 3: create-project-structure

| Field | Content |
|---|---|
| **Assignment** | `create-project-structure`: Create Project Structure |
| **Goal** | Create the actual project structure and scaffolding for the application |
| **Key Acceptance Criteria** | - Solution/project structure created<br>- All required directories established<br>- Initial configuration files created<br>- CI/CD pipeline structure established<br>- Documentation structure created<br>- Repository summary document created<br>- All GitHub Actions pinned to SHA |
| **Project-Specific Notes** | Python project using uv; structure defined in Implementation Spec:<br>- pyproject.toml, uv.lock<br>- src/notifier_service.py, src/orchestrator_sentinel.py<br>- src/models/, src/queue/<br>- scripts/, local_ai_instruction_modules/, docs/ |
| **Prerequisites** | create-app-plan completed |
| **Dependencies** | Application plan for tech stack decisions |
| **Risks / Challenges** | - Must use Python/uv conventions, not .NET<br>- Docker healthchecks must use Python stdlib, not curl |
| **Events** | None defined |

---

### Assignment 4: create-agents-md-file

| Field | Content |
|---|---|
| **Assignment** | `create-agents-md-file`: Create AGENTS.md File |
| **Goal** | Create a comprehensive AGENTS.md file for AI coding agents |
| **Key Acceptance Criteria** | - AGENTS.md exists at repository root<br>- Contains project overview, setup commands, project structure<br>- Contains code style, testing instructions, PR guidelines<br>- All commands validated by running them |
| **Project-Specific Notes** | Must complement existing README.md and .ai-repository-summary.md |
| **Prerequisites** | create-project-structure completed (commands can be validated) |
| **Dependencies** | Project structure for command validation |
| **Risks / Challenges** | - Commands must be validated by actually running them |
| **Events** | None defined |

---

### Assignment 5: debrief-and-document

| Field | Content |
|---|---|
| **Assignment** | `debrief-and-document`: Debrief and Document Learnings |
| **Goal** | Create a comprehensive debriefing report capturing lessons learned |
| **Key Acceptance Criteria** | - Detailed report created using template<br>- All 12 sections complete<br>- Deviations documented<br>- Report reviewed and approved<br>- Committed and pushed to repo<br>- Execution trace saved |
| **Project-Specific Notes** | Must capture all deviations and issues from this workflow execution |
| **Prerequisites** | All prior assignments completed |
| **Dependencies** | All prior assignment outputs |
| **Risks / Challenges** | - Must be thorough in capturing all issues |
| **Events** | None defined |

---

### Assignment 6: pr-approval-and-merge

| Field | Content |
|---|---|
| **Assignment** | `pr-approval-and-merge`: Pull Request Approval and Merge |
| **Goal** | Complete the full PR approval and merge process |
| **Key Acceptance Criteria** | - All CI checks pass (up to 3 remediation cycles)<br>- Code review delegated to code-reviewer<br>- All review comments resolved<br>- Stakeholder approval obtained<br>- PR merged<br>- Source branch deleted<br>- Related issues closed |
| **Project-Specific Notes** | **Self-approval allowed** for this setup PR; CI remediation loop required |
| **Prerequisites** | All prior assignments completed, PR created in init-existing-repository |
| **Dependencies** | PR number from init-existing-repository |
| **Risks / Challenges** | - CI may fail requiring remediation<br>- Must wait for auto-reviewers (Copilot, etc.) |
| **Events** | None defined |

---

### Post-Script Event: Apply orchestration:plan-approved Label

| Field | Content |
|---|---|
| **Event** | `post-script-complete`: Apply Plan Approved Label |
| **Goal** | Apply orchestration:plan-approved label to the application plan issue |
| **Trigger** | After all assignments and post-assignment events complete successfully |
| **Action** | - Locate the application plan issue created during create-app-plan<br>- Apply label orchestration:plan-approved<br>- Record output as #events.post-script-complete.plan-approved |

---

## 4. Sequencing Diagram

```
pre-script-begin: create-workflow-plan
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Assignment 1: init-existing-repository                          │
│   - Create branch (already done)                                │
│   - Import branch protection ruleset                            │
│   - Create GitHub Project                                       │
│   - Import labels                                               │
│   - Rename workspace/devcontainer files                         │
│   - Create PR                                                   │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼ post-assignment-complete: validate, report-progress
         │
┌─────────────────────────────────────────────────────────────────┐
│ Assignment 2: create-app-plan                                   │
│   - Analyze plan_docs/                                          │
│   - Create plan issue using template                            │
│   - Create milestones                                           │
│   - Link to project, apply labels                               │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼ post-assignment-complete: validate, report-progress
         │
┌─────────────────────────────────────────────────────────────────┐
│ Assignment 3: create-project-structure                          │
│   - Create Python project structure (pyproject.toml, src/, etc.)│
│   - Create Dockerfile, docker-compose.yml                       │
│   - Create CI/CD workflows (SHA-pinned)                         │
│   - Create documentation structure                              │
│   - Create .ai-repository-summary.md                            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼ post-assignment-complete: validate, report-progress
         │
┌─────────────────────────────────────────────────────────────────┐
│ Assignment 4: create-agents-md-file                             │
│   - Create AGENTS.md with project context                       │
│   - Validate all commands work                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼ post-assignment-complete: validate, report-progress
         │
┌─────────────────────────────────────────────────────────────────┐
│ Assignment 5: debrief-and-document                              │
│   - Create debrief report with all 12 sections                  │
│   - Document deviations and lessons learned                     │
│   - Save execution trace                                        │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼ post-assignment-complete: validate, report-progress
         │
┌─────────────────────────────────────────────────────────────────┐
│ Assignment 6: pr-approval-and-merge                             │
│   - Verify CI passes (remediate if needed)                      │
│   - Delegate code review                                        │
│   - Resolve review comments                                     │
│   - Self-approve and merge                                      │
│   - Delete branch, close issues                                 │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼ post-script-complete: apply orchestration:plan-approved label
         │
    WORKFLOW COMPLETE
```

## 5. Open Questions

1. **Branch Protection Ruleset:** Does the GH_ORCHESTRATION_AGENT_TOKEN have `administration:write` scope for importing the ruleset?
2. **GitHub Project:** Should the project use the new GitHub Projects (beta) or classic project board?
3. **Milestone Names:** Should milestones follow the phase names from the development plan (Phase 0, Phase 1, etc.)?

---

## 6. Approval Record

| Reviewer | Status | Date | Comments |
|----------|--------|------|----------|
| Orchestrator (Self) | ✅ Approved | 2026-03-26 | Plan created and execution proceeding |

---

*Generated by: orchestrate-dynamic-workflow assignment*
*Date: 2026-03-26*

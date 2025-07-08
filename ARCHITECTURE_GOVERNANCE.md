# Architecture Governance - Ensuring Active Use of Technical Architecture

## Overview

This document establishes processes and practices to ensure the `TECHNICAL_ARCHITECTURE.md` document is actively referenced and used when making technical decisions, rather than becoming stale documentation.

## Team Size and Review Process

**Current Team:**
- 1 human (you)
- 1 session-based AI agent (me)

**Implication:**
- No need for formal biweekly meetings or large-team ceremonies.
- Architecture reviews are integrated directly into commit, deploy, and testing protocols.
- All architectural decisions, reviews, and documentation updates happen "just-in-time" as part of the normal development workflow.
- Commit messages and PR descriptions should record architectural decisions and rationale.

## Core Principles

1. **Architecture-First Decision Making**: All technical changes must be evaluated against our architecture
2. **Living Documentation**: Architecture document must be updated with every significant change
3. **Team Accountability**: Everyone is responsible for maintaining architectural consistency
4. **Continuous Validation**: Regular reviews ensure architecture remains relevant

## Processes and Workflows

### 1. Just-in-Time Architecture Review

**When**: Before every commit, deployment, or major test
**Who**: You (human) + AI agent
**Process**:
- Run the architecture validation script (`python scripts/validate_architecture.py`)
- Review any violations or warnings
- Update `TECHNICAL_ARCHITECTURE.md` as needed
- Record architectural decisions in commit messages or PR descriptions

### 2. Pull Request/Commit Architecture Validation

**When**: Every commit or pull request
**Who**: You (human) + AI agent
**Process**:
- Pre-commit hook runs architecture validation
- If violations are found, fix them before committing
- Use commit messages to document architectural changes

### 3. Documentation Updates

- Update `TECHNICAL_ARCHITECTURE.md` and related docs with every significant change
- Use the provided documentation templates for new components or changes
- Keep documentation up to date as part of the normal workflow

### 4. Architecture Decision Records (ADRs)

- For any significant architectural decision, create a simple markdown file in `/docs/architecture/decisions/` (optional for small team)
- Use commit messages to record rationale for minor decisions

## Tools and Automation

- **Architecture Validation Script**: Automated checks for architectural consistency
- **Pre-commit Hook**: Prevents commits with architecture violations
- **Documentation Standards**: Templates for component and change documentation

## Continuous Improvement

- Periodically review the architecture document for accuracy and completeness
- Refactor and update governance processes as the team grows or needs change

---

*This governance document is streamlined for a small, agile team. If the team grows, more formal review processes can be reintroduced as needed.* 
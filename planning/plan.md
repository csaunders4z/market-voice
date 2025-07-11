## Notes
- Script generation requirements are now loaded dynamically from planning/script_generation_requirements.md at runtime.
- Requirements are editable by the user and changes are reflected without code changes.
- If the requirements file is missing/unreadable, the script falls back to built-in requirements.

## Current Goal
Verify requirements markdown integration in production script generation

- Script generation requirements and quality standards are documented in planning/project-requirements.md and planning/quality-standards.md (MoSCoW, KPIs, technical/content/business requirements).
- Must/Should/Could features, success metrics, and test design factors are outlined in project-requirements.md and project-overview.md.
- User will manually edit the generated requirements markdown file and iterate on script generation logic with the assistant.
- Production script generation logic should load and apply requirements from the external markdown file (planning/script_generation_requirements.md) at runtime, keeping requirements human-editable.

- [ ] Review requirements for script generation and evaluate test design
  - [x] Review script generation requirements and quality standards in planning docs
  - [x] Summarize/document script generation requirements for implementation
  - [x] Create requirements markdown file for user editing and iteration
  - [x] Update production script generation logic to load/apply requirements from markdown file

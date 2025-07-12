# Planning Folder Overview

This folder contains all planning and technical strategy documents for the Market Voices system.

## Key Documents
- `project-overview.md`: High-level goals and vision
- `project-requirements.md`: MoSCoW requirements, KPIs, and dependencies
- `quality-standards.md`: Content quality and validation standards
- `plan.md`: Current implementation plan and progress
- `script_generation_requirements.md`: **Foundational prompt for script generation** (not a requirements checklist; see technical-strategy.md)
- `technical-strategy.md`: Technical strategy and rationale for the foundational prompt approach

## Script Generation Prompt Strategy
- The file `script_generation_requirements.md` is now a foundational, editable prompt for the LLM.
- At runtime, the system amends this prompt with daily market data and analysis before script generation.
- This approach enables rapid iteration and flexibility in show style, tone, and business logic.

See `technical-strategy.md` for full details.

# Technical Strategy: Foundational Prompt Approach for Script Generation

## Purpose
This document describes the updated technical strategy for script generation in the Market Voices system. The foundational prompt approach replaces the previous requirements-driven prompt construction. The file `planning/script_generation_requirements.md` now serves as the base prompt for every script generation run, and is amended at runtime with relevant daily stock market data and analysis.

## Key Changes
- **Foundational Prompt**: `planning/script_generation_requirements.md` is no longer a requirements checklist. It is a foundational prompt, written in natural language, that defines the style, tone, structure, and rules for script generation.
- **Dynamic Amendment**: At runtime, the system injects current market data, news, technical indicators, and analysis into the foundational prompt before sending it to the language model.
- **Editable by Users**: The foundational prompt can be edited at any time for rapid iteration and experimentation with script style or logic, without code changes.
- **Future-Proof**: This approach allows for easy evolution of the script generation process. The foundational prompt and the amendment logic can be refined independently.

## Implementation Overview
- The script generation module loads `planning/script_generation_requirements.md` as the base prompt.
- Before generating a script, the system reads this file and appends or merges in daily data (top gainers/losers, news, technicals, etc).
- The combined prompt is sent to the LLM for script generation.
- Output is parsed and validated as before.

## Example Flow
1. User edits `planning/script_generation_requirements.md` to update show style, tone, or rules.
2. Data pipeline collects daily market data and news.
3. Script generator loads foundational prompt, amends it with data, and generates the script.
4. Script is validated and output for production.

## Next Steps
- Update codebase (especially `src/script_generation/script_generator.py`) to treat the requirements file as a foundational prompt.
- Ensure all documentation and onboarding guides reflect this approach.
- Continue to iterate and refine both the prompt and amendment logic as needed.

# Project Bootstrap Plan

## Goal

Create the initial public repo structure for an AI-generated music transition pipeline distributed by The Faceless Dancer.

The first implementation should establish the project as a modular, runnable baseline rather than trying to solve model integration all at once.
It should also make configuration and future UI workflows first-class concerns, because different users will want different transition lengths, repaint behavior, model settings, prompts, output formats, and organization styles.

## Intended Approach

1. Initialize a small Python package for the core pipeline.
2. Add clear module boundaries for:
   - configuration
   - audio clip metadata
   - tail/context extraction
   - scaffold creation
   - transition generation interfaces
   - candidate scoring interfaces
   - export/output organization
3. Define user-editable configuration objects for common transition settings instead of hardcoding timing, paths, prompts, formats, or model parameters.
4. Keep pipeline data structures UI-friendly, so a future interface can show source clip, selected tail/context, transition settings, prompt/style, generation status, candidates, and exported result without reverse-engineering internal state.
5. Implement safe placeholder behavior where ACE-Step integration will later plug in.
6. Add a command-line entry point that can prepare a repaint scaffold from an input audio file.
7. Add repo hygiene files and setup documentation suitable for a public project.

## Proposed Files

- `README.md`
  - Project purpose, setup, quickstart, and current limitations.
- `pyproject.toml`
  - Package metadata, Python version, runtime dependencies, and console script.
- `.gitignore`
  - Ignore generated audio, model outputs, caches, and local environment files.
- `src/autotransition/`
  - Main Python package.
- `src/autotransition/config.py`
  - Central defaults for timing, output paths, formats, prompt presets, and future model settings.
- `src/autotransition/presets.py`
  - Named transition presets such as smooth continuation, energy build, breakdown, genre shift, and DJ-friendly bridge.
- `src/autotransition/audio/`
  - Audio loading, slicing, silence creation, and stitching helpers.
- `src/autotransition/pipeline/`
  - Transition planning and scaffold-building workflow with serializable state for UI/API use.
- `src/autotransition/models/`
  - Interface for future ACE-Step repaint integration.
- `src/autotransition/scoring/`
  - Candidate scoring interfaces and basic placeholder checks.
- `src/autotransition/cli.py`
  - Initial CLI for preparing a transition scaffold.
- `docs/ui-notes.md`
  - Early creator-facing UI requirements and terminology so the future app stays approachable.
- `tests/`
  - Focused tests for config and scaffold planning logic.

## Dependencies

Proposed initial dependencies:

- `pydub`
  - Practical audio slicing/stitching wrapper.
  - Requires `ffmpeg` for broad format support.
- `typer`
  - Small CLI framework with readable command definitions.

No model runtime dependency should be added in this first pass. ACE-Step integration should be planned separately because it affects GPU setup, model paths, inference parameters, and install complexity.

## Tradeoffs

- Starting with a CLI before UI keeps the pipeline testable and avoids designing UI around unstable internals.
- Designing state objects for UI/API use now adds a little structure early, but prevents the CLI from becoming the only shape the app understands.
- Using `pydub` is simpler than lower-level audio arrays for the first scaffold workflow, but later scoring and analysis may need `librosa`, `soundfile`, or `numpy`.
- Deferring ACE-Step execution avoids hardcoding machine-specific model paths or GPU assumptions.

## Risks

- Audio format support depends on local `ffmpeg`; documentation must make this explicit.
- Placeholder model interfaces can become dead weight if overdesigned, so the first pass should keep them small.
- Scaffold generation alone does not prove musical quality; candidate scoring and real repaint integration need follow-up plans.
- Too many settings can overwhelm non-technical users, so defaults and presets should expose a simple path first while keeping advanced controls available.

## Validation

- Run unit tests for pure planning/config behavior.
- Run the CLI against a small local audio file if available.
- Confirm generated scaffold files and metadata are written under predictable output folders that are ignored by git.

## Approval Needed

Implementation should wait until this plan is approved or revised.

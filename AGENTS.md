# AGENTS.md

## Project Context

This repository is distributed by **The Faceless Dancer** and is intended to become a public, reusable pipeline for AI-generated music transitions.

The goal is to help users generate, extend, transition, and organize music clips in a way that is practical for creators, streamers, visualizers, rhythm-game experiments, and other public-facing media projects.

Build this as a professional open-source tool, not a one-off script.

## Development Workflow

Before making changes, create a plan first.

For any meaningful feature, refactor, UI change, or architectural decision:

1. Add a plan in `docs/plans/`.
2. Explain the intended approach, affected files, tradeoffs, and risks.
3. Wait for approval before implementation unless the task is clearly tiny or explicitly marked as safe to proceed.

Keep plans direct and implementation-focused.

## Architecture Expectations

Keep the project modular and easy to hack.

Separate concerns clearly:

* audio analysis
* audio slicing and stitching
* model inference
* transition generation
* scoring/selection
* queue/playback/export logic
* UI/API layer
* configuration
* logging/debugging

Avoid hardcoding model paths, timing values, prompts, formats, or output locations inside core logic. Put configurable behavior in a central, organized config area.

Design modules so users can replace pieces later, such as switching models, changing BPM/key detection, adding new scoring rules, or swapping the UI.

## Public Repo Standards

Assume other developers will clone this repo and try to run it.

Prioritize:

* clear file names
* readable code
* small functions
* useful comments where behavior is not obvious
* practical defaults
* helpful errors
* documented setup steps
* no secret keys or personal paths committed
* examples that work out of the box

Keep the repo organized enough that someone can understand the project structure without reading every file.

## UI Expectations

The UI should look professional, clean, and intentional.

Do not build a bare developer panel unless specifically requested. Even early UI should feel like a real tool from The Faceless Dancer.

Use a polished layout with clear spacing, readable typography, obvious controls, useful status feedback, and sane empty/error/loading states.

The UI should make the pipeline understandable:

* current source clip
* selected tail/context
* transition settings
* target prompt/style
* generation status
* candidate outputs
* chosen/exported result

Design UI components so they can grow into a public creator-facing app.

## Branding

Use **The Faceless Dancer** as the distributor/brand.

Keep branding tasteful and minimal. Avoid locking core functionality to branding-specific code. Public users should be able to fork, rebrand, or customize the project without fighting the architecture.

## Code Quality Rules

Prefer simple, reliable code over clever code.

Do not create giant files. Split code when responsibilities diverge.

Do not silently swallow errors. Surface useful messages.

Do not introduce unnecessary dependencies.

When adding dependencies, explain why they are needed in the plan.

Keep generated files, model outputs, cache folders, and large media out of git unless explicitly intended.

## Audio Pipeline Priorities

The transition pipeline should be designed around repeatable steps:

1. Take the ending of the current generated clip.
2. Use it as context for the next generated clip.
3. Generate or repaint a continuation.
4. Score/check the result.
5. Export a clean transition-ready audio segment.

Keep timing, overlap, fade, BPM, key, prompt, seed, and model settings trackable as metadata.

Generated outputs should be organized predictably so users can inspect and reuse them.

## Agent Behavior

When working in this repo:

* plan before building
* keep changes modular
* preserve public usability
* update docs when behavior changes
* avoid personal-machine assumptions
* keep UI polished
* make the project easy for other developers to understand, fork, and extend

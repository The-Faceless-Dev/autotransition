# Model Management

Autotransition should support both manual model installation and automatic installation during generation.

## User Flow

Users should be able to:

1. Select a repaint-capable ACE-Step model.
2. See whether it is installed.
3. Install it from Hugging Face.
4. Start generation and allow the app to download the selected model if it is missing.

The UI should show friendly labels, repaint support, hardware guidance, and a clear install location before downloading large files.

## CLI Flow

List known model profiles:

```powershell
autotransition models list
```

Install a model:

```powershell
autotransition models install acestep-v15-turbo
```

Use a custom cache directory:

```powershell
autotransition models install acestep-v15-turbo --models-dir E:\models\autotransition
```

## Registry

The model registry stores:

- Slug
- Display name
- Hugging Face repo id
- Local directory name
- ACE-Step generation/version family
- Repaint capability
- Quality/speed label
- VRAM guidance
- Default inference steps
- Notes for users

Only repaint-capable models should appear in transition-generation UI by default.

## Download Behavior

Downloads use `huggingface_hub.snapshot_download` so the app can later support progress reporting, resumable downloads, and Hugging Face auth.

Failed downloads should surface practical errors: network failure, missing auth, disk space, unavailable repo, or interrupted download.

## Current Scope

This repo can list and install ACE-Step model profiles. Actual ACE-Step repaint inference is planned separately because it requires the official runtime package and hardware-specific settings.

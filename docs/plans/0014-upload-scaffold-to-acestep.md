# Upload Scaffold To ACE-Step Plan

## Goal

Fix ACE-Step repaint requests after ACE-Step started rejecting absolute audio file paths.

## Problem

Autotransition sends the generated scaffold path to ACE-Step as an absolute `src_audio_path`. ACE-Step now rejects absolute paths outside the system temp directory with:

```text
absolute audio file paths are not allowed
```

Sending a relative path is not reliable because ACE-Step runs from its runtime folder, not the Autotransition project root.

## Approach

1. Send `/release_task` as multipart form data.
2. Upload the generated scaffold as the `src_audio` file field.
3. Send all scalar generation settings as form fields.
4. Keep result polling and download behavior unchanged.
5. Add tests that verify the release request uses `files={"src_audio": ...}` and no absolute `src_audio_path`.

## Affected Files

- `src/autotransition/models/acestep_api.py`
- `tests/test_acestep_api.py`

## Tradeoffs

Uploading the scaffold copies the file to ACE-Step's temp directory on every generation request. These scaffold files are small compared with model weights and generated outputs, and this path matches ACE-Step's current security model.

## Risks

Multipart field parsing treats values as strings, so booleans and numbers need to be serialized predictably.

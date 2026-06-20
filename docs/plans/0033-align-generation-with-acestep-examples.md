# 0033 Align Generation With ACE-Step Examples

## Problem

The raw ACE-Step output is garbled before Autotransition stitches it to the source clip. That means the failure is not caused by our composite/stitching path. The request we send to ACE-Step is not equivalent to the generation path ACE-Step demonstrates in its own docs, examples, and Gradio UI.

Our current `text2music` request is too thin:

- It sends `prompt` plus `lyrics="[Instrumental]"`.
- It forces only a few diffusion settings.
- It does not send `time_signature`.
- It does not use ACE-Step's format/sample planning path.
- It does not send the full LM planning controls ACE-Step expects for prompt-following generation.
- It posts form data even for pure text generation, while ACE-Step's API docs show JSON request examples for text-only jobs.

ACE-Step's working generation examples are built around one of two valid flows:

- Custom text-to-music: detailed caption, structured lyrics, duration, BPM, key, language, time signature, and `thinking=true`.
- Simple/sample generation: natural-language description goes through the 5Hz LM planner, which produces caption, lyrics, and metadata before DiT generation.

For Autotransition, the user is usually giving a natural-language style prompt and selecting a target new-section duration. That is closer to ACE-Step's LM-planned flow than to a bare `prompt + [Instrumental]` request.

## Full Generation Audit

Checked against ACE-Step's local `docs/en/API.md`, `docs/en/INFERENCE.md`, `GenerateMusicRequest`, API job setup code, and Gradio `generate_with_progress` path.

### Correct in Autotransition

- Runtime order is correct: start ACE-Step API, call `/release_task`, poll `/query_result`, download via `/v1/audio`.
- Text continuation correctly avoids uploading `src_audio` to `text2music`. ACE-Step's Gradio code also clears `src_audio` for normal `text2music`.
- `batch_size=1` is correct for the app's current single-result workflow and avoids VRAM problems.
- `lyrics="[Instrumental]"` is valid ACE-Step syntax for instrumental generation.
- `audio_duration` should be the requested New section seconds for raw text generation.
- `bpm`, `key_scale`, `seed`, `inference_steps`, `guidance_scale`, and `shift` are real ACE-Step controls.
- Stitching/composite happens after raw generation, so it cannot explain garbled raw output.

### Wrong or Incomplete in Autotransition

- Raw generation sends form data for pure text generation. ACE-Step supports this, but its documented text generation examples use JSON. Matching the documented path makes request behavior easier to reason about and debug.
- Raw generation does not send `use_format=true`, so a short user prompt plus `[Instrumental]` goes into generation without ACE-Step's own caption/metadata formatting step.
- Raw generation does not explicitly send LM planning controls that ACE-Step's API and Gradio path use: `lm_temperature`, `lm_cfg_scale`, `lm_top_p`, `lm_negative_prompt`, `use_cot_caption`, `use_cot_language`, `constrained_decoding`, and `allow_lm_batch`.
- Raw generation does not send `time_signature`. ACE-Step treats this as core metadata. If missing, the LM may infer it, but for a controlled continuation workflow we should either set it to `"4"` or expose it.
- Raw generation does not verify that `/v1/init` actually initialized the 5Hz LM. The request requires the LM for `thinking=true` quality generation; if init silently returns a partial/non-useful state, generation can degrade or fail later.
- We still build a scaffold before default text generation. That is wasted and confusing because the scaffold is not sent to `text2music`. It does not cause garbled raw audio, but it is wrong for the current default workflow.
- Output format is `wav`. That is supported, but ACE-Step's direct inference default is `flac`. For diagnosis, raw ACE output should use a clearly recorded format and ideally match ACE-Step's default unless the app needs WAV for composition.
- We do not explicitly send `use_tiled_decode=true`. ACE-Step's request model defaults it to true and the handler uses it to choose tiled VAE decode with OOM fallbacks. Relying on the default is probably not the cause of static, but the corrected request should make the decode path explicit.
- We do not expose or record MP3-specific output settings. This is not relevant while raw output is FLAC/WAV, but it matters if users choose MP3/AAC later.
- We do not save the exact request payload before submission. That makes it too hard to compare our call with ACE-Step's known-good examples.
- We do not save `/release_task` and intermediate `/query_result` responses separately. That hides whether ACE-Step reformatted prompt/lyrics/metadata, changed duration, or returned warnings.
- Our UI exposes only a small subset of real ACE-Step generation controls. That is acceptable for a simple primary UI, but advanced controls should map to actual ACE-Step fields only.
- Repaint/boundary repaint is still present as a secondary path. It should not be part of the default raw generation diagnosis because ACE-Step docs say LM is skipped for repaint, and repaint cannot fix raw text2music corruption.

### Needs a Deliberate Decision

- `sample_query`/`sample_mode` is ACE-Step's official natural-language description path, but ACE-Step's code replaces duration/BPM/key/time signature with LM-generated metadata. Autotransition needs New section seconds to be respected, so the safer default is `use_format=true` with user metadata supplied.
- Short clips may be inherently weaker for ACE-Step. The docs say 10-20 seconds is the short minimum, and instrumentals work better at 30-180 seconds. We should keep user control but warn or clamp below ACE-Step's documented range.
- Lyrics are currently fixed to `[Instrumental]`. That matches the current instrumental-transition goal, but if users want vocal continuations later, lyrics must become a real input instead of being hardcoded.
- ACE-Step performs VAE decode and file encoding server-side. Autotransition should not re-decode raw generation before saving; it should download the file bytes returned by `/v1/audio`, store them with the correct extension, and only use local decoding later for composition/playback.

## Approach

1. Change Autotransition's default raw generation request to use ACE-Step's official LM-planned text generation path.
   - Send JSON to `/release_task` for text-only generation.
   - Use `task_type="text2music"`.
   - Use `thinking=true`.
   - Use `use_format=true` with the user's prompt as `prompt`.
   - Keep `lyrics="[Instrumental]"` for instrumental continuation unless we add an explicit lyrics field later.
   - Send `audio_duration` from New section seconds.
   - Send `bpm`, `key_scale`, and `time_signature` when known, with `time_signature` defaulting to `"4"`.
   - Send ACE-Step LM defaults explicitly: `lm_temperature=0.85`, `lm_cfg_scale=2.5`, `lm_top_p=0.9`, `lm_negative_prompt="NO USER INPUT"`.
   - Send generation defaults explicitly: `infer_method="ode"`, `use_tiled_decode=true`, `constrained_decoding=true`, `use_cot_caption=true`, `use_cot_language=true`, `allow_lm_batch=true`, `batch_size=1`.
   - Keep repaint controls out of text generation.

2. Verify model and LM initialization before submitting generation.
   - Call `/v1/init` with `init_llm=true`.
   - Require the response to confirm the selected DiT model and `llm_initialized=true` when available.
   - Fail clearly if the LM is unavailable, because `thinking=true` depends on it.

3. Add a deliberate fallback mode for diagnosis, not primary UI clutter.
   - Primary mode remains "generate a new section from the prompt".
   - Internally support switching between `format` and `sample` generation by config/advanced setting if needed.
   - `sample_mode` can override duration because ACE-Step's sample planner generates metadata, so it should not become the default until tested against user-selected durations.

4. Save exact ACE-Step request/debug artifacts beside each raw generation.
   - Write `ace-request.json` before submission.
   - Write `ace-release-response.json` after `/release_task`.
   - Write `ace-query-response-latest.json` on each poll and preserve the final response.
   - Keep existing task metadata from `/query_result`.
   - This lets us compare our call directly with ACE-Step examples and see whether ACE-Step reformatted duration, BPM, key, lyrics, or caption.

5. Improve surfaced errors for generation setup.
   - If the 5Hz LM is unavailable or init failed, fail clearly before generation instead of allowing a bad DiT-only request.
   - Include ACE-Step's response body in Autotransition status/logs when release/init/query fails.

6. Stop doing default-only scaffold work before text generation.
   - Do not build a source scaffold for the default `text2music` path.
   - Keep scaffold creation only for repaint/debug paths that actually send `src_audio`.
   - Keep source selection metadata so the selected point, context, and output timing are still trackable.

7. Treat raw output format deliberately.
   - Prefer ACE-Step's default `flac` for raw generation during diagnosis, then convert/stitch to the app output format as needed.
   - Record the requested raw format and final composite format in metadata.
   - Save the downloaded file with the extension matching the requested/returned ACE-Step audio format instead of always naming it `.wav`.
   - Keep `use_tiled_decode=true` explicit in text generation requests.
   - Leave ACE-Step's VAE decode server-side; do not add a local raw decode/re-encode step before saving the raw output.

8. Update tests around the ACE-Step request builder and generation route.
   - Assert text generation sends JSON, not form data.
   - Assert the ACE-Step example-aligned fields are present.
   - Assert `batch_size` remains `1`.
   - Assert raw request artifacts are written.
   - Assert the default text generation route does not create or depend on a scaffold.

## Affected Files

- `src/autotransition/models/acestep_api.py`
- `src/autotransition/models/acestep.py`
- `src/autotransition/pipeline/source_selection.py` if `time_signature` needs to move into the plan/config model
- `src/autotransition/config.py` if generation-mode defaults become central config
- `src/autotransition/ui/app.py` to avoid default scaffold work and record raw/final artifacts correctly
- `tests/` for ACE-Step API client behavior
- `README.md` or docs only if user-facing generation settings change

## Tradeoffs

- `use_format=true` requires the 5Hz LM. That is intentional: ACE-Step v1.5's documented quality path uses LM planning for prompt adherence. If LM init fails, the app should say so instead of producing garbage.
- `sample_mode=true` is tempting for prompt-only generation, but ACE-Step's code replaces duration/BPM/key with LM-generated metadata. Because Autotransition needs the user-selected New section seconds to matter, `use_format=true` is the safer first correction.
- Keeping `[Instrumental]` is consistent with ACE-Step's own instrumental handling, but we should expose lyrics later if users want vocal continuations.

## Risks

- ACE-Step may still generate poor short clips if the model expects longer musical structures. The request artifacts will make that visible, and the next adjustment would be an ACE-Step-native minimum duration or duration-auto mode rather than another invented stitching parameter.
- `use_format=true` may rewrite metadata. We will preserve the request and returned metadata so duration/key/BPM changes can be audited.
- If the installed 5Hz LM checkpoint is incomplete or unavailable, generation will now fail earlier and more loudly.

## Verification

- Run unit tests for the ACE-Step client/request construction.
- Generate one raw clip and inspect:
  - `data/generated/<id>/raw/ace-request.json`
  - ACE-Step result metadata
  - raw audio before stitching
- Confirm the UI results list still plays raw/composite outputs.

# Align REST Generation With Wan2GP ACE-Step Semantics

## Problem

Raw text-to-music output is still noisy/garbled even before stitching. A Wan2GP audit showed their working ACE-Step 1.5 path differs from Autotransition's REST request in conditioning semantics:

- Wan2GP switches the DiT instruction to the LM/audio-code instruction when LM audio codes are used.
- Wan2GP keeps lyrics and style/caption separate.
- Wan2GP uses explicit model metadata and LM settings instead of relying on implicit REST defaults.

## Approach

- Keep the user-selected ACE-Step model exactly as selected.
- Keep profile `default_inference_steps` unchanged, so base/SFT continue using their recommended defaults.
- Keep ACE-Step's normal `text2music` DiT instruction (`Fill the audio semantic mask...`). `thinking=true` controls LM audio-code generation; replacing the DiT instruction with the LM instruction can miscondition the diffusion pass.
- Send an explicit LM model path, preferring ACE-Step's 1.7B LM default for XL and non-XL profiles unless the user overrides it.
- Stop enabling `use_format` by default for text-to-music generation so ACE-Step does not rewrite the user's prompt before generation.
- Use ACE-Step's documented non-turbo baseline of 50 diffusion steps for base/SFT models.
- Keep debug JSON output so the exact request can be inspected after each run.

## Affected Files

- `src/autotransition/models/acestep_api.py`
- `src/autotransition/models/registry.py`
- `tests/test_acestep_api.py`
- `docs/ace-step-direct-generation.md`

## Risks

- ACE-Step REST may still not perfectly match Wan2GP's embedded pipeline because Wan2GP directly controls token/code generation internals.
- Disabling `use_format` may reduce automatic cleanup for weak prompts, but it avoids a hidden rewrite step while debugging raw generation quality.
- No-LM text-to-music without explicit `audio_code_string` is not a valid quality baseline; it bypasses the semantic audio-token path and may sound like static or random speech.

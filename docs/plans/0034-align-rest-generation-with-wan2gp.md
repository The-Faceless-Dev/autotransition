# Align REST Generation With Wan2GP ACE-Step Semantics

## Problem

Raw text-to-music output is still noisy/garbled even before stitching. Direct ACE-Step testing showed the working path depends on the normal text-to-music LM semantic-code flow:

- `thinking=true` must be enabled so ACE-Step generates semantic audio codes.
- The normal text-to-music DiT instruction must be preserved.
- Lyrics and style/caption should stay separate.
- Model metadata and LM settings should be explicit instead of relying on implicit REST defaults.

## Approach

- Default the app to `acestep-v15-xl-base`, matching the direct command that produced clean music, while still allowing users to select other ACE-Step models.
- Use profile `default_inference_steps` values from ACE-Step's documented recommendations.
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

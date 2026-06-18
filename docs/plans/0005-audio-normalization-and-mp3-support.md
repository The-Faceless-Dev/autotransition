# Audio Normalization and MP3 Support Plan

## Goal

Allow users to load MP3 files and other common audio formats, then automatically perform the conversions needed for preview and scaffold generation in the background.

The user should not need to manually convert files before using Autotransition.

## Requirements

1. Accept common source formats:
   - `.mp3`
   - `.wav`
   - `.flac`
   - `.ogg`
   - `.m4a`
2. Use ffmpeg through `pydub` for decoding.
3. Normalize internal scaffold-building output to a predictable format, initially WAV.
4. Preserve original source metadata.
5. Write conversion/normalization metadata so users can inspect what happened.
6. Surface clear UI logs for:
   - source loaded
   - format detected
   - conversion/normalization started
   - conversion/normalization finished
   - errors such as missing ffmpeg or unsupported codec

## Intended Behavior

For full-song selection:

```text
source.mp3
  -> probe via ffmpeg/pydub
  -> browser preview uses the original file when the browser supports it
  -> selected tail is decoded through ffmpeg/pydub
  -> scaffold is exported as WAV
```

For already-cut clips:

```text
clip.mp3
  -> decoded through ffmpeg/pydub
  -> tail + silence scaffold exported as WAV
```

The conversion should not change the source file. Outputs should be written under the configured scaffold/output folders.

## Backend Changes

Add an audio format policy layer:

- Supported input extensions.
- Default scaffold/export format.
- Format labels for UI.
- Validation helper with useful error messages.

Update audio helpers:

- Ensure probe reports source suffix/format.
- Ensure scaffold metadata records:
  - original source path
  - original extension
  - output audio format
  - whether ffmpeg decoding was used
  - scaffold path

The actual conversion happens as part of scaffold export:

- `AudioSegment.from_file(source_path)` decodes MP3 or other supported input.
- `scaffold.export(output_path, format="wav")` writes the normalized scaffold.

## UI Changes

- Make the source path placeholder mention MP3/WAV.
- Show detected format after load.
- Show output scaffold format.
- Add log lines explaining that MP3 is decoded and scaffold output is normalized to WAV.

## Proposed Files

- `src/autotransition/audio/formats.py`
  - Supported formats and validation helpers.
- `src/autotransition/audio/probe.py`
  - Add format info to `AudioProbe`.
- `src/autotransition/audio/scaffold.py`
  - Validate source format and log/raise useful errors.
- `src/autotransition/audio/selection.py`
  - Validate source format and export normalized WAV scaffold.
- `src/autotransition/ui/app.py`
  - Return format metadata and add log events.
- `src/autotransition/ui/static/index.html`
  - Update source placeholder/readouts.
- `src/autotransition/ui/static/app.js`
  - Display detected source/output formats.
- `tests/test_audio_formats.py`
  - Supported/unsupported format tests.
- `tests/test_ui_api.py`
  - Probe format metadata test.

## Tradeoffs

- WAV scaffolds are larger than compressed formats, but they are predictable and model-friendly.
- Browser preview can use original MP3 directly, while backend generation uses ffmpeg decoding.
- Real background job infrastructure is not necessary yet because decoding/export happens during scaffold creation, but logs should make the process visible.

## Risks

- ffmpeg must be available for MP3 and many compressed formats.
- Some files may have a supported extension but unsupported codec.
- Large MP3 files can take time to decode.

## Validation

- Unit-test supported extension detection.
- Unit-test unsupported extension errors.
- API-test probe response includes source format.
- Scaffold tests should confirm MP3-like supported paths are accepted by validation.
- Manual test with a real MP3 source when available.

## Approval Needed

Implementation should wait until this plan is approved or revised.

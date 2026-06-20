# ACE-Step Direct Generation Test

Run these commands from the Linux/container shell while the ACE-Step API is running on `127.0.0.1:8001`.

## 1. Submit Generation

```bash
curl -sS -X POST http://127.0.0.1:8001/release_task -H "Content-Type: application/json" -d '{"task_type":"text2music","model":"acestep-v15-xl-base","prompt":"suspenseful cinematic horror theme, dark ambient strings, low percussion, tense atmosphere, instrumental","lyrics":"[Instrumental]","audio_duration":30,"audio_format":"flac","thinking":true,"use_format":false,"bpm":120,"key_scale":"C minor","time_signature":"4","inference_steps":50,"guidance_scale":7.0,"shift":3.0,"batch_size":1,"lm_model_path":"acestep-5Hz-lm-1.7B","lm_temperature":0.85,"lm_cfg_scale":2.5,"lm_top_p":0.9,"lm_negative_prompt":"NO USER INPUT"}'
```

Copy the returned `task_id`.

## 2. Query Result

Replace `PASTE_TASK_ID_HERE` with the `task_id`.

```bash
curl -sS -X POST http://127.0.0.1:8001/query_result -H "Content-Type: application/json" -d '{"task_id_list":["PASTE_TASK_ID_HERE"]}'
```

Run that query again until the response includes a `file` value.

## 3. Download Audio

Replace `PASTE_RETURNED_AUDIO_PATH_HERE` with the returned `file` path, or the decoded `path` inside `/v1/audio?path=...`.

```bash
curl -L "http://127.0.0.1:8001/v1/audio?path=PASTE_RETURNED_AUDIO_PATH_HERE" -o ace-direct.flac
```

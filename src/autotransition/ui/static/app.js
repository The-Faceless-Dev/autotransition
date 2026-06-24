const state = {
  presets: [],
  models: [],
  selectedPreset: null,
  selectedModel: null,
  sourceProbe: null,
  toastTimer: null,
  generationPollTimer: null,
  isGenerating: false,
  advancedDirty: false,
  generatedResults: [],
  musicResults: [],
  extractionTracks: [],
  extractionResults: [],
  extractSourceProbe: null,
};

const el = {
  transitionTabButton: document.querySelector("#transitionTabButton"),
  extractionTabButton: document.querySelector("#extractionTabButton"),
  musicTabButton: document.querySelector("#musicTabButton"),
  transitionPage: document.querySelector("#transitionPage"),
  extractionPage: document.querySelector("#extractionPage"),
  musicPage: document.querySelector("#musicPage"),
  ffmpegBadge: document.querySelector("#ffmpegBadge"),
  modelCountBadge: document.querySelector("#modelCountBadge"),
  runtimeBadge: document.querySelector("#runtimeBadge"),
  sourceState: document.querySelector("#sourceState"),
  actionState: document.querySelector("#actionState"),
  systemState: document.querySelector("#systemState"),
  runtimeState: document.querySelector("#runtimeState"),
  modelState: document.querySelector("#modelState"),
  promptSummary: document.querySelector("#promptSummary"),
  captionInput: document.querySelector("#captionInput"),
  sourcePath: document.querySelector("#sourcePath"),
  sourceFile: document.querySelector("#sourceFile"),
  selectedFileName: document.querySelector("#selectedFileName"),
  loadSourceButton: document.querySelector("#loadSourceButton"),
  sourceDuration: document.querySelector("#sourceDuration"),
  sourceFormatReadout: document.querySelector("#sourceFormatReadout"),
  outputFormatReadout: document.querySelector("#outputFormatReadout"),
  sourceAudio: document.querySelector("#sourceAudio"),
  currentTimeReadout: document.querySelector("#currentTimeReadout"),
  continuationReadout: document.querySelector("#continuationReadout"),
  continuationSlider: document.querySelector("#continuationSlider"),
  contextRange: document.querySelector("#contextRange"),
  futureRange: document.querySelector("#futureRange"),
  outputDir: document.querySelector("#outputDir"),
  contextSeconds: document.querySelector("#contextSeconds"),
  newSeconds: document.querySelector("#newSeconds"),
  repaintOverlapSeconds: document.querySelector("#repaintOverlapSeconds"),
  bpmInput: document.querySelector("#bpmInput"),
  keyInput: document.querySelector("#keyInput"),
  seedInput: document.querySelector("#seedInput"),
  inferenceSteps: document.querySelector("#inferenceSteps"),
  guidanceScale: document.querySelector("#guidanceScale"),
  shiftValue: document.querySelector("#shiftValue"),
  repaintStrength: document.querySelector("#repaintStrength"),
  repaintMode: document.querySelector("#repaintMode"),
  repaintLatentCrossfadeFrames: document.querySelector("#repaintLatentCrossfadeFrames"),
  repaintWavCrossfadeSec: document.querySelector("#repaintWavCrossfadeSec"),
  resetAceDefaultsButton: document.querySelector("#resetAceDefaultsButton"),
  generateButton: document.querySelector("#generateButton"),
  generationActivity: document.querySelector("#generationActivity"),
  refreshButton: document.querySelector("#refreshButton"),
  generatedList: document.querySelector("#generatedList"),
  modelDetails: document.querySelector("#modelDetails"),
  autoInstallModel: document.querySelector("#autoInstallModel"),
  installModelButton: document.querySelector("#installModelButton"),
  systemStatus: document.querySelector("#systemStatus"),
  runtimeDetails: document.querySelector("#runtimeDetails"),
  copyRuntimeCommandButton: document.querySelector("#copyRuntimeCommandButton"),
  logList: document.querySelector("#logList"),
  extractSourceState: document.querySelector("#extractSourceState"),
  extractSourceFile: document.querySelector("#extractSourceFile"),
  extractSelectedFileName: document.querySelector("#extractSelectedFileName"),
  extractSourcePath: document.querySelector("#extractSourcePath"),
  loadExtractSourceButton: document.querySelector("#loadExtractSourceButton"),
  extractSourceDuration: document.querySelector("#extractSourceDuration"),
  extractSourceAudio: document.querySelector("#extractSourceAudio"),
  extractSourceFormatReadout: document.querySelector("#extractSourceFormatReadout"),
  extractTrackSelect: document.querySelector("#extractTrackSelect"),
  extractLabelInput: document.querySelector("#extractLabelInput"),
  extractOutputFormat: document.querySelector("#extractOutputFormat"),
  extractSeedInput: document.querySelector("#extractSeedInput"),
  extractInferenceSteps: document.querySelector("#extractInferenceSteps"),
  extractGuidanceScale: document.querySelector("#extractGuidanceScale"),
  extractShift: document.querySelector("#extractShift"),
  extractInstruction: document.querySelector("#extractInstruction"),
  runExtractionButton: document.querySelector("#runExtractionButton"),
  refreshExtractionsButton: document.querySelector("#refreshExtractionsButton"),
  extractActionState: document.querySelector("#extractActionState"),
  mergeLabelInput: document.querySelector("#mergeLabelInput"),
  mergeOutputFormat: document.querySelector("#mergeOutputFormat"),
  mergeExtractionsButton: document.querySelector("#mergeExtractionsButton"),
  extractionActivity: document.querySelector("#extractionActivity"),
  extractionList: document.querySelector("#extractionList"),
  extractRuntimeState: document.querySelector("#extractRuntimeState"),
  extractLogList: document.querySelector("#extractLogList"),
  musicActionState: document.querySelector("#musicActionState"),
  musicModelState: document.querySelector("#musicModelState"),
  musicPrompt: document.querySelector("#musicPrompt"),
  musicLabelInput: document.querySelector("#musicLabelInput"),
  musicModelSelect: document.querySelector("#musicModelSelect"),
  musicOutputFormat: document.querySelector("#musicOutputFormat"),
  musicDuration: document.querySelector("#musicDuration"),
  musicSeed: document.querySelector("#musicSeed"),
  musicInferenceSteps: document.querySelector("#musicInferenceSteps"),
  musicGuidanceScale: document.querySelector("#musicGuidanceScale"),
  musicShift: document.querySelector("#musicShift"),
  musicInferMethod: document.querySelector("#musicInferMethod"),
  musicUseTiledDecode: document.querySelector("#musicUseTiledDecode"),
  musicDcwEnabled: document.querySelector("#musicDcwEnabled"),
  musicVelocityNormThreshold: document.querySelector("#musicVelocityNormThreshold"),
  musicVelocityEmaFactor: document.querySelector("#musicVelocityEmaFactor"),
  runMusicButton: document.querySelector("#runMusicButton"),
  refreshMusicButton: document.querySelector("#refreshMusicButton"),
  musicActivity: document.querySelector("#musicActivity"),
  musicList: document.querySelector("#musicList"),
  musicLogList: document.querySelector("#musicLogList"),
  toast: document.querySelector("#toast"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body && body.detail ? body.detail : `Request failed: ${response.status}`;
    throw new Error(detail);
  }
  return body;
}

function setPill(node, text, tone = "neutral") {
  node.textContent = text;
  node.className = node.className
    .split(" ")
    .filter((part) => !["ok", "warn", "error", "neutral"].includes(part))
    .join(" ");
  node.classList.add(tone);
}

function showToast(message) {
  el.toast.textContent = message;
  el.toast.classList.add("visible");
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => {
    el.toast.classList.remove("visible");
  }, 3600);
}

function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const whole = Math.floor(seconds);
  const mins = Math.floor(whole / 60);
  const secs = String(whole % 60).padStart(2, "0");
  return `${mins}:${secs}`;
}

function option(label, value) {
  const item = document.createElement("option");
  item.value = value;
  item.textContent = label;
  return item;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function applyPreset(preset) {
  state.selectedPreset = preset;
  if (!el.captionInput.value.trim()) el.captionInput.value = preset.caption;
  el.contextSeconds.value = preset.config.context_seconds;
  el.newSeconds.value = preset.config.new_section_seconds;
  el.repaintOverlapSeconds.value = preset.config.repaint_overlap_seconds;
  if (!el.bpmInput.value) el.bpmInput.value = "120";
  updateSelectionReadout();
}

function renderPresets() {
  if (state.presets.length) {
    applyPreset(state.presets[0]);
  }
}

function modelTone(model) {
  return model.status.state === "ready" ? "ok" : "warn";
}

function renderModels() {
  if (state.models.length) {
    const preferred =
      state.models.find((model) => model.slug === "acestep-v15-turbo" && model.status.state === "ready") ||
      state.models.find((model) => model.slug === "acestep-v15-turbo") ||
      state.models.find((model) => model.status.state === "ready") ||
      state.models[0];
    applyModel(preferred);
  }
}

function applyModel(model) {
  state.selectedModel = model;
  setPill(el.modelState, "Locked", "ok");
  el.modelDetails.innerHTML = [
    "<strong>ACE-Step XL Turbo runtime</strong>",
    "Generation uses the active ACE-Step runtime path.",
    "Model selection is locked in this workflow.",
    `Runtime profile shown: ${model.display_name}`,
    `Status: ${model.status.state.replace("_", " ")}`,
  ].join("<br>");
  el.autoInstallModel.checked = false;
  el.autoInstallModel.disabled = true;
  el.installModelButton.disabled = true;
  if (!state.advancedDirty) {
    applyAceDefaults(model);
  }
}

function setNumeric(node, value) {
  node.value = value === null || value === undefined ? "" : String(value);
}

function applyAceDefaults(model) {
  const defaults = model ? { ...(model.generation_defaults || {}), ...(model.repaint_defaults || {}) } : {};
  setNumeric(el.inferenceSteps, defaults.inference_steps);
  setNumeric(el.guidanceScale, defaults.guidance_scale);
  setNumeric(el.shiftValue, defaults.shift);
  setNumeric(el.repaintStrength, defaults.repaint_strength);
  el.repaintMode.value = defaults.repaint_mode || "balanced";
  setNumeric(el.repaintLatentCrossfadeFrames, defaults.repaint_latent_crossfade_frames);
  setNumeric(el.repaintWavCrossfadeSec, defaults.repaint_wav_crossfade_sec);
  state.advancedDirty = false;
}

function renderStatus(status) {
  setPill(el.ffmpegBadge, status.ffmpeg_available ? "ffmpeg ready" : "ffmpeg missing", status.ffmpeg_available ? "ok" : "error");
  setPill(el.modelCountBadge, `${status.repaint_model_count} ACE models`, "ok");
  setPill(el.runtimeBadge, `Python ${status.python_version}`, "neutral");
  setPill(el.systemState, "Live", "ok");
  el.systemStatus.innerHTML = `
    <dt>Python</dt><dd>${status.python_version}</dd>
    <dt>ffmpeg</dt><dd>${status.ffmpeg_path || "Not found"}</dd>
    <dt>Inputs</dt><dd>${(status.supported_input_formats || []).join(", ")}</dd>
    <dt>Output</dt><dd>${String(status.default_scaffold_format || "wav").toUpperCase()} scaffold</dd>
    <dt>Models</dt><dd>${status.models_dir}</dd>
    <dt>Folder</dt><dd>${status.cwd}</dd>
  `;
  el.outputFormatReadout.textContent = `Output scaffold: ${String(status.default_scaffold_format || "wav").toUpperCase()}`;
}

function renderRuntime(runtime) {
  const tone = runtime.api_running ? "ok" : runtime.installed ? "warn" : "error";
  setPill(el.runtimeState, runtime.api_running ? "API running" : runtime.installed ? "Installed" : "Not installed", tone);
  el.runtimeDetails.innerHTML = [
    `<strong>${runtime.message}</strong>`,
    `Install: ${runtime.install_dir}`,
    `API: ${runtime.api_url}`,
    `uv: ${runtime.uv_available ? "available" : "missing"}`,
    `git: ${runtime.git_available ? "available" : "missing"}`,
    `Setup: ${runtime.simple_setup_command}`,
    `Start: ${runtime.simple_start_command}`,
  ].join("<br>");
  el.copyRuntimeCommandButton.dataset.command = `${runtime.simple_setup_command}\n${runtime.simple_start_command}`;
}

function renderLogs(logs) {
  renderLogList(el.logList, logs);
  renderLogList(el.extractLogList, logs);
  renderLogList(el.musicLogList, logs);
}

function renderLogList(node, logs) {
  node.replaceChildren();
  logs.forEach((entry) => {
    const item = document.createElement("li");
    const level = document.createElement("span");
    level.className = `level ${entry.level}`;
    level.textContent = entry.level;
    const text = document.createTextNode(`${entry.timestamp} ${entry.message}`);
    item.append(level, text);
    node.appendChild(item);
  });
}

function setActivePage(page) {
  el.transitionPage.classList.toggle("active", page === "transition");
  el.extractionPage.classList.toggle("active", page === "extraction");
  el.musicPage.classList.toggle("active", page === "music");
  el.transitionTabButton.classList.toggle("active", page === "transition");
  el.extractionTabButton.classList.toggle("active", page === "extraction");
  el.musicTabButton.classList.toggle("active", page === "music");
}

function applyMusicModelDefaults() {
  const base = el.musicModelSelect.value === "acestep-v15-base";
  el.musicInferenceSteps.value = base ? "80" : "8";
  el.musicGuidanceScale.value = base ? "0.6" : "1";
  el.musicShift.value = base ? "1" : "3";
  el.musicInferMethod.value = base ? "sde" : "ode";
  el.musicUseTiledDecode.checked = true;
  el.musicDcwEnabled.checked = false;
  el.musicVelocityNormThreshold.value = "0";
  el.musicVelocityEmaFactor.value = "0";
  setPill(el.musicModelState, base ? "Base" : "Turbo", "neutral");
}

function activityTone(phase) {
  if (phase === "error") return "error";
  if (["downloading", "initializing", "generating"].includes(phase)) return "warn";
  if (phase === "ready" || phase === "complete") return "ok";
  return "neutral";
}

function activityLabel(activity) {
  const phase = activity.phase || "idle";
  if (phase === "downloading") return "Downloading";
  if (phase === "initializing") return "Initializing";
  if (phase === "generating") return "Generating";
  if (phase === "error") return "Runtime error";
  if (phase === "ready") return "Runtime ready";
  return "Waiting";
}

function renderActivity(activity) {
  const message = activity.message || "No ACE-Step activity yet.";
  const detail = activity.detail ? `<br>${activity.detail}` : "";
  el.generationActivity.innerHTML = `<strong>${activityLabel(activity)}</strong><br>${message}${detail}`;
  if (state.isGenerating) {
    setPill(el.actionState, activityLabel(activity), activityTone(activity.phase));
  }
}

async function refreshActivity() {
  const activity = await api("/api/runtime/activity");
  renderActivity(activity);
  return activity;
}

function startGenerationPolling() {
  stopGenerationPolling();
  state.isGenerating = true;
  refreshActivity().catch(() => {});
  state.generationPollTimer = window.setInterval(() => {
    Promise.all([refreshActivity(), refreshLogs()]).catch(() => {});
  }, 2500);
}

function stopGenerationPolling() {
  state.isGenerating = false;
  if (state.generationPollTimer) {
    window.clearInterval(state.generationPollTimer);
    state.generationPollTimer = null;
  }
}

function renderGeneratedList() {
  el.generatedList.replaceChildren();
  if (!state.generatedResults.length) {
    const empty = document.createElement("div");
    empty.className = "empty-result";
    empty.textContent = "No generated audio yet.";
    el.generatedList.appendChild(empty);
    return;
  }

  state.generatedResults.forEach((item, index) => {
    const { result, plan } = item;
    const row = document.createElement("article");
    row.className = "generated-item";
    const outputPath = result.generated_audio_path || "";
    const audio = outputPath
      ? `<audio controls preload="metadata" src="/api/audio?path=${encodeURIComponent(outputPath)}"></audio>`
      : `<div class="empty-result">No playable audio for this result.</div>`;
    row.innerHTML = `
      <div class="generated-title">
        <strong>${index === 0 ? "Latest" : "Result"} - ${result.status}</strong>
        <span>${result.model_slug || "model"}</span>
      </div>
      ${audio}
      <div class="button-row generated-actions">
        <button class="secondary-button use-source-button" type="button" ${outputPath ? "" : "disabled"}>Use as Source</button>
      </div>
      <dl class="path-list">
        <dt>Message</dt><dd>${result.message}</dd>
        <dt>Mode</dt><dd>${plan.generation_region === "repaint_existing" ? "Repaint existing audio" : "Extend after marker"}</dd>
        <dt>Source</dt><dd>${formatTime(plan.tail_start_seconds)} to ${formatTime(plan.tail_end_seconds)}</dd>
        <dt>Generated</dt><dd>${Number(plan.new_section_seconds || 0).toFixed(1)}s</dd>
        <dt>Repaint before</dt><dd>${Number(plan.repaint_overlap_seconds || 0).toFixed(1)}s</dd>
        <dt>Output</dt><dd>${outputPath || "None"}</dd>
        <dt>Metadata</dt><dd>${result.generated_metadata_path || result.scaffold_metadata_path}</dd>
        <dt>Prompt</dt><dd>${plan.caption}</dd>
      </dl>
    `;
    const useSourceButton = row.querySelector(".use-source-button");
    if (useSourceButton && outputPath) {
      useSourceButton.addEventListener("click", () => useGeneratedAsSource(outputPath));
    }
    el.generatedList.appendChild(row);
  });
}

function renderExtractionTracks() {
  el.extractTrackSelect.replaceChildren();
  state.extractionTracks.forEach((track) => {
    el.extractTrackSelect.appendChild(option(track.replace("_", " "), track));
  });
  if (state.extractionTracks.includes("vocals")) {
    el.extractTrackSelect.value = "vocals";
  }
}

function renderExtractionList() {
  el.extractionList.replaceChildren();
  if (!state.extractionResults.length) {
    const empty = document.createElement("div");
    empty.className = "empty-result";
    empty.textContent = "No extractions yet.";
    el.extractionList.appendChild(empty);
    return;
  }

  state.extractionResults.forEach((item, index) => {
    const row = document.createElement("article");
    row.className = "generated-item";
    row.dataset.extractionId = item.extraction_id || "";
    const outputPath = item.generated_audio_path || "";
    const canMerge = item.type !== "base_test" && item.status === "complete" && outputPath;
    const itemType = item.type === "base_test" ? "Base test" : item.type === "merge" ? "Merge" : "Extraction";
    const sourceLabel = item.type === "base_test" ? "Prompt" : "Source";
    const sourceValue = item.type === "base_test" ? item.prompt || "" : item.source_path || "";
    const displayLabel = item.label || item.track_name || itemType;
    const audio = outputPath
      ? `<audio controls preload="metadata" src="/api/extractions/audio?path=${encodeURIComponent(outputPath)}"></audio>`
      : `<div class="empty-result">No playable audio for this extraction.</div>`;
    const mergeControl = canMerge
      ? `<label class="merge-select"><input class="merge-select-input" type="checkbox" value="${escapeHtml(item.extraction_id)}" /> Select for merge</label>`
      : "";
    const renameControl = item.type !== "base_test"
      ? `
        <div class="rename-row">
          <input class="rename-input" type="text" value="${escapeHtml(displayLabel)}" aria-label="Extraction label" />
          <button class="rename-button secondary-button" type="button">Save Label</button>
        </div>
      `
      : "";
    row.innerHTML = `
      <div class="generated-title">
        <strong>${index === 0 ? "Latest" : itemType} - ${escapeHtml(item.status)}</strong>
        <span>${escapeHtml(displayLabel)}</span>
      </div>
      ${mergeControl}
      ${renameControl}
      ${audio}
      <dl class="path-list">
        <dt>Type</dt><dd>${escapeHtml(itemType)}</dd>
        <dt>Message</dt><dd>${escapeHtml(item.message || "")}</dd>
        <dt>${escapeHtml(sourceLabel)}</dt><dd>${escapeHtml(sourceValue)}</dd>
        <dt>Track</dt><dd>${escapeHtml(item.track_name || "")}</dd>
        <dt>Output</dt><dd>${escapeHtml(outputPath || "None")}</dd>
        <dt>Metadata</dt><dd>${escapeHtml(item.metadata_path || "")}</dd>
      </dl>
    `;
    const renameButton = row.querySelector(".rename-button");
    if (renameButton) {
      renameButton.addEventListener("click", () => renameExtraction(item.extraction_id, row));
    }
    el.extractionList.appendChild(row);
  });
}

function renderMusicList() {
  el.musicList.replaceChildren();
  if (!state.musicResults.length) {
    const empty = document.createElement("div");
    empty.className = "empty-result";
    empty.textContent = "No music generations yet.";
    el.musicList.appendChild(empty);
    return;
  }

  state.musicResults.forEach((item, index) => {
    const row = document.createElement("article");
    row.className = "generated-item";
    const outputPath = item.generated_audio_path || "";
    const audio = outputPath
      ? `<audio controls preload="metadata" src="/api/music-generations/audio?path=${encodeURIComponent(outputPath)}"></audio>`
      : `<div class="empty-result">No playable audio for this generation.</div>`;
    row.innerHTML = `
      <div class="generated-title">
        <strong>${index === 0 ? "Latest" : "Music"} - ${escapeHtml(item.status)}</strong>
        <span>${escapeHtml(item.label || item.model || "music")}</span>
      </div>
      ${audio}
      <dl class="path-list">
        <dt>Message</dt><dd>${escapeHtml(item.message || "")}</dd>
        <dt>Model</dt><dd>${escapeHtml(item.model || "")}</dd>
        <dt>Prompt</dt><dd>${escapeHtml(item.prompt || "")}</dd>
        <dt>Output</dt><dd>${escapeHtml(outputPath || "None")}</dd>
        <dt>Metadata</dt><dd>${escapeHtml(item.metadata_path || "")}</dd>
      </dl>
    `;
    el.musicList.appendChild(row);
  });
}

async function renameExtraction(extractionId, row) {
  const input = row.querySelector(".rename-input");
  const label = input ? input.value.trim() : "";
  if (!label) {
    showToast("Enter a label");
    return;
  }
  try {
    const response = await api(`/api/extractions/${encodeURIComponent(extractionId)}/rename`, {
      method: "POST",
      body: JSON.stringify({ label }),
    });
    const index = state.extractionResults.findIndex((item) => item.extraction_id === extractionId);
    if (index >= 0) state.extractionResults[index] = response.extraction;
    renderExtractionList();
    showToast("Label saved");
  } catch (error) {
    showToast(error.message);
  }
}

async function mergeSelectedExtractions() {
  const ids = Array.from(el.extractionList.querySelectorAll(".merge-select-input:checked")).map((node) => node.value);
  const label = el.mergeLabelInput.value.trim();
  if (ids.length < 2) {
    showToast("Select at least two extraction items");
    return;
  }
  if (!label) {
    showToast("Enter a merge label");
    return;
  }
  el.mergeExtractionsButton.disabled = true;
  el.extractionActivity.innerHTML = "<strong>Merging</strong><br>Combining selected extraction outputs.";
  try {
    const response = await api("/api/extractions/merge", {
      method: "POST",
      body: JSON.stringify({
        extraction_ids: ids,
        label,
        output_format: el.mergeOutputFormat.value,
      }),
    });
    state.extractionResults.unshift(response.extraction);
    state.extractionResults = state.extractionResults.slice(0, 24);
    renderExtractionList();
    el.extractionActivity.innerHTML = "<strong>Complete</strong><br>Merge finished.";
    showToast("Merge complete");
  } catch (error) {
    el.extractionActivity.innerHTML = `<strong>Error</strong><br>${escapeHtml(error.message)}`;
    showToast(error.message);
  } finally {
    el.mergeExtractionsButton.disabled = false;
    refreshLogs();
  }
}

async function refreshExtractions() {
  state.extractionResults = await api("/api/extractions");
  renderExtractionList();
}

async function refreshMusicGenerations() {
  state.musicResults = await api("/api/music-generations");
  renderMusicList();
}

function addGeneratedResult(result, plan) {
  state.generatedResults.unshift({ result, plan });
  state.generatedResults = state.generatedResults.slice(0, 12);
  renderGeneratedList();
}

async function loadAll() {
  const [status, runtime, presets, models, tracks, extractions, musicGenerations, logs] = await Promise.all([
    api("/api/status"),
    api("/api/runtime/status"),
    api("/api/presets"),
    api("/api/models"),
    api("/api/extractions/tracks"),
    api("/api/extractions"),
    api("/api/music-generations"),
    api("/api/logs"),
  ]);
  state.presets = presets;
  state.models = models;
  state.extractionTracks = tracks;
  state.extractionResults = extractions;
  state.musicResults = musicGenerations;
  renderStatus(status);
  renderRuntime(runtime);
  renderPresets();
  renderModels();
  renderExtractionTracks();
  renderExtractionList();
  applyMusicModelDefaults();
  renderMusicList();
  renderLogs(logs);
}

function numericValue(node) {
  return node.value === "" ? null : Number(node.value);
}

function currentSettings() {
  return {
    contextSeconds: numericValue(el.contextSeconds),
    newSeconds: numericValue(el.newSeconds),
    repaintOverlapSeconds: numericValue(el.repaintOverlapSeconds),
  };
}

function updateSelectionReadout() {
  const continuation = Number(el.continuationSlider.value || 0);
  const settings = currentSettings();
  const context = settings.contextSeconds || 0;
  const future = settings.newSeconds || 0;
  const repaintBefore = settings.repaintOverlapSeconds || 0;
  const tail = context;
  const start = continuation - tail;
  el.continuationReadout.textContent = `Continue at ${formatTime(continuation)}`;
  el.futureRange.textContent = `Generate new section: ${future.toFixed(1)}s`;
  if (!state.sourceProbe) {
    el.contextRange.textContent = "Context not selected";
    return;
  }
  if (start < 0) {
    el.contextRange.textContent = `${tail.toFixed(1)}s source context needs marker at ${formatTime(tail)} or later`;
    setPill(el.sourceState, "Marker too early", "warn");
    return;
  }
  el.contextRange.textContent = `Source context: ${formatTime(start)} to ${formatTime(continuation)} (${tail.toFixed(1)}s), repaint starts ${repaintBefore.toFixed(1)}s before marker`;
  setPill(el.sourceState, "Source loaded", "ok");
}

function aceStepSettingsPayload() {
  return {
    inference_steps: numericValue(el.inferenceSteps),
    guidance_scale: numericValue(el.guidanceScale),
    shift: numericValue(el.shiftValue),
    repaint_strength: numericValue(el.repaintStrength),
    repaint_mode: el.repaintMode.value || null,
    repaint_latent_crossfade_frames: numericValue(el.repaintLatentCrossfadeFrames),
    repaint_wav_crossfade_sec: numericValue(el.repaintWavCrossfadeSec),
  };
}

async function loadProbeIntoPlayer(sourcePath, probe) {
  state.sourceProbe = probe;
  el.sourcePath.value = sourcePath;
  el.sourceAudio.src = `/api/source/audio?path=${encodeURIComponent(sourcePath)}`;
  el.continuationSlider.max = String(probe.duration_seconds);
  el.continuationSlider.value = String(Math.max(0, probe.duration_seconds - 1));
  el.sourceDuration.textContent = `Duration ${formatTime(probe.duration_seconds)}`;
  el.sourceFormatReadout.textContent = `Source format: ${probe.source_format}; decoded in background`;
  setPill(el.sourceState, "Source loaded", "ok");
  updateSelectionReadout();
}

async function useGeneratedAsSource(sourcePath) {
  setPill(el.sourceState, "Loading", "warn");
  try {
    const probe = await api("/api/source/probe", {
      method: "POST",
      body: JSON.stringify({ source_path: sourcePath }),
    });
    await loadProbeIntoPlayer(sourcePath, probe);
    el.selectedFileName.textContent = "Generated output";
    showToast("Generated output loaded as source");
  } catch (error) {
    setPill(el.sourceState, "Error", "error");
    showToast(error.message);
  } finally {
    refreshLogs();
  }
}

async function loadSource() {
  setPill(el.sourceState, "Loading", "warn");
  el.loadSourceButton.disabled = true;
  try {
    const sourcePath = el.sourcePath.value.trim();
    const probe = await api("/api/source/probe", {
      method: "POST",
      body: JSON.stringify({ source_path: sourcePath }),
    });
    await loadProbeIntoPlayer(sourcePath, probe);
    showToast("Source loaded");
  } catch (error) {
    state.sourceProbe = null;
    setPill(el.sourceState, "Error", "error");
    showToast(error.message);
  } finally {
    el.loadSourceButton.disabled = false;
    refreshLogs();
  }
}

async function uploadSourceFile() {
  const file = el.sourceFile.files && el.sourceFile.files[0];
  if (!file) return;

  setPill(el.sourceState, "Uploading", "warn");
  el.selectedFileName.textContent = file.name;
  el.loadSourceButton.disabled = true;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/source/upload", {
      method: "POST",
      body: formData,
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(body && body.detail ? body.detail : `Upload failed: ${response.status}`);
    }

    await loadProbeIntoPlayer(body.stored_path, body.probe);
    showToast("Audio file loaded");
  } catch (error) {
    state.sourceProbe = null;
    setPill(el.sourceState, "Error", "error");
    showToast(error.message);
  } finally {
    el.loadSourceButton.disabled = false;
    refreshLogs();
  }
}

async function loadExtractionProbeIntoPlayer(sourcePath, probe) {
  state.extractSourceProbe = probe;
  el.extractSourcePath.value = sourcePath;
  el.extractSourceAudio.src = `/api/extractions/audio?path=${encodeURIComponent(sourcePath)}`;
  el.extractSourceDuration.textContent = `Duration ${formatTime(probe.duration_seconds)}`;
  el.extractSourceFormatReadout.textContent = `Source format: ${probe.source_format}; full song extraction`;
  setPill(el.extractSourceState, "Source loaded", "ok");
}

async function loadExtractionSource() {
  setPill(el.extractSourceState, "Loading", "warn");
  el.loadExtractSourceButton.disabled = true;
  try {
    const sourcePath = el.extractSourcePath.value.trim();
    const probe = await api("/api/extractions/source/probe", {
      method: "POST",
      body: JSON.stringify({ source_path: sourcePath }),
    });
    await loadExtractionProbeIntoPlayer(sourcePath, probe);
    showToast("Extraction source loaded");
  } catch (error) {
    state.extractSourceProbe = null;
    setPill(el.extractSourceState, "Error", "error");
    showToast(error.message);
  } finally {
    el.loadExtractSourceButton.disabled = false;
    refreshLogs();
  }
}

async function uploadExtractionSourceFile() {
  const file = el.extractSourceFile.files && el.extractSourceFile.files[0];
  if (!file) return;

  setPill(el.extractSourceState, "Uploading", "warn");
  el.extractSelectedFileName.textContent = file.name;
  el.loadExtractSourceButton.disabled = true;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/extractions/source/upload", {
      method: "POST",
      body: formData,
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(body && body.detail ? body.detail : `Upload failed: ${response.status}`);
    }

    await loadExtractionProbeIntoPlayer(body.stored_path, body.probe);
    showToast("Extraction source loaded");
  } catch (error) {
    state.extractSourceProbe = null;
    setPill(el.extractSourceState, "Error", "error");
    showToast(error.message);
  } finally {
    el.loadExtractSourceButton.disabled = false;
    refreshLogs();
  }
}

async function runExtraction() {
  setPill(el.extractActionState, "Extracting", "warn");
  el.extractionActivity.innerHTML = "<strong>Starting</strong><br>Preparing ACE-Step extract request.";
  el.runExtractionButton.disabled = true;
  try {
    const response = await api("/api/extractions/run", {
      method: "POST",
      body: JSON.stringify({
        source_path: el.extractSourcePath.value.trim(),
        track_name: el.extractTrackSelect.value,
        label: el.extractLabelInput.value.trim() || null,
        output_format: el.extractOutputFormat.value,
        inference_steps: numericValue(el.extractInferenceSteps),
        guidance_scale: numericValue(el.extractGuidanceScale),
        shift: numericValue(el.extractShift),
        seed: numericValue(el.extractSeedInput),
        instruction: el.extractInstruction.value.trim() || null,
      }),
    });
    state.extractionResults.unshift(response.extraction);
    state.extractionResults = state.extractionResults.slice(0, 24);
    renderExtractionList();
    if (response.extraction.status === "complete") {
      setPill(el.extractActionState, "Complete", "ok");
      el.extractionActivity.innerHTML = "<strong>Complete</strong><br>Track extraction finished.";
    } else {
      setPill(el.extractActionState, "Failed", "error");
      el.extractionActivity.innerHTML = `<strong>Failed</strong><br>${response.extraction.message}`;
    }
    showToast(response.extraction.message);
  } catch (error) {
    setPill(el.extractActionState, "Error", "error");
    el.extractionActivity.innerHTML = `<strong>Error</strong><br>${error.message}`;
    showToast(error.message);
  } finally {
    el.runExtractionButton.disabled = false;
    refreshLogs();
  }
}

async function runMusicGeneration() {
  const prompt = el.musicPrompt.value.trim();
  if (!prompt) {
    showToast("Enter a music prompt");
    return;
  }
  setPill(el.musicActionState, "Generating", "warn");
  el.musicActivity.innerHTML = "<strong>Starting</strong><br>Preparing ACE-Step text-to-music request.";
  el.runMusicButton.disabled = true;
  try {
    const response = await api("/api/music-generations/run", {
      method: "POST",
      body: JSON.stringify({
        prompt,
        model: el.musicModelSelect.value,
        label: el.musicLabelInput.value.trim() || null,
        output_format: el.musicOutputFormat.value,
        audio_duration: numericValue(el.musicDuration),
        inference_steps: numericValue(el.musicInferenceSteps),
        guidance_scale: numericValue(el.musicGuidanceScale),
        shift: numericValue(el.musicShift),
        infer_method: el.musicInferMethod.value,
        use_tiled_decode: el.musicUseTiledDecode.checked,
        dcw_enabled: el.musicDcwEnabled.checked,
        velocity_norm_threshold: numericValue(el.musicVelocityNormThreshold),
        velocity_ema_factor: numericValue(el.musicVelocityEmaFactor),
        seed: numericValue(el.musicSeed),
      }),
    });
    state.musicResults.unshift(response.generation);
    state.musicResults = state.musicResults.slice(0, 24);
    renderMusicList();
    if (response.generation.status === "complete") {
      setPill(el.musicActionState, "Complete", "ok");
      el.musicActivity.innerHTML = "<strong>Complete</strong><br>Music generation finished.";
    } else {
      setPill(el.musicActionState, "Failed", "error");
      el.musicActivity.innerHTML = `<strong>Failed</strong><br>${escapeHtml(response.generation.message)}`;
    }
    showToast(response.generation.message);
  } catch (error) {
    setPill(el.musicActionState, "Error", "error");
    el.musicActivity.innerHTML = `<strong>Error</strong><br>${escapeHtml(error.message)}`;
    showToast(error.message);
  } finally {
    el.runMusicButton.disabled = false;
    refreshLogs();
  }
}

async function generateTransition() {
  setPill(el.actionState, "Generating", "warn");
  el.generationActivity.innerHTML = "<strong>Starting</strong><br>Preparing source selection and ACE-Step request.";
  el.generateButton.disabled = true;
  startGenerationPolling();
  try {
    const payload = {
      source_path: el.sourcePath.value.trim(),
      continuation_point_seconds: Number(el.continuationSlider.value || 0),
      generation_region: "extend",
      preset: state.selectedPreset ? state.selectedPreset.slug : "smooth-continuation",
      model_slug: state.selectedModel ? state.selectedModel.slug : "acestep-v15-turbo",
      auto_install: el.autoInstallModel.checked,
      caption: el.captionInput.value.trim(),
      output_dir: el.outputDir.value.trim() || null,
      context_seconds: numericValue(el.contextSeconds),
      repaint_overlap_seconds: numericValue(el.repaintOverlapSeconds),
      new_section_seconds: numericValue(el.newSeconds),
      bpm: numericValue(el.bpmInput),
      key: el.keyInput.value.trim() || null,
      seed: numericValue(el.seedInput),
      ace_step: aceStepSettingsPayload(),
    };
    const response = await api("/api/generate/from-selection", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    addGeneratedResult(response.result, response.plan);
    if (response.result.status === "complete") {
      setPill(el.actionState, "Complete", "ok");
      el.generationActivity.innerHTML = "<strong>Complete</strong><br>Transition generated.";
      showToast("Transition generated");
    } else {
      setPill(el.actionState, "Needs runtime", "warn");
      el.generationActivity.innerHTML = `<strong>Stopped</strong><br>${response.result.message}`;
      showToast(response.result.message);
    }
  } catch (error) {
    setPill(el.actionState, "Error", "error");
    el.generationActivity.innerHTML = `<strong>Error</strong><br>${error.message}`;
    showToast(error.message);
  } finally {
    stopGenerationPolling();
    el.generateButton.disabled = false;
    refreshLogs();
  }
}

async function installModel() {
  if (!state.selectedModel) return;
  setPill(el.modelState, "downloading", "warn");
  el.installModelButton.disabled = true;
  try {
    await api(`/api/models/${state.selectedModel.slug}/install`, { method: "POST" });
    showToast("Model installed");
    await refreshModels();
  } catch (error) {
    setPill(el.modelState, "failed", "error");
    showToast(error.message);
  } finally {
    refreshLogs();
  }
}

async function refreshModels() {
  state.models = await api("/api/models");
  const selectedSlug = state.selectedModel && state.selectedModel.slug;
  renderModels();
  const selected = state.models.find((model) => model.slug === selectedSlug);
  if (selected) {
    applyModel(selected);
  }
}

async function refreshLogs() {
  renderLogs(await api("/api/logs"));
}

async function refreshStatus() {
  renderStatus(await api("/api/status"));
  renderRuntime(await api("/api/runtime/status"));
  await refreshActivity();
  await refreshModels();
  await refreshLogs();
  showToast("Status refreshed");
}

el.transitionTabButton.addEventListener("click", () => setActivePage("transition"));
el.extractionTabButton.addEventListener("click", () => setActivePage("extraction"));
el.musicTabButton.addEventListener("click", () => setActivePage("music"));
el.generateButton.addEventListener("click", generateTransition);
el.loadSourceButton.addEventListener("click", loadSource);
el.sourceFile.addEventListener("change", uploadSourceFile);
el.loadExtractSourceButton.addEventListener("click", loadExtractionSource);
el.extractSourceFile.addEventListener("change", uploadExtractionSourceFile);
el.runExtractionButton.addEventListener("click", runExtraction);
el.mergeExtractionsButton.addEventListener("click", mergeSelectedExtractions);
el.runMusicButton.addEventListener("click", runMusicGeneration);
el.musicModelSelect.addEventListener("change", applyMusicModelDefaults);
el.refreshMusicButton.addEventListener("click", async () => {
  await refreshMusicGenerations();
  showToast("Music generations refreshed");
});
el.refreshExtractionsButton.addEventListener("click", async () => {
  await refreshExtractions();
  showToast("Extractions refreshed");
});
el.installModelButton.addEventListener("click", installModel);
el.refreshButton.addEventListener("click", refreshStatus);
el.copyRuntimeCommandButton.addEventListener("click", async () => {
  const command = el.copyRuntimeCommandButton.dataset.command || "";
  await navigator.clipboard.writeText(command);
  showToast("Setup commands copied");
});
el.continuationSlider.addEventListener("input", updateSelectionReadout);
el.sourceAudio.addEventListener("timeupdate", () => {
  el.currentTimeReadout.textContent = formatTime(el.sourceAudio.currentTime);
});
el.sourceAudio.addEventListener("seeked", () => {
  el.currentTimeReadout.textContent = formatTime(el.sourceAudio.currentTime);
});

[el.contextSeconds, el.newSeconds, el.repaintOverlapSeconds].forEach((node) => {
  node.addEventListener("input", updateSelectionReadout);
});

[
  el.inferenceSteps,
  el.guidanceScale,
  el.shiftValue,
  el.repaintStrength,
  el.repaintMode,
  el.repaintLatentCrossfadeFrames,
  el.repaintWavCrossfadeSec,
].forEach((node) => {
  node.addEventListener("input", () => {
    state.advancedDirty = true;
  });
  node.addEventListener("change", () => {
    state.advancedDirty = true;
  });
});

el.resetAceDefaultsButton.addEventListener("click", () => {
  if (state.selectedModel) {
    applyAceDefaults(state.selectedModel);
    showToast("ACE-Step defaults restored");
  }
});

loadAll().catch((error) => {
  setPill(el.actionState, "Error", "error");
  showToast(error.message);
});

window.setInterval(refreshLogs, 5000);

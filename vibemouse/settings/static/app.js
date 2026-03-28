const state = {
  config: null,
  status: null,
};

const defaultProfileSelect = document.querySelector("#default-profile");
const openclawProfileSelect = document.querySelector("#openclaw-profile");
const dictionaryBody = document.querySelector("#dictionary-body");
const backendStatus = document.querySelector("#backend-status");
const notice = document.querySelector("#notice");
const saveButton = document.querySelector("#save-config");
const refreshStatusButton = document.querySelector("#refresh-status");
const dictionaryForm = document.querySelector("#dictionary-form");

async function readJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(body.error || response.statusText);
  }
  return response.json();
}

function setNotice(message, type = "info") {
  notice.textContent = message;
  notice.dataset.type = type;
}

function renderProfiles() {
  defaultProfileSelect.value = state.config.profiles.default;
  openclawProfileSelect.value = state.config.profiles.openclaw;
}

function renderDictionary() {
  dictionaryBody.innerHTML = "";
  for (const [index, entry] of state.config.dictionary.entries()) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${escapeHtml(entry.term)}</td>
      <td>${escapeHtml(entry.phrases.join(", "))}</td>
      <td>${entry.weight}</td>
      <td>${escapeHtml(entry.scope)}</td>
      <td>${entry.enabled ? "Yes" : "No"}</td>
      <td><button class="button button-danger" data-remove-index="${index}" type="button">Remove</button></td>
    `;
    dictionaryBody.appendChild(row);
  }
}

function renderStatus() {
  backendStatus.innerHTML = "";
  for (const [target, details] of Object.entries(state.status.backends)) {
    const card = document.createElement("article");
    card.className = "status-card";
    card.innerHTML = `
      <p class="status-target">${escapeHtml(target)}</p>
      <h3>${escapeHtml(details.backend_id)}</h3>
      <p class="status-pill ${details.available ? "status-ok" : "status-fail"}">
        ${details.available ? "Available" : "Unavailable"}
      </p>
      <p class="status-reason">${escapeHtml(details.reason || "Ready")}</p>
    `;
    backendStatus.appendChild(card);
  }
}

function syncProfileState() {
  state.config.profiles.default = defaultProfileSelect.value;
  state.config.profiles.openclaw = openclawProfileSelect.value;
}

async function loadConfig() {
  state.config = await readJson("/api/config");
  renderProfiles();
  renderDictionary();
}

async function loadStatus() {
  state.status = await readJson("/api/status");
  renderStatus();
}

async function saveConfig() {
  syncProfileState();
  state.config = await readJson("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state.config),
  });
  renderProfiles();
  renderDictionary();
  try {
    await loadStatus();
  } catch (error) {
    setNotice(`Settings saved, but status refresh failed: ${error.message}`, "error");
    return;
  }
  setNotice("Settings saved.", "success");
}

function addDictionaryEntry(event) {
  event.preventDefault();
  const form = new FormData(dictionaryForm);
  const phrases = String(form.get("phrases") || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);

  if (!phrases.length) {
    setNotice("Add at least one phrase.", "error");
    return;
  }

  state.config.dictionary.push({
    term: String(form.get("term") || "").trim(),
    phrases,
    weight: Number(form.get("weight") || 8),
    scope: String(form.get("scope") || "both"),
    enabled: Boolean(form.get("enabled")),
  });
  dictionaryForm.reset();
  document.querySelector("#entry-weight").value = "8";
  document.querySelector("#entry-enabled").checked = true;
  renderDictionary();
  setNotice("Entry added locally. Save Settings to persist.", "info");
}

function removeDictionaryEntry(event) {
  const button = event.target.closest("[data-remove-index]");
  if (!button) {
    return;
  }
  const index = Number(button.dataset.removeIndex);
  state.config.dictionary.splice(index, 1);
  renderDictionary();
  setNotice("Entry removed locally. Save Settings to persist.", "info");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

saveButton.addEventListener("click", async () => {
  try {
    await saveConfig();
  } catch (error) {
    setNotice(error.message, "error");
  }
});

refreshStatusButton.addEventListener("click", async () => {
  try {
    await loadStatus();
    setNotice("Backend status refreshed.", "success");
  } catch (error) {
    setNotice(error.message, "error");
  }
});

dictionaryForm.addEventListener("submit", addDictionaryEntry);
dictionaryBody.addEventListener("click", removeDictionaryEntry);

Promise.all([loadConfig(), loadStatus()])
  .then(() => setNotice("Settings loaded.", "success"))
  .catch((error) => setNotice(error.message, "error"));

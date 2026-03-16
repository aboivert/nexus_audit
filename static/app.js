const SUPPORTED_FILES = [
  "agency.txt", "calendar.txt", "calendar_dates.txt",
  "routes.txt", "stop_times.txt", "stops.txt", "trips.txt",
];

let loadedFiles = [];

// ============================================================
// INIT
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  renderFileGrid();
  renderAuditSections();
  setupDropZone();
  setupFileInput();

  document.getElementById("btn-audit-all").addEventListener("click", () => runAudit("all"));
});


// ============================================================
// FILE GRID
// ============================================================

function renderFileGrid() {
  const grid = document.getElementById("file-grid");
  grid.innerHTML = "";
  SUPPORTED_FILES.forEach(name => {
    const badge = document.createElement("div");
    badge.className = "file-badge" + (loadedFiles.includes(name) ? " loaded" : "");
    badge.textContent = name.replace(".txt", "");
    badge.id = `badge-${name}`;
    grid.appendChild(badge);
  });
}

function updateFileGrid(files) {
  loadedFiles = files;
  SUPPORTED_FILES.forEach(name => {
    const badge = document.getElementById(`badge-${name}`);
    if (!badge) return;
    badge.className = "file-badge" + (files.includes(name) ? " loaded" : "");
  });
  updateSectionStates();
  document.getElementById("btn-audit-all").disabled = files.length === 0;
}


// ============================================================
// AUDIT SECTIONS
// ============================================================

function renderAuditSections() {
  const container = document.getElementById("audit-sections");
  container.innerHTML = "";
  SUPPORTED_FILES.forEach(name => {
    const section = document.createElement("div");
    section.className = "audit-section disabled";
    section.id = `section-${name}`;
    section.innerHTML = `
      <div class="section-header" onclick="toggleSection('${name}')">
        <h2>${name}</h2>
        <div class="section-header-right">
          <span class="section-score" id="score-${name}">—</span>
          <button class="btn-run" onclick="event.stopPropagation(); runAudit('${name}')">Lancer</button>
          <span class="chevron">▲</span>
        </div>
      </div>
      <div class="section-body" id="body-${name}"></div>
    `;
    container.appendChild(section);
  });
}

function updateSectionStates() {
  SUPPORTED_FILES.forEach(name => {
    const section = document.getElementById(`section-${name}`);
    if (!section) return;
    if (loadedFiles.includes(name)) {
      section.classList.remove("disabled");
    } else {
      section.classList.add("disabled");
    }
  });
}

function toggleSection(name) {
  const section = document.getElementById(`section-${name}`);
  if (section) section.classList.toggle("open");
}


// ============================================================
// UPLOAD
// ============================================================

function setupDropZone() {
  const zone = document.getElementById("drop-zone");

  zone.addEventListener("dragover", e => {
    e.preventDefault();
    zone.classList.add("dragover");
  });

  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));

  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("dragover");
    uploadFiles(e.dataTransfer.files);
  });
}

function setupFileInput() {
  const input = document.getElementById("file-input");
  input.addEventListener("change", () => uploadFiles(input.files));
}

function uploadFiles(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  fetch("/upload", { method: "POST", body: formData })
    .then(r => r.json())
    .then(data => updateFileGrid(data.files))
    .catch(err => console.error("Upload error:", err));
}


// ============================================================
// AUDIT
// ============================================================

function runAudit(target) {
  fetch("/audit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file: target }),
  })
    .then(r => r.json())
    .then(data => renderResults(data))
    .catch(err => console.error("Audit error:", err));
}

function renderResults(data) {
  for (const [filename, fileScore] of Object.entries(data)) {
    const body  = document.getElementById(`body-${filename}`);
    const score = document.getElementById(`score-${filename}`);
    const section = document.getElementById(`section-${filename}`);

    if (!body) continue;

    // Afficher le score global
    if (fileScore.error) {
      score.textContent = "erreur";
      body.innerHTML = `<p style="color:red;padding:16px">${fileScore.error}</p>`;
      continue;
    }

    score.textContent = `${fileScore.score?.toFixed(1) ?? "—"} / 100 · ${fileScore.grade ?? ""}`;

    // Rendre les catégories
    body.innerHTML = fileScore.categories.map(cat => renderCategory(cat)).join("");

    // Ouvrir la section automatiquement
    section.classList.add("open");
  }
}


// ============================================================
// RENDER CATEGORIES & CHECKS
// ============================================================

function renderCategory(cat) {
  const checks = cat.checks.map(c => renderCheck(c)).join("");
  return `
    <div class="category-block">
      <div class="category-header" onclick="this.parentElement.classList.toggle('open')">
        <span>${cat.category}</span>
        <span class="category-score">${cat.score?.toFixed(1) ?? "—"} / 100 · weight ${cat.total_weight}</span>
      </div>
      <div class="category-body">
        ${checks}
      </div>
    </div>
  `;
}

function renderCheck(check) {
  const score = check.score !== null && check.score !== undefined
    ? check.score.toFixed(1)
    : "—";

  const hasDetails = check.message || check.affected_ids?.length > 0 || check.details;
  const detailsId  = `details-${check.check_id.replace(/\./g, "-")}`;

  const detailsHtml = hasDetails ? `
    <div class="check-details" id="${detailsId}" style="display:none">
      ${check.message ? `<p class="detail-message">${check.message}</p>` : ""}
      ${check.affected_ids?.length > 0 ? `
        <p class="detail-label">Affected IDs (${check.affected_count}/${check.total_count})</p>
        <p class="detail-ids">${check.affected_ids.slice(0, 10).join(", ")}${check.affected_ids.length > 10 ? "..." : ""}</p>
      ` : ""}
      ${check.details ? `
        <p class="detail-label">Détails</p>
        <pre class="detail-json">${JSON.stringify(check.details, null, 2)}</pre>
      ` : ""}
    </div>
  ` : "";

  return `
    <div class="check-row">
      <span class="check-label">${check.label}</span>
      <span class="check-status ${check.status}">${check.status}</span>
      <div style="display:flex;align-items:center;gap:8px">
        <span class="check-score">${score}</span>
        ${hasDetails ? `<button class="btn-details" onclick="toggleDetails('${detailsId}')">détails</button>` : ""}
      </div>
    </div>
    ${detailsHtml}
  `;
}

function toggleDetails(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = el.style.display === "none" ? "block" : "none";
}
"use strict";

const state = { jobs: [], transcripts: [], selected: new Set(), viewer: null, current: "dashboard" };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const safeText = (value) => String(value ?? "");

async function api(endpoint, options = {}) {
  const response = await fetch(endpoint, { credentials: "same-origin", cache: "no-store", ...options });
  if (!response.ok) {
    let detail = "Error HTTP " + response.status;
    try { const data = await response.json(); detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail); } catch {}
    throw new Error(detail);
  }
  return response;
}
async function json(endpoint, options) { return (await api(endpoint, options)).json(); }
function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.style.display = "block";
  clearTimeout(toast.timeout);
  toast.timeout = setTimeout(() => { el.style.display = "none"; }, 5500);
}
function elt(tag, attrs = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") element.className = value;
    else if (key === "text") element.textContent = safeText(value);
    else if (key === "onClick") element.addEventListener("click", value);
    else if (key === "onChange") element.addEventListener("change", value);
    else element.setAttribute(key, value);
  }
  for (const child of children) {
    if (child != null) element.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return element;
}
function fmtStatus(status) {
  return ({ queued: "En cola", running: "Descargando", paused: "Pausado", completed: "Completado", failed: "Error", blocked: "Bloqueado", cancelled: "Cancelado" })[status] || status;
}
function switchTab(tab) {
  if (!["dashboard", "jobs", "library", "export"].includes(tab)) return;
  state.current = tab;
  $$(".panel").forEach(node => node.classList.toggle("current", node.id === tab));
  $$(".nav-btn").forEach(node => node.classList.toggle("active", node.dataset.tab === tab));
  $("#crumb").textContent = ({dashboard:"RESUMEN", jobs:"DESCARGAS", library:"BIBLIOTECA", export:"EXPORTACIONES"})[tab];
  if (tab === "library") refreshLibrary();
  window.scrollTo(0, 0);
}
function cardForJob(job) {
  const box = elt("div", { class:"job-card" });
  const main = elt("div", { class:"job-info" },
    elt("div", { class:"job-title", text:job.url }),
    elt("div", { class:"job-meta", text:`${job.processed} de ${job.total || "?"} procesados · ${job.downloaded} descargados · ${job.failed} fallidos` })
  );
  if (job.error) main.append(elt("div", { class:"job-meta", text: job.error.slice(0, 220) }));
  const side = elt("div", { class:"job-side" });
  side.append(elt("span", { class:"pill " + job.status, text:fmtStatus(job.status) }));
  const progress = elt("div", { class:"mini-progress" }, elt("span", {style:`width:${job.total ? Math.min(100, (job.processed / job.total) * 100) : 0}%` }));
  side.append(progress);
  const actions = elt("div", { class:"job-actions" });
  let names = [];
  if (["running", "queued"].includes(job.status)) names = [["pause", "Pausar"], ["cancel", "Cancelar"]];
  if (["paused", "blocked", "failed"].includes(job.status)) names = [["resume", "Reanudar"], ["cancel", "Cancelar"]];
  for (const [action, label] of names) {
    actions.append(elt("button", { text:label, onClick: async () => {
      try { await json(`/api/jobs/${job.id}/${action}`, { method:"POST" }); toast(`Trabajo: ${label.toLowerCase()}`); await refreshJobs(); }
      catch (error) { toast(error.message); }
    }}));
  }
  side.append(actions);
  box.append(main, side);
  return box;
}
function renderJobs() {
  const area = $("#job-list");
  const recent = $("#recent-jobs");
  area.replaceChildren(); recent.replaceChildren();
  for (const job of state.jobs) area.append(cardForJob(job));
  for (const job of state.jobs.slice(0, 3)) recent.append(cardForJob(job));
  if (!state.jobs.length) {
    area.textContent = "Todavía no has añadido ningún trabajo.";
    recent.textContent = "Tu primera descarga aparecerá aquí.";
  }
  $("#count-active").textContent = state.jobs.filter(job => ["queued", "running", "paused"].includes(job.status)).length;
}
async function refreshJobs() {
  state.jobs = await json("/api/jobs");
  renderJobs();
  const stats = await json("/api/stats");
  $("#count-transcripts").textContent = stats.transcripts;
  $("#count-videos").textContent = stats.videos;
}
async function createJob(event) {
  event.preventDefault();
  const button = $("#create-form button[type=submit]");
  button.disabled = true;
  try {
    const languages = $("#languages").value.split(",").map(v => v.trim()).filter(Boolean);
    const payload = {
      url:$("#video-url").value.trim(),languages,max_videos:Number($("#max-videos").value),
      browser:$("#browser").value || null
    };
    await json("/api/jobs", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
    toast("Trabajo añadido a la cola. Puedes cerrar la pestaña: el proceso continúa mientras esté abierto el servidor.");
    $("#video-url").value = "";
    switchTab("jobs");
    await refreshJobs();
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; }
}
async function refreshLibrary() {
  try {
    const query = new URLSearchParams({q:$("#search").value.trim(),language:$("#filter-language").value,limit: "200"});
    state.transcripts = await json("/api/transcripts?" + query);
    const area = $("#transcript-list"); area.replaceChildren();
    if (!state.transcripts.length) area.textContent = "No se encontraron transcripciones.";
    for (const item of state.transcripts) {
      const checkbox = elt("input", {type:"checkbox",class:"select-item", "aria-label":"Seleccionar " + item.title});
      checkbox.checked = state.selected.has(item.id);
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) state.selected.add(item.id); else state.selected.delete(item.id);
        renderSelection();
      });
      const metadata = elt("div", {class:"transcript-meta",text:`${item.language.toUpperCase()} · ${item.kind === "manual" ? "Subtítulos manuales" : "Subtítulos automáticos"}`});
      const info = elt("div", {}, elt("h3", {text:item.title}), metadata,
        elt("p", {class:"transcript-preview",text:item.preview}));
      const open = elt("button", {class:"subtle",text:"Leer →",onClick:()=>openViewer(item.id)});
      area.append(elt("div", {class:"transcript-card"}, checkbox, info, elt("div",{class:"transcript-actions"},open)));
    }
    renderSelection();
  } catch (error) { toast(error.message); }
}
async function openViewer(id) {
  try {
    const item = await json(`/api/transcripts/${id}`);
    state.viewer = item;
    $("#viewer-title").textContent = item.title;
    $("#viewer-lang").textContent = `${item.language.toUpperCase()} · ${item.video_id}`;
    $("#viewer-kind").textContent = item.kind === "manual" ? "Subtítulos manuales" : "Subtítulos automáticos";
    $("#viewer-text").textContent = item.text;
    $("#viewer-link").href = item.source_url;
    $("#viewer").showModal();
  } catch (error) { toast(error.message); }
}
function renderSelection() { $("#selection-count").textContent = state.selected.size; }
async function exportSelected() {
  const ids = [...state.selected];
  if (!ids.length) return toast("Selecciona al menos una transcripción en Biblioteca.");
  if (ids.length > 500) return toast("Selecciona como máximo 500 transcripciones.");
  const format = $('input[name="fmt"]:checked').value;
  const params = new URLSearchParams({ids:ids.join(","), format});
  if (format === "notebooklm") {
    params.set("words", $("#words").value);
    params.set("bytes_limit", String(Number($("#bytes-mb").value) * 1_000_000));
  }
  try {
    const response = await api("/api/export?" + params);
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const anchor = elt("a", {href:objectUrl,download:"transcript-studio-export.zip"});
    document.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    toast("Exportación preparada.");
  } catch (error) { toast(error.message); }
}
function init() {
  $$(".nav-btn").forEach(node => node.addEventListener("click", () => switchTab(node.dataset.tab)));
  $$("[data-go]").forEach(node => node.addEventListener("click", () => switchTab(node.dataset.go)));
  $("#create-form").addEventListener("submit", createJob);
  $("#refresh-jobs").addEventListener("click", () => refreshJobs().catch(error => toast(error.message)));
  $("#search-btn").addEventListener("click", refreshLibrary);
  $("#search").addEventListener("keydown", event => { if (event.key === "Enter") refreshLibrary(); });
  $("#filter-language").addEventListener("change", refreshLibrary);
  $("#viewer-close").addEventListener("click", () => $("#viewer").close());
  $("#copy-text").addEventListener("click", async () => {
    if (!state.viewer) return;
    try { await navigator.clipboard.writeText(state.viewer.text); toast("Texto copiado."); }
    catch { toast("Tu navegador no permite copiar automáticamente."); }
  });
  $("#select-loaded").addEventListener("click", () => {
    for (const item of state.transcripts) state.selected.add(item.id);
    $$(".select-item").forEach(item => { item.checked = true; });
    renderSelection();
  });
  $("#clear-selection").addEventListener("click", () => {
    state.selected.clear(); $$(".select-item").forEach(item => { item.checked = false; }); renderSelection();
  });
  $$('#formats input[name="fmt"]').forEach(input => input.addEventListener("change", () => {
    $("#notebook-options").classList.toggle("hidden", $('input[name="fmt"]:checked').value !== "notebooklm");
  }));
  $("#download-export").addEventListener("click", exportSelected);
  refreshJobs().catch(error => toast(error.message));
  // Polling is intentionally simple: no frontend build process or websocket service needed.
  setInterval(() => refreshJobs().catch(() => {}), 3000);
  setInterval(() => { if (state.current === "library") refreshLibrary(); }, 12000);
}
document.addEventListener("DOMContentLoaded", init);

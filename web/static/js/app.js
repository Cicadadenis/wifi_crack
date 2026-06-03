async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }

  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : response.text();
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function renderLogs(lines) {
  const box = document.getElementById("live-logs");
  if (!box) return;
  box.textContent = (lines || []).join("\n");
  box.scrollTop = box.scrollHeight;
}

async function refreshDashboard() {
  if (!document.body.dataset.page || document.body.dataset.page !== "dashboard") return;
  const status = await apiFetch("/api/status");
  setText("cpu-load", `${status.cpu.percent}%`);
  setText("ram-load", `${status.memory.percent}%`);
  setText("uptime", status.uptime);
  setText("interface-count", status.interfaces.length);
  renderLogs(status.logs);
}

async function togglePlugin(name, enabled) {
  await apiFetch(`/api/plugins/${encodeURIComponent(name)}/toggle`, {
    method: "POST",
    body: JSON.stringify({ enabled }),
  });
  window.location.reload();
}

async function deleteReport(name) {
  if (!window.confirm(`Delete report "${name}"?`)) return;
  await apiFetch(`/api/reports/${encodeURIComponent(name)}`, { method: "DELETE" });
  window.location.reload();
}

function connectLogs() {
  const box = document.getElementById("live-logs");
  if (!box || typeof io === "undefined") return;
  const socket = io();
  socket.on("logs", (payload) => renderLogs(payload.lines));
}

document.addEventListener("DOMContentLoaded", () => {
  connectLogs();
  refreshDashboard().catch(console.error);
  window.setInterval(() => refreshDashboard().catch(console.error), 5000);
});


const allowedTasks = new Set([
  "system_status",
  "list_interfaces",
  "check_dependencies",
  "list_plugins",
  "list_reports",
  "tail_logs",
]);

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof payload === "string" ? payload : payload.error || response.statusText;
    throw new Error(message);
  }

  return payload;
}

function showToast(message, variant = "info") {
  const container = document.getElementById("toast-container");
  if (!container || typeof bootstrap === "undefined") return;
  const id = `toast-${Date.now()}`;
  const icon = variant === "danger" ? "bi-exclamation-triangle" : "bi-info-circle";
  container.insertAdjacentHTML("beforeend", `
    <div id="${id}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="toast-header bg-transparent text-light border-secondary">
        <i class="bi ${icon} me-2"></i>
        <strong class="me-auto">SATANA</strong>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">${message}</div>
    </div>
  `);
  const el = document.getElementById(id);
  const toast = new bootstrap.Toast(el, { delay: 3500 });
  toast.show();
  el.addEventListener("hidden.bs.toast", () => el.remove());
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

function renderTaskLogs(lines) {
  const box = document.getElementById("task-logs");
  if (!box) return;
  box.textContent = (lines || []).join("\n");
  box.scrollTop = box.scrollHeight;
}

function statusClass(status) {
  return `status-${status || "muted"}`;
}

function setTaskStatus(value, status = "muted") {
  const el = document.getElementById("task-status");
  if (!el) return;
  el.textContent = value;
  el.className = `badge status-badge ${statusClass(status)}`;
}

function taskItemHtml(task) {
  return `
    <button class="activity-item" data-status="${task.status}" type="button" onclick="showTask('${task.id}')">
      <span class="activity-main">
        <strong>${task.task}</strong>
        <small>${task.created_at || ""}</small>
      </span>
      <span class="badge status-badge ${statusClass(task.status)}">${task.status}</span>
    </button>
  `;
}

function renderTaskList(tasks) {
  const list = document.getElementById("task-list");
  if (!list || !tasks) return;
  if (!tasks.length) {
    list.innerHTML = '<div class="empty-state">No tasks yet</div>';
    return;
  }
  list.innerHTML = tasks.map(taskItemHtml).join("");
  applyTaskFilter();
}

function applyTaskFilter() {
  const filter = document.getElementById("task-filter")?.value || "all";
  document.querySelectorAll("#task-list .activity-item").forEach((item) => {
    item.style.display = filter === "all" || item.dataset.status === filter ? "" : "none";
  });
}

async function refreshTasks() {
  const data = await apiFetch("/api/tasks");
  renderTaskList(data.tasks || []);
}

async function refreshDashboard() {
  if (document.body.dataset.page !== "dashboard") return;
  const status = await apiFetch("/api/status");
  setText("cpu-load", `${status.cpu.percent}%`);
  setText("ram-load", `${status.memory.percent}%`);
  setText("uptime", status.uptime);
  setText("interface-count", `${status.interfaces.length} found`);
  renderLogs(status.logs);
  await refreshTasks();
}

async function togglePlugin(name, enabled) {
  try {
    await apiFetch(`/api/plugins/${encodeURIComponent(name)}/toggle`, {
      method: "POST",
      body: JSON.stringify({ enabled }),
    });
    showToast("Plugin state saved");
    window.setTimeout(() => window.location.reload(), 500);
  } catch (error) {
    showToast(error.message, "danger");
  }
}

async function showTask(taskId) {
  const task = await apiFetch(`/api/tasks/${encodeURIComponent(taskId)}`);
  setTaskStatus(`${task.task}: ${task.status}`, task.status);
  renderTaskLogs(task.logs || []);
  return task;
}

async function pollTask(taskId) {
  const task = await showTask(taskId);
  await refreshTasks().catch(() => {});
  if (task.status === "pending" || task.status === "running") {
    window.setTimeout(() => pollTask(taskId).catch((error) => showToast(error.message, "danger")), 1200);
    return;
  }
  showToast(`${task.task}: ${task.status}`, task.status === "failed" ? "danger" : "info");
  if (task.task === "list_interfaces" && document.body.dataset.page === "interfaces") {
    window.setTimeout(() => window.location.reload(), 700);
  }
  if ((task.task === "monitor_mode" || task.task === "managed_mode") && document.body.dataset.page) {
    window.setTimeout(() => window.location.reload(), 700);
  }
  if (task.task === "list_plugins" && document.body.dataset.page === "plugins") {
    window.setTimeout(() => window.location.reload(), 700);
  }
}

async function runTask(taskName, params = {}) {
  try {
    setTaskStatus(`${taskName}: pending`, "pending");
    const result = await apiFetch("/api/tasks/run", {
      method: "POST",
      body: JSON.stringify({ task: taskName, params }),
    });
    showToast(`Task queued: ${taskName}`);
    await pollTask(result.task_id);
  } catch (error) {
    setTaskStatus("Task failed", "failed");
    showToast(error.message, "danger");
  }
}

let actionModalInstance = null;

function fieldHtml(field) {
  const id = `field-${field.name}`;
  if (field.type === "checkbox") {
    return `
      <div class="form-check mb-3">
        <input class="form-check-input" type="checkbox" id="${id}" name="${field.name}">
        <label class="form-check-label" for="${id}">${field.label}</label>
      </div>
    `;
  }
  const required = field.required ? "required" : "";
  const inputType = field.type === "number" ? "number" : "text";
  const value = field.default ? `value="${field.default}"` : "";
  return `
    <div class="mb-3">
      <label class="form-label" for="${id}">${field.label}</label>
      <input class="form-control bg-dark text-light border-secondary" type="${inputType}" id="${id}" name="${field.name}" ${required} ${value}>
    </div>
  `;
}

function openActionModal(button) {
  const action = button.dataset.action;
  const title = button.dataset.title || action;
  const fields = JSON.parse(button.dataset.fields || "[]");
  document.getElementById("actionModalTitle").textContent = title;
  document.getElementById("action-name").value = action;
  document.getElementById("action-fields").innerHTML = fields.map(fieldHtml).join("");
  const modalEl = document.getElementById("actionModal");
  if (!modalEl || typeof bootstrap === "undefined") {
    runAction(action, {});
    return;
  }
  actionModalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);
  actionModalInstance.show();
}

function collectActionParams() {
  const form = document.getElementById("action-form");
  const params = {};
  if (!form) return params;
  form.querySelectorAll("input[name]").forEach((input) => {
    if (input.type === "hidden") return;
    if (input.type === "checkbox") {
      if (input.checked) params[input.name] = "1";
      return;
    }
    if (input.value.trim()) params[input.name] = input.value.trim();
  });
  return params;
}

async function runAction(action, params = {}) {
  try {
    setTaskStatus(`${action}: pending`, "pending");
    const result = await apiFetch("/api/actions/run", {
      method: "POST",
      body: JSON.stringify({ action, params }),
    });
    showToast(`Запущено: ${action}`);
    if (actionModalInstance) actionModalInstance.hide();
    await pollTask(result.task_id);
  } catch (error) {
    setTaskStatus("Task failed", "failed");
    showToast(error.message, "danger");
  }
}

function submitAction() {
  const action = document.getElementById("action-name")?.value;
  if (!action) return;
  runAction(action, collectActionParams());
}

async function selectInterface(name) {
  try {
    await apiFetch("/api/interface/select", {
      method: "POST",
      body: JSON.stringify({ interface: name }),
    });
    showToast(`Интерфейс выбран: ${name}`);
    window.setTimeout(() => window.location.reload(), 500);
  } catch (error) {
    showToast(error.message, "danger");
  }
}

async function deleteReport(name) {
  if (!window.confirm(`Delete report "${name}"?`)) return;
  try {
    await apiFetch(`/api/reports/${encodeURIComponent(name)}`, { method: "DELETE" });
    showToast("Report deleted");
    window.location.reload();
  } catch (error) {
    showToast(error.message, "danger");
  }
}

function clearTaskScreen() {
  renderTaskLogs([]);
  setTaskStatus("Screen cleared", "muted");
}

async function copyTaskLog() {
  const text = document.getElementById("task-logs")?.textContent || "";
  try {
    await navigator.clipboard.writeText(text);
    showToast("Log copied");
  } catch {
    showToast("Clipboard is unavailable", "danger");
  }
}

function connectLogs() {
  const hasLogs = document.getElementById("live-logs") || document.getElementById("task-logs");
  if (!hasLogs || typeof io === "undefined") return;
  const socket = io();
  socket.on("logs", (payload) => renderLogs(payload.lines));
  socket.on("task_logs", (payload) => {
    renderTaskLogs(payload.lines);
    renderTaskList(payload.tasks);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  connectLogs();
  refreshDashboard().catch((error) => showToast(error.message, "danger"));
  if (document.getElementById("task-list")) {
    refreshTasks().catch((error) => showToast(error.message, "danger"));
  }
  window.setInterval(() => refreshDashboard().catch(console.error), 5000);
});

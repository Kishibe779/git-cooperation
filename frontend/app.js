const copy = {
  dashboard: "\u9996\u9875\u4eea\u8868\u76d8",
  analyze: "\u667a\u80fd\u5206\u6790",
  history: "\u5206\u6790\u5386\u53f2",
  billing: "\u8ba2\u9605\u4e0e\u4ed8\u8d39",
  settings: "\u7cfb\u7edf\u8bbe\u7f6e",
  backendOk: "\u540e\u7aef\u5df2\u8fde\u63a5",
  backendOff: "\u540e\u7aef\u672a\u8fde\u63a5",
  guest: "\u672a\u767b\u5f55",
  login: "\u767b\u5f55 / \u6ce8\u518c",
  switchAccount: "\u5207\u6362\u8d26\u6237",
  needLogin: "\u8bf7\u5148\u767b\u5f55\u3002",
};

const state = {
  apiBase: getDefaultApiBase(),
  meta: null,
  token: localStorage.getItem("careerpilot-token") || "",
  user: null,
  latestReport: "",
};

const routes = {
  "/": { title: copy.dashboard, eyebrow: "Product Dashboard", render: renderDashboard },
  "/analyze": { title: copy.analyze, eyebrow: "Resume Studio", render: renderAnalyze },
  "/history": { title: copy.history, eyebrow: "Saved Reports", render: renderHistory },
  "/plans": { title: copy.billing, eyebrow: "Billing", render: renderPlans },
  "/settings": { title: copy.settings, eyebrow: "System", render: renderSettings },
};

const viewRoot = document.querySelector("#view-root");
const routeTitle = document.querySelector("#route-title");
const routeEyebrow = document.querySelector("#route-eyebrow");
const backendStatus = document.querySelector("#backend-status");
const userChip = document.querySelector("#user-chip");
const authButton = document.querySelector("#auth-button");
const authDialog = document.querySelector("#auth-dialog");

window.addEventListener("hashchange", renderRoute);
document.querySelectorAll(".nav a").forEach((link) => {
  link.addEventListener("click", () => setTimeout(renderRoute, 0));
});
authButton.addEventListener("click", () => {
  setAuthTab(state.user ? "account" : "login");
  authDialog.showModal();
});
authDialog.addEventListener("close", () => showAuthMessage(""));
document.querySelector("#login-tab").addEventListener("click", () => setAuthTab("login"));
document.querySelector("#register-tab").addEventListener("click", () => setAuthTab("register"));
document.querySelector("#login-submit").addEventListener("click", login);
document.querySelector("#register-submit").addEventListener("click", register);
document.querySelector("#logout-submit").addEventListener("click", logout);

renderRoute();
bootstrap().then(renderRoute).catch(() => updateShell());

async function bootstrap() {
  try {
    state.meta = await api("/meta", { auth: false, timeout: 3000 });
    backendStatus.textContent = `${copy.backendOk}: ${state.meta.default_provider}`;
  } catch {
    backendStatus.textContent = copy.backendOff;
  }
  if (state.token) {
    try {
      state.user = await api("/auth/me", { timeout: 3000 });
    } catch {
      state.token = "";
      localStorage.removeItem("careerpilot-token");
    }
  }
  updateShell();
}

function renderRoute() {
  const path = location.hash.replace("#", "") || "/";
  const route = routes[path] || routes["/"];
  document.querySelectorAll(".nav a").forEach((link) => {
    link.classList.toggle("active", link.dataset.route === path);
  });
  routeTitle.textContent = route.title;
  routeEyebrow.textContent = route.eyebrow;
  viewRoot.innerHTML = route.render();
  bindCurrentView(path);
}

function renderDashboard() {
  const provider = state.meta?.llm_enabled ? state.meta.model_name : state.meta?.default_provider || "mock";
  const plan = state.user?.plan || "free";
  return `
    <section class="hero-band">
      <div>
        <p class="eyebrow">AI Resume Workspace</p>
        <h2>\u4ece\u7b80\u5386\u5230\u5c97\u4f4d\u5339\u914d\uff0c\u628a\u6c42\u804c\u6d41\u7a0b\u505a\u6210\u53ef\u6267\u884c\u7684\u4ea7\u54c1\u5de5\u4f5c\u53f0</h2>
        <p>\u652f\u6301\u767b\u5f55\u6ce8\u518c\u3001AI \u5206\u6790\u3001\u5386\u53f2\u62a5\u544a\u3001\u8ba2\u9605\u8ba1\u5212\u548c Markdown \u5bfc\u51fa\u3002DeepSeek \u53ef\u7528\u65f6\u8d70 AI\uff0c\u4e0d\u53ef\u7528\u65f6\u81ea\u52a8\u56de\u9000\u672c\u5730\u89c4\u5219\u3002</p>
        <div class="hero-actions">
          <a class="primary-link" href="#/analyze">\u5f00\u59cb\u5206\u6790</a>
          <a class="secondary-link" href="#/plans">\u67e5\u770b\u4ed8\u8d39\u8ba1\u5212</a>
        </div>
      </div>
      <div class="metric-stack">
        <article><span>Provider</span><strong>${escapeHtml(provider)}</strong></article>
        <article><span>\u5f53\u524d\u8ba1\u5212</span><strong>${escapeHtml(plan)}</strong></article>
        <article><span>\u5de5\u4f5c\u6d41</span><strong>3 steps</strong></article>
      </div>
    </section>
    <section class="section-grid">
      ${feature("\u5c97\u4f4d\u5339\u914d", "\u8bc6\u522b JD \u5173\u952e\u80fd\u529b\uff0c\u8f93\u51fa\u5339\u914d\u8bcd\u3001\u7f3a\u5931\u8bcd\u548c\u5f97\u5206\u3002")}
      ${feature("AI \u6539\u5199", "\u751f\u6210\u4f18\u5316\u6458\u8981\u3001\u9879\u76ee\u6539\u5199\u5efa\u8bae\u548c\u98ce\u9669\u63d0\u9192\u3002")}
      ${feature("\u5546\u4e1a\u5316\u58f3\u5c42", "\u5305\u542b\u7528\u6237\u3001\u5386\u53f2\u3001\u4ed8\u8d39\u6863\u4f4d\u548c\u8bbe\u7f6e\u9875\u3002")}
    </section>
    <section class="workflow-strip">
      ${step("01", "\u8f93\u5165\u7b80\u5386\u548c JD", "\u9ed8\u8ba4\u7ed9\u4e00\u7ec4\u53ef\u76f4\u63a5\u6f14\u793a\u7684\u6837\u4f8b\u3002")}
      ${step("02", "\u751f\u6210 AI \u62a5\u544a", "\u8f93\u51fa\u5f97\u5206\u3001\u4f18\u52bf\u3001\u98ce\u9669\u548c\u6539\u5199\u5efa\u8bae\u3002")}
      ${step("03", "\u4fdd\u5b58\u4e0e\u5bfc\u51fa", "\u767b\u5f55\u540e\u4fdd\u5b58\u5386\u53f2\uff0c\u5e76\u53ef\u4e0b\u8f7d Markdown\u3002")}
    </section>
  `;
}

function renderAnalyze() {
  const providerText = state.meta?.llm_enabled
    ? `DeepSeek: ${state.meta.model_name}`
    : "\u672c\u5730\u89c4\u5219\u5f15\u64ce";
  return `
    <section class="analysis-layout">
      <form id="analyze-form" class="panel form-panel">
        <div class="panel-heading">
          <h2>\u65b0\u5efa\u7b80\u5386\u5206\u6790</h2>
          <span>${escapeHtml(providerText)}</span>
        </div>
        <div class="input-row">
          <label>\u5019\u9009\u4eba\u59d3\u540d <input id="candidate-name" value="\u5f20\u540c\u5b66" maxlength="50" /></label>
          <label>\u76ee\u6807\u5c97\u4f4d <input id="target-role" value="AI \u4ea7\u54c1\u52a9\u7406" maxlength="80" /></label>
        </div>
        <label>\u7b80\u5386\u5185\u5bb9
          <textarea id="resume-text" rows="12">\u8d1f\u8d23\u57fa\u4e8e Python \u548c FastAPI \u5f00\u53d1\u7b80\u5386\u4f18\u5316\u7cfb\u7edf\uff0c\u5b8c\u6210\u63a5\u53e3\u8bbe\u8ba1\u3001\u529f\u80fd\u8054\u8c03\u548c\u6d4b\u8bd5\u3002\u66fe\u6574\u7406\u9879\u76ee\u6587\u6863\u5e76\u4e0e\u524d\u7aef\u540c\u5b66\u534f\u4f5c\uff0c\u5c06\u63a5\u53e3\u8054\u8c03\u6548\u7387\u63d0\u5347 30%\uff0c\u80fd\u591f\u56f4\u7ed5\u9700\u6c42\u5206\u6790\u3001\u9879\u76ee\u6392\u671f\u548c\u7ed3\u679c\u4ea4\u4ed8\u63a8\u8fdb\u5de5\u4f5c\u3002</textarea>
        </label>
        <label>\u5c97\u4f4d\u63cf\u8ff0
          <textarea id="job-description" rows="10">\u5c97\u4f4d\u9700\u8981\u5177\u5907 Python \u5f00\u53d1\u80fd\u529b\uff0c\u80fd\u591f\u8fdb\u884c\u9700\u6c42\u5206\u6790\u3001\u9879\u76ee\u6392\u671f\u4e0e\u8de8\u56e2\u961f\u6c9f\u901a\uff1b\u6709 AI \u5e94\u7528\u3001\u5927\u6a21\u578b\u5de5\u5177\u3001\u6587\u6863\u8868\u8fbe\u548c\u7ed3\u679c\u5bfc\u5411\u7ecf\u9a8c\u8005\u4f18\u5148\u3002</textarea>
        </label>
        <div class="input-row">
          <label>Provider
            <select id="provider"></select>
          </label>
          <button id="submit-button" type="submit">\u751f\u6210\u5206\u6790\u62a5\u544a</button>
        </div>
      </form>
      <section class="panel result-panel">
        <div class="panel-heading">
          <h2>\u5206\u6790\u7ed3\u679c</h2>
          <span id="status-text">\u7b49\u5f85\u63d0\u4ea4</span>
        </div>
        <div id="empty-state" class="empty-state">\u63d0\u4ea4\u540e\u5c55\u793a\u5339\u914d\u5f97\u5206\u3001\u6539\u5199\u5efa\u8bae\u3001\u98ce\u9669\u548c\u5bfc\u51fa\u62a5\u544a\u3002</div>
        <div id="result-content" class="hidden"></div>
      </section>
    </section>
  `;
}

function renderHistory() {
  if (!state.user) {
    return `<section class="panel"><div class="empty-state">${copy.needLogin}</div></section>`;
  }
  return `<section class="panel"><div class="panel-heading"><h2>\u5206\u6790\u5386\u53f2</h2><span>\u6b63\u5728\u8bfb\u53d6</span></div><div id="history-list" class="history-list"></div></section>`;
}

function renderPlans() {
  return `<section id="plans-grid" class="plans-grid"><div class="empty-state">\u6b63\u5728\u8bfb\u53d6\u8ba1\u5212</div></section>`;
}

function renderSettings() {
  return `
    <section class="panel settings-panel">
      <div class="panel-heading"><h2>\u7cfb\u7edf\u8bbe\u7f6e</h2><span>API</span></div>
      <label>API Base <input id="api-base" value="${escapeHtml(state.apiBase)}" /></label>
      <button id="save-settings" type="button">\u4fdd\u5b58\u8bbe\u7f6e</button>
      <div class="settings-note">Backend: ${escapeHtml(state.meta?.app_name || "unknown")} / Provider: ${escapeHtml(state.meta?.default_provider || "mock")}</div>
    </section>
  `;
}

function bindCurrentView(path) {
  if (path === "/analyze") bindAnalyze();
  if (path === "/history") loadHistory();
  if (path === "/plans") loadPlans();
  if (path === "/settings") bindSettings();
}

function bindAnalyze() {
  const provider = document.querySelector("#provider");
  const availableProviders = state.meta?.available_providers?.length
    ? state.meta.available_providers
    : ["deepseek_strict"];
  provider.innerHTML = availableProviders.map((value) => {
    const label = value === "deepseek_strict" ? "deepseek strict (no fallback)" : value;
    return `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`;
  }).join("");
  provider.value = availableProviders.includes(state.meta?.default_provider)
    ? state.meta.default_provider
    : availableProviders[0];
  document.querySelector("#analyze-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = document.querySelector("#submit-button");
    const status = document.querySelector("#status-text");
    const payload = {
      candidate_name: document.querySelector("#candidate-name").value.trim() || "\u533f\u540d\u5019\u9009\u4eba",
      target_role: document.querySelector("#target-role").value.trim() || "\u76ee\u6807\u5c97\u4f4d",
      resume_text: document.querySelector("#resume-text").value.trim(),
      job_description: document.querySelector("#job-description").value.trim(),
      provider: provider.value,
    };
    if (payload.resume_text.length < 20 || payload.job_description.length < 20) {
      alert("\u7b80\u5386\u5185\u5bb9\u548c\u5c97\u4f4d\u63cf\u8ff0\u90fd\u81f3\u5c11\u9700\u8981 20 \u4e2a\u5b57\u7b26\u3002");
      return;
    }
    button.disabled = true;
    status.textContent = "\u5206\u6790\u4e2d";
    try {
      const data = await api("/analyze", { method: "POST", body: payload, timeout: 60000 });
      state.latestReport = data.report_markdown || "";
      renderResult(data);
      status.textContent = data.provider_meta.fallback_used ? "\u5df2\u56de\u9000\u5b8c\u6210" : "\u5206\u6790\u5b8c\u6210";
    } catch (error) {
      status.textContent = "\u8bf7\u6c42\u5931\u8d25";
      alert(error.message);
    } finally {
      button.disabled = false;
    }
  });
}

function renderResult(data) {
  document.querySelector("#empty-state").classList.add("hidden");
  const root = document.querySelector("#result-content");
  root.classList.remove("hidden");
  root.innerHTML = `
    <div class="score-card">
      <span>\u5339\u914d\u5f97\u5206</span>
      <strong>${data.match_overview.score}</strong>
      <p>${escapeHtml(data.summary)}</p>
      <small>${formatProvider(data.provider_meta)}</small>
      <div class="provider-badge ${data.provider_meta.fallback_used ? "warn" : "ok"}">
        ${data.provider_meta.provider_used === "deepseek" && !data.provider_meta.fallback_used ? "DeepSeek real response" : "Fallback or local result"}
      </div>
    </div>
    <div class="toolbar">
      <button id="download-report" type="button">\u4e0b\u8f7d Markdown \u62a5\u544a</button>
      <button id="copy-summary" class="secondary-button" type="button">\u590d\u5236\u4f18\u5316\u6458\u8981</button>
    </div>
    <div class="result-grid">
      ${card("\u5339\u914d\u5173\u952e\u8bcd", tags(data.match_overview.matched_keywords, false))}
      ${card("\u7f3a\u5931\u5173\u952e\u8bcd", tags(data.match_overview.missing_keywords, true))}
      ${card("\u7b80\u5386\u4f18\u52bf", list(data.strengths))}
      ${card("\u98ce\u9669\u63d0\u9192", list(data.risks))}
    </div>
    ${card("\u4f18\u5316\u6458\u8981", `<p>${escapeHtml(data.optimized_summary)}</p>`)}
    ${card("\u5b9a\u5236\u5316\u6539\u5199\u5efa\u8bae", list(data.tailored_bullets))}
    ${data.suggestion_sections.map((section) => card(section.title, list(section.items))).join("")}
  `;
  document.querySelector("#download-report").addEventListener("click", downloadReport);
  document.querySelector("#copy-summary").addEventListener("click", () => {
    navigator.clipboard.writeText(data.optimized_summary || "");
    alert("\u5df2\u590d\u5236");
  });
}

async function loadHistory() {
  const root = document.querySelector("#history-list");
  if (!root) return;
  try {
    const data = await api("/analyses");
    root.innerHTML = data.items.length
      ? data.items.map((item) => `
          <article class="history-item">
            <div>
              <strong>${escapeHtml(item.target_role)}</strong>
              <p>${escapeHtml(item.summary)}</p>
              <small>${new Date(item.created_at).toLocaleString()} / ${escapeHtml(item.provider_used)}</small>
            </div>
            <span>${item.score}</span>
          </article>
        `).join("")
      : `<div class="empty-state">\u8fd8\u6ca1\u6709\u5386\u53f2\u62a5\u544a\u3002</div>`;
  } catch (error) {
    root.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadPlans() {
  const root = document.querySelector("#plans-grid");
  try {
    const plans = await api("/plans", { auth: false });
    root.innerHTML = plans.map((plan) => `
      <article class="plan-card ${plan.highlighted ? "highlighted" : ""}">
        <h2>${escapeHtml(plan.name)}</h2>
        <strong>${escapeHtml(plan.price)}</strong>
        <p>${plan.quota} analyses / month</p>
        ${list(plan.features)}
        <button data-plan="${plan.id}" type="button">${state.user?.plan === plan.id ? "\u5f53\u524d\u8ba1\u5212" : "\u5f00\u901a\u8ba1\u5212"}</button>
      </article>
    `).join("");
    root.querySelectorAll("button[data-plan]").forEach((button) => {
      button.addEventListener("click", () => checkout(button.dataset.plan));
    });
  } catch (error) {
    root.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function bindSettings() {
  document.querySelector("#save-settings").addEventListener("click", async () => {
    state.apiBase = document.querySelector("#api-base").value.trim() || getDefaultApiBase();
    localStorage.setItem("careerpilot-api-base", state.apiBase);
    await bootstrap();
    alert("\u8bbe\u7f6e\u5df2\u4fdd\u5b58");
  });
}

async function checkout(plan) {
  if (!state.user) {
    authDialog.showModal();
    return;
  }
  const result = await api("/billing/checkout", { method: "POST", body: { plan } });
  state.user.plan = result.plan;
  updateShell();
  alert(result.message);
  loadPlans();
}

async function login() {
  const payload = {
    email: document.querySelector("#login-email").value.trim(),
    password: document.querySelector("#login-password").value,
  };
  const error = validateLogin(payload);
  if (error) {
    showAuthMessage(error, true);
    return;
  }
  await finishAuth("/auth/login", payload);
}

async function register() {
  const payload = {
    name: document.querySelector("#register-name").value.trim(),
    email: document.querySelector("#register-email").value.trim(),
    password: document.querySelector("#register-password").value,
  };
  const confirm = document.querySelector("#register-confirm").value;
  const error = validateRegister(payload, confirm);
  if (error) {
    showAuthMessage(error, true);
    return;
  }
  await finishAuth("/auth/register", payload);
}

async function finishAuth(path, payload) {
  try {
    showAuthMessage("Working...");
    const data = await api(path, { method: "POST", body: payload, auth: false });
    state.token = data.token;
    state.user = data.user;
    localStorage.setItem("careerpilot-token", state.token);
    authDialog.close();
    updateShell();
    renderRoute();
  } catch (error) {
    showAuthMessage(error.message, true);
  }
}

async function logout() {
  try {
    await api("/auth/logout", { method: "POST" });
  } catch {
    // Local sign-out still clears the stale token.
  }
  state.token = "";
  state.user = null;
  localStorage.removeItem("careerpilot-token");
  authDialog.close();
  updateShell();
  renderRoute();
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), options.timeout || 10000);
  if (options.auth !== false && state.token) headers.Authorization = `Bearer ${state.token}`;
  try {
    const response = await fetch(`${state.apiBase}${path}`, {
      method: options.method || "GET",
      headers,
      signal: controller.signal,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      throw new Error(payload?.message || payload?.detail || "Request failed");
    }
    return response.json();
  } finally {
    clearTimeout(timeout);
  }
}

function updateShell() {
  userChip.textContent = state.user ? `${state.user.name} / ${state.user.plan}` : copy.guest;
  authButton.textContent = state.user ? copy.switchAccount : copy.login;
  updateAccountPanel();
}

function setAuthTab(tab) {
  if (state.user) tab = "account";
  showAuthMessage("");
  document.querySelector("#login-tab").classList.toggle("active", tab === "login");
  document.querySelector("#register-tab").classList.toggle("active", tab === "register");
  document.querySelector("#login-panel").classList.toggle("hidden", tab !== "login");
  document.querySelector("#register-panel").classList.toggle("hidden", tab !== "register");
  document.querySelector("#account-panel").classList.toggle("hidden", tab !== "account");
}

function updateAccountPanel() {
  const accountPanel = document.querySelector("#account-panel");
  if (!accountPanel) return;
  if (state.user) {
    document.querySelector("#account-name").textContent = state.user.name;
    document.querySelector("#account-email").textContent = state.user.email;
    document.querySelector("#account-plan").textContent = `Plan: ${state.user.plan}`;
    document.querySelector("#login-tab").disabled = true;
    document.querySelector("#register-tab").disabled = true;
  } else {
    document.querySelector("#login-tab").disabled = false;
    document.querySelector("#register-tab").disabled = false;
  }
}

function showAuthMessage(message, isError = false) {
  const box = document.querySelector("#auth-message");
  box.textContent = message;
  box.classList.toggle("hidden", !message);
  box.classList.toggle("error", Boolean(isError));
}

function validateLogin(payload) {
  if (!isEmail(payload.email)) return "Enter a valid email address.";
  if (payload.password.length < 8) return "Password must be at least 8 characters.";
  return "";
}

function validateRegister(payload, confirm) {
  if (payload.name.length < 2) return "Name must be at least 2 characters.";
  if (!isEmail(payload.email)) return "Enter a valid email address.";
  if (payload.password.length < 8) return "Password must be at least 8 characters.";
  if (!/[A-Za-z]/.test(payload.password) || !/[0-9]/.test(payload.password)) {
    return "Password must include letters and numbers.";
  }
  if (payload.password !== confirm) return "Passwords do not match.";
  return "";
}

function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function downloadReport() {
  if (!state.latestReport) return;
  const blob = new Blob([state.latestReport], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "careerpilot-analysis-report.md";
  link.click();
  URL.revokeObjectURL(url);
}

function getDefaultApiBase() {
  const isBackend = ["127.0.0.1", "localhost"].includes(location.hostname) && location.port === "8000";
  if (isBackend) return `${location.origin}/api/v1`;
  return localStorage.getItem("careerpilot-api-base") || "http://127.0.0.1:8000/api/v1";
}

function feature(title, body) {
  return `<article class="feature-card"><h3>${title}</h3><p>${body}</p></article>`;
}

function step(number, title, body) {
  return `<article><span>${number}</span><strong>${title}</strong><p>${body}</p></article>`;
}

function card(title, body) {
  return `<article class="result-card"><h3>${escapeHtml(title)}</h3>${body}</article>`;
}

function list(items) {
  return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function tags(items, missing) {
  const values = items.length ? items : [missing ? "\u6682\u65e0\u660e\u663e\u7f3a\u53e3" : "\u6682\u65e0\u5339\u914d\u9879"];
  return `<div class="tag-list">${values.map((item) => `<span class="tag ${missing ? "missing" : ""}">${escapeHtml(item)}</span>`).join("")}</div>`;
}

function formatProvider(meta) {
  const parts = [`Provider: ${meta.provider_used}`];
  if (meta.model_used) parts.push(`Model: ${meta.model_used}`);
  if (meta.fallback_used) parts.push("\u5df2\u89e6\u53d1\u56de\u9000");
  return parts.join(" / ");
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}

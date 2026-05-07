let polling = {};
let knownStatuses = {}; 
let accessToken = localStorage.getItem("access_token");

const loginBox = document.getElementById("loginBox");
const appBox = document.getElementById("appBox");

const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const loginPassword = document.getElementById("loginPassword");

const logoutBtn = document.getElementById("logoutBtn");
const sidebarToggle = document.getElementById("sidebarToggle");
const mobileToggleBtn = document.getElementById("mobileToggleBtn");
const sidebar = document.getElementById("sidebar");
const mainContent = document.getElementById("mainContent");

const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");

const uploadProgressBlock = document.getElementById("uploadProgressBlock");
const uploadProgressBar = document.getElementById("uploadProgressBar");
const uploadPercent = document.getElementById("uploadPercent");

const requestList = document.getElementById("requestList");
const scheduledList = document.getElementById("scheduledList");
const recentRequestList = document.getElementById("recentRequestList");
const recentScheduledList = document.getElementById("recentScheduledList");
const userInfo = document.getElementById("userInfo");

// Special Job Elements
const specialJobToggle = document.getElementById("specialJobToggle");
const specialJobPanel = document.getElementById("specialJobPanel");
const specialDate = document.getElementById("specialDate");
const specialTime = document.getElementById("specialTime");

// AI Assistant
const aiQueryForm = document.getElementById("aiQueryForm");
const aiQueryInput = document.getElementById("aiQueryInput");
const aiQueryBtn = document.getElementById("aiQueryBtn");
const assistantRequestList = document.getElementById("assistantRequestList");

// Profile Modal Elements
const profileModal = document.getElementById("profileModal");
const userProfileBtn = document.getElementById("userProfileBtn");
const closeProfileBtn = document.getElementById("closeProfileBtn");

// ================= THEME MANAGER =================
const themeToggle = document.getElementById("themeToggle");
const currentTheme = localStorage.getItem("theme");

if (currentTheme === "light") {
  document.documentElement.classList.add("light-mode");
  if(themeToggle) themeToggle.innerHTML = `<i class="fa-solid fa-sun text-warning"></i> <span class="nav-text">Light Mode</span>`;
}

themeToggle?.addEventListener("click", () => {
  document.documentElement.classList.toggle("light-mode");
  
  if (document.documentElement.classList.contains("light-mode")) {
    localStorage.setItem("theme", "light");
    themeToggle.innerHTML = `<i class="fa-solid fa-sun text-warning"></i> <span class="nav-text">Light Mode</span>`;
  } else {
    localStorage.setItem("theme", "dark");
    themeToggle.innerHTML = `<i class="fa-solid fa-moon"></i> <span class="nav-text">Dark Mode</span>`;
  }
});

// ================= MODAL LOGIC =================
userProfileBtn?.addEventListener("click", () => {
  profileModal.classList.remove("hidden");
});

closeProfileBtn?.addEventListener("click", () => {
  profileModal.classList.add("hidden");
});

// Close modal if clicked outside the content box
profileModal?.addEventListener("click", (e) => {
  if (e.target === profileModal) profileModal.classList.add("hidden");
});

// ================= UTILITIES =================
function formatBytes(bytes, decimals = 2) {
  if (!+bytes) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

// ================= SPECIAL JOB TOGGLE =================
if (specialJobToggle) {
  specialJobToggle.addEventListener("change", (e) => {
    if (e.target.checked) {
      specialJobPanel.classList.remove("hidden");
      specialDate.required = true;
      specialTime.required = true;
    } else {
      specialJobPanel.classList.add("hidden");
      specialDate.required = false;
      specialTime.required = false;
    }
  });
}

// ================= LIVE SEARCH & TABS =================
function switchRequestTab(tabName) {
  document.querySelectorAll('.custom-tabs .tab').forEach(t => t.classList.remove('active'));
  
  if (tabName === 'all') {
    document.querySelectorAll('.custom-tabs .tab')[0].classList.add('active');
    requestList.classList.remove('hidden');
    scheduledList.classList.add('hidden');
  } else {
    document.querySelectorAll('.custom-tabs .tab')[1].classList.add('active');
    requestList.classList.add('hidden');
    scheduledList.classList.remove('hidden');
  }
}

const searchInput = document.getElementById("searchInput");
searchInput?.addEventListener("input", (e) => {
  const term = e.target.value.toLowerCase();
  const cards = document.querySelectorAll("#requestList .request-card, #scheduledList .request-card");
  
  cards.forEach(card => {
    const name = card.querySelector(".req-name").innerText.toLowerCase();
    const id = card.querySelector(".req-id").innerText.toLowerCase();
    if (name.includes(term) || id.includes(term)) {
      card.style.display = "block";
    } else {
      card.style.display = "none";
    }
  });
});

setLoggedInUI(false);

// ================= TOAST NOTIFICATIONS =================
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return; 
  
  const toast = document.createElement("div");
  toast.className = `toast toast-${type} animated fade-in`;
  
  let icon = "fa-circle-info";
  if (type === "success") icon = "fa-circle-check";
  if (type === "error") icon = "fa-circle-exclamation";

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function authHeaders() {
  return accessToken ? { Authorization: "Bearer " + accessToken } : {};
}

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const auth = authHeaders();
  for (const [k, v] of Object.entries(auth)) headers.set(k, v);

  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    logout();
    throw new Error("Unauthorized");
  }
  return res;
}

// ================= UI CONTROLS =================
function setLoggedInUI(isLoggedIn) {
  if (isLoggedIn) {
    loginBox.classList.add("hidden");
    appBox.classList.remove("hidden");
  } else {
    loginBox.classList.remove("hidden");
    appBox.classList.add("hidden");
  }
}

function showSection(sectionId) {
  document.querySelectorAll(".page-section").forEach(sec => sec.classList.remove("active"));
  const targetSec = document.getElementById(sectionId);
  if (targetSec) targetSec.classList.add("active");

  document.querySelectorAll(".nav-links li").forEach(li => li.classList.remove("active"));
  if (window.event && window.event.currentTarget && window.event.currentTarget.tagName === 'LI') {
    window.event.currentTarget.classList.add("active");
  }
  if (window.innerWidth <= 768) sidebar.classList.remove("mobile-active");
}

sidebarToggle?.addEventListener("click", () => {
  sidebar.classList.toggle("collapsed");
  mainContent.classList.toggle("expanded");
});

mobileToggleBtn?.addEventListener("click", () => sidebar.classList.toggle("mobile-active"));

function logout() {
  accessToken = null;
  localStorage.removeItem("access_token");
  Object.values(polling).forEach(id => clearInterval(id));
  polling = {};
  knownStatuses = {}; 

  if (requestList) requestList.innerHTML = "";
  if (scheduledList) scheduledList.innerHTML = "";
  if (recentRequestList) recentRequestList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-inbox fa-2x"></i><p>No active jobs</p></div>`;
  if (recentScheduledList) recentScheduledList.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;"><i class="fa-solid fa-calendar fa-2x"></i><p>No scheduled jobs</p></div>`;
  if (assistantRequestList) assistantRequestList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-message fa-2x"></i><p>Waiting for your prompt...</p></div>`;

  setLoggedInUI(false);
  showToast("Logged out successfully", "info");
}

// ================= USER & STATS =================
async function loadMe() {
  const res = await apiFetch("/users/me");
  if (!res.ok) return;
  const user = await res.json();
  
  if (userInfo) userInfo.innerText = user.name;
  
  const dashName = document.getElementById("dashboardName");
  if (dashName) dashName.innerText = `Hey, ${user.name}! 👋`;
  
  const dashEmail = document.getElementById("dashboardEmail");
  if (dashEmail) dashEmail.innerText = user.email;

  // Populate Profile Modal
  document.getElementById("modalUserName").innerText = user.name;
  document.getElementById("modalUserEmail").innerText = user.email;
}

async function loadStats() {
  try {
    const res = await apiFetch("/stats");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("statTotal").innerText = data.total_requests || 0;
    document.getElementById("statCompleted").innerText = data.completed_requests || 0;
    document.getElementById("statPending").innerText = data.pending_requests || 0;
    document.getElementById("statFailed").innerText = data.failed_requests || 0;
    document.getElementById("statScheduled").innerText = data.scheduled_requests || 0;
    document.getElementById("statProcessed").innerText = data.total_jobs_processed || 0;

    // Populate Modal Storage
    const storageBytes = data.total_storage_used_bytes || 0;
    document.getElementById("modalStorageUsed").innerText = formatBytes(storageBytes);

  } catch (e) {
    console.error("Failed to load user stats");
  }
}

// ================= EXPAND RESULTS UI =================
async function toggleRequestDetails(headerElement, requestId) {
  const card = headerElement.closest('.request-card');
  if (!card) return;

  const resultsZone = card.querySelector('.results-zone');
  const icon = headerElement.querySelector('.toggle-icon');

  if (resultsZone.classList.contains('hidden')) {
    resultsZone.classList.remove('hidden');
    icon.style.transform = 'rotate(180deg)';

    if (resultsZone.innerHTML.trim() === '') {
      resultsZone.innerHTML = `<div style="text-align:center; padding: 15px;"><i class="fa-solid fa-circle-notch fa-spin text-primary"></i> Loading details...</div>`;
      try {
        const res = await apiFetch(`/requests/${requestId}/results`);
        if (res.ok) {
          const data = await res.json();
          renderResults(data, resultsZone);
        } else {
          resultsZone.innerHTML = `<div class="text-danger" style="text-align:center; padding: 10px;">Failed to load results.</div>`;
        }
      } catch (e) {
        resultsZone.innerHTML = `<div class="text-danger" style="text-align:center; padding: 10px;">Error connecting to server.</div>`;
      }
    }
  } else {
    resultsZone.classList.add('hidden');
    icon.style.transform = 'rotate(0deg)';
  }
}

function renderResults(data, container) {
  if (!data.results || data.results.length === 0) {
    container.innerHTML = `<div class="text-muted" style="text-align:center; padding: 15px; font-size: 0.9em;">No detailed job results available yet.</div>`;
    return;
  }

  let html = `<div class="results-scroll" style="margin-top: 10px; border-top: 1px solid var(--glass-border); padding-top: 10px;">`;
  data.results.forEach(r => {
    const statusColor = r.success ? 'var(--success)' : 'var(--danger)';
    const statusIcon = r.success ? 'fa-check' : 'fa-xmark';
    const outputText = r.success ? (r.output || 'Completed successfully') : (r.error || 'Job failed');
    
    html += `
      <div style="background: var(--input-bg); padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid ${statusColor};">
        <div style="display:flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.85em;">
          <strong>Row ${r.row_number} - ${r.job_type}</strong>
          <i class="fa-solid ${statusIcon}" style="color: ${statusColor};"></i>
        </div>
        <div style="color: var(--text-muted); font-size: 0.8em; word-break: break-all;">
          ${outputText}
        </div>
      </div>
    `;
  });
  html += `</div>`;
  container.innerHTML = html;
}

// ================= REQUEST UI =================
function createRequestCard(req, container) {
  const empty = container.querySelector(".empty-state");
  if (empty) empty.remove();

  let card = container.querySelector(`.request-card[data-req-id="${req.id}"]`);

  const statusText = req.status || "queued";
  const statusClass = `badge-${statusText}`;
  const totalJobs = req.total_jobs || 0;
  
  let completedJobs = req.completed_jobs || 0;
  if (statusText === "completed") {
      completedJobs = totalJobs;
  }

  const percent = totalJobs ? Math.round((completedJobs / totalJobs) * 100) : 0;
  const barColor = statusText === "completed" ? "#10b981" : "var(--primary)";

  if (!card) {
    card = document.createElement("div");
    card.className = "request-card glass animated slide-up";
    card.dataset.reqId = req.id; 
    
    const scheduledBadge = req.is_scheduled ? `<span class="badge" style="background: rgba(14, 165, 233, 0.2); color: var(--primary); border: 1px solid var(--primary); margin-left: 5px;"><i class="fa-solid fa-clock"></i> Scheduled</span>` : '';
    
    const downloadBtn = statusText === "completed" ? 
      `<button class="btn-success btn-sm w-100" onclick="downloadExcel('${req.id}')"><i class="fa-solid fa-download"></i> Download Report</button>` : '';

    card.innerHTML = `
      <div class="card-header" style="cursor: pointer; user-select: none;" onclick="toggleRequestDetails(this, '${req.id}')">
        <b class="req-name" style="display: flex; align-items: center; flex-wrap: wrap;">
           <i class="fa-solid fa-file-excel text-primary" style="margin-right: 8px;"></i> 
           <span></span>
           ${scheduledBadge}
        </b>
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="status badge ${statusClass}">${statusText}</span>
          <i class="fa-solid fa-chevron-down toggle-icon text-muted" style="transition: transform 0.3s ease;"></i>
        </div>
      </div>
      <div class="card-body">
        <div class="card-meta">ID: <span class="req-id text-muted"></span></div>
        <div class="card-meta">Progress: <span class="progress-text text-muted">${completedJobs}/${totalJobs}</span></div>
      </div>
      <div class="progress-wrap mt-10">
        <div class="progress-bar" style="width: ${percent}%; background: ${barColor};"></div>
      </div>
      <div class="download-zone mt-10">${downloadBtn}</div>
      <div class="results-zone hidden"></div>
    `;
    container.prepend(card); 
  } else {
    const statusBadge = card.querySelector(".status");
    if (statusBadge) {
        statusBadge.innerText = statusText;
        statusBadge.className = `status badge ${statusClass}`;
    }

    const progressText = card.querySelector(".progress-text");
    if (progressText) progressText.innerText = `${completedJobs}/${totalJobs}`;

    const bar = card.querySelector(".progress-bar");
    if (bar) {
        bar.style.width = percent + "%";
        bar.style.background = barColor;
    }

    const downloadDiv = card.querySelector(".download-zone");
    if (statusText === "completed" && downloadDiv && !downloadDiv.innerHTML.trim()) {
        downloadDiv.innerHTML = `<button class="btn-success btn-sm w-100" onclick="downloadExcel('${req.id}')"><i class="fa-solid fa-download"></i> Download Report</button>`;
    }
  }

  card.querySelector(".req-name span").innerText = req.name || "File";
  card.querySelector(".req-id").innerText = req.id;

  return card;
}

// ================= POLLING =================
async function fetchStatus(request_id) {
  const res = await apiFetch(`/requests/${request_id}/status`);
  if (!res.ok) return;

  const data = await res.json();
  const cards = document.querySelectorAll(`.request-card[data-req-id="${request_id}"]`);
  
  const previousStatus = knownStatuses[request_id];
  knownStatuses[request_id] = data.status;

  if (cards.length === 0) return;

  cards.forEach(card => {
    const statusBadge = card.querySelector(".status");
    statusBadge.innerText = data.status;
    statusBadge.className = `status badge badge-${data.status}`;
    
    card.querySelector(".progress-text").innerText = `${data.completed_jobs}/${data.total_jobs}`;

    const bar = card.querySelector(".progress-bar");
    const percent = data.total_jobs ? Math.round((data.completed_jobs / data.total_jobs) * 100) : 0;
    bar.style.width = percent + "%";

    if (data.status === "completed") {
      bar.style.background = "#10b981"; 
      const downloadDiv = card.querySelector(".download-zone");
      if (!downloadDiv.innerHTML.trim()) {
        downloadDiv.innerHTML = `<button class="btn-success btn-sm w-100"><i class="fa-solid fa-download"></i> Download Report</button>`;
        downloadDiv.querySelector("button").onclick = () => downloadExcel(request_id);
      }
      if (previousStatus !== "completed") {
         card.querySelector('.results-zone').innerHTML = '';
      }
    }
  });

  if (data.status === "completed") {
    if (previousStatus && previousStatus !== "completed") {
      const idString = request_id ? request_id.toString() : "";
      showToast(`Job ${idString.substring(0,6)} completed!`, "success");
      
      // Update stats passively when a job finishes
      loadStats(); 
    }
    if (polling[request_id]) {
      clearInterval(polling[request_id]);
      delete polling[request_id];
    }
  }
}

function startPolling(id) {
  if (polling[id]) return; 
  fetchStatus(id);
  polling[id] = setInterval(() => fetchStatus(id), 5000);
}

// ================= DOWNLOAD =================
async function downloadExcel(id) {
  showToast("Starting download...", "info");
  const res = await apiFetch(`/requests/${id}/download`);
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${id}.xlsx`;
  a.click();
  window.URL.revokeObjectURL(url);
}

// ================= DATA LOADERS =================
async function loadRecentRequests() {
  const res = await apiFetch("/requests/recent");
  if (!res.ok) return;
  const data = await res.json();
  if(!data || data.length === 0) return;

  data.slice(-3).forEach(req => {
    createRequestCard(req, recentRequestList);
    if (req.status !== "completed" && req.status !== "failed") {
      startPolling(req.id);
    }
  });
}

async function loadAllRequests() {
  const res = await apiFetch("/requests/recent");
  if (!res.ok) return;
  const data = await res.json();
  if(!data || data.length === 0) return;

  data.forEach(req => {
    createRequestCard(req, requestList);
    if (req.status !== "completed" && req.status !== "failed") {
      startPolling(req.id);
    }
  });
  if(searchInput && searchInput.value) searchInput.dispatchEvent(new Event('input'));
}

async function loadScheduledRequests() {
  const res = await apiFetch("/requests/scheduled");
  if (!res.ok) return;
  const data = await res.json();

  if(!data || data.length === 0) {
    if (recentScheduledList) recentScheduledList.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;"><i class="fa-solid fa-calendar fa-2x"></i><p>No scheduled jobs</p></div>`;
    if (scheduledList) scheduledList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-calendar fa-2x"></i><p>No scheduled jobs found</p></div>`;
    return;
  }

  data.slice(0, 3).forEach(req => {
    createRequestCard(req, recentScheduledList);
    if (req.status !== "completed" && req.status !== "failed") startPolling(req.id);
  });

  data.forEach(req => {
    createRequestCard(req, scheduledList);
    if (req.status !== "completed" && req.status !== "failed") startPolling(req.id);
  });
  
  if(searchInput && searchInput.value) searchInput.dispatchEvent(new Event('input'));
}

// ================= FILE SELECTION HANDLER =================
function handleFileSelection(inputEl) {
  const textElement = inputEl.nextElementSibling;
  
  if (inputEl.files && inputEl.files.length > 0) {
    const fileName = inputEl.files[0].name;
    if (textElement && textElement.tagName === "P") {
      textElement.innerHTML = `
        <span style="color: #10b981; font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 8px; position: relative; z-index: 20;">
          <i class="fa-solid fa-check"></i> ${fileName} ready 
          <span class="clear-file-btn" title="Remove file">
            <i class="fa-solid fa-xmark"></i>
          </span>
        </span>`;

      const clearBtn = textElement.querySelector('.clear-file-btn');
      clearBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        inputEl.value = ""; 
        textElement.innerHTML = "Choose a file or drag it here";
      });
    }
  } else {
    if (textElement && textElement.tagName === "P") {
      textElement.innerHTML = "Choose a file or drag it here";
    }
  }
}

if (fileInput) {
  fileInput.addEventListener("change", () => handleFileSelection(fileInput));
}

// ================= UPLOADERS =================
function handleUpload(e, form, fileInputId, progressBlock, progressBar, percentText, targetListContainer) {
  e.preventDefault();
  if (!accessToken) return;

  const fileInputEl = document.getElementById(fileInputId);
  if (!fileInputEl.files.length) {
    showToast("Please select a file first", "error");
    return;
  }

  const formData = new FormData(form);
  progressBlock.classList.remove("hidden");
  progressBar.style.width = "0%";

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload");
  xhr.responseType = "json";
  xhr.setRequestHeader("Authorization", "Bearer " + accessToken);

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const p = Math.round((e.loaded / e.total) * 100);
      progressBar.style.width = p + "%";
      percentText.innerText = p + "%";
    }
  };

  xhr.onload = async () => {
    const res = xhr.response;
    if (!res || xhr.status >= 400) {
      showToast(res?.detail || "Upload failed", "error");
      progressBlock.classList.add("hidden");
      return;
    }

    showToast("File uploaded successfully!", "success");

    // FIX: Parallelize these requests instead of waiting for them one by one
    await Promise.all([
      loadRecentRequests(),
      loadAllRequests(),
      loadScheduledRequests(),
      loadStats()
    ]);
    
    startPolling(res.request_id);

    setTimeout(() => {
        progressBlock.classList.add("hidden");
        form.reset();
        
        if (form.id === "uploadForm") {
          if (specialJobPanel) specialJobPanel.classList.add("hidden");
          if (specialDate) specialDate.required = false;
          if (specialTime) specialTime.required = false;
        }
        
        const textElement = fileInputEl.nextElementSibling;
        if (textElement && textElement.tagName === "P") {
            textElement.innerHTML = "Choose a file or drag it here";
        }
    }, 1500);
  };

  xhr.send(formData);
}

if(uploadForm) uploadForm.addEventListener("submit", (e) => handleUpload(e, uploadForm, "fileInput", uploadProgressBlock, uploadProgressBar, uploadPercent, recentRequestList));

// ================= AI ASSISTANT QUERY =================
if (aiQueryForm) {
  aiQueryForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = aiQueryInput.value.trim();
    if (!query) return;

    const originalBtnText = aiQueryBtn.innerHTML;
    aiQueryBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Processing Query...`;
    aiQueryBtn.disabled = true;

    try {
      const res = await apiFetch("/ai/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      });

      const data = await res.json();
      renderAiResult(query, data);
      aiQueryInput.value = ""; 
    } catch (err) {
      showToast("AI Query failed", "error");
      renderAiResult(query, { type: "error", message: err.message });
    } finally {
      aiQueryBtn.innerHTML = originalBtnText;
      aiQueryBtn.disabled = false;
    }
  });
}

function renderAiResult(query, data) {
  const container = document.getElementById("assistantRequestList");
  const empty = container.querySelector(".empty-state");
  if (empty) empty.remove();

  const resultCard = document.createElement("div");
  resultCard.className = "request-card glass animated slide-up mb-10";

  let contentHtml = "";

  if (data.type === "query_result") {
    
    if (data.executed_sql) {
      contentHtml += `<div style="font-family: monospace; font-size: 0.8em; color: var(--text-muted); margin-bottom: 10px; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap;">${data.executed_sql}</div>`;
    }

    if (data.data && data.data.length > 0) {
       let headers = Object.keys(data.data[0]);
       let tableHtml = `<div class="ai-table-container"><table class="ai-table">`;
       tableHtml += `<thead><tr>`;
       headers.forEach(h => tableHtml += `<th>${h}</th>`);
       tableHtml += `</tr></thead><tbody>`;
       data.data.forEach(row => {
         tableHtml += `<tr>`;
         headers.forEach(h => tableHtml += `<td>${row[h] !== null ? row[h] : ''}</td>`);
         tableHtml += `</tr>`;
       });
       tableHtml += `</tbody></table></div>`;
       contentHtml += tableHtml;
    } else {
       contentHtml += `<p class="text-muted" style="margin-top: 10px;">Query returned no results.</p>`;
    }
  } else if (data.type === "action_result") {
    contentHtml = `<div style="margin-top: 10px; background: rgba(16, 185, 129, 0.1); border-left: 3px solid var(--success); padding: 12px; border-radius: 8px; color: var(--text-main);">
      <i class="fa-solid fa-check text-success" style="margin-right: 8px;"></i> ${data.message}
    </div>`;
  } else {
    contentHtml = `<div class="text-danger" style="margin-top: 10px;">${data.message || data.detail || 'Unknown response from AI'}</div>`;
  }

  resultCard.innerHTML = `
    <div style="font-weight: 600; margin-bottom: 12px; color: var(--text-main); border-bottom: 1px solid var(--glass-border); padding-bottom: 8px;">
      <i class="fa-solid fa-user text-muted" style="margin-right: 8px;"></i> ${query}
    </div>
    <div>
      <i class="fa-solid fa-robot text-primary" style="margin-right: 8px;"></i>
      ${contentHtml}
    </div>
  `;

  container.prepend(resultCard);
}


// ================= LOGIN =================
if(loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const btn = loginForm.querySelector('button');
    const originalText = btn.innerHTML;
    btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Authenticating...`;
    btn.disabled = true;

    const body = new URLSearchParams();
    body.append("username", loginEmail.value);
    body.append("password", loginPassword.value);

    try {
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body
      });

      const data = await res.json();

      if (!res.ok) {
        showToast(data.detail || "Login failed", "error");
        btn.innerHTML = originalText;
        btn.disabled = false;
        return;
      }

      accessToken = data.access_token;
      localStorage.setItem("access_token", accessToken);
      showToast("Welcome back!", "success");

      // FIX: Parallelize boot requests for instantly faster login
      await Promise.all([
        loadMe(),
        loadStats(),
        loadRecentRequests(),
        loadAllRequests(),
        loadScheduledRequests()
      ]);

      showSection("dashboardSection");
      setLoggedInUI(true);
    } catch (err) {
      showToast("Connection error", "error");
    } finally {
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  });
}

if(logoutBtn) logoutBtn.addEventListener("click", logout);

// ================= BOOT =================
const bootOverlay = document.createElement("div");
bootOverlay.className = "drop-overlay glass active";
bootOverlay.style.border = "none"; 
bootOverlay.style.zIndex = "10000"; 
bootOverlay.innerHTML = `
  <div style="text-align:center">
    <i class="fa-solid fa-circle-notch fa-spin fa-4x text-primary mb-10"></i>
    <h2 style="color: white; margin-top: 15px;">Restoring Session...</h2>
  </div>
`;

if (accessToken) {
  document.body.appendChild(bootOverlay);
}

async function boot() {
  if (!accessToken) {
    setLoggedInUI(false);
    return;
  }

  try {
    // FIX: Parallelize boot requests for instantly faster load times
    await Promise.all([
      loadMe(),
      loadStats(),
      loadRecentRequests(),
      loadAllRequests(),
      loadScheduledRequests()
    ]);
    
    showSection("dashboardSection");
    setLoggedInUI(true);
  } catch (e) {
    logout();
  } finally {
    if (document.body.contains(bootOverlay)) bootOverlay.remove();
  }
}

// ================= DRAG & DROP =================
const dropOverlay = document.createElement("div");
dropOverlay.className = "drop-overlay glass";
dropOverlay.innerHTML = `<div style="text-align:center"><i class="fa-solid fa-cloud-arrow-up fa-4x text-primary mb-10"></i><h2>Drop File to Upload</h2></div>`;
document.body.appendChild(dropOverlay);

window.addEventListener("dragenter", (e) => {
  if (e.dataTransfer && e.dataTransfer.types.includes("Files")) dropOverlay.classList.add("active");
});
window.addEventListener("dragleave", (e) => { 
  if (e.target === dropOverlay) dropOverlay.classList.remove("active"); 
});
window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("drop", (e) => { 
  e.preventDefault(); 
  dropOverlay.classList.remove("active"); 

  const files = e.dataTransfer.files;
  if (!files || files.length === 0) return;

  const dashboardActive = document.getElementById("dashboardSection").classList.contains("active");
  const targetInput = dashboardActive ? document.getElementById("fileInput") : null;
  
  if (targetInput) {
    targetInput.files = files; 
    handleFileSelection(targetInput);
    showToast(`Attached: ${files[0].name}`, "info");
  }
});

boot();


// ================= PWA SERVICE WORKER =================
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then(registration => {
        console.log('Service Worker registered with scope:', registration.scope);
      })
      .catch(error => {
        console.error('Service Worker registration failed:', error);
      });
  });
}
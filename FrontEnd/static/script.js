let polling = {};
let knownStatuses = {}; // Tracks statuses to prevent toast spam
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
const recentRequestList = document.getElementById("recentRequestList");
const userInfo = document.getElementById("userInfo");

// assistant
const assistantForm = document.getElementById("assistantUploadForm");
const assistantFileInput = document.getElementById("assistantFileInput");
const assistantBar = document.getElementById("assistantBar");
const assistantPercent = document.getElementById("assistantPercent");
const assistantProgress = document.getElementById("assistantProgressBlock");
const assistantRequestList = document.getElementById("assistantRequestList");

// ================= THEME MANAGER =================
const themeToggle = document.getElementById("themeToggle");
const currentTheme = localStorage.getItem("theme");

// Apply saved theme on load
if (currentTheme === "light") {
  document.documentElement.classList.add("light-mode");
  if(themeToggle) themeToggle.innerHTML = `<i class="fa-solid fa-sun text-warning"></i> <span class="nav-text">Light Mode</span>`;
}

// Toggle theme on click
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

// ================= LIVE SEARCH =================
const searchInput = document.getElementById("searchInput");
searchInput?.addEventListener("input", (e) => {
  const term = e.target.value.toLowerCase();
  const cards = requestList.querySelectorAll(".request-card");
  
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

// ================= AUTH HEADERS =================
function authHeaders() {
  return accessToken ? { Authorization: "Bearer " + accessToken } : {};
}

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const auth = authHeaders();

  for (const [k, v] of Object.entries(auth)) {
    headers.set(k, v);
  }

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
  document.querySelectorAll(".page-section").forEach(sec => {
    sec.classList.remove("active");
  });
  
  const targetSec = document.getElementById(sectionId);
  if (targetSec) targetSec.classList.add("active");

  document.querySelectorAll(".nav-links li").forEach(li => li.classList.remove("active"));
  if (window.event && window.event.currentTarget && window.event.currentTarget.tagName === 'LI') {
    window.event.currentTarget.classList.add("active");
  }
  
  // Auto-close sidebar on mobile after clicking a link
  if (window.innerWidth <= 768) {
    sidebar.classList.remove("mobile-active");
  }
}

sidebarToggle?.addEventListener("click", () => {
  sidebar.classList.toggle("collapsed");
  mainContent.classList.toggle("expanded");
});

mobileToggleBtn?.addEventListener("click", () => {
  sidebar.classList.toggle("mobile-active");
});

// ================= LOGOUT =================
function logout() {
  accessToken = null;
  localStorage.removeItem("access_token");

  Object.values(polling).forEach(id => clearInterval(id));
  polling = {};
  knownStatuses = {}; 

  if (requestList) requestList.innerHTML = "";
  if (recentRequestList) recentRequestList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-inbox fa-2x"></i><p>No active jobs</p></div>`;
  if (assistantRequestList) assistantRequestList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-file-circle-question fa-2x"></i><p>Waiting for input...</p></div>`;

  setLoggedInUI(false);
  showToast("Logged out successfully", "info");
}

// ================= USER =================
async function loadMe() {
  const res = await apiFetch("/users/me");
  if (!res.ok) return;
  const user = await res.json();

  if (userInfo) userInfo.innerText = user.name;
  
  const dashName = document.getElementById("dashboardName");
  if (dashName) dashName.innerText = `Hey, ${user.name}! 👋`;
  
  const dashEmail = document.getElementById("dashboardEmail");
  if (dashEmail) dashEmail.innerText = user.email;
}

// ================= REQUEST UI =================
function createRequestCard(req, container) {
  const empty = container.querySelector(".empty-state");
  if (empty) empty.remove();

  let card = container.querySelector(`.request-card[data-req-id="${req.id}"]`);

  if (!card) {
    card = document.createElement("div");
    card.className = "request-card glass animated slide-up";
    card.dataset.reqId = req.id; 

    card.innerHTML = `
      <div class="card-header">
        <b class="req-name"><i class="fa-solid fa-file-excel text-primary"></i> <span></span></b>
        <span class="status badge badge-queued">queued</span>
      </div>
      <div class="card-body">
        <div class="card-meta">ID: <span class="req-id text-muted"></span></div>
        <div class="card-meta">Progress: <span class="progress-text text-muted"></span></div>
      </div>
      <div class="progress-wrap mt-10">
        <div class="progress-bar"></div>
      </div>
      <div class="download-zone mt-10"></div>
    `;
    container.prepend(card); 
  }

  card.querySelector(".req-name span").innerText = req.name || "File";
  card.querySelector(".req-id").innerText = req.id;
  card.querySelector(".progress-text").innerText = `0/${req.total_jobs || 0}`;

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
    }
  });

  if (data.status === "completed") {
    if (previousStatus && previousStatus !== "completed") {
      const idString = request_id ? request_id.toString() : "";
      showToast(`Job ${idString.substring(0,6)} completed!`, "success");
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

  recentRequestList.innerHTML = ""; 
  
  data.slice(-3).forEach(req => {
    createRequestCard(req, recentRequestList);
    startPolling(req.id);
  });
}

async function loadAllRequests() {
  const res = await apiFetch("/requests/recent");
  if (!res.ok) return;
  const data = await res.json();
  
  if(!data || data.length === 0) return;

  requestList.innerHTML = ""; 
  data.forEach(req => {
    createRequestCard(req, requestList);
    startPolling(req.id);
  });
  
  // Apply current search filter to new data if a search is active
  if(searchInput && searchInput.value) {
    searchInput.dispatchEvent(new Event('input'));
  }
}

// ================= UPLOADERS =================
function handleUpload(e, form, fileInputId, progressBlock, progressBar, percentText, targetListContainer, isAssistant = false) {
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

    await loadRecentRequests();
    await loadAllRequests();
    
    if (isAssistant) {
      targetListContainer.innerHTML = "";
      createRequestCard({ id: res.request_id, name: fileInputEl.files[0].name, status: "queued", total_jobs: 0 }, targetListContainer);
    }
    
    startPolling(res.request_id);

    setTimeout(() => {
        progressBlock.classList.add("hidden");
        form.reset();
        
        const textElement = fileInputEl.nextElementSibling;
        if (textElement && textElement.tagName === "P") {
            textElement.innerHTML = isAssistant ? "Upload document for analysis" : "Choose a file or drag it here";
        }
    }, 1500);
  };

  xhr.send(formData);
}

if(uploadForm) uploadForm.addEventListener("submit", (e) => handleUpload(e, uploadForm, "fileInput", uploadProgressBlock, uploadProgressBar, uploadPercent, recentRequestList, false));
if(assistantForm) assistantForm.addEventListener("submit", (e) => handleUpload(e, assistantForm, "assistantFileInput", assistantProgress, assistantBar, assistantPercent, assistantRequestList, true));

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

      await loadMe();
      await loadRecentRequests();
      await loadAllRequests(); 

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

// ================= BOOT (AUTO-LOGIN HANDLER) =================
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
    await loadMe();
    await loadRecentRequests();
    await loadAllRequests(); 
    showSection("dashboardSection");
    setLoggedInUI(true);
  } catch (e) {
    logout();
  } finally {
    if (document.body.contains(bootOverlay)) {
      bootOverlay.remove();
    }
  }
}

// ================= DRAG & DROP =================
const dropOverlay = document.createElement("div");
dropOverlay.className = "drop-overlay glass";
dropOverlay.innerHTML = `<div style="text-align:center"><i class="fa-solid fa-cloud-arrow-up fa-4x text-primary mb-10"></i><h2>Drop File to Upload</h2></div>`;
document.body.appendChild(dropOverlay);

window.addEventListener("dragenter", (e) => {
  if (e.dataTransfer && e.dataTransfer.types.includes("Files")) {
    dropOverlay.classList.add("active");
  }
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
  const targetInput = dashboardActive ? document.getElementById("fileInput") : document.getElementById("assistantFileInput");
  
  if (targetInput) {
    targetInput.files = files; 
    
    const textElement = targetInput.nextElementSibling;
    if (textElement && textElement.tagName === "P") {
      textElement.innerHTML = `<span style="color: #10b981; font-weight: bold;"><i class="fa-solid fa-check"></i> ${files[0].name} ready</span>`;
    }
    
    showToast(`Attached: ${files[0].name}`, "info");
  }
});

boot();
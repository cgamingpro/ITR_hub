let polling = {};
let accessToken = localStorage.getItem("access_token");

const loginBox = document.getElementById("loginBox");
const appBox = document.getElementById("appBox");

const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const loginPassword = document.getElementById("loginPassword");
const loginMessage = document.getElementById("loginMessage");

const logoutBtn = document.getElementById("logoutBtn");

const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");

const statusMessage = document.getElementById("statusMessage");

const uploadProgressBlock = document.getElementById("uploadProgressBlock");
const uploadProgressBar = document.getElementById("uploadProgressBar");
const uploadPercent = document.getElementById("uploadPercent");

const requestList = document.getElementById("requestList");
const recentRequestList = document.getElementById("recentRequestList");

const userInfo = document.getElementById("userInfo");

// assistant
const assistantForm = document.getElementById("assistantUploadForm");
const assistantFileInput = document.getElementById("assistantFileInput");
const assistantStatus = document.getElementById("assistantStatusMessage");
const assistantBar = document.getElementById("assistantBar");
const assistantPercent = document.getElementById("assistantPercent");
const assistantProgress = document.getElementById("assistantProgressBlock");
const clientTableBody = document.getElementById("clientTableBody");

setLoggedInUI(false);

// ================= AUTH HEADERS =================
function authHeaders() {
  return accessToken
    ? { Authorization: "Bearer " + accessToken }
    : {};
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

// ================= UI =================
function setLoggedInUI(isLoggedIn) {
  loginBox.classList.toggle("hidden", isLoggedIn);
  appBox.classList.toggle("hidden", !isLoggedIn);
}

function showSection(sectionId) {
  document.querySelectorAll(".page-section").forEach(sec => {
    sec.classList.toggle("active", sec.id === sectionId);
  });
}

// ================= LOGOUT =================
function logout() {
  accessToken = null;
  localStorage.removeItem("access_token");

  Object.values(polling).forEach(id => clearInterval(id));
  polling = {};

  requestList.innerHTML = "";
  recentRequestList.innerHTML = "";

  setLoggedInUI(false);
  loginMessage.innerText = "";
}

// ================= USER =================
async function loadMe() {
  const res = await apiFetch("/users/me");
  const user = await res.json();

  userInfo.innerText = `Logged in as ${user.name}`;

  document.getElementById("dashboardName").innerText = "Name: " + user.name;
  document.getElementById("dashboardEmail").innerText = "Email: " + user.email;
}

// ================= REQUEST UI =================
function createRequestCard(req, container) {
  let card = document.getElementById("req-" + req.id);

  if (!card) {
    card = document.createElement("div");
    card.className = "request-card";
    card.id = "req-" + req.id;

    card.innerHTML = `
      <b class="req-name"></b>
      <div>ID: <span class="req-id"></span></div>
      <div>Status: <span class="status"></span></div>
      <div>Progress: <span class="progress"></span></div>

      <div class="progress-wrap">
        <div class="progress-bar"></div>
      </div>

      <div class="download"></div>
    `;

    container.prepend(card);
  }

  card.querySelector(".req-name").innerText = req.name;
  card.querySelector(".req-id").innerText = req.id;
  card.querySelector(".status").innerText = req.status;
  card.querySelector(".progress").innerText = `0/${req.total_jobs || 0}`;

  return card;
}

// ================= POLLING =================
async function fetchStatus(request_id) {
  const res = await apiFetch(`/requests/${request_id}/status`);
  if (!res.ok) return;

  const data = await res.json();
  const card = document.getElementById("req-" + request_id);
  if (!card) return;

  card.querySelector(".status").innerText = data.status;
  card.querySelector(".progress").innerText =
    `${data.completed_jobs}/${data.total_jobs}`;

  const bar = card.querySelector(".progress-bar");
  const percent = data.total_jobs
    ? Math.round((data.completed_jobs / data.total_jobs) * 100)
    : 0;

  bar.style.width = percent + "%";

  if (data.status === "completed") {
    clearInterval(polling[request_id]);
    delete polling[request_id];

    const downloadDiv = card.querySelector(".download");

    if (!downloadDiv.innerHTML.trim()) {
      downloadDiv.innerHTML = `<button>Download Excel</button>`;
      downloadDiv.querySelector("button").onclick = () =>
        downloadExcel(request_id);
    }

    // assistant table fill (if backend sends clients)
    if (data.clients) {
      fillClientTable(data.clients);
    }
  }
}

function startPolling(id) {
  fetchStatus(id);
  polling[id] = setInterval(() => fetchStatus(id), 5000);
}

// ================= DOWNLOAD =================
async function downloadExcel(id) {
  const res = await apiFetch(`/requests/${id}/download`);
  const blob = await res.blob();

  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${id}.xlsx`;
  a.click();

  window.URL.revokeObjectURL(url);
}

// ================= RECENT REQUESTS (ONLY 2) =================
async function loadRecentRequests() {
  const res = await apiFetch("/requests/recent");
  const data = await res.json();

  recentRequestList.innerHTML = "";

  data.slice(0, 2).forEach(req => {
    createRequestCard(req, recentRequestList);
    startPolling(req.id);
  });
}

// ================= FULL REQUEST PAGE =================
async function loadAllRequests() {
  const res = await apiFetch("/requests/recent");
  const data = await res.json();

  requestList.innerHTML = "";

  data.forEach(req => {
    createRequestCard(req, requestList);
    startPolling(req.id);
  });
}

// ================= UPLOAD =================
uploadForm.addEventListener("submit", function (e) {
  e.preventDefault();

  if (!accessToken) return;

  const formData = new FormData(uploadForm);

  uploadProgressBlock.classList.remove("hidden");
  uploadProgressBar.style.width = "0%";

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload");
  xhr.responseType = "json";
  xhr.setRequestHeader("Authorization", "Bearer " + accessToken);

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const p = Math.round((e.loaded / e.total) * 100);
      uploadProgressBar.style.width = p + "%";
      uploadPercent.innerText = p + "%";
    }
  };

  xhr.onload = () => {
    const res = xhr.response;

    if (!res) return;

    createRequestCard(
      {
        id: res.request_id,
        name: fileInput.files[0].name,
        status: "queued",
        total_jobs: 0
      },
      recentRequestList
    );

    startPolling(res.request_id);
    showSection("requestSection");
  };

  xhr.send(formData);
});

// ================= ASSISTANT UPLOAD =================
assistantForm?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData();
  formData.append("user_file", assistantFileInput.files[0]);

  assistantProgress.classList.remove("hidden");

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload");
  xhr.setRequestHeader("Authorization", "Bearer " + accessToken);
  xhr.responseType = "json";

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const p = Math.round((e.loaded / e.total) * 100);
      assistantBar.style.width = p + "%";
      assistantPercent.innerText = p + "%";
    }
  };

  xhr.onload = () => {
    const res = xhr.response;

    assistantStatus.innerText = "Uploaded";

    startPolling(res.request_id);
    showSection("requestSection");
  };

  xhr.send(formData);
});

// ================= CLIENT TABLE =================
function fillClientTable(clients) {
  clientTableBody.innerHTML = "";

  clients.forEach((c, i) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${i + 1}</td>
      <td>${c.name || ""}</td>
      <td>${c.pan || ""}</td>
      <td>${c.password || ""}</td>
    `;
    clientTableBody.appendChild(row);
  });
}

// ================= LOGIN =================
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  loginMessage.innerText = "Logging in...";

  const body = new URLSearchParams();
  body.append("username", loginEmail.value);
  body.append("password", loginPassword.value);

  const res = await fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body
  });

  const data = await res.json();

  if (!res.ok) {
    loginMessage.innerText = data.detail || "Login failed";
    return;
  }

  accessToken = data.access_token;
  localStorage.setItem("access_token", accessToken);

  setLoggedInUI(true);

  await loadMe();
  await loadRecentRequests();

  showSection("dashboardSection");
});

// ================= SIDEBAR =================
logoutBtn?.addEventListener("click", logout);

// ================= BOOT =================
async function boot() {
  if (!accessToken) {
    setLoggedInUI(false);
    return;
  }

  setLoggedInUI(true);
  await loadMe();
  await loadRecentRequests();
  showSection("dashboardSection");
}
// GLOBAL DRAG DROP OVERLAY
const overlay = document.createElement("div");
overlay.className = "drop-overlay";
overlay.innerHTML = "<h2>Drop File to Upload</h2>";
document.body.appendChild(overlay);

window.addEventListener("dragenter", () => {
  overlay.classList.add("active");
});

window.addEventListener("dragleave", () => {
  overlay.classList.remove("active");
});

window.addEventListener("drop", (e) => {
  overlay.classList.remove("active");
});
boot();
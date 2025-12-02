const chatBox = document.getElementById("chatBox");
const promptInput = document.getElementById("prompt");
const loginStatus = document.getElementById("loginStatus");
const userInfo = document.getElementById("userInfo");
const btnLogout = document.getElementById("btnLogout");
const btnAdmin = document.getElementById("btnAdmin");
const btnDemoAdmin = document.getElementById("btnDemoAdmin");
const btnFillAdmin = document.getElementById("btnFillAdmin");
const btnFillWorker = document.getElementById("btnFillWorker");
const btnFillSupervisor = document.getElementById("btnFillSupervisor");
const btnRegister = document.getElementById("btnRegister");
const loginBlock = document.getElementById("loginBlock");
const qrBlock = document.getElementById("qrBlock");
const convBlock = document.getElementById("convBlock");
const convList = document.getElementById("convList");
const convTitle = document.getElementById("convTitle");
const chatShell = document.getElementById("chatShell");
const configShell = document.getElementById("configShell");
const adminShell = document.getElementById("adminShell");
const tabs = document.getElementById("tabs");
const contentShell = document.getElementById("contentShell");
const layout = document.getElementById("layout");
const statusEl = document.getElementById("status");
const profileInfo = document.getElementById("profileInfo");
const pwStatus = document.getElementById("pwStatus");
const ollamaStatus = document.getElementById("ollamaStatus");
const adminUserList = document.getElementById("adminUserList");
const adminConvList = document.getElementById("adminConvList");
const adminMessages = document.getElementById("adminMessages");
const adminConvTitle = document.getElementById("adminConvTitle");
const adminUserSelected = document.getElementById("adminUserSelected");
const adminStatus = document.getElementById("adminStatus");
const reassignSelect = document.getElementById("reassignSelect");
const btnReassign = document.getElementById("btnReassign");
let currentUserEmail = "";
let accessToken = "";
let refreshToken = "";
let currentConversationId = null;
let adminSelectedUserId = null;
let adminSelectedConvId = null;
let adminUsers = [];
let session2FAToken = null;  // Token temporal para 2FA
let demoQRData = {};  // Almacenar QR codes indexados por email

function append(text, isAssistant = false) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `msg ${isAssistant ? "assistant" : "user"}`;
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = isAssistant ? "Assistant" : currentUserEmail || "User";
  const body = document.createElement("div");
  body.innerHTML = escapeHtml(text);
  msgDiv.append(meta, body);
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function escapeHtml(text) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

function setTab(tab) {
  document.querySelectorAll(".tabs button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });
  const sections = { chat: chatShell, config: configShell, admin: adminShell };
  Object.entries(sections).forEach(([key, el]) => {
    const isActive = key === tab;
    el.classList.toggle("active", isActive);
    el.classList.toggle("hidden", !isActive);
  });
  if (tab === "admin") {
    loadAdminUsers();
  }
}

async function loadConversations() {
  if (!accessToken) return;
  try {
    const res = await fetch("/conversations?limit=50", {
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) return;
    const convs = await res.json();
    convList.innerHTML = "";
    convs.forEach((c) => {
      const div = document.createElement("div");
      div.className = "conv-item";
      div.dataset.id = c.id;
      const span = document.createElement("span");
      span.className = "conv-title";
      span.textContent = c.title || "Sin título";
      const del = document.createElement("button");
      del.className = "conv-delete";
      del.textContent = "✕";
      del.addEventListener("click", (ev) => {
        ev.stopPropagation();
        deleteConversation(c.id);
      });
      div.addEventListener("click", () => setActiveConversation(c.id, c.title));
      div.append(span, del);
      convList.appendChild(div);
    });
  } catch (e) {
    console.error(e);
  }
}

async function loadMessages(conversationId) {
  if (!accessToken || !conversationId) return;
  try {
    const res = await fetch(`/conversations/${conversationId}/messages?limit=200`, {
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) return;
    const msgs = await res.json();
    chatBox.innerHTML = "";
    msgs.forEach((m) => {
      append(m.content, m.role === "assistant");
    });
    if (msgs.length === 0) {
      chatBox.innerHTML = '<div class="welcome">Escribe tu primer mensaje para comenzar una nueva conversación.</div>';
    }
  } catch (e) {
    console.error(e);
  }
}

function setActiveConversation(id, title) {
  currentConversationId = id;
  convTitle.textContent = title || "Nueva conversacion";
  document.querySelectorAll(".conv-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.id === String(id));
  });
  loadMessages(id);
}

async function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  loginStatus.textContent = "Iniciando sesion...";
  try {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Login failed");
    const data = await res.json();

    if (data.needs_2fa) {
      // Requerimos 2FA
      session2FAToken = data.session_token;
      loginStatus.textContent = "";
      show2FAPrompt();
    } else {
      // Login directo sin 2FA
      accessToken = data.access_token;
      refreshToken = data.refresh_token;
      loginStatus.textContent = "Login OK";
      userInfo.textContent = `Logueado: ${email}`;
      setAuthedUI(true);
      await fetchProfile();
      await loadConversations();
      chatBox.innerHTML = '<div class="welcome">Escribe tu primer mensaje para comenzar una nueva conversación.</div>';
      loadConfigInfo();
    }
  } catch (err) {
    loginStatus.textContent = "Error de login";
    console.error(err);
  }
}

function show2FAPrompt() {
  loginBlock.classList.add("hidden");
  document.getElementById("twoFABlock").classList.remove("hidden");
  document.getElementById("totpCode").focus();
}

function hide2FAPrompt() {
  document.getElementById("twoFABlock").classList.add("hidden");
  loginBlock.classList.remove("hidden");
  document.getElementById("totpCode").value = "";
  document.getElementById("twoFAStatus").textContent = "";
  session2FAToken = null;
}

async function verify2FA() {
  const totp_code = document.getElementById("totpCode").value;
  if (totp_code.length !== 6 || !/^\d+$/.test(totp_code)) {
    document.getElementById("twoFAStatus").textContent = "Código inválido";
    return;
  }

  document.getElementById("twoFAStatus").textContent = "Verificando...";
  try {
    const res = await fetch("/auth/verify-2fa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_token: session2FAToken, totp_code }),
    });

    if (!res.ok) {
      const err = await res.json();
      document.getElementById("twoFAStatus").textContent = err.detail || "Código incorrecto";
      return;
    }

    const data = await res.json();
    accessToken = data.access_token;
    refreshToken = data.refresh_token;

    hide2FAPrompt();
    loginStatus.textContent = "Login OK";
    setAuthedUI(true);
    await fetchProfile();
    await loadConversations();
    chatBox.innerHTML = '<div class="welcome">Escribe tu primer mensaje para comenzar una nueva conversación.</div>';
    loadConfigInfo();
  } catch (err) {
    document.getElementById("twoFAStatus").textContent = "Error de verificación";
    console.error(err);
  }
}

async function fetchProfile() {
  if (!accessToken) return;
  try {
    const res = await fetch("/auth/me", {
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) return;
    const me = await res.json();
    currentUserEmail = me.email;
    userInfo.textContent = `Logueado: ${me.email} (rol: ${me.role})`;
    profileInfo.textContent = `${me.email} (rol: ${me.role})`;
  } catch (e) {
    /* ignore */
  }
}

async function createConversation() {
  if (!accessToken) return;
  try {
    const res = await fetch("/conversations", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + accessToken,
      },
      body: JSON.stringify({ title: "Nueva conversacion" }),
    });
    if (!res.ok) return;
    const conv = await res.json();
    await loadConversations();
    setActiveConversation(conv.id, conv.title);
  } catch (e) {
    console.error(e);
  }
}

async function sendPrompt() {
  if (!accessToken) {
    alert("Haz login primero");
    return;
  }
  const prompt = promptInput.value.trim();
  if (!prompt) return;
  if (!currentConversationId) {
    await createConversation();
  }

  const isFirstMessage =
    chatBox.children.length === 0 ||
    (chatBox.children.length === 1 && chatBox.querySelector(".welcome"));
  if (isFirstMessage && currentConversationId) {
    try {
      const titleRes = await fetch(`/conversations/${currentConversationId}/generate-title`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + accessToken,
        },
        body: JSON.stringify({ prompt }),
      });
      if (titleRes.ok) {
        const titleData = await titleRes.json();
        convTitle.textContent = titleData.title;
        const activeItem = document.querySelector(`[data-id="${currentConversationId}"]`);
        if (activeItem) {
          const titleSpan = activeItem.querySelector(".conv-title");
          if (titleSpan) titleSpan.textContent = titleData.title;
        }
      }
    } catch (e) {
      console.error("Error generando título:", e);
    }
  }

  append(prompt, false);
  promptInput.value = "";
  setStatus("Generando respuesta...");
  document.getElementById("btnSend").disabled = true;

  const assistantMsgDiv = document.createElement("div");
  assistantMsgDiv.className = "msg assistant";
  assistantMsgDiv.innerHTML = "<strong>Assistant:</strong> ";
  chatBox.appendChild(assistantMsgDiv);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + accessToken,
      },
      body: JSON.stringify({ prompt, conversation_id: currentConversationId }),
    });
    if (!res.ok) {
      const errText = await res.text();
      append("Error: " + errText, true);
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      assistantMsgDiv.innerHTML = `<strong>Assistant:</strong> ${escapeHtml(buf)}`;
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  } catch (err) {
    append("Error: " + err.message, true);
  } finally {
    setStatus("");
    document.getElementById("btnSend").disabled = false;
  }
}

async function changePassword() {
  if (!accessToken) return;
  const current = document.getElementById("currentPassword").value.trim();
  const newPw = document.getElementById("newPassword").value.trim();
  const confirm = document.getElementById("confirmPassword").value.trim();
  if (!current || !newPw || newPw !== confirm) {
    pwStatus.textContent = "Revisa las contraseñas (deben coincidir y no estar vacías).";
    return;
  }
  pwStatus.textContent = "Guardando...";
  try {
    const res = await fetch("/auth/change-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + accessToken,
      },
      body: JSON.stringify({ current_password: current, new_password: newPw }),
    });
    if (!res.ok) {
      const err = await res.text();
      pwStatus.textContent = "Error: " + err;
    } else {
      pwStatus.textContent = "Contraseña actualizada.";
      document.getElementById("currentPassword").value = "";
      document.getElementById("newPassword").value = "";
      document.getElementById("confirmPassword").value = "";
    }
  } catch (e) {
    pwStatus.textContent = "Error: " + e.message;
  }
}

async function loadConfigInfo() {
  if (!accessToken) return;
  try {
    const res = await fetch("/config/info", {
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById("cfgModel").value = data.ollama_model || "";
    document.getElementById("cfgHost").value = data.ollama_host || "";
    document.getElementById("cfgTemp").value = data.ollama_temperature ?? "";
    document.getElementById("cfgTopP").value = data.ollama_top_p ?? "";
    document.getElementById("cfgMaxTokens").value = data.ollama_max_tokens ?? "";
  } catch (e) {
    console.error(e);
  }
}

async function pingOllama() {
  if (!accessToken) return;
  ollamaStatus.textContent = "Probando...";
  try {
    const res = await fetch("/config/test-ollama", {
      method: "POST",
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) {
      const err = await res.text();
      ollamaStatus.textContent = "Error: " + err;
      return;
    }
    const data = await res.json();
    ollamaStatus.textContent = data.ok ? "Ollama OK" : "Error";
  } catch (e) {
    ollamaStatus.textContent = "Error: " + e.message;
  }
}

function logout() {
  accessToken = "";
  refreshToken = "";
  currentConversationId = null;
  chatBox.innerHTML = "";
  convTitle.textContent = "Nueva conversacion";
  convList.innerHTML = "";
  userInfo.textContent = "";
  profileInfo.textContent = "Email / rol";
  setAuthedUI(false);
}

function setAuthedUI(isAuthed) {
  if (isAuthed) {
    loginBlock.classList.add("hidden");
    qrBlock.classList.add("hidden");
    convBlock.classList.remove("hidden");
    contentShell.classList.remove("hidden");
    tabs.classList.add("visible");
    layout.classList.add("authed");
    layout.classList.remove("unauth");
  } else {
    loginBlock.classList.remove("hidden");
    qrBlock.classList.remove("hidden");
    convBlock.classList.add("hidden");
    contentShell.classList.add("hidden");
    tabs.classList.remove("visible");
    layout.classList.remove("authed");
    layout.classList.add("unauth");
    setTab("chat");
  }
}

async function loadAdminUsers() {
  if (!accessToken) return;
  adminStatus.textContent = "";
  try {
    const res = await fetch("/admin/users?limit=200", {
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) {
      adminStatus.textContent = "Error cargando usuarios (¿tienes rol admin?)";
      return;
    }
    const users = await res.json();
    adminUsers = users;
    renderReassignOptions();
    adminUserList.innerHTML = "";
    users.forEach((u) => {
      const div = document.createElement("div");
      div.className = "admin-item";
      div.dataset.id = u.id;
      div.innerHTML = `<strong>${u.email}</strong><div class="meta">Rol: ${u.role} · Última actividad: ${u.last_activity || "—"}</div>`;
      div.addEventListener("click", () => {
        adminSelectedUserId = u.id;
        adminSelectedConvId = null;
        document.querySelectorAll(".admin-item").forEach((el) => el.classList.remove("active"));
        div.classList.add("active");
        adminUserSelected.textContent = `${u.email} (id ${u.id})`;
        adminMessages.innerHTML = "";
        adminConvTitle.textContent = "Selecciona una conversación";
        renderReassignOptions(u.id);
        loadAdminConversations(u.id);
      });
      adminUserList.appendChild(div);
    });
  } catch (e) {
    adminStatus.textContent = "Error cargando usuarios";
  }
}

async function loadAdminConversations(userId) {
  if (!accessToken || !userId) return;
  try {
    const res = await fetch(`/admin/conversations?user_id=${userId}`, {
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) {
      adminStatus.textContent = "Error cargando conversaciones";
      return;
    }
    const convs = await res.json();
    adminConvList.innerHTML = "";
    convs.forEach((c) => {
      const item = document.createElement("div");
      item.className = "conv-item";
      item.dataset.id = c.id;
      const span = document.createElement("span");
      span.className = "conv-title";
      span.textContent = c.title || `Conv ${c.id}`;
      item.append(span);
      item.addEventListener("click", () => {
        document.querySelectorAll("#adminConvList .conv-item").forEach((el) => el.classList.remove("active"));
        item.classList.add("active");
        adminSelectedConvId = c.id;
        adminConvTitle.textContent = c.title || `Conv ${c.id}`;
        loadAdminMessages(c.id);
      });
      adminConvList.appendChild(item);
    });
    if (convs.length === 0) {
      adminConvList.innerHTML = '<div class="muted">Sin conversaciones</div>';
    }
  } catch (e) {
    adminStatus.textContent = "Error cargando conversaciones";
  }
}

async function loadAdminMessages(conversationId) {
  if (!accessToken || !conversationId) return;
  try {
    const res = await fetch(`/admin/conversations/${conversationId}/messages?limit=400`, {
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) {
      adminStatus.textContent = "Error cargando mensajes";
      return;
    }
    const msgs = await res.json();
    adminMessages.innerHTML = "";
    msgs.forEach((m) => {
      const div = document.createElement("div");
      div.className = `msg ${m.role === "assistant" ? "assistant" : "user"}`;
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = m.role;
      const body = document.createElement("div");
      body.innerHTML = escapeHtml(m.content);
      div.append(meta, body);
      adminMessages.appendChild(div);
    });
    if (msgs.length === 0) {
      adminMessages.innerHTML = '<div class="welcome">Sin mensajes</div>';
    }
  } catch (e) {
    adminStatus.textContent = "Error cargando mensajes";
  }
}

async function reassignConversation() {
  if (!accessToken || !adminSelectedConvId) {
    adminStatus.textContent = "Selecciona una conversación";
    return;
  }
  const targetEmail = reassignSelect.value;
  if (!targetEmail) {
    adminStatus.textContent = "Elige destinatario";
    return;
  }
  adminStatus.textContent = "Reasignando...";
  try {
    const res = await fetch(`/admin/conversations/${adminSelectedConvId}/reassign`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + accessToken,
      },
      body: JSON.stringify({ target_email: targetEmail }),
    });
    if (!res.ok) {
      const err = await res.text();
      adminStatus.textContent = "Error: " + err;
      return;
    }
    adminStatus.textContent = "Reasignado.";
    if (adminSelectedUserId) {
      loadAdminConversations(adminSelectedUserId);
    }
  } catch (e) {
    adminStatus.textContent = "Error: " + e.message;
  }
}

function renderReassignOptions(currentUserId) {
  if (!reassignSelect) return;
  reassignSelect.innerHTML = "";
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Seleccionar usuario";
  reassignSelect.appendChild(placeholder);
  adminUsers.forEach((u) => {
    if (currentUserId && u.id === currentUserId) return;
    const opt = document.createElement("option");
    opt.value = u.email;
    opt.textContent = u.email;
    reassignSelect.appendChild(opt);
  });
}

async function deleteConversation(id) {
  if (!accessToken) return;
  if (!confirm("Eliminar esta conversacion?")) return;
  try {
    const res = await fetch(`/conversations/${id}`, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) return;
    if (currentConversationId === id) {
      currentConversationId = null;
      chatBox.innerHTML = "";
      convTitle.textContent = "Nueva conversacion";
    }
    await loadConversations();
  } catch (e) {
    console.error(e);
  }
}

function setStatus(text) {
  statusEl.textContent = text || "";
}

// Función para registrar nuevos usuarios
async function registerNewUser(email, password) {
  try {
    const res = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    if (!res.ok) {
      alert("Error en registro: " + (data.detail || "Error desconocido"));
      return;
    }

    alert("Cuenta creada exitosamente! Ahora puedes iniciar sesión.");
    document.getElementById("email").value = email;
    document.getElementById("password").value = password;
  } catch (err) {
    alert("Error en registro: " + err.message);
  }
}

const btnLogin = document.getElementById("btnLogin");
if (btnLogin) btnLogin.addEventListener("click", login);
const btnVerify2FA = document.getElementById("btnVerify2FA");
if (btnVerify2FA) btnVerify2FA.addEventListener("click", verify2FA);
const btnCancel2FA = document.getElementById("btnCancel2FA");
if (btnCancel2FA) btnCancel2FA.addEventListener("click", hide2FAPrompt);
const totpCode = document.getElementById("totpCode");
if (totpCode) totpCode.addEventListener("keypress", (e) => {
  if (e.key === "Enter") verify2FA();
});
const btnSend = document.getElementById("btnSend");
if (btnSend) btnSend.addEventListener("click", sendPrompt);
const btnClear = document.getElementById("btnClear");
if (btnClear) btnClear.addEventListener("click", () => {
  chatBox.innerHTML = "";
});
const btnNewConv = document.getElementById("btnNewConv");
if (btnNewConv) btnNewConv.addEventListener("click", () => {
  if (accessToken) {
    currentConversationId = null;
    convTitle.textContent = "Nueva conversacion";
    chatBox.innerHTML = '<div class="welcome">Escribe tu primer mensaje para comenzar una nueva conversación.</div>';
    createConversation();
  }
});
if (btnLogout) btnLogout.addEventListener("click", logout);
if (btnAdmin) btnAdmin.addEventListener("click", () => setTab("admin"));
if (btnDemoAdmin) btnDemoAdmin.addEventListener("click", () => {
  document.getElementById("email").value = "administrador@alvaradomazzei.cl";
  document.getElementById("password").value = "admin123";
  login();
});
// Función para mostrar QR code para un email específico
function displayQRForEmail(email) {
  const qrDisplay = document.getElementById("qrDisplayContainer");
  const secretDisplay = document.getElementById("qrSecretDisplay");

  if (!qrDisplay) return;

  if (demoQRData[email]) {
    const qr = demoQRData[email];
    qrDisplay.innerHTML = `
      <div style="text-align:center;">
        <img src="${escapeHtml(qr.qr_code)}" style="width:150px; height:150px; border:1px solid var(--border); padding:4px; background:white; border-radius:4px;" />
      </div>
    `;
    if (secretDisplay) {
      secretDisplay.style.display = "block";
      secretDisplay.innerHTML = `<strong style="font-size:11px;">Secret:</strong> <code style="word-break:break-all;">${escapeHtml(qr.secret)}</code>`;
    }
  } else {
    qrDisplay.innerHTML = '<div class="muted" style="font-size:12px;">Sin 2FA configurado</div>';
    if (secretDisplay) secretDisplay.style.display = "none";
  }
}

btnFillAdmin.addEventListener("click", () => {
  const email = "administrador@alvaradomazzei.cl";
  document.getElementById("email").value = email;
  document.getElementById("password").value = "admin123";
  displayQRForEmail(email);
});
btnFillWorker.addEventListener("click", () => {
  const email = "trabajador@alvaradomazzei.cl";
  document.getElementById("email").value = email;
  document.getElementById("password").value = "worker123";
  displayQRForEmail(email);
});
btnFillSupervisor.addEventListener("click", () => {
  const email = "supervisor@alvaradomazzei.cl";
  document.getElementById("email").value = email;
  document.getElementById("password").value = "supervisor123";
  displayQRForEmail(email);
});
const btnChangePassword = document.getElementById("btnChangePassword");
if (btnChangePassword) btnChangePassword.addEventListener("click", changePassword);
const btnPingOllama = document.getElementById("btnPingOllama");
if (btnPingOllama) btnPingOllama.addEventListener("click", pingOllama);
document.querySelectorAll(".tabs button").forEach((btn) => {
  btn.addEventListener("click", () => setTab(btn.dataset.tab));
});
if (btnReassign) btnReassign.addEventListener("click", reassignConversation);

// Registro de nuevas cuentas
if (btnRegister) {
  btnRegister.addEventListener("click", () => {
    const newEmail = prompt("Ingresa tu correo:");
    if (!newEmail) return;

    // Validar dominio permitido
    const allowedDomains = ["@alvaradomazzei.cl", "@inacapmail.cl"];
    const isValidDomain = allowedDomains.some(domain => newEmail.endsWith(domain));

    if (!isValidDomain) {
      alert("Solo se permiten correos @alvaradomazzei.cl o @inacapmail.cl");
      return;
    }

    const newPassword = prompt("Ingresa una contraseña (mínimo 8 caracteres):");
    if (!newPassword || newPassword.length < 8) {
      alert("La contraseña debe tener al menos 8 caracteres");
      return;
    }

    const confirmPassword = prompt("Confirma tu contraseña:");
    if (confirmPassword !== newPassword) {
      alert("Las contraseñas no coinciden");
      return;
    }

    // Enviar solicitud de registro
    registerNewUser(newEmail, newPassword);
  });
}

// Cargar QR codes de usuarios demo
async function loadDemoQRCodes() {
  console.log("[QR] Iniciando carga de QR codes...");
  try {
    const res = await fetch("/auth/demo-qr-codes");
    console.log("[QR] Response status:", res.status);
    if (!res.ok) {
      console.warn("[QR] Response not OK:", res.status);
      return;
    }
    const data = await res.json();
    console.log("[QR] Data recibida:", data);

    if (!data.demo_qrs || data.demo_qrs.length === 0) {
      console.warn("[QR] Sin usuarios demo con 2FA");
      return;
    }

    // Almacenar QR codes en memoria indexados por email
    console.log(`[QR] Almacenando ${data.demo_qrs.length} QR codes en memoria`);
    data.demo_qrs.forEach((qr) => {
      demoQRData[qr.email] = qr;
      console.log(`[QR] Guardado QR para: ${qr.email}`);
    });
    console.log("[QR] QR codes cargados exitosamente");
  } catch (e) {
    console.error("[QR] Error cargando QR codes:", e);
  }
}

// Cargar QR codes al iniciar (con delay para asegurar DOM listo)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadDemoQRCodes);
} else {
  loadDemoQRCodes();
}

/* RPsoft 前端逻辑（原生 JS，无构建步骤） */
"use strict";

const state = {
  characters: [],
  chats: [],
  meta: { character_order: [], pinned_characters: [], chat_order: [], pinned_chats: [] },
  activeCharacterId: null,
  currentChat: null,       // 当前打开的会话对象
  settings: null,
  sending: false,
};

const $ = (sel) => document.querySelector(sel);

async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail || ""; } catch (e) { /* ignore */ }
    throw new Error(detail || `请求失败 (${res.status})`);
  }
  return res.json();
}

/* ================= 初始化 ================= */
async function init() {
  bindEvents();
  await loadMeta();
  await Promise.all([loadCharacters(), loadChats(), loadSettings()]);
}

function bindEvents() {
  $("#btn-new-chat").addEventListener("click", () => startNewChat());
  $("#btn-send").addEventListener("click", () => sendMessage());
  $("#btn-settings").addEventListener("click", openSettings);
  $("#btn-import").addEventListener("click", () => $("#file-import").click());
  $("#btn-new-character").addEventListener("click", () => openCharacterEditor(null));
  $("#file-import").addEventListener("change", onImportFile);

  // 设置弹窗
  $("#btn-settings-save").addEventListener("click", saveSettings);
  $("#btn-settings-cancel").addEventListener("click", () => closeModal("settings-modal"));
  $("#btn-test").addEventListener("click", testConnection);

  // 设置分栏：左侧分类点击展开 / 折叠
  document.querySelectorAll(".settings-nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.panel;
      const panel = document.getElementById(`panel-${name}`);
      if (panel.classList.contains("hidden")) {
        showSettingsPanel(name);
      } else {
        panel.classList.add("hidden");
        btn.classList.remove("active");
      }
    });
  });

  // 角色弹窗
  $("#btn-character-save").addEventListener("click", saveCharacter);
  $("#btn-character-cancel").addEventListener("click", () => closeModal("character-modal"));

  // 确认弹窗
  $("#btn-confirm-cancel").addEventListener("click", () => resolveConfirm(false));
  $("#btn-confirm-ok").addEventListener("click", () => resolveConfirm(true));

  // 重命名弹窗
  $("#btn-rename-cancel").addEventListener("click", () => resolveRename(null));
  $("#btn-rename-ok").addEventListener("click", () => resolveRename($("#rename-input").value));
  $("#rename-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") resolveRename($("#rename-input").value);
  });

  // 输入框
  const input = $("#input");
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 160) + "px";
  });

  // 点击弹窗遮罩关闭
  document.querySelectorAll(".modal").forEach((m) => {
    m.addEventListener("click", (e) => {
      if (e.target === m) {
        if (m.id === "confirm-modal") {
          resolveConfirm(false);
        } else if (m.id === "rename-modal") {
          resolveRename(null);
        } else {
          m.classList.add("hidden");
        }
      }
    });
  });
}

/* ================= 角色 ================= */
async function loadCharacters() {
  state.characters = await api("/api/characters");
  renderCharacters();
}

function renderCharacters() {
  const ul = $("#character-list");
  ul.innerHTML = "";
  const chars = sortedCharacters();
  if (!chars.length) {
    ul.innerHTML = '<li class="dim">暂无角色，导入或新建一个吧</li>';
    return;
  }
  chars.forEach((c) => {
    const isPinned = (state.meta.pinned_characters || []).includes(c.id);
    const li = document.createElement("li");
    li.draggable = true;
    li.className = c.id === state.activeCharacterId ? "active" : "";
    li.innerHTML = `<span class="name">${isPinned ? "📌 " : ""}${escapeHtml(c.name)}${c.locked ? " 🔒" : ""}</span>`;
    li.title = c.locked ? "预设角色（不可编辑）" : (c.description || c.name);

    if (!c.locked) {
      const edit = document.createElement("button");
      edit.className = "edit";
      edit.textContent = "✏️";
      edit.title = "编辑角色";
      edit.addEventListener("click", (e) => { e.stopPropagation(); openCharacterEditor(c.id); });
      li.appendChild(edit);
    }

    const pin = document.createElement("button");
    pin.className = "pin" + (isPinned ? " pinned" : "");
    pin.textContent = "📌";
    pin.title = isPinned ? "取消置顶" : "置顶";
    pin.addEventListener("click", (e) => { e.stopPropagation(); togglePinCharacter(c.id); });
    li.appendChild(pin);

    if (!c.locked) {
      const del = document.createElement("button");
      del.className = "del";
      del.textContent = "✕";
      del.title = "删除角色";
      del.addEventListener("click", (e) => { e.stopPropagation(); deleteCharacter(c.id); });
      li.appendChild(del);
    }

    li.addEventListener("click", () => selectCharacter(c.id));
    li.addEventListener("dragstart", (e) => { e.dataTransfer.setData("text/plain", c.id); li.classList.add("dragging"); });
    li.addEventListener("dragend", () => li.classList.remove("dragging"));
    li.addEventListener("dragover", (e) => { e.preventDefault(); li.classList.add("drag-over"); });
    li.addEventListener("dragleave", () => li.classList.remove("drag-over"));
    li.addEventListener("drop", (e) => {
      e.preventDefault();
      li.classList.remove("drag-over");
      onCharacterDrop(e.dataTransfer.getData("text/plain"), c.id);
    });
    ul.appendChild(li);
  });
}

function selectCharacter(id) {
  state.activeCharacterId = id;
  renderCharacters();
  startNewChat();
}

async function startNewChat() {
  if (!state.activeCharacterId) {
    const first = state.characters[0];
    if (!first) { toast("请先导入或新建角色"); return; }
    state.activeCharacterId = first.id;
    renderCharacters();
  }
  try {
    const chat = await api("/api/chats", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ character_id: state.activeCharacterId }),
    });
    await openChat(chat.id);
    await loadChats();
  } catch (err) {
    toast(err.message);
  }
}

async function loadChats() {
  state.chats = await api("/api/chats");
  renderChats();
}

/* ================= 排序与置顶 ================= */
async function loadMeta() {
  state.meta = await api("/api/meta");
}

function sortedCharacters() {
  const byId = {};
  state.characters.forEach((c) => { byId[c.id] = c; });
  const pinned = (state.meta.pinned_characters || []).filter((id) => byId[id]);
  const pinnedSet = new Set(pinned);
  const ordered = (state.meta.character_order || []).filter((id) => byId[id] && !pinnedSet.has(id));
  const seen = new Set([...pinned, ...ordered]);
  const rest = state.characters
    .filter((c) => !seen.has(c.id))
    .sort((a, b) => a.name.localeCompare(b.name, "zh"));
  return [...pinned.map((id) => byId[id]), ...ordered.map((id) => byId[id]), ...rest];
}

function sortedChats() {
  const byId = {};
  state.chats.forEach((c) => { byId[c.id] = c; });
  const pinned = (state.meta.pinned_chats || []).filter((id) => byId[id]);
  const pinnedSet = new Set(pinned);
  const ordered = (state.meta.chat_order || []).filter((id) => byId[id] && !pinnedSet.has(id));
  const seen = new Set([...pinned, ...ordered]);
  const rest = state.chats
    .filter((c) => !seen.has(c.id))
    .sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0));
  return [...pinned.map((id) => byId[id]), ...ordered.map((id) => byId[id]), ...rest];
}

function reorderIds(ids, draggedId, targetId) {
  if (draggedId === targetId) return ids;
  const fromIdx = ids.indexOf(draggedId);
  const toIdx = ids.indexOf(targetId);
  if (fromIdx === -1 || toIdx === -1) return ids;
  const arr = ids.filter((id) => id !== draggedId);
  // 向下拖（原在目标上方）插到目标之后；向上拖插到目标之前
  let insertAt = arr.indexOf(targetId);
  if (fromIdx < toIdx) insertAt += 1;
  arr.splice(insertAt, 0, draggedId);
  return arr;
}

async function saveMeta() {
  state.meta = await api("/api/meta", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      character_order: state.meta.character_order,
      pinned_characters: state.meta.pinned_characters,
      chat_order: state.meta.chat_order,
      pinned_chats: state.meta.pinned_chats,
    }),
  });
}

async function togglePinCharacter(id) {
  const pinned = [...(state.meta.pinned_characters || [])];
  const order = [...(state.meta.character_order || [])];
  if (pinned.includes(id)) {
    state.meta.pinned_characters = pinned.filter((x) => x !== id);
    state.meta.character_order = [id, ...order.filter((x) => x !== id)];
  } else {
    state.meta.pinned_characters = [id, ...pinned];
    state.meta.character_order = order.filter((x) => x !== id);
  }
  await saveMeta();
  renderCharacters();
}

async function togglePinChat(id) {
  const pinned = [...(state.meta.pinned_chats || [])];
  const order = [...(state.meta.chat_order || [])];
  if (pinned.includes(id)) {
    state.meta.pinned_chats = pinned.filter((x) => x !== id);
    state.meta.chat_order = [id, ...order.filter((x) => x !== id)];
  } else {
    state.meta.pinned_chats = [id, ...pinned];
    state.meta.chat_order = order.filter((x) => x !== id);
  }
  await saveMeta();
  renderChats();
}

async function onCharacterDrop(draggedId, targetId) {
  if (draggedId === targetId) return;
  const visible = sortedCharacters().map((c) => c.id);
  const newOrder = reorderIds(visible, draggedId, targetId);
  const pinnedSet = new Set(state.meta.pinned_characters || []);
  state.meta.pinned_characters = newOrder.filter((id) => pinnedSet.has(id));
  state.meta.character_order = newOrder.filter((id) => !pinnedSet.has(id));
  await saveMeta();
  renderCharacters();
}

async function onChatDrop(draggedId, targetId) {
  if (draggedId === targetId) return;
  const visible = sortedChats().map((c) => c.id);
  const newOrder = reorderIds(visible, draggedId, targetId);
  const pinnedSet = new Set(state.meta.pinned_chats || []);
  state.meta.pinned_chats = newOrder.filter((id) => pinnedSet.has(id));
  state.meta.chat_order = newOrder.filter((id) => !pinnedSet.has(id));
  await saveMeta();
  renderChats();
}

function renderChats() {
  const ul = $("#chat-list");
  ul.innerHTML = "";
  const chats = sortedChats();
  if (!chats.length) {
    ul.innerHTML = '<li class="dim">暂无会话</li>';
    return;
  }
  chats.forEach((ch) => {
    const isPinned = (state.meta.pinned_chats || []).includes(ch.id);
    const name = ch.title || ch.character_name;
    const li = document.createElement("li");
    li.draggable = true;
    li.className = state.currentChat && state.currentChat.id === ch.id ? "active" : "";
    li.innerHTML = `<span class="name">${isPinned ? "📌 " : ""}${escapeHtml(name)}</span>`;

    const edit = document.createElement("button");
    edit.className = "edit";
    edit.textContent = "✏️";
    edit.title = "重命名会话";
    edit.addEventListener("click", (e) => { e.stopPropagation(); renameChat(ch.id); });
    li.appendChild(edit);

    const pin = document.createElement("button");
    pin.className = "pin" + (isPinned ? " pinned" : "");
    pin.textContent = "📌";
    pin.title = isPinned ? "取消置顶" : "置顶";
    pin.addEventListener("click", (e) => { e.stopPropagation(); togglePinChat(ch.id); });
    li.appendChild(pin);

    const del = document.createElement("button");
    del.className = "del";
    del.textContent = "✕";
    del.title = "删除会话";
    del.addEventListener("click", (e) => { e.stopPropagation(); deleteChat(ch.id); });
    li.appendChild(del);

    li.addEventListener("click", () => openChat(ch.id));
    li.addEventListener("dragstart", (e) => { e.dataTransfer.setData("text/plain", ch.id); li.classList.add("dragging"); });
    li.addEventListener("dragend", () => li.classList.remove("dragging"));
    li.addEventListener("dragover", (e) => { e.preventDefault(); li.classList.add("drag-over"); });
    li.addEventListener("dragleave", () => li.classList.remove("drag-over"));
    li.addEventListener("drop", (e) => {
      e.preventDefault();
      li.classList.remove("drag-over");
      onChatDrop(e.dataTransfer.getData("text/plain"), ch.id);
    });
    ul.appendChild(li);
  });
}

async function openChat(chatId) {
  state.currentChat = await api(`/api/chats/${chatId}`);
  state.activeCharacterId = state.currentChat.character_id;
  $("#chat-name").textContent = state.currentChat.character_name || "未命名";
  $("#btn-send").disabled = false;
  renderCharacters();
  renderChats();
  renderMessages();
}

async function deleteChat(chatId) {
  const ch = state.chats.find((c) => c.id === chatId);
  const name = ch ? (ch.title || ch.character_name) : "该会话";
  const ok = await confirmDialog("删除会话", `确定要删除会话「${name}」吗？删除后无法恢复。`);
  if (!ok) return;
  await api(`/api/chats/${chatId}`, { method: "DELETE" });
  if (state.currentChat && state.currentChat.id === chatId) {
    state.currentChat = null;
    $("#chat-name").textContent = "未选择角色";
    $("#btn-send").disabled = true;
    renderMessages();
  }
  await loadChats();
}

async function renameChat(chatId) {
  const ch = state.chats.find((c) => c.id === chatId);
  if (!ch) return;
  const newName = await renameDialog(ch.title || ch.character_name);
  if (newName === null || !newName.trim()) return;
  try {
    await api(`/api/chats/${chatId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newName.trim() }),
    });
  } catch (err) {
    toast(err.message);
    return;
  }
  toast("已重命名");
  await loadChats();
}

function renderMessages() {
  const box = $("#messages");
  box.innerHTML = "";
  const empty = document.createElement("div");
  empty.id = "empty-hint";
  empty.className = "empty-hint";
  empty.innerHTML = "<p>选择左侧角色，或点击「＋ 新对话」开始。</p><p class='dim'>首次使用请先在「设置」中填写 DeepSeek API Key。</p>";
  box.appendChild(empty);

  const msgs = state.currentChat ? state.currentChat.messages : [];
  if (msgs.length) empty.classList.add("hidden");
  msgs.forEach((m) => appendBubble(m.role, m.content));
  box.scrollTop = box.scrollHeight;
}

function appendBubble(role, content) {
  $("#empty-hint").classList.add("hidden");
  const box = $("#messages");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  const roleLabel = role === "user" ? "你" : (state.currentChat?.character_name || "助手");
  div.innerHTML = `<div class="role">${escapeHtml(roleLabel)}</div><div class="content"></div>`;
  div.querySelector(".content").textContent = content;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

/* ================= 发送消息（流式） ================= */
async function sendMessage() {
  if (state.sending || !state.currentChat) return;
  const input = $("#input");
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  input.style.height = "auto";
  state.sending = true;
  $("#btn-send").disabled = true;

  appendBubble("user", text);

  try {
    const res = await fetch(`/api/chats/${state.currentChat.id}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: text }),
    });
    if (!res.ok) {
      let detail = "";
      try { detail = (await res.json()).detail || ""; } catch (e) {}
      throw new Error(detail || `请求失败 (${res.status})`);
    }

    const bubble = appendBubble("assistant", "");
    const contentEl = bubble.querySelector(".content");
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let fullText = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const chunk = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        for (const line of chunk.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          let evt;
          try { evt = JSON.parse(line.slice(6)); } catch (e) { continue; }
          if (evt.delta) {
            fullText += evt.delta;
            contentEl.textContent = fullText;
            $("#messages").scrollTop = $("#messages").scrollHeight;
          } else if (evt.error) {
            contentEl.textContent = fullText + (fullText ? "\n" : "") + `⚠ ${evt.error}`;
          } else if (evt.done) {
            contentEl.textContent = evt.message?.content || fullText;
          }
        }
      }
    }
    // 更新内存中的会话（下次打开时从服务器重新拉取即可）
  } catch (err) {
    toast(err.message);
  } finally {
    state.sending = false;
    $("#btn-send").disabled = !state.currentChat;
    $("#input").focus();
  }
}

/* ================= 角色导入 / 编辑 ================= */
async function onImportFile(e) {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  const buf = await file.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(buf);
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  const b64 = btoa(binary);
  try {
    const card = await api("/api/characters/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name, data_base64: b64 }),
    });
    toast(`已导入角色「${card.name}」`);
    await loadCharacters();
    state.activeCharacterId = card.id;
    renderCharacters();
    startNewChat();
  } catch (err) {
    toast(`导入失败: ${err.message}`);
  }
}

function openCharacterEditor(charId) {
  if (charId) {
    const ch = state.characters.find((c) => c.id === charId);
    if (ch && ch.locked) {
      toast("预设角色不可编辑");
      return;
    }
  }
  const modal = $("#character-modal");
  $("#character-modal-title").textContent = charId ? "编辑角色" : "新建角色";
  const empty = { name: "", tags: "", description: "", personality: "", scenario: "", greeting: "", dialogue_examples: "", system_prompt: "" };

  if (charId) {
    api(`/api/characters/${charId}`).then((card) => {
      fillCharacterForm({ ...card, tags: (card.tags || []).join(", ") });
      modal.dataset.id = charId;
      modal.classList.remove("hidden");
    }).catch((err) => toast(err.message));
  } else {
    fillCharacterForm(empty);
    delete modal.dataset.id;
    modal.classList.remove("hidden");
  }
}

function fillCharacterForm(d) {
  $("#char-name").value = d.name || "";
  $("#char-tags").value = d.tags || "";
  $("#char-description").value = d.description || "";
  $("#char-personality").value = d.personality || "";
  $("#char-scenario").value = d.scenario || "";
  $("#char-greeting").value = d.greeting || "";
  $("#char-dialogue-examples").value = d.dialogue_examples || "";
  $("#char-system-prompt").value = d.system_prompt || "";
}

async function saveCharacter() {
  const payload = {
    name: $("#char-name").value.trim() || "未命名角色",
    tags: $("#char-tags").value.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
    description: $("#char-description").value,
    personality: $("#char-personality").value,
    scenario: $("#char-scenario").value,
    greeting: $("#char-greeting").value,
    dialogue_examples: $("#char-dialogue-examples").value,
    system_prompt: $("#char-system-prompt").value,
  };
  const modal = $("#character-modal");
  const id = modal.dataset.id;
  try {
    const card = await api(id ? `/api/characters/${id}` : "/api/characters", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    closeModal("character-modal");
    toast("已保存角色");
    await loadCharacters();
    state.activeCharacterId = card.id;
    renderCharacters();
    if (state.currentChat && state.currentChat.character_id === card.id) {
      $("#chat-name").textContent = card.name;
    }
  } catch (err) {
    toast(err.message);
  }
}

async function deleteCharacter(charId) {
  const ch = state.characters.find((c) => c.id === charId);
  if (!ch) return;
  const chatCount = state.chats.filter((c) => c.character_id === charId).length;
  const extra = chatCount > 0 ? `（共 ${chatCount} 个会话）` : "";
  const ok = await confirmDialog(
    "删除角色",
    `确定要删除角色「${ch.name}」吗？该角色的所有对话${extra}也会一并删除，且无法恢复。`
  );
  if (!ok) return;
  try {
    await api(`/api/characters/${charId}`, { method: "DELETE" });
  } catch (err) {
    toast(err.message);
    return;
  }
  toast("已删除角色");
  if (state.activeCharacterId === charId) {
    state.activeCharacterId = null;
  }
  if (state.currentChat && state.currentChat.character_id === charId) {
    state.currentChat = null;
    $("#chat-name").textContent = "未选择角色";
    $("#btn-send").disabled = true;
    renderMessages();
  }
  await loadCharacters();
  await loadChats();
}

/* ================= 设置 ================= */
function showSettingsPanel(name) {
  document.querySelectorAll(".settings-panel").forEach((p) => p.classList.add("hidden"));
  document.querySelectorAll(".settings-nav-item").forEach((b) => b.classList.remove("active"));
  const panel = document.getElementById(`panel-${name}`);
  const btn = document.querySelector(`.settings-nav-item[data-panel="${name}"]`);
  if (panel) panel.classList.remove("hidden");
  if (btn) btn.classList.add("active");
}

function applyTheme(theme) {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

async function loadSettings() {
  state.settings = await api("/api/settings");
  applyTheme(state.settings.theme || "light");
  updateConnBadge();
}

function openSettings() {
  if (!state.settings) return;
  $("#set-api-key").value = state.settings.api_key || "";
  $("#set-base-url").value = state.settings.base_url || "https://api.deepseek.com/v1";
  $("#set-model").value = state.settings.model || "deepseek-v4-flash";
  $("#set-temperature").value = state.settings.temperature ?? 1.0;
  $("#set-max-tokens").value = state.settings.max_tokens ?? 2048;
  $("#set-system-prompt").value = state.settings.system_prompt || "";
  $("#set-theme-dark").checked = state.settings.theme === "dark";
  $("#test-result").textContent = "";
  $("#test-result").className = "test-result";
  $("#settings-modal").classList.remove("hidden");
  showSettingsPanel("api");
}

async function saveSettings() {
  const theme = $("#set-theme-dark").checked ? "dark" : "light";
  const payload = {
    api_key: $("#set-api-key").value.trim(),
    base_url: $("#set-base-url").value.trim(),
    model: $("#set-model").value,
    temperature: parseFloat($("#set-temperature").value),
    max_tokens: parseInt($("#set-max-tokens").value, 10),
    system_prompt: $("#set-system-prompt").value,
    theme,
  };
  try {
    state.settings = await api("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    applyTheme(theme);
    closeModal("settings-modal");
    toast("设置已保存");
    updateConnBadge();
  } catch (err) {
    toast(err.message);
  }
}

async function testConnection() {
  const btn = $("#btn-test");
  const result = $("#test-result");
  btn.disabled = true;
  result.textContent = "测试中…";
  result.className = "test-result";
  // 先临时保存当前表单到后端，再测试
  try {
    await saveSettingsSilently();
    const res = await api("/api/settings/test", { method: "POST" });
    result.textContent = res.message + (res.models?.length ? `（模型: ${res.models.join(", ")}）` : "");
    result.className = "test-result " + (res.ok ? "ok" : "fail");
    updateConnBadge();
  } catch (err) {
    result.textContent = err.message;
    result.className = "test-result fail";
  } finally {
    btn.disabled = false;
  }
}

async function saveSettingsSilently() {
  const theme = $("#set-theme-dark").checked ? "dark" : "light";
  const payload = {
    api_key: $("#set-api-key").value.trim(),
    base_url: $("#set-base-url").value.trim(),
    model: $("#set-model").value,
    temperature: parseFloat($("#set-temperature").value),
    max_tokens: parseInt($("#set-max-tokens").value, 10),
    system_prompt: $("#set-system-prompt").value,
    theme,
  };
  state.settings = await api("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  applyTheme(theme);
}

function updateConnBadge() {
  const badge = $("#conn-badge");
  if (!state.settings) return;
  if (state.settings.api_key) {
    badge.textContent = "已配置 Key";
    badge.className = "badge badge-ok";
  } else {
    badge.textContent = "未配置 Key";
    badge.className = "badge badge-fail";
  }
}

/* ================= 工具 ================= */
function closeModal(id) {
  $("#" + id).classList.add("hidden");
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

let confirmResolver = null;

function resolveConfirm(result) {
  $("#confirm-modal").classList.add("hidden");
  if (confirmResolver) {
    confirmResolver(result);
    confirmResolver = null;
  }
}

function confirmDialog(title, message, okText = "删除") {
  $("#confirm-title").textContent = title;
  $("#confirm-message").textContent = message;
  $("#btn-confirm-ok").textContent = okText;
  $("#confirm-modal").classList.remove("hidden");
  return new Promise((resolve) => { confirmResolver = resolve; });
}

let renameResolver = null;

function resolveRename(value) {
  $("#rename-modal").classList.add("hidden");
  if (renameResolver) {
    renameResolver(value);
    renameResolver = null;
  }
}

function renameDialog(initial) {
  $("#rename-input").value = initial || "";
  $("#rename-modal").classList.remove("hidden");
  $("#rename-input").focus();
  return new Promise((resolve) => { renameResolver = resolve; });
}

let toastTimer = null;
function toast(msg) {
  let el = $("#toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.remove(), 3200);
}

init();

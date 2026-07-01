/**
 * NutriAgent AI — Main Frontend Script
 * app.js
 */

'use strict';

/* ═══════════════════════════════════════════════
   STATE
═══════════════════════════════════════════════ */
const state = {
  messages:     [],       // chat history
  userContext:  {},       // profile data sent with every request
  familyMembers: [],      // family planner members
  darkMode:     false,
};

/* ═══════════════════════════════════════════════
   UTILITIES
═══════════════════════════════════════════════ */
const $ = id => document.getElementById(id);
const showToast = (msg, type = 'success') => {
  const toastEl = $('appToast');
  $('toastBody').textContent = msg;
  toastEl.className = `toast align-items-center border-0 text-bg-${type}`;
  bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 3000 }).show();
};

const showLoading  = () => $('loadingOverlay').classList.remove('d-none');
const hideLoading  = () => $('loadingOverlay').classList.add('d-none');

/** Convert **bold**, *italic*, and • bullet markdown-lite to HTML */
function markdownToHtml(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^(#{1,3})\s+(.+)$/gm, (_, hashes, content) => {
      const level = Math.min(hashes.length + 4, 6);
      return `<h${level} style="margin:8px 0 4px;font-weight:700">${content}</h${level}>`;
    })
    .replace(/\n- /g, '\n• ')
    .replace(/^• (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/gs, m => `<ul style="padding-left:1.3rem;margin:6px 0">${m}</ul>`)
    .replace(/\n{2,}/g, '<br><br>')
    .replace(/\n/g, '<br>');
}

/* ═══════════════════════════════════════════════
   NAVIGATION — TAB SWITCHING
═══════════════════════════════════════════════ */
function switchTab(tabId) {
  document.querySelectorAll('.tab-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(a => a.classList.remove('active'));
  const section = $(`tab-${tabId}`);
  if (section) section.classList.add('active');
  document.querySelectorAll(`.nav-tab[data-tab="${tabId}"]`).forEach(el => el.classList.add('active'));
}

document.querySelectorAll('.nav-tab').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    switchTab(link.dataset.tab);
    // Close mobile navbar
    const navCollapse = document.getElementById('navbarNav');
    if (navCollapse.classList.contains('show')) {
      bootstrap.Collapse.getOrCreateInstance(navCollapse).hide();
    }
  });
});

/* ═══════════════════════════════════════════════
   DARK MODE TOGGLE
═══════════════════════════════════════════════ */
const themeToggle = $('themeToggle');
const themeIcon   = $('themeIcon');

function applyTheme(dark) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  themeIcon.className = dark ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
  state.darkMode = dark;
  localStorage.setItem('nutriagent_dark', dark);
}

themeToggle.addEventListener('click', () => applyTheme(!state.darkMode));

// Restore saved theme
const savedDark = localStorage.getItem('nutriagent_dark');
if (savedDark === 'true') applyTheme(true);

/* ═══════════════════════════════════════════════
   CHAT
═══════════════════════════════════════════════ */
const chatMessages = $('chatMessages');
const chatInput    = $('chatInput');
const sendBtn      = $('sendBtn');

function renderGreeting() {
  const greeting = document.body.dataset.greeting;
  if (greeting) {
    appendMessage('bot', greeting, new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
  }
}

function appendMessage(role, content, time) {
  const row = document.createElement('div');
  row.className = `message-row ${role === 'user' ? 'user' : 'bot'}`;

  const avatarIcon = role === 'user' ? 'bi-person-fill' : 'bi-robot';
  const timeStr    = time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const htmlContent = role === 'bot' ? markdownToHtml(content) : escapeHtml(content);

  row.innerHTML = `
    <div class="msg-avatar ${role === 'user' ? 'user' : 'bot'}">
      <i class="bi ${avatarIcon}"></i>
    </div>
    <div>
      <div class="message-bubble">${htmlContent}</div>
      <div class="msg-time">${timeStr}</div>
    </div>
  `;
  chatMessages.appendChild(row);
  scrollToBottom();
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function showTyping() {
  const row = document.createElement('div');
  row.className = 'message-row bot';
  row.id = 'typingIndicator';
  row.innerHTML = `
    <div class="msg-avatar bot"><i class="bi bi-robot"></i></div>
    <div class="message-bubble typing-bubble">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>
  `;
  chatMessages.appendChild(row);
  scrollToBottom();
}

function removeTyping() {
  const el = $('typingIndicator');
  if (el) el.remove();
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;

  chatInput.value = '';
  updateCharCount();
  appendMessage('user', text);
  state.messages.push({ role: 'user', content: text });
  sendBtn.disabled = true;
  showTyping();

  try {
    const res  = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        message:      text,
        messages:     state.messages.slice(-12),
        user_context: state.userContext,
      }),
    });
    const data = await res.json();
    removeTyping();
    if (data.reply) {
      appendMessage('bot', data.reply, data.timestamp);
      state.messages.push({ role: 'assistant', content: data.reply });
      if (state.messages.length > 30) state.messages = state.messages.slice(-30);
    } else if (data.error) {
      appendMessage('bot', `⚠️ Error: ${data.error}`);
    }
  } catch (err) {
    removeTyping();
    appendMessage('bot', '⚠️ Network error. Please check your connection and try again.');
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

// Send on Enter (Shift+Enter = new line)
chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
sendBtn.addEventListener('click', sendMessage);

// Character counter
function updateCharCount() {
  $('charCount').textContent = `${chatInput.value.length} / 1000`;
}
chatInput.addEventListener('input', updateCharCount);
chatInput.setAttribute('maxlength', 1000);

// Clear chat
$('clearChat').addEventListener('click', () => {
  chatMessages.innerHTML = '';
  state.messages = [];
  renderGreeting();
  showToast('Chat cleared', 'info');
});

// Quick prompt buttons
document.querySelectorAll('[data-prompt]').forEach(btn => {
  btn.addEventListener('click', () => {
    chatInput.value = btn.dataset.prompt;
    updateCharCount();
    switchTab('chat');
    sendMessage();
  });
});

/* ═══════════════════════════════════════════════
   DASHBOARD — Food Calorie List
═══════════════════════════════════════════════ */
async function loadFoodCalories() {
  try {
    const res  = await fetch('/api/food-calories');
    const data = await res.json();
    const list = $('foodCalList');
    list.innerHTML = Object.entries(data.foods)
      .map(([food, cal]) => `
        <div class="food-cal-item">
          <span>${food}</span>
          <span class="food-cal-badge">${cal} kcal</span>
        </div>`)
      .join('');
  } catch (_) {}
}

/* ═══════════════════════════════════════════════
   DASHBOARD — Meal Analyzer
═══════════════════════════════════════════════ */
$('analyzeMealBtn').addEventListener('click', async () => {
  const meal = $('mealAnalyzeInput').value.trim();
  if (!meal) { showToast('Please describe a meal first', 'warning'); return; }

  showLoading();
  try {
    const res  = await fetch('/api/analyze-meal', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ meal, user_context: state.userContext }),
    });
    const data = await res.json();
    const box  = $('mealAnalysisResult');
    box.classList.remove('d-none');
    box.innerHTML = markdownToHtml(data.analysis);
  } catch (_) {
    showToast('Analysis failed. Please try again.', 'danger');
  } finally {
    hideLoading();
  }
});

$('mealAnalyzeInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') $('analyzeMealBtn').click();
});

/* ═══════════════════════════════════════════════
   BMI CALCULATOR
═══════════════════════════════════════════════ */
$('calcBmiBtn').addEventListener('click', async () => {
  const weight   = parseFloat($('bmiWeight').value);
  const height   = parseFloat($('bmiHeight').value);
  const age      = parseInt($('bmiAge').value) || 25;
  const gender   = $('bmiGender').value;
  const activity = $('bmiActivity').value;

  if (!weight || !height || weight < 20 || weight > 300 || height < 100 || height > 250) {
    showToast('Please enter valid weight (20–300 kg) and height (100–250 cm)', 'warning');
    return;
  }

  showLoading();
  try {
    const res  = await fetch('/api/bmi', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ weight, height, age, gender, activity }),
    });
    const data = await res.json();
    displayBmiResults(data);
  } catch (_) {
    showToast('Calculation failed. Please try again.', 'danger');
  } finally {
    hideLoading();
  }
});

function displayBmiResults(data) {
  $('bmiResults').classList.remove('d-none');
  $('bmiValue').textContent    = data.bmi;
  $('bmiCategory').textContent = data.category;
  $('calMaintain').textContent = `${data.maintenance} kcal`;
  $('calLoss').textContent     = `${data.weight_loss} kcal`;
  $('calGain').textContent     = `${data.weight_gain} kcal`;
  $('calBmr').textContent      = `${data.bmr} kcal`;
  $('bmiTip').textContent      = data.tip;

  // Update dashboard stat
  $('dash-bmi-val').textContent = data.bmi;
  $('dash-calories').textContent = data.maintenance.toLocaleString();

  // Colour the result card
  const card = document.querySelector('.bmi-result-card');
  if (data.category === 'Normal weight') {
    card.style.background = 'linear-gradient(135deg, #059669, #10b981)';
  } else if (data.category === 'Underweight') {
    card.style.background = 'linear-gradient(135deg, #d97706, #f59e0b)';
  } else if (data.category === 'Overweight') {
    card.style.background = 'linear-gradient(135deg, #ea580c, #f97316)';
  } else {
    card.style.background = 'linear-gradient(135deg, #dc2626, #ef4444)';
  }

  // Move pointer on BMI scale
  // Scale: 10 → 40 maps to 0% → 100%
  const pct = Math.min(Math.max(((data.bmi - 10) / 30) * 100, 2), 97);
  $('bmiPointer').style.left = `${pct}%`;

  $('bmiResults').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/* ═══════════════════════════════════════════════
   MEAL PLANNER — Sample Plans
═══════════════════════════════════════════════ */
$('getMealPlanBtn').addEventListener('click', async () => {
  const dietType = $('mealDietType').value;
  const goal     = $('mealGoal').value;
  const calories = $('mealCalories').value;

  showLoading();
  try {
    const res  = await fetch('/api/meal-plan', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ diet_type: dietType, goal, calories }),
    });
    const data = await res.json();
    renderSampleMealPlan(data);
    $('aiMealPlanDisplay').classList.add('d-none');
  } catch (_) {
    showToast('Failed to fetch meal plan.', 'danger');
  } finally {
    hideLoading();
  }
});

const MEAL_META = {
  breakfast: { icon: 'bi-sunrise-fill',     label: 'Breakfast', cls: 'breakfast' },
  lunch:     { icon: 'bi-brightness-high-fill', label: 'Lunch',     cls: 'lunch'     },
  dinner:    { icon: 'bi-moon-stars-fill',   label: 'Dinner',    cls: 'dinner'    },
  snacks:    { icon: 'bi-apple',             label: 'Snacks',    cls: 'snacks'    },
};

function renderSampleMealPlan(data) {
  const container = $('mealPlanCards');
  container.innerHTML = Object.entries(data.plan)
    .map(([type, items]) => {
      const meta = MEAL_META[type] || { icon: 'bi-cup', label: type, cls: 'snacks' };
      const itemsHtml = items.map(i => `<div class="meal-item">${i}</div>`).join('');
      return `
        <div class="col-md-6 col-lg-3">
          <div class="meal-type-card">
            <div class="meal-type-header ${meta.cls}">
              <i class="bi ${meta.icon}"></i>${meta.label}
            </div>
            ${itemsHtml}
          </div>
        </div>`;
    }).join('');

  const tipsList = $('mealTipsList');
  tipsList.innerHTML = data.tips.map(t => `<li>${t}</li>`).join('');
  $('mealPlanDisplay').classList.remove('d-none');
  $('mealPlanDisplay').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/* ─── AI Meal Plan ─── */
$('getAIMealPlanBtn').addEventListener('click', async () => {
  const dietType = $('mealDietType').value;
  const goal     = $('mealGoal').value;
  const calories = $('mealCalories').value;

  const prompt = `Create a detailed 7-day ${dietType} meal plan for goal: ${goal.replace('_', ' ')}, targeting ${calories} calories/day. Include breakfast, lunch, dinner, and snacks for each day. Focus on Indian foods and ingredients.`;

  chatInput.value = prompt;
  updateCharCount();

  // Redirect to chat for AI response
  switchTab('chat');
  await sendMessage();
  showToast('AI meal plan generated in Chat tab!', 'success');
});

/* ═══════════════════════════════════════════════
   FAMILY PLANNER
═══════════════════════════════════════════════ */
$('addMemberBtn').addEventListener('click', () => {
  const name   = $('fmName').value.trim();
  const age    = parseInt($('fmAge').value) || 0;
  const gender = $('fmGender').value;
  const goal   = $('fmGoal').value;
  const diet   = $('fmDiet').value;

  if (!name || !age) {
    showToast('Please enter name and age.', 'warning');
    return;
  }
  state.familyMembers.push({ name, age, gender, goal, diet });
  renderFamilyMembers();

  // Clear form
  $('fmName').value = '';
  $('fmAge').value  = '';
  showToast(`${name} added to family!`, 'success');
});

function renderFamilyMembers() {
  const list = $('familyMembersList');
  const count = state.familyMembers.length;
  $('memberCount').textContent = `${count} member${count !== 1 ? 's' : ''}`;
  $('getFamilyPlanBtn').disabled = count === 0;

  if (count === 0) {
    list.innerHTML = `<div class="text-center text-muted py-4">
      <i class="bi bi-people fs-2 d-block mb-2"></i>No family members added yet</div>`;
    return;
  }

  list.innerHTML = state.familyMembers.map((m, i) => `
    <div class="family-member-card">
      <div class="member-avatar"><i class="bi bi-person-fill"></i></div>
      <div class="member-info">
        <div class="member-name">${m.name}</div>
        <div class="member-details">${m.age} yrs · ${m.gender} · ${m.goal} · ${m.diet}</div>
      </div>
      <button class="member-remove" data-index="${i}" title="Remove"><i class="bi bi-x-circle-fill"></i></button>
    </div>`).join('');

  // Attach remove handlers
  list.querySelectorAll('.member-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      state.familyMembers.splice(parseInt(btn.dataset.index), 1);
      renderFamilyMembers();
    });
  });
}

$('getFamilyPlanBtn').addEventListener('click', async () => {
  if (state.familyMembers.length === 0) return;
  showLoading();
  try {
    const res  = await fetch('/api/family-plan', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ members: state.familyMembers }),
    });
    const data = await res.json();
    const box  = $('familyPlanResult');
    box.classList.remove('d-none');
    $('familyPlanContent').innerHTML = markdownToHtml(data.plan);
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (_) {
    showToast('Failed to generate family plan.', 'danger');
  } finally {
    hideLoading();
  }
});

/* ═══════════════════════════════════════════════
   PROFILE
═══════════════════════════════════════════════ */
function loadProfile() {
  const saved = localStorage.getItem('nutriagent_profile');
  if (!saved) return;
  try {
    const profile = JSON.parse(saved);
    Object.assign(state.userContext, profile);
    $('profileName').value    = profile.name    || '';
    $('profileAge').value     = profile.age     || '';
    $('profileWeight').value  = profile.weight  || '';
    $('profileHeight').value  = profile.height  || '';
    $('profileGender').value  = profile.gender  || '';
    $('profileGoal').value    = profile.goal    || '';
    $('profileDiet').value    = profile.diet_type || '';
    $('profileAllergies').value = profile.allergies || '';
    $('profileMedical').value   = profile.medical   || '';
    if (profile.name) renderProfileSummary(profile);

    // Update dashboard stats
    if (profile.weight) {
      const proteinGoal = Math.round(parseFloat(profile.weight) * 0.8);
      $('dash-protein').textContent = `${proteinGoal}g`;
    }
  } catch (_) {}
}

$('saveProfileBtn').addEventListener('click', () => {
  const profile = {
    name:      $('profileName').value.trim(),
    age:       $('profileAge').value,
    weight:    $('profileWeight').value,
    height:    $('profileHeight').value,
    gender:    $('profileGender').value,
    goal:      $('profileGoal').value,
    diet_type: $('profileDiet').value,
    allergies: $('profileAllergies').value.trim(),
    medical:   $('profileMedical').value.trim(),
  };
  if (!profile.name) { showToast('Please enter your name.', 'warning'); return; }

  localStorage.setItem('nutriagent_profile', JSON.stringify(profile));
  Object.assign(state.userContext, profile);

  if (profile.weight) {
    $('dash-protein').textContent = `${Math.round(parseFloat(profile.weight) * 0.8)}g`;
  }
  renderProfileSummary(profile);
  showToast('Profile saved! AI will now personalise all responses.', 'success');
});

function renderProfileSummary(p) {
  const card = $('profileSummaryCard');
  const cont = $('profileSummaryContent');
  card.classList.remove('d-none');

  const items = [
    ['Name',        p.name],
    ['Age',         p.age ? `${p.age} years` : ''],
    ['Weight',      p.weight ? `${p.weight} kg` : ''],
    ['Height',      p.height ? `${p.height} cm` : ''],
    ['Gender',      p.gender],
    ['Goal',        p.goal],
    ['Diet',        p.diet_type],
    ['Allergies',   p.allergies || '—'],
    ['Medical',     p.medical   || '—'],
  ].filter(([, v]) => v);

  cont.innerHTML = items.map(([k, v]) => `
    <div class="profile-item">
      <span class="profile-key">${k}</span>
      <span class="profile-val">${v}</span>
    </div>`).join('');
}

/* ═══════════════════════════════════════════════
   DAILY TIP (SIDEBAR)
═══════════════════════════════════════════════ */
async function loadDailyTip() {
  try {
    const res  = await fetch('/api/tips');
    const data = await res.json();
    if (data.tips && data.tips.length) {
      const idx  = new Date().getDate() % data.tips.length;
      $('tipText').textContent = data.tips[idx].replace(/^[^\s]+\s/, ''); // strip emoji
    }
  } catch (_) {}
}

/* ═══════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════ */
(function init() {
  renderGreeting();
  loadProfile();
  loadFoodCalories();
  loadDailyTip();
})();

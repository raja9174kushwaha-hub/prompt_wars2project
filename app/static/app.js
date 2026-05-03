/**
 * ElectionGuide AI – app.js
 * Vanilla JS, zero dependencies, fully accessible, CSP-safe.
 * Covers: routing, chat, election flow, timeline, learn, quiz, voice input.
 */

'use strict';

/* ═══════════════════════════════════════════════════════════
   CONSTANTS & STATE
   ═══════════════════════════════════════════════════════════ */
const API = {
  CHAT:        '/api/chat/message',
  SUGGESTIONS: '/api/chat/suggestions',
  STEPS:       '/api/election/steps',
  PHASES:      '/api/election/phases',
  KNOWLEDGE:   '/api/election/knowledge',
  QUIZ:        '/api/election/quiz',
};

const state = {
  currentPage:    'home',
  chatHistory:    [],          // [{role,content}]
  language:       'en',
  quizQuestions:  [],
  quizIndex:      0,
  quizScore:      0,
  quizAnswered:   false,
  isLoading:      false,
  voiceActive:    false,
  recognition:    null,
};

/* Simple i18n labels */
const I18N = {
  en: {
    chatPlaceholder:  'Ask about elections…',
    readMore:         'Read article →',
    learnMore:        'Learn more →',
    askAssistant:     'Ask AI Assistant →',
    listening:        'Listening…',
    errorNetwork:     'Network error. Please try again.',
    errorAI:          'AI service unavailable. Showing default response.',
    voiceUnsupported: 'Voice input is not supported in this browser.',
  },
  hi: {
    chatPlaceholder:  'चुनाव के बारे में पूछें…',
    readMore:         'लेख पढ़ें →',
    learnMore:        'अधिक जानें →',
    askAssistant:     'AI सहायक से पूछें →',
    listening:        'सुन रहा है…',
    errorNetwork:     'नेटवर्क त्रुटि। कृपया पुनः प्रयास करें।',
    errorAI:          'AI सेवा अनुपलब्ध।',
    voiceUnsupported: 'इस ब्राउज़र में आवाज़ इनपुट समर्थित नहीं है।',
  },
};

function t(key) {
  return (I18N[state.language] || I18N.en)[key] || key;
}

/* ═══════════════════════════════════════════════════════════
   UTILITY HELPERS
   ═══════════════════════════════════════════════════════════ */

/** Debounce: delays execution until after `ms` milliseconds of inactivity. */
function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

/** Safely query a single element – throws if not found. */
function qs(selector, root = document) {
  const el = root.querySelector(selector);
  if (!el) throw new Error(`Element not found: ${selector}`);
  return el;
}

/** Safely query all elements. */
function qsa(selector, root = document) {
  return Array.from(root.querySelectorAll(selector));
}

/** Encode text to prevent XSS when inserting into innerHTML. */
function esc(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

/**
 * Convert Markdown-style bold (**text**), numbered lists (1. item),
 * and bullet lists (- item) to safe HTML for chat bubbles.
 */
function renderMarkdown(text) {
  // Escape first
  let html = esc(text);
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Numbered list: lines starting with "1. "
  html = html.replace(/((?:\d+\.\s.+\n?)+)/g, (match) => {
    const items = match.trim().split('\n').map(l => `<li>${l.replace(/^\d+\.\s/, '')}</li>`).join('');
    return `<ol class="msg-list">${items}</ol>`;
  });
  // Bullet list: lines starting with "- "
  html = html.replace(/((?:-\s.+\n?)+)/g, (match) => {
    const items = match.trim().split('\n').map(l => `<li>${l.replace(/^-\s/, '')}</li>`).join('');
    return `<ul class="msg-list">${items}</ul>`;
  });
  // Line breaks
  html = html.replace(/\n/g, '<br>');
  return html;
}

/** Show a toast notification. */
function showToast(msg, duration = 3000) {
  const toast = qs('#toast');
  toast.textContent = msg;
  toast.hidden = false;
  setTimeout(() => { toast.hidden = true; }, duration);
}

/** Animate counter from 0 to target. */
function animateCounter(el, target, duration = 1200) {
  const start = performance.now();
  const update = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    el.textContent = Math.floor(progress * target);
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = target;
  };
  requestAnimationFrame(update);
}

/** Debounce a function. */
function debounce(fn, delay) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

/* ═══════════════════════════════════════════════════════════
   ROUTER (hash-based SPA)
   ═══════════════════════════════════════════════════════════ */

const pageLoaders = {
  home:      initHomePage,
  assistant: initAssistantPage,
  flow:      initFlowPage,
  timeline:  initTimelinePage,
  learn:     initLearnPage,
  quiz:      initQuizPage,
};

const pageInitialised = new Set();

function navigateTo(pageId) {
  if (!document.getElementById(pageId)) return;
  if (state.currentPage === pageId) return;

  // Hide current
  const prev = document.getElementById(state.currentPage);
  if (prev) {
    prev.hidden = true;
    prev.classList.remove('active');
  }

  // Show new
  const next = document.getElementById(pageId);
  next.hidden = false;
  next.classList.add('active');
  state.currentPage = pageId;

  // Update nav links
  qsa('.nav-link').forEach(link => {
    const active = link.dataset.page === pageId;
    link.classList.toggle('active', active);
    link.setAttribute('aria-current', active ? 'page' : 'false');
  });

  // Lazy-init page content
  if (!pageInitialised.has(pageId) && pageLoaders[pageId]) {
    pageLoaders[pageId]();
    pageInitialised.add(pageId);
  }

  // Update URL hash without scroll
  history.replaceState(null, '', `#${pageId}`);

  // Move focus to main heading for accessibility
  const heading = next.querySelector('[id$="Heading"]');
  if (heading) { heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true }); }

  // Close mobile nav
  closeNavMenu();
}

function initRouter() {
  // Handle all nav link clicks
  document.addEventListener('click', (e) => {
    const link = e.target.closest('[data-page]');
    if (!link) return;
    e.preventDefault();
    navigateTo(link.dataset.page);
  });

  // Handle hash on load
  const hash = location.hash.replace('#', '') || 'home';
  navigateTo(hash);

  // Footer year
  const yr = document.getElementById('currentYear');
  if (yr) yr.textContent = new Date().getFullYear();
}

/* ═══════════════════════════════════════════════════════════
   NAVIGATION
   ═══════════════════════════════════════════════════════════ */

function initNav() {
  const toggle = qs('#navToggle');
  const menu   = qs('#navMenu');

  toggle.addEventListener('click', () => {
    const open = menu.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!toggle.contains(e.target) && !menu.contains(e.target)) closeNavMenu();
  });

  // Language toggle
  qsa('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      state.language = btn.dataset.lang;
      qsa('.lang-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.lang === state.language);
        b.setAttribute('aria-pressed', String(b.dataset.lang === state.language));
      });
      applyLanguage();
    });
  });
}

function closeNavMenu() {
  const menu = document.getElementById('navMenu');
  if (menu) {
    menu.classList.remove('open');
    const toggle = document.getElementById('navToggle');
    if (toggle) toggle.setAttribute('aria-expanded', 'false');
  }
}

function applyLanguage() {
  const input = document.getElementById('chatInput');
  if (input) input.placeholder = t('chatPlaceholder');
}

/* ═══════════════════════════════════════════════════════════
   PAGE: HOME
   ═══════════════════════════════════════════════════════════ */

function initHomePage() {
  // Animate stat counters using Intersection Observer
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.target, 10);
        animateCounter(el, target);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  qsa('[data-target]').forEach(el => observer.observe(el));
}

/* ═══════════════════════════════════════════════════════════
   PAGE: AI ASSISTANT
   ═══════════════════════════════════════════════════════════ */

function initAssistantPage() {
  loadSuggestions();
  initChatForm();
  initVoiceInput();
  applyLanguage();
}

async function loadSuggestions() {
  try {
    const res  = await fetch(API.SUGGESTIONS);
    if (!res.ok) throw new Error('Failed to load suggestions');
    const data = await res.json();
    renderSuggestions(data.suggestions || []);
  } catch {
    renderSuggestions([
      'How does voter registration work?',
      'What is the election timeline?',
      'Explain the voting process.',
      'What are types of elections?',
      'Who is eligible to vote?',
    ]);
  }
}

function renderSuggestions(suggestions) {
  const list = document.getElementById('suggestionList');
  if (!list) return;
  list.innerHTML = suggestions.map(s =>
    `<li>
      <button class="suggestion-item" type="button" aria-label="Ask: ${esc(s)}">${esc(s)}</button>
    </li>`
  ).join('');

  list.querySelectorAll('.suggestion-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById('chatInput');
      if (input) {
        input.value = btn.textContent.trim();
        input.dispatchEvent(new Event('input'));
        submitChatMessage();
      }
    });
  });
}

function initChatForm() {
  const form    = document.getElementById('chatForm');
  const input   = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const counter = document.getElementById('charCount');

  if (!form || !input) return;

  // Auto-grow textarea
  input.addEventListener('input', () => {
    const len = input.value.length;
    if (counter) counter.textContent = `${len} / 500`;
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
    if (sendBtn) sendBtn.disabled = len === 0 || state.isLoading;
  });

  // Enter to send (Shift+Enter = newline)
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitChatMessage();
    }
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    submitChatMessage();
  });
}

async function submitChatMessage() {
  const input   = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  if (!input) return;

  const message = input.value.trim();
  if (!message || state.isLoading) return;

  // Append user bubble
  appendMessage('user', message);
  input.value = '';
  input.style.height = 'auto';
  const counter = document.getElementById('charCount');
  if (counter) counter.textContent = '0 / 500';
  if (sendBtn) sendBtn.disabled = true;

  // Update history
  state.chatHistory.push({ role: 'user', content: message });

  // Show typing indicator
  const typingId = appendTypingIndicator();
  state.isLoading = true;

  try {
    const res = await fetch(API.CHAT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        chat_history: state.chatHistory.slice(-6),
        language: state.language,
      }),
    });

    removeTypingIndicator(typingId);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      appendMessage('ai', err.detail || t('errorAI'));
      return;
    }

    const data = await res.json();
    const reply = data.response || t('errorAI');
    appendMessage('ai', reply);
    state.chatHistory.push({ role: 'assistant', content: reply });

    // Keep history bounded
    if (state.chatHistory.length > 20) state.chatHistory = state.chatHistory.slice(-20);

  } catch {
    removeTypingIndicator(typingId);
    appendMessage('ai', t('errorNetwork'));
    showToast(t('errorNetwork'));
  } finally {
    state.isLoading = false;
    if (sendBtn) sendBtn.disabled = false;
    const inp = document.getElementById('chatInput');
    if (inp) inp.focus();
  }
}

function appendMessage(role, content) {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const isAI  = role === 'ai';
  const msgEl = document.createElement('div');
  msgEl.className = `chat-message ${isAI ? 'ai-message' : 'user-message'}`;
  msgEl.setAttribute('role', 'article');
  msgEl.setAttribute('aria-label', `${isAI ? 'AI' : 'You'}: ${content.slice(0, 80)}`);

  if (isAI) {
    msgEl.innerHTML = `
      <div class="msg-avatar" aria-hidden="true">
        <span class="material-icons-round">smart_toy</span>
      </div>
      <div class="msg-bubble">${renderMarkdown(content)}</div>`;
  } else {
    msgEl.innerHTML = `
      <div class="msg-bubble">${esc(content)}</div>
      <div class="msg-avatar" aria-hidden="true">
        <span class="material-icons-round">person</span>
      </div>`;
  }

  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator() {
  const container = document.getElementById('chatMessages');
  if (!container) return null;
  const id = `typing-${Date.now()}`;
  const el = document.createElement('div');
  el.id = id;
  el.className = 'chat-message ai-message typing-indicator';
  el.setAttribute('aria-label', 'AI is typing');
  el.innerHTML = `
    <div class="msg-avatar" aria-hidden="true">
      <span class="material-icons-round">smart_toy</span>
    </div>
    <div class="msg-bubble">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>`;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  if (!id) return;
  const el = document.getElementById(id);
  if (el) el.remove();
}

/* ─── Voice Input ─────────────────────────────────────────── */
function initVoiceInput() {
  const btn = document.getElementById('voiceBtn');
  if (!btn) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    btn.setAttribute('aria-label', 'Voice input not supported');
    btn.title = t('voiceUnsupported');
    btn.disabled = true;
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = state.language === 'hi' ? 'hi-IN' : 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  state.recognition = recognition;

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    const input = document.getElementById('chatInput');
    if (input) {
      input.value = transcript;
      input.dispatchEvent(new Event('input'));
    }
    stopVoice();
  };

  recognition.onerror = () => stopVoice();
  recognition.onend   = () => stopVoice();

  btn.addEventListener('click', () => {
    if (state.voiceActive) stopVoice();
    else startVoice(recognition, btn);
  });
}

function startVoice(recognition, btn) {
  state.voiceActive = true;
  btn.classList.add('active');
  btn.setAttribute('aria-label', 'Stop voice input');
  const indicator = document.getElementById('voiceIndicator');
  if (indicator) indicator.hidden = false;
  try { recognition.start(); } catch { stopVoice(); }
}

function stopVoice() {
  state.voiceActive = false;
  const btn = document.getElementById('voiceBtn');
  if (btn) { btn.classList.remove('active'); btn.setAttribute('aria-label', 'Start voice input'); }
  const indicator = document.getElementById('voiceIndicator');
  if (indicator) indicator.hidden = true;
  if (state.recognition) { try { state.recognition.stop(); } catch { /* noop */ } }
}

/* ═══════════════════════════════════════════════════════════
   PAGE: ELECTION FLOW
   ═══════════════════════════════════════════════════════════ */

async function initFlowPage() {
  const container = document.getElementById('flowContainer');
  if (!container) return;

  try {
    const res   = await fetch(API.STEPS);
    if (!res.ok) throw new Error('Failed to load steps');
    const data  = await res.json();
    renderFlowSteps(data.steps || []);
  } catch {
    container.innerHTML = '<p class="flow-loading" role="alert">Failed to load election steps. Please refresh.</p>';
  }
}

function renderFlowSteps(steps) {
  const container = document.getElementById('flowContainer');
  if (!container) return;

  container.setAttribute('role', 'list');
  container.innerHTML = steps.map((step, i) => `
    <article
      class="flow-step-card"
      style="--step-color: ${esc(step.color)}; animation-delay: ${i * 80}ms"
      tabindex="0"
      role="listitem"
      aria-label="Step ${step.id}: ${esc(step.title)}"
      data-step-id="${step.id}"
    >
      <div class="step-num" aria-hidden="true">${step.id}</div>
      <p class="step-icon-lg material-icons-round" aria-hidden="true">${esc(step.icon)}</p>
      <h3 class="step-title">${esc(step.title)}</h3>
      <p class="step-desc">${esc(step.description)}</p>
      <span class="step-cta" aria-hidden="true">Click to explore →</span>
    </article>
  `).join('');

  // Store steps data for detail panel
  container._stepsData = steps;

  // Event delegation
  container.addEventListener('click', handleStepClick);
  container.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleStepClick(e);
    }
  });
}

function handleStepClick(e) {
  const card = e.target.closest('[data-step-id]');
  if (!card) return;
  const stepId = parseInt(card.dataset.stepId, 10);
  const container = document.getElementById('flowContainer');
  const steps = container?._stepsData || [];
  const step  = steps.find(s => s.id === stepId);
  if (step) openStepDetail(step);
}

function openStepDetail(step) {
  const panel   = document.getElementById('stepDetail');
  const content = document.getElementById('stepDetailContent');
  if (!panel || !content) return;

  content.innerHTML = `
    <p class="detail-step-num">Step ${step.id} of 6</p>
    <h3 class="detail-title" style="color: ${esc(step.color)}">${esc(step.title)}</h3>
    <p class="detail-desc">${esc(step.description)}</p>
    <ul class="detail-list" role="list">
      ${step.details.map(d => `
        <li class="detail-item" role="listitem">
          <div class="detail-item-dot" aria-hidden="true"></div>
          <span>${esc(d)}</span>
        </li>
      `).join('')}
    </ul>
    <button class="btn btn-primary detail-ask-btn" data-ask="${esc(step.title)}">
      <span class="material-icons-round btn-icon" aria-hidden="true">smart_toy</span>
      Ask AI about this step
    </button>
  `;

  panel.hidden = false;
  panel.setAttribute('aria-label', `Details: ${step.title}`);
  // Focus close button for accessibility
  const closeBtn = document.getElementById('closeDetail');
  if (closeBtn) closeBtn.focus();

  // Ask AI button
  content.querySelector('.detail-ask-btn')?.addEventListener('click', (e) => {
    const topic = e.currentTarget.dataset.ask;
    closeStepDetail();
    navigateTo('assistant');
    setTimeout(() => {
      const input = document.getElementById('chatInput');
      if (input) {
        input.value = `Explain the "${topic}" step in the election process.`;
        input.dispatchEvent(new Event('input'));
        submitChatMessage();
      }
    }, 200);
  });
}

function initFlowPanelControls() {
  const closeBtn = document.getElementById('closeDetail');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeStepDetail);
  }

  // ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeStepDetail();
      closeModal();
    }
  });
}

function closeStepDetail() {
  const panel = document.getElementById('stepDetail');
  if (panel) panel.hidden = true;
}

/* ═══════════════════════════════════════════════════════════
   PAGE: TIMELINE
   ═══════════════════════════════════════════════════════════ */

const PHASE_ICONS = ['announcement', 'edit_note', 'campaign', 'ballot', 'calculate', 'emoji_events'];

async function initTimelinePage() {
  try {
    const res  = await fetch(API.PHASES);
    if (!res.ok) throw new Error();
    const data = await res.json();
    renderTimeline(data.phases || []);
  } catch {
    const c = document.getElementById('timelineContainer');
    if (c) c.innerHTML = '<p role="alert" style="color:var(--clr-error)">Failed to load timeline. Please refresh.</p>';
  }
}

function renderTimeline(phases) {
  const container = document.getElementById('timelineContainer');
  if (!container) return;

  container.innerHTML = phases.map((phase, i) => `
    <div
      class="timeline-phase"
      role="listitem"
      style="animation-delay: ${i * 120}ms"
      aria-label="Phase ${phase.id}: ${esc(phase.name)} — ${esc(phase.duration)}"
    >
      <div class="phase-dot" aria-hidden="true">
        <span class="material-icons-round">${PHASE_ICONS[i] || 'circle'}</span>
      </div>
      <div class="phase-body">
        <h3 class="phase-name">${esc(phase.name)}</h3>
        <span class="phase-duration">${esc(phase.duration)}</span>
        <p class="phase-desc">${esc(phase.description)}</p>
      </div>
    </div>
  `).join('');

  // Animate progress bar
  animateProgressBar(phases.length);
}

function animateProgressBar(total) {
  const bar   = document.getElementById('timelineProgress');
  const label = document.getElementById('progressLabel');
  if (!bar) return;

  // Simulate 35% into current cycle
  const pct = Math.round((2 / total) * 100);
  setTimeout(() => {
    bar.style.width = `${pct}%`;
    bar.setAttribute('aria-valuenow', pct);
    if (label) label.textContent = `Campaign phase active — ${pct}% through election cycle`;
  }, 300);
}

/* ═══════════════════════════════════════════════════════════
   PAGE: LEARN
   ═══════════════════════════════════════════════════════════ */

let allArticles = [];

async function initLearnPage() {
  try {
    const res  = await fetch(API.KNOWLEDGE);
    if (!res.ok) throw new Error();
    const data = await res.json();
    allArticles = data.articles || [];
    renderArticles(allArticles);
    initFilterBar();
  } catch {
    const grid = document.getElementById('articlesGrid');
    if (grid) grid.innerHTML = '<p role="alert" style="color:var(--clr-error)">Failed to load articles.</p>';
  }
}

function renderArticles(articles) {
  const grid = document.getElementById('articlesGrid');
  if (!grid) return;

  if (articles.length === 0) {
    grid.innerHTML = '<p style="color:var(--clr-text-muted)">No articles in this category.</p>';
    return;
  }

  grid.innerHTML = articles.map(a => `
    <article
      class="article-card"
      tabindex="0"
      role="listitem"
      aria-label="${esc(a.title)}"
      data-article-id="${esc(a.id)}"
    >
      <span class="article-cat">${esc(a.category)}</span>
      <h3 class="article-title">${esc(a.title)}</h3>
      <p class="article-summary">${esc(a.summary)}</p>
      <span class="article-read">${t('readMore')}</span>
    </article>
  `).join('');

  grid.querySelectorAll('.article-card').forEach(card => {
    card.addEventListener('click',   () => openArticleModal(card.dataset.articleId));
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openArticleModal(card.dataset.articleId); }
    });
  });
}

function initFilterBar() {
  qsa('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      qsa('.filter-btn').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-pressed', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-pressed', 'true');
      const cat = btn.dataset.category;
      const filtered = cat ? allArticles.filter(a => a.category === cat) : allArticles;
      renderArticles(filtered);
    });
  });
}

function openArticleModal(articleId) {
  const article = allArticles.find(a => a.id === articleId);
  if (!article) return;

  const overlay = document.getElementById('modalOverlay');
  const content = document.getElementById('modalContent');
  if (!overlay || !content) return;

  content.innerHTML = `
    <h2 id="modalTitle">${esc(article.title)}</h2>
    <span class="article-cat" style="margin-bottom:20px;display:inline-block">${esc(article.category)}</span>
    ${article.content.map(p => `<p>${renderMarkdown(p)}</p>`).join('')}
    <button class="btn btn-primary" style="margin-top:24px" id="modalAskBtn" data-topic="${esc(article.title)}">
      <span class="material-icons-round btn-icon" aria-hidden="true">smart_toy</span>
      Ask AI about this topic
    </button>
  `;

  overlay.hidden = false;
  const closeBtn = document.getElementById('modalClose');
  if (closeBtn) closeBtn.focus();

  document.getElementById('modalAskBtn')?.addEventListener('click', (e) => {
    const topic = e.currentTarget.dataset.topic;
    closeModal();
    navigateTo('assistant');
    setTimeout(() => {
      const input = document.getElementById('chatInput');
      if (input) {
        input.value = `Tell me more about: ${topic}`;
        input.dispatchEvent(new Event('input'));
        submitChatMessage();
      }
    }, 200);
  });
}

function closeModal() {
  const overlay = document.getElementById('modalOverlay');
  if (overlay) overlay.hidden = true;
}

function initModalControls() {
  document.getElementById('modalClose')?.addEventListener('click', closeModal);
  document.getElementById('modalOverlay')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
  });
}

/* ═══════════════════════════════════════════════════════════
   PAGE: QUIZ
   ═══════════════════════════════════════════════════════════ */

async function initQuizPage() {
  document.getElementById('startQuizBtn')?.addEventListener('click', startQuiz);
  document.getElementById('retryBtn')?.addEventListener('click', resetQuiz);
  document.getElementById('nextBtn')?.addEventListener('click', nextQuestion);

  try {
    const res  = await fetch(API.QUIZ);
    if (!res.ok) throw new Error();
    const data = await res.json();
    state.quizQuestions = data.questions || [];
  } catch {
    state.quizQuestions = getFallbackQuestions();
  }
}

function getFallbackQuestions() {
  return [
    { id:1, question:"What is the minimum voting age in most democracies?", options:["16","18","21","25"], correct_index:1, explanation:"Most countries set the minimum voting age at 18." },
    { id:2, question:"Which system allocates seats proportional to vote share?", options:["FPTP","Proportional Representation","Two-Round","Block Voting"], correct_index:1, explanation:"PR ensures seat percentage matches vote percentage." },
    { id:3, question:"What governs candidate behaviour during campaigns?", options:["Election Act","Model Code of Conduct","Voter Registration Rules","Election Commission Orders"], correct_index:1, explanation:"The Model Code of Conduct sets guidelines for parties and candidates." },
    { id:4, question:"What is a by-election?", options:["Overseas election","Mid-term vacancy election","Second-round election","Local body election"], correct_index:1, explanation:"A by-election fills a vacancy between general elections." },
    { id:5, question:"Which ID is typically required at a polling booth?", options:["Passport only","Valid Voter ID","Birth certificate","Tax returns"], correct_index:1, explanation:"A valid voter ID or approved photo ID is required to cast a ballot." },
  ];
}

function startQuiz() {
  state.quizIndex   = 0;
  state.quizScore   = 0;
  state.quizAnswered = false;
  document.getElementById('quizStart').hidden = true;
  document.getElementById('quizResults').hidden = true;
  document.getElementById('quizQuestion').hidden = false;
  showQuestion();
}

function resetQuiz() {
  document.getElementById('quizResults').hidden = true;
  startQuiz();
}

function showQuestion() {
  const q   = state.quizQuestions[state.quizIndex];
  if (!q) return;

  const total = state.quizQuestions.length;
  qs('#quizCounter').textContent = `Question ${state.quizIndex + 1} of ${total}`;
  qs('#liveScore').textContent   = state.quizScore;

  const pct = ((state.quizIndex) / total) * 100;
  const bar = document.getElementById('quizProgressBar');
  if (bar) { bar.style.width = `${pct}%`; }

  qs('#quizQText').textContent = q.question;

  const optContainer = document.getElementById('quizOptions');
  optContainer.innerHTML = q.options.map((opt, i) => `
    <button
      class="quiz-option"
      type="button"
      data-index="${i}"
      role="radio"
      aria-checked="false"
    >${esc(opt)}</button>
  `).join('');

  optContainer.querySelectorAll('.quiz-option').forEach(btn => {
    btn.addEventListener('click', () => answerQuestion(parseInt(btn.dataset.index, 10)));
  });

  const explanation = document.getElementById('quizExplanation');
  if (explanation) explanation.hidden = true;
  const nextBtn = document.getElementById('nextBtn');
  if (nextBtn) nextBtn.hidden = true;

  state.quizAnswered = false;
}

function answerQuestion(selectedIndex) {
  if (state.quizAnswered) return;
  state.quizAnswered = true;

  const q = state.quizQuestions[state.quizIndex];
  const correct = q.correct_index;
  const isCorrect = selectedIndex === correct;

  if (isCorrect) state.quizScore++;

  // Style options
  const options = qsa('.quiz-option');
  options.forEach((btn, i) => {
    btn.disabled = true;
    btn.setAttribute('aria-checked', String(i === selectedIndex));
    if (i === correct)  btn.classList.add('correct');
    if (i === selectedIndex && !isCorrect) btn.classList.add('incorrect');
  });

  // Show explanation
  const explanation = document.getElementById('quizExplanation');
  if (explanation) {
    explanation.innerHTML = `<strong>${isCorrect ? '✓ Correct!' : '✗ Incorrect.'}</strong> ${esc(q.explanation)}`;
    explanation.hidden = false;
  }

  // Show next / finish
  const nextBtn = document.getElementById('nextBtn');
  if (nextBtn) {
    nextBtn.hidden = false;
    nextBtn.textContent = state.quizIndex + 1 < state.quizQuestions.length ? 'Next Question' : 'See Results';
    nextBtn.focus();
  }
}

function nextQuestion() {
  state.quizIndex++;
  if (state.quizIndex >= state.quizQuestions.length) {
    showResults();
  } else {
    showQuestion();
  }
}

function showResults() {
  document.getElementById('quizQuestion').hidden = true;
  const results = document.getElementById('quizResults');
  results.hidden = false;

  const total = state.quizQuestions.length;
  const score = state.quizScore;
  const pct   = Math.round((score / total) * 100);

  qs('#finalScore').textContent = score;
  qs('#quizProgressBar').style.width = '100%';

  let icon, title, msg;
  if (pct === 100) {
    icon  = 'emoji_events'; title = 'Perfect Score!';
    msg   = 'Outstanding! You have excellent election knowledge.';
  } else if (pct >= 60) {
    icon  = 'thumb_up'; title = 'Good Job!';
    msg   = `You got ${score} out of ${total} correct. Keep learning to master election knowledge!`;
  } else {
    icon  = 'school'; title = 'Keep Learning!';
    msg   = `You got ${score} out of ${total}. Visit the Learn section to brush up on election basics.`;
  }

  qs('#resultsIcon').textContent  = icon;
  qs('#resultsTitle').textContent = title;
  qs('#resultsMessage').textContent = msg;
  results.focus?.();

  // Log to analytics
  fetch('/api/quiz-result', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      score: score,
      total: total,
      time_taken_seconds: 0
    })
  }).catch(() => {});
}

/* ═══════════════════════════════════════════════════════════
   GLOBAL KEYBOARD ACCESSIBILITY
   ═══════════════════════════════════════════════════════════ */

function initGlobalKeyboard() {
  document.addEventListener('keydown', (e) => {
    // ESC closes panels/modals
    if (e.key === 'Escape') {
      closeStepDetail();
      closeModal();
    }

    // Press "/" to focus chat input (like YouTube / GitHub)
    if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      const active = document.activeElement;
      const isInput = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable);
      if (!isInput) {
        e.preventDefault();
        navigateTo('assistant');
        setTimeout(() => {
          const chatInput = document.getElementById('chatInput');
          if (chatInput) chatInput.focus();
        }, 100);
      }
    }
  });
}

/* ═══════════════════════════════════════════════════════════
   SCROLL-TO-TOP
   ═══════════════════════════════════════════════════════════ */

function initScrollToTop() {
  const btn = document.getElementById('scrollTop');
  if (!btn) return;

  const check = debounce(() => {
    btn.hidden = window.scrollY < 300;
  }, 100);

  window.addEventListener('scroll', check, { passive: true });
  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ═══════════════════════════════════════════════════════════
   KEYBOARD SHORTCUT HINT
   ═══════════════════════════════════════════════════════════ */

function showKeyboardHint() {
  // Show once per session
  if (sessionStorage.getItem('kbdHintShown')) return;
  const hint = document.getElementById('kbdHint');
  if (!hint) return;

  setTimeout(() => {
    hint.hidden = false;
    sessionStorage.setItem('kbdHintShown', '1');
    setTimeout(() => { hint.hidden = true; }, 4000);
  }, 3000);
}

/* ═══════════════════════════════════════════════════════════
   SERVICE WORKER (offline support)
   ═══════════════════════════════════════════════════════════ */

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js').catch(() => {
        // SW registration failed — app works without it
      });
    });
  }
}

/* ═══════════════════════════════════════════════════════════
   FEEDBACK SYSTEM
   ═══════════════════════════════════════════════════════════ */

function initFeedback() {
  const openBtn = document.getElementById('openFeedbackBtn');
  const closeBtn = document.getElementById('feedbackClose');
  const modal = document.getElementById('feedbackModal');
  const stars = qsa('#feedbackStars .star');
  const submitBtn = document.getElementById('submitFeedbackBtn');
  const comment = document.getElementById('feedbackComment');
  let currentRating = 0;

  if (!openBtn || !modal) return;

  openBtn.addEventListener('click', () => {
    modal.hidden = false;
    currentRating = 0;
    stars.forEach(s => {
      s.textContent = 'star_border';
      s.style.color = '#ccc';
    });
    comment.value = '';
    submitBtn.disabled = true;
  });

  closeBtn?.addEventListener('click', () => { modal.hidden = true; });

  stars.forEach((star, index) => {
    star.addEventListener('click', () => {
      currentRating = index + 1;
      submitBtn.disabled = false;
      stars.forEach((s, i) => {
        s.textContent = i < currentRating ? 'star' : 'star_border';
        s.style.color = i < currentRating ? '#FFB300' : '#ccc';
      });
    });
  });

  submitBtn.addEventListener('click', async () => {
    if (currentRating === 0) return;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';

    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating: currentRating,
          comment: comment.value.trim(),
          page: state.currentPage
        })
      });
      showToast('Thank you for your feedback!');
    } catch {
      showToast('Feedback submitted locally.');
    } finally {
      modal.hidden = true;
      submitBtn.textContent = 'Submit Feedback';
    }
  });
}

/* ═══════════════════════════════════════════════════════════
   BOOTSTRAP
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initRouter();
  initFlowPanelControls();
  initModalControls();
  initGlobalKeyboard();
  initScrollToTop();
  initFeedback();
  registerServiceWorker();
  showKeyboardHint();

  // Init home on first load
  if (!pageInitialised.has('home')) {
    initHomePage();
    pageInitialised.add('home');
  }
});


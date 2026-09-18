(() => {
  let csrfToken = '';
  let currentUser = null;
  const $ = (id) => document.getElementById(id);

  const style = document.createElement('style');
  style.textContent = `
    .auth-screen { position:fixed; inset:0; z-index:20; display:grid; place-items:center; padding:24px; background:#e9ece7; }
    .auth-screen[hidden] { display:none; }
    .auth-card { width:min(430px,100%); padding:32px; border:1px solid #d5ddd8; border-radius:8px; color:var(--ink); background:var(--surface); box-shadow:0 18px 45px rgba(27,41,43,.12); }
    .auth-brand { display:flex; align-items:center; gap:10px; margin-bottom:25px; }
    .auth-brand .brand-mark { flex:none; }
    .auth-card h2 { margin:0 0 6px; font-size:1.5rem; }
    .auth-copy { margin-bottom:22px; color:var(--muted); font-size:.84rem; }
    .auth-tabs { display:flex; gap:18px; margin-bottom:22px; border-bottom:1px solid #d5ddd8; }
    .auth-tab { padding:9px 0 11px; border:0; border-bottom:2px solid transparent; color:var(--muted); background:transparent; font-weight:700; }
    .auth-tab.active { color:var(--forest); border-color:var(--green); }
    .auth-form { display:grid; gap:13px; }
    .auth-form[hidden] { display:none; }
    .auth-error { min-height:18px; color:#a34535; font-size:.76rem; }
    .session-tools { display:flex; align-items:center; gap:9px; }
    .session-user { color:var(--muted); font-size:.76rem; }
    .follow-up { display:inline-flex; align-items:center; gap:5px; padding:5px 8px; border:1px solid #d6dfd9; border-radius:4px; color:var(--muted); background:transparent; font-size:.72rem; }
    .follow-up:hover { border-color:var(--green); color:var(--forest); background:var(--mint); }
    .follow-up.done { color:var(--green); border-color:#b9d3c4; background:var(--mint); }
    .support-summary { color:var(--muted); font-size:.74rem; }
    @media (max-width:620px) { .session-user { display:none; } .auth-card { padding:24px; } }
  `;
  document.head.appendChild(style);
  document.body.insertAdjacentHTML('afterbegin', `
    <section class="auth-screen" id="auth-screen" aria-label="Account access">
      <div class="auth-card">
        <div class="auth-brand"><div class="brand-mark">AR</div><div><strong>Atlas Records</strong><div class="subtle">Secure student workspace</div></div></div>
        <h2 id="auth-title">Welcome back</h2>
        <p class="auth-copy" id="auth-copy">Sign in to access your private student records.</p>
        <div class="auth-tabs"><button class="auth-tab active" id="login-tab" type="button">Sign in</button><button class="auth-tab" id="register-tab" type="button">Create account</button></div>
        <form class="auth-form" id="login-form"><label>Email<input id="login-email" type="email" autocomplete="email" required placeholder="you@example.com" /></label><label>Password<input id="login-password" type="password" autocomplete="current-password" required /></label><div class="auth-error" id="login-error"></div><button class="button primary" type="submit">Sign in</button></form>
        <form class="auth-form" id="register-form" hidden><label>Your name<input id="register-name" autocomplete="name" required placeholder="e.g. Asha Singh" /></label><label>Email<input id="register-email" type="email" autocomplete="email" required placeholder="you@example.com" /></label><label>Password<input id="register-password" type="password" autocomplete="new-password" minlength="10" required placeholder="At least 10 characters" /></label><div class="auth-error" id="register-error"></div><button class="button primary" type="submit">Create account</button></form>
      </div>
    </section>
  `);

  const authScreen = $('auth-screen');
  const loginForm = $('login-form');
  const registerForm = $('register-form');

  function notify(message, tone = '') {
    const toast = $('toast');
    toast.textContent = message;
    toast.className = `toast show ${tone}`;
    window.clearTimeout(notify.timer);
    notify.timer = window.setTimeout(() => toast.classList.remove('show'), 3000);
  }

  async function api(path, options = {}) {
    const method = options.method || 'GET';
    const headers = { ...(options.headers || {}) };
    if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }
    if (method !== 'GET') {
      if (!csrfToken) csrfToken = (await fetch('/api/auth/csrf', { credentials: 'same-origin' })).json().then((data) => data.csrf_token);
      if (csrfToken instanceof Promise) csrfToken = await csrfToken;
      headers['X-CSRF-Token'] = csrfToken;
    }
    const response = await fetch(path, { ...options, method, headers, credentials: 'same-origin' });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(data.error || 'The request could not be completed.');
      error.status = response.status;
      throw error;
    }
    return data;
  }

  function setAuthMode(mode) {
    const login = mode === 'login';
    $('login-tab').classList.toggle('active', login);
    $('register-tab').classList.toggle('active', !login);
    loginForm.hidden = !login;
    registerForm.hidden = login;
    $('auth-title').textContent = login ? 'Welcome back' : 'Create your workspace';
    $('auth-copy').textContent = login ? 'Sign in to access your private student records.' : 'Create an account for a secure, private student workspace.';
  }

  function showAuth() {
    authScreen.hidden = false;
    currentUser = null;
  }

  function showApp(user) {
    currentUser = user;
    authScreen.hidden = true;
    let tools = document.querySelector('.session-tools');
    if (!tools) {
      tools = document.createElement('div');
      tools.className = 'session-tools';
      $('export-button').before(tools);
    }
    tools.innerHTML = `<span class="session-user">${escapeHtml(user.name)}</span><button class="button ghost" id="logout-button" type="button">Sign out</button>`;
    $('logout-button').addEventListener('click', async () => {
      try { await api('/api/auth/logout', { method: 'POST' }); showAuth(); setAuthMode('login'); } catch (error) { notify(error.message, 'danger'); }
    });
  }

  function escapeHtml(value) {
    return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  }

  async function loadStudents() {
    try {
      const data = await api('/api/students');
      students = data.students || {};
      render();
    } catch (error) {
      if (error.status === 401) showAuth(); else notify(error.message, 'danger');
    }
  }

  function decorateFollowUps() {
    const headerRow = document.querySelector('thead tr');
    if (headerRow && !headerRow.querySelector('.follow-up-heading')) {
      const header = document.createElement('th');
      header.className = 'follow-up-heading';
      header.textContent = 'Follow-up';
      headerRow.appendChild(header);
    }
    const records = Object.values(students);
    const pending = records.filter((student) => Number(student.attendance) < 75 && !student.followed_up).length;
    const supportCard = document.querySelectorAll('.stat')[3];
    if (supportCard) {
      supportCard.querySelector('.stat-label').textContent = 'Follow-up queue';
      supportCard.querySelector('.stat-value').textContent = pending;
      supportCard.querySelector('.stat-detail').textContent = pending ? 'students still needing contact' : 'all support actions handled';
    }
    document.querySelectorAll('#students-tbody tr').forEach((row) => {
      const action = row.querySelector('[data-id]');
      const id = action && action.dataset.id;
      const student = id && students[id];
      if (!student || row.querySelector('.follow-up')) return;
      const cell = document.createElement('td');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `follow-up ${student.followed_up ? 'done' : ''}`;
      button.dataset.action = 'follow-up';
      button.dataset.id = id;
      button.textContent = student.followed_up ? 'Contacted' : 'Mark contacted';
      cell.appendChild(button);
      row.appendChild(cell);
    });
  }

  async function submitStudent(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
    const wasEditing = Boolean(editingId);
    const id = $('sid').value.trim();
    const payload = { id, name: $('name').value.trim(), age: Number($('age').value), course: $('course').value.trim(), attendance: Number($('attendance').value), marks: { Math: Number($('math').value), Science: Number($('science').value), English: Number($('english').value) } };
    try {
      await api(editingId ? `/api/students/${encodeURIComponent(editingId)}` : '/api/students', { method: editingId ? 'PUT' : 'POST', body: payload });
      resetForm();
      await loadStudents();
      notify(wasEditing ? 'Student record updated.' : 'Student added to the directory.');
    } catch (error) { notify(error.message, 'warning'); }
  }

  async function deleteStudent(id) {
    if (!students[id] || !window.confirm(`Remove ${students[id].name} from the directory?`)) return;
    try { await api(`/api/students/${encodeURIComponent(id)}`, { method: 'DELETE' }); await loadStudents(); notify('Student record removed.'); } catch (error) { notify(error.message, 'danger'); }
  }

  async function toggleFollowUp(id) {
    try {
      await api(`/api/students/${encodeURIComponent(id)}/follow-up`, { method: 'POST' });
      await loadStudents();
      notify(students[id]?.followed_up ? 'Student marked as contacted.' : 'Student returned to the follow-up queue.');
    } catch (error) { notify(error.message, 'danger'); }
  }

  async function importFile(file) {
    if (!file) return;
    try {
      const data = JSON.parse(await file.text());
      await api('/api/students/import', { method: 'POST', body: data });
      await loadStudents();
      notify('Records imported securely.');
    } catch (error) { notify(error.message || 'Import failed. Check the JSON structure.', 'danger'); }
  }

  async function exportRecordsFromApi() {
    try {
      const data = await api('/api/students/export');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'students_data.json';
      link.click();
      URL.revokeObjectURL(link.href);
      notify('Records exported successfully.');
    } catch (error) { notify(error.message, 'danger'); }
  }

  loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    $('login-error').textContent = '';
    try { const result = await api('/api/auth/login', { method: 'POST', body: { email: $('login-email').value, password: $('login-password').value } }); showApp(result.user); await loadStudents(); } catch (error) { $('login-error').textContent = error.message; }
  });
  registerForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    $('register-error').textContent = '';
    try { const result = await api('/api/auth/register', { method: 'POST', body: { name: $('register-name').value, email: $('register-email').value, password: $('register-password').value } }); showApp(result.user); await loadStudents(); } catch (error) { $('register-error').textContent = error.message; }
  });
  $('login-tab').addEventListener('click', () => setAuthMode('login'));
  $('register-tab').addEventListener('click', () => setAuthMode('register'));

  $('student-form').addEventListener('submit', submitStudent, true);
  $('students-tbody').addEventListener('click', (event) => {
    event.stopImmediatePropagation();
    const action = event.target.dataset.action;
    const id = event.target.dataset.id;
    if (!action || !id) return;
    if (action === 'view') showDetails(id);
    if (action === 'edit') loadForm(id);
    if (action === 'delete') deleteStudent(id);
    if (action === 'follow-up') toggleFollowUp(id);
  }, true);
  ['search-input', 'grade-filter', 'sort-select', 'attendance-filter'].forEach((id) => {
    const element = $(id);
    if (!element) return;
    element.addEventListener(element.tagName === 'INPUT' ? 'input' : 'change', (event) => { event.stopImmediatePropagation(); render(); }, true);
  });
  $('export-button').addEventListener('click', (event) => { event.stopImmediatePropagation(); exportRecordsFromApi(); }, true);
  $('import-trigger').addEventListener('click', (event) => { event.stopImmediatePropagation(); $('import-file').click(); }, true);
  $('import-file').addEventListener('change', (event) => { event.stopImmediatePropagation(); importFile(event.target.files[0]); event.target.value = ''; }, true);

  const originalRender = render;
  render = function renderWithFollowUps() {
    originalRender();
    decorateFollowUps();
  };

  (async function initialize() {
    try {
      csrfToken = await fetch('/api/auth/csrf', { credentials: 'same-origin' }).then((response) => response.json()).then((data) => data.csrf_token);
      const result = await api('/api/auth/me');
      if (result.authenticated) { showApp(result.user); await loadStudents(); } else showAuth();
    } catch (error) { showAuth(); $('login-error').textContent = 'The server is unavailable. Start the Flask app and try again.'; }
  }());
})();

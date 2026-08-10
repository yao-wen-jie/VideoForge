/**
 * 视频自动化 Web 控制台 - 前端逻辑
 */

// ===== 全局状态 =====
const state = {
  currentPage: 'dashboard',
  activeTasks: new Set(),
  pollInterval: null,
};

// ===== API 封装 =====
async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

function post(url, body) {
  return api(url, { method: 'POST', body: JSON.stringify(body) });
}

function get(url) {
  return api(url);
}

// ===== Toast 通知 =====
function toast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ===== 页面导航 =====
function initNavigation() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      const page = item.dataset.page;
      switchPage(page);
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      item.classList.add('active');
    });
  });
}

function switchPage(page) {
  state.currentPage = page;
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  const target = document.getElementById(`page-${page}`);
  if (target) target.classList.remove('hidden');

  const titles = {
    dashboard: '仪表盘',
    director: '智能导演',
    openmontage: 'OpenMontage',
    replicate: '爆款复刻',
    topics: '每日选题',
    cost: '成本追踪',
    shotcraft: 'ShotCraft',
    matrix: '选题矩阵',
    scriptgen: 'AI脚本',
    assets: '素材库',
    analytics: '数据看板',
    skills: 'Skill 工具',
    outputs: '成果库',
    tasks: '任务管理',
    workflow: '工作流',
    settings: '系统设置',
  };
  document.getElementById('pageTitle').textContent = titles[page] || page;

  // 页面特定初始化
  if (page === 'dashboard') loadDashboard();
  if (page === 'settings') loadSettings();
  if (page === 'outputs') loadOutputs();
  if (page === 'tasks') loadTasks();
  if (page === 'shotcraft') loadShotCraftLibrary();
}

// ===== 选项卡切换 =====
function initTabs() {
  document.querySelectorAll('.tabs').forEach(tabContainer => {
    tabContainer.addEventListener('click', e => {
      const tab = e.target.closest('.tab');
      if (!tab) return;
      const parent = tab.closest('.card');
      parent.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      parent.querySelectorAll('[id^="tab-"]').forEach(p => p.classList.add('hidden'));
      const target = parent.querySelector(`#tab-${tab.dataset.tab}`);
      if (target) target.classList.remove('hidden');
    });
  });
}

// ===== 仪表盘 =====
async function loadDashboard() {
  try {
    const status = await get('/api/system/status');

    // 工作流目录
    const wfEl = document.getElementById('dashWorkflowStatus');
    document.getElementById('dashWorkflowPath').textContent = status.workflow_exists ? '已连接' : '未找到';
    wfEl.innerHTML = status.workflow_exists
      ? '<span class="status-dot online"></span> 就绪'
      : '<span class="status-dot offline"></span> 未就绪 → 去设置配置路径';

    // OpenMontage
    const omEl = document.getElementById('dashOMStatus');
    document.getElementById('dashOMPath').textContent = status.openmontage_exists ? '已连接' : '未找到';
    omEl.innerHTML = status.openmontage_exists
      ? '<span class="status-dot online"></span> 就绪'
      : '<span class="status-dot offline"></span> 未就绪';

    // GPU
    document.getElementById('dashGPU').textContent = status.gpu_available ? '可用 ✅' : '不可用';
    document.getElementById('dashGPUSub').textContent = status.gpu_available ? 'NVIDIA 加速已启用' : '仅 CPU 模式';

    // FFmpeg
    document.getElementById('dashFFmpeg').textContent = status.ffmpeg_available ? '就绪 ✅' : '未找到';
    document.getElementById('dashFFmpegSub').textContent = status.ffmpeg_available ? '视频处理引擎正常' : '请安装 FFmpeg 并添加到 PATH';

    // API Keys
    const keyGrid = document.getElementById('apiKeyStatusGrid');
    keyGrid.innerHTML = '';
    const keyLabels = {
      dashscope: 'DashScope',
      deepseek: 'DeepSeek',
      openai: 'OpenAI',
      elevenlabs: 'ElevenLabs',
      google: 'Google',
      pixabay: 'Pixabay',
      pexels: 'Pexels',
      seedance: 'Seedance',
    };
    for (const [key, label] of Object.entries(keyLabels)) {
      const ok = status.api_keys?.[key];
      const el = document.createElement('span');
      el.className = `tag ${ok ? 'tag-success' : 'tag-error'}`;
      el.textContent = `${label}: ${ok ? '已配置' : '未配置'}`;
      keyGrid.appendChild(el);
    }
  } catch (e) {
    toast('加载仪表盘失败: ' + e.message, 'error');
  }

  // 历史记录
  try {
    const history = await get('/api/system/history');
    const list = document.getElementById('historyList');
    if (history.length === 0) {
      list.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">暂无操作记录</p>';
    } else {
      list.innerHTML = history.map(h => `
        <div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;">
          <span style="color:var(--text-muted);font-size:11px;">${h.time}</span>
          <span style="margin-left:8px;font-weight:500;">${h.action}</span>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error('加载历史失败', e);
  }
}

// ===== 智能导演 =====
async function directorPlan() {
  const btn = event.target;
  btn.disabled = true;
  try {
    const data = {
      topic: document.getElementById('dirTopic').value,
      style: document.getElementById('dirStyle').value,
      budget: parseFloat(document.getElementById('dirBudget').value) || 10,
      dynamic: document.getElementById('dirDynamic').checked,
      duration: document.getElementById('dirDuration').value || null,
      reference_url: document.getElementById('dirRefUrl').value,
    };
    const res = await post('/api/director/plan', data);
    showOutput('dirOutputCard', 'dirOutput', res.stdout + '\n' + (res.stderr || ''));
    toast('方案预览已生成', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function directorRun() {
  const btn = event.target;
  if (!confirm('确认执行？这会产生 API 调用费用。')) return;
  btn.disabled = true;
  try {
    const data = {
      topic: document.getElementById('dirTopic').value,
      style: document.getElementById('dirStyle').value,
      budget: parseFloat(document.getElementById('dirBudget').value) || 10,
      dynamic: document.getElementById('dirDynamic').checked,
      duration: document.getElementById('dirDuration').value || null,
      reference_url: document.getElementById('dirRefUrl').value,
    };
    const res = await post('/api/director/run', data);
    state.activeTasks.add(res.task_id);
    showOutput('dirOutputCard', 'dirOutput', `任务已启动: ${res.task_id}\n正在执行...\n`);
    startPolling(res.task_id, 'dirOutput');
    toast('导演任务已启动', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ===== OpenMontage =====
async function runOpenMontage(pipeline) {
  const btn = event.target;
  btn.disabled = true;
  try {
    let data = { pipeline };
    if (pipeline === 'factory') {
      data.topic = document.getElementById('omFactoryTopic').value;
      if (!data.topic) { toast('请输入主题', 'error'); return; }
    } else if (pipeline === 'yaosheng') {
      data.topic_id = document.getElementById('omYaoshengId').value;
      data.use_wan = document.getElementById('omYaoshengWan').checked;
      if (!data.topic_id) { toast('请输入选题 ID', 'error'); return; }
    } else if (pipeline === 'documentary') {
      data.topic = document.getElementById('omDocTopic').value;
      if (!data.topic) { toast('请输入主题', 'error'); return; }
    } else if (pipeline === 'replicate') {
      data.url = document.getElementById('omReplicateUrl').value;
      if (!data.url) { toast('请输入视频链接', 'error'); return; }
    }

    const res = await post('/api/openmontage/run', data);
    state.activeTasks.add(res.task_id);
    showOutput('omOutputCard', 'omOutput', `任务已启动: ${res.task_id}\nPipeline: ${pipeline}\n正在执行...\n`);
    startPolling(res.task_id, 'omOutput');
    toast('OpenMontage 任务已启动', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ===== 爆款复刻 =====
async function replicateAnalyze() {
  const btn = event.target;
  btn.disabled = true;
  try {
    const url = document.getElementById('repUrl').value.trim();
    if (!url) { toast('请输入视频链接', 'error'); return; }
    const res = await post('/api/replicate/analyze', { url });
    showOutput('repOutputCard', 'repOutput', res.stdout + '\n' + (res.stderr || ''));
    toast('分析完成', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function replicateRun() {
  const btn = event.target;
  if (!confirm('确认复刻？这会产生 DashScope API 费用。')) return;
  btn.disabled = true;
  try {
    const data = {
      url: document.getElementById('repUrl').value.trim(),
      shot_duration: parseInt(document.getElementById('repShotDuration').value) || 4,
      search_name: document.getElementById('repSearchName').value.trim(),
    };
    const res = await post('/api/replicate/run', data);
    state.activeTasks.add(res.task_id);
    showOutput('repOutputCard', 'repOutput', `任务已启动: ${res.task_id}\n正在复刻...\n`);
    startPolling(res.task_id, 'repOutput');
    toast('复刻任务已启动', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ===== 每日选题 =====
async function getDailyTopics() {
  const btn = event.target;
  btn.disabled = true;
  try {
    const count = document.getElementById('topicCount').value || 3;
    const res = await get(`/api/topics/daily?count=${count}`);
    const out = document.getElementById('topicOutput');
    out.style.display = 'block';
    out.textContent = res.stdout + '\n' + (res.stderr || '');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }

  // 同时加载选题池
  try {
    const pool = await get('/api/topics/list');
    const list = document.getElementById('topicPoolList');
    if (pool.categories) {
      let html = '';
      for (const [catKey, cat] of Object.entries(pool.categories)) {
        html += `<h4 style="margin:12px 0 6px;color:var(--primary-light);font-size:14px;">${cat.name || catKey}</h4>`;
        html += '<div style="display:flex;flex-direction:column;gap:4px;">';
        for (const t of cat.topics || []) {
          html += `<div style="padding:8px 10px;background:var(--bg);border-radius:6px;font-size:13px;">
            <strong>${t.title}</strong>
            <span style="color:var(--text-muted);margin-left:8px;font-size:11px;">ID: ${t.id} | 优先级: ${t.priority || 3}</span>
          </div>`;
        }
        html += '</div>';
      }
      list.innerHTML = html;
    } else {
      list.innerHTML = `<pre style="font-size:12px;color:var(--text-muted);">${JSON.stringify(pool, null, 2)}</pre>`;
    }
  } catch (e) {
    document.getElementById('topicPoolList').innerHTML = `<p style="color:var(--text-muted);">加载选题池失败: ${e.message}</p>`;
  }
}

// ===== 成本追踪 =====
async function loadCostSummary() {
  const btn = event.target;
  if (btn) btn.disabled = true;
  try {
    const days = document.getElementById('costDays').value;
    const url = days ? `/api/cost/summary?days=${days}` : '/api/cost/summary';
    const res = await get(url);
    const out = document.getElementById('costOutput');
    out.style.display = 'block';
    out.textContent = res.stdout + '\n' + (res.stderr || '');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function addCostRecord() {
  const btn = event.target;
  btn.disabled = true;
  try {
    const data = {
      topic_id: document.getElementById('costTopicId').value,
      title: document.getElementById('costTitle').value,
      mode: document.getElementById('costMode').value,
      cost: parseFloat(document.getElementById('costAmount').value) || 0,
    };
    const res = await post('/api/cost/add', data);
    toast(res.stdout?.includes('OK') ? '记录成功' : '记录完成', 'success');
    document.getElementById('costTopicId').value = '';
    document.getElementById('costTitle').value = '';
    document.getElementById('costAmount').value = '0';
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ===== Skill 工具 =====
async function runSkill(skill) {
  const btn = event.target;
  btn.disabled = true;
  try {
    let data = {};
    if (skill === 'parse') {
      data.url = document.getElementById('skillParseUrl').value.trim();
      data.download = document.getElementById('skillParseDownload').checked;
      if (!data.url) { toast('请输入视频链接', 'error'); return; }
      const res = await post('/api/skill/parse', data);
      showOutput('skillOutputCard', 'skillOutput', res.stdout + '\n' + (res.stderr || ''));
    } else if (skill === 'transcribe') {
      data.url = document.getElementById('skillTranscribeUrl').value.trim();
      if (!data.url) { toast('请输入视频链接', 'error'); return; }
      const res = await post('/api/skill/transcribe', data);
      showOutput('skillOutputCard', 'skillOutput', res.stdout + '\n' + (res.stderr || ''));
    }
    toast('执行完成', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ===== 成果库 =====
async function loadOutputs() {
  const grid = document.getElementById('outputsGrid');
  grid.innerHTML = '<p style="color:var(--text-muted);font-size:13px;grid-column:1/-1;">加载中...</p>';
  try {
    const items = await get('/api/outputs');
    if (items.length === 0) {
      grid.innerHTML = '<p style="color:var(--text-muted);font-size:13px;grid-column:1/-1;">暂无生成成果</p>';
      return;
    }
    grid.innerHTML = items.map(item => {
      const date = new Date(item.mtime * 1000).toLocaleString('zh-CN');
      return `
        <div class="video-card">
          <div class="cover">${item.has_cover ? '🖼️' : (item.has_video ? '🎬' : '📁')}</div>
          <div class="info">
            <h4>${item.name}</h4>
            <p>📅 ${date}</p>
            <p>${item.has_video ? '✅ 含视频' : '❌ 无视频'} | ${item.meta.title || ''}</p>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    grid.innerHTML = `<p style="color:var(--error);grid-column:1/-1;">加载失败: ${e.message}</p>`;
  }
}

// ===== 任务管理 =====
async function loadTasks() {
  const list = document.getElementById('tasksList');
  try {
    const tasks = await get('/api/tasks');
    const entries = Object.entries(tasks);
    if (entries.length === 0) {
      list.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">暂无运行中任务</p>';
      updateTaskBadge(0);
      return;
    }
    list.innerHTML = entries.map(([id, t]) => `
      <div style="padding:12px;background:var(--bg);border-radius:8px;margin-bottom:8px;border:1px solid var(--border);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <code style="font-size:12px;color:var(--accent);">${id}</code>
          <span class="tag ${t.status === 'running' ? 'tag-primary' : (t.status === 'done' ? 'tag-success' : 'tag-error')}">${t.status}</span>
        </div>
        <pre style="font-size:11px;color:var(--text-muted);max-height:80px;overflow:hidden;">${(t.output || '').slice(-300)}</pre>
        ${t.status === 'running' ? `<button class="btn btn-danger" style="padding:4px 10px;font-size:11px;margin-top:6px;" onclick="killTask('${id}')">⏹ 终止</button>` : ''}
      </div>
    `).join('');
    updateTaskBadge(entries.filter(([,t]) => t.status === 'running').length);
  } catch (e) {
    list.innerHTML = `<p style="color:var(--error);">加载失败: ${e.message}</p>`;
  }
}

async function killTask(taskId) {
  try {
    await post(`/api/task/${taskId}/kill`, {});
    toast('任务已终止', 'info');
    loadTasks();
  } catch (e) {
    toast(e.message, 'error');
  }
}

function updateTaskBadge(count) {
  const badge = document.getElementById('taskCountBadge');
  if (count > 0) {
    badge.textContent = `${count} 个任务运行中`;
    badge.style.display = 'inline-block';
  } else {
    badge.style.display = 'none';
  }
}

// ===== 任务轮询 =====
function startPolling(taskId, outputId) {
  const el = document.getElementById(outputId);
  const poll = async () => {
    try {
      const task = await get(`/api/task/${taskId}`);
      el.textContent = task.output || '';
      el.scrollTop = el.scrollHeight;
      if (task.status === 'done' || task.status === 'error' || task.status === 'killed') {
        state.activeTasks.delete(taskId);
        toast(`任务 ${taskId} ${task.status === 'done' ? '完成' : ('失败: ' + task.status)}`, task.status === 'done' ? 'success' : 'error');
        return;
      }
      setTimeout(poll, 1500);
    } catch (e) {
      console.error('轮询失败', e);
      setTimeout(poll, 3000);
    }
  };
  poll();
}

// ===== 系统设置 =====
async function loadSettings() {
  try {
    const cfg = await get('/api/system/config');
    document.getElementById('cfgWorkflowRoot').value = cfg.workflow_root || '';
    document.getElementById('cfgOMRoot').value = cfg.openmontage_root || '';
    document.getElementById('cfgVibeRoot').value = cfg.vibefilming_root || '';
    document.getElementById('cfgSkillsRoot').value = cfg.skills_root || '';
    document.getElementById('cfgOutputDir').value = cfg.output_dir || '';
    document.getElementById('cfgBudget').value = cfg.daily_budget || 50;

    // API Keys（显示为 ****）
    if (cfg.api_keys) {
      document.getElementById('cfgKeyDashscope').placeholder = cfg.api_keys.dashscope || '未配置';
      document.getElementById('cfgKeyDeepseek').placeholder = cfg.api_keys.deepseek || '未配置';
      document.getElementById('cfgKeyOpenAI').placeholder = cfg.api_keys.openai || '未配置';
      document.getElementById('cfgKeyElevenlabs').placeholder = cfg.api_keys.elevenlabs || '未配置';
      document.getElementById('cfgKeyGoogle').placeholder = cfg.api_keys.google || '未配置';
      document.getElementById('cfgKeyPixabay').placeholder = cfg.api_keys.pixabay || '未配置';
      document.getElementById('cfgKeyPexels').placeholder = cfg.api_keys.pexels || '未配置';
      document.getElementById('cfgKeySeedance').placeholder = cfg.api_keys.seedance || '未配置';
    }
  } catch (e) {
    toast('加载配置失败: ' + e.message, 'error');
  }
}

async function saveSettings() {
  const btn = event.target;
  btn.disabled = true;
  try {
    const data = {
      workflow_root: document.getElementById('cfgWorkflowRoot').value,
      openmontage_root: document.getElementById('cfgOMRoot').value,
      vibefilming_root: document.getElementById('cfgVibeRoot').value,
      skills_root: document.getElementById('cfgSkillsRoot').value,
      output_dir: document.getElementById('cfgOutputDir').value,
      daily_budget: parseFloat(document.getElementById('cfgBudget').value) || 50,
      api_keys: {},
    };

    // 只收集已填写的 key
    const keyMap = {
      dashscope: 'cfgKeyDashscope',
      deepseek: 'cfgKeyDeepseek',
      openai: 'cfgKeyOpenAI',
      elevenlabs: 'cfgKeyElevenlabs',
      google: 'cfgKeyGoogle',
      pixabay: 'cfgKeyPixabay',
      pexels: 'cfgKeyPexels',
      seedance: 'cfgKeySeedance',
    };
    for (const [k, id] of Object.entries(keyMap)) {
      const v = document.getElementById(id).value.trim();
      if (v) data.api_keys[k] = v;
    }

    await post('/api/system/config', data);
    toast('配置已保存', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ===== 辅助函数 =====
function showOutput(cardId, outputId, text) {
  document.getElementById(cardId).classList.remove('hidden');
  const el = document.getElementById(outputId);
  el.textContent = text;
  el.scrollTop = el.scrollHeight;
}

function formatTerminal(text) {
  // 简单的终端着色
  return text
    .replace(/\[OK\]/g, '<span class="line-ok">[OK]</span>')
    .replace(/\[ERR\]/g, '<span class="line-err">[ERR]</span>')
    .replace(/\[WARN\]/g, '<span class="line-warn">[WARN]</span>')
    .replace(/\[INFO\]/g, '<span class="line-info">[INFO]</span>');
}



// ===== ShotCraft 镜头配方卡 =====
let scLibrary = { cards: [], categories: [] };
let scSelected = new Set();

async function loadShotCraftLibrary() {
  const grid = document.getElementById('scCardsGrid');
  if (grid) grid.innerHTML = '<p style="color:var(--text-muted);font-size:13px;grid-column:1/-1;">加载中...</p>';
  
  try {
    const data = await get('/api/shotcraft/library');
    scLibrary = data;
    
    // 填充分类下拉框
    const catSelect = document.getElementById('scCategory');
    if (catSelect && data.categories) {
      catSelect.innerHTML = '<option value="">全部分类</option>' + 
        data.categories.map(c => `<option value="${c.key}">${c.icon} ${c.name}</option>`).join('');
    }
    
    renderShotCraftCards(data.cards);
  } catch (e) {
    if (grid) grid.innerHTML = `<p style="color:var(--error);grid-column:1/-1;">加载失败: ${e.message}</p>`;
  }
}

function renderShotCraftCards(cards) {
  const grid = document.getElementById('scCardsGrid');
  if (!grid) return;
  
  if (!cards || cards.length === 0) {
    grid.innerHTML = '<p style="color:var(--text-muted);font-size:13px;grid-column:1/-1;">没有找到匹配的镜头卡</p>';
    return;
  }
  
  const energyColors = {
    '低': 'tag-info',
    '中': 'tag-primary',
    '高': 'tag-success',
    '峰值': 'tag-error',
    '中高': 'tag-warning',
    '低开缓升': 'tag-info',
    '高开中收': 'tag-warning',
  };
  
  grid.innerHTML = cards.map(card => {
    const isSelected = scSelected.has(card.name);
    const energyTag = energyColors[card.energy] || 'tag-primary';
    const catMap = {
      opening: '🎬', camera: '📷', 'ui-entrance': '🎯', transition: '🔄',
      typography: '🔤', effects: '✨', interaction: '👆', data: '📊',
      rhythm: '🥁', outro: '🏁'
    };
    const catIcon = catMap[card.category] || '🎞️';
    
    return `
      <div class="video-card" style="position:relative;${isSelected ? 'border-color:var(--primary);' : ''}">
        <div style="position:absolute;top:8px;right:8px;z-index:2;">
          <button class="btn ${isSelected ? 'btn-danger' : 'btn-primary'}" 
                  style="padding:4px 10px;font-size:12px;border-radius:6px;"
                  onclick="toggleShotSelection('${card.name}')">
            ${isSelected ? '−' : '+'}
          </button>
        </div>
        <div class="cover" style="font-size:32px;height:100px;">${catIcon}</div>
        <div class="info">
          <h4 style="font-size:13px;font-weight:600;margin-bottom:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${card.name}</h4>
          <p style="font-size:11px;color:var(--text-muted);margin-bottom:8px;line-height:1.4;height:32px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">${card.summary}</p>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <span class="tag ${energyTag}" style="font-size:10px;padding:2px 8px;">${card.energy}</span>
            <span class="tag tag-info" style="font-size:10px;padding:2px 8px;">${card.duration}</span>
          </div>
          <div style="margin-top:8px;display:flex;gap:4px;flex-wrap:wrap;">
            ${(card.tags || []).map(t => `<span style="font-size:10px;color:var(--text-muted);background:var(--bg);padding:2px 6px;border-radius:4px;">${t}</span>`).join('')}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

async function searchShotCraft() {
  const query = document.getElementById('scSearch').value;
  const category = document.getElementById('scCategory').value;
  const energy = document.getElementById('scEnergy').value;
  
  try {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (category) params.append('category', category);
    if (energy) params.append('energy', energy);
    
    const data = await get(`/api/shotcraft/search?${params}`);
    renderShotCraftCards(data.cards);
  } catch (e) {
    toast(e.message, 'error');
  }
}

function toggleShotSelection(name) {
  if (scSelected.has(name)) {
    scSelected.delete(name);
  } else {
    scSelected.add(name);
  }
  updateSelectedShotsUI();
  // 重新渲染以保持选中状态一致
  searchShotCraft();
}

function updateSelectedShotsUI() {
  const list = document.getElementById('scSelectedList');
  const count = document.getElementById('scSelectedCount');
  if (!list || !count) return;
  
  count.textContent = scSelected.size;
  
  if (scSelected.size === 0) {
    list.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">点击卡片上的 + 号添加镜头</span>';
    return;
  }
  
  list.innerHTML = Array.from(scSelected).map(name => {
    const card = scLibrary.cards.find(c => c.name === name);
    return `
      <span style="display:inline-flex;align-items:center;gap:4px;background:var(--primary);color:#fff;padding:4px 10px;border-radius:16px;font-size:12px;">
        ${name}
        <span style="cursor:pointer;font-weight:bold;" onclick="toggleShotSelection('${name}')">×</span>
      </span>
    `;
  }).join('');
}

function clearSelectedShots() {
  scSelected.clear();
  updateSelectedShotsUI();
  searchShotCraft();
}

async function generateShotPlan() {
  if (scSelected.size === 0) {
    toast('请至少选择一张镜头卡', 'error');
    return;
  }
  
  const btn = event.target;
  btn.disabled = true;
  
  try {
    const data = {
      cards: Array.from(scSelected),
      product_type: 'web',
      duration: 30,
      style: 'auto',
    };
    
    const plan = await post('/api/shotcraft/generate-plan', data);
    
    const output = document.getElementById('scPlanOutput');
    const card = document.getElementById('scPlanOutputCard');
    card.classList.remove('hidden');
    
    let text = `🎬 分镜方案生成完成\n`;
    text += `═══════════════════════════════════════\n`;
    text += `产品类型: ${plan.product_type}\n`;
    text += `目标时长: ${plan.target_duration}秒 | 预估总时长: ${plan.total_duration}秒\n`;
    text += `视觉风格: ${plan.style}\n`;
    text += `镜头数量: ${plan.shots.length}\n\n`;
    
    text += `📋 分镜表\n`;
    text += `───────────────────────────────────────\n`;
    plan.shots.forEach((shot, i) => {
      text += `\n[镜头 ${shot.order}] ${shot.name}\n`;
      text += `  时间: ${shot.start_time}s - ${shot.end_time}s (约${shot.estimated_duration}秒)\n`;
      text += `  分类: ${shot.category} | 能量: ${shot.energy}\n`;
      text += `  描述: ${shot.summary}\n`;
    });
    
    text += `\n\n📝 制作备忘\n`;
    text += `───────────────────────────────────────\n`;
    plan.notes.forEach(n => text += `• ${n}\n`);
    
    text += `\n\n🔗 相关链接\n`;
    text += `• 在线 Gallery: https://vincentwei1021.github.io/video-shotcraft/\n`;
    text += `• 仓库: https://github.com/Vincentwei1021/video-shotcraft\n`;
    
    output.textContent = text;
    output.scrollTop = output.scrollHeight;
    
    toast('分镜方案已生成', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}



// ===== 工作流集成 =====
let wfCurrentTaskId = null;
let wfPollInterval = null;

async function loadWorkflowScripts() {
  try {
    const data = await get('/api/workflow/scripts');
    const grid = document.getElementById('workflowScriptsGrid');
    if (!grid) return;
    grid.innerHTML = '';
    
    const categories = {};
    data.scripts.forEach(s => {
      const cat = s.category || '其他';
      if (!categories[cat]) categories[cat] = [];
      categories[cat].push(s);
    });
    
    for (const [cat, scripts] of Object.entries(categories)) {
      const catDiv = document.createElement('div');
      catDiv.style.cssText = 'width:100%;margin-bottom:8px;';
      catDiv.innerHTML = `<div style="color:#4fc3f7;font-size:12px;margin:10px 0 6px;font-weight:600;">${cat}</div>`;
      grid.appendChild(catDiv);
      
      scripts.forEach(s => {
        const card = document.createElement('div');
        card.className = 'script-card';
        card.style.cssText = 'background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:14px;cursor:pointer;transition:all .2s;flex:1 1 280px;min-width:260px;max-width:400px;';
        card.innerHTML = `
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            <span style="font-size:22px;">${s.icon}</span>
            <span style="font-weight:600;color:#e0e6f0;">${s.name}</span>
          </div>
          <div style="color:#8899aa;font-size:12px;margin-bottom:10px;line-height:1.4;">${s.desc}</div>
          <div id="wf-params-${s.key}" style="display:none;margin-bottom:10px;"></div>
          <button class="btn btn-sm btn-primary" onclick="runWorkflowScript('${s.key}', '${s.name}')" style="width:100%;">▶ 运行</button>
        `;
        card.dataset.scriptKey = s.key;
        card.dataset.scriptParams = JSON.stringify(s.params || []);
        card.onclick = (e) => {
          if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'SELECT') {
            toggleWorkflowParams(card.dataset.scriptKey, JSON.parse(card.dataset.scriptParams));
          }
        };
        grid.appendChild(card);
      });
    }
  } catch (e) {
    console.error('加载脚本失败', e);
  }
}

function toggleWorkflowParams(key, params) {
  const el = document.getElementById(`wf-params-${key}`);
  if (!el) return;
  if (el.style.display === 'none') {
    let html = '';
    params.forEach(p => {
      if (p.type === 'select') {
        html += `<div style="margin-bottom:6px;"><label style="color:#aabbcc;font-size:11px;">${p.label}</label><select class="form-select" id="wf-param-${key}-${p.name}" style="width:100%;padding:6px;border-radius:6px;border:1px solid #2a3a50;background:#0f1720;color:#e0e6f0;">${p.options.map(o => `<option value="${o}">${o}</option>`).join('')}</select></div>`;
      } else if (p.type === 'number') {
        html += `<div style="margin-bottom:6px;"><label style="color:#aabbcc;font-size:11px;">${p.label}</label><input type="number" id="wf-param-${key}-${p.name}" value="${p.default}" min="${p.min}" max="${p.max}" style="width:100%;padding:6px;border-radius:6px;border:1px solid #2a3a50;background:#0f1720;color:#e0e6f0;"></div>`;
      } else {
        html += `<div style="margin-bottom:6px;"><label style="color:#aabbcc;font-size:11px;">${p.label}</label><input type="text" id="wf-param-${key}-${p.name}" value="${p.default || ''}" placeholder="${p.placeholder || ''}" style="width:100%;padding:6px;border-radius:6px;border:1px solid #2a3a50;background:#0f1720;color:#e0e6f0;"></div>`;
      }
    });
    el.innerHTML = html;
    el.style.display = 'block';
  } else {
    el.style.display = 'none';
  }
}

async function runWorkflowScript(key, name) {
  // 收集参数
  const params = {};
  const paramEls = document.querySelectorAll(`[id^=wf-param-${key}-]`);
  paramEls.forEach(el => {
    const paramName = el.id.replace(`wf-param-${key}-`, '');
    params[paramName] = el.value;
  });
  
  try {
    const result = await post('/api/workflow/run', { script: key, params });
    wfCurrentTaskId = result.task_id;
    document.getElementById('workflowLogCard').classList.remove('hidden');
    document.getElementById('wfLogTaskName').textContent = `— ${name}`;
    document.getElementById('workflowLogOutput').textContent = `任务 ${result.task_id} 启动中...\n`;
    startWorkflowPolling(result.task_id);
    toast(`已启动: ${name}`, 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
}

function startWorkflowPolling(taskId) {
  if (wfPollInterval) clearInterval(wfPollInterval);
  wfPollInterval = setInterval(async () => {
    try {
      const task = await get(`/api/workflow/task/${taskId}`);
      const out = document.getElementById('workflowLogOutput');
      if (task.output && task.output.length > 0) {
        out.textContent = task.output.join('\n');
        out.scrollTop = out.scrollHeight;
      }
      if (task.status !== 'running') {
        clearInterval(wfPollInterval);
        wfPollInterval = null;
        toast(`任务完成: ${task.status}`, task.status === 'completed' ? 'success' : 'error');
      }
    } catch (e) {
      clearInterval(wfPollInterval);
      wfPollInterval = null;
    }
  }, 1500);
}

async function killWorkflowTask() {
  if (!wfCurrentTaskId) return;
  try {
    await post(`/api/workflow/task/${wfCurrentTaskId}/kill`, {});
    toast('已发送终止信号', 'info');
  } catch (e) {
    toast(e.message, 'error');
  }
}

function clearWorkflowLog() {
  const out = document.getElementById('workflowLogOutput');
  if (out) out.textContent = '';
}

async function runEnvCheck() {
  const container = document.getElementById('envCheckResults');
  container.innerHTML = '<div style="color:#aabbcc;">检查中...</div>';
  try {
    const data = await get('/api/workflow/env-check');
    let html = '<div style="width:100%;"><div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;">';
    const items = [
      ['工作流目录', data.workflow_exists, '✅', '❌'],
      ['脚本目录', data.scripts_dir_exists, '✅', '❌'],
      ['成果目录', data.outputs_dir_exists, '✅', '❌'],
      ['FFmpeg', data.ffmpeg_exists, '✅', '❌'],
      ['OpenMontage', data.openmontage_exists, '✅', '❌'],
      ['虚拟环境', data.openmontage_venv, '✅', '❌'],
      ['GPU', data.gpu, '✅', '❌'],
    ];
    items.forEach(([label, ok, yes, no]) => {
      const color = ok ? '#4caf50' : '#f44336';
      html += `<div style="background:#1a2332;border:1px solid #2a3a50;border-radius:8px;padding:8px 14px;display:flex;align-items:center;gap:6px;"><span style="color:${color};font-size:16px;">${ok ? yes : no}</span><span style="color:#aabbcc;font-size:12px;">${label}</span></div>`;
    });
    html += '</div>';
    html += `<div style="color:#aabbcc;font-size:12px;">Python: ${data.python_version} | 磁盘剩余: ${data.disk_free_gb} GB</div>`;
    html += '</div>';
    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = `<div style="color:#f44336;">检查失败: ${e.message}</div>`;
  }
}





// ===== 成果浏览器 =====
async function loadOutputsV2() {
  const container = document.getElementById('outputsBrowser');
  if (!container) return;
  container.innerHTML = '<div style="color:#aabbcc;">加载中...</div>';
  try {
    const data = await get('/api/outputs/list');
    if (!data.outputs || data.outputs.length === 0) {
      container.innerHTML = '<div style="color:#aabbcc;">暂无生成成果</div>';
      return;
    }
    container.innerHTML = '';
    data.outputs.forEach(item => {
      const card = document.createElement('div');
      card.style.cssText = 'background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:12px;flex:1 1 300px;min-width:260px;max-width:400px;';
      
      let mediaPreview = '';
      if (item.video_count > 0) {
        mediaPreview = `<div style="background:#0f1720;border-radius:6px;padding:8px;margin-bottom:8px;text-align:center;"><span style="font-size:28px;">🎬</span><div style="color:#4fc3f7;font-size:11px;">${item.video_count} 个视频</div></div>`;
      } else if (item.image_count > 0) {
        mediaPreview = `<div style="background:#0f1720;border-radius:6px;padding:8px;margin-bottom:8px;text-align:center;"><span style="font-size:28px;">🖼️</span><div style="color:#4fc3f7;font-size:11px;">${item.image_count} 张图片</div></div>`;
      }
      
      const mtime = new Date(item.mtime * 1000).toLocaleString('zh-CN');
      let metaInfo = '';
      if (item.meta) {
        if (item.meta.note) metaInfo += `<div style="color:#8899aa;font-size:11px;margin-top:4px;">📝 ${item.meta.note}</div>`;
        if (item.meta.duration) metaInfo += `<div style="color:#8899aa;font-size:11px;">⏱️ ${Math.round(item.meta.duration)}秒</div>`;
      }
      
      card.innerHTML = `
        ${mediaPreview}
        <div style="font-weight:600;color:#e0e6f0;font-size:14px;margin-bottom:4px;word-break:break-all;">${item.name}</div>
        <div style="color:#667788;font-size:11px;">📅 ${mtime}</div>
        ${metaInfo}
      `;
      container.appendChild(card);
    });
  } catch (e) {
    container.innerHTML = `<div style="color:#f44336;">加载失败: ${e.message}</div>`;
  }
}

// ===== 选题管理 =====
async function loadTopicsV2() {
  const container = document.getElementById('topicPoolList');
  if (!container) return;
  try {
    const data = await get('/api/topics/list');
    container.innerHTML = '';
    if (!data.topics || data.topics.length === 0) {
      container.innerHTML = '<div style="color:#aabbcc;">选题池为空</div>';
      return;
    }
    data.topics.forEach(t => {
      const div = document.createElement('div');
      div.style.cssText = 'background:#1a2332;border:1px solid #2a3a50;border-radius:8px;padding:10px;margin-bottom:8px;';
      div.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <span style="color:#4fc3f7;font-size:12px;">[${t.category_name || t.category}]</span>
            <span style="color:#e0e6f0;font-weight:600;margin-left:6px;">${t.title || t.id}</span>
          </div>
          <span style="color:#667788;font-size:11px;">ID: ${t.id}</span>
        </div>
        <div style="color:#8899aa;font-size:12px;margin-top:4px;">${t.desc || t.description || ''}</div>
      `;
      container.appendChild(div);
    });
  } catch (e) {
    console.error('加载选题失败', e);
  }
}

// ===== 成本追踪 =====
async function loadCostSummaryV2() {
  const container = document.getElementById('costOutput');
  if (!container) return;
  try {
    const data = await get('/api/logs/cost?days=7');
    container.style.display = 'block';
    let html = `<div style="display:flex;gap:15px;margin-bottom:15px;">`;
    html += `<div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;flex:1;text-align:center;"><div style="font-size:24px;font-weight:700;color:#4fc3f7;">¥${data.total}</div><div style="color:#8899aa;font-size:12px;">近${data.days}天成本</div></div>`;
    html += `<div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;flex:1;text-align:center;"><div style="font-size:24px;font-weight:700;color:#4fc3f7;">${data.count}</div><div style="color:#8899aa;font-size:12px;">调用次数</div></div>`;
    html += `</div>`;
    
    if (Object.keys(data.by_service).length > 0) {
      html += `<div style="color:#aabbcc;font-size:13px;margin-bottom:8px;">按服务分布</div>`;
      html += `<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;">`;
      for (const [svc, cost] of Object.entries(data.by_service)) {
        html += `<div style="background:#0f1720;border-radius:6px;padding:6px 12px;font-size:12px;"><span style="color:#e0e6f0;">${svc}</span> <span style="color:#4fc3f7;">¥${cost}</span></div>`;
      }
      html += `</div>`;
    }
    
    if (data.entries && data.entries.length > 0) {
      html += `<div style="color:#aabbcc;font-size:13px;margin-bottom:8px;">最近记录</div>`;
      html += `<div style="max-height:200px;overflow:auto;">`;
      data.entries.forEach(e => {
        html += `<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1a2332;font-size:12px;"><span style="color:#8899aa;">${e.date} ${e.service || ''}</span><span style="color:#4fc3f7;">¥${e.cost || 0}</span></div>`;
      });
      html += `</div>`;
    }
    
    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = `<div style="color:#f44336;">加载失败: ${e.message}</div>`;
  }
}
async function loadTopicsV2() {
  const container = document.getElementById('topicsList');
  if (!container) return;
  try {
    const data = await get('/api/topics/list');
    container.innerHTML = '';
    if (!data.topics || data.topics.length === 0) {
      container.innerHTML = '<div style="color:#aabbcc;">选题池为空</div>';
      return;
    }
    data.topics.forEach(t => {
      const div = document.createElement('div');
      div.style.cssText = 'background:#1a2332;border:1px solid #2a3a50;border-radius:8px;padding:10px;margin-bottom:8px;';
      div.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <span style="color:#4fc3f7;font-size:12px;">[${t.category_name || t.category}]</span>
            <span style="color:#e0e6f0;font-weight:600;margin-left:6px;">${t.title || t.id}</span>
          </div>
          <span style="color:#667788;font-size:11px;">ID: ${t.id}</span>
        </div>
        <div style="color:#8899aa;font-size:12px;margin-top:4px;">${t.desc || t.description || ''}</div>
      `;
      container.appendChild(div);
    });
  } catch (e) {
    console.error('加载选题失败', e);
  }
}


// ===== 原有代码继续 =====
// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initTabs();
  loadDashboard();

  // 定期刷新任务状态
  setInterval(() => {
    if (state.currentPage === 'tasks') loadTasks();
    if (state.activeTasks.size > 0) {
      get('/api/tasks').then(tasks => {
        const running = Object.values(tasks).filter(t => t.status === 'running').length;
        updateTaskBadge(running);
      }).catch(() => {});
    }
  }, 3000);
});


// ===== 选题矩阵 =====
async function generateMatrix() {
  const btn = event.target;
  btn.disabled = true;
  try {
    const category = document.getElementById('matrixCategory').value;
    const count = document.getElementById('matrixCount').value;
    const data = await post('/api/matrix/generate', { category, count: parseInt(count) });
    
    const card = document.getElementById('matrixResultsCard');
    card.classList.remove('hidden');
    const container = document.getElementById('matrixResults');
    
    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-top:12px;">';
    data.topics.forEach((t, i) => {
      html += `
        <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:14px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="color:#4fc3f7;font-size:11px;">${t.id}</span>
            <span style="color:#667788;font-size:11px;">优先级 ${t.priority}</span>
          </div>
          <div style="font-weight:600;color:#e0e6f0;font-size:14px;margin-bottom:8px;">${t.title}</div>
          <div style="color:#8899aa;font-size:12px;margin-bottom:8px;">🪝 ${t.hook}</div>
          <div style="display:flex;flex-wrap:wrap;gap:4px;">
            ${t.tags.map(tag => `<span style="background:#0f1720;color:#aabbcc;padding:2px 8px;border-radius:4px;font-size:11px;">${tag}</span>`).join('')}
          </div>
          <div style="margin-top:10px;display:flex;gap:6px;">
            <button class="btn btn-sm btn-primary" style="padding:4px 10px;font-size:11px;" onclick="useMatrixTopic('${t.title.replace(/'/g, "\'")}')">写脚本</button>
          </div>
        </div>
      `;
    });
    html += '</div>';
    container.innerHTML = html;
    toast(`已生成 ${data.topics.length} 个选题`, 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

function useMatrixTopic(title) {
  switchPage('scriptgen');
  document.getElementById('sgTopic').value = title;
  document.getElementById('sgAiTopic').value = title;
  toast('主题已填入脚本生成器', 'info');
}

// ===== AI脚本生成 =====
async function generateScriptOutline() {
  const btn = event.target;
  btn.disabled = true;
  try {
    const data = {
      topic: document.getElementById('sgTopic').value,
      template: document.getElementById('sgTemplate').value,
      duration: parseInt(document.getElementById('sgDuration').value),
      style: document.getElementById('sgStyle').value,
    };
    if (!data.topic) { toast('请输入主题', 'error'); return; }
    const result = await post('/api/script/outline', data);
    
    const out = document.getElementById('sgOutlineOutput');
    out.classList.remove('hidden');
    let text = `🎬 ${result.topic}\n`;
    text += `模板: ${result.template} | 时长: ${result.duration}秒 | 风格: ${result.style}\n`;
    text += '═══════════════════════════════════════\n\n';
    result.segments.forEach(s => {
      text += `[${s.type.toUpperCase()}] ${s.start}s - ${s.end}s\n`;
      text += `提示: ${s.prompt}\n\n`;
    });
    text += '\n📝 制作备忘\n';
    result.notes.forEach(n => text += `• ${n}\n`);
    out.textContent = text;
    toast('脚本大纲已生成', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function generateScriptWithAI() {
  const btn = event.target;
  btn.disabled = true;
  try {
    const data = {
      topic: document.getElementById('sgAiTopic').value,
      style: document.getElementById('sgAiStyle').value,
      duration: parseInt(document.getElementById('sgAiDuration').value),
    };
    if (!data.topic) { toast('请输入主题', 'error'); return; }
    const out = document.getElementById('sgAiOutput');
    out.classList.remove('hidden');
    out.textContent = 'AI生成中，请稍候...\n（调用 DeepSeek API，可能需要10-30秒）';
    
    const result = await post('/api/script/generate', data);
    if (result.error) {
      out.textContent = `❌ 错误: ${result.error}`;
      toast(result.error, 'error');
    } else {
      out.textContent = `✅ ${result.source} 生成完成\n主题: ${result.topic}\n风格: ${result.style}\n时长: ${result.duration}秒\n\n${result.script}`;
      toast('AI脚本生成完成', 'success');
    }
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ===== 素材库 =====
async function loadAssets() {
  const container = document.getElementById('assetsList');
  const statsContainer = document.getElementById('assetsStats');
  container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">加载中...</p>';
  
  try {
    const typeFilter = document.getElementById('assetTypeFilter').value;
    const url = typeFilter ? `/api/assets/list?type=${typeFilter}` : '/api/assets/list';
    const [data, stats] = await Promise.all([
      get(url),
      get('/api/assets/stats')
    ]);
    
    // 统计
    statsContainer.innerHTML = `
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:12px;flex:1;text-align:center;">
        <div style="font-size:20px;font-weight:700;color:#4fc3f7;">${stats.total}</div>
        <div style="color:#8899aa;font-size:12px;">总素材</div>
      </div>
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:12px;flex:1;text-align:center;">
        <div style="font-size:20px;font-weight:700;color:#4fc3f7;">${stats.total_size_human || '0 B'}</div>
        <div style="color:#8899aa;font-size:12px;">占用空间</div>
      </div>
    `;
    for (const [t, c] of Object.entries(stats.by_type || {})) {
      const icons = { video: '🎬', image: '🖼️', audio: '🎵', script: '📝' };
      statsContainer.innerHTML += `
        <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:12px;flex:1;text-align:center;">
          <div style="font-size:20px;font-weight:700;color:#4fc3f7;">${icons[t] || '📄'} ${c}</div>
          <div style="color:#8899aa;font-size:12px;">${t}</div>
        </div>
      `;
    }
    
    // 列表
    if (!data.assets || data.assets.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;grid-column:1/-1;">素材库为空，请将素材放入 03-素材库/ 目录</p>';
      return;
    }
    
    container.innerHTML = data.assets.map(a => {
      const icons = { video: '🎬', image: '🖼️', audio: '🎵', script: '📝' };
      return `
        <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:12px;">
          <div style="font-size:24px;text-align:center;margin-bottom:8px;">${icons[a.type] || '📄'}</div>
          <div style="font-weight:600;color:#e0e6f0;font-size:13px;word-break:break-all;margin-bottom:4px;">${a.name}</div>
          <div style="color:#667788;font-size:11px;">${a.size_human} | ${a.mtime_str}</div>
          <div style="color:#4fc3f7;font-size:11px;margin-top:4px;">${a.type}</div>
        </div>
      `;
    }).join('');
  } catch (e) {
    container.innerHTML = `<p style="color:var(--error);">加载失败: ${e.message}</p>`;
  }
}

// ===== 数据看板 =====
async function loadDashboardStats() {
  const container = document.getElementById('analyticsContainer');
  const publishContainer = document.getElementById('publishStatsContainer');
  container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">加载中...</p>';
  
  try {
    const [stats, publish] = await Promise.all([
      get('/api/dashboard/stats'),
      get('/api/publish/stats'),
    ]);
    
    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:20px;">';
    
    // 输出统计
    const o = stats.outputs || {};
    html += `
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#4fc3f7;">${o.video_count || 0}</div>
        <div style="color:#8899aa;font-size:12px;">生成视频</div>
      </div>
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#4fc3f7;">${o.recent_7d || 0}</div>
        <div style="color:#8899aa;font-size:12px;">近7天生成</div>
      </div>
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#4fc3f7;">${o.total_size_gb || 0}GB</div>
        <div style="color:#8899aa;font-size:12px;">占用空间</div>
      </div>
    `;
    
    // 成本统计
    const c = stats.costs || {};
    html += `
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#4fc3f7;">¥${c.total_all_time || 0}</div>
        <div style="color:#8899aa;font-size:12px;">累计成本</div>
      </div>
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#4fc3f7;">¥${c.today || 0}</div>
        <div style="color:#8899aa;font-size:12px;">今日成本</div>
      </div>
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#4fc3f7;">${c.entry_count || 0}</div>
        <div style="color:#8899aa;font-size:12px;">生成次数</div>
      </div>
    `;
    
    // 素材统计
    const a = stats.assets || {};
    html += `
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#4fc3f7;">${a.total || 0}</div>
        <div style="color:#8899aa;font-size:12px;">素材总数</div>
      </div>
    `;
    
    // 任务统计
    const t = stats.tasks || {};
    html += `
      <div style="background:#1a2332;border:1px solid #2a3a50;border-radius:10px;padding:15px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#4fc3f7;">${t.scheduled_enabled || 0}</div>
        <div style="color:#8899aa;font-size:12px;">定时任务</div>
      </div>
    `;
    
    html += '</div>';
    container.innerHTML = html;
    
    // 发布统计
    if (publish.total_published > 0) {
      let pubHtml = `<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;">`;
      for (const [platform, count] of Object.entries(publish.by_platform || {})) {
        pubHtml += `<div style="background:#0f1720;border-radius:6px;padding:6px 12px;font-size:12px;"><span style="color:#e0e6f0;">${platform}</span> <span style="color:#4fc3f7;">${count}</span></div>`;
      }
      pubHtml += `</div>`;
      pubHtml += `<div style="color:#aabbcc;font-size:12px;">累计发布 ${publish.total_published} 条</div>`;
      publishContainer.innerHTML = pubHtml;
    } else {
      publishContainer.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">暂无发布记录</p>';
    }
    
  } catch (e) {
    container.innerHTML = `<p style="color:var(--error);">加载失败: ${e.message}</p>`;
  }
}

// 页面切换钩子（合并版）
const _origSwitchPage = switchPage;
switchPage = function(page) {
  _origSwitchPage(page);
  if (page === 'workflow') {
    loadWorkflowScripts();
    runEnvCheck();
  }
  if (page === 'outputs') {
    loadOutputsV2();
  }
  if (page === 'topics') {
    loadTopicsV2();
  }
  if (page === 'cost') {
    loadCostSummaryV2();
  }
  if (page === 'assets') {
    loadAssets();
  }
  if (page === 'analytics') {
    loadDashboardStats();
  }
};

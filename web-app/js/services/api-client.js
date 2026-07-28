// 后端 API 调用封装
// 路径沿用现有下划线动词式风格；FMS 相关为新增接口

// 解析后端 API 地址：
// 1. config.local.js 中配置了 BACKEND_URL 字符串 → 直接使用
// 2. 同源（后端直接托管前端）→ 相对路径 /api
// 3. 跨域（如 Cloudflare Pages）→ 回退到 localhost:3000（本地开发）
function resolveApiBase() {
  const cfg = window.HDZM_CONFIG || {};
  if (typeof cfg.BACKEND_URL === 'string' && cfg.BACKEND_URL !== 'auto') {
    return cfg.BACKEND_URL;
  }
  const origin = window.location.origin;
  if (origin === 'http://localhost:3000' || origin === 'http://127.0.0.1:3000') {
    return '/api';
  }
  // Cloudflare Pages 等静态托管：需在 config.local.js 配置后端地址
  // 未配置时回退到 localhost（仅本地开发可用）
  return 'http://localhost:3000/api';
}
const API_BASE = resolveApiBase();

export class ApiClient {
  constructor() {
    this.token = localStorage.getItem('hudongzhimou:token') || '';
  }

  setToken(token) {
    this.token = token;
    if (token) localStorage.setItem('hudongzhimou:token', token);
    else localStorage.removeItem('hudongzhimou:token');
  }

  isLoggedIn() {
    return !!this.token;
  }

  /** 通用请求 */
  async request(path, options = {}, { raw = false } = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      ...options.headers,
    };
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
    if (raw) return res;
    return res.json();
  }

  // ---- 用户 ----
  login(username, password) {
    return this.request('/login', { method: 'POST', body: JSON.stringify({ username, password }) });
  }
  register(username, password, nickname) {
    return this.request('/register', { method: 'POST', body: JSON.stringify({ username, password, nickname }) });
  }
  logout() {
    return this.request('/logout', { method: 'POST' });
  }
  getProfile() {
    return this.request('/get_profile');
  }
  updateProfile(data) {
    return this.request('/update_profile', { method: 'POST', body: JSON.stringify(data) });
  }

  // ---- FMS 评分 ----
  saveFMSScore(data) {
    return this.request('/fms_save', { method: 'POST', body: JSON.stringify(data) });
  }
  getFMSHistory(limit = 50) {
    return this.request(`/fms_history?limit=${limit}`);
  }

  // ---- 训练记录 ----
  saveTrainingRecord(summary) {
    return this.request('/training_save', { method: 'POST', body: JSON.stringify(summary) });
  }
  getTrainingHistory(limit = 50) {
    return this.request(`/training_history?limit=${limit}`);
  }

  // ---- AI 分析（FMS 专用新接口）----
  /** 文本轨：发送关节角度数据，GLM-4-Flash 分析 */
  requestFMSReport(jointData, testName, injuryHistory) {
    return this.request('/ai_report', {
      method: 'POST',
      body: JSON.stringify({ action_name: testName, joint_sequence: jointData, injury_history: injuryHistory }),
    });
  }
  /** 视觉轨：发送关键帧截图，GLM-4V-Flash 分析 */
  requestVisualAnalysis(imageBase64, testName, currentScore) {
    return this.request('/ai_visual', {
      method: 'POST',
      body: JSON.stringify({ image: imageBase64, action_name: testName, current_score: currentScore }),
    });
  }

  /** 健康检查（探测后端是否在线） */
  async ping() {
    try {
      const res = await fetch(API_BASE.replace('/api', '') + '/health', { method: 'GET' });
      return res.ok;
    } catch {
      return false;
    }
  }
}

// 护动智眸 — 应用入口与路由、主循环、评分记录、AI 触发

import { FramePipeline } from './core/pipeline.js';
import { CameraView } from './ui/camera-view.js';
import { FMSPanel } from './ui/fms-panel.js';
import { Dashboard } from './ui/dashboard.js';
import { ReportView } from './ui/report-view.js';
import { Settings } from './ui/settings.js';
import { ApiClient } from './services/api-client.js';
import { AIAnalyzer } from './services/ai-analyzer.js';
import { FMS_TESTS } from './core/fms-engine.js';
import { storage, offlineQueue } from './utils/storage.js';
import { throttle, formatDate } from './utils/helpers.js';

class App {
  constructor() {
    this.pipeline = null;
    this.cameraView = null;
    this.fmsPanel = new FMSPanel();
    this.dashboard = new Dashboard();
    this.reportView = new ReportView();
    this.settings = new Settings();
    this.api = new ApiClient();
    this.ai = new AIAnalyzer();

    this.running = false;
    this.rafId = null;

    // 当前 FMS 筛查会话：累积各项评分
    this.session = { scores: {}, totalScore: 0, risk: null, testDate: null };

    // 最近一帧的关节角度序列（供 AI 文本分析）
    this._jointBuffer = [];
    this._latestResult = null;

    // AI 分析节流（2.5s 一次）
    this._aiThrottled = throttle((...a) => this._doAIAnalysis(...a), 2500);
  }

  async init() {
    this.bindNavigation();
    this.bindControls();
    this.settings.bind(this.api.isLoggedIn() ? this.api : null, (m, t) => this.toast(m, t));
    this.refreshCameras();
    this.updateLoginUI();
    this.reportView.reset();

    // 探测后端
    this.backendOnline = await this.api.ping();
  }

  // ===== 导航 =====
  bindNavigation() {
    document.querySelectorAll('.nav-tab').forEach((tab) => {
      tab.addEventListener('click', () => this.switchPage(tab.dataset.page));
    });
  }

  switchPage(name) {
    document.querySelectorAll('.nav-tab').forEach((t) => t.classList.toggle('active', t.dataset.page === name));
    document.querySelectorAll('.page').forEach((p) => p.classList.toggle('active', p.id === `page-${name}`));
    if (name === 'report') this._renderReport();
    if (name === 'settings') this.refreshCameras();
  }

  // ===== 控制 =====
  bindControls() {
    document.getElementById('btn-start').addEventListener('click', () => this.startTraining());
    document.getElementById('btn-stop').addEventListener('click', () => this.stopTraining());
    document.getElementById('btn-snapshot').addEventListener('click', () => this.recordScore());
    document.getElementById('fms-test-select').addEventListener('change', (e) => {
      if (this.pipeline) this.pipeline.setTest(e.target.value);
      this.fmsPanel.reset();
      this.dashboard.reset();
    });
    document.getElementById('nav-login-btn').addEventListener('click', () => this.openLoginModal());
  }

  // ===== 摄像头 + 主循环 =====
  async startTraining() {
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const btnSnap = document.getElementById('btn-snapshot');
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');

    try {
      // 启动摄像头
      const constraints = {
        video: this.settings.get('cameraDeviceId')
          ? { deviceId: { exact: this.settings.get('cameraDeviceId') } }
          : { facingMode: 'user' },
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      const video = document.getElementById('camera-video');
      video.srcObject = stream;
      await video.play();

      // 初始化管线（按需）
      if (!this.pipeline || this.pipeline.needsReinit) {
        overlay.style.display = 'flex';
        loadingText.textContent = '正在加载姿态识别模型…';
        this.pipeline = new FramePipeline({ maxFps: this.settings.get('maxFps') });
        await this.pipeline.init({ variant: this.settings.get('modelVariant') }, (msg) => {
          loadingText.textContent = msg;
        });
        overlay.style.display = 'none';
      }

      // 初始化渲染视图
      if (!this.cameraView) {
        this.cameraView = new CameraView(video, document.getElementById('skeleton-canvas'), {
          mirror: this.settings.get('mirror'),
        });
      }
      this.cameraView.setMirror(this.settings.get('mirror'));

      this.running = true;
      btnStart.disabled = true;
      btnStop.disabled = false;
      btnSnap.disabled = false;
      this.toast('检测已开始', 'success');
      this.loop();
    } catch (err) {
      console.error(err);
      this.showCameraError(err);
      overlay.style.display = 'none';
    }
  }

  loop() {
    if (!this.running) return;
    const video = document.getElementById('camera-video');
    const result = this.pipeline.process(video);
    if (result) {
      this._latestResult = result;
      this.cameraView.render(result);
      this.fmsPanel.update(result.fms);
      this.dashboard.updateAngles(result.fms);
      this.dashboard.updateAlerts(result.safety);

      // 收集关节角度序列供 AI 分析
      this._collectJointData(result);

      // 触发节流后的 AI 分析
      if (result.fms && result.fms.score <= 2) {
        this._aiThrottled(result);
      }
    }
    this.rafId = requestAnimationFrame(() => this.loop());
  }

  stopTraining() {
    this.running = false;
    if (this.rafId) cancelAnimationFrame(this.rafId);
    const video = document.getElementById('camera-video');
    if (video.srcObject) {
      video.srcObject.getTracks().forEach((t) => t.stop());
      video.srcObject = null;
    }
    if (this.cameraView) this.cameraView.clear();
    document.getElementById('btn-start').disabled = false;
    document.getElementById('btn-stop').disabled = true;
    document.getElementById('btn-snapshot').disabled = true;
    this.toast('检测已停止', 'success');
  }

  // ===== 评分记录 =====
  recordScore() {
    if (!this._latestResult?.fms) {
      this.toast('暂无有效评分数据', 'error');
      return;
    }
    const test = this._latestResult.test;
    this.session.scores[test] = this._latestResult.fms;
    const total = Object.values(this.session.scores).reduce((s, r) => s + (r?.score || 0), 0);
    this.session.totalScore = total;

    const asymmetries = Object.values(this.session.scores)
      .filter((r) => r?.asymmetry)
      .map((r) => r.asymmetry);
    this.session.risk = this.pipeline.fmsEngine.getRiskLevel(total, asymmetries);

    const testName = FMS_TESTS.find((t) => t.key === test)?.name || test;
    this.toast(`已记录「${testName}」评分：${this._latestResult.fms.score} 分`, 'success');
  }

  _renderReport() {
    const scoreCount = Object.keys(this.session.scores).length;
    if (scoreCount === 0) {
      this.reportView.reset();
      return;
    }
    this.session.testDate = formatDate(new Date());
    this.reportView.render(this.session);

    // 触发 AI 报告（异步，不阻塞渲染）
    this._generateAIReport();

    // 拉取历史趋势并追加折线图
    this._loadHistoryTrend();

    // 持久化
    this._saveSession();
  }

  async _loadHistoryTrend() {
    if (!this.api.isLoggedIn() || !this.backendOnline) return;
    try {
      const res = await this.api.getFMSHistory(10);
      if (res?.success && Array.isArray(res.data) && res.data.length > 0) {
        this.reportView.renderTrend(res.data);
      }
    } catch (e) {
      console.warn('history trend load failed', e);
    }
  }

  async _generateAIReport() {
    if (!this.backendOnline) return;
    try {
      const jointData = this._jointBuffer.slice(-30);
      const testName = Object.keys(this.session.scores).join(',');
      const injury = (storage.get('profile', {}).injury_history || []).join('；');
      const textRes = await this.ai.textAnalysis(testName, jointData, injury);
      // 视觉分析需要 0-3 分制的单次评分，传总分(0-21)会导致 prompt 异常
      const scoreCount = Object.keys(this.session.scores).length;
      const avgScore = scoreCount > 0 ? Math.round(this.session.totalScore / scoreCount) : 0;
      const visualRes = await this.ai.visualAnalysis(
        document.getElementById('skeleton-canvas'),
        testName,
        avgScore,
      );
      const cross = this.ai.crossValidate(textRes, visualRes);
      if (cross) {
        const tip = cross.coaching_tip || (cross.recommendations || []).join('；') || '暂无建议';
        this.session.aiAnalysis = tip;
        this.reportView.render(this.session);
      }
    } catch (e) {
      console.warn('AI report failed', e);
    }
  }

  async _saveSession() {
    const payload = {
      scores: Object.fromEntries(
        Object.entries(this.session.scores).map(([k, v]) => [k, v.score])
      ),
      total_score: this.session.totalScore,
      asymmetry_flags: Object.values(this.session.scores)
        .filter((r) => r?.asymmetry)
        .map((r) => r.asymmetry),
      ai_analysis: this.session.aiAnalysis || '',
    };
    if (this.api.isLoggedIn() && this.backendOnline) {
      try {
        await this.api.saveFMSScore(payload);
        // 同步离线队列
        const q = offlineQueue.all();
        for (const r of q) await this.api.saveFMSScore(r);
        offlineQueue.clear();
        this.toast('评分已上传', 'success');
        return;
      } catch (e) { /* 落入离线队列 */ }
    }
    offlineQueue.add(payload);
    storage.set('last_session', this.session);
    this.toast('后端不可用，已保存到本地', 'success');
  }

  // ===== AI 实时分析 =====
  _collectJointData(result) {
    const m = result.fms?.metrics;
    if (!m) return;
    this._jointBuffer.push({ t: result.timestamp, test: result.test, ...m });
    if (this._jointBuffer.length > 60) this._jointBuffer.shift();
  }

  async _doAIAnalysis(result) {
    if (!this.backendOnline) return;
    try {
      const testName = result.test;
      const injury = (storage.get('profile', {}).injury_history || []).join('；');
      const textRes = await this.ai.textAnalysis(testName, this._jointBuffer.slice(-20), injury);
      const visualRes = await this.ai.visualAnalysis(
        document.getElementById('skeleton-canvas'),
        testName,
        result.fms?.score ?? 0,
      );
      const cross = this.ai.crossValidate(textRes, visualRes);
      if (cross?.coaching_tip) {
        this.toast(cross.coaching_tip, cross.fms_score <= 1 ? 'error' : 'success');
      }
    } catch (e) {
      console.warn('realtime AI failed', e);
    }
  }

  // ===== 登录 =====
  updateLoginUI() {
    const nameEl = document.getElementById('nav-username');
    const btn = document.getElementById('nav-login-btn');
    const profile = storage.get('profile', {});
    if (this.api.isLoggedIn()) {
      nameEl.textContent = profile.nickname || profile.username || '已登录';
      btn.textContent = '退出';
      btn.onclick = async () => {
        try { await this.api.logout(); } catch {}
        this.api.setToken('');
        this.updateLoginUI();
        this.toast('已退出登录', 'success');
      };
    } else {
      nameEl.textContent = '';
      btn.textContent = '登录';
      btn.onclick = () => this.openLoginModal();
    }
  }

  openLoginModal() {
    if (this.api.isLoggedIn()) { this.api.logout(); return; }
    const modal = document.createElement('div');
    modal.className = 'login-modal';
    modal.innerHTML = `
      <div class="card" style="width:320px;padding:24px">
        <h3 style="margin-bottom:16px">登录 / 注册</h3>
        <div class="form-row" style="margin-bottom:10px">
          <input type="text" id="li-user" class="input" placeholder="用户名">
        </div>
        <div class="form-row" style="margin-bottom:16px">
          <input type="password" id="li-pass" class="input" placeholder="密码">
        </div>
        <div style="display:flex;gap:8px">
          <button id="li-login" class="btn btn-primary" style="flex:1">登录</button>
          <button id="li-reg" class="btn btn-secondary" style="flex:1">注册</button>
        </div>
        <button id="li-close" class="btn btn-ghost btn-sm" style="width:100%;margin-top:8px">取消</button>
      </div>`;
    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;z-index:2000';
    document.body.appendChild(modal);

    const close = () => modal.remove();
    modal.querySelector('#li-close').onclick = close;
    modal.onclick = (e) => { if (e.target === modal) close(); };

    const doLogin = async (isReg) => {
      const u = modal.querySelector('#li-user').value.trim();
      const p = modal.querySelector('#li-pass').value;
      if (!u || !p) { this.toast('请输入用户名和密码', 'error'); return; }
      try {
        const res = isReg ? await this.api.register(u, p, u) : await this.api.login(u, p);
        if (res?.success && res.data?.token) {
          this.api.setToken(res.data.token);
          storage.set('profile', { username: res.data.username, nickname: res.data.nickname });
          this.updateLoginUI();
          close();
          this.toast(isReg ? '注册成功' : '登录成功', 'success');
          this.settings.loadProfile(this.api, (m, t) => this.toast(m, t));
        } else {
          this.toast(res?.error || '操作失败', 'error');
        }
      } catch (e) {
        this.toast('网络错误，请检查后端', 'error');
      }
    };
    modal.querySelector('#li-login').onclick = () => doLogin(false);
    modal.querySelector('#li-reg').onclick = () => doLogin(true);
  }

  // ===== 辅助 =====
  refreshCameras() { this.settings.refreshCameras(); }

  showCameraError(err) {
    const el = document.getElementById('camera-error');
    let msg = '摄像头启动失败';
    if (err.name === 'NotAllowedError') msg = '摄像头权限被拒绝，请在浏览器设置中允许访问';
    else if (err.name === 'NotFoundError') msg = '未找到摄像头设备';
    el.textContent = msg;
    el.style.display = 'flex';
    this.toast(msg, 'error');
  }

  toast(msg, type = '') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = `toast show ${type}`;
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => el.classList.remove('show'), 2500);
  }
}

const app = new App();
app.init();

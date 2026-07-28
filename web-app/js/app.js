// 护动智眸 — 应用入口与路由、主循环、评分记录、AI 触发

import { FramePipeline } from './core/pipeline.js';
import { CameraView } from './ui/camera-view.js';
import { FMSPanel } from './ui/fms-panel.js';
import { Dashboard } from './ui/dashboard.js';
import { ReportView } from './ui/report-view.js';
import { Settings } from './ui/settings.js';
import { TrainingPanel } from './ui/training-panel.js';
import { StatsView } from './ui/stats-view.js';
import { VoiceCoach } from './ui/voice-coach.js';
import { TrainingSession } from './core/training-session.js';
import { EXERCISE_LIST } from './core/exercise-library.js';
import { ApiClient } from './services/api-client.js';
import { AIAnalyzer } from './services/ai-analyzer.js';
import { FMS_TESTS } from './core/fms-engine.js';
import { storage, offlineQueue } from './utils/storage.js';
import { throttle, formatDate } from './utils/helpers.js';

// 已知虚拟摄像头关键词（小写匹配）
const VIRTUAL_CAM_KEYWORDS = [
  'ivcam', 'obs', 'virtual', 'manycam', 'snap camera',
  'splitcam', 'ndi', 'mmhmm', 'epoccam', 'droidcam', 'youcam',
];

class App {
  constructor() {
    this.pipeline = null;
    this.cameraView = null;
    this.fmsPanel = new FMSPanel();
    this.dashboard = new Dashboard();
    this.reportView = new ReportView();
    this.settings = new Settings();
    this.trainingPanel = new TrainingPanel();
    this.statsView = new StatsView();
    this.voice = new VoiceCoach();
    this.trainingSession = null;
    this.api = new ApiClient();
    this.ai = new AIAnalyzer();

    this.running = false;
    this.rafId = null;

    // 当前模式：'fms' | 'training'
    this.mode = 'fms';

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
    this.bindModeSwitch();
    this.populateExerciseSelect();
    this.settings.bind(this.api.isLoggedIn() ? this.api : null, (m, t) => this.toast(m, t));
    this.refreshCameras();
    this.updateLoginUI();
    this.reportView.reset();
    this.trainingPanel.reset();

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

  // ===== 模式切换（FMS / 训练）=====
  bindModeSwitch() {
    document.querySelectorAll('.mode-btn').forEach((btn) => {
      btn.addEventListener('click', () => this.switchMode(btn.dataset.mode));
    });
  }

  switchMode(mode) {
    if (this.mode === mode) return;
    if (this.running) {
      this.toast('请先停止当前检测', 'error');
      return;
    }
    this.mode = mode;
    this.pipeline?.setMode(mode);

    // 切换头部控件显隐
    document.querySelectorAll('.fms-only').forEach((el) => el.style.display = mode === 'fms' ? '' : 'none');
    document.querySelectorAll('.training-only').forEach((el) => el.style.display = mode === 'training' ? '' : 'none');

    // 切换模式按钮高亮
    document.querySelectorAll('.mode-btn').forEach((b) => b.classList.toggle('active', b.dataset.mode === mode));

    // 重置面板
    this.fmsPanel.reset();
    this.dashboard.reset();
    this.trainingPanel.reset();
  }

  /** 填充训练动作下拉 */
  populateExerciseSelect() {
    const sel = document.getElementById('exercise-select');
    if (!sel) return;
    sel.innerHTML = EXERCISE_LIST.map((e) =>
      `<option value="${e.key}">${e.name}（${e.en}）${e.isStatic ? '· 静态' : ''}</option>`
    ).join('');
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
    document.getElementById('exercise-select')?.addEventListener('change', (e) => {
      if (this.pipeline && this.mode === 'training') this.pipeline.setExercise(e.target.value);
    });
    // 训练模式控制按钮
    document.getElementById('btn-train-start')?.addEventListener('click', () => this.startTrainingSession());
    document.getElementById('btn-train-pause')?.addEventListener('click', () => this.togglePauseTraining());
    document.getElementById('btn-train-stop')?.addEventListener('click', () => this.stopTrainingSession());
    document.getElementById('nav-login-btn').addEventListener('click', () => this.openLoginModal());
  }

  // ===== 摄像头 + 主循环 =====
  /** 共享：摄像头初始化 + 管线加载 + 渲染视图（FMS / 训练共用） */
  async _initCameraPipeline() {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');

    // 启动摄像头：用户指定设备 → 真实物理设备（需先拿权限才能识别 label）→ 自动选择
    let stream;
    const savedDeviceId = this.settings.get('cameraDeviceId');
    if (savedDeviceId) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: savedDeviceId } } });
      } catch { /* 设备可能被占用，fallback */ }
    }
    if (!stream) {
      // 先用默认方式获取流（同时拿到摄像头权限 + track.label）
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      // 检查默认流是否选中了虚拟摄像头
      const isVirtual = this._isVirtualCamera(stream.getVideoTracks()[0]?.label);
      if (isVirtual) {
        // 停止虚拟流，重新枚举（此时已有权限，label 可读），找真实设备
        stream.getTracks().forEach((t) => t.stop());
        const realCamId = await this._findRealCamera();
        if (realCamId) {
          try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: realCamId } } });
          } catch { /* 真实设备被占用，回退到默认流 */ }
        }
        if (!stream) {
          stream = await navigator.mediaDevices.getUserMedia({ video: true });
        }
      }
    }
    const video = document.getElementById('camera-video');
    video.srcObject = stream;

    // 确保 video 真正播放（某些浏览器需要显式调用 play）
    try {
      await video.play();
    } catch (playErr) {
      console.warn('[App] video.play() 失败，尝试静音后重试:', playErr);
      video.muted = true;
      await video.play();
    }

    // 应用镜像设置（从用户偏好读取）
    const container = document.querySelector('.camera-container');
    if (container) {
      container.classList.toggle('mirrored', this.settings.get('mirror'));
    }

    // 等 video 真正有帧数据（readyState >= 2），否则 MediaPipe 会在空帧上检测到噪声
    if (video.readyState < 2) {
      await new Promise((resolve) => {
        video.addEventListener('loadeddata', resolve, { once: true });
        setTimeout(resolve, 3000); // 超时兜底
      });
    }

    // 验证视频流是否真正活跃（防止黑屏：某些情况下 stream 已断开）
    const track = stream.getVideoTracks()[0];
    if (!track || track.readyState !== 'live') {
      throw new Error('摄像头流未就绪，请检查设备是否被其他程序占用');
    }

    // 初始化管线（按需）
    if (!this.pipeline || this.pipeline.needsReinit) {
      overlay.style.display = 'flex';
      loadingText.textContent = '正在加载姿态识别模型…';
      this.pipeline = new FramePipeline({ maxFps: this.settings.get('maxFps') });
      try {
        await this.pipeline.init({ variant: this.settings.get('modelVariant') }, (msg) => {
          loadingText.textContent = msg;
        });
      } catch (initErr) {
        overlay.style.display = 'none';
        throw new Error('模型加载失败：' + (initErr.message || String(initErr)) + '。请刷新页面重试，或检查网络连接。');
      }
      overlay.style.display = 'none';
    }

    // 初始化渲染视图
    if (!this.cameraView) {
      this.cameraView = new CameraView(video, document.getElementById('skeleton-canvas'));
    }

    return video;
  }

  async startTraining() {
    const overlay = document.getElementById('loading-overlay');
    try {
      await this._initCameraPipeline();
      this.running = true;
      document.getElementById('btn-start').disabled = true;
      document.getElementById('btn-stop').disabled = false;
      document.getElementById('btn-snapshot').disabled = false;
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
      // 有新检测结果时才重绘骨架，避免每帧清屏导致闪烁
      this.cameraView.render(result);
      this._latestResult = result;
      this._staleFrames = 0;

      if (this.mode === 'training' && result.mode === 'training') {
        // 训练模式：会话聚合 + 面板渲染
        const snap = this.trainingSession?.onFrame(result);
        this.trainingPanel.update(snap, result.rep);
      } else {
        // FMS 模式：评分面板 + 角度 + 预警
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
    } else {
      // 帧率节流或偶尔检测不到时保留上一帧骨架，不闪烁
      // 连续 ~0.5s 无新结果才清屏（人物离开画面等情况）
      this._staleFrames = (this._staleFrames || 0) + 1;
      if (this._staleFrames > 30) {
        this.cameraView.render(null);
        this._staleFrames = 0;
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

  // ===== 训练模式会话控制 =====
  async startTrainingSession() {
    const overlay = document.getElementById('loading-overlay');
    try {
      await this._initCameraPipeline();

      // 设置训练模式 + 动作
      this.pipeline.setMode('training');
      const exerciseKey = document.getElementById('exercise-select').value;
      this.pipeline.setExercise(exerciseKey);

      // 启动训练会话
      this.trainingSession = new TrainingSession({ voice: this.voice });
      this.trainingSession.start(exerciseKey);
      this.trainingPanel.reset();

      this.running = true;
      document.getElementById('btn-train-start').disabled = true;
      document.getElementById('btn-train-pause').disabled = false;
      document.getElementById('btn-train-stop').disabled = false;
      this.toast('训练已开始', 'success');
      this.loop();
    } catch (err) {
      console.error(err);
      this.showCameraError(err);
      overlay.style.display = 'none';
    }
  }

  togglePauseTraining() {
    if (!this.trainingSession) return;
    const btn = document.getElementById('btn-train-pause');
    if (this.trainingSession.state === 'running') {
      this.trainingSession.pause();
      btn.textContent = '继续';
    } else if (this.trainingSession.state === 'paused') {
      this.trainingSession.resume();
      btn.textContent = '暂停';
    }
  }

  stopTrainingSession() {
    this.running = false;
    if (this.rafId) cancelAnimationFrame(this.rafId);
    const video = document.getElementById('camera-video');
    if (video.srcObject) {
      video.srcObject.getTracks().forEach((t) => t.stop());
      video.srcObject = null;
    }
    if (this.cameraView) this.cameraView.clear();

    // 生成摘要并保存
    if (this.trainingSession) {
      const summary = this.trainingSession.stop();
      this._saveTrainingRecord(summary);
    }

    document.getElementById('btn-train-start').disabled = false;
    document.getElementById('btn-train-pause').disabled = true;
    document.getElementById('btn-train-stop').disabled = true;
    document.getElementById('btn-train-pause').textContent = '暂停';
    this.toast('训练已结束，记录已保存', 'success');
  }

  /** 保存训练记录到本地 + 后端 */
  async _saveTrainingRecord(summary) {
    // 本地保存（统计页读取）
    StatsView.saveRecord(summary);

    // 后端保存（如果在线）
    if (this.api.isLoggedIn() && this.backendOnline) {
      try {
        await this.api.saveTrainingRecord(summary);
      } catch (e) {
        console.warn('训练记录上传失败，已保存本地', e);
      }
    }
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
    const reportEl = document.getElementById('report-content');
    const statsEl = document.getElementById('stats-content');

    // 训练模式：渲染训练统计页
    if (this.mode === 'training') {
      if (reportEl) reportEl.style.display = 'none';
      if (statsEl) statsEl.style.display = '';
      this.statsView.render();
      return;
    }
    // FMS 模式：渲染 FMS 评分报告
    if (reportEl) reportEl.style.display = '';
    if (statsEl) statsEl.style.display = 'none';

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

  /** 判断摄像头 label 是否属于虚拟设备 */
  _isVirtualCamera(label) {
    const l = (label || '').toLowerCase();
    return VIRTUAL_CAM_KEYWORDS.some((kw) => l.includes(kw));
  }

  /** 在可用摄像头中找到真实物理设备（跳过虚拟摄像头；无 label 的设备也跳过） */
  async _findRealCamera() {
    if (!navigator.mediaDevices?.enumerateDevices) return null;
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const cams = devices.filter((d) => d.kind === 'videoinput');
      // 只保留 label 非空且不是虚拟设备的摄像头
      const real = cams.filter((c) => c.label && !this._isVirtualCamera(c.label));
      return real[0]?.deviceId || null;
    } catch {
      return null;
    }
  }

  showCameraError(err) {
    const el = document.getElementById('camera-error');
    let msg = '摄像头启动失败';
    if (err.name === 'NotAllowedError') msg = '摄像头权限被拒绝，请在浏览器设置中允许访问';
    else if (err.name === 'NotFoundError') msg = '未找到摄像头设备';
    else if (err.name === 'NotReadableError') msg = '摄像头被其他程序占用，请关闭后重试';
    else if (err.name === 'OverconstrainedError') msg = '摄像头不满足要求，请更换设备';
    else if (err.message) msg = err.message;
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

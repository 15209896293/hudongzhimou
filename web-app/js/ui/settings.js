// 设置管理：本地偏好 + 用户档案同步

import { storage } from '../utils/storage.js';

const DEFAULTS = {
  modelVariant: 'lite',
  maxFps: 60,
  mirror: true,
  cameraDeviceId: '',
};

export class Settings {
  constructor() {
    this.prefs = { ...DEFAULTS, ...storage.get('prefs', {}) };
  }

  get(key) {
    return this.prefs[key];
  }

  set(key, value) {
    this.prefs[key] = value;
    storage.set('prefs', this.prefs);
  }

  getAll() {
    return { ...this.prefs };
  }

  /** 绑定设置页 UI */
  bind(apiClient, onToast) {
    const $ = (id) => document.getElementById(id);
    const setModel = $('set-model');
    const setFps = $('set-fps');
    const setMirror = $('set-mirror');
    const setCamera = $('set-camera');
    const btnSaveProfile = $('btn-save-profile');
    const btnRefreshCam = $('btn-refresh-cameras');

    // 回填当前设置
    if (setModel) setModel.value = this.prefs.modelVariant;
    if (setFps) setFps.value = String(this.prefs.maxFps);
    if (setMirror) setMirror.checked = this.prefs.mirror;

    if (setModel) setModel.addEventListener('change', () => this.set('modelVariant', setModel.value));
    if (setFps) setFps.addEventListener('change', () => this.set('maxFps', parseInt(setFps.value)));
    if (setMirror) setMirror.addEventListener('change', () => {
      this.set('mirror', setMirror.checked);
      // 实时应用镜像到当前画面
      const container = document.querySelector('.camera-container');
      if (container) container.classList.toggle('mirrored', setMirror.checked);
    });
    if (setCamera) setCamera.addEventListener('change', () => this.set('cameraDeviceId', setCamera.value));

    if (btnRefreshCam) {
      btnRefreshCam.addEventListener('click', () => this.refreshCameras());
    }

    // 加载用户档案
    this.loadProfile(apiClient, onToast);

    if (btnSaveProfile) {
      btnSaveProfile.addEventListener('click', () => this.saveProfile(apiClient, onToast));
    }
  }

  async refreshCameras() {
    const sel = document.getElementById('set-camera');
    if (!sel || !navigator.mediaDevices?.enumerateDevices) return;
    try {
      // 如果没有权限，先获取一次
      let devices;
      try { devices = await navigator.mediaDevices.enumerateDevices(); } catch {
        const tmp = await navigator.mediaDevices.getUserMedia({ video: true });
        tmp.getTracks().forEach((t) => t.stop());
        devices = await navigator.mediaDevices.enumerateDevices();
      }
      const cams = devices.filter((d) => d.kind === 'videoinput');
      const virtualKeywords = ['ivcam', 'obs', 'virtual', 'manycam', 'snap camera', 'splitcam', 'ndi', 'mmhmm', 'epoccam', 'droidcam', 'youcam'];
      const cur = this.prefs.cameraDeviceId;
      sel.innerHTML = '<option value="">自动（跳过虚拟设备）</option>' +
        cams.map((c) => {
          const label = c.label || '未知设备';
          const isVirtual = virtualKeywords.some((kw) => label.toLowerCase().includes(kw));
          const tag = isVirtual ? ' ⚠️虚拟' : '';
          return `<option value="${c.deviceId}" ${c.deviceId === cur ? 'selected' : ''}>${label.slice(0, 40)}${tag}</option>`;
        }).join('');
    } catch (e) {
      console.warn('enumerate cameras failed', e);
    }
  }

  async loadProfile(apiClient, onToast) {
    if (!apiClient) {
      // 离线：从本地读
      const p = storage.get('profile', {});
      this._fillProfile(p);
      return;
    }
    try {
      const res = await apiClient.getProfile();
      if (res?.success && res.data) {
        this._fillProfile(res.data);
        storage.set('profile', res.data);
      }
    } catch { /* 离线静默 */ }
  }

  _fillProfile(p) {
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v ?? ''; };
    set('set-nickname', p.nickname);
    set('set-gender', p.gender);
    set('set-height', p.height);
    set('set-weight', p.weight);
    set('set-age', p.age);
    set('set-injury', Array.isArray(p.injury_history) ? p.injury_history.join('；') : (p.injury_history || ''));
  }

  async saveProfile(apiClient, onToast) {
    const get = (id) => document.getElementById(id)?.value || null;
    const injuryText = get('set-injury');
    const data = {
      nickname: get('set-nickname'),
      gender: get('set-gender') || null,
      height: get('set-height') ? parseInt(get('set-height')) : null,
      weight: get('set-weight') ? parseInt(get('set-weight')) : null,
      age: get('set-age') ? parseInt(get('set-age')) : null,
      injury_history: injuryText ? injuryText.split(/[；;，,]/).map((s) => s.trim()).filter(Boolean) : [],
    };
    storage.set('profile', data);
    if (!apiClient) { onToast?.('已保存到本地', 'success'); return; }
    try {
      const res = await apiClient.updateProfile(data);
      if (res?.success) onToast?.('用户信息已保存', 'success');
      else onToast?.(res?.error || '保存失败', 'error');
    } catch { onToast?.('网络不可用，已保存到本地', 'success'); }
  }
}

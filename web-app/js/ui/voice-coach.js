// 语音播报 — 浏览器原生 SpeechSynthesis + Web Audio API 合成音效
// 零依赖，替代桌面版 pyttsx3 + mp3 音频文件

export class VoiceCoach {
  constructor() {
    this.enabled = true;
    this.synth = window.speechSynthesis;
    this.lastSpeak = 0;
    this.cooldown = 3000; // 3 秒冷却，避免刷屏
    this._audioCtx = null;
  }

  /**
   * 语音播报
   * @param {string} text - 播报文本
   * @param {object} [opts] - { priority: 'normal'|'urgent' }
   */
  speak(text, { priority = 'normal' } = {}) {
    if (!this.enabled || !this.synth || !text) return;
    const now = performance.now();
    if (priority !== 'urgent' && now - this.lastSpeak < this.cooldown) return;

    // urgent 级别打断当前播报
    if (priority === 'urgent') this.synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    utterance.rate = 1.0;
    utterance.volume = 0.9;
    this.synth.speak(utterance);
    this.lastSpeak = now;
  }

  /**
   * 合成音效（无需音频文件）
   * @param {number} freq - 频率 Hz
   * @param {number} duration - 时长 ms
   */
  beep(freq = 800, duration = 100) {
    try {
      if (!this._audioCtx) {
        this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      const ctx = this._audioCtx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = freq;
      osc.connect(gain);
      gain.connect(ctx.destination);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration / 1000);
      osc.start();
      osc.stop(ctx.currentTime + duration / 1000);
    } catch {
      // AudioContext 不可用时静默降级
    }
  }

  /** 计数完成音效 */
  countBeep() {
    this.beep(880, 80);
  }

  /** 警告音效 */
  warningBeep() {
    this.beep(440, 200);
  }

  /** 危险音效 */
  dangerBeep() {
    this.beep(220, 400);
  }

  setEnabled(enabled) {
    this.enabled = enabled;
    if (!enabled && this.synth) this.synth.cancel();
  }

  /** 检查浏览器是否支持语音合成 */
  static isSupported() {
    return 'speechSynthesis' in window;
  }
}

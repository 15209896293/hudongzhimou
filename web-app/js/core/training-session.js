// 训练会话管理 — 生命周期 / 计时 / 计数 / 质量 / 安全 / 疲劳 聚合
// 协调 FatigueMonitor 与 VoiceCoach，输出可保存的会话摘要

import { FatigueMonitor } from './fatigue-monitor.js';
import { VoiceCoach } from '../ui/voice-coach.js';
import { EXERCISES } from './exercise-library.js';

export class TrainingSession {
  /**
   * @param {object} [opts]
   * @param {VoiceCoach} [opts.voice] - 外部传入的语音教练实例（可选）
   */
  constructor(opts = {}) {
    this.fatigue = new FatigueMonitor();
    this.voice = opts.voice || new VoiceCoach();

    this.state = 'idle';   // 'idle' | 'running' | 'paused' | 'stopped'
    this.exerciseKey = null;
    this.exerciseConfig = null;

    // 计时
    this._startTs = 0;       // 本段开始时间戳
    this._accumMs = 0;       // 已累计的有效训练时长
    this._endTs = 0;

    // 计数
    this.reps = 0;
    this._lastRepCount = 0;

    // 质量评分
    this._qualitySum = 0;
    this._qualityCount = 0;
    this._qualityHistory = [];   // 采样序列（用于趋势）
    this.lastQuality = null;     // 最近一帧 { score, breakdown }

    // 安全事件
    this.safetyEvents = [];      // [{ time, level, message, joint, value }]
    this.lastSafety = null;      // 最近一帧 { level, alerts }

    // 疲劳警告
    this.fatigueWarnings = [];

    // 危险/警告语音冷却（避免重复播报同一告警）
    this._voiceCooldown = new Map(); // alertType -> 上次播报时间
  }

  /** 开始一次训练会话 */
  start(exerciseKey) {
    this.exerciseKey = exerciseKey;
    this.exerciseConfig = EXERCISES[exerciseKey];
    this.state = 'running';
    this._startTs = performance.now();
    this._accumMs = 0;
    this._endTs = 0;

    this.reps = 0;
    this._lastRepCount = 0;
    this._qualitySum = 0;
    this._qualityCount = 0;
    this._qualityHistory = [];
    this.lastQuality = null;
    this.safetyEvents = [];
    this.lastSafety = null;
    this.fatigueWarnings = [];
    this._voiceCooldown.clear();

    this.fatigue.start();

    const name = this.exerciseConfig ? this.exerciseConfig.name : exerciseKey;
    this.voice.speak(`开始${name}训练，注意动作标准`, { priority: 'urgent' });
  }

  /** 暂停 */
  pause() {
    if (this.state !== 'running') return;
    this._accumMs += performance.now() - this._startTs;
    this.state = 'paused';
    this.voice.speak('已暂停', { priority: 'urgent' });
  }

  /** 恢复 */
  resume() {
    if (this.state !== 'paused') return;
    this._startTs = performance.now();
    this.state = 'running';
    this.voice.speak('继续训练', { priority: 'urgent' });
  }

  /** 停止并生成摘要 */
  stop() {
    if (this.state === 'stopped') return this.getSummary();
    if (this.state === 'running') {
      this._accumMs += performance.now() - this._startTs;
    }
    this._endTs = performance.now();
    this.state = 'stopped';
    this.voice.speak('训练结束', { priority: 'urgent' });
    return this.getSummary();
  }

  /** 当前有效训练时长（秒） */
  getDuration() {
    if (this.state === 'idle') return 0;
    if (this.state === 'running') {
      return Math.round((this._accumMs + performance.now() - this._startTs) / 1000);
    }
    // paused / stopped
    return Math.round(this._accumMs / 1000);
  }

  /** 平均质量评分 */
  getAvgQuality() {
    return this._qualityCount > 0
      ? Math.round(this._qualitySum / this._qualityCount)
      : 0;
  }

  /**
   * 每帧调用：处理训练结果，驱动计数/质量/安全/疲劳/语音
   * @param {object} result - pipeline 训练模式输出
   * @returns {object} 给面板渲染的实时状态
   */
  onFrame(result) {
    if (this.state !== 'running') return this._snapshot();

    // 1. 计数
    if (result.rep) {
      if (result.rep.repCompleted) {
        this.reps = result.rep.count;
        this.voice.countBeep();
        // 次数里程碑
        const warn = this.fatigue.onRep(this.reps);
        if (warn) {
          this.fatigueWarnings.push({ time: this.getDuration(), message: warn });
          this.voice.speak(warn, { priority: 'urgent' });
        }
      } else {
        this.reps = result.rep.count;
      }
    }

    // 2. 质量评分
    if (result.quality) {
      this.lastQuality = result.quality;
      this._qualitySum += result.quality.score;
      this._qualityCount++;
      // 每 30 帧采样一次趋势
      if (this._qualityCount % 30 === 0) {
        this._qualityHistory.push(result.quality.score);
      }
    }

    // 3. 安全检测 + 语音播报
    if (result.safety) {
      this.lastSafety = result.safety;
      this._handleSafety(result.safety);
    }

    // 4. 疲劳时间里程碑
    const fatigueWarn = this.fatigue.check();
    if (fatigueWarn) {
      this.fatigueWarnings.push({ time: this.getDuration(), message: fatigueWarn });
      this.voice.speak(fatigueWarn, { priority: 'urgent' });
    }

    return this._snapshot();
  }

  /** 处理安全告警：记录事件 + 语音播报（带冷却） */
  _handleSafety(safety) {
    const now = performance.now();
    for (const alert of safety.alerts) {
      // 记录危险/警告事件
      if (alert.severity === 'danger' || alert.severity === 'warning') {
        this.safetyEvents.push({
          time: this.getDuration(),
          level: alert.severity,
          type: alert.type,
          joint: alert.joint,
          message: alert.message,
          value: alert.value,
        });
      }
      // 语音播报（同类型 5 秒冷却）
      const key = alert.type;
      const last = this._voiceCooldown.get(key) || 0;
      if (now - last > 5000) {
        if (alert.severity === 'danger') {
          this.voice.dangerBeep();
          this.voice.speak(alert.message, { priority: 'urgent' });
          this._voiceCooldown.set(key, now);
        } else if (alert.severity === 'warning') {
          this.voice.warningBeep();
          this.voice.speak(alert.message);
          this._voiceCooldown.set(key, now);
        }
      }
    }
  }

  /** 当前实时快照（供面板渲染） */
  _snapshot() {
    return {
      state: this.state,
      exercise: this.exerciseKey,
      exerciseName: this.exerciseConfig ? this.exerciseConfig.name : '',
      duration: this.getDuration(),
      reps: this.reps,
      avgQuality: this.getAvgQuality(),
      lastQuality: this.lastQuality,
      lastSafety: this.lastSafety,
      isFatigued: this.fatigue.isFatigued,
      fatigueWarnings: this.fatigueWarnings,
    };
  }

  /** 生成可保存的会话摘要 */
  getSummary() {
    return {
      exercise: this.exerciseKey,
      exerciseName: this.exerciseConfig ? this.exerciseConfig.name : '',
      category: this.exerciseConfig ? this.exerciseConfig.category : 'fitness',
      duration: this.getDuration(),
      reps: this.reps,
      avgQuality: this.getAvgQuality(),
      qualityHistory: this._qualityHistory,
      safetyEventCount: this.safetyEvents.length,
      dangerCount: this.safetyEvents.filter((e) => e.level === 'danger').length,
      warningCount: this.safetyEvents.filter((e) => e.level === 'warning').length,
      safetyEvents: this.safetyEvents,
      fatigueWarnings: this.fatigueWarnings,
      isFatigued: this.fatigue.isFatigued,
      endTime: new Date().toISOString(),
    };
  }

  /** 是否正在运行 */
  get isRunning() {
    return this.state === 'running';
  }
}

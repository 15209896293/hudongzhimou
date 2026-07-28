// 疲劳监测 — 时间里程碑 + 次数里程碑，30 秒冷却

export class FatigueMonitor {
  constructor() {
    this.warnings = [];
    this.lastWarningTime = 0;
    this.startTime = 0;
    this._timeTriggered = new Set();
    this._repTriggered = new Set();

    // 时间里程碑（毫秒）
    this.timeMilestones = [
      { ms: 5 * 60 * 1000, msg: '已训练 5 分钟，注意动作质量' },
      { ms: 10 * 60 * 1000, msg: '已训练 10 分钟，建议适当休息' },
      { ms: 15 * 60 * 1000, msg: '已训练 15 分钟，疲劳风险增加，建议停止' },
    ];

    // 次数里程碑
    this.repMilestones = [
      { count: 50, msg: '已完成 50 次，注意动作变形' },
      { count: 100, msg: '已完成 100 次，建议休息' },
      { count: 200, msg: '已完成 200 次，疲劳风险高' },
    ];

    this.cooldownMs = 30000; // 30 秒冷却
  }

  start() {
    this.startTime = performance.now();
    this._timeTriggered.clear();
    this._repTriggered.clear();
    this.warnings = [];
    this.lastWarningTime = 0;
  }

  /**
   * 每帧调用，检查时间里程碑
   * @returns {string|null} 提醒消息，null 表示无
   */
  check() {
    if (!this.startTime) return null;
    const now = performance.now();
    if (now - this.lastWarningTime < this.cooldownMs) return null;

    const elapsed = now - this.startTime;
    for (const m of this.timeMilestones) {
      if (elapsed >= m.ms && !this._timeTriggered.has(m.ms)) {
        this._timeTriggered.add(m.ms);
        this.lastWarningTime = now;
        this.warnings.push({ type: 'time', value: m.ms, message: m.msg });
        return m.msg;
      }
    }
    return null;
  }

  /**
   * 每次完成动作时调用
   * @param {number} count - 当前累计次数
   * @returns {string|null} 提醒消息
   */
  onRep(count) {
    const now = performance.now();
    if (now - this.lastWarningTime < this.cooldownMs) return null;

    for (const m of this.repMilestones) {
      if (count >= m.count && !this._repTriggered.has(m.count)) {
        this._repTriggered.add(m.count);
        this.lastWarningTime = now;
        this.warnings.push({ type: 'rep', value: m.count, message: m.msg });
        return m.msg;
      }
    }
    return null;
  }

  /** 是否已进入疲劳状态（超过 10 分钟或 100 次） */
  get isFatigued() {
    if (!this.startTime) return false;
    const elapsed = performance.now() - this.startTime;
    return elapsed >= 10 * 60 * 1000 || this._repTriggered.has(100);
  }

  reset() {
    this.startTime = 0;
    this._timeTriggered.clear();
    this._repTriggered.clear();
    this.warnings = [];
    this.lastWarningTime = 0;
  }
}

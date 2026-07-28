// 训练模式数据面板 — 计时 / 计数 / 质量评分 / 安全预警 / 疲劳状态

/** 质量分颜色档位 */
function qualityColor(score) {
  if (score >= 85) return '#30D158';   // 绿
  if (score >= 70) return '#FF9F0A';   // 橙
  return '#FF453A';                    // 红
}

/** 秒 → mm:ss */
function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

const DIM_LABELS = {
  kneeFlexion: '膝关节屈曲',
  elbowFlexion: '肘关节屈曲',
  trunkLean: '躯干前倾',
  kneeValgus: '膝关节内扣',
  trunkAlignment: '躯干直线度',
  shoulderStability: '肩部稳定',
  shoulderAbduction: '肩外展',
  shoulderFlexion: '肩屈曲',
  elbowExtension: '肘伸展',
  hipFlexion: '髋屈曲',
  trunkFlexion: '躯干屈曲',
  trunkStability: '躯干稳定',
  shoulderLevel: '肩部水平',
  lateralFlexion: '侧屈',
};

export class TrainingPanel {
  constructor() {
    this.durationEl = document.getElementById('train-duration');
    this.repsEl = document.getElementById('train-reps');
    this.stageEl = document.getElementById('train-stage');
    this.qualityEl = document.getElementById('train-quality');
    this.qualityBarEl = document.getElementById('train-quality-bar');
    this.breakdownEl = document.getElementById('train-quality-breakdown');
    this.alertsEl = document.getElementById('train-alerts');
    this.fatigueEl = document.getElementById('train-fatigue');
  }

  /**
   * 渲染训练快照
   * @param {object} snap - TrainingSession._snapshot() 输出
   * @param {object} [repDetail] - pipeline 的 rep 结果（含 stage/angle）
   */
  update(snap, repDetail) {
    if (!snap) return;

    // 计时
    if (this.durationEl) this.durationEl.textContent = formatTime(snap.duration);

    // 计数
    if (this.repsEl) this.repsEl.textContent = snap.reps;

    // 动作阶段
    if (this.stageEl && repDetail) {
      const stageMap = { up: '准备', down: '发力', hold: '保持' };
      this.stageEl.textContent = stageMap[repDetail.stage] || repDetail.stage || '--';
    }

    // 质量评分
    if (this.qualityEl) {
      const score = snap.lastQuality ? snap.lastQuality.score : snap.avgQuality;
      this.qualityEl.textContent = score || '--';
      this.qualityEl.style.color = score ? qualityColor(score) : '';
    }
    if (this.qualityBarEl) {
      const pct = snap.avgQuality || 0;
      this.qualityBarEl.style.width = `${pct}%`;
      this.qualityBarEl.style.background = qualityColor(pct);
    }

    // 质量明细
    if (this.breakdownEl && snap.lastQuality && snap.lastQuality.breakdown) {
      const entries = Object.entries(snap.lastQuality.breakdown);
      if (entries.length === 0) {
        this.breakdownEl.innerHTML = '<p class="empty-hint">动作标准</p>';
      } else {
        this.breakdownEl.innerHTML = entries.map(([dim, info]) => {
          const label = DIM_LABELS[dim] || dim;
          const cls = info.penalty === 0 ? '' : info.penalty < 15 ? 'warning' : 'danger';
          return `<div class="quality-row ${cls}"><span class="quality-label">${label}</span><span class="quality-value">${typeof info.value === 'number' ? info.value.toFixed(1) : '--'}°</span><span class="quality-penalty">-${info.penalty}</span></div>`;
        }).join('');
      }
    }

    // 安全预警
    if (this.alertsEl) {
      const alerts = (snap.lastSafety && snap.lastSafety.alerts) || [];
      if (alerts.length === 0) {
        this.alertsEl.innerHTML = '<p class="empty-hint">动作安全</p>';
      } else {
        this.alertsEl.innerHTML = alerts.map((a) => {
          const tag = a.severity === 'danger' ? 'danger' : 'warning';
          const side = a.side ? `（${a.side === 'left' ? '左' : '右'}）` : '';
          const val = a.value != null ? ` · ${a.value}` : '';
          return `<div class="alert-item ${tag}">${a.message}${side}${val}</div>`;
        }).join('');
      }
    }

    // 疲劳状态
    if (this.fatigueEl) {
      if (snap.isFatigued) {
        this.fatigueEl.textContent = '疲劳风险';
        this.fatigueEl.className = 'fatigue-badge danger';
      } else if (snap.fatigueWarnings && snap.fatigueWarnings.length > 0) {
        this.fatigueEl.textContent = '注意';
        this.fatigueEl.className = 'fatigue-badge warning';
      } else {
        this.fatigueEl.textContent = '状态良好';
        this.fatigueEl.className = 'fatigue-badge safe';
      }
    }
  }

  reset() {
    if (this.durationEl) this.durationEl.textContent = '00:00';
    if (this.repsEl) this.repsEl.textContent = '0';
    if (this.stageEl) this.stageEl.textContent = '--';
    if (this.qualityEl) { this.qualityEl.textContent = '--'; this.qualityEl.style.color = ''; }
    if (this.qualityBarEl) { this.qualityBarEl.style.width = '0%'; this.qualityBarEl.style.background = ''; }
    if (this.breakdownEl) this.breakdownEl.innerHTML = '<p class="empty-hint">开始训练后显示</p>';
    if (this.alertsEl) this.alertsEl.innerHTML = '<p class="empty-hint">开始训练后显示</p>';
    if (this.fatigueEl) { this.fatigueEl.textContent = '--'; this.fatigueEl.className = 'fatigue-badge'; }
  }
}

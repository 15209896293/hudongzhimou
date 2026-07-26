// 数据面板：关节角度 + 风险预警

export class Dashboard {
  constructor() {
    this.anglesEl = document.getElementById('angles-list');
    this.alertsEl = document.getElementById('alerts-list');
  }

  /**
   * 更新关节角度列表
   * @param {{metrics:Object, test:string}} fmsResult
   */
  updateAngles(fmsResult) {
    if (!this.anglesEl) return;
    const metrics = fmsResult?.metrics;
    if (!metrics) {
      this.anglesEl.innerHTML = '<p class="empty-hint">开始检测后显示</p>';
      return;
    }
    const labels = this._metricLabels(fmsResult.test);
    const html = Object.entries(metrics)
      .filter(([k]) => labels[k] != null)
      .map(([k, v]) => {
        const fmt = typeof v === 'number' && v < 1 ? v.toFixed(3) : v;
        return `<div class="angle-item"><span class="angle-label">${labels[k]}</span><span class="angle-value">${fmt}</span></div>`;
      }).join('');
    this.anglesEl.innerHTML = html || '<p class="empty-hint">无数据</p>';
  }

  /**
   * 更新风险预警列表
   * @param {{level:string, alerts:Array}} safetyResult
   */
  updateAlerts(safetyResult) {
    if (!this.alertsEl) return;
    const alerts = safetyResult?.alerts || [];
    if (alerts.length === 0) {
      this.alertsEl.innerHTML = `<div class="alert-item safe">✓ 未检测到风险</div>`;
      return;
    }
    this.alertsEl.innerHTML = alerts.map((a) => {
      const cls = a.severity === 'danger' ? 'danger' : 'warning';
      const val = a.value != null ? ` · ${a.value}` : '';
      return `<div class="alert-item ${cls}">⚠ ${a.message}${val}</div>`;
    }).join('');
  }

  // 各动作的指标中文标签
  _metricLabels(test) {
    const map = {
      deep_squat: { kneeFlexion: '膝关节屈曲', kneeFlexL: '左膝屈曲', kneeFlexR: '右膝屈曲', trunkLean: '躯干前倾', kneeValgus: '膝外翻' },
      hurdle_step: { hipFlexion: '髋屈曲', kneeOffset: '膝偏离', pelvicTilt: '骨盆倾斜' },
      inline_lunge: { frontKneeAlign: '前膝对齐', rearExtension: '后腿伸展', trunkLean: '躯干前倾' },
      shoulder_mobility: { raiseHeight: '上举高度', raiseL: '左肩', raiseR: '右肩', asymmetry: '不对称度' },
      aslr: { legRaiseAngle: '抬腿角度', ankleVsOppKnee: '踝-对侧膝' },
      trunk_stability: { trunkSag: '躯干下凹', sagType: '姿态' },
      rotary_stability: { shoulderTilt: '肩倾斜', hipTilt: '髋倾斜', kneeAsymmetry: '膝不对称' },
    };
    return map[test] || {};
  }

  reset() {
    if (this.anglesEl) this.anglesEl.innerHTML = '<p class="empty-hint">开始检测后显示</p>';
    if (this.alertsEl) this.alertsEl.innerHTML = '<p class="empty-hint">开始检测后显示</p>';
  }
}

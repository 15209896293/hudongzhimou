// FMS 评分面板：更新当前评分、评分条、问题列表

const SCORE_COLORS = { 3: '#30D158', 2: '#FF9F0A', 1: '#FF453A', 0: '#AEAEB2' };

export class FMSPanel {
  constructor() {
    this.scoreEl = document.getElementById('fms-score');
    this.barEl = document.querySelector('.score-bar-fill');
    this.issuesEl = document.getElementById('fms-issues');
  }

  /**
   * 更新评分显示
   * @param {{score:number, issues:Array, recommendations:Array, test:string}} fmsResult
   */
  update(fmsResult) {
    if (!fmsResult) return;

    this.scoreEl.textContent = fmsResult.score ?? '--';
    const color = SCORE_COLORS[fmsResult.score] || SCORE_COLORS[0];
    this.scoreEl.style.color = color;

    if (this.barEl) {
      const pct = ((fmsResult.score || 0) / 3) * 100;
      this.barEl.style.width = `${pct}%`;
      this.barEl.style.background = color;
    }

    // 问题列表
    if (this.issuesEl) {
      const issues = fmsResult.issues || [];
      if (issues.length === 0) {
        this.issuesEl.innerHTML = '<p class="empty-hint">动作标准</p>';
      } else {
        this.issuesEl.innerHTML = issues.map((it) => {
          const tag = it.severity === 'severe' ? 'danger' : it.severity === 'moderate' ? 'warning' : '';
          const side = it.side ? `（${it.side === 'left' ? '左' : '右'}）` : '';
          return `<div class="alert-item ${tag}">${it.problem}${side}${it.value != null ? ` · ${typeof it.value === 'number' ? it.value.toFixed(it.value < 1 ? 3 : 0) : it.value}` : ''}</div>`;
        }).join('');
      }
    }
  }

  reset() {
    this.scoreEl.textContent = '--';
    this.scoreEl.style.color = '';
    if (this.barEl) { this.barEl.style.width = '0%'; this.barEl.style.background = ''; }
    if (this.issuesEl) this.issuesEl.innerHTML = '';
  }
}

// 报告页：FMS 总分圆环图 + 七项雷达图 + 历史趋势 + AI 教练建议
// 全部用 SVG 绘制，无第三方图表库

import { FMS_TESTS } from '../core/fms-engine.js';

const RISK_COLORS = { low: '#30D158', moderate: '#FF9F0A', high: '#FF453A' };
const RISK_LABELS = { low: '受伤风险低', moderate: '受伤风险中等', high: '受伤风险高' };

export class ReportView {
  constructor(container) {
    this.container = container || document.getElementById('report-content');
  }

  /**
   * 渲染完整报告
   * @param {object} session - { scores:{}, totalScore, risk, aiAnalysis?, testDate }
   */
  render(session) {
    if (!session || !session.scores) {
      this.container.innerHTML = '<div class="card report-empty"><p class="empty-hint">完成一次 FMS 筛查后，此处将展示评分报告</p></div>';
      return;
    }
    const { scores, totalScore, risk, aiAnalysis, testDate } = session;
    const riskLevel = risk?.level || 'moderate';

    this.container.innerHTML = `
      <div class="card report-card">
        <h3 class="card-title">FMS 总分</h3>
        <div class="report-score-ring">
          ${this._ringSVG(totalScore, 21, RISK_COLORS[riskLevel])}
          <span class="risk-badge ${riskLevel}">${RISK_LABELS[riskLevel]}</span>
          <p class="empty-hint">${testDate || ''}</p>
        </div>
      </div>
      <div class="card report-card">
        <h3 class="card-title">七项评分</h3>
        <div style="display:flex;justify-content:center">${this._radarSVG(scores)}</div>
      </div>
      <div class="card report-card report-card-full">
        <h3 class="card-title">各单项详情</h3>
        ${this._detailTable(scores)}
      </div>
      ${aiAnalysis ? `<div class="card report-card report-card-full"><h3 class="card-title">AI 教练建议</h3><div class="coaching-card">${aiAnalysis}</div></div>` : ''}
    `;
  }

  /** 渲染历史趋势 */
  renderTrend(history) {
    if (!history || history.length === 0) {
      return '<p class="empty-hint">暂无历史记录</p>';
    }
    const trendEl = document.createElement('div');
    trendEl.className = 'card report-card report-card-full';
    trendEl.innerHTML = `<h3 class="card-title">历史趋势</h3><div style="display:flex;justify-content:center">${this._trendSVG(history)}</div>`;
    this.container.appendChild(trendEl);
  }

  // ---- 圆环图 ----
  _ringSVG(score, max, color) {
    const r = 70, cx = 90, cy = 90;
    const circ = 2 * Math.PI * r;
    const pct = Math.max(0, Math.min(1, score / max));
    const offset = circ * (1 - pct);
    return `
      <svg class="ring-svg" viewBox="0 0 180 180">
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#F5F5F7" stroke-width="14"/>
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${color}" stroke-width="14"
          stroke-linecap="round" stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
          transform="rotate(-90 ${cx} ${cy})"/>
        <text x="${cx}" y="${cy - 4}" text-anchor="middle" class="ring-center">${score}</text>
        <text x="${cx}" y="${cy + 20}" text-anchor="middle" class="ring-label">/ ${max}</text>
      </svg>`;
  }

  // ---- 雷达图（七轴 0-3）----
  _radarSVG(scores) {
    const size = 320, cx = size / 2, cy = size / 2, R = 120;
    const n = FMS_TESTS.length;
    const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2; // 从正上方开始

    // 参考圆（1/2/3 分）
    let grid = '';
    for (const lv of [1, 2, 3]) {
      const rr = (R * lv) / 3;
      let pts = '';
      for (let i = 0; i < n; i++) {
        const a = angle(i);
        pts += `${cx + rr * Math.cos(a)},${cy + rr * Math.sin(a)} `;
      }
      grid += `<polygon points="${pts}" fill="none" stroke="#E5E5EA" stroke-width="1"/>`;
    }
    // 轴线 + 标签
    let axes = '', labels = '';
    FMS_TESTS.forEach((t, i) => {
      const a = angle(i);
      const x2 = cx + R * Math.cos(a), y2 = cy + R * Math.sin(a);
      axes += `<line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="#E5E5EA" stroke-width="1"/>`;
      const lx = cx + (R + 18) * Math.cos(a), ly = cy + (R + 18) * Math.sin(a);
      const sc = scores[t.key]?.score ?? 0;
      labels += `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="middle" font-size="9" fill="#6E6E73">${t.name}</text>`;
    });
    // 数据多边形
    let dataPts = '';
    FMS_TESTS.forEach((t, i) => {
      const sc = scores[t.key]?.score ?? 0;
      const rr = (R * sc) / 3;
      const a = angle(i);
      dataPts += `${cx + rr * Math.cos(a)},${cy + rr * Math.sin(a)} `;
    });

    return `
      <svg class="radar-svg" viewBox="0 0 ${size} ${size}">
        ${grid}${axes}
        <polygon points="${dataPts}" fill="rgba(0,122,255,0.2)" stroke="#007AFF" stroke-width="2"/>
        ${FMS_TESTS.map((t, i) => {
          const sc = scores[t.key]?.score ?? 0;
          const rr = (R * sc) / 3; const a = angle(i);
          const x = cx + rr * Math.cos(a), y = cy + rr * Math.sin(a);
          return `<circle cx="${x}" cy="${y}" r="3" fill="${sc >= 2 ? '#30D158' : sc === 1 ? '#FF9F0A' : '#FF453A'}"/>`;
        }).join('')}
        ${labels}
      </svg>`;
  }

  // ---- 单项详情表 ----
  _detailTable(scores) {
    const rows = FMS_TESTS.map((t) => {
      const s = scores[t.key];
      const sc = s?.score ?? 0;
      const color = sc >= 2 ? '#30D158' : sc === 1 ? '#FF9F0A' : '#FF453A';
      const issues = (s?.issues || []).map((i) => i.problem).join('；') || '动作标准';
      return `<tr><td style="padding:6px 8px">${t.name}</td>
        <td style="padding:6px 8px;text-align:center"><span style="color:${color};font-weight:600">${sc}</span> / 3</td>
        <td style="padding:6px 8px;color:#6E6E73;font-size:12px">${issues}</td></tr>`;
    }).join('');
    return `<table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead><tr style="border-bottom:1px solid #E5E5EA">
        <th style="text-align:left;padding:6px 8px;font-weight:600">动作</th>
        <th style="padding:6px 8px;font-weight:600">评分</th>
        <th style="text-align:left;padding:6px 8px;font-weight:600">问题</th>
      </tr></thead><tbody>${rows}</tbody></table>`;
  }

  // ---- 历史趋势折线图 ----
  _trendSVG(history) {
    const w = 520, h = 180, pad = 30;
    const pts = history.map((h0, i) => i);
    const max = 21;
    const n = history.length;
    const x = (i) => pad + (i / Math.max(1, n - 1)) * (w - pad * 2);
    const y = (v) => h - pad - (v / max) * (h - pad * 2);

    let line = '', dots = '', xlabels = '';
    history.forEach((rec, i) => {
      const px = x(i), py = y(rec.total_score ?? 0);
      line += `${i === 0 ? 'M' : 'L'}${px},${py} `;
      dots += `<circle cx="${px}" cy="${py}" r="3" fill="#007AFF"/>`;
      xlabels += `<text x="${px}" y="${h - pad + 14}" text-anchor="middle" font-size="9" fill="#AEAEB2">${(rec.test_date || '').slice(5, 10)}</text>`;
    });

    return `
      <svg viewBox="0 0 ${w} ${h}" style="width:100%;max-width:520px">
        ${[0, 7, 14, 21].map((v) => `<line x1="${pad}" y1="${y(v)}" x2="${w - pad}" y2="${y(v)}" stroke="#F0F0F2"/><text x="${pad - 6}" y="${y(v) + 3}" text-anchor="end" font-size="9" fill="#AEAEB2">${v}</text>`).join('')}
        <path d="${line}" fill="none" stroke="#007AFF" stroke-width="2"/>
        ${dots}${xlabels}
      </svg>`;
  }

  reset() {
    this.container.innerHTML = '<div class="card report-empty"><p class="empty-hint">完成一次 FMS 筛查后，此处将展示评分报告</p></div>';
  }
}

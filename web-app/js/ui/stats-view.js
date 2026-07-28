// 训练统计页 — 4 Tab：总览 / 动作分布 / 质量趋势 / 安全事件
// 全部用 SVG 绘制，无第三方图表库，风格与 report-view 一致

import { storage } from '../utils/storage.js';
import { formatDate } from '../utils/helpers.js';

const TABS = [
  { key: 'overview', label: '训练总览' },
  { key: 'distribution', label: '动作分布' },
  { key: 'quality', label: '质量趋势' },
  { key: 'safety', label: '安全事件' },
];

export class StatsView {
  constructor(container) {
    this.container = container || document.getElementById('stats-content');
    this.activeTab = 'overview';
  }

  /** 读取本地训练记录 */
  static loadRecords() {
    return storage.get('training_records', []);
  }

  /** 保存一条训练记录 */
  static saveRecord(summary) {
    const records = StatsView.loadRecords();
    records.push({ ...summary, id: Date.now() });
    storage.set('training_records', records);
    return records;
  }

  /** 渲染整个统计页 */
  render() {
    if (!this.container) return;
    const records = StatsView.loadRecords();

    const tabs = TABS.map((t) =>
      `<button class="stats-tab ${t.key === this.activeTab ? 'active' : ''}" data-tab="${t.key}">${t.label}</button>`
    ).join('');

    this.container.innerHTML = `
      <div class="stats-tabs">${tabs}</div>
      <div class="stats-body" id="stats-body"></div>
    `;

    this.container.querySelectorAll('.stats-tab').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.activeTab = btn.dataset.tab;
        this.container.querySelectorAll('.stats-tab').forEach((b) => b.classList.toggle('active', b === btn));
        this._renderTab(records);
      });
    });

    this._renderTab(records);
  }

  _renderTab(records) {
    const body = this.container.querySelector('#stats-body');
    if (!body) return;

    if (!records || records.length === 0) {
      body.innerHTML = '<div class="card report-empty"><p class="empty-hint">完成一次训练后，此处将展示训练统计</p></div>';
      return;
    }

    switch (this.activeTab) {
      case 'overview': body.innerHTML = this._overview(records); break;
      case 'distribution': body.innerHTML = this._distribution(records); break;
      case 'quality': body.innerHTML = this._quality(records); break;
      case 'safety': body.innerHTML = this._safety(records); break;
    }
  }

  // ---- Tab 1: 训练总览 ----
  _overview(records) {
    const totalSessions = records.length;
    const totalReps = records.reduce((s, r) => s + (r.reps || 0), 0);
    const totalDuration = records.reduce((s, r) => s + (r.duration || 0), 0);
    const avgQuality = Math.round(records.reduce((s, r) => s + (r.avgQuality || 0), 0) / totalSessions);
    const totalDanger = records.reduce((s, r) => s + (r.dangerCount || 0), 0);

    const kpi = (label, value, unit, color) => `
      <div class="card stats-kpi">
        <p class="stats-kpi-label">${label}</p>
        <p class="stats-kpi-value" style="${color ? `color:${color}` : ''}">${value}<span class="stats-kpi-unit">${unit}</span></p>
      </div>`;

    return `
      <div class="stats-kpi-grid">
        ${kpi('训练次数', totalSessions, '次')}
        ${kpi('累计动作', totalReps, '次')}
        ${kpi('累计时长', this._fmtDur(totalDuration), '', '#007AFF')}
        ${kpi('平均质量', avgQuality, '/100', avgQuality >= 85 ? '#30D158' : avgQuality >= 70 ? '#FF9F0A' : '#FF453A')}
        ${kpi('危险事件', totalDanger, '次', totalDanger > 0 ? '#FF453A' : '#30D158')}
      </div>
      <div class="card report-card report-card-full">
        <h3 class="card-title">最近训练</h3>
        ${this._recentTable(records.slice(-10).reverse())}
      </div>`;
  }

  // ---- Tab 2: 动作分布 ----
  _distribution(records) {
    const byExercise = {};
    for (const r of records) {
      const key = r.exercise || 'unknown';
      if (!byExercise[key]) byExercise[key] = { name: r.exerciseName || key, reps: 0, duration: 0, sessions: 0 };
      byExercise[key].reps += r.reps || 0;
      byExercise[key].duration += r.duration || 0;
      byExercise[key].sessions++;
    }
    const items = Object.values(byExercise).sort((a, b) => b.reps - a.reps);
    const maxReps = Math.max(1, ...items.map((i) => i.reps));

    const bars = items.map((it) => {
      const w = (it.reps / maxReps) * 100;
      return `<div class="dist-row">
        <span class="dist-name">${it.name}</span>
        <div class="dist-bar-wrap"><div class="dist-bar" style="width:${w}%"></div></div>
        <span class="dist-val">${it.reps}次 · ${this._fmtDur(it.duration)} · ${it.sessions}组</span>
      </div>`;
    }).join('');

    return `<div class="card report-card report-card-full">
      <h3 class="card-title">各动作累计</h3>
      <div class="dist-list">${bars || '<p class="empty-hint">暂无数据</p>'}</div>
    </div>`;
  }

  // ---- Tab 3: 质量趋势 ----
  _quality(records) {
    const recent = records.slice(-20);
    const svg = this._trendSVG(recent);
    return `<div class="card report-card report-card-full">
      <h3 class="card-title">质量评分趋势（最近 ${recent.length} 次）</h3>
      <div style="display:flex;justify-content:center">${svg}</div>
    </div>`;
  }

  // ---- Tab 4: 安全事件 ----
  _safety(records) {
    const events = [];
    for (const r of records) {
      for (const e of (r.safetyEvents || [])) {
        events.push({ ...e, exercise: r.exerciseName, date: (r.endTime || '').slice(0, 10) });
      }
    }
    events.reverse();

    if (events.length === 0) {
      return '<div class="card report-empty"><p class="empty-hint">暂无安全事件记录</p></div>';
    }

    const rows = events.slice(0, 50).map((e) => {
      const cls = e.level === 'danger' ? 'danger' : 'warning';
      const tag = e.level === 'danger' ? '危险' : '警告';
      return `<tr>
        <td style="padding:6px 8px"><span class="safety-tag ${cls}">${tag}</span></td>
        <td style="padding:6px 8px">${e.exercise || '--'}</td>
        <td style="padding:6px 8px">${e.message}</td>
        <td style="padding:6px 8px;text-align:center">${e.value != null ? e.value : '--'}</td>
        <td style="padding:6px 8px;color:#AEAEB2;font-size:12px">${e.date} · ${this._fmtDur(e.time)}</td>
      </tr>`;
    }).join('');

    return `<div class="card report-card report-card-full">
      <h3 class="card-title">安全事件记录（最近 ${Math.min(50, events.length)} 条）</h3>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead><tr style="border-bottom:1px solid #E5E5EA">
          <th style="text-align:left;padding:6px 8px">级别</th>
          <th style="text-align:left;padding:6px 8px">动作</th>
          <th style="text-align:left;padding:6px 8px">事件</th>
          <th style="padding:6px 8px">数值</th>
          <th style="text-align:left;padding:6px 8px">时间</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  // ---- 最近训练表 ----
  _recentTable(records) {
    const rows = records.map((r) => {
      const qColor = (r.avgQuality || 0) >= 85 ? '#30D158' : (r.avgQuality || 0) >= 70 ? '#FF9F0A' : '#FF453A';
      return `<tr>
        <td style="padding:6px 8px">${r.exerciseName || r.exercise}</td>
        <td style="padding:6px 8px;text-align:center">${r.reps || 0}</td>
        <td style="padding:6px 8px;text-align:center">${this._fmtDur(r.duration)}</td>
        <td style="padding:6px 8px;text-align:center;color:${qColor};font-weight:600">${r.avgQuality || '--'}</td>
        <td style="padding:6px 8px;text-align:center">${r.dangerCount || 0}</td>
        <td style="padding:6px 8px;color:#AEAEB2;font-size:12px">${(r.endTime || '').slice(0, 10)}</td>
      </tr>`;
    }).join('');
    return `<table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead><tr style="border-bottom:1px solid #E5E5EA">
        <th style="text-align:left;padding:6px 8px">动作</th>
        <th style="padding:6px 8px">次数</th>
        <th style="padding:6px 8px">时长</th>
        <th style="padding:6px 8px">质量</th>
        <th style="padding:6px 8px">危险</th>
        <th style="text-align:left;padding:6px 8px">日期</th>
      </tr></thead><tbody>${rows}</tbody></table>`;
  }

  // ---- 质量趋势折线 ----
  _trendSVG(records) {
    const w = 520, h = 180, pad = 30;
    const n = records.length;
    const x = (i) => pad + (n <= 1 ? (w - pad * 2) / 2 : (i / (n - 1)) * (w - pad * 2));
    const y = (v) => h - pad - (v / 100) * (h - pad * 2);

    let line = '', dots = '', xlabels = '';
    records.forEach((r, i) => {
      const px = x(i), py = y(r.avgQuality || 0);
      line += `${i === 0 ? 'M' : 'L'}${px},${py} `;
      const color = (r.avgQuality || 0) >= 85 ? '#30D158' : (r.avgQuality || 0) >= 70 ? '#FF9F0A' : '#FF453A';
      dots += `<circle cx="${px}" cy="${py}" r="3" fill="${color}"/>`;
      xlabels += `<text x="${px}" y="${h - pad + 14}" text-anchor="middle" font-size="9" fill="#AEAEB2">${(r.endTime || '').slice(5, 10)}</text>`;
    });

    return `<svg viewBox="0 0 ${w} ${h}" style="width:100%;max-width:520px">
      ${[0, 25, 50, 75, 100].map((v) => `<line x1="${pad}" y1="${y(v)}" x2="${w - pad}" y2="${y(v)}" stroke="#F0F0F2"/><text x="${pad - 6}" y="${y(v) + 3}" text-anchor="end" font-size="9" fill="#AEAEB2">${v}</text>`).join('')}
      <path d="${line}" fill="none" stroke="#007AFF" stroke-width="2"/>
      ${dots}${xlabels}
    </svg>`;
  }

  _fmtDur(sec) {
    if (!sec) return '0秒';
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return m > 0 ? `${m}分${s > 0 ? s + '秒' : ''}` : `${s}秒`;
  }
}

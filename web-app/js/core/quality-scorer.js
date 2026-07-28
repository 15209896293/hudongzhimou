// 动作质量评分 — 0-100 分制
// 每个动作定义"标准动作模型"，实时对比输出质量评分

import {
  calculateAngle,
  calculateFromVertical,
  calculateKneeValgus,
  deviationFromLine,
} from './angle-utils.js';

const VIS_THRESHOLD = 0.5;

function pt(landmarks, idx) {
  return landmarks?.[idx] || { x: 0, y: 0, z: 0, visibility: 0 };
}

function vis(p) {
  return (p?.visibility ?? 0) >= VIS_THRESHOLD;
}

export class QualityScorer {
  /**
   * @param {object} rules - EXERCISES[key].quality
   */
  constructor(rules) {
    this.rules = rules || {};
  }

  /**
   * 评分
   * @param {Array} landmarks - MediaPipe 33 点
   * @returns {{ score: number, breakdown: object }}
   */
  score(landmarks) {
    if (!landmarks || landmarks.length < 33) {
      return { score: 0, breakdown: {} };
    }

    let total = 100;
    const breakdown = {};

    // 逐维度计算
    for (const [dim, rule] of Object.entries(this.rules)) {
      const value = this._calcDimension(landmarks, dim);
      if (value == null) continue;
      const penalty = this._evalRule(value, rule);
      total -= penalty;
      breakdown[dim] = { value: Math.round(value * 100) / 100, penalty };
    }

    return { score: Math.max(0, Math.round(total)), breakdown };
  }

  /** 计算某个维度的数值（角度或偏离度） */
  _calcDimension(landmarks, dim) {
    const ls = pt(landmarks, 11), rs = pt(landmarks, 12);
    const le = pt(landmarks, 13), re = pt(landmarks, 14);
    const lw = pt(landmarks, 15), rw = pt(landmarks, 16);
    const lh = pt(landmarks, 23), rh = pt(landmarks, 24);
    const lk = pt(landmarks, 25), rk = pt(landmarks, 26);
    const la = pt(landmarks, 27), ra = pt(landmarks, 28);

    const shoulderMid = { x: (ls.x + rs.x) / 2, y: (ls.y + rs.y) / 2 };
    const hipMid = { x: (lh.x + rh.x) / 2, y: (lh.y + rh.y) / 2 };
    const kneeMid = { x: (lk.x + rk.x) / 2, y: (lk.y + rk.y) / 2 };

    switch (dim) {
      case 'kneeFlexion':
        if (!vis(lh) || !vis(lk) || !vis(la)) return null;
        return (calculateAngle(lh, lk, la) + calculateAngle(rh, rk, ra)) / 2;

      case 'elbowFlexion':
        if (!vis(ls) || !vis(le) || !vis(lw)) return null;
        return (calculateAngle(ls, le, lw) + calculateAngle(rs, re, rw)) / 2;

      case 'trunkLean':
        if (!vis(ls) || !vis(rs) || !vis(lh) || !vis(rh)) return null;
        return calculateFromVertical(shoulderMid, hipMid);

      case 'kneeValgus': {
        if (!vis(lh) || !vis(lk) || !vis(la)) return null;
        const vL = calculateKneeValgus(lh, lk, la, 'left');
        const vR = calculateKneeValgus(rh, rk, ra, 'right');
        return Math.max(Math.abs(vL), Math.abs(vR));
      }

      case 'trunkAlignment':
        if (!vis(ls) || !vis(rs) || !vis(lh) || !vis(rh) || !vis(lk) || !vis(rk)) return null;
        return deviationFromLine(shoulderMid, hipMid, kneeMid);

      case 'shoulderStability': {
        // 肩关节角度（肘-肩-髋），评估上臂是否稳定
        if (!vis(le) || !vis(ls) || !vis(lh)) return null;
        const angL = calculateAngle(le, ls, lh);
        const angR = calculateAngle(re, rs, rh);
        // 理想值 ~0-15°（大臂贴近身体），偏离越大越不稳
        return Math.min(angL, angR);
      }

      case 'shoulderAbduction':
      case 'shoulderFlexion': {
        // 肩外展/屈曲角度（髋-肩-肘）
        if (!vis(lh) || !vis(ls) || !vis(le)) return null;
        return (calculateAngle(lh, ls, le) + calculateAngle(rh, rs, re)) / 2;
      }

      case 'elbowExtension':
        if (!vis(ls) || !vis(le) || !vis(lw)) return null;
        return (calculateAngle(ls, le, lw) + calculateAngle(rs, re, rw)) / 2;

      case 'hipFlexion': {
        if (!vis(ls) || !vis(lh) || !vis(lk)) return null;
        return (calculateAngle(ls, lh, lk) + calculateAngle(rs, rh, rk)) / 2;
      }

      case 'trunkFlexion': {
        // 躯干屈曲角度（肩-髋-膝）
        if (!vis(ls) || !vis(lh) || !vis(lk)) return null;
        return (calculateAngle(ls, lh, lk) + calculateAngle(rs, rh, rk)) / 2;
      }

      case 'trunkStability':
        if (!vis(ls) || !vis(rs) || !vis(lh) || !vis(rh)) return null;
        return calculateFromVertical(shoulderMid, hipMid);

      case 'shoulderLevel':
        if (!vis(ls) || !vis(rs)) return null;
        return Math.abs(ls.y - rs.y);

      case 'lateralFlexion': {
        // 侧弯角度（肩连线与水平线夹角）
        if (!vis(ls) || !vis(rs)) return null;
        const dx = rs.x - ls.x;
        const dy = rs.y - ls.y;
        // 0=水平，90=垂直侧弯
        return Math.abs(Math.atan2(Math.abs(dy), Math.abs(dx) || 1e-6) * 180 / Math.PI);
      }

      default:
        return null;
    }
  }

  /** 三档扣分评估 */
  _evalRule(value, rule) {
    const [idealMin, idealMax] = rule.ideal;
    const [mildMin, mildMax] = rule.mild;
    const [badMin, badMax] = rule.bad;

    if (value >= idealMin && value <= idealMax) return 0;
    if (value >= mildMin && value <= mildMax) return Math.round(rule.penalty * 0.4);
    return rule.penalty;
  }
}

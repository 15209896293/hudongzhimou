// 防伤规则检测引擎
// 检测膝关节内扣、骨盆倾斜、躯干过度前倾、左右不对称

import { calculateKneeValgus, calculateFromVertical, calculateAngle } from './angle-utils.js';
import { POSE_LANDMARKS } from './pose-detector.js';

const VIS_THRESHOLD = 0.5;

function pt(landmarks, idx) {
  return landmarks?.[idx] || { x: 0, y: 0, z: 0, visibility: 0 };
}
function vis(p) {
  return (p?.visibility ?? 0) >= VIS_THRESHOLD;
}

export class SafetyChecker {
  /**
   * 执行全部防伤规则检测
   * @param {Array<object>} landmarks - MediaPipe 33 关键点
   * @returns {{ level: 'safe'|'warning'|'danger', alerts: Array }}
   *   alert: { type, side?, severity, message, value?, joint }
   */
  check(landmarks) {
    const alerts = [];
    if (!landmarks || landmarks.length < 33) {
      return { level: 'safe', alerts };
    }

    const lh = pt(landmarks, 23), rh = pt(landmarks, 24);
    const lk = pt(landmarks, 25), rk = pt(landmarks, 26);
    const la = pt(landmarks, 27), ra = pt(landmarks, 28);
    const ls = pt(landmarks, 11), rs = pt(landmarks, 12);

    // ---- 1. 膝关节内扣（valgus）----
    if (vis(lh) && vis(lk) && vis(la)) {
      const v = calculateKneeValgus(lh, lk, la, 'left');
      this._pushKneeAlert(alerts, 'left', v);
    }
    if (vis(rh) && vis(rk) && vis(ra)) {
      const v = calculateKneeValgus(rh, rk, ra, 'right');
      this._pushKneeAlert(alerts, 'right', v);
    }

    // ---- 2. 骨盆倾斜 ----
    if (vis(lh) && vis(rh)) {
      const tilt = Math.abs(lh.y - rh.y);
      if (tilt > 0.06) {
        alerts.push({ type: 'pelvic_tilt', severity: 'danger', joint: 'pelvis', message: '骨盆明显倾斜', value: +tilt.toFixed(3) });
      } else if (tilt > 0.03) {
        alerts.push({ type: 'pelvic_tilt', severity: 'warning', joint: 'pelvis', message: '骨盆轻微倾斜', value: +tilt.toFixed(3) });
      }
    }

    // ---- 3. 躯干过度前倾 ----
    if (vis(ls) && vis(rs) && vis(lh) && vis(rh)) {
      const shoulderMid = { x: (ls.x + rs.x) / 2, y: (ls.y + rs.y) / 2 };
      const hipMid = { x: (lh.x + rh.x) / 2, y: (lh.y + rh.y) / 2 };
      const lean = calculateFromVertical(shoulderMid, hipMid);
      if (lean > 45) {
        alerts.push({ type: 'trunk_lean', severity: 'danger', joint: 'trunk', message: '躯干过度前倾', value: Math.round(lean) });
      } else if (lean > 30) {
        alerts.push({ type: 'trunk_lean', severity: 'warning', joint: 'trunk', message: '躯干前倾偏大', value: Math.round(lean) });
      }
    }

    // ---- 4. 左右膝关节角度不对称 ----
    if (vis(lh) && vis(lk) && vis(la) && vis(rh) && vis(rk) && vis(ra)) {
      const angL = calculateAngle(lh, lk, la);
      const angR = calculateAngle(rh, rk, ra);
      const diff = Math.abs(angL - angR);
      if (diff > 25) {
        alerts.push({ type: 'asymmetry', severity: 'warning', joint: 'knee', message: '左右膝关节角度不对称', value: Math.round(diff) });
      }
    }

    const level = alerts.some((a) => a.severity === 'danger') ? 'danger'
      : alerts.some((a) => a.severity === 'warning') ? 'warning'
      : 'safe';

    return { level, alerts };
  }

  _pushKneeAlert(alerts, side, valgus) {
    if (valgus > 25) {
      alerts.push({ type: 'knee_valgus', side, severity: 'danger', joint: 'knee', message: `${side === 'left' ? '左' : '右'}膝严重内扣`, value: Math.round(valgus) });
    } else if (valgus > 15) {
      alerts.push({ type: 'knee_valgus', side, severity: 'warning', joint: 'knee', message: `${side === 'left' ? '左' : '右'}膝内扣`, value: Math.round(valgus) });
    }
  }

  /**
   * 训练模式专用：按动作配置检测
   * @param {Array} landmarks - MediaPipe 33 点
   * @param {object} exerciseConfig - EXERCISES[key] 的配置
   * @param {object} adjustedThresholds - 个性化后的安全阈值
   * @returns {{ level: 'safe'|'warning'|'danger', alerts: Array }}
   */
  checkForExercise(landmarks, exerciseConfig, adjustedThresholds) {
    const alerts = [];
    if (!landmarks || landmarks.length < 33) {
      return { level: 'safe', alerts };
    }

    // 按动作配置的关节逐个检测
    for (const [joint, threshold] of Object.entries(adjustedThresholds || {})) {
      const angle = this._getJointAngle(landmarks, joint);
      if (angle == null) continue;

      if (angle < threshold.min || angle > threshold.max) {
        alerts.push({
          type: `${joint}_danger`,
          severity: 'danger',
          joint,
          message: exerciseConfig.voiceTips[`${joint}_min`] || exerciseConfig.voiceTips[`${joint}_max`] || `${joint}角度超出安全范围`,
          value: Math.round(angle),
        });
      } else if (angle < threshold.warning_min || angle > threshold.warning_max) {
        alerts.push({
          type: `${joint}_warning`,
          severity: 'warning',
          joint,
          message: exerciseConfig.voiceTips[`${joint}_min`] || exerciseConfig.voiceTips[`${joint}_max`] || `${joint}角度接近安全边界`,
          value: Math.round(angle),
        });
      }
    }

    // 同时保留通用规则（膝内扣、骨盆倾斜、躯干前倾、不对称）
    const general = this.check(landmarks);
    alerts.push(...general.alerts);

    const level = alerts.some((a) => a.severity === 'danger') ? 'danger'
      : alerts.some((a) => a.severity === 'warning') ? 'warning'
      : 'safe';

    return { level, alerts };
  }

  /** 计算指定关节的角度（左右均值） */
  _getJointAngle(landmarks, joint) {
    const jointMap = {
      knee: { pts: [23, 25, 27], mirror: [24, 26, 28] },
      elbow: { pts: [11, 13, 15], mirror: [12, 14, 16] },
      shoulder: { pts: [13, 11, 23], mirror: [14, 12, 24] },
      back: { pts: [11, 23, 25], mirror: [12, 24, 26] },
      lower_back: { pts: [11, 23, 25], mirror: [12, 24, 26] },
      hip: { pts: [11, 23, 25], mirror: [12, 24, 26] },
      neck: { pts: [7, 11, 12], mirror: [8, 12, 11] },
      spine: { pts: [11, 23, 25], mirror: [12, 24, 26] },
    };
    const cfg = jointMap[joint];
    if (!cfg) return null;
    const a = pt(landmarks, cfg.pts[0]);
    const b = pt(landmarks, cfg.pts[1]);
    const c = pt(landmarks, cfg.pts[2]);
    const am = pt(landmarks, cfg.mirror[0]);
    const bm = pt(landmarks, cfg.mirror[1]);
    const cm = pt(landmarks, cfg.mirror[2]);
    if (!vis(a) || !vis(b) || !vis(c)) return null;
    const angleL = calculateAngle(a, b, c);
    if (!vis(am) || !vis(bm) || !vis(cm)) return angleL;
    const angleR = calculateAngle(am, bm, cm);
    return (angleL + angleR) / 2;
  }
}

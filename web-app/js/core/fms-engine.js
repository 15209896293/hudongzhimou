// FMS 评分引擎 — 七项功能性运动筛查评分
// 评分参考：Cook et al. (2006) Functional Movement Screen
// 阈值基于公开发表的 FMS 评分标准 + 生物力学常识设定

import {
  calculateAngle,
  calculateFromVertical,
  calculateKneeValgus,
  checkSymmetry,
  angleFromHorizontal,
  deviationFromLine,
} from './angle-utils.js';
import { POSE_LANDMARKS } from './pose-detector.js';

// 可见度阈值：关键点 visibility 低于此值视为不可信
const VIS_THRESHOLD = 0.5;

/** 取关键点，附带存在性保护 */
function pt(landmarks, idx) {
  const p = landmarks?.[idx];
  return p || { x: 0, y: 0, z: 0, visibility: 0 };
}

/** 批量检查关键点可见度，返回是否可信 */
function isVisible(landmarks, indices) {
  return indices.every((i) => (landmarks[i]?.visibility ?? 0) >= VIS_THRESHOLD);
}

/** 构造标准结果对象 */
function result(test, score, { issues = [], recommendations = [], metrics = {}, asymmetry = null, confidence = 'high' } = {}) {
  return { test, score, confidence, issues, recommendations, metrics, asymmetry };
}

// FMS 七项动作元数据
export const FMS_TESTS = [
  { key: 'deep_squat', name: '深蹲', en: 'Deep Squat', side: null },
  { key: 'hurdle_step', name: '跨栏步', en: 'Hurdle Step', side: 'bilateral' },
  { key: 'inline_lunge', name: '直线弓步', en: 'In-Line Lunge', side: 'bilateral' },
  { key: 'shoulder_mobility', name: '肩关节灵活性', en: 'Shoulder Mobility', side: 'bilateral' },
  { key: 'aslr', name: '主动直腿抬高', en: 'ASLR', side: 'bilateral' },
  { key: 'trunk_stability', name: '躯干稳定性俯卧撑', en: 'Trunk Stability Push-Up', side: null },
  { key: 'rotary_stability', name: '旋转稳定性', en: 'Rotary Stability', side: 'bilateral' },
];

export class FMSEngine {
  /**
   * 1. 深蹲评分
   * 评分要点：下蹲深度、躯干直立、足跟着地、膝追踪脚尖（无内扣）
   */
  scoreDeepSquat(landmarks) {
    const need = [11, 12, 23, 24, 25, 26, 27, 28, 31, 32];
    if (!isVisible(landmarks, need)) {
      return result('deep_squat', 0, { confidence: 'low', issues: [{ problem: '关键点不可见，请确保全身入镜' }] });
    }
    const ls = pt(landmarks, 11), rs = pt(landmarks, 12);
    const lh = pt(landmarks, 23), rh = pt(landmarks, 24);
    const lk = pt(landmarks, 25), rk = pt(landmarks, 26);
    const la = pt(landmarks, 27), ra = pt(landmarks, 28);
    const lf = pt(landmarks, 31), rf = pt(landmarks, 32);

    // 膝关节屈曲（取两侧均值）
    const kneeFlexL = calculateAngle(lh, lk, la);
    const kneeFlexR = calculateAngle(rh, rk, ra);
    const kneeFlex = (kneeFlexL + kneeFlexR) / 2;

    // 躯干前倾（肩中点→髋中点 与垂直线夹角）
    const shoulderMid = { x: (ls.x + rs.x) / 2, y: (ls.y + rs.y) / 2 };
    const hipMid = { x: (lh.x + rh.x) / 2, y: (lh.y + rh.y) / 2 };
    const trunkLean = calculateFromVertical(shoulderMid, hipMid);

    // 膝外翻
    const valgusL = calculateKneeValgus(lh, lk, la, 'left');
    const valgusR = calculateKneeValgus(rh, rk, ra, 'right');
    const valgusMax = Math.max(valgusL, valgusR);

    // 足跟着地（脚跟 y 应 ≥ 脚趾 y，即脚跟更低/同高；y 越大越靠下）
    const heelOffL = lf.y - la.y;  // 正值=脚趾比脚跟低（正常）
    const heelOffR = rf.y - ra.y;

    const issues = [];
    const recs = [];
    let score = 3;

    // 下蹲深度：膝屈曲越小越深。约 <110° 视为大腿低于水平
    if (kneeFlex > 130) { issues.push({ joint: 'knee', problem: '下蹲深度不足', severity: 'moderate', value: kneeFlex }); recs.push('继续下蹲至大腿与地面平行'); score = Math.min(score, 1); }
    else if (kneeFlex > 115) { issues.push({ joint: 'knee', problem: '下蹲略浅', severity: 'mild', value: kneeFlex }); if (score > 2) score = 2; }

    // 躯干前倾
    if (trunkLean > 45) { issues.push({ joint: 'trunk', problem: '躯干过度前倾', severity: 'moderate', value: trunkLean }); recs.push('保持挺胸，躯干更直立'); score = Math.min(score, 1); }
    else if (trunkLean > 30) { issues.push({ joint: 'trunk', problem: '躯干轻微前倾', severity: 'mild', value: trunkLean }); if (score > 2) score = 2; }

    // 膝内扣
    if (valgusMax > 15) { issues.push({ joint: 'knee', problem: '膝关节内扣', severity: valgusMax > 25 ? 'severe' : 'moderate', value: valgusMax }); recs.push('膝盖追踪脚尖方向，加强臀中肌'); score = Math.min(score, 1); }

    // 足跟离地
    if (heelOffL < -0.02 || heelOffR < -0.02) { issues.push({ joint: 'ankle', problem: '足跟离地', severity: 'moderate' }); recs.push('保持足跟着地，或垫高足跟测试踝关节背屈'); score = Math.min(score, 1); }

    if (issues.length === 0) recs.push('动作标准，保持');

    return result('deep_squat', score, {
      issues, recommendations: recs,
      metrics: { kneeFlexion: Math.round(kneeFlex), trunkLean: Math.round(trunkLean), kneeValgus: Math.round(valgusMax), kneeFlexL: Math.round(kneeFlexL), kneeFlexR: Math.round(kneeFlexR) },
    });
  }

  /**
   * 2. 跨栏步评分
   * 评分要点：抬腿侧髋膝踝对齐、骨盆水平、躯干稳定
   */
  scoreHurdleStep(landmarks) {
    const need = [11, 12, 23, 24, 25, 26, 27, 28];
    if (!isVisible(landmarks, need)) {
      return result('hurdle_step', 0, { confidence: 'low', issues: [{ problem: '关键点不可见' }] });
    }
    const lh = pt(landmarks, 23), rh = pt(landmarks, 24);
    const lk = pt(landmarks, 25), rk = pt(landmarks, 26);
    const la = pt(landmarks, 27), ra = pt(landmarks, 28);

    // 抬得较高的一侧作为评估侧（y 越小越高）
    const leftHigher = la.y < ra.y;
    const hip = leftHigher ? lh : rh;
    const knee = leftHigher ? lk : rk;
    const ankle = leftHigher ? la : ra;
    const side = leftHigher ? 'left' : 'right';

    // 髋膝踝垂直对齐（膝相对髋-踝连线的 x 偏移）
    const kneeOffset = Math.abs(knee.x - (hip.x + ankle.x) / 2);
    // 髋屈曲
    const hipFlex = calculateAngle(pt(landmarks, leftHigher ? 11 : 12), hip, knee);
    // 骨盆水平度
    const pelvicTilt = Math.abs(lh.y - rh.y);

    const issues = [], recs = [];
    let score = 3;
    if (kneeOffset > 0.05) { issues.push({ joint: 'knee', side, problem: '髋膝踝未对齐', severity: 'moderate', value: kneeOffset }); score = Math.min(score, 2); }
    if (pelvicTilt > 0.05) { issues.push({ joint: 'pelvis', problem: '骨盆倾斜', severity: pelvicTilt > 0.08 ? 'moderate' : 'mild', value: pelvicTilt }); recs.push('保持骨盆水平，避免代偿'); score = Math.min(score, 2); }
    if (issues.length === 0) recs.push('抬腿稳定，对齐良好');

    return result('hurdle_step', score, {
      issues, recommendations: recs, asymmetry: { side, delta: 0 },
      metrics: { hipFlexion: Math.round(hipFlex), kneeOffset: +kneeOffset.toFixed(3), pelvicTilt: +pelvicTilt.toFixed(3) },
    });
  }

  /**
   * 3. 直线弓步评分
   * 评分要点：前膝在踝上方、后腿伸直、躯干稳定
   */
  scoreInlineLunge(landmarks) {
    const need = [23, 24, 25, 26, 27, 28];
    if (!isVisible(landmarks, need)) {
      return result('inline_lunge', 0, { confidence: 'low', issues: [{ problem: '关键点不可见' }] });
    }
    const lh = pt(landmarks, 23), rh = pt(landmarks, 24);
    const lk = pt(landmarks, 25), rk = pt(landmarks, 26);
    const la = pt(landmarks, 27), ra = pt(landmarks, 28);

    // 用膝-踝水平对齐判断：前膝应在前踝正上方
    const kneeAnkleGapL = Math.abs(lk.x - la.x);
    const kneeAnkleGapR = Math.abs(rk.x - ra.x);
    const leftFront = kneeAnkleGapL < kneeAnkleGapR; // 前腿膝踝更接近垂直对齐
    const fKnee = leftFront ? lk : rk;
    const fAnkle = leftFront ? la : ra;
    const bKnee = leftFront ? rk : lk;
    const bHip = leftFront ? rh : lh;
    const side = leftFront ? 'left' : 'right';

    // 前膝-踝对齐
    const frontAlign = Math.abs(fKnee.x - fAnkle.x);
    // 后腿伸展度（髋-膝-踝角度，越接近 180 越直）
    const rearExt = calculateAngle(bHip, bKnee, leftFront ? ra : la);
    // 躯干稳定（双肩中点-双髋中点 倾斜）
    const shoulderMid = { x: (pt(landmarks, 11).x + pt(landmarks, 12).x) / 2, y: (pt(landmarks, 11).y + pt(landmarks, 12).y) / 2 };
    const hipMid = { x: (lh.x + rh.x) / 2, y: (lh.y + rh.y) / 2 };
    const trunkLean = calculateFromVertical(shoulderMid, hipMid);

    const issues = [], recs = [];
    let score = 3;
    if (frontAlign > 0.04) { issues.push({ joint: 'knee', side, problem: '前膝偏离踝关节', severity: 'moderate', value: frontAlign }); score = Math.min(score, 2); }
    if (rearExt < 150) { issues.push({ joint: 'knee', problem: '后腿未伸直', severity: 'mild', value: rearExt }); recs.push('后腿充分伸展'); score = Math.min(score, 2); }
    if (trunkLean > 30) { issues.push({ joint: 'trunk', problem: '躯干倾斜', severity: 'mild', value: trunkLean }); score = Math.min(score, 2); }
    if (issues.length === 0) recs.push('弓步稳定，对齐良好');

    return result('inline_lunge', score, {
      issues, recommendations: recs, asymmetry: { side, delta: 0 },
      metrics: { frontKneeAlign: +frontAlign.toFixed(3), rearExtension: Math.round(rearExt), trunkLean: Math.round(trunkLean) },
    });
  }

  /**
   * 4. 肩关节灵活性评分
   * 注意：FMS 原版双手在背后，MediaPipe 正面视角难以精确捕捉。
   * 降级方案：评估双侧肩关节上举活动度（腕相对肩的高度）+ 左右对称性
   */
  scoreShoulderMobility(landmarks) {
    const need = [11, 12, 15, 16];
    if (!isVisible(landmarks, need)) {
      return result('shoulder_mobility', 0, { confidence: 'low', issues: [{ problem: '关键点不可见' }] });
    }
    const ls = pt(landmarks, 11), rs = pt(landmarks, 12);
    const lw = pt(landmarks, 15), rw = pt(landmarks, 16);

    // 腕相对肩的上举高度（y 越小越高）。负值=腕高于肩
    const raiseL = ls.y - lw.y;
    const raiseR = rs.y - rw.y;
    const raise = (raiseL + raiseR) / 2;
    const asym = Math.abs(raiseL - raiseR);

    const issues = [], recs = [];
    let score = 3;
    if (raise < 0.05) { issues.push({ joint: 'shoulder', problem: '肩关节上举活动度受限', severity: 'moderate', value: raise }); recs.push('加强肩关节灵活性训练'); score = Math.min(score, 1); }
    else if (raise < 0.12) { issues.push({ joint: 'shoulder', problem: '肩关节活动度稍欠', severity: 'mild', value: raise }); score = Math.min(score, 2); }
    if (asym > 0.04) { issues.push({ joint: 'shoulder', problem: '左右肩活动度不对称', severity: 'mild', value: asym }); recs.push('针对活动度较差一侧加强训练'); }
    if (issues.length === 0) recs.push('肩关节灵活性良好');

    return result('shoulder_mobility', score, {
      issues, recommendations: recs, asymmetry: asym > 0.04 ? { side: raiseL < raiseR ? 'left' : 'right', delta: +asym.toFixed(3) } : null,
      metrics: { raiseHeight: +raise.toFixed(3), raiseL: +raiseL.toFixed(3), raiseR: +raiseR.toFixed(3), asymmetry: +asym.toFixed(3) },
    });
  }

  /**
   * 5. 主动直腿抬高（ASLR）评分
   * 评分要点：抬高腿与水平面夹角，参照对侧膝关节/髋关节高度
   */
  scoreASLR(landmarks) {
    const need = [23, 24, 25, 26, 27, 28];
    if (!isVisible(landmarks, need)) {
      return result('aslr', 0, { confidence: 'low', issues: [{ problem: '关键点不可见' }] });
    }
    const lh = pt(landmarks, 23), rh = pt(landmarks, 24);
    const lk = pt(landmarks, 25), rk = pt(landmarks, 26);
    const la = pt(landmarks, 27), ra = pt(landmarks, 28);

    // 抬高侧：踝 y 较小（更高）的一侧
    const leftRaised = la.y < ra.y;
    const hip = leftRaised ? lh : rh;
    const ankle = leftRaised ? la : ra;
    const oppKnee = leftRaised ? rk : lk;
    const oppHip = leftRaised ? rh : lh;
    const side = leftRaised ? 'left' : 'right';

    // 抬高腿与水平线夹角（髋→踝，y 差越大越接近垂直）
    const legAngle = angleFromHorizontal(hip, ankle); // 0=水平，90=垂直
    // 抬高踝相对对侧膝/髋高度
    const ankleVsKnee = oppKnee.y - ankle.y; // 正=踝高于对侧膝
    const ankleVsHip = oppHip.y - ankle.y;

    const issues = [], recs = [];
    let score = 3;
    if (ankleVsKnee > 0) { score = 3; } // 踝高于对侧膝 → 3分
    else if (ankleVsHip > 0) { score = 2; issues.push({ joint: 'hamstring', side, problem: '腘绳肌柔韧性一般', value: legAngle }); recs.push('加强腘绳肌拉伸'); }
    else { score = 1; issues.push({ joint: 'hamstring', side, problem: '抬腿高度不足', severity: 'moderate', value: legAngle }); recs.push('重点拉伸腘绳肌与小腿'); }
    if (issues.length === 0) recs.push('抬腿高度良好');

    return result('aslr', score, {
      issues, recommendations: recs, asymmetry: { side, delta: 0 },
      metrics: { legRaiseAngle: Math.round(legAngle), ankleVsOppKnee: +ankleVsKnee.toFixed(3) },
    });
  }

  /**
   * 6. 躯干稳定性俯卧撑评分
   * 评分要点：肩-髋-膝成直线，无塌腰/翘臀
   */
  scoreTrunkStability(landmarks) {
    const need = [11, 12, 23, 24, 25, 26];
    if (!isVisible(landmarks, need)) {
      return result('trunk_stability', 0, { confidence: 'low', issues: [{ problem: '关键点不可见' }] });
    }
    const ls = pt(landmarks, 11), rs = pt(landmarks, 12);
    const lh = pt(landmarks, 23), rh = pt(landmarks, 24);
    const lk = pt(landmarks, 25), rk = pt(landmarks, 26);

    const shoulderMid = { x: (ls.x + rs.x) / 2, y: (ls.y + rs.y) / 2 };
    const hipMid = { x: (lh.x + rh.x) / 2, y: (lh.y + rh.y) / 2 };
    const kneeMid = { x: (lk.x + rk.x) / 2, y: (lk.y + rk.y) / 2 };

    // 髋偏离肩-膝直线的程度
    const sag = deviationFromLine(shoulderMid, hipMid, kneeMid);
    // 髋相对肩-膝连线方向：下凹=塌腰，上凸=翘臀
    const cross = (hipMid.x - shoulderMid.x) * (kneeMid.y - shoulderMid.y) - (hipMid.y - shoulderMid.y) * (kneeMid.x - shoulderMid.x);
    const sagType = cross > 0 ? '塌腰' : '翘臀';

    const issues = [], recs = [];
    let score = 3;
    if (sag > 0.04) { issues.push({ joint: 'trunk', problem: `${sagType}，躯干未成直线`, severity: sag > 0.07 ? 'moderate' : 'mild', value: sag }); recs.push('收紧核心，保持脊柱中立位'); score = Math.min(score, sag > 0.07 ? 1 : 2); }
    if (issues.length === 0) recs.push('躯干稳定，身体成直线');

    return result('trunk_stability', score, {
      issues, recommendations: recs,
      metrics: { trunkSag: +sag.toFixed(3), sagType },
    });
  }

  /**
   * 7. 旋转稳定性评分
   * 注意：FMS 原版为四点支撑同侧手脚伸展，正面视角评估受限。
   * 降级方案：评估站立躯干旋转时的肩部水平对称性 + 髋膝稳定性
   */
  scoreRotaryStability(landmarks) {
    const need = [11, 12, 23, 24, 25, 26];
    if (!isVisible(landmarks, need)) {
      return result('rotary_stability', 0, { confidence: 'low', issues: [{ problem: '关键点不可见' }] });
    }
    const ls = pt(landmarks, 11), rs = pt(landmarks, 12);
    const lh = pt(landmarks, 23), rh = pt(landmarks, 24);
    const lk = pt(landmarks, 25), rk = pt(landmarks, 26);

    // 肩连线与水平线夹角（反映躯干旋转）
    const shoulderTilt = angleFromHorizontal(ls, rs);
    const hipTilt = angleFromHorizontal(lh, rh);
    // 膝关节左右对称（x 相对髋的偏移应对称）
    const kneeAsym = Math.abs((lk.x - lh.x) - (rk.x - rh.x));

    const issues = [], recs = [];
    let score = 3;
    if (shoulderTilt > 25) { issues.push({ joint: 'spine', problem: '躯干旋转过度', severity: 'mild', value: shoulderTilt }); score = Math.min(score, 2); }
    if (hipTilt > 15) { issues.push({ joint: 'pelvis', problem: '骨盆旋转不稳', severity: 'mild', value: hipTilt }); recs.push('保持骨盆稳定'); score = Math.min(score, 2); }
    if (kneeAsym > 0.05) { issues.push({ joint: 'knee', problem: '下肢左右不对称', severity: 'mild', value: kneeAsym }); score = Math.min(score, 2); }
    if (issues.length === 0) recs.push('旋转稳定性良好');

    return result('rotary_stability', score, {
      issues, recommendations: recs, asymmetry: kneeAsym > 0.05 ? { side: 'bilateral', delta: +kneeAsym.toFixed(3) } : null,
      metrics: { shoulderTilt: Math.round(shoulderTilt), hipTilt: Math.round(hipTilt), kneeAsymmetry: +kneeAsym.toFixed(3) },
    });
  }

  /** 汇总总分 */
  getTotalScore(scores) {
    return Object.values(scores).reduce((sum, s) => sum + (s?.score || 0), 0);
  }

  /**
   * 风险等级判定
   * @param {number} totalScore - 0-21
   * @param {Array} asymmetries - 不对称标记列表
   * @returns {{level:'low'|'moderate'|'high', label:string}}
   */
  getRiskLevel(totalScore, asymmetries = []) {
    if (totalScore < 14 || asymmetries.length > 0) {
      return { level: 'high', label: '受伤风险高' };
    }
    if (totalScore < 18) {
      return { level: 'moderate', label: '受伤风险中等' };
    }
    return { level: 'low', label: '受伤风险低' };
  }
}

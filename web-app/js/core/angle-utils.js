// 关节角度计算工具（纯数学，无外部依赖）

import { radToDeg } from '../utils/helpers.js';

/**
 * 计算三点之间的角度（度数）
 * @param {object} a - 起点 {x, y, z?}
 * @param {object} b - 顶点 {x, y, z?}
 * @param {object} c - 终点 {x, y, z?}
 * @returns {number} 0-180 度，顶点处的夹角
 */
export function calculateAngle(a, b, c) {
  // 向量 BA 与 BC
  const v1 = { x: a.x - b.x, y: a.y - b.y, z: (a.z || 0) - (b.z || 0) };
  const v2 = { x: c.x - b.x, y: c.y - b.y, z: (c.z || 0) - (b.z || 0) };

  // 优先用 2D（x,y），z 仅在两侧 z 均有意义时纳入
  const useZ = (a.z != null && b.z != null && c.z != null);
  const dot = useZ
    ? v1.x * v2.x + v1.y * v2.y + v1.z * v2.z
    : v1.x * v2.x + v1.y * v2.y;
  const mag1 = useZ
    ? Math.sqrt(v1.x ** 2 + v1.y ** 2 + v1.z ** 2)
    : Math.hypot(v1.x, v1.y);
  const mag2 = useZ
    ? Math.sqrt(v2.x ** 2 + v2.y ** 2 + v2.z ** 2)
    : Math.hypot(v2.x, v2.y);

  if (mag1 < 1e-6 || mag2 < 1e-6) return 0;
  const cos = Math.max(-1, Math.min(1, dot / (mag1 * mag2)));
  return radToDeg(Math.acos(cos));
}

/**
 * 计算线段（upper→lower）与垂直方向的夹角
 * 用于躯干前倾角度检测：shoulder→hip 与垂直线的偏离
 * @param {object} upper - 上端点（如肩）
 * @param {object} lower - 下端点（如髋）
 * @returns {number} 与垂直线的夹角（度），0 = 完全直立
 */
export function calculateFromVertical(upper, lower) {
  const seg = { x: lower.x - upper.x, y: lower.y - upper.y };
  // 垂直方向 (0, 1)（图像坐标 y 向下）
  const cross = seg.x * 1 - seg.y * 0; // = seg.x
  const dot = seg.y;
  const ang = radToDeg(Math.atan2(Math.abs(cross), dot));
  return Math.abs(ang) > 90 ? 180 - Math.abs(ang) : ang;
}

/**
 * 计算左右对称性（比较两侧对应关键点的 y 坐标差）
 * @param {object} leftKeypoint - 左侧关键点
 * @param {object} rightKeypoint - 右侧关键点
 * @param {number} threshold - 判定不对称的阈值（归一化坐标）
 * @returns {{ isSymmetric: boolean, offset: number }}
 */
export function checkSymmetry(leftKeypoint, rightKeypoint, threshold = 0.05) {
  if (!leftKeypoint || !rightKeypoint) {
    return { isSymmetric: true, offset: 0 };
  }
  const offset = Math.abs(leftKeypoint.y - rightKeypoint.y);
  return { isSymmetric: offset <= threshold, offset };
}

/**
 * 计算膝关节外翻角度（膝关节相对髋-踝连线的偏移）
 * @param {object} hip - 髋关节 {x, y}
 * @param {object} knee - 膝关节 {x, y}
 * @param {object} ankle - 踝关节 {x, y}
 * @param {'left'|'right'} [side] - 肢体侧别，用于统一正负号
 * @returns {number} 外翻角度（正值=外翻/内扣，负值=内翻/外翻）
 *
 * 约定：side='left' 时不翻转，side='right' 时翻转符号，
 * 使得"正值=膝内扣（valgus）"在两侧一致。
 * 注意：MediaPipe 处理原始未镜像帧，CSS 仅镜像显示，数学计算无需考虑镜像。
 */
export function calculateKneeValgus(hip, knee, ankle, side) {
  // 髋→踝 参考向量
  const refX = ankle.x - hip.x;
  const refY = ankle.y - hip.y;
  // 髋→膝 向量
  const knX = knee.x - hip.x;
  const knY = knee.y - hip.y;

  const cross = refX * knY - refY * knX; // 叉积，符号反映偏向
  const dot = refX * knX + refY * knY;
  let ang = radToDeg(Math.atan2(cross, dot));

  // 右侧翻转符号，使正值统一表示外翻（膝内扣）
  if (side === 'right') ang = -ang;
  return ang;
}

/**
 * 计算一条线段与水平线的夹角（用于抬腿角度等）
 * @param {object} a - 线段端点 A
 * @param {object} b - 线段端点 B
 * @returns {number} 0-180 度，0 = 水平
 */
export function angleFromHorizontal(a, b) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  return radToDeg(Math.atan2(Math.abs(dy), Math.abs(dx) || 1e-6));
}

/**
 * 计算三点共线的偏离度（用于俯卧撑身体是否成直线）
 * 返回膝关节（顶点 b）到 ac 直线的垂直距离（归一化坐标）
 * @param {object} a - 肩
 * @param {object} b - 髋（偏离点）
 * @param {object} c - 膝
 * @returns {number} 偏离距离（归一化），0 = 完全共线
 */
export function deviationFromLine(a, b, c) {
  const acx = c.x - a.x;
  const acy = c.y - a.y;
  const len = Math.hypot(acx, acy) || 1e-6;
  // b 到 ac 直线的垂直距离（叉积 / |ac|）
  return Math.abs((b.x - a.x) * acy - (b.y - a.y) * acx) / len;
}

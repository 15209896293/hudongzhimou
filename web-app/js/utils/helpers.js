// 通用工具函数

/** clamp 值到 [min, max] */
export function clamp(v, min, max) {
  return Math.min(Math.max(v, min), max);
}

/** 角度转弧度 */
export function degToRad(deg) {
  return (deg * Math.PI) / 180;
}

/** 弧度转角度 */
export function radToDeg(rad) {
  return (rad * 180) / Math.PI;
}

/** 0-1 归一化坐标转像素坐标 */
export function toPixel(point, width, height) {
  return {
    x: point.x * width,
    y: point.y * height,
    z: (point.z || 0) * width,
    visibility: point.visibility ?? 1,
  };
}

/** 两点间欧氏距离（2D） */
export function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

/** 平滑滤波器：指数加权移动平均，抑制骨架抖动 */
export class SmoothFilter {
  constructor(alpha = 0.5) {
    this.alpha = alpha;
    this.state = null;
  }
  reset() {
    this.state = null;
  }
  update(value) {
    if (this.state === null) {
      this.state = value;
      return value;
    }
    this.state = this.state.map((p, i) => ({
      x: p.x * (1 - this.alpha) + value[i].x * this.alpha,
      y: p.y * (1 - this.alpha) + value[i].y * this.alpha,
      z: (p.z || 0) * (1 - this.alpha) + (value[i].z || 0) * this.alpha,
      visibility: value[i].visibility ?? p.visibility ?? 1,
    }));
    return this.state;
  }
}

/** 节流：limit 周期内只执行一次 */
export function throttle(fn, intervalMs) {
  let last = 0;
  let timer = null;
  return function (...args) {
    const now = performance.now();
    const remaining = intervalMs - (now - last);
    if (remaining <= 0) {
      if (timer) { clearTimeout(timer); timer = null; }
      last = now;
      fn.apply(this, args);
    } else if (!timer) {
      timer = setTimeout(() => {
        last = performance.now();
        timer = null;
        fn.apply(this, args);
      }, remaining);
    }
  };
}

/** 格式化日期为 YYYY-MM-DD */
export function formatDate(date) {
  const d = date instanceof Date ? date : new Date(date);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** 安全 JSON 解析，失败返回 fallback */
export function safeJSON(text, fallback = null) {
  try {
    return JSON.parse(text);
  } catch {
    try {
      const m = String(text).match(/\{[\s\S]*\}/);
      if (m) return JSON.parse(m[0]);
    } catch { /* noop */ }
    return fallback;
  }
}

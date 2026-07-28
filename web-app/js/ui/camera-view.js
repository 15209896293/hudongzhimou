// 骨架渲染
// 职责单一：在 Canvas 上画骨架线 + 关键点 + 风险脉冲
// 视频画面由 <video> 元素直接显示（CSS 负责镜像），Canvas 是透明层叠在上面

export const POSE_CONNECTIONS = {
  torso: [[11, 12], [11, 23], [12, 24], [23, 24]],
  leftArm: [[11, 13], [13, 15]],
  rightArm: [[12, 14], [14, 16]],
  leftLeg: [[23, 25], [25, 27], [27, 31]],
  rightLeg: [[24, 26], [26, 28], [28, 32]],
  face: [[0, 11], [0, 12]],
};

export const COLORS = {
  torso: '#FF9F0A',
  leftArm: '#30D158',
  rightArm: '#64D2FF',
  leftLeg: '#BF5AF2',
  rightLeg: '#FFD60A',
  face: '#FF375F',
  joint: '#FFFFFF',
  risk: '#FF453A',
};

const JOINT_INDEX = {
  knee: { left: 25, right: 26 },
  pelvis: { left: 23, right: 24, both: [23, 24] },
  trunk: [11, 12, 23, 24],
  spine: [11, 12, 23, 24],
  shoulder: { left: 11, right: 12 },
  hamstring: { left: 25, right: 26 },
};

export function riskLandmarkIndices(alerts) {
  const set = new Set();
  for (const a of alerts || []) {
    const map = JOINT_INDEX[a.joint];
    if (!map) continue;
    if (Array.isArray(map)) { map.forEach((i) => set.add(i)); continue; }
    if (a.side && map[a.side] != null) { set.add(map[a.side]); continue; }
    if (map.both) { map.both.forEach((i) => set.add(i)); continue; }
    Object.values(map).forEach((v) => { if (typeof v === 'number') set.add(v); });
  }
  return set;
}

export class CameraView {
  constructor(video, canvas, opts = {}) {
    this.video = video;
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.fpsEl = document.getElementById('fps-display');
    this.riskEl = document.getElementById('risk-indicator');
    this._pulse = 0;
    this._mirror = true;
  }

  /** 同步 Canvas 绘制缓冲区到视频分辨率 */
  syncSize() {
    const w = this.video.videoWidth || 640;
    const h = this.video.videoHeight || 480;
    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w;
      this.canvas.height = h;
    }
  }

  /**
   * 渲染骨架（output 为 null 时只清屏）
   */
  render(output) {
    this.syncSize();
    const w = this.canvas.width;
    const h = this.canvas.height;

    // 清屏（透明 → 露出下方 video 画面）
    this.ctx.clearRect(0, 0, w, h);

    const { landmarks, safety, fps } = output || {};
    if (!landmarks || landmarks.length < 33) {
      this._updateRiskIndicator(null);
      return;
    }

    // 画骨架
    this._drawSkeleton(landmarks, safety, w, h);

    // FPS
    if (this.fpsEl && fps != null) {
      this.fpsEl.style.display = 'block';
      this.fpsEl.textContent = `FPS: ${fps}`;
    }

    this._updateRiskIndicator(safety?.level);
  }

  // ── 骨架绘制 ──

  _drawSkeleton(landmarks, safety, w, h) {
    const riskSet = riskLandmarkIndices(safety?.alerts);
    this._pulse = (this._pulse + 0.08) % (Math.PI * 2);

    // 连线
    this.ctx.lineWidth = 4;
    this.ctx.lineCap = 'round';
    for (const [group, conns] of Object.entries(POSE_CONNECTIONS)) {
      this.ctx.strokeStyle = COLORS[group] || '#FFF';
      for (const [a, b] of conns) {
        const pa = landmarks[a], pb = landmarks[b];
        if (!pa || !pb || (pa.visibility ?? 0) < 0.3 || (pb.visibility ?? 0) < 0.3) continue;
        this.ctx.beginPath();
        this.ctx.moveTo(pa.x * w, pa.y * h);
        this.ctx.lineTo(pb.x * w, pb.y * h);
        this.ctx.stroke();
      }
    }

    // 关键点
    for (let i = 0; i < landmarks.length; i++) {
      const p = landmarks[i];
      if (!p || (p.visibility ?? 0) < 0.3) continue;
      const px = p.x * w, py = p.y * h;
      const isRisk = riskSet.has(i);
      const r = isRisk ? 7 + Math.sin(this._pulse) * 2 : 6;

      if (isRisk) {
        this.ctx.beginPath();
        this.ctx.arc(px, py, r + 5, 0, Math.PI * 2);
        this.ctx.fillStyle = 'rgba(255,69,58,0.25)';
        this.ctx.fill();
      }

      this.ctx.beginPath();
      this.ctx.arc(px, py, r, 0, Math.PI * 2);
      this.ctx.fillStyle = COLORS.joint;
      this.ctx.fill();
      this.ctx.lineWidth = 2;
      this.ctx.strokeStyle = isRisk ? COLORS.risk : this._jointColor(i);
      this.ctx.stroke();
    }
  }

  _jointColor(i) {
    if ([11, 13, 15, 23, 25, 27, 31].includes(i)) return COLORS.leftArm;
    if ([12, 14, 16, 24, 26, 28, 32].includes(i)) return COLORS.rightArm;
    return COLORS.torso;
  }

  _updateRiskIndicator(level) {
    if (!this.riskEl) return;
    this.riskEl.classList.remove('safe', 'warning', 'danger', 'show');
    if (!level || level === 'safe') {
      this.riskEl.textContent = '安全';
      this.riskEl.classList.add('safe', 'show');
    } else {
      this.riskEl.textContent = level === 'danger' ? '危险' : '警告';
      this.riskEl.classList.add(level, 'show');
    }
  }

  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (this.riskEl) this.riskEl.classList.remove('show');
  }
}

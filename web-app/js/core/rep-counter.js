// 动作计数器 — 状态机 + 滑动滤波
// 从桌面版 exercise_counters.py 迁移，适配 MediaPipe 33 点

import { calculateAngle } from './angle-utils.js';

export class RepCounter {
  /**
   * @param {object} config - EXERCISES[key].counter
   * { keypoints, downAngle, upAngle, isLegExercise, isStatic, minRepTime }
   */
  constructor(config) {
    this.config = config;
    this.stage = 'up';
    this.count = 0;
    this.lastRepTime = 0;
    this.smoothWindow = [];
    this.lastAngle = 0;
  }

  /**
   * 处理一帧
   * @param {Array} landmarks - MediaPipe 33 点
   * @returns {{ count, stage, angle, repCompleted: boolean }}
   */
  update(landmarks) {
    if (this.config.isStatic) {
      return { count: 0, stage: 'hold', angle: 0, repCompleted: false };
    }

    const { left, right } = this.config.keypoints;
    const angleL = calculateAngle(landmarks[left[0]], landmarks[left[1]], landmarks[left[2]]);
    const angleR = calculateAngle(landmarks[right[0]], landmarks[right[1]], landmarks[right[2]]);
    const angle = (angleL + angleR) / 2;

    // 5 帧滑动均值滤波
    this.smoothWindow.push(angle);
    if (this.smoothWindow.length > 5) this.smoothWindow.shift();
    const smoothAngle = this.smoothWindow.reduce((a, b) => a + b, 0) / this.smoothWindow.length;
    this.lastAngle = smoothAngle;

    // 判断计数方向：down < up = 深蹲型（角度小=下），down > up = 弯举型（角度大=起点）
    const isSquatType = this.config.downAngle < this.config.upAngle;
    const now = performance.now();

    if (isSquatType) {
      // 深蹲型：角度 < downAngle = 下，角度 > upAngle = 上
      if (smoothAngle < this.config.downAngle) {
        this.stage = 'down';
      } else if (smoothAngle > this.config.upAngle && this.stage === 'down') {
        if (now - this.lastRepTime > this.config.minRepTime) {
          this.count++;
          this.lastRepTime = now;
          this.stage = 'up';
          return { count: this.count, stage: 'up', angle: smoothAngle, repCompleted: true };
        }
      }
    } else {
      // 弯举型：角度 > downAngle = 起点(下)，角度 < upAngle = 终点(上)
      if (smoothAngle > this.config.downAngle) {
        this.stage = 'down';
      } else if (smoothAngle < this.config.upAngle && this.stage === 'down') {
        if (now - this.lastRepTime > this.config.minRepTime) {
          this.count++;
          this.lastRepTime = now;
          this.stage = 'up';
          return { count: this.count, stage: 'up', angle: smoothAngle, repCompleted: true };
        }
      }
    }

    return { count: this.count, stage: this.stage, angle: smoothAngle, repCompleted: false };
  }

  reset() {
    this.count = 0;
    this.stage = 'up';
    this.smoothWindow = [];
    this.lastAngle = 0;
    this.lastRepTime = 0;
  }
}

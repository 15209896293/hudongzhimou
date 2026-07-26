// 四阶段处理管线：推理 → FMS 分析 → 防伤检测 → 渲染数据准备

import { PoseDetector } from './pose-detector.js';
import { FMSEngine } from './fms-engine.js';
import { SafetyChecker } from './safety-checker.js';
import { SmoothFilter, clamp } from '../utils/helpers.js';

export class FramePipeline {
  constructor(opts = {}) {
    this.detector = new PoseDetector();
    this.fmsEngine = new FMSEngine();
    this.safetyChecker = new SafetyChecker();
    this.currentTest = 'deep_squat';
    this.onUpdate = null;

    // 骨架平滑滤波（抑制抖动）
    this.smoother = new SmoothFilter(opts.smoothAlpha ?? 0.4);

    // FPS 统计
    this._frameCount = 0;
    this._fpsTimer = performance.now();
    this.fps = 0;

    // 帧率上限控制
    this.maxFps = opts.maxFps ?? 60;
    this._lastProcessTs = 0;
  }

  /** 初始化：加载 MediaPipe 模型 */
  async init(opts, onProgress) {
    await this.detector.init(opts, onProgress);
  }

  /** 切换当前 FMS 测试项目 */
  setTest(testName) {
    if (testName !== this.currentTest) {
      this.currentTest = testName;
      this.smoother.reset();
    }
  }

  /** 切换模型精度（标记需重新 init） */
  setVariant(variant) {
    return this.detector.setVariant(variant);
  }

  get needsReinit() {
    return this.detector.landmarker === null;
  }

  /**
   * 处理单帧
   * @param {HTMLVideoElement} video
   * @returns {object|null} { landmarks, fms, safety, fps, timestamp }
   */
  process(video) {
    // 帧率上限节流
    const now = performance.now();
    const minInterval = 1000 / this.maxFps;
    if (now - this._lastProcessTs < minInterval) return null;
    this._lastProcessTs = now;

    // 阶段 1：推理
    const rawLandmarks = this.detector.detect(video);
    if (!rawLandmarks) return null;

    // 平滑骨架
    const landmarks = this.smoother.update(rawLandmarks);

    // 阶段 2：FMS 分析
    const fmsResult = this.scoreByTest(this.currentTest, landmarks);

    // 阶段 3：防伤检测
    const safetyResult = this.safetyChecker.check(landmarks);

    // FPS 计算
    this._frameCount++;
    const elapsed = now - this._fpsTimer;
    if (elapsed >= 500) {
      this.fps = Math.round((this._frameCount * 1000) / elapsed);
      this._frameCount = 0;
      this._fpsTimer = now;
    }

    // 阶段 4：渲染数据
    const output = {
      landmarks,
      fms: fmsResult,
      safety: safetyResult,
      fps: this.fps,
      test: this.currentTest,
      timestamp: now,
    };

    if (this.onUpdate) this.onUpdate(output);
    return output;
  }

  /** 按测试名分发评分 */
  scoreByTest(test, landmarks) {
    const map = {
      deep_squat: this.fmsEngine.scoreDeepSquat,
      hurdle_step: this.fmsEngine.scoreHurdleStep,
      inline_lunge: this.fmsEngine.scoreInlineLunge,
      shoulder_mobility: this.fmsEngine.scoreShoulderMobility,
      aslr: this.fmsEngine.scoreASLR,
      trunk_stability: this.fmsEngine.scoreTrunkStability,
      rotary_stability: this.fmsEngine.scoreRotaryStability,
    };
    const fn = map[test];
    return fn ? fn.call(this.fmsEngine, landmarks) : null;
  }

  resetSmoother() {
    this.smoother.reset();
  }

  close() {
    this.detector.close();
  }
}

// 四阶段处理管线：推理 → FMS 分析 → 防伤检测 → 渲染数据准备

import { PoseDetector } from './pose-detector.js';
import { FMSEngine } from './fms-engine.js';
import { SafetyChecker } from './safety-checker.js';
import { RepCounter } from './rep-counter.js';
import { QualityScorer } from './quality-scorer.js';
import { EXERCISES, applyUserProfile } from './exercise-library.js';
import { SmoothFilter, clamp } from '../utils/helpers.js';
import { storage } from '../utils/storage.js';

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

    // 训练模式状态
    this.mode = 'fms';          // 'fms' | 'training'
    this.exerciseKey = null;
    this.exerciseConfig = null;
    this.repCounter = null;
    this.qualityScorer = null;
    this.adjustedThresholds = null;
    this._qualitySkipFrames = 0; // 质量评分跳帧计数
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

  /** 切换模式：'fms' 或 'training' */
  setMode(mode) {
    if (this.mode === mode) return;
    this.mode = mode;
    this.smoother.reset();
  }

  /** 设置训练动作 */
  setExercise(exerciseKey) {
    if (this.exerciseKey === exerciseKey && this.repCounter) return;
    this.exerciseKey = exerciseKey;
    this.exerciseConfig = EXERCISES[exerciseKey];
    if (!this.exerciseConfig) return;

    this.repCounter = new RepCounter(this.exerciseConfig.counter);
    this.qualityScorer = new QualityScorer(this.exerciseConfig.quality);

    // 从用户档案计算个性化安全阈值
    const profile = storage.get('profile', {});
    this.adjustedThresholds = applyUserProfile(this.exerciseConfig.safety, profile);
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

    // FPS 计算（两种模式共用）
    this._frameCount++;
    const elapsed = now - this._fpsTimer;
    if (elapsed >= 500) {
      this.fps = Math.round((this._frameCount * 1000) / elapsed);
      this._frameCount = 0;
      this._fpsTimer = now;
    }

    // 阶段 2-4：按模式分发
    const output = this.mode === 'training'
      ? this._processTraining(landmarks, now)
      : this._processFMS(landmarks, now);

    if (this.onUpdate) this.onUpdate(output);
    return output;
  }

  /** FMS 筛查模式处理 */
  _processFMS(landmarks, now) {
    const fmsResult = this.scoreByTest(this.currentTest, landmarks);
    const safetyResult = this.safetyChecker.check(landmarks);
    return {
      landmarks,
      mode: 'fms',
      fms: fmsResult,
      safety: safetyResult,
      fps: this.fps,
      test: this.currentTest,
      timestamp: now,
    };
  }

  /** 训练模式处理：计数 → 质量评分(每3帧) → 动作专属安全检测 */
  _processTraining(landmarks, now) {
    // 计数
    const repResult = this.repCounter
      ? this.repCounter.update(landmarks)
      : { count: 0, stage: 'up', angle: 0, repCompleted: false };

    // 质量评分（每 3 帧计算一次，降低开销）
    let quality = null;
    if (this.qualityScorer && ++this._qualitySkipFrames % 3 === 0) {
      quality = this.qualityScorer.score(landmarks);
    }

    // 安全检测（动作专属阈值 + 个性化 + 通用规则）
    const safety = this.exerciseConfig
      ? this.safetyChecker.checkForExercise(landmarks, this.exerciseConfig, this.adjustedThresholds)
      : this.safetyChecker.check(landmarks);

    return {
      landmarks,
      mode: 'training',
      rep: repResult,
      quality,
      safety,
      exercise: this.exerciseKey,
      fps: this.fps,
      timestamp: now,
    };
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

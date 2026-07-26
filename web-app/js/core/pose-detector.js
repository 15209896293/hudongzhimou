// MediaPipe Pose Landmarker 封装
// 官方文档：https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/web_js

import { FilesetResolver, PoseLandmarker } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/vision_bundle.mjs';

// MediaPipe Pose 33 关键点索引
export const POSE_LANDMARKS = {
  NOSE: 0,
  LEFT_EYE_INNER: 1, LEFT_EYE: 2, LEFT_EYE_OUTER: 3,
  RIGHT_EYE_INNER: 4, RIGHT_EYE: 5, RIGHT_EYE_OUTER: 6,
  LEFT_EAR: 7, RIGHT_EAR: 8,
  MOUTH_LEFT: 9, MOUTH_RIGHT: 10,
  LEFT_SHOULDER: 11, RIGHT_SHOULDER: 12,
  LEFT_ELBOW: 13, RIGHT_ELBOW: 14,
  LEFT_WRIST: 15, RIGHT_WRIST: 16,
  LEFT_PINKY: 17, RIGHT_PINKY: 18,
  LEFT_INDEX: 19, RIGHT_INDEX: 20,
  LEFT_THUMB: 21, RIGHT_THUMB: 22,
  LEFT_HIP: 23, RIGHT_HIP: 24,
  LEFT_KNEE: 25, RIGHT_KNEE: 26,
  LEFT_ANKLE: 27, RIGHT_ANKLE: 28,
  LEFT_HEEL: 29, RIGHT_HEEL: 30,
  LEFT_FOOT_INDEX: 31, RIGHT_FOOT_INDEX: 32,
};

// 模型 URL 映射（精度可选）
const MODEL_URLS = {
  lite: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
  full: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task',
  heavy: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task',
};

const WASM_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm';

/**
 * MediaPipe 姿态检测封装
 * 使用 PoseLandmarker，VIDEO 模式，逐帧 detectForVideo
 */
export class PoseDetector {
  constructor() {
    this.landmarker = null;
    this.lastVideoTime = -1;
    this.modelVariant = 'lite';
  }

  /**
   * 初始化加载模型（首次调用，约 5MB 下载）
   * @param {object} [opts] - { variant: 'lite'|'full'|'heavy' }
   * @param {(msg: string) => void} [onProgress] - 加载进度回调
   */
  async init(opts = {}, onProgress) {
    this.modelVariant = opts.variant || 'lite';
    const modelPath = MODEL_URLS[this.modelVariant] || MODEL_URLS.lite;

    if (onProgress) onProgress('正在加载 WASM 运行时…');
    const vision = await FilesetResolver.forVisionTasks(WASM_URL);

    if (onProgress) onProgress('正在加载姿态识别模型…');
    this.landmarker = await PoseLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: modelPath,
        delegate: 'GPU',
      },
      runningMode: 'VIDEO',
      numPoses: 1,
    });
  }

  /**
   * 检测单帧姿态
   * @param {HTMLVideoElement} video
   * @returns {Array<object>|null} 33 个关键点 [{x,y,z,visibility}, ...] 或 null
   */
  detect(video) {
    if (!this.landmarker) return null;
    // 帧未更新则跳过
    if (video.readyState < 2) return null;
    const ts = performance.now();
    if (video.currentTime === this.lastVideoTime) return null;
    this.lastVideoTime = video.currentTime;

    let result;
    try {
      result = this.landmarker.detectForVideo(video, ts);
    } catch {
      return null;
    }
    return result?.landmarks?.[0] || null;
  }

  /**
   * 切换模型精度（需要重新 init）
   * @param {'lite'|'full'|'heavy'} variant
   */
  setVariant(variant) {
    if (MODEL_URLS[variant] && variant !== this.modelVariant) {
      this.modelVariant = variant;
      this.landmarker = null; // 标记需重新初始化
      this.lastVideoTime = -1;
      return true;
    }
    return false;
  }

  /** 释放模型资源 */
  close() {
    if (this.landmarker) {
      this.landmarker.close();
      this.landmarker = null;
    }
  }
}

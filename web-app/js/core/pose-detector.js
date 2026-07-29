// MediaPipe Pose Landmarker 封装
// 官方文档：https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/web_js
// 注意：MediaPipe 使用动态 import（在 init 中按需加载），避免顶层静态 import
// 导致 CDN 不可用时整个模块链崩溃、页面所有按钮失效。

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
// 本地托管：避免国内 CDN 访问慢/被墙导致模型加载卡死
const MODEL_URLS = {
  lite: '/libs/mediapipe/models/pose_landmarker_lite.task',
  full: '/libs/mediapipe/models/pose_landmarker_lite.task',  // 暂复用 lite，如需 full 可下载
  heavy: '/libs/mediapipe/models/pose_landmarker_lite.task', // 暂复用 lite
};

// WASM 运行时：本地托管
// 目录名含版本号 _v2 用于缓存破坏（避免 Cloudflare immutable 缓存旧错误响应）
const WASM_URL = '/libs/mediapipe/wasm_v2';

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
   * 检测当前设备是否为移动端（用于决定是否跳过 GPU 尝试）
   * 某些移动端浏览器 WebGL 报错不抛异常而是静默失败，直接用 CPU 更稳妥
   */
  _isMobile() {
    return /Android|iPhone|iPad|iPod|Mobile|Windows Phone/i.test(navigator.userAgent)
      || (navigator.maxTouchPoints > 1 && window.innerWidth < 768);
  }

  /**
   * 带超时的 Promise 包装
   * 移动端网络慢时 WASM 加载可能卡住，15 秒超时防止无限等待
   */
  _withTimeout(promise, ms, label) {
    return Promise.race([
      promise,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error(`${label} 超时（${ms / 1000}s）`)), ms)
      ),
    ]);
  }

  /**
   * 初始化加载模型（首次调用，约 5MB 下载）
   * 移动端策略：直接使用 CPU 模式，跳过 GPU 尝试（避免静默失败）
   * 桌面端策略：先 GPU，失败后 CPU 回退
   * @param {object} [opts] - { variant: 'lite'|'full'|'heavy' }
   * @param {(msg: string) => void} [onProgress] - 加载进度回调
   */
  async init(opts = {}, onProgress) {
    this.modelVariant = opts.variant || 'lite';
    const modelPath = MODEL_URLS[this.modelVariant] || MODEL_URLS.lite;
    const isMobile = this._isMobile();

    // 第一步：加载 WASM 运行时（带超时）
    if (onProgress) onProgress('正在加载 WASM 运行时…');
    let FilesetResolver, PoseLandmarker;
    try {
      const mod = await this._withTimeout(
        import('/libs/mediapipe/vision_bundle.mjs'),
        15000,
        'WASM 模块加载'
      );
      FilesetResolver = mod.FilesetResolver;
      PoseLandmarker = mod.PoseLandmarker;
    } catch (importErr) {
      throw new Error('WASM 运行时加载失败：' + (importErr.message || importErr) + '。请检查网络连接后刷新页面。');
    }

    // 第二步：初始化 FilesetResolver（加载 .wasm 文件）
    let vision;
    try {
      vision = await this._withTimeout(
        FilesetResolver.forVisionTasks(WASM_URL),
        20000,
        'WASM 文件初始化'
      );
    } catch (fsErr) {
      throw new Error('WASM 文件初始化失败：' + (fsErr.message || fsErr) + '。请刷新页面重试。');
    }

    // 第三步：创建 PoseLandmarker（模型加载）
    // 移动端直接 CPU；桌面端先 GPU 再 CPU 回退
    const delegate = isMobile ? 'CPU' : 'GPU';

    if (onProgress) {
      onProgress(isMobile
        ? '正在加载姿态识别模型（CPU 模式）…'
        : '正在加载姿态识别模型（GPU 加速）…');
    }

    try {
      this.landmarker = await this._withTimeout(
        PoseLandmarker.createFromOptions(vision, {
          baseOptions: { modelAssetPath: modelPath, delegate },
          runningMode: 'VIDEO',
          numPoses: 1,
        }),
        30000,
        '模型创建'
      );
    } catch (err) {
      // 桌面端 GPU 失败时回退到 CPU
      if (!isMobile && delegate === 'GPU') {
        console.warn('[PoseDetector] GPU 模式失败，回退到 CPU:', err);
        if (onProgress) onProgress('GPU 不可用，正在切换到 CPU 模式…');
        this.landmarker = await this._withTimeout(
          PoseLandmarker.createFromOptions(vision, {
            baseOptions: { modelAssetPath: modelPath, delegate: 'CPU' },
            runningMode: 'VIDEO',
            numPoses: 1,
          }),
          30000,
          'CPU 模型创建'
        );
      } else {
        throw new Error('模型加载失败：' + (err.message || err) + '。请刷新页面重试。');
      }
    }

    // 验证 landmarker 真正可用（防止静默失败：对象创建成功但 detect 不工作）
    if (!this.landmarker || typeof this.landmarker.detectForVideo !== 'function') {
      throw new Error('模型初始化异常：landmarker 对象不可用。请刷新页面重试。');
    }
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

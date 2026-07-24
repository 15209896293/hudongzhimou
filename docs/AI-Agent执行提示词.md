# 护动智眸 Web 应用开发 — AI Agent 执行提示词

> 将此文档完整复制给 AI Agent 作为任务指令。
> AI Agent 应按照下方步骤自主完成全部开发工作。

---

## 任务概述

你是一个资深前端开发工程师。你的任务是：在 `f:\比赛\护动智眸\web-app\` 目录下，从零创建一个基于浏览器的"运动健身防伤评估系统"Web 应用。

这个应用使用摄像头实时捕捉用户动作，通过 MediaPipe 进行姿态识别，基于 FMS（功能性运动筛查）体系评估动作质量，检测受伤风险，并提供 AI 教练建议。

**技术栈**：纯 HTML/CSS/JavaScript（无构建工具）+ MediaPipe Tasks Web API + Tailwind CSS (CDN) + Node.js 后端（已有）

**设计风格**：浅色主题，白底 + 彩色骨架线，参考 Apple Health 的简洁高级感

---

## 第一步：创建目录结构与基础文件

在 `f:\比赛\护动智眸\web-app\` 下创建以下结构：

```
web-app/
├── index.html
├── css/
│   ├── style.css
│   ├── theme.css
│   └── skeleton.css
├── js/
│   ├── app.js
│   ├── core/
│   │   ├── pose-detector.js
│   │   ├── fms-engine.js
│   │   ├── safety-checker.js
│   │   ├── angle-utils.js
│   │   └── pipeline.js
│   ├── ui/
│   │   ├── camera-view.js
│   │   ├── dashboard.js
│   │   ├── report-view.js
│   │   └── fms-panel.js
│   ├── services/
│   │   ├── api-client.js
│   │   └── ai-analyzer.js
│   └── utils/
│       ├── storage.js
│       └── helpers.js
└── assets/
    └── sounds/
```

### index.html 要求

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>护动智眸 — 运动健身防伤评估</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- MediaPipe Tasks Web API -->
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/vision_bundle.mjs" type="module"></script>
  <link rel="stylesheet" href="css/theme.css">
  <link rel="stylesheet" href="css/style.css">
  <link rel="stylesheet" href="css/skeleton.css">
</head>
<body>
  <!-- 顶部导航 -->
  <nav id="nav">...</nav>
  <!-- 页面容器 -->
  <main id="app">
    <div id="page-training" class="page active"></div>
    <div id="page-report" class="page"></div>
    <div id="page-settings" class="page"></div>
  </main>
  <script type="module" src="js/app.js"></script>
</body>
</html>
```

---

## 第二步：实现浅色主题 CSS

### css/theme.css

```css
:root {
  /* 背景色 */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F5F5F7;
  --bg-tertiary: #FAFAFA;

  /* 文字色 */
  --text-primary: #1D1D1F;
  --text-secondary: #6E6E73;
  --text-tertiary: #AEAEB2;

  /* 骨架线颜色 */
  --skeleton-head: #FF375F;
  --skeleton-torso: #FF9F0A;
  --skeleton-left-arm: #30D158;
  --skeleton-right-arm: #64D2FF;
  --skeleton-left-leg: #BF5AF2;
  --skeleton-right-leg: #FFD60A;
  --skeleton-joint: #FFFFFF;

  /* 风险等级 */
  --risk-safe: #30D158;
  --risk-warning: #FF9F0A;
  --risk-danger: #FF453A;

  /* 强调色 */
  --accent: #007AFF;
  --accent-pressed: #0051D5;

  /* 圆角 */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;

  /* 阴影 */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.08);

  /* 字体 */
  --font-sans: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
               'PingFang SC', 'Noto Sans CJK SC', sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--bg-secondary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}
```

### css/style.css 核心要求

- 顶部导航栏：白底，毛玻璃效果 `backdrop-filter: blur(20px)`，底部 1px 灰色边线
- 卡片：白底，`border-radius: var(--radius-lg)`，`box-shadow: var(--shadow-md)`
- 按钮：圆角 `var(--radius-sm)`，主按钮蓝底白字，次按钮灰底
- 页面切换：`.page` 默认 `display: none`，`.page.active` 为 `display: block`
- 数据数字：大号字体，`font-weight: 600`
- 标签/辅助文字：`color: var(--text-secondary)`，`font-size: 13px`

---

## 第三步：实现 MediaPipe 姿态检测

### js/core/pose-detector.js

```javascript
// MediaPipe Pose Landmarker 封装
// 使用 @mediapipe/tasks-vision 的 PoseLandmarker

export class PoseDetector {
  constructor() {
    this.landmarker = null;
    this.lastVideoTime = -1;
  }

  async init() {
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
    );
    this.landmarker = await PoseLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        delegate: "GPU"
      },
      runningMode: "VIDEO",
      numPoses: 1
    });
  }

  detect(video) {
    if (!this.landmarker) return null;
    const currentTime = video.currentTime;
    if (currentTime === this.lastVideoTime) return null;
    this.lastVideoTime = currentTime;
    const result = this.landmarker.detectForVideo(video, currentTime);
    return result.landmarks?.[0] || null;
  }
}
```

**关键点索引常量**（必须在代码中定义）：
```javascript
export const POSE_LANDMARKS = {
  NOSE: 0,
  LEFT_SHOULDER: 11, RIGHT_SHOULDER: 12,
  LEFT_ELBOW: 13, RIGHT_ELBOW: 14,
  LEFT_WRIST: 15, RIGHT_WRIST: 16,
  LEFT_HIP: 23, RIGHT_HIP: 24,
  LEFT_KNEE: 25, RIGHT_KNEE: 26,
  LEFT_ANKLE: 27, RIGHT_ANKLE: 28,
  LEFT_FOOT_INDEX: 31, RIGHT_FOOT_INDEX: 32
};
```

---

## 第四步：实现关节角度计算

### js/core/angle-utils.js

实现以下函数：

```javascript
// 计算三点之间的角度（度数）
// a, b, c 是 {x, y, z} 对象，b 是顶点
export function calculateAngle(a, b, c) {
  // 使用向量点积计算
  // 返回 0-180 度
}

// 计算线段与垂直方向的夹角
// 用于躯干前倾角度检测
export function calculateFromVertical(upper, lower) {
  // upper = {x, y, z}, lower = {x, y, z}
  // 返回与垂直线的夹角（度数）
}

// 计算左右对称性
// left, right 是关键点数组
// 返回 { isSymmetric: bool, offset: number }
export function checkSymmetry(leftKeypoint, rightKeypoint, threshold = 0.05) {
  // 比较左右两侧关键点的 y 坐标差异
}

// 计算膝关节外翻角度
// hip, knee, ankle 三点
// 返回外翻角度（正值=外翻，负值=内翻）
export function calculateKneeValgus(hip, knee, ankle) {
  // 膝关节相对髋-踝连线的偏移
}
```

---

## 第五步：实现 FMS 评分引擎

### js/core/fms-engine.js

这是核心模块。实现七项 FMS 动作的评分算法。

```javascript
import { calculateAngle, calculateFromVertical, calculateKneeValgus, checkSymmetry } from './angle-utils.js';
import { POSE_LANDMARKS } from './pose-detector.js';

// FMS 评分结果结构
// {
//   test: 'deep_squat',
//   score: 3,           // 0-3
//   issues: [],         // 发现的问题
//   recommendations: [] // 建议
// }

export class FMSEngine {
  // 深蹲评分
  scoreDeepSquat(landmarks) {
    // 评分标准：
    // 3分：大腿低于水平面，躯干直立，足跟着地，膝追踪脚尖
    // 2分：大腿达到水平面，轻微躯干前倾，足跟着地
    // 1分：大腿无法达到水平面，或足跟离地，或明显膝内扣
    // 0分：任何部位疼痛
    //
    // 需要计算：
    // 1. 膝关节屈曲角度（hip-knee-ankle）—— <100度算深蹲到位
    // 2. 躯干前倾角度（shoulder-hip vs 垂直线）—— >45度为过度前倾
    // 3. 膝关节外翻角度 —— >15度为内扣
    // 4. 足跟是否离地（ankle vs foot_index 的 y 坐标比较）
  }

  // 跨栏步评分
  scoreHurdleStep(landmarks) {
    // 评分标准：
    // 3分：髋膝踝对齐，躯干稳定，无代偿
    // 2分：轻微偏移，躯干晃动
    // 1分：明显失去平衡或对齐不良
    // 需要计算：髋关节屈曲角度、骨盆水平度、膝踝对齐
  }

  // 直线弓步评分
  scoreInlineLunge(landmarks) {
    // 评分标准：
    // 3分：前膝在脚踝正上方，后腿伸直，躯干稳定
    // 2分：前膝轻微偏移，后腿不完全伸直
    // 1分：失去平衡或膝盖明显偏离
    // 需要计算：前后脚距离比例、前膝位置、躯干倾斜
  }

  // 肩关节灵活性评分
  scoreShoulderMobility(landmarks) {
    // 评分标准：
    // 3分：双拳距离<1手宽
    // 2分：双拳距离1-1.5手宽
    // 1分：双拳距离>1.5手宽
    // 需要计算：双手腕在背后的距离（通过肩-肘-腕角度推算）
    // 注意：此动作需要双手在背后，MediaPipe 可能无法精确捕捉
    // 降级方案：改为双手在头顶后方拉伸，测量肩关节活动度
  }

  // 主动直腿抬高评分
  scoreASLR(landmarks) {
    // 评分标准：
    // 3分：抬高腿踝关节在对侧膝关节以上
    // 2分：踝关节在对侧膝关节与髂前上棘之间
    // 1分：踝关节低于对侧膝关节
    // 需要计算：抬高腿与地面的角度（hip-ankle vs 水平线）
  }

  // 躯干稳定性俯卧撑评分
  scoreTrunkStability(landmarks) {
    // 评分标准：
    // 3分：身体完全一线，无塌腰
    // 2分：轻微塌腰或翘臀
    // 1分：明显塌腰或无法完成
    // 需要计算：肩-髋-膝的直线度（偏离度）
  }

  // 旋转稳定性评分
  scoreRotaryStability(landmarks) {
    // 评分标准：
    // 3分：同侧手脚伸展，躯干稳定
    // 2分：需对侧手脚交替
    // 1分：无法完成
    // 需要计算：脊柱旋转角度、四肢协调性
  }

  // 获取总分
  getTotalScore(scores) {
    return Object.values(scores).reduce((sum, s) => sum + (s.score || 0), 0);
  }

  // 风险等级判定
  getRiskLevel(totalScore, asymmetries) {
    if (totalScore < 14 || asymmetries.length > 0) return 'high';
    if (totalScore < 18) return 'moderate';
    return 'low';
  }
}
```

**重要**：每个评分函数需要返回详细的结构化数据，包括具体角度数值和问题描述，供 UI 显示和 AI 分析使用。

---

## 第六步：实现防伤规则检测

### js/core/safety-checker.js

```javascript
import { calculateAngle, calculateKneeValgus, calculateFromVertical } from './angle-utils.js';
import { POSE_LANDMARKS } from './pose-detector.js';

export class SafetyChecker {
  check(landmarks) {
    const alerts = [];

    // 1. 膝关节内扣检测
    // 左膝：hip(23) - knee(25) - ankle(27)
    // 右膝：hip(24) - knee(26) - ankle(28)
    // 外翻角度 > 15度 = 警告，> 25度 = 危险

    // 2. 骨盆倾斜检测
    // 左髋(23) 和 右髋(24) 的 y 坐标差
    // 差值 > 0.03 = 警告，> 0.06 = 危险

    // 3. 躯干过度前倾
    // shoulder(11/12) - hip(23/24) 与垂直线夹角
    // > 30度 = 警告，> 45度 = 危险

    // 4. 左右不对称
    // 比较左右关节角度差异

    const level = alerts.some(a => a.severity === 'danger') ? 'danger'
                : alerts.some(a => a.severity === 'warning') ? 'warning'
                : 'safe';

    return { level, alerts };
  }
}
```

---

## 第七步：实现处理管线

### js/core/pipeline.js

```javascript
import { PoseDetector } from './pose-detector.js';
import { FMSEngine } from './fms-engine.js';
import { SafetyChecker } from './safety-checker.js';

export class FramePipeline {
  constructor() {
    this.detector = new PoseDetector();
    this.fmsEngine = new FMSEngine();
    this.safetyChecker = new SafetyChecker();
    this.currentTest = 'deep_squat';
    this.onUpdate = null; // 回调函数
  }

  async init() {
    await this.detector.init();
  }

  setTest(testName) {
    this.currentTest = testName;
  }

  process(video) {
    // 阶段1：推理
    const landmarks = this.detector.detect(video);
    if (!landmarks) return null;

    // 阶段2：FMS分析
    const fmsResult = this.scoreByTest(this.currentTest, landmarks);

    // 阶段3：防伤检测
    const safetyResult = this.safetyChecker.check(landmarks);

    // 阶段4：渲染数据准备
    const output = {
      landmarks,
      fms: fmsResult,
      safety: safetyResult,
      timestamp: performance.now()
    };

    if (this.onUpdate) this.onUpdate(output);
    return output;
  }

  scoreByTest(test, landmarks) {
    const map = {
      'deep_squat': this.fmsEngine.scoreDeepSquat,
      'hurdle_step': this.fmsEngine.scoreHurdleStep,
      'inline_lunge': this.fmsEngine.scoreInlineLunge,
      'shoulder_mobility': this.fmsEngine.scoreShoulderMobility,
      'aslr': this.fmsEngine.scoreASLR,
      'trunk_stability': this.fmsEngine.scoreTrunkStability,
      'rotary_stability': this.fmsEngine.scoreRotaryStability
    };
    const fn = map[test];
    return fn ? fn.call(this.fmsEngine, landmarks) : null;
  }
}
```

---

## 第八步：实现骨架线渲染

### js/ui/camera-view.js

这是用户看到的核心画面。需要在 Canvas 上叠加彩色骨架线。

```javascript
// 骨架连接定义
const POSE_CONNECTIONS = {
  // 躯干（橙色）
  torso: [
    [11, 12],  // 左肩-右肩
    [11, 23],  // 左肩-左髋
    [12, 24],  // 右肩-右髋
    [23, 24],  // 左髋-右髋
  ],
  // 左臂（绿色）
  leftArm: [
    [11, 13],  // 左肩-左肘
    [13, 15],  // 左肘-左腕
  ],
  // 右臂（蓝色）
  rightArm: [
    [12, 14],  // 右肩-右肘
    [14, 16],  // 右肘-右腕
  ],
  // 左腿（紫色）
  leftLeg: [
    [23, 25],  // 左髋-左膝
    [25, 27],  // 左膝-左踝
    [27, 31],  // 左踝-左脚
  ],
  // 右腿（黄色）
  rightLeg: [
    [24, 26],  // 右髋-右膝
    [26, 28],  // 右膝-右踝
    [28, 32],  // 右踝-右脚
  ]
};

// 渲染函数
function renderSkeleton(ctx, landmarks, canvasWidth, canvasHeight) {
  // 1. 绘制连线
  // 躯干用 var(--skeleton-torso)
  // 左臂用 var(--skeleton-left-arm)
  // 右臂用 var(--skeleton-right-arm)
  // 左腿用 var(--skeleton-left-leg)
  // 右腿用 var(--skeleton-right-leg)
  // 线宽 4px，圆角端点 lineCap='round'

  // 2. 绘制关键点
  // 白色填充圆，半径 6px，2px 彩色描边
  // 风险关节添加红色脉冲动画
}
```

**渲染要求**：
- 摄像头画面镜像翻转（用户看自己像照镜子）
- 骨架线叠加在画面上方，半透明背景
- 风险关节（safety alerts 中标记的关节）用红色脉冲效果
- 画面右上角显示当前 FPS

---

## 第九步：实现训练页面 UI

### 训练页面布局（HTML 结构）

```html
<div id="page-training" class="page active">
  <!-- 顶部：动作选择器 + 控制按钮 -->
  <div class="training-header">
    <select id="fms-test-select">
      <option value="deep_squat">深蹲 (Deep Squat)</option>
      <option value="hurdle_step">跨栏步 (Hurdle Step)</option>
      <option value="inline_lunge">直线弓步 (In-Line Lunge)</option>
      <option value="shoulder_mobility">肩关节灵活性 (Shoulder Mobility)</option>
      <option value="aslr">主动直腿抬高 (ASLR)</option>
      <option value="trunk_stability">躯干稳定性俯卧撑</option>
      <option value="rotary_stability">旋转稳定性</option>
    </select>
    <button id="btn-start">开始检测</button>
    <button id="btn-stop">停止</button>
  </div>

  <!-- 主体：左侧画面 + 右侧数据 -->
  <div class="training-body">
    <!-- 左侧 70%：摄像头画面 -->
    <div class="camera-container">
      <video id="camera-video" autoplay playsinline></video>
      <canvas id="skeleton-canvas"></canvas>
      <!-- 风险等级标识 -->
      <div id="risk-indicator"></div>
    </div>

    <!-- 右侧 30%：数据面板 -->
    <div class="data-panel">
      <!-- FMS 评分卡片 -->
      <div class="card fms-score-card">
        <h3>当前评分</h3>
        <div class="score-display">
          <span id="fms-score" class="score-number">--</span>
          <span class="score-max">/3</span>
        </div>
        <div id="fms-issues"></div>
      </div>

      <!-- 关节角度卡片 -->
      <div class="card angles-card">
        <h3>关节角度</h3>
        <div id="angles-list"></div>
      </div>

      <!-- 风险预警卡片 -->
      <div class="card alerts-card">
        <h3>风险预警</h3>
        <div id="alerts-list"></div>
      </div>
    </div>
  </div>
</div>
```

### css/style.css 训练页面样式要求

```css
.training-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  margin-bottom: 16px;
}

.training-body {
  display: flex;
  gap: 16px;
}

.camera-container {
  flex: 0 0 65%;
  position: relative;
  background: #000;
  border-radius: var(--radius-lg);
  overflow: hidden;
  aspect-ratio: 4/3;
}

.camera-container video,
.camera-container canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1); /* 镜像 */
}

.data-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-md);
}

.score-number {
  font-size: 48px;
  font-weight: 700;
  color: var(--accent);
}

/* 风险等级颜色 */
.risk-safe { background: var(--risk-safe); }
.risk-warning { background: var(--risk-warning); }
.risk-danger { background: var(--risk-danger); }
```

---

## 第十步：实现报告页面

### 报告页面需要包含

1. **FMS 总分圆环图** — 用 SVG 或 Canvas 绘制，总分 / 21，颜色根据风险等级变化
2. **七项评分雷达图** — 用 SVG 绘制，7 个轴对应 7 项测试
3. **AI 教练建议卡片** — 显示 AI 分析结果
4. **历史趋势折线图** — 总分随时间变化

### 雷达图实现要点

```javascript
// 7 个轴，每个 0-3 分
// 顶点：上(深蹲) 右上(跨栏步) 右(弓步) 右下(肩关节) 下(ASLR) 左下(俯卧撑) 左(旋转)
// 用 SVG polygon 绘制评分区域，半透明蓝色填充
// 轴线和刻度用浅灰色
```

---

## 第十一步：实现后端 API 调用

### js/services/api-client.js

```javascript
const API_BASE = 'http://localhost:3000/api';

export class ApiClient {
  // 通用请求
  async request(path, options = {}) {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers
      }
    });
    return res.json();
  }

  // 用户
  login(username, password) { ... }
  register(data) { ... }
  getProfile() { ... }

  // FMS
  saveFMSScore(scores) { ... }
  getFMSHistory() { ... }

  // AI 分析
  requestAIAnalysis(actionName, jointData, injuryHistory) { ... }
  requestVisualAnalysis(imageBase64, actionName, currentScore) { ... }
}
```

---

## 第十二步：实现 AI 分析集成

### js/services/ai-analyzer.js

```javascript
import { ApiClient } from './api-client.js';

export class AIAnalyzer {
  constructor() {
    this.api = new ApiClient();
  }

  // 文本分析轨：发送关节角度数据
  async textAnalysis(actionName, jointSequence, injuryHistory) {
    const result = await this.api.requestAIAnalysis(actionName, jointSequence, injuryHistory);
    // 解析并验证 JSON
    return this.validateResult(result);
  }

  // 视觉分析轨：发送当前帧截图
  async visualAnalysis(canvas, actionName, currentScore) {
    const imageBase64 = canvas.toDataURL('image/jpeg', 0.8);
    const result = await this.api.requestVisualAnalysis(imageBase64, actionName, currentScore);
    return this.validateResult(result);
  }

  // 交叉验证
  crossValidate(textResult, visualResult) {
    if (!textResult || !visualResult) return textResult || visualResult;
    const diff = Math.abs(textResult.score - visualResult.score);
    if (diff <= 1) return { ...textResult, score: Math.max(textResult.score, visualResult.score) };
    if (diff === 2) return { ...textResult, confidence: 'low', needsReview: true };
    return { needsReview: true, alert: '评分差异过大，建议重新测试' };
  }

  validateResult(result) {
    // 确保返回的是合法 JSON 结构
    if (!result || !result.success) return null;
    const data = result.result || result;
    if (typeof data.score !== 'number') return null;
    return data;
  }
}
```

---

## 第十三步：实现应用入口与路由

### js/app.js

```javascript
import { FramePipeline } from './core/pipeline.js';
import { CameraView } from './ui/camera-view.js';
import { Dashboard } from './ui/dashboard.js';
import { ReportView } from './ui/report-view.js';

class App {
  constructor() {
    this.pipeline = null;
    this.cameraView = null;
    this.running = false;
  }

  async init() {
    this.bindNavigation();
    this.bindControls();
    // 延迟初始化 pipeline（用户点击开始时才加载模型）
  }

  bindNavigation() {
    // 顶部导航切换页面
    // training / report / settings
  }

  async startTraining() {
    if (!this.pipeline) {
      this.pipeline = new FramePipeline();
      await this.pipeline.init(); // 加载 MediaPipe 模型
    }
    this.running = true;
    this.loop();
  }

  loop() {
    if (!this.running) return;
    const video = document.getElementById('camera-video');
    const result = this.pipeline.process(video);
    if (result) {
      this.cameraView.render(result);
      this.updateDataPanel(result);
    }
    requestAnimationFrame(() => this.loop());
  }
}

const app = new App();
app.init();
```

---

## 第十四步：后端新增接口

在 `f:\比赛\护动智眸\backend\server.js` 中新增以下接口：

```javascript
// ========== FMS 评分管理 ==========

// 保存 FMS 评分
app.post('/api/fms/save', tokenAuth, async (req, res) => {
  try {
    const { scores, total_score, asymmetry_flags, ai_analysis } = req.body;
    const userId = req.user.userId;
    // 存入 fms_records 表
    const [result] = await pool.execute(
      `INSERT INTO fms_records (user_id, deep_squat, hurdle_step, inline_lunge,
       shoulder_mobility, aslr, trunk_stability, rotary_stability,
       total_score, asymmetry_flags, ai_analysis)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [userId, scores.deep_squat, scores.hurdle_step, scores.inline_lunge,
       scores.shoulder_mobility, scores.aslr, scores.trunk_stability,
       scores.rotary_stability, total_score,
       JSON.stringify(asymmetry_flags), ai_analysis]
    );
    res.json({ success: true, id: result.insertId });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 获取 FMS 历史
app.get('/api/fms/history', tokenAuth, async (req, res) => {
  try {
    const userId = req.user.userId;
    const [rows] = await pool.execute(
      'SELECT * FROM fms_records WHERE user_id = ? ORDER BY test_date DESC LIMIT 50',
      [userId]
    );
    res.json({ success: true, data: rows });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// ========== AI 视觉分析 ==========

app.post('/api/ai/visual', tokenAuth, aiLimiter, async (req, res) => {
  try {
    const { image, action_name, current_score } = req.body;
    // 调用 GLM-4V-Flash
    const result = await analyzeVisual(image, action_name, current_score);
    res.json({ success: true, result });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});
```

同时在 `backend/db.js` 或单独的 SQL 文件中添加建表语句：

```sql
CREATE TABLE IF NOT EXISTS fms_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  test_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  deep_squat TINYINT DEFAULT 0,
  hurdle_step TINYINT DEFAULT 0,
  inline_lunge TINYINT DEFAULT 0,
  shoulder_mobility TINYINT DEFAULT 0,
  aslr TINYINT DEFAULT 0,
  trunk_stability TINYINT DEFAULT 0,
  rotary_stability TINYINT DEFAULT 0,
  total_score INT DEFAULT 0,
  asymmetry_flags JSON,
  ai_analysis TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 验收标准

每个文件完成后，用以下标准自检：

### 必须满足
1. `index.html` 用浏览器直接打开能显示浅色主题页面，不报错
2. 点击"开始检测"能调起摄像头
3. 摄像头画面上有彩色骨架线叠加（白底画面中骨架清晰可见）
4. 选择不同 FMS 动作时，右侧面板显示对应评分
5. 膝关节内扣时，画面上该关节显示红色脉冲
6. 报告页有 FMS 总分圆环图和七项雷达图
7. 所有 CSS 使用 theme.css 中定义的变量，无硬编码颜色

### 加分项
8. 骨架线平滑过渡（不抖动）
9. FPS 显示在画面右上角
10. 设置页可切换摄像头
11. 离线状态下（无后端）基础功能仍可用

### 禁止事项
- 不要使用 React、Vue 等框架
- 不要使用 npm/webpack/vite 等构建工具
- 不要安装任何 Node.js 包到 web-app 目录
- 不要修改 legacy-desktop 目录下的任何文件
- 不要使用深色主题

---

## 执行顺序

请严格按以下顺序执行，每步完成后再进入下一步：

1. 创建目录结构 + index.html + 三个 CSS 文件
2. 实现 angle-utils.js（纯数学，可独立测试）
3. 实现 pose-detector.js（MediaPipe 封装）
4. 实现 fms-engine.js（核心评分逻辑）
5. 实现 safety-checker.js（防伤检测）
6. 实现 pipeline.js（串联 1-4）
7. 实现 camera-view.js（骨架渲染）
8. 实现训练页面完整 UI
9. 实现报告页面（圆环图 + 雷达图）
10. 实现设置页面
11. 实现 api-client.js + ai-analyzer.js
12. 实现后端新增 API
13. 联调测试
14. 性能优化

---

## 参考资源

- MediaPipe Tasks Web API 文档：https://developers.google.com/mediapipe/solutions/vision/pose_landmarker/web_js
- FMS 评分标准参考：Cook et al. (2006) "Functional Movement Screen"
- 旧项目代码参考：`f:\比赛\护动智眸\legacy-desktop\` 下的 Python 实现（仅参考逻辑，不复制代码）
- 后端已有代码：`f:\比赛\护动智眸\backend\server.js`（在此基础上扩展）
- 设计资源参考：`f:\比赛\护动智眸\design\` 下的 UI 方案
- 完整重构方案：`f:\比赛\护动智眸\docs\重构方案-运动健身防伤.md`

---

## 注意事项

1. **MediaPipe 模型加载**：首次加载需要下载约 5MB 模型文件，需要给用户显示加载进度
2. **摄像头权限**：必须用 HTTPS 或 localhost 才能调用摄像头，本地测试用 localhost
3. **骨架镜像**：视频画面要水平翻转（照镜子效果），但骨架坐标也要对应翻转
4. **性能优先**：MediaPipe detectForVideo 每帧调用一次，用 requestAnimationFrame 驱动循环
5. **错误处理**：摄像头不可用、模型加载失败、API 不可达都要有友好的错误提示
6. **AI 分析频率**：不要每帧都调 AI API，建议每 2-3 秒采集一次关键帧分析

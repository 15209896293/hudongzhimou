// 训练动作库 — 11 种健身房动作配置
// 所有关键点索引统一使用 MediaPipe 33 点格式（非 COCO 17 点）
// 从桌面版 exercises.json 迁移，索引已转换

/**
 * 动作配置结构说明：
 * {
 *   name: 中文名,
 *   en: 英文名,
 *   category: 'fitness' | 'dance',
 *   counter: {
 *     keypoints: { left: [a,b,c], right: [a,b,c] },  // MediaPipe 索引，b 是顶点
 *     downAngle: number,   // 到达此角度进入"下"阶段
 *     upAngle: number,     // 回到此角度完成一次（up > down 为深蹲型，up < down 为弯举型）
 *     isLegExercise: bool, // true 时左右独立计数
 *     isStatic: bool,      // true 时不计数，只计时
 *     minRepTime: number,  // 最小动作间隔 ms
 *   },
 *   safety: { 关节名: { min, max, warning_min, warning_max } },
 *   quality: { 维度名: { ideal:[min,max], mild:[min,max], bad:[min,max], penalty:number } },
 *   voiceTips: { '关节_min'/'关节_max': 提示语 },
 * }
 */

export const EXERCISES = {
  squat: {
    name: '深蹲',
    en: 'Squat',
    category: 'fitness',
    counter: {
      keypoints: { left: [23, 25, 27], right: [24, 26, 28] }, // 髋-膝-踝
      downAngle: 110,
      upAngle: 160,
      isLegExercise: false,
      isStatic: false,
      minRepTime: 500,
    },
    safety: {
      knee: { min: 70, max: 170, warning_min: 80, warning_max: 160 },
      back: { min: 140, max: 180, warning_min: 150, warning_max: 180 },
    },
    quality: {
      kneeFlexion: { ideal: [70, 110], mild: [110, 130], bad: [130, 180], penalty: 25 },
      trunkLean: { ideal: [0, 30], mild: [30, 45], bad: [45, 90], penalty: 30 },
      kneeValgus: { ideal: [0, 15], mild: [15, 25], bad: [25, 999], penalty: 30 },
    },
    voiceTips: {
      knee_min: '膝盖弯曲角度过小，请稍微站直一些',
      knee_max: '膝盖弯曲超过安全范围，请减小下蹲深度',
      back_min: '请保持背部挺直，不要弯腰',
    },
  },

  pushup: {
    name: '俯卧撑',
    en: 'Push-up',
    category: 'fitness',
    counter: {
      keypoints: { left: [11, 13, 15], right: [12, 14, 16] }, // 肩-肘-腕
      downAngle: 90,
      upAngle: 160,
      isLegExercise: false,
      isStatic: false,
      minRepTime: 600,
    },
    safety: {
      elbow: { min: 60, max: 180, warning_min: 70, warning_max: 170 },
      back: { min: 150, max: 180, warning_min: 160, warning_max: 180 },
    },
    quality: {
      elbowFlexion: { ideal: [60, 90], mild: [90, 120], bad: [120, 180], penalty: 25 },
      trunkAlignment: { ideal: [0, 0.03], mild: [0.03, 0.06], bad: [0.06, 999], penalty: 30 },
    },
    voiceTips: {
      elbow_min: '手臂弯曲角度过小，请不要过度下压',
      back_min: '请保持身体呈一条直线，核心收紧',
    },
  },

  situp: {
    name: '仰卧起坐',
    en: 'Sit-up',
    category: 'fitness',
    counter: {
      keypoints: { left: [11, 23, 27], right: [12, 24, 28] }, // 肩-髋-踝
      downAngle: 145,
      upAngle: 70,
      isLegExercise: false,
      isStatic: false,
      minRepTime: 800,
    },
    safety: {
      neck: { min: 130, max: 180, warning_min: 140, warning_max: 180 },
    },
    quality: {
      trunkFlexion: { ideal: [40, 70], mild: [70, 100], bad: [100, 180], penalty: 30 },
    },
    voiceTips: {
      neck_min: '请不要用手拉扯头部，用腹部发力',
    },
  },

  bicep_curl: {
    name: '弯举',
    en: 'Bicep Curl',
    category: 'fitness',
    counter: {
      keypoints: { left: [11, 13, 15], right: [12, 14, 16] }, // 肩-肘-腕
      downAngle: 150,  // 伸直状态（大角度）= 起点
      upAngle: 60,     // 弯曲状态（小角度）= 终点
      isLegExercise: false,
      isStatic: false,
      minRepTime: 500,
    },
    safety: {
      elbow: { min: 40, max: 170, warning_min: 50, warning_max: 160 },
      shoulder: { min: 0, max: 45, warning_min: 0, warning_max: 30 },
    },
    quality: {
      elbowFlexion: { ideal: [40, 60], mild: [60, 80], bad: [80, 150], penalty: 25 },
      shoulderStability: { ideal: [0, 15], mild: [15, 30], bad: [30, 999], penalty: 20 },
    },
    voiceTips: {
      elbow_min: '弯曲角度过大，请控制动作幅度',
      shoulder_max: '请不要晃动肩膀，保持大臂贴近身体',
    },
  },

  lateral_raise: {
    name: '侧平举',
    en: 'Lateral Raise',
    category: 'fitness',
    counter: {
      keypoints: { left: [23, 11, 13], right: [24, 12, 14] }, // 髋-肩-肘
      downAngle: 20,
      upAngle: 80,
      isLegExercise: false,
      isStatic: false,
      minRepTime: 600,
    },
    safety: {
      shoulder: { min: 0, max: 100, warning_min: 0, warning_max: 90 },
    },
    quality: {
      shoulderAbduction: { ideal: [70, 90], mild: [50, 70], bad: [0, 50], penalty: 25 },
      elbowExtension: { ideal: [160, 180], mild: [140, 160], bad: [0, 140], penalty: 15 },
    },
    voiceTips: {
      shoulder_max: '手臂不要举得过高，避免肩峰撞击',
    },
  },

  overhead_press: {
    name: '推举',
    en: 'Overhead Press',
    category: 'fitness',
    counter: {
      keypoints: { left: [23, 11, 13], right: [24, 12, 14] }, // 髋-肩-肘
      downAngle: 90,
      upAngle: 150,
      isLegExercise: false,
      isStatic: false,
      minRepTime: 600,
    },
    safety: {
      shoulder: { min: 60, max: 180, warning_min: 70, warning_max: 170 },
      lower_back: { min: 150, max: 180, warning_min: 160, warning_max: 180 },
    },
    quality: {
      shoulderFlexion: { ideal: [150, 180], mild: [120, 150], bad: [60, 120], penalty: 25 },
      trunkStability: { ideal: [0, 15], mild: [15, 30], bad: [30, 999], penalty: 25 },
    },
    voiceTips: {
      lower_back_min: '请收紧核心，不要过度挺腰',
    },
  },

  leg_raise: {
    name: '抬腿',
    en: 'Leg Raise',
    category: 'fitness',
    counter: {
      keypoints: { left: [11, 23, 27], right: [12, 24, 28] }, // 肩-髋-踝
      downAngle: 160,
      upAngle: 90,
      isLegExercise: true,
      isStatic: false,
      minRepTime: 700,
    },
    safety: {
      lower_back: { min: 140, max: 180, warning_min: 150, warning_max: 180 },
    },
    quality: {
      hipFlexion: { ideal: [70, 90], mild: [50, 70], bad: [0, 50], penalty: 30 },
    },
    voiceTips: {
      lower_back_min: '请保持下背部贴地，不要拱腰',
    },
  },

  plank: {
    name: '平板支撑',
    en: 'Plank',
    category: 'fitness',
    counter: {
      keypoints: { left: [11, 23, 27], right: [12, 24, 28] },
      downAngle: 160,
      upAngle: 175,
      isLegExercise: false,
      isStatic: true,
      minRepTime: 0,
    },
    safety: {
      back: { min: 150, max: 180, warning_min: 160, warning_max: 180 },
      hip: { min: 150, max: 180, warning_min: 160, warning_max: 180 },
    },
    quality: {
      trunkAlignment: { ideal: [0, 0.03], mild: [0.03, 0.06], bad: [0.06, 999], penalty: 40 },
    },
    voiceTips: {
      back_min: '请保持背部挺直',
      hip_min: '请不要塌腰或翘臀',
    },
  },

  lunge: {
    name: '弓步蹲',
    en: 'Lunge',
    category: 'fitness',
    counter: {
      keypoints: { left: [23, 25, 27], right: [24, 26, 28] }, // 髋-膝-踝
      downAngle: 90,
      upAngle: 160,
      isLegExercise: true,
      isStatic: false,
      minRepTime: 600,
    },
    safety: {
      knee: { min: 70, max: 170, warning_min: 80, warning_max: 160 },
    },
    quality: {
      kneeFlexion: { ideal: [70, 100], mild: [100, 130], bad: [130, 180], penalty: 25 },
      trunkLean: { ideal: [0, 20], mild: [20, 35], bad: [35, 90], penalty: 25 },
    },
    voiceTips: {
      knee_min: '前腿膝盖不要超过脚尖',
    },
  },

  posture_1: {
    name: '形体站姿',
    en: 'Posture Standing',
    category: 'dance',
    counter: {
      keypoints: { left: [11, 23, 27], right: [12, 24, 28] },
      downAngle: 160,
      upAngle: 180,
      isLegExercise: false,
      isStatic: true,
      minRepTime: 0,
    },
    safety: {
      back: { min: 160, max: 180, warning_min: 170, warning_max: 180 },
      shoulder: { min: 160, max: 180, warning_min: 170, warning_max: 180 },
    },
    quality: {
      trunkAlignment: { ideal: [0, 0.03], mild: [0.03, 0.06], bad: [0.06, 999], penalty: 30 },
      shoulderLevel: { ideal: [0, 0.03], mild: [0.03, 0.05], bad: [0.05, 999], penalty: 20 },
    },
    voiceTips: {
      back_min: '请保持腰背挺直',
      shoulder_min: '请打开肩膀，不要含胸',
    },
  },

  stretch_1: {
    name: '侧腰拉伸',
    en: 'Side Bend Stretch',
    category: 'dance',
    counter: {
      keypoints: { left: [11, 23, 25], right: [12, 24, 26] }, // 肩-髋-膝
      downAngle: 160,
      upAngle: 130,
      isLegExercise: false,
      isStatic: false,
      minRepTime: 1000,
    },
    safety: {
      spine: { min: 120, max: 180, warning_min: 130, warning_max: 170 },
    },
    quality: {
      lateralFlexion: { ideal: [120, 140], mild: [140, 160], bad: [160, 180], penalty: 25 },
    },
    voiceTips: {
      spine_min: '侧弯幅度适中，不要过度拉伸',
    },
  },
};

/** 动作列表（用于下拉选择器） */
export const EXERCISE_LIST = Object.entries(EXERCISES).map(([key, v]) => ({
  key,
  name: v.name,
  en: v.en,
  category: v.category,
  isStatic: v.counter.isStatic,
}));

/**
 * 根据用户档案调整安全阈值（个性化）
 * @param {object} thresholds - 基准阈值 { joint: { min, max, warning_min, warning_max } }
 * @param {object} profile - { height, weight, age, gender, injury_history }
 * @returns {object} 调整后的阈值
 */
export function applyUserProfile(thresholds, profile) {
  if (!profile) return thresholds;
  const adjusted = JSON.parse(JSON.stringify(thresholds));

  // 身高偏差：每 10cm 偏差调整膝盖阈值 ±2°
  if (profile.height && adjusted.knee) {
    const heightDiff = profile.height - 170;
    const adj = Math.round(heightDiff / 10) * 2;
    adjusted.knee.min += adj;
    adjusted.knee.warning_min += adj;
  }

  // 年龄：40 岁以上每岁 +0.5°（膝盖更严格）
  if (profile.age && profile.age > 40 && adjusted.knee) {
    const ageAdj = (profile.age - 40) * 0.5;
    adjusted.knee.warning_min += ageAdj;
  }

  // 损伤史：相关部位加严 5°
  const injuries = Array.isArray(profile.injury_history)
    ? profile.injury_history
    : [profile.injury_history].filter(Boolean);

  for (const inj of injuries) {
    const s = String(inj);
    if (s.includes('膝') && adjusted.knee) {
      adjusted.knee.warning_min += 5;
    }
    if ((s.includes('腰') || s.includes('腰椎')) && adjusted.lower_back) {
      adjusted.lower_back.warning_min += 5;
    }
    if (s.includes('肩') && adjusted.shoulder) {
      adjusted.shoulder.warning_min += 5;
    }
  }

  return adjusted;
}

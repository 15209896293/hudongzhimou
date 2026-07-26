const axios = require('axios');

/**
 * 输入消毒：去除控制字符，限制长度
 */
function sanitizeInput(input) {
  if (!input || typeof input !== 'string') return '';
  return input
    .replace(/[\x00-\x1F\x7F]/g, '')
    .substring(0, 500);
}

/**
 * 从AI返回的文本中提取并解析JSON
 * @param {string} text - AI返回的原始文本
 * @returns {{ success: boolean, result?: object, error?: string, raw_text?: string }}
 */
function parseAIResponse(text) {
  if (!text || typeof text !== 'string') {
    return { success: false, error: 'AI返回为空', raw_text: text || '' };
  }

  let parsed = null;

  // 第一次尝试：直接 JSON.parse
  try {
    parsed = JSON.parse(text);
  } catch {
    // 直接解析失败，尝试从文本中提取 JSON 片段
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      try {
        parsed = JSON.parse(jsonMatch[0]);
      } catch {
        // 提取后仍然解析失败
      }
    }
  }

  if (!parsed) {
    return { success: false, error: 'AI返回格式异常', raw_text: text };
  }

  // 字段校验
  const validRiskLevels = ['safe', 'warning', 'danger'];
  const riskLevel = parsed.risk_level;
  if (!validRiskLevels.includes(riskLevel)) {
    return { success: false, error: 'AI返回格式异常：risk_level 无效', raw_text: text };
  }

  const suggestion = parsed.suggestion;
  if (typeof suggestion !== 'string' || suggestion.length === 0) {
    return { success: false, error: 'AI返回格式异常：suggestion 无效', raw_text: text };
  }

  const score = parsed.score;
  if (typeof score !== 'number' || !Number.isInteger(score) || score < 0 || score > 100) {
    return { success: false, error: 'AI返回格式异常：score 无效', raw_text: text };
  }

  return {
    success: true,
    result: {
      risk_level: riskLevel,
      suggestion: suggestion,
      score: score,
      affected_joints: Array.isArray(parsed.affected_joints) ? parsed.affected_joints : []
    }
  };
}

/**
 * 调用智谱AI GLM-4-Flash 分析运动动作
 * @param {string} actionName - 动作名称
 * @param {Array} jointSequence - 关节角度数据序列
 * @param {string} injuryHistory - 用户的损伤史
 * @returns {{ success: boolean, result?: object, error?: string, raw_text?: string }}
 */
async function analyzeAction(actionName, jointSequence, injuryHistory) {
  const apiKey = process.env.AI_API_KEY;
  const apiUrl = process.env.AI_API_URL || 'https://open.bigmodel.cn/api/paas/v4/chat/completions';
  const model = process.env.AI_MODEL || 'glm-4-flash';

  if (!apiKey) {
    throw new Error('AI API Key not configured');
  }

  // 输入消毒 + 帧数限制
  const safeActionName = sanitizeInput(actionName);
  const safeInjury = sanitizeInput(injuryHistory);
  const safeJointSeq = Array.isArray(jointSequence)
    ? jointSequence.slice(0, 50)
    : [];

  const prompt = `你是一位运动康复专家。用户正在做"${safeActionName}"动作。

用户损伤史：${safeInjury || '无'}

最近${safeJointSeq.length}帧关节角度数据：${JSON.stringify(safeJointSeq)}

请分析动作风险并严格按照以下JSON格式输出（不要输出其他内容）：
{
  "risk_level": "safe 或 warning 或 danger",
  "suggestion": "30字以内的纠正建议",
  "score": 0到100的整数评分,
  "affected_joints": ["受影响关节名称数组"]
}`;

  const response = await axios.post(
    apiUrl,
    {
      model: model,
      messages: [{ role: 'user', content: prompt }]
    },
    {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      timeout: 15000
    }
  );

  // 智谱AI返回格式兼容OpenAI：choices[0].message.content
  const aiText = response.data?.choices?.[0]?.message?.content || '';

  // 解析并校验返回结果
  return parseAIResponse(aiText);
}

// ========== FMS 专用：文本分析轨（GLM-4-Flash）==========
// 输出结构：{ fms_score, score_adjustment, issues[], recommendations[] }
// fms_score 为 0-3 整数，与现有 analyzeAction 的 0-100 风险制互不干扰

/**
 * 解析 FMS 文本分析返回
 * @returns {{ success: boolean, result?: object, error?: string, raw_text?: string }}
 */
function parseFMSResponse(text) {
  if (!text || typeof text !== 'string') {
    return { success: false, error: 'AI返回为空', raw_text: text || '' };
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch {
    const m = text.match(/\{[\s\S]*\}/);
    if (m) { try { parsed = JSON.parse(m[0]); } catch { /* noop */ } }
  }
  if (!parsed) return { success: false, error: 'AI返回格式异常', raw_text: text };

  if (typeof parsed.fms_score !== 'number' || !Number.isInteger(parsed.fms_score) ||
      parsed.fms_score < 0 || parsed.fms_score > 3) {
    return { success: false, error: 'AI返回格式异常：fms_score 无效', raw_text: text };
  }
  return {
    success: true,
    result: {
      fms_score: parsed.fms_score,
      score_adjustment: typeof parsed.score_adjustment === 'number' ? parsed.score_adjustment : 0,
      issues: Array.isArray(parsed.issues) ? parsed.issues : [],
      recommendations: Array.isArray(parsed.recommendations) ? parsed.recommendations : [],
    },
  };
}

/**
 * FMS 文本分析（GLM-4-Flash）
 * @param {string} testName - FMS 动作名（可含多个，逗号分隔）
 * @param {Array} jointSequence - 关节角度数据序列
 * @param {string} injuryHistory - 损伤史
 */
async function analyzeFMSAction(testName, jointSequence, injuryHistory) {
  const apiKey = process.env.AI_API_KEY;
  const apiUrl = process.env.AI_API_URL || 'https://open.bigmodel.cn/api/paas/v4/chat/completions';
  const model = process.env.AI_MODEL || 'glm-4-flash';

  if (!apiKey) throw new Error('AI API Key not configured');

  const safeAction = sanitizeInput(testName);
  const safeInjury = sanitizeInput(injuryHistory);
  const safeJointSeq = Array.isArray(jointSequence) ? jointSequence.slice(0, 50) : [];

  const prompt = `你是 FMS（功能性运动筛查）专家。用户正在做"${safeAction}"动作。
用户损伤史：${safeInjury || '无'}
最近${safeJointSeq.length}帧关节角度数据：${JSON.stringify(safeJointSeq)}

请基于 FMS 0-3 分制（3=完美，2=合格，1=不合格，0=疼痛）评估，严格按以下JSON输出（不要其他内容）：
{
  "fms_score": 0到3的整数,
  "score_adjustment": -1到1的整数微调,
  "issues": [{"joint":"关节","problem":"问题","severity":"mild|moderate|severe"}],
  "recommendations": ["建议1","建议2"]
}`;

  const response = await axios.post(apiUrl,
    { model, messages: [{ role: 'user', content: prompt }] },
    { headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' }, timeout: 15000 }
  );
  const aiText = response.data?.choices?.[0]?.message?.content || '';
  return parseFMSResponse(aiText);
}

// ========== FMS 专用：视觉分析轨（GLM-4V-Flash）==========
// 输出结构：{ fms_score, posture_quality, observed_issues[], coaching_tip }

/**
 * 解析视觉分析返回
 */
function parseVisualResponse(text) {
  if (!text || typeof text !== 'string') {
    return { success: false, error: 'AI返回为空', raw_text: text || '' };
  }
  let parsed = null;
  try { parsed = JSON.parse(text); }
  catch {
    const m = text.match(/\{[\s\S]*\}/);
    if (m) { try { parsed = JSON.parse(m[0]); } catch { /* noop */ } }
  }
  if (!parsed) return { success: false, error: 'AI返回格式异常', raw_text: text };

  if (typeof parsed.fms_score !== 'number' || !Number.isInteger(parsed.fms_score) ||
      parsed.fms_score < 0 || parsed.fms_score > 3) {
    return { success: false, error: 'AI返回格式异常：fms_score 无效', raw_text: text };
  }
  return {
    success: true,
    result: {
      fms_score: parsed.fms_score,
      posture_quality: typeof parsed.posture_quality === 'string' ? parsed.posture_quality : 'unknown',
      observed_issues: Array.isArray(parsed.observed_issues) ? parsed.observed_issues : [],
      coaching_tip: typeof parsed.coaching_tip === 'string' ? parsed.coaching_tip : '',
    },
  };
}

/**
 * FMS 视觉分析（GLM-4V-Flash，多模态）
 * @param {string} imageDataUrl - data:image/jpeg;base64,... 数据 URL
 * @param {string} testName - 动作名
 * @param {number} currentScore - 当前 FMS 引擎评分
 */
async function analyzeVisual(imageDataUrl, testName, currentScore) {
  const apiKey = process.env.AI_API_KEY;
  const apiUrl = process.env.AI_API_URL || 'https://open.bigmodel.cn/api/paas/v4/chat/completions';
  const visionModel = process.env.AI_VISION_MODEL || 'glm-4v-flash';

  if (!apiKey) throw new Error('AI API Key not configured');
  const safeAction = sanitizeInput(testName);
  const imageUrl = imageDataUrl.startsWith('data:') ? imageDataUrl : `data:image/jpeg;base64,${imageDataUrl}`;

  const prompt = `你是运动姿态分析专家。用户在做"${safeAction}"（FMS动作），当前评分${currentScore}/3。
请基于 FMS 0-3 分制评估图中姿态，严格按以下JSON输出（不要其他内容）：
{
  "fms_score": 0到3的整数,
  "posture_quality": "good|fair|poor",
  "observed_issues": ["问题1","问题2"],
  "coaching_tip": "30字以内的纠正建议"
}`;

  const response = await axios.post(apiUrl,
    {
      model: visionModel,
      messages: [{
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: imageUrl } },
        ],
      }],
    },
    { headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' }, timeout: 20000 }
  );
  const aiText = response.data?.choices?.[0]?.message?.content || '';
  return parseVisualResponse(aiText);
}

module.exports = { analyzeAction, parseAIResponse, analyzeFMSAction, parseFMSResponse, analyzeVisual, parseVisualResponse };

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

module.exports = { analyzeAction, parseAIResponse };

// AI 分析服务：文本轨 + 视觉轨 + 交叉验证
// 两轨均返回 fms_score(0-3) 用于交叉验证，各自另存诊断字段

import { ApiClient } from './api-client.js';
import { safeJSON } from '../utils/helpers.js';

export class AIAnalyzer {
  constructor() {
    this.api = new ApiClient();
  }

  /** 文本分析轨：发送关节角度数据 */
  async textAnalysis(actionName, jointSequence, injuryHistory) {
    let res;
    try {
      res = await this.api.requestFMSReport(jointSequence, actionName, injuryHistory);
    } catch {
      return null;
    }
    return this.validateTextResult(res);
  }

  /** 视觉分析轨：发送当前帧截图 */
  async visualAnalysis(canvas, actionName, currentScore) {
    const imageBase64 = canvas.toDataURL('image/jpeg', 0.8);
    let res;
    try {
      res = await this.api.requestVisualAnalysis(imageBase64, actionName, currentScore);
    } catch {
      return null;
    }
    return this.validateVisualResult(res);
  }

  /**
   * 交叉验证：比较两轨 fms_score
   * 差 ≤1 采用较高分；差 =2 标记需人工确认；差 =3 触发警报
   */
  crossValidate(textResult, visualResult) {
    if (!textResult && !visualResult) return null;
    if (!textResult) return visualResult;
    if (!visualResult) return textResult;

    const t = textResult.fms_score;
    const v = visualResult.fms_score;
    const diff = Math.abs(t - v);

    if (diff <= 1) {
      return {
        fms_score: Math.max(t, v),
        confidence: 'high',
        issues: [...(textResult.issues || []), ...(visualResult.observed_issues || [])],
        recommendations: textResult.recommendations || [],
        coaching_tip: visualResult.coaching_tip || '',
      };
    }
    if (diff === 2) {
      return {
        fms_score: Math.min(t, v),
        confidence: 'low',
        needsReview: true,
        note: '两轨评分差异较大，建议人工确认',
        issues: [...(textResult.issues || []), ...(visualResult.observed_issues || [])],
        recommendations: textResult.recommendations || [],
        coaching_tip: visualResult.coaching_tip || '',
      };
    }
    return {
      needsReview: true,
      alert: '评分差异过大（差3分），建议重新测试',
      fms_score: Math.min(t, v),
      confidence: 'low',
    };
  }

  // 校验文本轨结果
  validateTextResult(res) {
    if (!res || !res.success) return null;
    const data = res.data || res.result;
    if (!data || typeof data.fms_score !== 'number') return null;
    return {
      fms_score: Math.max(0, Math.min(3, Math.round(data.fms_score))),
      score_adjustment: data.score_adjustment || 0,
      issues: Array.isArray(data.issues) ? data.issues : [],
      recommendations: Array.isArray(data.recommendations) ? data.recommendations : [],
    };
  }

  // 校验视觉轨结果
  validateVisualResult(res) {
    if (!res || !res.success) return null;
    const data = res.data || res.result;
    if (!data || typeof data.fms_score !== 'number') return null;
    return {
      fms_score: Math.max(0, Math.min(3, Math.round(data.fms_score))),
      posture_quality: data.posture_quality || 'unknown',
      observed_issues: Array.isArray(data.observed_issues) ? data.observed_issues : [],
      coaching_tip: data.coaching_tip || '',
    };
  }
}

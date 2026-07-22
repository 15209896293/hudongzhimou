const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const crypto = require('crypto');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const pool = require('./db');
const { tokenAuth } = require('./middleware/auth');
const { generalLimiter, aiLimiter } = require('./middleware/rateLimit');
const { analyzeAction } = require('./services/aiAnalyzer');

const app = express();

app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '1mb' }));
app.use(generalLimiter);

// ========== 健康检查（无需认证） ==========
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ========== 注册接口 ==========
app.post('/api/register', async (req, res) => {
  try {
    const { username, password, nickname } = req.body;

    // 参数校验
    if (!username || !password) {
      return res.status(400).json({ success: false, error: '用户名和密码不能为空' });
    }
    if (username.length < 3 || username.length > 32) {
      return res.status(400).json({ success: false, error: '用户名长度需在3-32个字符之间' });
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      return res.status(400).json({ success: false, error: '用户名只能包含字母、数字和下划线' });
    }
    if (password.length < 6) {
      return res.status(400).json({ success: false, error: '密码长度不能少于6位' });
    }

    // 检查用户名是否已存在
    const [existing] = await pool.execute(
      'SELECT user_id FROM users WHERE username = ?',
      [username]
    );
    if (existing.length > 0) {
      return res.status(409).json({ success: false, error: '该用户名已被注册' });
    }

    // 加密密码
    const saltRounds = 10;
    const passwordHash = await bcrypt.hash(password, saltRounds);

    // 生成 user_id 和 token
    const userId = `user_${crypto.randomBytes(8).toString('hex')}`;
    const token = crypto.randomBytes(32).toString('hex');

    // 计算 token 过期时间
    const expireHours = parseInt(process.env.TOKEN_EXPIRE_HOURS) || 72;
    const expiresAt = new Date(Date.now() + expireHours * 3600 * 1000);

    // 存入数据库
    await pool.execute(
      `INSERT INTO users (user_id, username, password_hash, login_token, token_expires_at, nickname, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, NOW())`,
      [userId, username, passwordHash, token, expiresAt, nickname || username]
    );

    res.json({
      success: true,
      data: {
        user_id: userId,
        username: username,
        nickname: nickname || username,
        token: token
      }
    });
  } catch (err) {
    console.error('register error:', err.message);
    res.status(500).json({ success: false, error: '注册失败' });
  }
});

// ========== 登录接口 ==========
app.post('/api/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ success: false, error: '用户名和密码不能为空' });
    }

    // 查找用户
    const [rows] = await pool.execute(
      'SELECT user_id, username, nickname, password_hash, login_token FROM users WHERE username = ?',
      [username]
    );

    if (rows.length === 0) {
      return res.status(401).json({ success: false, error: '用户名或密码错误' });
    }

    const user = rows[0];

    // 验证密码
    const isValid = await bcrypt.compare(password, user.password_hash);
    if (!isValid) {
      return res.status(401).json({ success: false, error: '用户名或密码错误' });
    }

    // 生成新 token（每次登录都刷新）
    const newToken = crypto.randomBytes(32).toString('hex');

    // 计算 token 过期时间
    const expireHours = parseInt(process.env.TOKEN_EXPIRE_HOURS) || 72;
    const expiresAt = new Date(Date.now() + expireHours * 3600 * 1000);

    await pool.execute(
      'UPDATE users SET login_token = ?, token_expires_at = ? WHERE user_id = ?',
      [newToken, expiresAt, user.user_id]
    );

    res.json({
      success: true,
      data: {
        user_id: user.user_id,
        username: user.username,
        nickname: user.nickname || user.username,
        token: newToken
      }
    });
  } catch (err) {
    console.error('login error:', err.message);
    res.status(500).json({ success: false, error: '登录失败' });
  }
});

// ========== 登出接口（需要登录） ==========
app.post('/api/logout', tokenAuth, async (req, res) => {
  try {
    const userId = req.user.user_id;

    // 清空用户的 token 和过期时间
    await pool.execute(
      'UPDATE users SET login_token = NULL, token_expires_at = NULL WHERE user_id = ?',
      [userId]
    );

    res.json({ success: true });
  } catch (err) {
    console.error('logout error:', err.message);
    res.status(500).json({ success: false, error: '登出失败' });
  }
});

// ========== 更新用户档案（需要登录） ==========
app.post('/api/update_profile', tokenAuth, async (req, res) => {
  try {
    const { height, weight, age, injury_history, nickname } = req.body;
    const userId = req.user.user_id;

    await pool.execute(
      `UPDATE users SET
       height = ?, weight = ?, age = ?,
       injury_history = ?,
       nickname = COALESCE(?, nickname),
       updated_at = NOW()
       WHERE user_id = ?`,
      [height || null, weight || null, age || null,
       injury_history ? JSON.stringify(injury_history) : null,
       nickname || null, userId]
    );

    res.json({ success: true });
  } catch (err) {
    console.error('update_profile error:', err.message);
    res.status(500).json({ success: false, error: 'Database error' });
  }
});

// ========== 获取用户档案（需要登录） ==========
app.get('/api/get_profile', tokenAuth, async (req, res) => {
  try {
    const userId = req.user.user_id;

    const [rows] = await pool.execute(
      'SELECT user_id, username, nickname, height, weight, age, injury_history, updated_at FROM users WHERE user_id = ?',
      [userId]
    );

    if (rows.length === 0) {
      return res.json({ success: true, data: null });
    }

    const user = rows[0];
    res.json({
      success: true,
      data: {
        user_id: user.user_id,
        username: user.username,
        nickname: user.nickname,
        height: user.height,
        weight: user.weight,
        age: user.age,
        injury_history: user.injury_history ? (typeof user.injury_history === 'string' ? JSON.parse(user.injury_history) : user.injury_history) : [],
        updated_at: user.updated_at
      }
    });
  } catch (err) {
    console.error('get_profile error:', err.message);
    res.status(500).json({ success: false, error: 'Database error' });
  }
});

// ========== 保存训练记录（需要登录） ==========
app.post('/api/save_record', tokenAuth, async (req, res) => {
  try {
    const { exercise_type, count, duration_sec, safety_score, warning_count, joint_angles_json } = req.body;
    const userId = req.user.user_id;

    if (!exercise_type) {
      return res.status(400).json({ success: false, error: 'exercise_type is required' });
    }
    if (count === undefined || count === null || isNaN(Number(count)) || Number(count) < 0) {
      return res.status(400).json({ success: false, error: 'count must be a non-negative number' });
    }

    await pool.execute(
      `INSERT INTO training_records
       (user_id, exercise_type, count, duration_sec, safety_score, warning_count, joint_angles_json, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, NOW())`,
      [userId, exercise_type, Number(count), duration_sec || 0, 
       safety_score !== undefined ? Math.min(100, Math.max(0, safety_score)) : 100,
       warning_count || 0, joint_angles_json ? JSON.stringify(joint_angles_json) : '{}']
    );

    res.json({ success: true });
  } catch (err) {
    console.error('save_record error:', err.message);
    res.status(500).json({ success: false, error: 'Database error' });
  }
});

// ========== 获取历史记录（需要登录） ==========
app.get('/api/get_records', tokenAuth, async (req, res) => {
  try {
    const { limit = '30' } = req.query;
    const userId = req.user.user_id;
    const limitNum = Math.min(parseInt(limit) || 30, 100);

    const [rows] = await pool.execute(
      `SELECT id, exercise_type, count, duration_sec, safety_score,
              warning_count, joint_angles_json, created_at
       FROM training_records
       WHERE user_id = ?
       ORDER BY created_at DESC
       LIMIT ${limitNum}`,
      [userId]
    );

    res.json({ success: true, data: rows });
  } catch (err) {
    console.error('get_records error:', err.message);
    res.status(500).json({ success: false, error: 'Database error' });
  }
});

// ========== AI 动作分析（需要登录 + 单独限流） ==========
app.post('/api/analyze', tokenAuth, aiLimiter, async (req, res) => {
  try {
    const { action_name, joint_sequence, injury_history } = req.body;
    if (!action_name) {
      return res.status(400).json({ success: false, error: 'action_name is required' });
    }

    const aiResult = await analyzeAction(action_name, joint_sequence, injury_history);

    if (!aiResult.success) {
      return res.status(502).json({ success: false, error: aiResult.error, raw_text: aiResult.raw_text });
    }

    res.json({ success: true, result: aiResult.result });
  } catch (err) {
    console.error('analyze error:', err.message);
    res.status(500).json({ success: false, error: 'AI analysis failed' });
  }
});

// 全局错误处理
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err.message);
  res.status(500).json({ success: false, error: 'Internal server error' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
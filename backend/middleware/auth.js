const pool = require('../db');

/**
 * Token 认证中间件
 * 请求头中必须携带：Authorization: Bearer <token>
 * 验证通过后，将 user_id 和 username 挂载到 req.user 上
 * 同时校验 token 是否过期
 */
async function tokenAuth(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, error: 'Unauthorized: missing token' });
  }

  const token = authHeader.substring(7); // 去掉 "Bearer "

  // 验证 token 格式（64位十六进制字符串）
  if (!token || token.length !== 64 || !/^[a-f0-9]{64}$/.test(token)) {
    return res.status(401).json({ success: false, error: 'Unauthorized: invalid token format' });
  }

  try {
    // 同时校验 token 有效性和过期时间
    const [rows] = await pool.execute(
      'SELECT user_id, username, nickname FROM users WHERE login_token = ? AND (token_expires_at IS NULL OR token_expires_at > NOW())',
      [token]
    );

    if (rows.length === 0) {
      return res.status(401).json({ success: false, error: 'Token已过期或无效，请重新登录' });
    }

    req.user = {
      user_id: rows[0].user_id,
      username: rows[0].username,
      nickname: rows[0].nickname
    };

    next();
  } catch (err) {
    console.error('tokenAuth error:', err.message);
    res.status(500).json({ success: false, error: 'Authentication error' });
  }
}

module.exports = { tokenAuth };

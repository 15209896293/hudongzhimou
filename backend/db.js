const mysql = require('mysql2/promise');
require('dotenv').config();

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'hudongzhimou',
  port: parseInt(process.env.DB_PORT || '3306'),
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 0
});

// 标记数据库是否可用（降级模式：连接失败不退出，仅标记不可用）
pool.dbAvailable = false;

pool.getConnection()
  .then(conn => {
    console.log('MySQL connected successfully');
    pool.dbAvailable = true;
    conn.release();
  })
  .catch(err => {
    console.warn('[WARN] MySQL connection failed:', err.message);
    console.warn('[WARN] Running in degraded mode — DB features unavailable until MySQL is online.');
  });

module.exports = pool;
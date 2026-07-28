/**
 * 前端运行时配置
 *
 * 部署到 Cloudflare Pages 或其他静态托管时：
 *   1. 复制本文件为 config.local.js
 *   2. 修改 BACKEND_URL 为你的后端服务器地址（含 https://）
 *   3. 上传整个 web-app/ 目录到 Cloudflare Pages
 *
 * 本地开发（后端同源托管）时无需修改，自动使用相对路径 /api
 */
window.HDZM_CONFIG = {
  // 后端 API 地址
  // 'auto'  → 自动判断：同源用 /api，跨域用 localhost:3000（本地开发）
  // 字符串  → 直接使用该地址（如 'https://api.example.com/api'）
  BACKEND_URL: 'auto',
};

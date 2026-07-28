# 护动智眸 — 运动健身防伤评估系统

基于浏览器实时姿态识别（MediaPipe）的运动健身防伤评估系统，以 FMS（功能性运动筛查）为核心。

## 快速开始

```bash
# Windows 双击 start.bat 或在项目根目录执行：
start.bat
```

启动后访问 **http://localhost:3000**

## 项目结构

| 目录 | 说明 |
|------|------|
| `web-app/` | Web 前端（HTML + CSS + JS ES Modules） |
| `backend/` | Node.js 后端（Express + MySQL） |
| `legacy-desktop/` | 旧版 PyQt5 桌面端（仅参考，不可修改） |
| `design/` | 设计资源与方案文档 |
| `docs/` | 项目文档 |

## 环境要求

- Node.js 18+
- MySQL 8.0+（可选，后端支持降级模式）
- 支持摄像头的现代浏览器（Chrome/Edge 推荐）

## 详细文档

请阅读 [交接手册](handover-manual.html) 了解完整的项目架构、API 文档和开发指南。

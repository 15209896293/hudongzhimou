-- 护动智眸数据库初始化脚本
-- 使用方法：mysql -u root -p hudongzhimou < init.sql

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS hudongzhimou CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE hudongzhimou;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  user_id VARCHAR(64) PRIMARY KEY,
  username VARCHAR(32) UNIQUE,
  password_hash VARCHAR(255),
  login_token VARCHAR(128),
  token_expires_at DATETIME,
  nickname VARCHAR(64),
  height INT,
  weight INT,
  age INT,
  injury_history JSON,
  updated_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 训练记录表
CREATE TABLE IF NOT EXISTS training_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id VARCHAR(64),
  exercise_type VARCHAR(32) NOT NULL,
  count INT NOT NULL,
  duration_sec INT DEFAULT 0,
  safety_score INT DEFAULT 100,
  warning_count INT DEFAULT 0,
  joint_angles_json TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_time (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 官方动作表
CREATE TABLE IF NOT EXISTS official_actions (
  action_id VARCHAR(32) PRIMARY KEY,
  name VARCHAR(64),
  category VARCHAR(32),
  version INT DEFAULT 1,
  video_url VARCHAR(256),
  skeleton_labels JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 兼容已有数据库：为 users 表添加 token_expires_at 字段（如果不存在）
-- 使用存储过程安全添加列，避免列已存在时报错
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS add_token_expires_at_column()
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'hudongzhimou'
      AND TABLE_NAME = 'users'
      AND COLUMN_NAME = 'token_expires_at'
  ) THEN
    ALTER TABLE users ADD COLUMN token_expires_at DATETIME AFTER login_token;
  END IF;
END //
DELIMITER ;
CALL add_token_expires_at_column();
DROP PROCEDURE IF EXISTS add_token_expires_at_column;
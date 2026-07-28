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
  gender ENUM('male', 'female', '') DEFAULT '',
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
  exercise_name VARCHAR(64),
  category VARCHAR(32),
  count INT NOT NULL,
  duration_sec INT DEFAULT 0,
  safety_score INT DEFAULT 100,
  avg_quality INT DEFAULT 0,
  quality_history JSON,
  safety_event_count INT DEFAULT 0,
  danger_count INT DEFAULT 0,
  warning_count INT DEFAULT 0,
  safety_events JSON,
  fatigue_warnings JSON,
  is_fatigued BOOLEAN DEFAULT FALSE,
  joint_angles_json TEXT,
  end_time DATETIME,
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

-- 兼容已有数据库：为 users 表添加 gender 字段
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS add_gender_column()
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'hudongzhimou'
      AND TABLE_NAME = 'users'
      AND COLUMN_NAME = 'gender'
  ) THEN
    ALTER TABLE users ADD COLUMN gender ENUM('male', 'female', '') DEFAULT '' AFTER nickname;
  END IF;
END //
DELIMITER ;
CALL add_gender_column();
DROP PROCEDURE IF EXISTS add_gender_column;

-- 兼容已有数据库：为 training_records 表添加新字段
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS add_training_records_columns()
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'hudongzhimou'
      AND TABLE_NAME = 'training_records'
      AND COLUMN_NAME = 'exercise_name'
  ) THEN
    ALTER TABLE training_records
      ADD COLUMN exercise_name VARCHAR(64) AFTER exercise_type,
      ADD COLUMN category VARCHAR(32) AFTER exercise_name,
      ADD COLUMN avg_quality INT DEFAULT 0 AFTER safety_score,
      ADD COLUMN quality_history JSON AFTER avg_quality,
      ADD COLUMN safety_event_count INT DEFAULT 0 AFTER quality_history,
      ADD COLUMN danger_count INT DEFAULT 0 AFTER safety_event_count,
      ADD COLUMN safety_events JSON AFTER danger_count,
      ADD COLUMN fatigue_warnings JSON AFTER safety_events,
      ADD COLUMN is_fatigued BOOLEAN DEFAULT FALSE AFTER fatigue_warnings,
      ADD COLUMN end_time DATETIME AFTER joint_angles_json;
  END IF;
END //
DELIMITER ;
CALL add_training_records_columns();
DROP PROCEDURE IF EXISTS add_training_records_columns;

-- FMS 评分记录表（新增）
-- user_id 为 VARCHAR(64)，与 users.user_id 一致（非自增 INT）
CREATE TABLE IF NOT EXISTS fms_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  test_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  deep_squat TINYINT DEFAULT 0,
  hurdle_step TINYINT DEFAULT 0,
  inline_lunge TINYINT DEFAULT 0,
  shoulder_mobility TINYINT DEFAULT 0,
  aslr TINYINT DEFAULT 0,
  trunk_stability TINYINT DEFAULT 0,
  rotary_stability TINYINT DEFAULT 0,
  total_score INT DEFAULT 0,
  asymmetry_flags JSON,
  ai_analysis TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_time (user_id, test_date),
  CONSTRAINT fk_fms_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
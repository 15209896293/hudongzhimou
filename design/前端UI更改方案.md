# 护动智眸 PyQt5 前端 UI 迁移指南

> 本文档为从当前深色主题迁移到 Apple Health 风格浅色主题的完整技术指南。  
> 所有修改仅涉及视觉层（QSS 样式 + 布局参数），**不改动业务逻辑和信号连接**。

---

## 1. 概述

### 1.1 当前问题总结

| 问题 | 描述 |
|------|------|
| 深色主题不适合投影 | 纯黑背景 `#000000` 在投影仪上过于刺眼，远距离观看对比度过强 |
| 布局紧凑 | 右侧 520px 内堆叠安全面板 + 计数器 + 设置 + 开关 + 按钮 + 用户档案，信息密度过高 |
| 控件重叠 | 窗口缩小或不同分辨率下，间距不足导致控件挤在一起 |
| 产品感不足 | 深色主题容易看起来像「科研 Demo」，缺乏正式产品的视觉质感 |
| 安全面板占用过多空间 | 包含统计行和大量信息，核心安全提示不够突出 |

### 1.2 目标效果描述

迁移到 **Apple Health 风格浅色主题**，具体目标：

- **浅色背景** `#F5F5F7`，投影仪友好，远距离可读性佳
- **白色卡片 + 轻微阴影**，层次分明，不依赖边框
- **视频区占 70% 宽度**，核心信息优先
- **计数器放大至 56pt**，超轻字重，高辨识度
- **安全消息改为聊天气泡样式**，更有亲和力
- **用户档案改为侧边抽屉**，默认隐藏，减少右侧面板压力
- **顶部导航栏** 替代传统菜单栏，更现代化

### 1.3 参考原型文件

目标设计 HTML 原型可直接在浏览器中打开查看效果：

```
traedesign/hudong-smart-eyes/pages/training.html   -- 运动训练模式
traedesign/hudong-smart-eyes/pages/stats.html      -- 统计分析模式
```

> **开发时建议**：在浏览器中打开上述 HTML 文件作为视觉参考，对比 PyQt5 实际渲染效果进行微调。

---

## 2. 色彩迁移对照表

### 2.1 背景色

| 用途 | 当前值 | 新值 | 说明 |
|------|--------|------|------|
| 页面主背景 | `#000000` | `#F5F5F7` | Apple 式浅灰白，不是纯白 |
| 中央部件背景 | `#000000` (hardcoded in main_window) | `#F5F5F7` | `central_widget.setStyleSheet` 中的硬编码色 |
| 状态栏背景 | `#1C1C1E` | `#FFFFFF` | 状态栏改为白色卡片风格 |

### 2.2 卡片/表面色

| 用途 | 当前值 | 新值 | 说明 |
|------|--------|------|------|
| 卡片背景 | `#1C1C1E` | `#FFFFFF` | 纯白卡片，配合阴影 |
| 表面/输入框背景 | `#2C2C2E` | `#FFFFFF` | 输入框、下拉框内部背景 |
| 嵌套表面 | `#38383A` | `#F0F0F5` | 按钮底色、聊天气泡背景 |
| 按下/激活表面 | `#48484A` | `#EFEFF4` | 禁用状态的替代底色 |
| Tab 面板背景 | `#000000` | `#F5F5F7` | TabWidget pane 背景 |

### 2.3 文字色

| 用途 | 当前值 | 新值 | 说明 |
|------|--------|------|------|
| 主文字 | `#FFFFFF` | `#1D1D1F` | 近黑，不是纯黑 |
| 次要文字 | `#8E8E93` | `#86868B` | 灰色辅助文字 |
| 三级文字 | `#636366` | `#AEAEB2` | 更浅的灰，用于 placeholder |
| 禁用文字 | `#636366` | `#AEAEB2` | 禁用状态文字 |
| 反色文字（按钮上） | `#000000` | `#FFFFFF` | 彩色按钮上的白色文字 |
| 计数器大数字 | `#FFFFFF` / 运动色 | `#1D1D1F` | 大数字用深色 |
| 成功计数器 | `#34C759` | `#34C759` | 保留不变 |

### 2.4 边框色

| 用途 | 当前值 | 新值 | 说明 |
|------|--------|------|------|
| 通用边框 | `#38383A` | `#E5E5EA` | 极浅灰边框 |
| 分隔线 | `#38383A` | `#D2D2D7` | 浅灰分隔 |
| 分割线 (divider) | `#38383A` | `#E5E5EA` | 垂直分割线 |

### 2.5 语义状态色

| 用途 | 当前值 | 新值 | 说明 |
|------|--------|------|------|
| 安全/成功 | `#34C759` | `#34C759` | 保留不变 |
| 品牌/安全（品牌色） | `#34C759` | `#34C759` | 保留不变 |
| 警告 | `#FF9500` | `#FF9F0A` | 微调，更偏橙黄 |
| 危险/错误 | `#FF3B30` | `#FF453A` | 微调，更柔和 |
| 强调/确认 | `#0A84FF` | `#007AFF` | 更换为标准 iOS 蓝 |
| 信息 | `#0A84FF` | `#007AFF` | 同上 |

### 2.6 运动专属色

| 运动 | 当前值 | 新值 | 说明 |
|------|--------|------|------|
| 深蹲 | `#34C759` | `#34C759` | 保留 |
| 俯卧撑 | `#FF3B30` | `#FF453A` | 同步到新危险色 |
| 仰卧起坐 | `#0A84FF` | `#007AFF` | 同步到新蓝色 |
| 二头弯举 | `#FF9500` | `#FF9F0A` | 同步到新警告色 |
| 三头臂屈伸 | `#FF9500` | `#FF9F0A` | 同步到新警告色 |
| 侧平举 | `#AF52DE` | `#AF52DE` | 保留 |
| 颈前推举 | `#5AC8FA` | `#5AC8FA` | 保留 |
| 左右交替抬腿 | `#FFCC00` | `#FFCC00` | 保留 |
| 高抬腿 | `#30D158` | `#30D158` | 保留 |
| 提膝下压 | `#AF52DE` | `#AF52DE` | 保留 |

> **注意**：由于运动色用于计数器大数字和 Phase Indicator 的背景，在浅色背景上直接作为文字颜色依然清晰可辨。但需将 `#FF3B30` -> `#FF453A`、`#0A84FF` -> `#007AFF`、`#FF9500` -> `#FF9F0A` 的变更同步到 `EXERCISE_COLORS` 字典。

### 2.7 语义色（半透明背景）

| 用途 | 当前值 | 新值 | 说明 |
|------|--------|------|------|
| 安全 badge 背景 | `rgba(52,199,89,0.15)` | `rgba(52,199,89,0.10)` | 降低不透明度 |
| 警告 badge 背景 | `rgba(255,149,0,0.15)` | `rgba(255,159,10,0.10)` | 降低不透明度 |
| 危险 badge 背景 | `rgba(255,59,48,0.15)` | `rgba(255,69,58,0.10)` | 降低不透明度 |
| overlay pill 背景 | `rgba(0,0,0,0.6)` | `rgba(255,255,255,0.8)` | FPS pill 改为白色半透明 |

---

## 3. 字体规范

### 3.1 字体族

| 用途 | 当前 | 新值 |
|------|------|------|
| 全局字体 | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` | `'Inter', 'PingFang SC', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` |

> 变更：增加 `'PingFang SC'` 和 `'Noto Sans SC'` 以改善中文字体渲染。

### 3.2 字号映射

| 用途 | 当前 | 新值 | 变化 |
|------|------|------|------|
| 计数器大数字 | 48pt | 56pt | 增大，配合 font-weight: 200 |
| 角度数值 | 36pt | 36pt | 保持不变 |
| 面板标题 | 20px | 17px | 缩小，与 section title 合并 |
| section caption | 13px | 13px | 保持 |
| 正文/下拉框 | 15px | 15px | 保持 |
| 按钮文字 | 15px | 15px | 保持 |
| 统计数字 | -- | 48px | 新增用于统计面板 |
| 状态文字 (stage) | 16px | 16px | 保持 |
| Phase indicator | 14px | 14px | 保持 |
| 状态标签 (status badge) | 13px | 13px | 保持 |
| 辅助信息 (caption) | 12px | 13px | 微调 |
| 状态栏 | 13px | 11px | 缩小 |

### 3.3 字重映射

| 用途 | 当前 | 新值 | 变化 |
|------|------|------|------|
| 计数器大数字 | 300 (light) | 200 (extra-light) | 更轻，Apple Health 风格 |
| 角度数值 | 300 | 200 | 同上 |
| 标题 | 600 | 600 | 保持 |
| 正文 | 400 | 400 | 保持 |
| caption | 500 | 500 | 保持 |
| 按钮 | 600 | 600 | 保持 |
| 统计数字 | -- | 200 | 新增 |

### 3.4 字距

| 用途 | 当前 | 新值 |
|------|------|------|
| 计数器大数字 | 无 (0px) | -2px (`letter-spacing: -2px`) |
| section caption | 0.5px | 0.5px |
| 计数标签 | 无 | 0.5px + uppercase |
| 标题 | 1px | 0px |

---

## 4. 圆角规范

| 组件 | 当前值 | 新值 | 说明 |
|------|--------|------|------|
| 卡片 | 16px | 20px | 更大更精致 |
| 视频/图像区域 | 24px | 20px | 与卡片统一 |
| 按钮 | 12px | 12px | 保持不变 |
| 输入框/下拉框 | 12px / 10px | 12px | 统一为 12px |
| Phase indicator pill | 100px | 100px | 保持 |
| 状态 badge | 100px | 100px | 保持 |
| checkbox indicator | 6px | 6px | 保持 |
| checkbox 容器 | 100px | 100px | 保持 |
| ToggleSwitch 滑块 | 14px (drawRoundedRect) | 13px | 微调 |
| ToggleSwitch 容器 | 14px | 13px | 微调 |
| 进度条 | 4px | 4px | 保持 |
| 滚动条 | 3px | 3px | 保持 |
| 聊天气泡 | 10px | 12px | 增大 |

---

## 5. 间距规范

| 位置 | 当前 | 新值 | 说明 |
|------|------|------|------|
| 页面外边距 | 16px | 24px | 更宽松（主布局 margins） |
| 卡片间距 | 12px | 12px | 保持 |
| 卡片内边距 (counter) | 16px | 20px~32px | 计数器卡片更宽松 |
| 卡片内边距 (safety) | 16px, 12px | 16px | 保持 |
| 卡片内边距 (settings) | 16px, 12px | 12px | 紧凑化 |
| 卡片内边距 (toggles) | 16px, 12px | 12px | 紧凑化 |
| 卡片内边距 (actions) | 16px, 12px | 12px | 紧凑化 |
| 元素间距 | 12px | 12px | 保持 |
| 紧凑元素间距 | 8px | 8px | 保持 |
| Grid 水平间距 | 16px | 16px | 保持 |
| 下拉框 padding | 8px 12px | 8px 12px | 保持 |

---

## 6. 阴影规范

### 6.1 当前方案

当前代码 **无阴影**，所有层级关系通过不同深度的背景色 + 1px 边框来区分：

```python
# 卡片样式 - 当前
f"""
    background-color: #1C1C1E;   # 深色卡片
    border-radius: 16px;
    padding: 16px;
    /* 无 border，无 shadow */
"""
```

```python
# 输入框 - 当前
"""
    background-color: #2C2C2E;
    border: 1px solid #38383A;   # 1px 边框
    border-radius: 12px;
"""
```

### 6.2 新方案

改为 **轻微阴影 + 无边框（或极浅边框）**，更符合 Apple 设计语言。

由于 QSS 不直接支持 `box-shadow`，需通过以下方式模拟：

**方案 A：使用 QGraphicsDropShadowEffect（推荐）**

```python
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QGraphicsEffect
from PyQt5.QtGui import QColor

def apply_card_shadow(widget):
    """给卡片 widget 添加轻微阴影"""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setOffset(0, 1)
    shadow.setBlurRadius(4)
    shadow.setColor(QColor(0, 0, 0, 15))   # rgba(0,0,0,0.06) 约 15/255
    widget.setGraphicsEffect(shadow)
```

**方案 B：使用 QSS 代理边框模拟（简单但效果略差）**

```python
# 浅色卡片 - QSS
"""
    background-color: #FFFFFF;
    border-radius: 20px;
    padding: 16px;
    border: 1px solid rgba(0, 0, 0, 0.04);   # 极淡边框模拟阴影
"""
```

> **建议**：使用方案 A（QGraphicsDropShadowEffect），效果更好。在 `_create_card()` 方法中统一添加。

### 6.3 阴影参数对照

| 用途 | 当前 | 新值 (QGraphicsDropShadowEffect) |
|------|------|------|
| 卡片阴影 | 无 | offset(0,1), blur=4, color=rgba(0,0,0,0.05) |
| 浮起元素 | 无 | offset(0,4), blur=12, color=rgba(0,0,0,0.08) |
| ToggleSwitch 滑块 | 无 | offset(0,1), blur=3, color=rgba(0,0,0,0.15) |
| 边框 | 1px solid #38383A | 1px solid #E5E5EA 或无 |

---

## 7. 逐文件修改清单

### 7.1 `ui/styles.py` -- 核心样式系统重写

**优先级**：P0（必须最先修改，其他所有文件依赖此文件的样式方法）

#### 修改 1：全局色彩常量

```python
# 当前
class AppStyles:
    BG = "#000000"
    CARD = "#1C1C1E"
    SURFACE = "#2C2C2E"
    TEXT = "#FFFFFF"
    TEXT2 = "#8E8E93"
    TEXT3 = "#636366"
    BORDER = "#38383A"
    GREEN = "#34C759"
    ORANGE = "#FF9500"
    RED = "#FF3B30"
    BLUE = "#0A84FF"

# 新值
class AppStyles:
    BG = "#F5F5F7"
    CARD = "#FFFFFF"
    SURFACE = "#FFFFFF"          # 输入框/下拉框用白底
    SURFACE_SUNKEN = "#EFEFF4"   # 新增：按下/禁用底色
    SURFACE_INSET = "#F0F0F5"    # 新增：嵌套表面，聊天气泡背景
    TEXT = "#1D1D1F"
    TEXT2 = "#86868B"
    TEXT3 = "#AEAEB2"
    BORDER = "#E5E5EA"
    SEPARATOR = "#D2D2D7"        # 新增：分隔线色
    GREEN = "#34C759"
    ORANGE = "#FF9F0A"           # 微调
    RED = "#FF453A"              # 微调
    BLUE = "#007AFF"              # 更换
    BRAND = "#34C759"             # 新增：品牌色（与安全色统一）
```

#### 修改 2：`EXERCISE_COLORS` 字典同步

将字典中的 `#FF3B30` -> `#FF453A`、`#0A84FF` -> `#007AFF`、`#FF9500` -> `#FF9F0A` 同步更新（对应俯卧撑、仰卧起坐、二头弯举等运动）。

#### 修改 3：`get_window_palette()` 方法

```python
# 当前
palette.setColor(QPalette.Window, QColor("#000000"))
palette.setColor(QPalette.Base, QColor("#2C2C2E"))
palette.setColor(QPalette.Text, QColor("#FFFFFF"))
# ...

# 新值
palette.setColor(QPalette.Window, QColor("#F5F5F7"))
palette.setColor(QPalette.WindowText, QColor("#1D1D1F"))
palette.setColor(QPalette.Base, QColor("#FFFFFF"))
palette.setColor(QPalette.AlternateBase, QColor("#F0F0F5"))
palette.setColor(QPalette.Text, QColor("#1D1D1F"))
palette.setColor(QPalette.Button, QColor("#F0F0F5"))
palette.setColor(QPalette.ButtonText, QColor("#1D1D1F"))
```

#### 修改 4：`get_global_stylesheet()` 方法

```python
# 当前全局样式中关键颜色
QWidget { color: #FFFFFF; background-color: #000000; }
QComboBox { border: 1px solid #38383A; background-color: #2C2C2E; color: #FFFFFF; }
QLabel { color: #FFFFFF; }

# 新值
QWidget { color: #1D1D1F; background-color: #F5F5F7; }
QComboBox { border: 1px solid #E5E5EA; background-color: #FFFFFF; color: #1D1D1F; }
QLabel { color: #1D1D1F; }
QCheckBox::indicator { border: 1px solid #E5E5EA; background-color: #FFFFFF; }
QCheckBox::indicator:checked { background-color: #34C759; border-color: #34C759; }
QGroupBox::title { color: #86868B; }
```

#### 修改 5：`get_counter_value_style()` 方法

```python
# 当前
font-size: 48pt; font-weight: 300;

# 新值
font-size: 56pt; font-weight: 200; letter-spacing: -2px;
```

#### 修改 6：`get_success_counter_style()` 方法

```python
# 当前
color: #34C759; font-size: 48pt; font-weight: 300;

# 新值
color: #34C759; font-size: 56pt; font-weight: 200; letter-spacing: -2px;
```

#### 修改 7：`get_angle_value_style()` 方法

```python
# 当前
background-color: #2C2C2E; font-size: 36pt; font-weight: 300;

# 新值
background-color: #FFFFFF; border: 1px solid #E5E5EA;
font-size: 36pt; font-weight: 200;
```

#### 修改 8：`get_phase_indicator_style()` 方法

```python
# 当前
bg_color = color if active else "#2C2C2E"
text_color = "#000000" if active else "#8E8E93"
border_color = "none" if active else "#38383A"

# 新值
bg_color = color if active else "#F0F0F5"
text_color = "#FFFFFF" if active else "#86868B"   # active 背景为彩色时，文字为白色
border_color = "none" if active else "#E5E5EA"
```

#### 修改 9：所有按钮样式方法

需要修改的方法列表（全部 P0）：

| 方法名 | 主要变更 |
|--------|---------|
| `get_increase_button_style()` | 背景 `#34C759` -> `rgba(52,199,89,0.1)`, 文字 `#000000` -> `#34C759`（浅底绿字风格）|
| `get_decrease_button_style()` | 背景 `#FF9500` -> `rgba(255,159,10,0.1)`, 文字 `#000000` -> `#FF9F0A`（浅底橙字风格）|
| `get_reset_button_style()` | 背景 `#2C2C2E` -> `#F0F0F5`, 文字 `#FFFFFF` -> `#1D1D1F` |
| `get_confirm_button_style()` | 背景 `#0A84FF` -> `#007AFF`, 文字保持白色 |
| `get_success_button_style()` | 保留绿色，文字保持白色 |
| `get_primary_button_style()` | 背景 `#0A84FF` -> `#007AFF`, 文字 `#FFFFFF` -> `#FFFFFF`（当前已是白色则保持）|
| `get_secondary_button_style()` | 背景 `#2C2C2E` -> `#F0F0F5`, 文字 `#FFFFFF` -> `#1D1D1F`, 边框 `#38383A` -> `#E5E5EA` |
| `get_counter_button_style()` | increase: `rgba(52,199,89,0.1)` 底 + `#34C759` 字; decrease: `rgba(255,159,10,0.1)` 底 + `#FF9F0A` 字 |
| `get_toggle_button_style()` | on: `#34C759`; off: `#E5E5EA`（替代 `#636366`）|
| disabled 态 | 背景 `#38383A` -> `#EFEFF4`, 文字 `#636366` -> `#AEAEB2` |

**QSS 片段示例 - 增加按钮新样式：**

```css
/* 新的浅色增加按钮 */
QPushButton {
    background-color: rgba(52, 199, 89, 0.1);
    color: #34C759;
    border-radius: 12px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 15px;
    border: none;
    min-height: 40px;
}
QPushButton:hover {
    background-color: rgba(52, 199, 89, 0.2);
}
```

#### 修改 10：`get_card_style()` 方法

```python
# 当前
f"""
    background-color: #1C1C1E;
    border-radius: 16px;
    padding: 16px;
"""

# 新值
f"""
    background-color: #FFFFFF;
    border-radius: 20px;
    padding: 16px;
    /* 阴影通过 QGraphicsDropShadowEffect 添加，不在 QSS 中 */
"""
```

> 配合 `QGraphicsDropShadowEffect` 使用（见第 6 节）。

#### 修改 11：`get_section_title_style()` / `get_caption_style()`

```python
# 当前
color: #8E8E93;

# 新值
color: #86868B;
```

#### 修改 12：`get_status_badge_style()` 方法

```python
# 当前
{"bg": "rgba(52, 199, 89, 0.15)", "text": "#34C759"},
{"bg": "rgba(255, 149, 0, 0.15)", "text": "#FF9500"},
{"bg": "rgba(255, 59, 48, 0.15)", "text": "#FF3B30"},

# 新值
{"bg": "rgba(52, 199, 89, 0.10)", "text": "#34C759"},
{"bg": "rgba(255, 159, 10, 0.10)", "text": "#FF9F0A"},
{"bg": "rgba(255, 69, 58, 0.10)", "text": "#FF453A"},
```

#### 修改 13：`get_dark_input_style()` -> `get_light_input_style()`

建议将方法名改为 `get_input_style()`，颜色全面更新：

```python
# 当前
background-color: #2C2C2E; color: #FFFFFF; border: 1px solid #38383A;
focus: border-color: #34C759;

# 新值
background-color: #FFFFFF; color: #1D1D1F; border: 1px solid #E5E5EA;
focus: border-color: #007AFF;
```

#### 修改 14：`get_scrollbar_style()` 方法

```python
# 当前
QScrollBar:vertical { background-color: #000000; }
QScrollBar::handle:vertical { background-color: #636366; }
hover: background-color: #8E8E93;

# 新值
QScrollBar:vertical { background-color: #F0F0F5; }
QScrollBar::handle:vertical { background-color: #AEAEB2; }
QScrollBar::handle:vertical:hover { background-color: #86868B; }
```

#### 修改 15：`get_table_style()` 方法

```python
# 当前
QTableWidget { background-color: #000000; color: #FFFFFF; }
QTableWidget::item:alternate { background-color: #1C1C1E; }
QHeaderView::section { background-color: #2C2C2E; color: #FFFFFF; }

# 新值
QTableWidget { background-color: #FFFFFF; color: #1D1D1F; gridline-color: #F0F0F5; }
QTableWidget::item:alternate { background-color: #F5F5F7; }
QHeaderView::section { background-color: #F0F0F5; color: #1D1D1F; }
```

#### 修改 16：`get_progressbar_style()` 方法

```python
# 当前
background-color: #2C2C2E;

# 新值
background-color: #E5E5EA;
```

#### 修改 17：`get_tab_widget_style()` 方法

```python
# 当前
QTabWidget::pane { background-color: #000000; }
QTabBar::tab:selected { background-color: #FFFFFF; color: #000000; }
QTabBar::tab:hover:!selected { color: #FFFFFF; }

# 新值
QTabWidget::pane { background-color: #F5F5F7; }
QTabBar::tab { color: #86868B; }  /* 仍然是 #86868B */
QTabBar::tab:selected { background-color: #FFFFFF; color: #1D1D1F; }
QTabBar::tab:hover:!selected { color: #1D1D1F; }
```

#### 修改 18：`get_statusbar_style()` 方法

```python
# 当前
background-color: #1C1C1E; color: #8E8E93;

# 新值
background-color: #FFFFFF; color: #AEAEB2; border-top: 1px solid #E5E5EA;
```

#### 修改 19：新增方法

```python
@staticmethod
def get_safety_gradient_bar_style():
    """视频底部安全状态渐变条"""
    return """
        QWidget {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #34C759,
                stop:0.5 #FF9F0A,
                stop:1 #FF453A
            );
            border: none;
            border-radius: 0px;
        }
    """

@staticmethod
def get_chat_bubble_style(border_color="#34C759"):
    """聊天气泡样式的安全消息"""
    return f"""
        QLabel {{
            padding: 12px 16px;
            background-color: #F0F0F5;
            border-radius: 12px;
            font-size: 15px;
            color: #1D1D1F;
            border-left: 3px solid {border_color};
        }}
    """

@staticmethod
def get_nav_bar_style():
    """顶部导航栏样式"""
    return """
        QWidget {
            background-color: #FFFFFF;
            border-bottom: 1px solid #E5E5EA;
        }
    """

@staticmethod
def get_score_badge_style():
    """视频右上角评分圆环"""
    return """
        QWidget {
            background-color: rgba(255, 255, 255, 0.9);
            border: 2px solid #34C759;
            border-radius: 36px;
        }
    """

@staticmethod
def get_drawer_style():
    """用户档案侧边抽屉"""
    return """
        QWidget {
            background-color: #FFFFFF;
            border-left: 1px solid #E5E5EA;
        }
    """
```

---

### 7.2 `app/main_window.py` -- 主窗口布局

**优先级**：P0

#### 修改 1：布局比例变更

```python
# 当前 (setup_ui 方法)
main_layout.addWidget(left_widget, 6)     # 左侧 60%
main_layout.addWidget(right_widget, 4)    # 右侧 40%

# 新值
main_layout.addWidget(left_widget, 7)     # 左侧 70%
main_layout.addWidget(right_widget, 3)    # 右侧 30%
```

#### 修改 2：右侧面板最大宽度

```python
# 当前
right_widget.setMaximumWidth(520)

# 新值
right_widget.setMaximumWidth(400)
```

#### 修改 3：页面外边距

```python
# 当前
main_layout.setContentsMargins(16, 16, 16, 16)

# 新值（顶部留给导航栏，左右下留 24px）
main_layout.setContentsMargins(24, 76, 24, 24)
# 顶部 76px = 52px 导航栏高度 + 24px 间距
```

#### 修改 4：中央部件背景色

```python
# 当前
central_widget.setStyleSheet("background-color: #000000;")

# 新值
central_widget.setStyleSheet("background-color: #F5F5F7;")
```

#### 修改 5：新增顶部导航栏（P1）

在 `setup_ui()` 中，在创建中央部件后、主布局前，添加导航栏组件：

```python
# 新增：顶部导航栏
self.nav_bar = QWidget(self)
self.nav_bar.setFixedHeight(52)
self.nav_bar.move(0, 0)
# 导航栏内容：左侧品牌 logo + 中间 Tab Pills + 右侧用户头像/设置
# 具体 UI 构建可封装到独立方法 _setup_nav_bar() 中
```

> 导航栏的实现需要新增一个 `TopNavBar` 组件类（可放在 `ui/widgets/` 下或直接写在 main_window 中）。

#### 修改 6：右侧面板添加滚动支持（P1）

```python
# 当前
right_layout = QVBoxLayout(right_widget)

# 新值：将 right_layout 包在 QScrollArea 中
from PyQt5.QtWidgets import QScrollArea
scroll = QScrollArea()
scroll.setWidgetResizable(True)
scroll.setFrameShape(QFrame.NoFrame)
scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
# 将 right_widget 的内容放入 scroll
```

#### 修改 7：用户档案面板从右侧面板移除

```python
# 当前：在 right_layout 中添加
right_layout.addWidget(self.user_profile_panel)

# 新值：不在 right_layout 中添加
# 改为通过导航栏的用户头像按钮触发 Drawer
```

---

### 7.3 `ui/control_panel.py` -- 控制面板

**优先级**：P0

#### 修改 1：`_create_card()` 方法添加阴影

```python
def _create_card(self):
    card = QWidget()
    card.setStyleSheet(AppStyles.get_card_style())
    # 新增：添加阴影
    from PyQt5.QtWidgets import QGraphicsDropShadowEffect
    shadow = QGraphicsDropShadowEffect(card)
    shadow.setOffset(0, 1)
    shadow.setBlurRadius(4)
    shadow.setColor(QColor(0, 0, 0, 15))
    card.setGraphicsEffect(shadow)
    return card
```

#### 修改 2：面板标题移除

```python
# 当前：在 setup_ui() 中显示面板标题
self.title_label = QLabel(T.get("app_title"))
self.title_label.setAlignment(Qt.AlignCenter)
self.title_label.setStyleSheet(AppStyles.get_panel_title_style())
self.layout.addWidget(self.title_label)

# 新值：移除面板标题
# 标题已在顶部导航栏中显示，右侧面板无需重复
```

#### 修改 3：计数器卡片字号更新

```python
# 当前 (_setup_counter_card)
self.counter_value.setStyleSheet(AppStyles.get_counter_value_style())
# 默认 font-size: 48pt

# 新值：styles.py 中已更新为 56pt，此处无需改代码
# 但 update_counter_style() 中传入的默认颜色需更新：
self.counter_value.setStyleSheet(AppStyles.get_counter_value_style("#1D1D1F"))
# 默认数字颜色从白色改为深色
```

#### 修改 4：计数器布局调整为居中大数字

参考 HTML 原型，计数器卡片应该：
- 大数字居中显示
- 上下各有一个小箭头符号（纯装饰）
- 下方是 "已完成" 标签
- Phase indicator 改为更紧凑的行内样式

```python
# 当前：左侧计数器 + 分隔线 + 右侧 Phase
# 新值：居中布局
# ┌────────────────────────┐
# │          ↑             │
# │        0 (56pt)         │
# │          ↓             │
# │       已完成            │
# │      准备开始           │
# └────────────────────────┘
```

> 布局从 `QHBoxLayout`（左右分割）改为 `QVBoxLayout`（上下居中），Phase indicator 改为更紧凑的行内显示。

#### 修改 5：设置卡片紧凑化

```python
# 当前 (_setup_settings_card)
layout.setContentsMargins(16, 12, 16, 12)

# 新值
layout.setContentsMargins(12, 12, 12, 12)
```

#### 修改 6：显示设置卡片紧凑化

```python
# 当前 (_setup_display_card)
layout.setContentsMargins(16, 12, 16, 12)

# 新值
layout.setContentsMargins(12, 12, 12, 12)
```

#### 修改 7：操作按钮布局微调

参考 HTML 原型，按钮排列为：`[-] [重置] [确认] [+]`，其中重置和确认各占 flex:1。

```python
# 当前 (_setup_actions_card)
# decrease | increase （一行）
# reset | confirm （一行）

# 新值：所有按钮在一行
# [-] [reset(flex)] [confirm(flex)] [+]
```

#### 修改 8：`update_counter_style()` 方法

```python
# 当前
current_color = AppStyles.EXERCISE_COLORS.get(current_exercise, "#FFFFFF")

# 新值
current_color = AppStyles.EXERCISE_COLORS.get(current_exercise, "#1D1D1F")
# 默认颜色从白色改为深色
```

---

### 7.4 `ui/coach_panel.py` (SafetyPanel) -- 安全面板

**优先级**：P0

#### 修改 1：卡片样式更新

```python
# 当前
card.setStyleSheet(AppStyles.get_card_style())
# 使用 #1C1C1E 深色背景

# 新值：使用更新后的 get_card_style()（#FFFFFF 白色 + 20px 圆角）
# 同时添加 QGraphicsDropShadowEffect
```

#### 修改 2：状态指示器字号

```python
# 当前
self.status_indicator.setStyleSheet("font-size: 14px; font-weight: 600; color: #34C759;")

# 新值
self.status_indicator.setStyleSheet("font-size: 17px; font-weight: 600; color: #34C759;")
# 从 14px 增大到 17px，与 HTML 原型一致
```

#### 修改 3：消息区改为聊天气泡样式

**当前样式：**

```css
QLabel {
    padding: 12px 16px;
    background-color: #2C2C2E;
    border-radius: 10px;
    font-size: 14px;
    color: #FFFFFF;
    border-left: 3px solid #34C759;
}
```

**新样式（聊天气泡）：**

```css
QLabel {
    padding: 12px 16px;
    background-color: #F0F0F5;
    border-radius: 12px;
    font-size: 15px;
    color: #1D1D1F;
    border-left: 3px solid #34C759;
}
```

#### 修改 4：聊天气泡增加 AI 教练头像

在消息 QLabel 前添加一个圆形图标（QLabel with QPixmap 或纯 CSS 圆形色块）：

```python
# 新增：AI 教练头像
avatar = QLabel()
avatar.setFixedSize(24, 24)
avatar.setStyleSheet("""
    QLabel {
        background-color: #34C759;
        border-radius: 12px;
    }
""")
# 可选：设置 SVG 或文字图标
```

> 消息区域改为 QHBoxLayout：左侧 avatar + 右侧 bubble QLabel。

#### 修改 5：统计行颜色更新

```python
# 当前
self.stats_label.setStyleSheet("font-size: 12px; color: #8E8E93;")

# 新值
self.stats_label.setStyleSheet("font-size: 12px; color: #86868B;")
```

#### 修改 6：`update_safety_status()` 方法中所有样式

将方法内三处 `setStyleSheet` 调用的颜色全面更新：

| 状态 | 状态圆点 | 状态文字 | 消息气泡背景 | 消息气泡边框 |
|------|---------|---------|-------------|-------------|
| 安全 | `#34C759` | `color: #34C759` | `#F0F0F5` | `border-left: 3px solid #34C759` |
| 警告 | `#FF9F0A` | `color: #FF9F0A` | `#FFF5EE` (暖色浅底) | `border-left: 3px solid #FF9F0A` |
| 危险 | `#FF453A` | `color: #FF453A` | `#FFF0EE` (红色浅底) | `border-left: 3px solid #FF453A` |

> 消息气泡的背景色可以根据安全等级做微调：安全用默认 `#F0F0F5`，警告用 `#FFF5EE`，危险用 `#FFF0EE`。

---

### 7.5 `ui/video_display.py` -- 视频显示区域

**优先级**：P1

#### 修改 1：视频区域圆角和边框

```python
# 当前
self.setStyleSheet("""
    background-color: #000000;
    border-radius: 24px;
    border: 1px solid #38383A;
""")

# 新值
self.setStyleSheet("""
    background-color: #FFFFFF;
    border-radius: 20px;
    border: none;
""")
# 阴影通过 QGraphicsDropShadowEffect 添加
```

#### 修改 2：Overlay pills 样式

```python
# 当前 - RTMPose label
self.rtmpose_label.setStyleSheet("""
    background: rgba(0,0,0,0.6);
    color: #FFFFFF;
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 100px;
""")

# 新值
self.rtmpose_label.setStyleSheet("""
    background: rgba(52,199,89,0.9);
    color: #FFFFFF;
    font-size: 10px;
    padding: 4px 10px;
    border-radius: 100px;
""")
```

```python
# 当前 - FPS label
self.fps_label.setStyleSheet("""
    background: rgba(0,0,0,0.6);
    color: #FFFFFF;
    ...
""")

# 新值
self.fps_label.setStyleSheet("""
    background: rgba(255,255,255,0.8);
    color: #1D1D1F;
    font-size: 10px;
    padding: 4px 10px;
    border-radius: 100px;
""")
```

#### 修改 3：新增安全状态渐变条 (P1)

在视频区域底部添加一个 4px 高的渐变条 widget：

```python
# 在 _setup_overlays() 中新增
self.safety_bar = QWidget(self)
self.safety_bar.setFixedHeight(4)
self.safety_bar.setStyleSheet("""
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #34C759,
        stop:0.5 #FF9F0A,
        stop:1 #FF453A
    );
""")
```

在 `resizeEvent()` 中调整其位置：

```python
self.safety_bar.move(0, self.height() - 4)  # 底部对齐
self.safety_bar.setFixedWidth(self.width())
self.safety_bar.raise_()
```

#### 修改 4：新增动作评分圆环占位 (P2)

在视频右上角添加一个圆形评分徽章：

```python
# 新增
self.score_badge = QWidget(self)
self.score_badge.setFixedSize(72, 72)
self.score_badge.setStyleSheet("""
    background-color: rgba(255, 255, 255, 0.9);
    border: 2px solid #34C759;
    border-radius: 36px;
""")
```

> 评分圆环内部可放置 QLabel 显示分数数字。在 `resizeEvent()` 中调整位置到右上角。

#### 修改 5：`resizeEvent()` 中 overlay 定位调整

```python
# 当前
self.overlay_container.move(12 + margins.left(), 12 + margins.top())

# 新值（保持 12px 偏移不变，但需确保不超出新的圆角范围）
# 同步更新 safety_bar 和 score_badge 的位置
```

---

### 7.6 `ui/custom_widgets.py` -- 自定义控件

**优先级**：P0

#### 修改 1：`ToggleSwitch` 颜色更新

```python
# 当前
self.on_color = QColor("#34C759")
self.off_color = QColor("#636366")
self.thumb_color = QColor("#FFFFFF")

# 新值
self.on_color = QColor("#34C759")       # 保留
self.off_color = QColor("#E5E5EA")       # 从深灰改为浅灰
self.thumb_color = QColor("#FFFFFF")     # 保留
```

#### 修改 2：`ToggleSwitch` 尺寸微调

```python
# 当前
self.setMinimumWidth(50)
self.setMaximumWidth(50)
self.setMinimumHeight(28)
self.setMaximumHeight(28)

# 新值（参考 HTML 原型：44px x 26px）
self.setMinimumWidth(44)
self.setMaximumWidth(44)
self.setMinimumHeight(26)
self.setMaximumHeight(26)
```

> 注意：HTML 原型的 Toggle 是 44x26，当前代码是 50x28。可视情况选择保持 50x28 或缩小到 44x26。建议缩小以更紧凑。

#### 修改 3：`SwitchControl` label 颜色

```python
# 当前
self.label.setStyleSheet("color: #FFFFFF; font-size: 15px;")

# 新值
self.label.setStyleSheet("color: #1D1D1F; font-size: 15px;")
```

#### 修改 4：`ToggleSwitch.paintEvent()` 圆角微调

```python
# 当前
painter.drawRoundedRect(0, 0, self.width(), self.height(), 14, 14)
thumb_diameter = 24

# 新值（如果尺寸改为 44x26）
painter.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)
thumb_diameter = 22
```

#### 修改 5：ToggleSwitch 滑块阴影

```python
# 当前：无阴影
# 新值：添加轻微阴影
shadow_pen = QPen(QColor(0, 0, 0, 38))  # rgba(0,0,0,0.15) 约 38/255
# 或在 thumb 圆上先画一个偏移阴影圆
painter.setBrush(QBrush(QColor(0, 0, 0, 38)))
painter.drawEllipse(thumb_x + 0, thumb_y + 1, thumb_diameter, thumb_diameter)
# 再画白色滑块
painter.setBrush(QBrush(self.thumb_color))
painter.drawEllipse(thumb_x, thumb_y, thumb_diameter, thumb_diameter)
```

---

### 7.7 `ui/user_profile_panel.py` -- 用户档案面板

**优先级**：P1

#### 修改 1：从内联面板改为 Drawer

**核心思路**：将 UserProfilePanel 从右侧面板的固定组件改为 **侧边抽屉 (Drawer)**，默认隐藏，通过导航栏的用户头像按钮触发显示。

```python
# 当前：在 main_window.py 的 right_layout 中直接 addWidget
# 新值：不再在 right_layout 中添加
# 改为创建一个覆盖在主窗口上的 Drawer
```

#### 修改 2：Drawer 实现方案

```python
class UserProfileDrawer(QWidget):
    """用户档案侧边抽屉"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(360)
        self.setVisible(False)  # 默认隐藏
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-left: 1px solid #E5E5EA;
            }
        """)

        # 添加 QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(-4, 0)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

    def show_drawer(self):
        # 动画滑入（从右侧）
        self.setVisible(True)
        # 可选：使用 QPropertyAnimation 实现滑入动画

    def hide_drawer(self):
        # 动画滑出
        self.setVisible(False)
```

#### 修改 3：标题栏样式更新

```python
# 当前
self._header.setStyleSheet("""
    QFrame {
        background-color: #1C1C1E;
        border-radius: 12px;
    }
""")

# 新值
self._header.setStyleSheet("""
    QFrame {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E5E5EA;
    }
""")
```

#### 修改 4：内容区样式更新

```python
# 当前
self._content_frame.setStyleSheet("""
    QFrame {
        background-color: #1C1C1E;
        border-radius: 0 0 12px 12px;
    }
""")

# 新值
self._content_frame.setStyleSheet("""
    QFrame {
        background-color: #FFFFFF;
        border-radius: 0 0 12px 12px;
    }
""")
```

#### 修改 5：所有输入框颜色

```python
# 当前：所有 QLineEdit/QSpinBox/QComboBox 使用 AppStyles.get_dark_input_style()
# 新值：使用更新后的 get_input_style()（白色背景 + 浅灰边框）
```

#### 修改 6：Label 颜色

```python
# 当前
name_label.setStyleSheet("color: #8E8E93; font-size: 15px;")

# 新值
name_label.setStyleSheet("color: #86868B; font-size: 15px;")
```

#### 修改 7：Checkbox 样式

```python
# 当前
QCheckBox { background-color: #2C2C2E; color: #FFFFFF; }
QCheckBox:checked { background-color: rgba(52, 199, 89, 0.1); color: #34C759; }

# 新值
QCheckBox { background-color: #F0F0F5; color: #1D1D1F; border: 1px solid #E5E5EA; }
QCheckBox:checked { background-color: rgba(52, 199, 89, 0.1); color: #34C759; border-color: #34C759; }
```

#### 修改 8：保存/重置按钮样式

```python
# 当前
self.save_btn.setStyleSheet(AppStyles.get_success_button_style())
self.reset_btn.setStyleSheet(AppStyles.get_reset_button_style())

# 新值：使用更新后的样式方法（已包含浅色主题颜色）
```

#### 修改 9：提示信息样式

```python
# 当前 - 成功提示
background-color: rgba(52, 199, 89, 0.1); color: #34C759;

# 新值
background-color: rgba(52, 199, 89, 0.08); color: #34C759;
```

```python
# 当前 - 错误提示
background-color: rgba(255, 59, 48, 0.1); color: #FF3B30;

# 新值
background-color: rgba(255, 69, 58, 0.08); color: #FF453A;
```

---

## 8. 新增功能实现

### 8.1 顶部导航栏 (TopNavBar)

**位置**：固定在主窗口顶部，高度 52px。

**结构**：
```
┌────────────────────────────────────────────────────────────┐
│ [Logo]  护动智眸    [运动训练] [统计分析]    [头像] [设置] │
└────────────────────────────────────────────────────────────┘
```

**实现建议**：

1. 在 `ui/` 下新建 `nav_bar.py`，或直接在 `main_window.py` 中内联实现
2. 使用 `QWidget` 作为容器，`setFixedHeight(52)`
3. 内部 `QHBoxLayout`：左侧 logo + 标题、中间 pill tabs、右侧头像 + 设置按钮
4. pill tabs 使用 `QPushButton` + 圆角 QSS 样式
5. 中间 pill tabs 背景为 `#EFEFF4`，选中项为 `#34C759` 绿色背景 + 白色文字

**QSS 片段 - 导航栏：**

```css
/* 导航栏容器 */
QWidget#navBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E5EA;
}

/* Tab pill - 未选中 */
QPushButton#navTab {
    background-color: #F0F0F5;
    color: #1D1D1F;
    border: none;
    border-radius: 100px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
}

/* Tab pill - 选中 */
QPushButton#navTab:checked {
    background-color: #34C759;
    color: #FFFFFF;
}

/* Tab pill 容器背景 */
QWidget#tabContainer {
    background-color: #EFEFF4;
    border-radius: 100px;
    padding: 4px;
}
```

### 8.2 安全状态渐变条

**位置**：视频区域底部，4px 高，全宽。

**实现**：见 `video_display.py` 修改清单第 3 项。

**动态更新**：可根据当前安全等级动态更新渐变条显示的范围。例如：
- 安全时：整条显示绿色
- 警告时：左侧 60% 绿色 + 40% 橙色
- 危险时：左侧 40% 绿色 + 30% 橙色 + 30% 红色

### 8.3 评分圆环叠加

**位置**：视频右上角，72x72 圆形。

**实现**：见 `video_display.py` 修改清单第 4 项。

**内容**：
- 外圈：2px solid #34C759
- 内部：分数数字（24px, font-weight: 600）
- 下方：「动作评分」文字（9px）

### 8.4 聊天气泡样式的安全消息

**位置**：安全面板内，替代当前的左边框消息区。

**结构**：
```
┌──────────────────────────────┐
│ 🟢 [24px 圆形图标]  动作标准，│
│    继续保持！关节角度在安全范 │
│    围内。                     │
└──────────────────────────────┘
```

**实现**：见 `coach_panel.py` 修改清单第 3、4 项。

**状态变化时的颜色联动**：
- 安全：图标 + 左边框 = `#34C759`，背景 = `#F0F0F5`
- 警告：图标 + 左边框 = `#FF9F0A`，背景 = `#FFF5EE`
- 危险：图标 + 左边框 = `#FF453A`，背景 = `#FFF0EE`

### 8.5 用户档案侧边抽屉

**位置**：覆盖在主窗口右侧，宽度 360px。

**交互**：
- 默认隐藏
- 点击导航栏「用户头像」按钮打开
- 抽屉外部点击或点击关闭按钮关闭
- 可选：QPropertyAnimation 实现滑入/滑出动画

**实现**：见 `user_profile_panel.py` 修改清单第 2 项。

---

## 9. 布局调整详情

### 9.1 视频区域

| 属性 | 当前 | 新值 |
|------|------|------|
| 宽度占比 | 60% (stretch=6) | 70% (stretch=7) |
| 背景色 | `#000000` | `#FFFFFF` |
| 圆角 | 24px | 20px |
| 边框 | 1px solid `#38383A` | 无（使用阴影） |
| 最小尺寸 | 无限制 | 保持当前行为 |

### 9.2 右侧面板

| 属性 | 当前 | 新值 |
|------|------|------|
| 宽度占比 | 40% (stretch=4) | 30% (stretch=3) |
| 最大宽度 | 520px | 400px |
| 最小宽度 | 无限制 | 320px (建议添加) |
| 外边距 | 0px (由父布局控制) | 0px |
| 卡片间距 | 12px | 12px (保持) |
| 滚动 | 无 | 添加 QScrollArea |

### 9.3 计数器

| 属性 | 当前 | 新值 |
|------|------|------|
| 字号 | 48pt | 56pt |
| 字重 | 300 (light) | 200 (extra-light) |
| 字距 | 无 | -2px |
| 默认颜色 | `#FFFFFF` | `#1D1D1F` |
| 布局 | 左(计数器) + 右(Phase) | 居中(数字 + 箭头 + 标签) |

### 9.4 安全面板

| 属性 | 当前 | 新值 |
|------|------|------|
| 状态文字字号 | 14px | 17px |
| 消息区字号 | 14px | 15px |
| 消息区样式 | 左边框深色背景 | 聊天气泡浅色背景 + 头像 |
| 统计行 | 有 | 保留但移到统计面板（P2）|

### 9.5 用户档案面板

| 属性 | 当前 | 新值 |
|------|------|------|
| 位置 | 右侧面板底部固定 | 侧边抽屉（默认隐藏）|
| 宽度 | 继承右侧面板宽度 | 固定 360px |
| 触发方式 | 始终可见 | 导航栏头像按钮 |

---

## 10. 实施顺序建议

按照以下顺序实施，可以最小化风险并确保每一步都可验证：

### 第 1 步：`styles.py` -- 色彩/间距/圆角 Token 重写

- 更新所有颜色常量（BG, CARD, SURFACE, TEXT, BORDER, 语义色）
- 更新 `EXERCISE_COLORS` 字典
- 更新 `get_window_palette()`
- 更新 `get_global_stylesheet()`
- 更新所有 `get_*_style()` 方法中的颜色值
- 新增方法：`get_chat_bubble_style()`, `get_nav_bar_style()`, `get_score_badge_style()` 等

> **验证点**：此时运行程序，所有控件颜色应该已经是浅色主题，虽然布局和细节可能还不完美。

### 第 2 步：`custom_widgets.py` -- ToggleSwitch 和 SwitchControl

- 更新 ToggleSwitch 颜色
- 更新 ToggleSwitch 尺寸（可选）
- 更新 SwitchControl label 颜色

> **验证点**：所有开关控件在浅色背景下可正常显示和切换。

### 第 3 步：`video_display.py` -- 视频区域叠加层

- 更新视频区背景色、圆角、边框
- 更新 overlay pills 样式
- 新增安全状态渐变条
- 新增评分圆环占位

> **验证点**：视频区域显示为白色卡片风格，overlay 标签可读。

### 第 4 步：`coach_panel.py` -- 安全面板

- 更新卡片阴影
- 更新状态指示器字号
- 将消息区改为聊天气泡样式
- 更新所有 `update_safety_status()` 中的样式

> **验证点**：安全面板显示为白色卡片，聊天气泡样式正确，安全等级变化时颜色联动正常。

### 第 5 步：`control_panel.py` -- 控制面板

- `_create_card()` 添加阴影
- 移除面板标题（或缩小字号）
- 更新计数器布局（居中化）
- 紧凑化设置卡片和开关卡片
- 更新按钮布局为一行排列
- 更新 `update_counter_style()` 中的默认颜色

> **验证点**：控制面板所有卡片为白色带阴影，计数器大数字清晰可读。

### 第 6 步：`user_profile_panel.py` -- 用户档案 Drawer 转换

- 将面板从内联组件改为 Drawer
- 更新所有输入框、标签、按钮颜色
- 添加打开/关闭逻辑
- 更新 header 和 content frame 样式

> **验证点**：Drawer 可从右侧滑入/滑出，所有表单控件颜色正确。

### 第 7 步：`main_window.py` -- 主窗口布局和导航栏

- 更新布局比例 6:4 -> 7:3
- 更新右侧面板最大宽度 520px -> 400px
- 更新页面外边距 16px -> 24px
- 新增顶部导航栏组件
- 将用户档案从右侧面板移除
- 添加右侧面板滚动支持
- 更新中央部件背景色

> **验证点**：整体布局与 HTML 原型一致，导航栏功能正常。

---

## 11. 验证清单

迁移完成后，逐项检查以下内容：

### 11.1 视觉验证

- [ ] 所有颜色在浅色主题下渲染正确，无残留深色
- [ ] 卡片阴影显示正常，层级关系清晰
- [ ] 文字颜色与背景对比度足够（WCAG AA 标准）
- [ ] 语义状态色（绿/橙/红）在白色背景上醒目
- [ ] 计数器大数字（56pt, font-weight: 200）清晰可读
- [ ] 字距 -2px 不会导致数字重叠

### 11.2 布局验证

- [ ] 无文字重叠或裁剪
- [ ] 窗口缩小至 1280x720 时布局不崩溃
- [ ] 右侧面板在 400px 宽度内所有控件可完整显示
- [ ] 右侧面板内容超出时可正常滚动
- [ ] 视频区域占 70% 宽度，不小于最小尺寸

### 11.3 交互验证

- [ ] ToggleSwitch 开关切换正常，颜色正确（on=#34C759, off=#E5E5EA）
- [ ] 所有下拉框展开时颜色正确（白色背景，深色文字）
- [ ] 按钮点击 hover/pressed/disabled 态颜色正确
- [ ] Phase indicator 激活/未激活状态切换正常
- [ ] 安全面板等级变化时，聊天气泡颜色联动正确

### 11.4 视频叠加层验证

- [ ] overlay pills（RTMPose + FPS）可读且不遮挡视频主要内容
- [ ] 安全状态渐变条在视频底部正确显示
- [ ] 评分圆环在视频右上角正确显示（如果实现了）
- [ ] overlay 元素在窗口 resize 后位置正确

### 11.5 新功能验证

- [ ] 顶部导航栏正确显示
- [ ] 导航栏模式切换按钮（运动训练/统计分析）可点击
- [ ] 用户档案 Drawer 可通过头像按钮打开和关闭
- [ ] Drawer 打开时主界面不响应（遮罩层）
- [ ] Drawer 关闭后恢复正常

### 11.6 投影效果验证

- [ ] 在 1920x1080 投影仪上浅色背景不刺眼
- [ ] 远距离（3-5 米）可看清计数器数字
- [ ] 安全等级变化在投影仪上可辨识
- [ ] 视频区域骨架线在浅色背景下可辨识

### 11.7 兼容性验证

- [ ] 统计模式（Stats mode）在浅色主题下正常显示
- [ ] 语言切换功能不受影响（中/英文）
- [ ] 所有业务逻辑（信号连接、计数、安全检测）不受影响
- [ ] 模型切换、摄像头切换功能正常
- [ ] 声音提醒开关正常工作

---

> **文档版本**: v1.0  
> **创建日期**: 2026-07-08  
> **适用范围**: 护动智眸 PyQt5 桌面端前端 UI 浅色主题迁移  
> **参考原型**: `traedesign/hudong-smart-eyes/pages/training.html` 和 `stats.html`

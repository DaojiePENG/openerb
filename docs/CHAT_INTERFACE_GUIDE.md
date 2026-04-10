# OpenERB Chat Interface - Quick Start Guide

## 概述

OpenERB Chat Interface 是一个交互式聊天窗口，让您在没有物理机器人身体的情况下体验和调试具身机器大脑的核心能力。

系统采用**两层架构**：
1. **对话层** — LLM 自然语言对话，负责理解用户意图并进行路由
2. **执行层** — 代码生成与执行（MotorCortex），处理计算、机器人控制等实际任务

## 快速开始

### 启动聊天界面

```bash
# 方式1：直接使用python（推荐）
python scripts/chat.py

# 方式2：使用uv run
uv run python scripts/chat.py

# 确保虚拟环境激活且依赖已安装
source .venv/bin/activate  # Linux/Mac
pip install -e .            # 如果还未安装
```

### 环境变量配置

```bash
export DASHSCOPE_API_KEY="sk-your-key"       # 必需：LLM API 密钥
export LLM_MODEL="qwen-vl-plus"              # 可选：对话模型
export LLM_CODE_MODEL="qwen-plus"            # 可选：代码生成模型（可与对话模型不同）
```

### CLI 命令

进入聊天后，以下是硬编码的 CLI 命令：

| 命令 | 说明 |
|------|------|
| `help` | 显示帮助信息 |
| `quit` / `exit` / `bye` | 退出聊天 |

其他所有交互都通过**自然语言**驱动，由 LLM 理解并路由。

## 核心能力

### 自然对话

直接和机器人聊天，它会像朋友一样回应：

```
You: 你好！
OpenERB: 你好！我是 OpenERB，一个具身机器人大脑。有什么可以帮你的吗？

You: What's your name?
OpenERB: I'm OpenERB, an embodied robot brain assistant. I have a physical robot body (G1).
```

### 计算与代码执行

当用户提出计算任务时，LLM 会发出 `[ACTION_REQUIRED]` 标记，系统自动生成代码并执行：

```
You: what is 8 + 8?
🧠 Thinking...
🔧 Let me work on that...
🆕 No existing skill found, generating new code...
  └─ Method: 🤖 LLM-generated code | Time: 0.012s
The answer to 8 + 8 is 16.
💾 New skill learned and saved: math_calculation (id: 5b48e61e-08a)
```

### 技能复用（含参数适配）

学过的技能会自动保存，下次遇到类似任务时直接复用。系统会自动**重新参数化**已学技能以适配新输入：

```
You: what is 9 + 9?
🧠 Thinking...
🔧 Let me work on that...
📚 Found existing skill: math_calculation (id: 5b48e61e-08a), reusing...
  └─ 🔧 Adapted parameters for: what is 9 + 9?
  └─ Method: ♻️ Reused skill: math_calculation (adapted) | Time: 0.001s
9 + 9 equals 18.
```

参数适配通过 LLM 完成：保留已学函数定义，仅修改调用参数。例如学了 `factorial(5)` 后问 `factorial(10)`，不会重新生成代码。

### 失败自动修复

当代码执行失败时，系统会自动重试并将错误信息反馈给 LLM 进行修正（最多 2 次）：

```
You: 生成一个复杂图表
🧠 Thinking...
🔧 Let me work on that...
🆕 No existing skill found, generating new code...
⚠ Attempt failed: NameError: name 'np' is not defined
  └─ 🔄 Refining... (attempt 1/2)
  └─ Method: 🔄 Refined code (attempt 2) | Time: 0.045s
  └─ ✅ Succeeded after 1 refinement(s)!
```

### 技能库查询

自然语言询问，LLM 会发出 `[LIST_SKILLS]` 标记触发技能列表：

```
You: 你会什么？
OpenERB: 以下是我当前掌握的技能：
┏━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┓
┃ #   ┃ Name             ┃ Description             ┃ Type    ┃ Source     ┃ Runs ┃ Success ┃
┡━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━┩
│ 1   │ math_calculation │ Auto-learned: 8 + 8     │ body_sp │ 🤖 learned │    1 │   100%  │
│ 2   │ move_forward     │ Auto-generated skill    │ body_sp │ 🤖 learned │    0 │       - │
└─────┴──────────────────┴─────────────────────────┴─────────┴────────────┴──────┴─────────┘
Storage: openerb/skills/skill_library.json
```

### 用户档案（跨会话持久化）

用户信息自动保存到 `openerb/data/user_profiles.json`，下次登录时自动识别：

```
You: who am I?
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property            ┃ Value                          ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Name                │ Daojie                         │
│ Status              │ 🎉 Old friend                  │
│ First Seen          │ 2026-04-08 14:00:00            │
│ Total Sessions      │ 5                              │
│ Total Interactions  │ 42                             │
│ Skills Learned      │ 3                              │
└─────────────────────┴────────────────────────────────┘
```

退出时（`quit` 或 `Ctrl+C`），系统会使用 LLM 自动总结当前对话并保存，下次登录时作为上下文注入。

### 学习进度报告

查看技能掌握程度、熟练度和练习建议：

```
You: 学习进度
📊 Learning Progress Report
┏━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ #   ┃ Skill            ┃ Mastery         ┃ Confidence ┃ Success Rate ┃ Executions  ┃
┡━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 1   │ math_calculation │ 🌿 beginner     │       60%  │         100% │           6 │
│ 2   │ fibonacci        │ 🌱 novice       │       40%  │         100% │           3 │
│ 3   │ draw_shape       │ 🌱 novice       │       30%  │          50% │           2 │
└─────┴──────────────────┴─────────────────┴────────────┴──────────────┴─────────────┘
Overall: 3 skills tracked, 0 mastered, avg competency: 43%
💡 Suggested practice:
  • draw_shape (improvement potential: 50%)
```

## 系统架构

### LLM 路由标记

系统通过 LLM 在回复中嵌入的标记进行路由，所有行为约束通过**系统提示词**（`.md` 文件）定义，而非硬编码：

| 标记 | 触发条件 | 系统行为 |
|------|----------|----------|
| `[ACTION_REQUIRED]` | 计算、机器人控制、绘图、学习技能 | 代码生成 → 执行 → 失败自动修复 → 结果解释 → 技能保存 |
| `[CODE_REQUIRED]` | 用户要求写/生成代码 | 代码生成（展示，不一定执行） |
| `[LIST_SKILLS]` | 查询能力、技能列表 | 读取 Cerebellum 展示技能表 |
| `[USER_PROFILE]` | 查询"我是谁"、用户信息 | 展示用户档案 |
| `[LEARNING_PROGRESS]` | 学习进度、掌握程度 | 展示 Hippocampus 学习分析报告 |
| 无标记 | 普通对话 | 直接展示 LLM 回复 |

**二层路由容错**：当 LLM 未返回正确标记时，系统通过正则 fallback 从用户输入推断意图（`_extract_marker()`），确保即使模型不遵守格式，也能正确路由。

### 提示词管理

所有 LLM 实例的系统提示词以 `.md` 文件形式集中管理在 `openerb/prompts/` 目录下：

```
openerb/prompts/
├── __init__.py              # load_prompt() 工具函数
├── chat_system.md           # 主对话 LLM 系统提示词（路由规则、行为约束）
├── code_generator.md        # 代码生成 LLM 系统提示词（安全规则、输出格式）
├── intent_recognition.md    # 意图识别 LLM 系统提示词（JSON 输出格式）
└── result_interpreter.md    # 执行结果解释 LLM 系统提示词
```

修改 `.md` 文件即可调整 LLM 行为，无需改动 Python 代码。

### 技能持久化

学到的技能以 JSON 格式保存在 `openerb/skills/skill_library.json`：

```
学习闭环：用户提问 → 代码生成 → 执行（失败→自动修复重试） → 结果反馈 → 技能保存 → 下次复用（参数适配）
```

- 新技能自动保存（名称由 `_derive_skill_name()` 从用户输入推导，自动剥离 "learn to"/"学习" 前缀）
- 已有技能通过 Cerebellum 搜索匹配并复用，搜索排除 `learned`/`auto_generated` 等元标签防止误匹配
- 复用时自动通过 LLM 重新参数化（保留函数定义，修改调用参数）
- 执行统计（运行次数、成功率）自动更新
- 执行失败和成功均记录到 Hippocampus（海马体）用于学习分析

### 记忆与持久化

| 数据 | 存储位置 | 跨会话 |
|------|----------|--------|
| 技能代码 | `openerb/skills/skill_library.json` | ✅ |
| 用户档案 | `openerb/data/user_profiles.json` | ✅ |
| 对话摘要 | `user_profiles.json → conversation_summaries` | ✅ |
| 学习进度 | Hippocampus 内存（会话内） | ❌ |
| 对话历史 | `_chat_messages`（会话内） | ❌ |

## 故障排除

### LLM 未初始化

**现象**: 看到 "LLM not available" 提示

**解决**:
```bash
export DASHSCOPE_API_KEY="sk-your-key"
# 或在项目根目录创建 .env 文件
echo 'DASHSCOPE_API_KEY=sk-your-key' > .env
```

### LLM 不返回 `[ACTION_REQUIRED]`

**现象**: 数学问题被 LLM 直接回答，没有走代码执行

**解决**: 编辑 `openerb/prompts/chat_system.md`，加强 Action Routing 部分的约束描述。系统提示词的质量直接决定路由准确性。

### 技能没有保存

**现象**: 技能执行成功但下次没有复用

**检查**:
1. 确认 `openerb/skills/skill_library.json` 文件存在且有写入权限
2. 查看日志中是否有 `💾 Persisted skill` 记录
3. 确认 Cerebellum 模块已正确初始化

### Profile not found 警告

**现象**: 执行后出现 "Profile not found for ..." 警告

**原因**: Hippocampus 中的用户档案未创建。这是非阻塞的警告，不影响核心功能。

**解决方案**: 正在改进，当前版本可使用其他技能

## 进阶用法

### 连续对话

保持聊天窗口打开，进行多轮对话。所有对话会自动记录在会话历史中。

```
You: hello
OpenERB: [响应]

You: what's your name?
OpenERB: [响应]

You: history
OpenERB: [显示两条对话记录]
```

### 导出对话

使用 `history` 命令查看对话，复制输出到文本文件进行分析。

### 测试集成

聊天界面与以下核心模块集成：
- ✅ PrefrontalCortex（对话处理）
- ✅ Cerebellum（技能管理）
- ✅ Hippocampus（学习和记忆）
- ✅ IntegrationEngine（跨模块协调）

## 开发计划

- [x] 完整 LLM 集成（DashScope qwen3.6-plus）
- [x] 技能学习闭环（生成→执行→保存→复用→参数适配）
- [x] 失败自动修复（错误反馈→LLM 重新生成→重试）
- [x] 用户持久化（跨会话记忆用户、对话摘要）
- [x] 学习进度分析（Hippocampus 海马体集成）
- [x] 绘图/matplotlib 支持（Agg 无头渲染）
- [ ] Hippocampus 学习数据持久化（当前仅会话内）
- [ ] 技能组合（将多个技能链式调用）
- [ ] 技能泛化（同类技能跨机器人迁移）
- [ ] Web 界面版本
- [ ] 真机部署后的无缝过渡

## 相关文档

- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - 项目发展路线图
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - 系统架构
- [SYSTEM_FAMILIARIZATION.md](SYSTEM_FAMILIARIZATION.md) - 系统功能熟悉
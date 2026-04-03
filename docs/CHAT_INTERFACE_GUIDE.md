# OpenERB Chat Interface - Quick Start Guide

## 概述

OpenERB Chat Interface 是一个交互式聊天窗口，让您在没有物理机器人身体的情况下体验和调试具身机器大脑的核心能力。

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

### 基础命令

进入聊天后，您可以使用以下命令：

| 命令 | 说明 | 示例 |
|------|------|------|
| `help` | 显示所有可用命令和软技能 | `help` |
| `history` | 查看最近的10条对话记录 | `history` |
| `stats` | 显示学习统计信息 | `stats` |
| `skill [name]` | 演示特定的软技能 | `skill math` |
| `quit`/`exit` | 退出聊天程序 | `quit` |

## 软技能演示

机器人支持6个核心软技能，可以通过自然语言触发或使用 `skill` 命令演示。

### 1. 数学计算 (math)

机器人可以进行基础数学运算。

**触发方式**:
- 消息中包含 "calculate"、"solve"、"math" 等关键词
- 或使用：`skill math`

**示例**:
```
You: calculate 10 + 5 * 2
OpenERB: The result of 10+5*2 is 20
```

### 2. 讲笑话 (joke)

机器人维护了一个笑话库，可以随机讲述相关主题的笑话。

**触发方式**:
- 消息中包含 "joke"、"funny"、"laugh" 等关键词
- 或使用：`skill joke`

**示例**:
```
You: tell me a joke
OpenERB: 🤖 Here's a joke: Why did the robot go on a diet? Because it had too many bytes!
```

### 3. 写作创意 (write)

机器人可以编写故事、诗歌和文档。

**触发方式**:
- 消息中包含 "write"、"poem"、"story" 等关键词
- 或使用：`skill write`

**示例**:
```
You: write a poem
OpenERB: Roses are red,
         Violets are blue,
         I'm learning from you,
         And growing too! 📝
```

### 4. 解释说明 (explain)

机器人可以解释AI、机器人、学习等基础概念。

**触发方式**:
- 消息中包含 "explain"、"what is"、"tell me about" 等关键词
- 或使用：`skill explain`

**示例**:
```
You: explain AI
OpenERB: AI stands for Artificial Intelligence. It's technology that allows machines to learn and make decisions.
```

### 5. 记忆功能 (remember)

机器人可以记住您提供的信息，并在后续对话中回顾。

**触发方式**:
- 消息中包含 "remember" 关键词
- 或使用：`skill remember`

**示例**:
```
You: remember that I like robotics
OpenERB: ✅ I'll remember: 'that I like robotics'
```

### 6. 学习能力 (learn)

机器人表现出学习意愿和能力，可以接受新知识。

**触发方式**:
- 消息中包含 "learn"、"teach"、"training" 等关键词
- 或使用：`skill learn`

**示例**:
```
You: teach me something new
OpenERB: I'm always learning! Every conversation helps me understand humans better. What would you like to teach me?
```

## 使用场景

### 场景1：测试对话能力

```
You: What are you?
OpenERB: I'm your embodied robot brain assistant!
         I'm here to chat and learn with you! What would you like to talk about?
```

### 场景2：教机器人新知识

```
You: remember that my favorite robot is Unitree G1
OpenERB: ✅ I'll remember: 'that my favorite robot is Unitree G1'

You: what's my favorite robot?
OpenERB: (查询记忆库) You told me: Your favorite robot is Unitree G1
```

### 场景3：演示多个技能

```
You: skill math
OpenERB: (显示数学技能演示)

You: skill joke  
OpenERB: (随机讲一个笑话)

You: history
OpenERB: (显示对话历史表格)
```

### 场景4：查看学习进度

```
You: stats
OpenERB: (显示学习统计面板)
         • Session Duration: 0:15:30
         • Total Interactions: 12
         • Skills Learned: 3
         • Skills Mastered: 1
```

## 故障排除

### 问题1：命令找不到

**现象**: 键入命令后没有响应

**解决**:
- 确保虚拟环境已激活：`source .venv/bin/activate`
- 确保依赖已安装：`python -m pip install -e .`
- 检查是否有错误信息

### 问题2：LLM未初始化

**现象**: 看到警告 "Failed to initialize LLM client"

**原因**: dashscope 模块未安装，但这不影响基础功能

**解决方案**:
- 对话仍然可以进行，使用fallback模式
- 如需完整LLM支持，配置环境变量：
  ```bash
  export LLM_PROVIDER=dashscope
  export LLM_API_KEY=your_api_key
  ```

### 问题3：记忆功能报错

**现象**: 使用 remember 命令时出错

**原因**: Hippocampus 模块初始化需要用户档案

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

- [ ] 完整LLM集成
- [ ] 更多软技能（编码、绘画描述、故事续写等）
- [ ] 持久化聊天历史到文件
- [ ] Web界面版本
- [ ] 多用户支持
- [ ] 真机部署后的无缝过渡

## 相关文档

- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - 项目发展路线图
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - 系统架构
- [SYSTEM_FAMILIARIZATION.md](SYSTEM_FAMILIARIZATION.md) - 系统功能熟悉
# OpenERB - Open Embodied Robot Brain

**OpenERB** 是一个基于类脑架构的自主学习机器人控制系统。机器人能够基于自然语言指令自动生成控制代码，并通过技能学习和记忆实现不断进化。

一个完全自主的、自我进化的、具有多模态交互能力的机器人大脑。

## 📚 文档导航

| 文档 | 用途 | 用户 |
|------|------|------|
| [README.md](README.md) | 项目概览 | 所有人 |
| **[SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)** | **完整系统设计 + 具身大脑设计理念** | **所有人** |
| **[CHAT_INTERFACE_GUIDE.md](docs/CHAT_INTERFACE_GUIDE.md)** | **聊天交互与软技能调试（Phase 5.1）** | **所有用户** |
| [SYSTEM_FAMILIARIZATION.md](docs/SYSTEM_FAMILIARIZATION.md) | 系统功能熟悉指南 | 开发者/用户 |
| [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) | 开发路线图（Phase 5 已调整） | 项目规划 |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | 完整 API 文档 | 开发者 |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | 部署和运维指南 | 运维工程师 |
| [docs/PERFORMANCE_GUIDE.md](docs/PERFORMANCE_GUIDE.md) | 性能优化指南 | 性能工程师 |
| [docs/SAFETY_SANDBOX_GUIDE.md](docs/SAFETY_SANDBOX_GUIDE.md) | 沙盒执行实现指南 | 后端开发者 |



### 环境要求
- Python 3.9+
- Unitree G1 或 Go2 机器人
- 阿里 DASHSCOPE API 密钥
- **推荐**: uv 包管理工具 (更快的依赖解析)

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/DaojiePENG/openerb.git
cd openerb

# 2. 安装依赖 (推荐使用 uv)
uv venv --python 3.11 && source .venv/bin/activate
uv pip install -e .

# 或使用 pip
python -m venv venv && source venv/bin/activate
pip install -e .

# 3. 配置 API 密钥
export DASHSCOPE_API_KEY="sk-your-key"

# 4. 初始化系统
python -m openerb.core.bootstrap init --robot-type G1
```

📖 **详细安装指南**: [部署指南](docs/DEPLOYMENT_GUIDE.md)

### 🚀 真机部署快速开始

**30 分钟内让 OpenERB 在真实机器人上运行！**

#### 1. 硬件连接
```bash
# G1 机器人
ssh unitree@192.168.123.161

# Go2 机器人  
ssh unitree@192.168.12.1
```

#### 2. 一键部署测试
```bash
# 运行自动化部署测试
python scripts/robot_deployment_test.py \
    --robot-type G1 \
    --robot-ip 192.168.123.161
```

#### 3. 基础功能验证
```python
from openerb.modules.system_integration import IntegrationEngine
from openerb.core.types import Intent, UserProfile

engine = IntegrationEngine()
intent = Intent("向前走一步", "walk_forward", {"distance": 0.5})
user = UserProfile("operator", "操作员")

result = await engine.execute_intent(intent, user, "G1")
print(f"执行结果: {result['status']}")
```

📖 **详细指南**: [聊天交互指南](docs/CHAT_INTERFACE_GUIDE.md) | [系统功能熟悉](docs/SYSTEM_FAMILIARIZATION.md) | [API 文档](docs/API_REFERENCE.md)

### 启动聊天交互

体验具身机器大脑的对话和学习能力，无需物理机器人：

```bash
# 启动聊天界面
python scripts/chat.py
```

系统采用两层架构：LLM 对话层负责理解意图并路由，MotorCortex 执行层负责代码生成与运行。

在聊天中你可以：
- 🗣️ 自然语言对话（中英文均可）
- 🧮 计算任务 — 自动生成代码执行，不依赖 LLM 知识
- 🤖 机器人控制 — 生成运动代码
- 📚 查看技能库 — 直接问"你会什么？"
- 🧠 技能学习闭环 — 学到的技能自动保存、下次复用
- 🔄 失败自动修复 — 代码执行失败时自动重试（最多 2 次，LLM 根据错误信息修正）
- 🔧 参数适配 — 复用已学技能时自动适配新参数
- 📊 学习进度 — 询问"学习进度"查看 Hippocampus 掌握程度分析
- 👤 跨会话记忆 — 记住用户身份、自动总结并保存对话
- ✏️ 自定义行为 — 编辑 `openerb/prompts/*.md` 文件调整 LLM 行为

只有 `help` 和 `quit` 是硬编码命令，其他一切通过自然语言驱动。

详见 [聊天交互指南](docs/CHAT_INTERFACE_GUIDE.md)。

### 启动主系统

```bash
python -m openerb
```

## 项目结构

```
openerb/
├── core/                          # 核心框架
│   ├── bootstrap.py               # 系统初始化
│   ├── config.py                  # 配置管理
│   ├── types.py                   # 类型定义
│   ├── storage.py                 # 数据持久化
│   └── logger.py                  # 日志系统
├── modules/                       # 8个类脑模块
│   ├── prefrontal_cortex/         # 前额叶皮层 (对话Agent)
│   ├── insular_cortex/            # 岛叶皮层 (机体识别)
│   ├── limbic_system/             # 边缘系统 (安全约束)
│   ├── cerebellum/                # 小脑 (技能库)
│   ├── hippocampus/               # 海马体 (长期记忆)
│   ├── motor_cortex/              # 运动皮层 (代码生成)
│   ├── vision/                    # 视觉模块
│   └── communication/             # 通信与协作
├── prompts/                       # 🆕 LLM 系统提示词（.md 文件集中管理）
│   ├── chat_system.md             # 主对话 LLM 路由规则与行为约束
│   ├── code_generator.md          # 代码生成 LLM 安全规则与输出格式
│   ├── intent_recognition.md      # 意图识别 LLM JSON 输出格式
│   └── result_interpreter.md      # 执行结果解释 LLM
├── skills/                        # 技能库
│   ├── active/                    # 激活的技能
│   ├── deprecated/                # 弃用的技能
│   └── retired/                   # 垃圾箱
├── data/                          # 数据存储
│   ├── body_profiles/             # 机器人档案
│   ├── users/                     # 用户档案
│   └── memories/                  # 记忆与学习历史
├── tests/                         # 测试用例
├── scripts/                       # 🆕 部署和测试脚本
│   ├── robot_deployment_test.py   # 真机部署测试脚本
│   └── ...                        # 其他工具脚本
├── docs/                          # 文档
└── generated_code/                # 运行时生成的代码
```

## 核心特性

- **多模态交互**: 支持文本和图像输入的自然语言理解
- **动态代码生成**: 基于意图自动生成Python控制代码
- **安全约束**: 危险检测、二次确认机制、障碍物规避
- **技能记忆**: 技能持久化、版本管理、智能检索
- **机体识别**: 自动识别当前控制的机器人类型
- **知识迁移**: 在不同机器人平台间迁移通用技能
- **机器人协作**: 机器人间的技能分享和通信
- **🆕 真机部署**: 完整的 Unitree G1/Go2 机器人部署支持
- **🆕 自动化测试**: 一键部署验证和系统诊断工具
- **🆕 提示词管理**: LLM 系统提示词以 `.md` 文件集中管理，修改即生效
- **🆕 技能学习闭环**: 代码生成 → 执行 → 结果解释 → 技能保存 → 自动复用

## 模块说明

详见 [SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)

## 开发进度

- [ ] 基础架构与类型定义
- [ ] 前额叶皮层 (对话Agent)
- [ ] 岛叶皮层 (机体识别)
- [ ] 小脑 (技能库)
- [ ] 边缘系统 (安全检验)
- [ ] 运动皮层 (代码生成)
- [ ] 海马体 (长期记忆)
- [ ] 视觉模块 (人脸识别)
- [ ] 通信与协作
- [ ] 集成测试与优化

## 论文投稿

本项目计划投稿至:
- IEEE Transactions on Robotics (TRO)
- Science Robotics

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或 PR。


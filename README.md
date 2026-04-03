# OpenERB - Open Embodied Robot Brain

**OpenERB** 是一个基于类脑架构的自主学习机器人控制系统。机器人能够基于自然语言指令自动生成控制代码，并通过技能学习和记忆实现不断进化。

一个完全自主的、自我进化的、具有多模态交互能力的机器人大脑。

## 📚 文档导航

| 文档 | 用途 | 用户 |
|------|------|------|
| [README.md](README.md) | 项目概览 | 所有人 |
| [QUICK_START.md](QUICK_START.md) | 3 分钟快速开始 | 新用户 |
| [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) | Phase 1 交付总结 | 项目经理 |
| [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) | 完整系统设计 + 安全架构 | 架构师/开发者 |
| [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) | 5 阶段开发路线图 | 项目规划 |
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

使用 **uv** (推荐):
```bash
# 使用 uv 创建虚拟环境 (比 venv 快得多)
uv venv --python 3.11
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 安装依赖
uv pip install -e .
```

或使用传统 pip:
```bash
# 1. 配置环境变量
export DASHSCOPE_API_KEY="sk-xxx"

# 2. 创建虚拟环境
python -m venv venv
source venv/activate

# 3. 安装依赖
pip install -e .

# 4. 初始化系统
python -m openerb.core.bootstrap init --robot-type G1
```

### 启动对话Agent

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
├── skills/                        # 技能库
│   ├── active/                    # 激活的技能
│   ├── deprecated/                # 弃用的技能
│   └── retired/                   # 垃圾箱
├── data/                          # 数据存储
│   ├── body_profiles/             # 机器人档案
│   ├── users/                     # 用户档案
│   └── memories/                  # 记忆与学习历史
├── tests/                         # 测试用例
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


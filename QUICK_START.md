# 快速启动指南 (Quick Start Guide)

## 环境设置 (Environment Setup)

### 1. 配置 API 密钥

```bash
# 导出阿里 DASHSCOPE API 密钥（已完成）
export DASHSCOPE_API_KEY="sk-xxx"

# 或创建 .env 文件
cp .env.example .env
# 编辑 .env 填入你的 API 密钥
```

### 2. 创建虚拟环境

```bash
cd /home/daojie/openerb/openerb

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 初始化系统

```bash
# 初始化系统（G1 机器人）
python -m openerb.core.bootstrap init --robot-type G1

# 或 Go2
python -m openerb.core.bootstrap init --robot-type Go2
```

### 5. 验证安装

```bash
# 检查系统状态
python -m openerb.core.bootstrap status

# 运行测试
pytest tests/ -v
```

## 项目结构概览

```
openerb/
├── core/                      # 核心框架
│   ├── types.py              # 数据类型定义
│   ├── config.py             # 配置管理
│   ├── logger.py             # 日志系统
│   ├── storage.py            # 数据存储
│   └── bootstrap.py          # 系统初始化
│
├── modules/                  # 类脑模块（待开发）
│   ├── prefrontal_cortex/    # 前额叶皮层 - 对话Agent
│   ├── insular_cortex/       # 岛叶皮层 - 机体识别
│   ├── limbic_system/        # 边缘系统 - 安全约束
│   ├── cerebellum/           # 小脑 - 技能库
│   ├── hippocampus/          # 海马体 - 长期记忆
│   ├── motor_cortex/         # 运动皮层 - 代码生成
│   ├── vision/               # 视觉模块
│   └── communication/        # 通信与协作
│
├── skills/                   # 技能库
│   ├── active/               # 激活的技能
│   ├── deprecated/           # 弃用的技能
│   └── retired/              # 垃圾箱
│
├── data/                     # 数据存储
│   ├── body_profiles/        # 机器人档案
│   ├── users/                # 用户档案
│   └── memories/             # 学习记忆
│
├── tests/                    # 测试
│   ├── conftest.py          # 测试配置和 fixtures
│   └── test_core.py         # 核心测试
│
├── docs/                     # 文档
│   ├── SYSTEM_ARCHITECTURE.md  # 系统架构
│   └── DEVELOPMENT_PLAN.md     # 开发计划
│
├── requirements.txt          # Python 依赖
├── README.md                # 项目简介
├── .env.example             # 环境变量示例
└── .gitignore               # Git 忽略规则
```

## 运行系统

### 测试存储层

```bash
python -m openerb.core.bootstrap test
```

### 启动对话 Agent（待实现）

```bash
python -m openerb
```

## 开发流程

### 添加新技能

1. 编写代码
2. 使用 storage API 保存：

```python
from openerb.core import get_storage, Skill, SkillStatus, SkillType

skill = Skill(
    name="move_forward",
    description="让机器人向前移动",
    code="...",
    status=SkillStatus.DRAFT,
    skill_type=SkillType.BODY_SPECIFIC,
)
get_storage().save_skill(skill)
```

### 开发新模块

1. 在 `modules/` 目录下创建新子模块
2. 在 `modules/__init__.py` 中导入
3. 编写模块接口
4. 编写单元测试

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_core.py::TestStorage::test_skill_save_and_load -v

# 显示覆盖率
pytest tests/ --cov=openerb
```

## 常见问题

### Q: 如何修改机器人类型？
A: 
```bash
python -m openerb.core.bootstrap init --robot-type Go2
```

### Q: 如何清空所有数据重新开始？
A:
```bash
rm -rf ~/openerb/data/*
python -m openerb.core.bootstrap init --robot-type G1
```

### Q: 如何查看日志？
A:
```bash
tail -f ~/openerb/logs/robot_system.log
```

## 下一步

1. ✅ **已完成**: 基础架构搭建
2. 📋 **下一步**: 开发前额叶皮层 (对话 Agent)
   - 集成 Qwen-VL-Plus
   - 实现意图识别
   - 实现任务分解

3. 继续按开发计划实现其他模块

详见 [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)

## 参考资源

- [系统架构文档](docs/SYSTEM_ARCHITECTURE.md)
- [开发计划](docs/DEVELOPMENT_PLAN.md)
- [Unitree SDK2 Python](https://github.com/unitreerobotics/unitree_sdk2_python)
- [Qwen 模型](https://huggingface.co/Qwen/Qwen-VL-Plus)


# OpenERB API 文档

## 概述

OpenERB 提供了完整的类脑机器人控制系统 API，支持从自然语言指令到机器人动作执行的完整流程。

## 核心组件

### 1. PrefrontalCortex - 前额叶皮层 (对话处理)

```python
from openerb.modules.prefrontal_cortex import PrefrontalCortex
from openerb.llm.config import LLMConfig

# 初始化
llm_client = LLMConfig.create_client()
cortex = PrefrontalCortex(llm_client=llm_client)

# 处理文本输入
result = await cortex.process_input(text="让机器人向前走一步")

# 处理多模态输入
with open("scene.jpg", "rb") as f:
    result = await cortex.process_input(text="抓住红色球", image=f.read())
```

**主要方法**:
- `process_input(text, image=None, user=None)` - 处理用户输入
- `get_conversation_history()` - 获取对话历史
- `clear_history()` - 清空对话历史

### 2. InsularCortex - 岛叶皮层 (机体认知)

```python
from openerb.modules.insular_cortex import InsularCortex
from openerb.core.types import RobotType

# 初始化并识别机器人
cortex = InsularCortex()
cortex.identify_robot("G1-EDU")

# 获取机器人信息
robot_type = cortex.get_robot_type()  # RobotType.G1
capabilities = cortex.get_capabilities()
is_compatible = cortex.can_run_skill(skill)
```

**主要方法**:
- `identify_robot(robot_name, firmware_version=None)` - 识别机器人型号
- `get_capabilities()` - 获取机器人能力
- `can_run_skill(skill)` - 检查技能兼容性

### 3. Cerebellum - 小脑 (技能记忆)

```python
from openerb.modules.cerebellum import Cerebellum

# 初始化
cerebellum = Cerebellum()

# 注册技能
skill_id = cerebellum.register_skill(skill, robot_type)

# 搜索技能
existing = cerebellum.search_skill("move_forward", robot_type=RobotType.G1)

# 获取技能
skill_data = cerebellum.get_skill(skill_id)
```

**主要方法**:
- `register_skill(skill, robot_type, description=None)` - 注册新技能
- `search_skill(query, robot_type=None)` - 搜索现有技能
- `get_skill(skill_id)` - 获取技能数据

### 4. Hippocampus - 海马体 (学习记忆)

```python
from openerb.modules.hippocampus import Hippocampus

# 初始化
hippocampus = Hippocampus()

# 创建用户档案
hippocampus.create_user_profile(user_id, name, robot_type)

# 开始学习会话
hippocampus.start_learning(user_id, skill)

# 记录学习事件
hippocampus.record_event(user_id, skill_id, event_type, data)
```

**主要方法**:
- `create_user_profile(user_id, name, robot_type)` - 创建用户学习档案
- `start_learning(user_id, skill)` - 开始技能学习
- `record_event(user_id, skill_id, event_type, data)` - 记录学习事件

### 5. CommunicationModule - 通信模块

```python
from openerb.modules.communication import CommunicationModule

# 初始化
comm = CommunicationModule()

# 注册节点
node = CommunicationNode(node_id="robot_1", robot_type=RobotType.G1, address="192.168.1.100")
comm.register_node(node)

# 发现对等节点
peers = comm.discover_nodes(robot_type=RobotType.G1)

# 共享技能
comm.share_skill(skill_id, target_node_id)
```

**主要方法**:
- `register_node(node)` - 注册通信节点
- `discover_nodes(robot_type=None)` - 发现对等节点
- `share_skill(skill_id, target_node_id)` - 共享技能

### 6. MotorCortex - 运动皮层 (代码生成)

```python
from openerb.modules.motor_cortex import MotorCortex

# 初始化
motor = MotorCortex(simulation_mode=True)

# 生成技能
skill = await motor.generate_skill(intent)

# 执行代码
result = await motor.execute_skill(skill, robot_type=RobotType.G1)
```

**主要方法**:
- `generate_skill(intent)` - 从意图生成技能代码
- `execute_skill(skill, robot_type)` - 执行技能代码

### 7. VisualCortex - 视觉皮层

```python
from openerb.modules.visual_cortex import VisualCortex

# 初始化
visual = VisualCortex()

# 处理图像
with open("scene.jpg", "rb") as f:
    image_data = f.read()

analysis = await visual.analyze_scene(image_data)
objects = visual.detect_objects(image_data)
```

**主要方法**:
- `analyze_scene(image_data)` - 分析场景
- `detect_objects(image_data)` - 检测物体
- `recognize_faces(image_data)` - 人脸识别

### 8. LimbicSystem - 边缘系统 (安全控制)

```python
from openerb.modules.limbic_system import LimbicSystem

# 初始化
limbic = LimbicSystem()

# 评估安全性
assessment = await limbic.evaluate_safety(action, context)

# 请求确认
if assessment.level == SafetyLevel.YELLOW:
    confirmed = await limbic.request_confirmation(action, assessment)
```

**主要方法**:
- `evaluate_safety(action, context)` - 评估动作安全性
- `request_confirmation(action, assessment)` - 请求用户确认

### 9. IntegrationEngine - 系统集成引擎

```python
from openerb.modules.system_integration import IntegrationEngine

# 初始化
engine = IntegrationEngine()

# 执行端到端意图处理
result = await engine.execute_intent(intent, user, robot_type)
```

**主要方法**:
- `execute_intent(intent, user, robot_type)` - 执行完整意图处理流程

## 数据类型

### 核心类型

```python
from openerb.core.types import (
    Intent, UserProfile, RobotType, Skill, SkillStatus,
    SafetyLevel, CommunicationNode, ImageAnnotation
)

# Intent - 用户意图
intent = Intent(
    raw_text="Move forward",
    action="move_forward",
    parameters={"distance": 1.0, "speed": 0.5},
    confidence=0.9
)

# Skill - 可执行技能
skill = Skill(
    name="forward_movement",
    description="Move robot forward",
    code="robot.move_forward(distance, speed)",
    skill_type=SkillType.UNIVERSAL,
    supported_robots=[RobotType.G1, RobotType.Go2]
)

# UserProfile - 用户档案
user = UserProfile(
    user_id="user_123",
    name="Alice",
    preferences={"language": "zh"}
)
```

## 配置管理

### 环境变量

```bash
# LLM 配置
export LLM_PROVIDER=dashscope  # 或 openai, vllm
export LLM_API_KEY="sk-xxxxx"
export LLM_MODEL=qwen-vl-plus

# 机器人配置
export ROBOT_TYPE=G1
export ROBOT_ADDRESS=192.168.1.100

# 系统配置
export OPENERB_LOG_LEVEL=INFO
export OPENERB_STORAGE_PATH=./data
```

### 程序化配置

```python
from openerb.core.config import SystemConfig

config = SystemConfig()
config.robot_type = RobotType.G1
config.storage_path = "./data"
config.save()
```

## 错误处理

OpenERB 使用标准的 Python 异常处理：

```python
try:
    result = await cortex.process_input(text="危险操作")
except SafetyException as e:
    print(f"安全异常: {e}")
except NetworkException as e:
    print(f"网络异常: {e}")
except ValidationError as e:
    print(f"验证错误: {e}")
```

## 异步编程

所有 I/O 操作都是异步的：

```python
import asyncio

async def main():
    cortex = PrefrontalCortex(llm_client=client)
    result = await cortex.process_input(text="Hello")
    print(result)

asyncio.run(main())
```

## 最佳实践

1. **总是使用适当的异常处理**
2. **在生产环境中启用安全评估**
3. **定期备份技能和学习数据**
4. **监控系统资源使用情况**
5. **使用类型提示提高代码质量**
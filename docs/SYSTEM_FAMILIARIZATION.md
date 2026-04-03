# OpenERB 系统功能熟悉指南

## 概述

本指南帮助你快速熟悉 OpenERB 系统的各项功能，包括核心模块、技能系统、学习机制和集成工作流。

## 核心模块介绍

### 1. 岛叶皮层 (Insular Cortex) - 机器人识别与能力管理

```python
from openerb.modules.insular_cortex import InsularCortex

# 初始化
cortex = InsularCortex()

# 识别机器人
robot_info = cortex.identify_robot(
    model="G1-EDU",
    firmware_version="1.5.0",
    hardware_version="2.1"
)

print(f"机器人类型: {robot_info.type}")
print(f"能力列表: {robot_info.capabilities}")
print(f"限制条件: {robot_info.constraints}")

# 获取特定能力
joint_limits = cortex.get_capability("joint_limits")
max_payload = cortex.get_capability("max_payload")
battery_life = cortex.get_capability("battery_life")
```

**主要功能:**
- 机器人型号识别和验证
- 硬件能力查询和管理
- 安全限制和约束检查
- 固件兼容性验证

### 2. 运动皮层 (Motor Cortex) - 运动控制和技能执行

```python
from openerb.modules.motor_cortex import MotorCortex
from openerb.core.types import Skill, SkillType

# 初始化运动控制器
motor = MotorCortex(simulation_mode=False)

# 创建基础运动技能
walk_skill = Skill(
    name="walk_forward",
    description="向前行走 1 米",
    code="""
import time

# 设置步态参数
robot.set_gait_parameters(
    step_height=0.05,
    step_length=0.3,
    speed=0.5
)

# 执行行走
robot.walk_forward(distance=1.0, speed=0.5)
time.sleep(2)  # 等待完成

# 停止
robot.stop()
""",
    skill_type=SkillType.MOTOR,
    parameters={
        "distance": {"type": "float", "default": 1.0, "min": 0.1, "max": 5.0},
        "speed": {"type": "float", "default": 0.5, "min": 0.1, "max": 1.0}
    }
)

# 注册并执行技能
skill_id = motor.register_skill(walk_skill)
result = await motor.execute_skill(skill_id, {"distance": 2.0, "speed": 0.3})

print(f"技能执行结果: {result.status}")
print(f"执行时间: {result.execution_time}s")
```

**主要功能:**
- 基础运动控制 (行走、转向、停止)
- 复杂技能执行
- 实时运动规划和优化
- 安全监控和异常处理

### 3. 视觉皮层 (Visual Cortex) - 视觉感知和理解

```python
from openerb.modules.visual_cortex import VisualCortex
import asyncio

# 初始化视觉系统
visual = VisualCortex()

async def demonstrate_vision():
    # 捕获图像
    image_data = await visual.capture_image()
    print(f"图像尺寸: {image_data.shape}")

    # 物体检测
    detections = await visual.detect_objects(image_data)
    for detection in detections:
        print(f"检测到: {detection.label} "
              f"(置信度: {detection.confidence:.2f}, "
              f"位置: {detection.bbox})")

    # 场景理解
    scene_analysis = await visual.analyze_scene(image_data)
    print(f"场景描述: {scene_analysis.description}")
    print(f"主要物体: {scene_analysis.main_objects}")
    print(f"空间布局: {scene_analysis.spatial_layout}")

    # 目标跟踪
    if detections:
        target = detections[0]
        tracker = visual.create_tracker(target)
        tracked_positions = []

        for _ in range(10):  # 跟踪10帧
            frame = await visual.capture_image()
            position = await tracker.update(frame)
            tracked_positions.append(position)

        print(f"跟踪轨迹: {tracked_positions}")

# 运行演示
asyncio.run(demonstrate_vision())
```

**主要功能:**
- 实时图像捕获和处理
- 物体检测和识别
- 场景理解和语义分析
- 目标跟踪和运动预测
- 深度感知和3D重建

### 4. 小脑 (Cerebellum) - 技能学习和协调

```python
from openerb.modules.cerebellum import Cerebellum
from openerb.core.types import Skill, SkillType, RobotType

# 初始化技能系统
cerebellum = Cerebellum()

# 创建复合技能
grasp_and_place_skill = Skill(
    name="grasp_and_place",
    description="抓取物体并放置到指定位置",
    code="""
# 视觉引导抓取
objects = await visual.detect_objects()
if not objects:
    raise Exception("未检测到物体")

target_object = objects[0]  # 选择第一个物体

# 计算抓取姿态
grasp_pose = await motor.calculate_grasp_pose(target_object)

# 执行抓取
await motor.execute_grasp(grasp_pose)

# 移动到放置位置
await motor.move_to_position(target_position)

# 释放物体
await motor.release_object()
""",
    skill_type=SkillType.UNIVERSAL,
    dependencies=["visual_cortex", "motor_cortex"],
    parameters={
        "target_position": {
            "type": "dict",
            "properties": {
                "x": {"type": "float"},
                "y": {"type": "float"},
                "z": {"type": "float"}
            }
        }
    }
)

# 注册技能
skill_id = cerebellum.register_skill(grasp_and_place_skill, RobotType.G1)

# 技能组合
pick_skill = cerebellum.get_skill("pick_object")
place_skill = cerebellum.get_skill("place_object")

combined_skill = cerebellum.combine_skills(
    [pick_skill, place_skill],
    name="pick_and_place",
    description="拿起并放置物体"
)

print(f"组合技能创建成功: {combined_skill.skill_id}")
```

**主要功能:**
- 技能注册和管理
- 技能组合和编排
- 依赖关系解析
- 技能优化和缓存

### 5. 海马体 (Hippocampus) - 记忆和学习

```python
from openerb.modules.hippocampus import Hippocampus
from openerb.core.types import UserProfile, LearningEvent

# 初始化记忆系统
hippocampus = Hippocampus()

# 创建用户档案
user = UserProfile(
    user_id="operator_001",
    name="张三",
    preferences={
        "language": "zh-CN",
        "skill_level": "intermediate",
        "preferred_actions": ["grasp", "navigate", "communicate"]
    }
)

hippocampus.create_user_profile(
    user.user_id,
    user.name,
    RobotType.G1,
    user.preferences
)

# 记录学习事件
learning_event = LearningEvent(
    user_id=user.user_id,
    skill_name="grasp_red_ball",
    context="用户第一次学习抓取红色球体",
    success=True,
    execution_time=3.2,
    feedback="抓取成功，但动作可以更流畅"
)

hippocampus.record_learning_event(learning_event)

# 分析学习模式
learning_patterns = hippocampus.analyze_learning_patterns(user.user_id)
print(f"学习偏好: {learning_patterns.preferences}")
print(f"技能掌握度: {learning_patterns.skill_mastery}")
print(f"改进建议: {learning_patterns.improvements}")

# 个性化推荐
recommendations = hippocampus.get_personalized_recommendations(user.user_id)
for rec in recommendations:
    print(f"推荐技能: {rec.skill_name} (置信度: {rec.confidence})")
```

**主要功能:**
- 用户档案管理
- 学习事件记录和分析
- 个性化推荐系统
- 技能掌握度评估

### 6. 通信模块 (Communication) - 多机器人协作

```python
from openerb.modules.communication import CommunicationModule
from openerb.core.types import CommunicationNode, Message

# 初始化通信系统
comm = CommunicationModule()

# 注册本机器人节点
local_node = CommunicationNode(
    node_id="robot_g1_001",
    robot_type=RobotType.G1,
    address="192.168.123.161",
    capabilities=["motion", "vision", "manipulation"],
    status="active"
)

comm.register_node(local_node)

# 发现网络中的其他机器人
discovered_nodes = comm.discover_nodes()
print(f"发现 {len(discovered_nodes)} 个机器人节点")

for node in discovered_nodes:
    print(f"- {node.node_id}: {node.robot_type} @ {node.address}")

# 发送协作任务
if discovered_nodes:
    task_message = Message(
        message_id="task_001",
        sender_id=local_node.node_id,
        receiver_id=discovered_nodes[0].node_id,
        message_type="task_request",
        content={
            "task": "assist_grasp",
            "description": "协助抓取大型物体",
            "parameters": {
                "object_position": [1.0, 0.5, 0.0],
                "required_force": 50.0
            }
        },
        timestamp=datetime.now()
    )

    comm.send_message(task_message)

    # 等待响应
    response = await comm.wait_for_response(task_message.message_id, timeout=10.0)
    if response:
        print(f"收到响应: {response.content}")
    else:
        print("任务超时")
```

**主要功能:**
- 机器人节点发现和管理
- 消息传递和路由
- 协作任务协调
- 状态同步和监控

## 集成工作流示例

### 1. 简单任务执行

```python
from openerb.modules.system_integration import IntegrationEngine
from openerb.core.types import Intent

# 初始化集成引擎
engine = IntegrationEngine()

# 创建用户意图
intent = Intent(
    raw_text="帮我把那个红色的杯子拿到桌子上",
    action="move_object",
    parameters={
        "object": "red_cup",
        "source": "current_location",
        "target": "table"
    },
    confidence=0.85
)

# 执行意图
user = UserProfile(user_id="user_001", name="操作员")
result = await engine.execute_intent(intent, user, RobotType.G1)

print("=== 执行结果 ===")
print(f"意图: {result['intent'].action}")
print(f"使用的技能: {result['skill'].name}")
print(f"执行状态: {result['status']}")
print(f"执行时间: {result['execution_time']:.2f}秒")

if result['learning_event']:
    print(f"学习记录: {result['learning_event'].context}")
```

### 2. 复杂协作任务

```python
# 多机器人协作场景
async def collaborative_task():
    # 场景: 两个机器人协作搬运大型物体

    # 机器人A (G1) - 主要执行者
    robot_a = IntegrationEngine()
    robot_a.register_node("robot_a", RobotType.G1)

    # 机器人B (Go2) - 辅助者
    robot_b = IntegrationEngine()
    robot_b.register_node("robot_b", RobotType.Go2)

    # 任务分解
    tasks = [
        {
            "robot": "robot_a",
            "intent": Intent("定位大型物体", "locate_object",
                           {"object": "large_box"}, 0.9)
        },
        {
            "robot": "robot_b",
            "intent": Intent("提供辅助支撑", "provide_support",
                           {"position": "adjacent"}, 0.9)
        },
        {
            "robot": "robot_a",
            "intent": Intent("协同搬运物体", "collaborative_carry",
                           {"target": "storage_area"}, 0.9)
        }
    ]

    # 协调执行
    results = []
    for task in tasks:
        if task["robot"] == "robot_a":
            result = await robot_a.execute_intent(
                task["intent"], user, RobotType.G1)
        else:
            result = await robot_b.execute_intent(
                task["intent"], user, RobotType.Go2)

        results.append(result)

        # 检查是否需要调整策略
        if not result["success"]:
            # 重新规划任务
            adjustment = await robot_a.replan_task(task["intent"], result)
            if adjustment:
                task["intent"] = adjustment

    return results

# 执行协作任务
results = await collaborative_task()
for i, result in enumerate(results):
    print(f"任务 {i+1}: {'成功' if result['success'] else '失败'}")
```

### 3. 学习和适应

```python
# 学习新技能的工作流
async def learn_new_skill():
    # 初始化各模块
    cerebellum = Cerebellum()
    hippocampus = Hippocampus()
    motor = MotorCortex()

    # 步骤1: 演示学习
    print("=== 技能学习演示 ===")

    # 创建学习任务
    learning_task = {
        "skill_name": "wave_hello",
        "description": "挥手打招呼",
        "demonstrations": [
            # 第一次演示
            {
                "trajectory": [
                    {"joint_angles": [0, 0, 0, 0, 0, 0], "timestamp": 0.0},
                    {"joint_angles": [0, 0.5, 0, 0, 0, 0], "timestamp": 0.5},
                    {"joint_angles": [0, 0, 0, 0, 0, 0], "timestamp": 1.0}
                ],
                "success": True
            }
        ]
    }

    # 记录学习事件
    user = UserProfile(user_id="trainer_001", name="培训师")
    hippocampus.start_learning(user.user_id, learning_task["skill_name"])

    # 步骤2: 技能泛化
    print("=== 技能泛化 ===")

    # 从演示中学习
    skill = cerebellum.learn_from_demonstration(
        learning_task["demonstrations"],
        skill_name=learning_task["skill_name"]
    )

    # 优化技能参数
    optimized_skill = cerebellum.optimize_skill(skill, RobotType.G1)

    # 步骤3: 验证学习
    print("=== 技能验证 ===")

    # 执行学习到的技能
    result = await motor.execute_skill(optimized_skill.skill_id)

    # 记录学习结果
    learning_event = LearningEvent(
        user_id=user.user_id,
        skill_name=skill.name,
        context="通过演示学习挥手技能",
        success=result.status == "success",
        execution_time=result.execution_time,
        feedback="技能执行流畅" if result.status == "success" else "需要调整"
    )

    hippocampus.record_learning_event(learning_event)

    # 步骤4: 个性化调整
    print("=== 个性化调整 ===")

    # 基于用户偏好调整技能
    personalized_skill = hippocampus.personalize_skill(
        optimized_skill,
        user.user_id
    )

    print(f"学习完成! 掌握度: {hippocampus.get_skill_mastery(user.user_id, skill.name)}")

    return personalized_skill

# 执行学习流程
learned_skill = await learn_new_skill()
```

## 实用工具和调试

### 1. 系统监控

```python
from openerb.core.monitor import SystemMonitor

# 启动系统监控
monitor = SystemMonitor()
monitor.start_monitoring()

# 获取实时状态
status = monitor.get_system_status()
print(f"""
系统状态:
CPU 使用率: {status.cpu_percent}%
内存使用率: {status.memory_percent}%
活跃技能数: {status.active_skill_count}
网络连接数: {status.network_connections}
""")

# 性能指标
metrics = monitor.get_performance_metrics()
for metric_name, value in metrics.items():
    print(f"{metric_name}: {value}")
```

### 2. 配置管理

```python
from openerb.core.config import SystemConfig, RobotConfig

# 系统级配置
sys_config = SystemConfig()
sys_config.debug_mode = True
sys_config.log_level = "DEBUG"
sys_config.save()

# 机器人特定配置
robot_config = RobotConfig()
robot_config.robot_type = RobotType.G1
robot_config.max_speed = 1.0
robot_config.safety_limits = {
    "max_force": 100.0,
    "max_velocity": 2.0
}
robot_config.save()

# 验证配置
print("配置验证:")
print(f"调试模式: {sys_config.debug_mode}")
print(f"机器人类型: {robot_config.robot_type}")
print(f"最大速度: {robot_config.max_speed}")
```

### 3. 日志和调试

```python
import logging
from openerb.core.logger import setup_logging

# 配置详细日志
setup_logging(
    level="DEBUG",
    file_path="debug.log",
    console=True,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 创建调试会话
logger = logging.getLogger("openerb.debug")

def debug_function(func):
    async def wrapper(*args, **kwargs):
        logger.debug(f"调用 {func.__name__} 参数: {args}, {kwargs}")
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} 执行成功, 耗时: {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败, 耗时: {execution_time:.3f}s, 错误: {e}")
            raise

    return wrapper

# 使用调试装饰器
@debug_function
async def test_skill_execution():
    # 测试代码...
    pass
```

## 最佳实践

### 1. 技能开发

- **模块化**: 将复杂技能分解为可重用的子技能
- **参数化**: 使用参数使技能更灵活和可配置
- **错误处理**: 为所有技能添加适当的异常处理
- **测试**: 为每个技能编写单元测试和集成测试

### 2. 系统集成

- **异步优先**: 使用 async/await 进行所有 I/O 操作
- **资源管理**: 正确管理连接和资源释放
- **监控**: 实施全面的监控和日志记录
- **容错**: 设计系统以优雅地处理失败

### 3. 用户体验

- **反馈**: 为所有操作提供清晰的用户反馈
- **进度**: 显示长时间运行任务的进度
- **撤销**: 允许用户撤销或修改操作
- **个性化**: 根据用户偏好定制行为

### 4. 性能优化

- **缓存**: 缓存频繁访问的数据和计算结果
- **并发**: 使用并发执行独立任务
- **资源限制**: 实施资源使用限制以防止系统过载
- **监控**: 持续监控性能并识别瓶颈

这个功能熟悉指南提供了 OpenERB 系统核心功能的全面介绍和实用示例，帮助你快速上手和有效使用系统。
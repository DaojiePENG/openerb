# OpenERB 真机部署快速开始指南

## 概述

本指南帮助你在 30 分钟内完成 OpenERB 系统在真实 Unitree 机器人上的部署和基本功能验证。

## 前置要求

### 硬件要求
- Unitree G1 或 Go2 机器人
- 稳定的网络连接 (WiFi 或以太网)
- 开发电脑 (Ubuntu 20.04+ 或 macOS)

### 软件要求
- Python 3.9+
- Git
- SSH 客户端

## 步骤 1: 环境准备 (5 分钟)

### 1.1 克隆项目
```bash
cd ~
git clone https://github.com/your-org/openerb.git
cd openerb
```

### 1.2 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 OpenERB
pip install -e .
```

### 1.3 验证安装
```bash
python -c "import openerb; print('✅ OpenERB 安装成功')"
```

## 步骤 2: 机器人连接 (5 分钟)

### 2.1 连接机器人网络

#### G1 机器人:
```bash
# 连接 WiFi
# SSID: Unitree_G1_XXXX
# 密码: (通常为空或 123456)

# SSH 连接
ssh unitree@192.168.123.161
# 密码: 123 或根据配置
```

#### Go2 机器人:
```bash
# 连接 WiFi
# SSID: Unitree_Go2_XXXX
# 密码: (通常为空或 123456)

# SSH 连接
ssh unitree@192.168.12.1
# 密码: 123 或根据配置
```

### 2.2 验证连接
```bash
# 在机器人上运行
ping -c 3 8.8.8.8  # 测试网络连接

# 检查机器人状态
python3 -c "
import unitree_sdk
print('✅ Unitree SDK 可用')
"
```

## 步骤 3: 系统配置 (5 分钟)

### 3.1 基本配置
```python
# 在开发电脑上运行
from openerb.core.config import RobotConfig, NetworkConfig

# 机器人配置
config = RobotConfig()
config.robot_type = "G1"  # 或 "Go2"
config.robot_address = "192.168.123.161"  # G1 IP
config.robot_port = 8080
config.save()

# 网络配置
net_config = NetworkConfig()
net_config.enable_mdns = True
net_config.save()

print("✅ 配置完成")
```

### 3.2 验证配置
```python
from openerb.modules.insular_cortex import InsularCortex

cortex = InsularCortex()
robot_info = cortex.identify_robot("G1-EDU", firmware_version="1.5.0")
print(f"机器人类型: {robot_info.type}")
print(f"能力: {list(robot_info.capabilities.keys())}")
```

## 步骤 4: 基础功能测试 (10 分钟)

### 4.1 运行自动化测试
```bash
# 运行真机部署测试脚本
python scripts/robot_deployment_test.py \
    --robot-type G1 \
    --robot-ip 192.168.123.161 \
    --log-level INFO
```

### 4.2 手动测试基础功能

#### 运动测试
```python
from openerb.modules.motor_cortex import MotorCortex

motor = MotorCortex(simulation_mode=False)

# 创建行走技能
skill_code = """
import time
robot.walk_forward(distance=0.5, speed=0.3)
time.sleep(1)
robot.stop()
"""

skill = motor.create_skill("test_walk", skill_code)
result = await motor.execute_skill(skill.skill_id)
print(f"运动测试: {'成功' if result.status == 'success' else '失败'}")
```

#### 视觉测试
```python
from openerb.modules.visual_cortex import VisualCortex

visual = VisualCortex()

# 捕获和分析图像
image = await visual.capture_image()
detections = await visual.detect_objects(image)
print(f"检测到 {len(detections)} 个物体")
```

#### 技能测试
```python
from openerb.modules.cerebellum import Cerebellum

cerebellum = Cerebellum()

# 注册简单技能
skill = cerebellum.create_skill(
    name="hello",
    code="robot.speak('你好，我是机器人')",
    skill_type="universal"
)

print(f"技能注册成功: {skill.skill_id}")
```

## 步骤 5: 集成测试 (5 分钟)

### 5.1 端到端意图执行
```python
from openerb.modules.system_integration import IntegrationEngine
from openerb.core.types import Intent, UserProfile

engine = IntegrationEngine()

# 创建意图
intent = Intent(
    raw_text="请帮我向前走两步",
    action="walk_forward",
    parameters={"distance": 1.0, "speed": 0.4},
    confidence=0.9
)

user = UserProfile(user_id="operator", name="操作员")

# 执行意图
result = await engine.execute_intent(intent, user, "G1")

print("=== 执行结果 ===")
print(f"状态: {result['status']}")
print(f"技能: {result['skill']['name']}")
print(f"执行时间: {result['execution_time']:.2f}秒")
```

### 5.2 多模块协作测试
```python
# 视觉引导运动测试
async def vision_guided_motion():
    # 检测物体
    objects = await visual.detect_objects(await visual.capture_image())

    if objects:
        target = objects[0]
        print(f"发现目标: {target.label}")

        # 计算运动路径
        path = await motor.calculate_path_to_object(target)

        # 执行运动
        await motor.follow_path(path)
        print("✅ 视觉引导运动完成")
    else:
        print("⚠️ 未检测到物体")

await vision_guided_motion()
```

## 步骤 6: 监控和调试 (5 分钟)

### 6.1 启动系统监控
```python
from openerb.core.monitor import SystemMonitor

monitor = SystemMonitor()
monitor.start_monitoring()

# 查看系统状态
status = monitor.get_system_status()
print(f"CPU: {status.cpu_percent}%")
print(f"内存: {status.memory_percent}%")
print(f"活跃任务: {status.active_skill_count}")
```

### 6.2 日志配置
```python
import logging
from openerb.core.logger import setup_logging

# 配置详细日志
setup_logging(
    level="DEBUG",
    file_path="robot_debug.log",
    console=True
)

print("✅ 日志系统已启动")
```

### 6.3 性能分析
```bash
# 运行性能基准测试
python -c "
import asyncio
from scripts.robot_deployment_test import RobotDeploymentTester
from openerb.core.types import RobotType

tester = RobotDeploymentTester(RobotType.G1, '192.168.123.161')
result = asyncio.run(tester.test_system_monitoring())
print('性能测试完成')
"
```

## 故障排除

### 常见问题

#### 1. 连接失败
```bash
# 检查网络
ping 192.168.123.161

# 检查 SSH
ssh -v unitree@192.168.123.161

# 检查防火墙
sudo ufw status
```

#### 2. SDK 初始化失败
```python
# 检查 SDK 版本
import unitree_sdk
print(unitree_sdk.__version__)

# 验证机器人固件
cortex = InsularCortex()
cortex.identify_robot('G1-EDU', firmware_version='1.5.0')
```

#### 3. 运动控制异常
```python
# 检查关节状态
status = motor.get_joint_status()
print(f"关节状态: {status}")

# 验证安全限制
limits = cortex.get_capability('joint_limits')
print(f"关节限制: {limits}")
```

#### 4. 视觉系统无响应
```bash
# 检查相机设备
ls /dev/video*

# 测试相机
gst-launch-1.0 v4l2src device=/dev/video0 ! videoconvert ! autovideosink
```

### 调试命令
```bash
# 查看系统日志
tail -f robot_debug.log

# 检查进程状态
ps aux | grep python

# 查看网络连接
netstat -tlnp | grep :8080

# 重启机器人服务
sudo systemctl restart unitree_sdk
```

## 下一步

恭喜！你已经成功完成了 OpenERB 系统的基本部署。现在你可以：

1. **深入学习**: 阅读 [系统功能熟悉指南](SYSTEM_FAMILIARIZATION.md)
2. **高级配置**: 查看 [真机部署调试指南](ROBOT_DEPLOYMENT_DEBUG.md)
3. **开发技能**: 开始创建自定义机器人技能
4. **集成应用**: 将 OpenERB 集成到你的应用中

## 性能基准

在标准配置下，系统应该达到以下性能指标：

- **初始化时间**: < 5 秒
- **意图响应时间**: < 2 秒
- **技能执行时间**: < 10 秒 (取决于复杂度)
- **CPU 使用率**: < 30%
- **内存使用率**: < 200MB

如果你的系统性能明显低于这些指标，请检查配置和硬件。

## 获取帮助

- **文档**: 查看 `docs/` 目录下的完整文档
- **日志**: 检查 `robot_debug.log` 文件
- **测试**: 运行 `python scripts/robot_deployment_test.py` 进行诊断
- **社区**: 访问项目仓库获取社区支持

祝你部署顺利！ 🤖
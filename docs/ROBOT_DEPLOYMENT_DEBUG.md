# OpenERB 真机部署调试指南

## 概述

本指南帮助你在真实的 Unitree 机器人（G1、Go2）上部署和调试 OpenERB 系统。

## 环境准备

### 1. 机器人连接

#### Unitree G1 连接
```bash
# 连接机器人 WiFi
# SSID: Unitree_G1_XXXX
# 默认 IP: 192.168.123.161

# SSH 连接 (如果启用)
ssh unitree@192.168.123.161
# 密码: 123 或根据配置
```

#### Unitree Go2 连接
```bash
# 连接机器人 WiFi
# SSID: Unitree_Go2_XXXX
# 默认 IP: 192.168.12.1

# SSH 连接
ssh unitree@192.168.12.1
```

### 2. 开发环境设置

```bash
# 在机器人上安装 Python 和依赖
sudo apt update
sudo apt install python3 python3-pip python3-venv

# 创建虚拟环境
python3 -m venv ~/openerb_env
source ~/openerb_env/bin/activate

# 安装 OpenERB
pip install /path/to/openerb/wheel.whl
# 或从源码安装
pip install -e /path/to/openerb
```

## 系统配置

### 1. 机器人配置

```python
from openerb.core.config import RobotConfig

# G1 配置
config = RobotConfig()
config.robot_type = RobotType.G1
config.robot_address = "192.168.123.161"
config.robot_port = 8080  # G1 SDK 端口
config.save()

# Go2 配置
config = RobotConfig()
config.robot_type = RobotType.Go2
config.robot_address = "192.168.12.1"
config.robot_port = 8082  # Go2 SDK 端口
config.save()
```

### 2. 网络配置

```python
from openerb.core.config import NetworkConfig

config = NetworkConfig()
config.enable_mdns = True  # 启用多播 DNS 用于机器人发现
config.broadcast_port = 9999  # 广播端口
config.heartbeat_interval = 30  # 心跳间隔(秒)
config.save()
```

## 功能调试

### 1. 基础连接测试

```python
# 测试机器人连接
from openerb.modules.insular_cortex import InsularCortex

cortex = InsularCortex()
try:
    cortex.identify_robot("G1-EDU", firmware_version="1.5.0")
    print("✅ 机器人识别成功")
    print(f"机型: {cortex.get_robot_type()}")
    print(f"能力: {cortex.get_capabilities()}")
except Exception as e:
    print(f"❌ 连接失败: {e}")
```

### 2. 运动控制测试

```python
# 基础运动测试
from openerb.modules.motor_cortex import MotorCortex

motor = MotorCortex(simulation_mode=False)  # 真机模式

# 创建简单移动技能
skill = Skill(
    name="forward_test",
    description="向前移动测试",
    code="""
import time
robot.move_forward(distance=0.5, speed=0.3)
time.sleep(1)
robot.stop()
""",
    skill_type=SkillType.UNIVERSAL
)

# 执行技能
try:
    result = await motor.execute_skill(skill)
    print("✅ 运动控制成功")
except Exception as e:
    print(f"❌ 运动控制失败: {e}")
```

### 3. 视觉系统测试

```python
# 相机测试
from openerb.modules.visual_cortex import VisualCortex

visual = VisualCortex()

try:
    # 获取相机图像
    image_data = await visual.capture_image()
    print("✅ 相机捕获成功")

    # 物体检测
    detections = await visual.detect_objects(image_data)
    print(f"检测到 {len(detections)} 个物体")

    # 场景理解
    analysis = await visual.analyze_scene(image_data)
    print(f"场景: {analysis.description}")

except Exception as e:
    print(f"❌ 视觉系统失败: {e}")
```

### 4. 通信系统测试

```python
# 机器人间通信测试
from openerb.modules.communication import CommunicationModule

comm = CommunicationModule()

# 注册本机器人
node = CommunicationNode(
    node_id="robot_001",
    robot_type=RobotType.G1,
    address="192.168.123.161"
)
comm.register_node(node)

# 发现其他机器人
peers = comm.discover_nodes()
print(f"发现 {len(peers)} 个对等节点")

# 发送测试消息
if peers:
    test_message = {
        "type": "test",
        "data": "Hello from robot_001"
    }
    comm.send_message(peers[0].node_id, test_message)
    print("✅ 消息发送成功")
```

### 5. 技能学习测试

```python
# 技能学习和记忆测试
from openerb.modules.cerebellum import Cerebellum
from openerb.modules.hippocampus import Hippocampus

cerebellum = Cerebellum()
hippocampus = Hippocampus()

# 创建测试技能
skill = Skill(
    name="grasp_test",
    description="抓取测试技能",
    code="robot.grasp_object()",
    skill_type=SkillType.UNIVERSAL
)

# 注册技能
skill_id = cerebellum.register_skill(skill, RobotType.G1)
print(f"技能注册成功: {skill_id}")

# 记录学习事件
user = UserProfile(user_id="test_user", name="Test User")
hippocampus.create_user_profile(user.user_id, user.name, RobotType.G1)
hippocampus.start_learning(user.user_id, skill)

print("✅ 技能学习记录成功")
```

## 端到端集成测试

### 1. 完整工作流测试

```python
# 端到端意图处理测试
from openerb.modules.system_integration import IntegrationEngine
from openerb.core.types import Intent

engine = IntegrationEngine()

# 创建意图
intent = Intent(
    raw_text="帮我抓起那个红色的球",
    action="grasp_red_ball",
    parameters={"color": "red", "object": "ball"},
    confidence=0.9
)

user = UserProfile(user_id="operator_001", name="Robot Operator")

try:
    # 执行意图
    result = await engine.execute_intent(intent, user, RobotType.G1)

    print("✅ 意图执行成功")
    print(f"意图: {result['intent']}")
    print(f"技能: {result['skill']['name']}")
    print(f"来源: {'现有技能' if result['from_existing'] else '新生成'}")

except Exception as e:
    print(f"❌ 意图执行失败: {e}")
    import traceback
    traceback.print_exc()
```

### 2. 多机器人协作测试

```python
# 多机器人协作测试
from openerb.modules.communication import CommunicationModule

# 机器人 A (G1)
comm_a = CommunicationModule()
comm_a.register_node(CommunicationNode("robot_A", RobotType.G1, "192.168.123.161"))

# 机器人 B (Go2)
comm_b = CommunicationModule()
comm_b.register_node(CommunicationNode("robot_B", RobotType.Go2, "192.168.12.1"))

# 技能共享测试
skill = Skill(name="shared_skill", description="共享技能", code="pass")

# 机器人 A 打包技能
pkg = comm_a.skill_sharing.package_skill(skill, comm_a.nodes["robot_A"])

# 发送给机器人 B
comm_a.share_skill(pkg.skill.skill_id, "robot_B")

# 机器人 B 接收
received_skill = comm_b.skill_sharing.receive_skill(pkg.skill.skill_id)
print(f"✅ 技能共享成功: {received_skill.name}")
```

## 调试工具

### 1. 系统状态监控

```python
# 实时监控系统状态
from openerb.core.monitor import SystemMonitor

monitor = SystemMonitor()
monitor.start_monitoring()

# 获取状态
status = monitor.get_system_status()
print(f"CPU: {status.cpu_percent}%")
print(f"内存: {status.memory_percent}%")
print(f"活跃技能: {status.active_skill_count}")
print(f"网络连接: {status.network_connections}")
```

### 2. 日志配置

```python
# 配置详细日志
import logging
from openerb.core.logger import setup_logging

setup_logging(
    level="DEBUG",
    file_path="/var/log/openerb_debug.log",
    console=True
)

# 启用特定模块的调试
logging.getLogger("openerb.modules.motor_cortex").setLevel(logging.DEBUG)
logging.getLogger("openerb.modules.communication").setLevel(logging.DEBUG)
```

### 3. 性能分析

```python
# 性能分析工具
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()

    result = func(*args, **kwargs)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 前20个耗时函数

    return result

# 使用示例
# result = profile_function(await engine.execute_intent, intent, user, RobotType.G1)
```

## 常见问题解决

### 连接问题

#### 机器人无法连接
```bash
# 检查网络连接
ping 192.168.123.161  # G1
ping 192.168.12.1     # Go2

# 检查端口
telnet 192.168.123.161 8080

# 检查防火墙
sudo ufw status
sudo ufw allow 8080
```

#### SDK 初始化失败
```python
# 检查 SDK 版本兼容性
from unitree_sdk import __version__
print(f"SDK 版本: {__version__}")

# 检查机器人固件版本
cortex = InsularCortex()
cortex.identify_robot("G1-EDU", firmware_version="1.5.0")
```

### 运动控制问题

#### 关节角度异常
```python
# 检查关节限制
joint_limits = cortex.get_capability("joint_limits")
print(f"关节限制: {joint_limits}")

# 验证运动参数
if speed > cortex.get_capability("max_speed"):
    print("⚠️ 速度超过限制")
```

#### 平衡问题
```python
# 启用平衡控制
robot.enable_balance_control()
robot.set_balance_mode("dynamic")

# 检查 IMU 数据
imu_data = robot.get_imu_data()
print(f"姿态: {imu_data['orientation']}")
```

### 视觉系统问题

#### 相机无法访问
```bash
# 检查相机设备
ls /dev/video*

# 检查权限
sudo usermod -a -G video $USER

# 测试相机
gst-launch-1.0 v4l2src device=/dev/video0 ! videoconvert ! autovideosink
```

#### 检测精度低
```python
# 调整检测参数
detector = ObjectDetector()
detector.confidence_threshold = 0.7
detector.nms_threshold = 0.4

# 使用更高分辨率
visual.set_camera_resolution(1920, 1080)
```

### 通信问题

#### 节点发现失败
```python
# 检查多播配置
comm.enable_multicast_discovery()
comm.set_broadcast_address("192.168.123.255")

# 检查防火墙多播规则
sudo ufw allow from 192.168.123.0/24 to any port 9999 proto udp
```

#### 消息丢失
```python
# 启用消息确认
comm.enable_message_acknowledgment()
comm.set_retry_attempts(3)
comm.set_message_timeout(5.0)
```

## 生产环境部署

### 1. 服务化部署

```bash
# 创建系统服务
sudo tee /etc/systemd/system/openerb.service > /dev/null <<EOF
[Unit]
Description=OpenERB Robot Brain Service
After=network.target

[Service]
Type=simple
User=unitree
WorkingDirectory=/home/unitree/openerb
ExecStart=/home/unitree/openerb_env/bin/python -m openerb
Restart=always
Environment=PYTHONPATH=/home/unitree/openerb
Environment=ROBOT_TYPE=G1

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl enable openerb
sudo systemctl start openerb
sudo systemctl status openerb
```

### 2. 监控和告警

```bash
# 安装监控工具
pip install prometheus_client

# 配置指标暴露
from prometheus_client import start_http_server, Gauge

# 系统指标
cpu_gauge = Gauge('openerb_cpu_percent', 'CPU usage percentage')
memory_gauge = Gauge('openerb_memory_mb', 'Memory usage in MB')

# 启动指标服务器
start_http_server(8000)

# 在监控循环中更新指标
cpu_gauge.set(psutil.cpu_percent())
memory_gauge.set(psutil.Process().memory_info().rss / 1024 / 1024)
```

### 3. 日志聚合

```bash
# 配置日志轮转
sudo tee /etc/logrotate.d/openerb > /dev/null <<EOF
/var/log/openerb/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    create 644 unitree unitree
    postrotate
        systemctl reload openerb
    endscript
}
EOF
```

## 维护和更新

### 1. 技能库更新

```bash
# 备份当前技能库
cp data/skills.db data/skills.db.backup

# 更新技能
python -c "
from openerb.modules.cerebellum import Cerebellum
cerebellum = Cerebellum()
# 添加新技能...
"
```

### 2. 系统更新

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -e . --upgrade

# 重启服务
sudo systemctl restart openerb
```

### 3. 性能监控

```bash
# 定期性能检查
python -c "
from openerb.core.monitor import SystemMonitor
monitor = SystemMonitor()
status = monitor.get_system_status()
print(f'系统状态: CPU {status.cpu_percent}%, 内存 {status.memory_percent}%')
"
```

这个调试指南涵盖了从基础连接测试到生产环境部署的完整流程，帮助你在真实机器人上顺利部署和调试 OpenERB 系统。
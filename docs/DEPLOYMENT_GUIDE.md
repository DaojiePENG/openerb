# OpenERB 部署指南

## 概述

本指南介绍如何在不同环境中部署和运行 OpenERB 系统。

## 系统要求

### 硬件要求
- **CPU**: Intel i5 或 AMD Ryzen 5 以上
- **内存**: 8GB RAM 以上
- **存储**: 50GB 可用磁盘空间
- **网络**: 稳定的互联网连接 (用于 LLM API)

### 软件要求
- **操作系统**: Ubuntu 20.04+, macOS 12+, Windows 10+
- **Python**: 3.9 - 3.11
- **机器人**: Unitree G1, Go2, 或 Go1

## 开发环境设置

### 推荐方案: 使用 uv (比 pip 快 10-100 倍)

`uv` 是用 Rust 编写的超快 Python 包管理工具，推荐用于开发和测试。

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或 macOS: brew install uv
# 或 Ubuntu: apt install uv (需要添加 PPA)

# 2. 创建虚拟环境（极速）
cd ~/openerb
uv venv --python 3.11

# 3. 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 4. 配置 API 密钥
export DASHSCOPE_API_KEY="sk-your-key-here"

# 5. 安装依赖（极速）
uv pip install -e .

# 6. 初始化系统
python -m openerb.core.bootstrap init --robot-type G1

# 7. 验证安装
python -m pytest tests/
```

### 传统方案: 使用 pip

如果你还没有 `uv`，可以使用传统的 pip：

```bash
# 1. 创建虚拟环境
cd ~/openerb
python -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 升级 pip
pip install --upgrade pip setuptools

# 4. 配置 API 密钥
export DASHSCOPE_API_KEY="sk-your-key-here"

# 5. 安装依赖
pip install -e .

# 6. 初始化系统（G1 机器人）
python -m openerb.core.bootstrap init --robot-type G1

# 或 Go2
python -m openerb.core.bootstrap init --robot-type Go2
```

### Docker 沙盒执行环境

为了安全执行 AI 生成的代码，推荐使用 Docker 容器隔离：

```bash
# 1. 构建 Docker 镜像
docker build -t openerb:latest .

# 2. 运行容器
docker run -it \
  -e DASHSCOPE_API_KEY="sk-your-key" \
  -e ROBOT_TYPE="G1" \
  -v ~/openerb/data:/app/data \
  openerb:latest

# 3. 在容器内验证安装
python -m pytest tests/
```

### 验证安装

```bash
# 检查系统状态
python -m openerb.core.bootstrap status

# 运行测试
pytest tests/ -v
```

## 快速部署

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/DaojiePENG/openerb.git
cd openerb

# 创建虚拟环境 (推荐使用 uv)
uv venv --python 3.11
source .venv/bin/activate

# 安装依赖
uv pip install -e .
```

### 2. 配置 API 密钥

```bash
# 配置阿里 DASHSCOPE API (推荐)
export DASHSCOPE_API_KEY="sk-your-api-key-here"

# 或配置 OpenAI API
export OPENAI_API_KEY="sk-your-api-key-here"
export LLM_PROVIDER=openai
```

### 3. 初始化系统

```bash
# 初始化系统配置
python -m openerb.core.bootstrap init --robot-type G1

# 验证安装
python -m pytest tests/ -v
```

### 4. 启动系统

```bash
# 启动完整系统
python -m openerb

# 或启动特定模块进行测试
python -c "from openerb.modules.prefrontal_cortex import PrefrontalCortex; print('PrefrontalCortex ready')"
```

## 生产环境部署

### Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml .
COPY openerb/ ./openerb/
COPY tests/ ./tests/

# 安装 Python 依赖
RUN pip install -e .

# 创建数据目录
RUN mkdir -p /app/data

# 设置环境变量
ENV PYTHONPATH=/app
ENV OPENERB_STORAGE_PATH=/app/data

# 暴露端口 (如果需要)
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "openerb"]
```

构建和运行：

```bash
# 构建镜像
docker build -t openerb .

# 运行容器
docker run -e DASHSCOPE_API_KEY="sk-xxx" -v /host/data:/app/data openerb
```

### Kubernetes 部署

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openerb
spec:
  replicas: 1
  selector:
    matchLabels:
      app: openerb
  template:
    metadata:
      labels:
        app: openerb
    spec:
      containers:
      - name: openerb
        image: openerb:latest
        env:
        - name: DASHSCOPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: openerb-secrets
              key: dashscope-api-key
        - name: ROBOT_TYPE
          value: "G1"
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: openerb-data
```

### 云服务器部署

#### AWS EC2

```bash
# 安装依赖
sudo apt update
sudo apt install python3.11 python3.11-venv

# 配置安全组 (开放必要端口)
# SSH: 22, HTTP: 80, HTTPS: 443, 自定义端口: 8000

# 使用 Systemd 服务
sudo tee /etc/systemd/system/openerb.service > /dev/null <<EOF
[Unit]
Description=OpenERB Robot Brain
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/openerb
ExecStart=/home/ubuntu/openerb/.venv/bin/python -m openerb
Restart=always
Environment=DASHSCOPE_API_KEY=sk-xxx
Environment=ROBOT_TYPE=G1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable openerb
sudo systemctl start openerb
```

#### Google Cloud Run

```yaml
# cloud-run.yaml
service: openerb
runtime: python311

env_variables:
  DASHSCOPE_API_KEY: "sk-xxx"
  ROBOT_TYPE: "G1"

handlers:
- url: /.*
  script: auto
```

## 机器人连接配置

### Unitree G1 配置

```python
# 配置机器人连接
from openerb.core.config import RobotConfig

config = RobotConfig()
config.robot_type = RobotType.G1
config.robot_address = "192.168.123.161"  # G1 默认 IP
config.robot_port = 8080
config.save()
```

### Unitree Go2 配置

```python
config = RobotConfig()
config.robot_type = RobotType.Go2
config.robot_address = "192.168.12.1"    # Go2 默认 IP
config.robot_port = 8082
config.save()
```

## 监控和日志

### 日志配置

```python
# 配置日志
import logging
from openerb.core.logger import setup_logging

# 开发环境 - 详细日志
setup_logging(level="DEBUG", file_path="logs/openerb.log")

# 生产环境 - 标准日志
setup_logging(level="INFO", file_path="/var/log/openerb.log")
```

### 监控指标

系统自动收集以下指标：

- **性能指标**: 响应时间、CPU 使用率、内存使用率
- **业务指标**: 技能执行成功率、用户交互次数
- **系统指标**: 磁盘使用率、网络连接状态

```python
# 查看系统状态
from openerb.core.monitor import SystemMonitor

monitor = SystemMonitor()
status = monitor.get_system_status()
print(f"CPU: {status.cpu_percent}%")
print(f"Memory: {status.memory_percent}%")
print(f"Active skills: {status.active_skill_count}")
```

## 故障排除

### 常见问题

#### 1. LLM API 连接失败

```bash
# 检查网络连接
curl -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
     https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation

# 检查 API 密钥
python -c "import os; print('API Key set:', bool(os.getenv('DASHSCOPE_API_KEY')))"
```

#### 2. 机器人连接失败

```bash
# 检查网络连接
ping 192.168.123.161  # G1
ping 192.168.12.1     # Go2

# 检查端口
telnet 192.168.123.161 8080
```

#### 3. 内存不足

```bash
# 增加交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 日志分析

```bash
# 查看错误日志
tail -f logs/openerb.log | grep ERROR

# 分析性能瓶颈
python -c "
import cProfile
from openerb.modules.prefrontal_cortex import PrefrontalCortex
cProfile.run('cortex.process_input(\"test\")')
"
```

## 备份和恢复

### 数据备份

```bash
# 备份用户数据和技能
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# 备份到云存储
aws s3 cp backup_*.tar.gz s3://openerb-backups/
```

### 系统恢复

```bash
# 从备份恢复
tar -xzf backup_20260403.tar.gz -C /

# 重新初始化
python -m openerb.core.bootstrap init --robot-type G1 --restore-from-backup
```

## 性能优化

### 内存优化

```python
# 启用内存监控
from openerb.core.monitor import MemoryMonitor

monitor = MemoryMonitor()
monitor.start_monitoring(interval=60)  # 每分钟检查一次

# 自动清理缓存
monitor.enable_auto_cleanup(threshold_mb=500)
```

### 并发优化

```python
# 配置异步池
from openerb.core.config import AsyncConfig

config = AsyncConfig()
config.max_workers = 4
config.queue_size = 100
config.timeout = 30
config.save()
```

### 缓存优化

```python
# 启用技能缓存
from openerb.modules.cerebellum import SkillCache

cache = SkillCache(max_size=1000, ttl_hours=24)
cache.enable()
```

## 安全配置

### API 密钥管理

```bash
# 使用密钥管理服务
export DASHSCOPE_API_KEY_FROM_AWS_SECRETS=arn:aws:secretsmanager:region:account:secret:name

# 或使用环境变量文件
echo "DASHSCOPE_API_KEY=sk-xxx" > .env
export $(cat .env | xargs)
```

### 网络安全

```bash
# 配置防火墙
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 8000/tcp    # OpenERB API
sudo ufw --force enable

# 使用 HTTPS
# 配置 Nginx 反向代理 + Let's Encrypt SSL
```

### 访问控制

```python
# 配置用户认证
from openerb.core.auth import AuthManager

auth = AuthManager()
auth.enable_user_authentication()
auth.add_user("admin", "secure_password", role="admin")
```
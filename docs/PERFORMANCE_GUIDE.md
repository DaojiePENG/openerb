# OpenERB 性能优化指南

## 概述

本指南介绍 OpenERB 系统的性能优化策略和最佳实践。

## 性能基准

### 当前性能指标

基于最新测试数据 (2026.04.03):

- **响应时间**: 平均 2.3 秒 (LLM 调用 + 意图解析)
- **内存使用**: 平均 180MB (基础配置)
- **CPU 使用**: 平均 15% (单核)
- **并发处理**: 支持 10 个并发请求
- **技能执行**: 平均 0.8 秒

### 性能目标

- **响应时间**: < 2.0 秒 (95% 分位数)
- **内存使用**: < 256MB
- **CPU 使用**: < 20%
- **并发处理**: 50 个并发请求
- **可用性**: 99.9%

## 优化策略

### 1. LLM 优化

#### 模型选择
```python
# 推荐配置
LLM_MODEL=qwen-turbo  # 速度优先
# 或
LLM_MODEL=qwen-plus   # 平衡性能
# 或
LLM_MODEL=qwen-max    # 质量优先
```

#### 缓存策略
```python
from openerb.core.cache import LLMCache

# 启用意图缓存
cache = LLMCache(max_size=1000, ttl_minutes=30)
cache.enable_intent_caching()

# 启用响应缓存
cache.enable_response_caching(similarity_threshold=0.85)
```

#### 并发控制
```python
# 配置并发限制
from openerb.llm.config import LLMConfig

config = LLMConfig()
config.max_concurrent_requests = 5
config.request_timeout = 10
config.retry_attempts = 2
```

### 2. 内存优化

#### 对象池管理
```python
from openerb.core.pool import ObjectPool

# 技能对象池
skill_pool = ObjectPool(Skill, max_size=100)
skill_pool.enable()

# 图像处理池
image_pool = ObjectPool(ImageProcessor, max_size=10)
image_pool.enable()
```

#### 垃圾回收优化
```python
import gc
from openerb.core.gc import GCOptimizer

# 启用智能 GC
gc_optimizer = GCOptimizer()
gc_optimizer.enable_adaptive_gc()

# 手动触发 GC (在低负载时段)
gc_optimizer.schedule_gc(hour=2)  # 凌晨 2 点
```

#### 内存监控
```python
from openerb.core.monitor import MemoryMonitor

monitor = MemoryMonitor()
monitor.start_monitoring(interval=60)

# 设置内存阈值告警
monitor.set_thresholds(
    warning_mb=300,
    critical_mb=500,
    action=lambda: gc_optimizer.force_gc()
)
```

### 3. 并发优化

#### 异步架构
```python
import asyncio
from openerb.core.asyncio import AsyncManager

# 配置异步池
async_manager = AsyncManager()
async_manager.configure_pool(
    max_workers=8,
    thread_pool_size=4,
    process_pool_size=2
)

# 使用异步上下文管理器
async with async_manager:
    results = await asyncio.gather(*tasks)
```

#### 任务队列
```python
from openerb.core.queue import TaskQueue

# 配置任务队列
queue = TaskQueue(max_size=1000, workers=4)
queue.enable_priority_queue()

# 提交任务
await queue.submit_task(
    func=process_intent,
    args=(intent,),
    priority=TaskPriority.HIGH
)
```

### 4. 存储优化

#### 数据库优化
```python
from openerb.core.storage import StorageOptimizer

optimizer = StorageOptimizer()

# 启用连接池
optimizer.enable_connection_pool(max_connections=10)

# 配置索引
optimizer.create_indexes([
    "skills.name",
    "skills.skill_type",
    "users.user_id",
    "events.timestamp"
])

# 启用查询缓存
optimizer.enable_query_cache(ttl_seconds=300)
```

#### 缓存策略
```python
from openerb.core.cache import MultiLevelCache

# 多级缓存配置
cache = MultiLevelCache(
    l1_size=100,    # 内存缓存
    l2_size=1000,   # Redis 缓存
    l3_size=10000   # 磁盘缓存
)

# 技能缓存
cache.enable_skill_caching()

# 用户会话缓存
cache.enable_session_caching(ttl_hours=24)
```

### 5. 网络优化

#### 连接池
```python
from openerb.core.network import ConnectionPool

# HTTP 连接池
http_pool = ConnectionPool(
    max_connections=20,
    max_keepalive=10,
    timeout=30
)

# WebSocket 连接池 (用于机器人通信)
ws_pool = ConnectionPool(
    max_connections=50,
    heartbeat_interval=30
)
```

#### 压缩优化
```python
from openerb.core.compression import CompressionManager

compressor = CompressionManager()

# 启用响应压缩
compressor.enable_response_compression(
    algorithm="gzip",
    min_size_kb=1
)

# 启用图像压缩
compressor.enable_image_compression(
    quality=85,
    max_width=1920
)
```

## 监控和分析

### 性能监控
```python
from openerb.core.monitor import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.start_collecting()

# 实时指标
metrics = monitor.get_metrics()
print(f"Response time: {metrics.avg_response_time:.2f}s")
print(f"Throughput: {metrics.requests_per_second:.1f} req/s")
print(f"Error rate: {metrics.error_rate:.2%}")
```

### 分析工具
```python
from openerb.core.profiler import SystemProfiler

profiler = SystemProfiler()

# CPU 分析
profiler.profile_cpu(duration_seconds=60)

# 内存分析
profiler.profile_memory()

# I/O 分析
profiler.profile_io()
```

### 可视化仪表板
```python
from openerb.core.dashboard import MetricsDashboard

dashboard = MetricsDashboard()
dashboard.start_server(port=8080)

# 访问 http://localhost:8080 查看实时指标
```

## 扩展策略

### 水平扩展
```python
# 多实例部署
instances = [
    {"host": "node1", "port": 8000},
    {"host": "node2", "port": 8000},
    {"host": "node3", "port": 8000}
]

# 负载均衡器配置
from openerb.core.loadbalancer import LoadBalancer
lb = LoadBalancer(instances)
lb.enable_health_checks()
```

### 垂直扩展
```python
# 资源分配优化
from openerb.core.resources import ResourceManager

manager = ResourceManager()
manager.allocate_resources({
    "cpu_cores": 4,
    "memory_gb": 8,
    "gpu_memory_gb": 2
})
```

## 故障排查

### 性能问题诊断
```python
from openerb.core.diagnostics import PerformanceDiagnostics

diagnostics = PerformanceDiagnostics()

# 运行完整诊断
report = diagnostics.run_full_diagnosis()

# 生成优化建议
recommendations = diagnostics.generate_recommendations(report)
for rec in recommendations:
    print(f"- {rec}")
```

### 常见性能问题

#### 1. 高延迟
```python
# 检查 LLM 响应时间
llm_metrics = monitor.get_llm_metrics()
if llm_metrics.avg_response_time > 5.0:
    # 切换到更快的模型
    config.switch_to_faster_model()

# 检查网络延迟
network_metrics = monitor.get_network_metrics()
if network_metrics.avg_latency > 1.0:
    # 启用本地缓存
    cache.enable_offline_mode()
```

#### 2. 内存泄漏
```python
# 检测内存泄漏
leak_detector = MemoryLeakDetector()
leaks = leak_detector.scan_for_leaks()

if leaks:
    for leak in leaks:
        print(f"Memory leak: {leak.object_type} - {leak.size_mb}MB")
        leak_detector.fix_leak(leak)
```

#### 3. CPU 瓶颈
```python
# CPU 使用率分析
cpu_analyzer = CPUAnalyzer()
bottlenecks = cpu_analyzer.find_bottlenecks()

for bottleneck in bottlenecks:
    if bottleneck.function == "llm_call":
        # 启用并发调用
        config.enable_concurrent_llm_calls()
    elif bottleneck.function == "image_processing":
        # 使用 GPU 加速
        config.enable_gpu_acceleration()
```

## 基准测试

### 运行性能测试
```bash
# 运行基准测试套件
python -m pytest tests/performance/ -v

# 压力测试
python -m pytest tests/stress/ --stress-level=high

# 负载测试
python -m pytest tests/load/ --duration=3600 --concurrency=50
```

### 自定义基准测试
```python
from openerb.tests.performance import BenchmarkSuite

suite = BenchmarkSuite()

# 意图处理基准测试
@suite.benchmark
async def test_intent_processing():
    cortex = PrefrontalCortex(llm_client=client)
    for intent in test_intents:
        await cortex.process_input(intent)

# 技能执行基准测试
@suite.benchmark
async def test_skill_execution():
    motor = MotorCortex()
    for skill in test_skills:
        await motor.execute_skill(skill)

# 运行测试
results = suite.run()
suite.generate_report(results, "performance_report.html")
```

## 最佳实践

1. **监控优先**: 始终启用性能监控，及早发现问题
2. **渐进优化**: 先解决最大瓶颈，再处理次要问题
3. **测试驱动**: 所有优化都应通过性能测试验证
4. **资源意识**: 根据实际负载调整资源分配
5. **自动化**: 使用自动化工具进行持续性能监控

## 性能目标跟踪

| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| 响应时间 | 2.3s | <2.0s | 🔄 优化中 |
| 内存使用 | 180MB | <256MB | ✅ 已达标 |
| CPU 使用 | 15% | <20% | ✅ 已达标 |
| 并发处理 | 10 | 50 | 🔄 优化中 |
| 可用性 | 99.5% | 99.9% | 🔄 优化中 |
# 自主进化机器人系统架构设计文档

## 项目概述

本项目实现一个自主学习和进化的机器人控制系统，机器人能够基于人类指令自动生成控制代码、记忆技能、进行安全检验，并在不同机器人平台间迁移知识。该系统采用类脑结构设计，融合神经科学概念与工程实现。

## 系统整体架构

```
┌─────────────────────────────────────────────────────────┐
│              对话入口 (前额叶皮层代理)                    │
│        Multi-Modal LLM Agent (Qwen-VL-Plus)              │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌────────────────────┐   ┌────────────────────┐
│  意图理解            │   │  任务规划          │
│  & 任务分解          │   │  & 逻辑判断        │
└─────────┬──────────┘   └────────┬───────────┘
          │                       │
          └───────────┬───────────┘
                      ▼
        ┌─────────────────────────────────┐
        │   边缘系统 (安全约束引擎)        │
        │  - 安全校验                      │
        │  - 危险检测                      │
        │  - 二次确认机制                  │
        └─────────────┬───────────────────┘
                      ▼
        ┌─────────────────────────────────┐
        │  岛叶皮层 (机体自我认知)         │
        │  - 机器人型号识别 (G1/Go2)      │
        │  - 能力集合管理                  │
        │  - 平台特性映射                  │
        └─────────────┬───────────────────┘
                      ▼
        ┌─────────────────────────────────┐
        │  小脑 (技能记忆库)               │
        │  - 技能检索与匹配                │
        │  - 版本管理                      │
        │  - 垃圾箱管理                    │
        └─────────────┬───────────────────┘
                      ▼
        ┌─────────────────────────────────┐
        │  海马体 (长期记忆管理)           │
        │  - 技能固化                      │
        │  - 知识持久化                    │
        │  - 学习曲线管理                  │
        └─────────────┬───────────────────┘
                      ▼
        ┌─────────────────────────────────┐
        │  运动皮层 (代码生成引擎)         │
        │  - 代码模板库                    │
        │  - SDK调用生成                   │
        │  - 动态编译与执行                │
        └─────────────┬───────────────────┘
                      ▼
        ┌─────────────────────────────────┐
        │  视觉模块 (顶叶&枕叶)            │
        │  - 多模态感知                    │
        │  - 人脸识别                      │
        │  - 用户档案管理                  │
        └─────────────────────────────────┘
```

## 核心模块详细说明

### 1. 前额叶皮层 (Prefrontal Cortex) - 对话Agent
**位置**: `modules/prefrontal_cortex/`

**职责**:
- 多模态对话管理 (文本+图像输入)
- 意图理解与任务分解
- 上下文管理
- 用户交互

**主要接口**:
```python
class PrefrontalCortex:
    async def process_input(text: str, image: Optional[Image]) -> IntentResult
    async def decompose_task(intent: Intent) -> List[Subtask]
    def maintain_context(conversation_history: List[Turn])
```

**依赖**: Qwen-VL-Plus API

---

### 2. 岛叶皮层 (Insular Cortex) - 机体自我认知
**位置**: `modules/insular_cortex/`

**职责**:
- 机器人型号识别 (当前是G1还是Go2)
- 机器人身体特征管理
- 能力集集映射
- 通用技能vs本体技能区分

**主要接口**:
```python
class InsularCortex:
    def identify_robot_body() -> RobotType  # G1, Go2, etc.
    def get_robot_capabilities() -> RobotCapabilities
    def classify_skill(skill: Skill) -> SkillType  # UNIVERSAL or BODY_SPECIFIC
    def adapt_skill_to_body(skill: Skill, target_body: RobotType) -> AdaptedSkill
```

**数据结构**:
```python
class RobotProfile:
    robot_type: str  # "G1", "Go2"
    body_id: str  # 唯一识别符
    capabilities: Dict[str, Any]
    skills_learned: List[Skill]
    created_at: datetime
```

---

### 3. 边缘系统 (Limbic System & Amygdala) - 安全约束
**位置**: `modules/limbic_system/`

**职责**:
- 安全性校验
- 危险检测与规避
- 障碍物识别
- 二次确认机制

**主要接口**:
```python
class LimbicSystem:
    def validate_action(action: Action, context: RobotContext) -> (bool, str)
    def detect_danger(instruction: Instruction, sensor_data: SensorData) -> DangerLevel
    def request_confirmation(instruction: Instruction, danger: DangerLevel) -> bool
    def suggest_safe_alternative(instruction: Instruction) -> Instruction
```

**安全级别**:
- GREEN: 安全执行
- YELLOW: 需要二次确认
- RED: 拒绝执行，给出建议

---

### 4. 小脑 (Cerebellum) - 技能记忆库
**位置**: `modules/cerebellum/`

**职责**:
- 技能存储与版本管理
- 快速检索与匹配
- 技能废弃管理
- 技能重排序

**主要接口**:
```python
class Cerebellum:
    def search_skill(query: str, robot_body: Optional[RobotType]) -> List[Skill]
    def register_skill(skill: Skill, robot_body: RobotType, tags: List[str])
    def retire_skill(skill_id: str, reason: str)  # 移至垃圾箱
    def export_skill(skill_id: str) -> SkillPackage  # 用于分享
    def import_skill(package: SkillPackage) -> Skill  # 接收分享
```

**技能数据结构**:
```python
class Skill:
    id: str  # UUID
    name: str
    description: str
    code: str  # Python代码
    dependencies: List[str]  # 依赖的其他技能或库
    tags: List[str]
    robot_bodies: List[str]  # 支持的机器人类型
    created_at: datetime
    last_used: datetime
    success_rate: float
    version: int
    status: SkillStatus  # ACTIVE, DEPRECATED, RETIRED
```

---

### 5. 海马体 (Hippocampus) - 长期记忆
**位置**: `modules/hippocampus/`

**职责**:
- 技能长期记忆管理
- 学习进度追踪
- 知识固化与持久化
- 增量学习支持

**主要接口**:
```python
class Hippocampus:
    def consolidate_skill(skill: Skill, performance_metrics: Dict)
    def recall_learning_history(skill_id: str) -> LearningHistory
    def update_competency(skill_id: str, new_metric: float)
    def save_to_disk(path: str)
    def load_from_disk(path: str)
```

---

### 6. 运动皮层 (Motor Cortex) - 代码生成
**位置**: `modules/motor_cortex/`

**职责**:
- 基于意图生成Python代码
- SDK调用编排
- 动态编译与执行
- 代码安全沙箱

**主要接口**:
```python
class MotorCortex:
    async def generate_code(intent: Intent, context: RobotContext) -> str
    async def validate_code(code: str) -> (bool, str)
    async def execute_code(code: str, timeout: float) -> ExecutionResult
    def generate_from_template(template: str, vars: Dict) -> str
```

**代码生成流程**:
1. 接收意图
2. 查询技能库 (小脑)
3. 若有现成技能，使用现成技能
4. 若无，调用LLM生成新代码
5. 代码审查与安全检测
6. 动态执行

---

## 🔐 安全与沙盒机制 (Safety & Sandboxing)

### 设计理念

OpenERB 的核心创新是让 AI 自动生成代码控制机器人，但这引入了严重的安全隐患：
- **代码执行危险**: AI 生成的恶意或错误代码可能损坏机器人硬件（如烧毁电机）
- **资源枚举**: 无限循环或内存泄漏可能导致系统崩溃
- **权限提升**: 生成的代码不应访问 OS 层面的关键操作

因此，**OpenERB 的所有代码执行都在严格的沙盒环境中进行**。

### 三层沙盒架构

#### 第1层: 代码静态分析 (RestrictedPython)

**用途**: 轻量级、快速的代码检查
**执行环境**: Motor Cortex 模块
**机制**:
- 使用 RestrictedPython 库进行 AST 分析
- 禁止导入危险模块 (`os`, `sys`, `subprocess`, `socket`, etc.)
- 禁止调用危险 builtin (`exec`, `eval`, `__import__`, `open`)
- 提前拒绝明显的恶意代码

**配置示例**:
```python
from openerb.core.types import CodeExecutionPolicy, SandboxType

# 默认执行策略（对大多数技能生成足够）
default_policy = CodeExecutionPolicy(
    sandbox_type=SandboxType.RESTRICTED_PYTHON,
    timeout=60.0,  # 60秒超时
    max_memory=512,  # 512MB 内存限制
    allowed_imports=["math", "random", "time", "collections"],
    forbidden_modules=["os", "sys", "subprocess", "socket", "threading"],
    forbidden_builtins=["exec", "eval", "__import__", "open"],
    enable_network=False,
    enable_file_access=False,
    enable_subprocess=False
)
```

#### 第2层: 进程隔离 (Process Sandbox)

**用途**: 中等风险代码，需要进程级隔离
**执行环境**: 子进程
**机制**:
- 在独立的子进程中执行代码
- 设置资源限制（CPU、内存）
- 超时自动杀死进程
- 使用管道捕获输出，防止副作用

**适用场景**:
- 需要文件访问但隔离在临时目录
- 需要执行系统命令（通过 SDK 对象）
- 较复杂的算法，需要更多计算资源

#### 第3层: 容器隔离 (Docker Sandbox)

**用途**: 高风险代码，需要完全隔离
**执行环境**: Docker 容器
**机制**:
- 完全虚拟化的文件系统和网络
- 网络隔离（可选启用 VPN）
- 严格的 CPU 和内存限制
- 容器内无 root 权限

**适用场景**:
- 用户 UGC（用户生成内容）
- 来自不信任来源的代码
- 生产环境公开 API

**Docker 配置示例**:
```dockerfile
FROM python:3.11-slim

# 非 root 用户
RUN useradd -m sandbox

# 最小化依赖
RUN apt-get update && apt-get install -y \
    unitree-sdk \
    && rm -rf /var/lib/apt/lists/*

# 限制权限
RUN chmod -R 755 /app

USER sandbox
WORKDIR /app

# 资源限制在运行时设置
# docker run -m 512M --cpus=1 openerb:latest
```

### 沙盒选择流程

```
┌─────────────────────────────────┐
│  Motor Cortex 生成代码            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ RestrictedPython 静态分析        │
│ ✗ 发现危险 → 拒绝执行             │
└────┬─────────────────────┬──────┘
     │ ✓ 通过               │
     ▼                    ▼
┌──────────────┐   ┌────────────┐
│ 检查风险等级   │   │ 获取用户偏好 │
│ (Danger      │   │ 沙盒策略    │
│  Level)      │   └────┬──────┘
└──────┬───────┘        │
       │                │
       ▼                ▼
  ┌─────────────────────────────┐
  │  选择沙盒类型:              │
  │  - RESTRICTED_PYTHON        │
  │  - PROCESS (子进程)         │
  │  - DOCKER (容器)            │
  │  - DISABLED (仅开发环境)    │
  └──────┬────────────────────┘
         │
         ▼
  ┌─────────────────────────────┐
  │  执行代码 + 监控             │
  │  - 超时检查                  │
  │  - 内存监控                  │
  │  - 异常捕获                  │
  │  - 资源清理                  │
  └──────┬────────────────────┘
         │
         ▼
  ┌─────────────────────────────┐
  │  记录执行结果与指标           │
  │  (用于学习与改进)             │
  └──────────────────────────────┘
```

### 类型定义

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List

class SandboxType(str, Enum):
    """沙盒执行类型"""
    RESTRICTED_PYTHON = "restricted_python"  # AST 分析 - 最快
    PROCESS = "process"                      # 进程隔离 - 中等
    DOCKER = "docker"                        # 容器隔离 - 最安全
    DISABLED = "disabled"                    # 无沙盒 - 仅开发环境

@dataclass
class CodeExecutionPolicy:
    """代码执行策略"""
    sandbox_type: SandboxType = SandboxType.RESTRICTED_PYTHON
    timeout: float = 60.0  # 秒
    max_memory: Optional[int] = None  # MB
    
    # 导入白名单
    allowed_imports: List[str] = field(default_factory=lambda: [
        "math", "random", "time", "collections", "itertools"
    ])
    
    # 模块黑名单
    forbidden_modules: List[str] = field(default_factory=lambda: [
        "os", "sys", "subprocess", "socket", "threading", 
        "multiprocessing", "importlib", "pickle"
    ])
    
    # 内置函数黑名单
    forbidden_builtins: List[str] = field(default_factory=lambda: [
        "exec", "eval", "compile", "__import__", "open", 
        "input", "globals", "locals", "vars"
    ])
    
    # 权限控制
    enable_network: bool = False        # 禁用网络
    enable_file_access: bool = False    # 禁用文件访问
    enable_subprocess: bool = False     # 禁用系统命令
```

### 实施指南

#### 步骤 1: 代码生成时应用策略

```python
# 在 Motor Cortex 中
from openerb.core.types import CodeExecutionPolicy, SandboxType

class MotorCortex:
    def __init__(self):
        self.policy = CodeExecutionPolicy(
            sandbox_type=SandboxType.RESTRICTED_PYTHON,  # 默认
            timeout=60.0
        )
    
    async def execute_code(self, code: str, risk_level: str):
        # 根据风险等级动态调整沙盒
        if risk_level == "HIGH":
            self.policy.sandbox_type = SandboxType.DOCKER
        elif risk_level == "MEDIUM":
            self.policy.sandbox_type = SandboxType.PROCESS
        
        # 执行代码（会调用对应的沙盒执行器）
        result = await self._execute_in_sandbox(code, self.policy)
        return result
```

#### 步骤 2: 创建沙盒执行器

```python
# core/execution.py - 待实现
class SandboxExecutor:
    """沙盒执行器基类"""
    
    @abstractmethod
    def execute(self, code: str, policy: CodeExecutionPolicy) -> ExecutionResult:
        pass

class RestrictedPythonExecutor(SandboxExecutor):
    """使用 RestrictedPython AST 分析"""
    
    def execute(self, code: str, policy: CodeExecutionPolicy) -> ExecutionResult:
        # 1. 解析代码为 AST
        # 2. 检查禁用的模块和函数
        # 3. 若无违规，编译并执行
        # 4. 返回结果
        pass

class ProcessSandboxExecutor(SandboxExecutor):
    """使用进程隔离"""
    
    def execute(self, code: str, policy: CodeExecutionPolicy) -> ExecutionResult:
        # 1. 创建子进程
        # 2. 设置资源限制
        # 3. 执行代码
        # 4. 超时处理
        # 5. 返回结果
        pass

class DockerSandboxExecutor(SandboxExecutor):
    """使用 Docker 容器隔离"""
    
    def execute(self, code: str, policy: CodeExecutionPolicy) -> ExecutionResult:
        # 1. 构建 Docker 命令
        # 2. 设置环境变量和卷挂载
        # 3. 执行容器
        # 4. 收集输出
        # 5. 清理容器
        # 6. 返回结果
        pass
```

### 论文中的安全讨论

当投稿到 IEEE TRO 或 Science Robotics 时，应在论文中强调：

1. **创新点**: 
   - "我们首次提出了多层沙盒执行架构，确保 AI 生成代码的安全性"
   - "三层防御 (AST分析、进程隔离、容器隔离) 消除了直接 exec() 的风险"

2. **安全性证明**:
   - 对禁用 builtin 和模块的完整性进行形式化验证
   - 演示恶意代码检测的失败 case 分析
   - 资源限制的有效性测试

3. **性能权衡**:
   - RestrictedPython: ~1ms 开销 (推荐用于大多数技能)
   - Process: ~50ms 开销 (中等风险代码)
   - Docker: ~500ms 开销 (仅限高风险)

4. **用户研究**:
   - 用户对沙盒执行的可接受性调查
   - 在真实机器人上的安全事件记录 (0 硬件损坏)

---

### 7. 视觉模块 (Parietal & Occipital Lobes)
**位置**: `modules/vision/`

**职责**:
- 多模态图像处理
- 人脸识别
- 用户档案建立与识别
- 环境理解

**主要接口**:
```python
class VisionModule:
    async def recognize_face(image: Image) -> (bool, UserProfile)
    async def extract_scene_understanding(image: Image) -> SceneInfo
    async def update_user_profile(user_id: str, features: Dict)
    def get_user_by_face(image: Image) -> Optional[UserProfile]
```

---

### 8. 通信与协作模块
**位置**: `modules/communication/`

**职责**:
- 机器人间通信协议
- 技能分享机制
- 分布式学习

**主要接口**:
```python
class CommunicationModule:
    async def send_skill_to_peer(robot_id: str, skill: Skill)
    async def receive_skill_from_peer(robot_id: str, skill_package: SkillPackage)
    async def query_peer_capability(robot_id: str, capability: str) -> bool
    async def broadcast_learned_skill(skill: Skill)
```

---

## 数据流与工作流

### 标准对话流程

```
用户输入 (文本+可选图像)
    ↓
前额叶皮层: 意图理解与分解
    ↓
岛叶皮层: 当前机体识别
    ↓
小脑: 技能检索
    ├─ 找到匹配技能 → 使用现成技能
    └─ 未找到 → 继续
        ↓
    运动皮层: 代码生成
        ↓
    边缘系统: 安全检测
        ├─ 危险 → 二次确认 / 建议 / 拒绝
        └─ 安全 → 继续
            ↓
    执行代码
        ↓
    成功? 
        ├─ 是 → 海马体: 固化技能
        └─ 否 → 运动皮层: 调整代码
            ↓
    重试或放弃
```

---

## 持久化存储结构

```
openerb/
├── data/
│   ├── body_profiles/
│   │   ├── G1_<body_id>.json          # G1机器人档案
│   │   └── Go2_<body_id>.json         # Go2机器人档案
│   ├── skills/
│   │   ├── active/                    # 激活的技能
│   │   ├── deprecated/                # 弃用的技能
│   │   └── retired/                   # 垃圾箱
│   ├── users/
│   │   └── <user_id>.json             # 用户档案 (含人脸特征)
│   └── memories/
│       ├── learning_history/          # 学习历史
│       └── knowledge_base.json         # 知识库
├── generated_code/
│   └── <timestamp>_<task>.py          # 生成的代码
└── logs/
    └── execution.log                  # 执行日志
```

---

## 开发计划

### Phase 1: 基础架构 (第1-2周)
- [ ] 核心类型定义与接口
- [ ] 数据持久化层
- [ ] 配置管理
- [ ] 单元测试框架

### Phase 2: 核心模块 (第3-6周)
- [ ] 前额叶皮层 (对话Agent)
- [ ] 岛叶皮层 (机体识别)
- [ ] 小脑 (技能库)
- [ ] 边缘系统 (安全)

### Phase 3: 智能生成 (第7-9周)
- [ ] 运动皮层 (代码生成)
- [ ] 海马体 (记忆系统)
- [ ] 集成测试

### Phase 4: 高级特性 (第10-12周)
- [ ] 视觉模块
- [ ] 通信与协作
- [ ] 性能优化
- [ ] 文档与开源准备

---

## 技术栈

| 组件 | 技术选择 |
|------|---------|
| LLM API | 阿里 DASHSCOPE (Qwen-VL-Plus) |
| 机器人SDK | Unitree SDK2 Python |
| 代码生成 | Python AST + 动态执行 |
| 存储 | SQLite + JSON |
| 进程通信 | RPC / gRPC (可选) |
| 日志 | Python logging |
| 测试 | pytest |

---

## 安全考量

1. **代码沙箱**: 使用 `RestrictedPython` 或 `ast` 黑名单
2. **权限管理**: 限制文件操作、网络访问
3. **超时控制**: 所有代码执行有超时机制
4. **审计日志**: 所有操作记录
5. **环境隔离**: 在虚拟环境中执行生成的代码

---

## 参考资源

- [Unitree SDK2 Python](https://github.com/unitreerobotics/unitree_sdk2_python)
- [Qwen VL Model](https://huggingface.co/Qwen/Qwen-VL-Plus)
- [Human Brain Neuroscience](https://en.wikipedia.org/wiki/Neuroanatomy)


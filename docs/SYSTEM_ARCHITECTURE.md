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


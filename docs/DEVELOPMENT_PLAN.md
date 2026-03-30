# 开发计划与工作流

## 项目目标

实现一个自主学习和进化的机器人控制系统，能够在宇树 G1-EDU/Go2 上运行，实现以下功能：

1. ✅ 基于大模型的自然语言交互
2. ✅ 自动代码生成与执行
3. ✅ 安全性约束与检验
4. ✅ 技能持久化与记忆
5. ✅ 机器人身体识别与适应
6. ✅ 机器人间的知识共享

## 开发阶段划分

### Phase 1: 基础架构 (已完成 ~40%)

**本周期目标**: 建立项目框架、数据模型和持久化层

**已完成的工作**:
- ✅ 项目目录结构设计
- ✅ 系统架构文档 (SYSTEM_ARCHITECTURE.md)
- ✅ 类型定义系统 (types.py) - 所有核心数据结构
- ✅ 配置管理系统 (config.py)
- ✅ 日志系统 (logger.py) - 使用 loguru
- ✅ 数据存储层 (storage.py) - SQLite + JSON 混合方案
- ✅ 引导初始化 (bootstrap.py)
- ✅ 依赖管理 (requirements.txt, README.md)

**待完成的工作**:
- [ ] 集成测试框架 (pytest)
- [ ] 环境变量配置验证
- [ ] 单元测试编写

---

### Phase 2: 核心智能模块 (待开始)

#### 2.1 前额叶皮层 (Prefrontal Cortex) - 对话Agent
**预期时间**: 2-3周
**关键任务**:
- [ ] 集成 Qwen-VL-Plus API 客户端
- [ ] 多模态输入处理 (文本+图像)
- [ ] 意图识别与分类
- [ ] 任务规划与分解
- [ ] 上下文管理器

**关键接口**:
```python
class PrefrontalCortex:
    async def process_input(text: str, image: Optional[Image]) -> IntentResult
    async def decompose_task(intent: Intent) -> List[Subtask]
    def maintain_context(conversation_history)
```

**单元测试**:
- 测试意图识别准确性
- 测试任务分解逻辑
- 测试多模态输入处理

---

#### 2.2 岛叶皮层 (Insular Cortex) - 机体自我认知
**预期时间**: 1-2周
**关键任务**:
- [ ] 机器人型号识别 (G1/Go2/其他)
- [ ] 机器人特性数据库维护
- [ ] 能力集合映射
- [ ] 技能分类 (通用 vs 本体特定)

**关键接口**:
```python
class InsularCortex:
    def identify_robot_body() -> RobotType
    def get_robot_capabilities() -> RobotCapabilities
    def classify_skill(skill: Skill) -> SkillType
```

**单元测试**:
- 测试多种机器人的识别
- 测试能力映射的准确性

---

#### 2.3 边缘系统 (Limbic System) - 安全约束
**预期时间**: 2周
**关键任务**:
- [ ] 动作安全评估
- [ ] 障碍物检测与规避
- [ ] 危险等级判定 (GREEN/YELLOW/RED)
- [ ] 二次确认机制

**关键接口**:
```python
class LimbicSystem:
    def validate_action(action: Action, context: RobotContext) -> (bool, str)
    def detect_danger(instruction: Instruction, sensor_data: SensorData) -> DangerLevel
    def request_confirmation(instruction: Instruction) -> bool
```

**单元测试**:
- 测试危险检测的准确性
- 测试安全等级判定

---

#### 2.4 小脑 (Cerebellum) - 技能库与记忆
**预期时间**: 2-3周
**关键任务**:
- [ ] 技能存储与检索
- [ ] 技能版本管理
- [ ] 技能评分系统 (成功率等)
- [ ] 技能废弃与垃圾箱管理
- [ ] 技能导入导出 (用于分享)

**关键接口**:
```python
class Cerebellum:
    def search_skill(query: str, robot_body: Optional[RobotType]) -> List[Skill]
    def register_skill(skill: Skill, robot_body: RobotType)
    def retire_skill(skill_id: str, reason: str)
```

**单元测试**:
- 测试技能检索的相关性
- 测试技能版本管理

---

### Phase 3: 智能代码生成与执行 (待开始)

#### 3.1 运动皮层 (Motor Cortex) - 代码生成
**预期时间**: 3-4周
**关键任务**:
- [ ] 意图到代码的转换引擎
- [ ] 代码模板库建立
- [ ] Unitree SDK 集成与调用生成
- [ ] 代码安全审查 (AST 分析)
- [ ] 动态编译与执行

**核心流程**:
```
Intent → 查询技能库 
       → 有则使用现有技能
       → 无则调用 LLM 生成代码
       → 代码审查 & 安全检测
       → 执行
       → 记录结果
```

**关键接口**:
```python
class MotorCortex:
    async def generate_code(intent: Intent, context: RobotContext) -> str
    async def validate_code(code: str) -> (bool, str)
    async def execute_code(code: str, timeout: float) -> ExecutionResult
```

**单元测试**:
- 测试代码生成的可执行性
- 测试安全检测的有效性
- 集成测试：模拟机器人指令执行

---

#### 3.2 海马体 (Hippocampus) - 长期记忆
**预期时间**: 2周
**关键任务**:
- [ ] 技能固化与持久化
- [ ] 学习历史追踪
- [ ] 性能指标管理
- [ ] 增量学习支持

**关键接口**:
```python
class Hippocampus:
    def consolidate_skill(skill: Skill, metrics: Dict)
    def recall_learning_history(skill_id: str) -> LearningHistory
    def update_competency(skill_id: str, metric: float)
```

---

### Phase 4: 高级特性 (待开始)

#### 4.1 视觉模块 (Parietal & Occipital Lobes)
**预期时间**: 2周
**关键任务**:
- [ ] 多模态图像理解
- [ ] 人脸识别与用户档案
- [ ] 场景理解

---

#### 4.2 通信与协作 (Communication Module)
**预期时间**: 1-2周
**关键任务**:
- [ ] 机器人间通信协议
- [ ] 技能分享机制
- [ ] 分布式学习

---

### Phase 5: 集成测试与优化
**预期时间**: 2-3周
**关键任务**:
- [ ] 完整系统集成测试
- [ ] 性能优化
- [ ] 文档完善
- [ ] 开源准备

---

## 当前里程碑

✅ **Milestone 1: 项目基础架构** (已完成)
- 完整的类型系统
- 数据持久化
- 配置管理
- 日志系统

🔄 **Milestone 2: 进行中** - 需要完成阶段1的剩余部分，然后开始阶段2

下一步: 编写集成测试 → 开始前额叶皮层模块

---

## 技术决策记录

### 1. 存储方案
**决策**: SQLite + JSON 混合
- 快速查询: 使用 SQLite
- 灵活性: 关键数据存储为 JSON 文件
- 好处: 易于版本控制、便于调试

### 2. LLM 集成
**决策**: 使用阿里 DASHSCOPE API (Qwen-VL-Plus)
- 原因: 支持中文、多模态输入
- 备选: 支持 OpenAI API 作为 fallback

### 3. 代码生成
**决策**: 使用 RestrictedPython + AST 分析
- 安全性: 可以检测危险操作
- 灵活性: 支持动态代码执行
- 隔离性: 在虚拟环境中运行

### 4. 类型系统
**决策**: 使用 dataclass + Enum
- 简洁性: 易于理解和维护
- 类型安全: IDE 支持优秀
- 序列化: 易于 JSON/数据库存储

---

## 开发指南

### 代码规范
- 使用 Python 3.9+ 类型提示
- 所有函数必须有 docstring
- 使用 loguru 进行日志记录
- 异步函数使用 async/await

### 测试规范
- 使用 pytest 框架
- 每个模块至少 80% 代码覆盖率
- 包含单元测试、集成测试和系统测试

### 提交规范
- 每个功能完成后进行提交
- 提交信息格式: `[MODULE] Description`
- 例: `[prefrontal_cortex] Add intent parsing`

---

## 环境设置

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化系统
python -m openerb.core.bootstrap init --robot-type G1

# 4. 运行测试
pytest tests/

# 5. 启动对话 Agent (后续实现)
python -m openerb.run
```

---

## 预期论文贡献

1. **系统架构**：类脑机器人控制系统的设计与实现
2. **知识迁移**：跨机器人平台的技能迁移方法
3. **自主学习**：基于大模型的动态代码生成和学习
4. **安全机制**：机器人自主决策的安全约束框架

---

## 相关资源

- [Unitree SDK2 Python](https://github.com/unitreerobotics/unitree_sdk2_python)
- [Qwen 视觉语言模型](https://huggingface.co/Qwen/Qwen-VL-Plus)
- [脑神经解剖学参考](https://en.wikipedia.org/wiki/Neuroanatomy)
- [IEEE TRO 投稿指南](https://www.ieee-ras.org/publications/t-ro)


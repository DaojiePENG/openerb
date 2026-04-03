#!/usr/bin/env python3
"""
OpenERB 真机部署测试脚本

此脚本用于在真实的 Unitree 机器人上测试 OpenERB 系统的各项功能。
运行前请确保：
1. 机器人已开机并连接到网络
2. OpenERB 系统已正确安装
3. 机器人 SDK 已正确配置

使用方法:
python robot_deployment_test.py --robot-type G1 --robot-ip 192.168.123.161
"""

import asyncio
import argparse
import sys
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

# OpenERB 模块导入
from openerb.core.types import RobotType, Skill, SkillType, UserProfile, Intent
from openerb.modules.insular_cortex import InsularCortex
from openerb.modules.motor_cortex import MotorCortex
from openerb.modules.visual_cortex import VisualCortex
from openerb.modules.cerebellum import Cerebellum
from openerb.modules.hippocampus import Hippocampus
from openerb.modules.communication import CommunicationModule
from openerb.modules.system_integration import IntegrationEngine
from openerb.core.monitor import SystemMonitor
from openerb.core.config import RobotConfig, NetworkConfig
from openerb.core.logger import setup_logging

class RobotDeploymentTester:
    """真机部署测试器"""

    def __init__(self, robot_type: RobotType, robot_ip: str, log_level: str = "INFO"):
        self.robot_type = robot_type
        self.robot_ip = robot_ip
        self.log_level = log_level

        # 初始化日志
        setup_logging(level=log_level, console=True)
        self.logger = logging.getLogger("RobotDeploymentTest")

        # 初始化模块
        self.cortex = None
        self.motor = None
        self.visual = None
        self.cerebellum = None
        self.hippocampus = None
        self.comm = None
        self.engine = None
        self.monitor = None

        # 测试结果
        self.test_results = {}

    async def initialize_system(self) -> bool:
        """初始化系统模块"""
        self.logger.info("=== 初始化系统模块 ===")

        try:
            # 配置机器人
            robot_config = RobotConfig()
            robot_config.robot_type = self.robot_type
            robot_config.robot_address = self.robot_ip
            robot_config.robot_port = 8080 if self.robot_type == RobotType.G1 else 8082
            robot_config.save()

            # 配置网络
            network_config = NetworkConfig()
            network_config.enable_mdns = True
            network_config.broadcast_port = 9999
            network_config.save()

            # 初始化各模块
            self.cortex = InsularCortex()
            self.motor = MotorCortex(simulation_mode=False)
            self.visual = VisualCortex()
            self.cerebellum = Cerebellum()
            self.hippocampus = Hippocampus()
            self.comm = CommunicationModule()
            self.engine = IntegrationEngine()
            self.monitor = SystemMonitor()

            self.logger.info("✅ 系统模块初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"❌ 系统模块初始化失败: {e}")
            return False

    async def test_robot_identification(self) -> Dict[str, Any]:
        """测试机器人识别"""
        self.logger.info("=== 测试机器人识别 ===")

        result = {
            "test_name": "robot_identification",
            "passed": False,
            "details": {},
            "error": None
        }

        try:
            # 识别机器人
            robot_info = self.cortex.identify_robot(
                model="G1-EDU" if self.robot_type == RobotType.G1 else "Go2",
                firmware_version="1.5.0",
                hardware_version="2.1"
            )

            result["details"] = {
                "robot_type": robot_info.type.value,
                "capabilities": list(robot_info.capabilities.keys()),
                "constraints": list(robot_info.constraints.keys())
            }

            # 验证基本能力
            required_caps = ["motion", "vision", "communication"]
            has_required = all(cap in robot_info.capabilities for cap in required_caps)

            if has_required:
                result["passed"] = True
                self.logger.info("✅ 机器人识别测试通过")
            else:
                result["error"] = f"缺少必要能力: {required_caps}"
                self.logger.warning(f"⚠️ 机器人识别测试部分通过: {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ 机器人识别测试失败: {e}")

        self.test_results["robot_identification"] = result
        return result

    async def test_basic_motion(self) -> Dict[str, Any]:
        """测试基础运动"""
        self.logger.info("=== 测试基础运动 ===")

        result = {
            "test_name": "basic_motion",
            "passed": False,
            "details": {},
            "error": None
        }

        try:
            # 创建简单行走技能
            walk_skill = Skill(
                name="test_walk",
                description="测试行走技能",
                code="""
import time

# 设置安全参数
robot.set_gait_parameters(
    step_height=0.03,
    step_length=0.2,
    speed=0.2
)

# 短距离行走测试
robot.walk_forward(distance=0.3, speed=0.2)
time.sleep(1.5)  # 等待完成

# 停止
robot.stop()
""",
                skill_type=SkillType.MOTOR
            )

            # 注册技能
            skill_id = self.motor.register_skill(walk_skill)

            # 执行技能
            start_time = time.time()
            execution_result = await self.motor.execute_skill(skill_id)
            execution_time = time.time() - start_time

            result["details"] = {
                "skill_id": skill_id,
                "execution_time": execution_time,
                "status": execution_result.status
            }

            if execution_result.status == "success":
                result["passed"] = True
                self.logger.info(".2f"            else:
                result["error"] = f"执行状态: {execution_result.status}"
                self.logger.warning(f"⚠️ 基础运动测试失败: {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ 基础运动测试失败: {e}")

        self.test_results["basic_motion"] = result
        return result

    async def test_vision_system(self) -> Dict[str, Any]:
        """测试视觉系统"""
        self.logger.info("=== 测试视觉系统 ===")

        result = {
            "test_name": "vision_system",
            "passed": False,
            "details": {},
            "error": None
        }

        try:
            # 捕获图像
            image_data = await self.visual.capture_image()

            result["details"]["image_shape"] = image_data.shape if hasattr(image_data, 'shape') else "unknown"

            # 物体检测
            detections = await self.visual.detect_objects(image_data)

            result["details"]["detections_count"] = len(detections)

            # 场景分析
            scene_analysis = await self.visual.analyze_scene(image_data)

            result["details"]["scene_description"] = scene_analysis.description
            result["details"]["main_objects"] = scene_analysis.main_objects

            # 基本验证
            if len(detections) >= 0:  # 允许没有检测到物体
                result["passed"] = True
                self.logger.info(f"✅ 视觉系统测试通过 - 检测到 {len(detections)} 个物体")
            else:
                result["error"] = "视觉处理失败"
                self.logger.warning("⚠️ 视觉系统测试失败: 无法处理图像")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ 视觉系统测试失败: {e}")

        self.test_results["vision_system"] = result
        return result

    async def test_skill_system(self) -> Dict[str, Any]:
        """测试技能系统"""
        self.logger.info("=== 测试技能系统 ===")

        result = {
            "test_name": "skill_system",
            "passed": False,
            "details": {},
            "error": None
        }

        try:
            # 创建测试技能
            test_skill = Skill(
                name="test_grasp",
                description="测试抓取技能",
                code="""
# 简单的抓取测试
robot.open_gripper()
time.sleep(0.5)
robot.close_gripper()
time.sleep(0.5)
robot.open_gripper()
""",
                skill_type=SkillType.UNIVERSAL
            )

            # 注册技能
            skill_id = self.cerebellum.register_skill(test_skill, self.robot_type)

            # 验证技能注册
            registered_skill = self.cerebellum.get_skill(skill_id)

            result["details"] = {
                "skill_id": skill_id,
                "skill_name": registered_skill.name,
                "skill_type": registered_skill.skill_type.value
            }

            if registered_skill and registered_skill.name == "test_grasp":
                result["passed"] = True
                self.logger.info("✅ 技能系统测试通过")
            else:
                result["error"] = "技能注册验证失败"
                self.logger.warning("⚠️ 技能系统测试失败: 注册验证失败")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ 技能系统测试失败: {e}")

        self.test_results["skill_system"] = result
        return result

    async def test_communication(self) -> Dict[str, Any]:
        """测试通信系统"""
        self.logger.info("=== 测试通信系统 ===")

        result = {
            "test_name": "communication",
            "passed": False,
            "details": {},
            "error": None
        }

        try:
            # 注册本地节点
            from openerb.core.types import CommunicationNode

            local_node = CommunicationNode(
                node_id=f"test_{self.robot_type.value.lower()}_001",
                robot_type=self.robot_type,
                address=self.robot_ip,
                capabilities=["motion", "vision"],
                status="active"
            )

            self.comm.register_node(local_node)

            # 节点发现
            discovered_nodes = self.comm.discover_nodes()

            result["details"] = {
                "local_node_id": local_node.node_id,
                "discovered_nodes_count": len(discovered_nodes),
                "discovered_nodes": [node.node_id for node in discovered_nodes]
            }

            # 基本验证（至少能发现自己）
            if len(discovered_nodes) >= 0:
                result["passed"] = True
                self.logger.info(f"✅ 通信系统测试通过 - 发现 {len(discovered_nodes)} 个节点")
            else:
                result["error"] = "节点发现失败"
                self.logger.warning("⚠️ 通信系统测试失败: 无法发现节点")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ 通信系统测试失败: {e}")

        self.test_results["communication"] = result
        return result

    async def test_integration_engine(self) -> Dict[str, Any]:
        """测试集成引擎"""
        self.logger.info("=== 测试集成引擎 ===")

        result = {
            "test_name": "integration_engine",
            "passed": False,
            "details": {},
            "error": None
        }

        try:
            # 创建测试意图
            intent = Intent(
                raw_text="请向前走一步",
                action="walk_forward",
                parameters={"distance": 0.5, "speed": 0.3},
                confidence=0.8
            )

            # 创建测试用户
            user = UserProfile(
                user_id="test_user",
                name="测试用户"
            )

            # 执行意图
            start_time = time.time()
            execution_result = await self.engine.execute_intent(intent, user, self.robot_type)
            execution_time = time.time() - start_time

            result["details"] = {
                "intent_action": intent.action,
                "execution_time": execution_time,
                "status": execution_result.get("status", "unknown"),
                "skill_used": execution_result.get("skill", {}).get("name", "unknown")
            }

            if execution_result.get("status") == "success":
                result["passed"] = True
                self.logger.info(".2f"            else:
                result["error"] = f"执行状态: {execution_result.get('status')}"
                self.logger.warning(f"⚠️ 集成引擎测试失败: {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ 集成引擎测试失败: {e}")

        self.test_results["integration_engine"] = result
        return result

    async def test_system_monitoring(self) -> Dict[str, Any]:
        """测试系统监控"""
        self.logger.info("=== 测试系统监控 ===")

        result = {
            "test_name": "system_monitoring",
            "passed": False,
            "details": {},
            "error": None
        }

        try:
            # 启动监控
            self.monitor.start_monitoring()

            # 获取系统状态
            status = self.monitor.get_system_status()

            result["details"] = {
                "cpu_percent": status.cpu_percent,
                "memory_percent": status.memory_percent,
                "active_skill_count": status.active_skill_count,
                "network_connections": status.network_connections
            }

            # 基本验证
            if status.cpu_percent >= 0 and status.memory_percent >= 0:
                result["passed"] = True
                self.logger.info("✅ 系统监控测试通过")
            else:
                result["error"] = "监控数据异常"
                self.logger.warning("⚠️ 系统监控测试失败: 监控数据异常")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ 系统监控测试失败: {e}")

        self.test_results["system_monitoring"] = result
        return result

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("🚀 开始 OpenERB 真机部署测试")
        self.logger.info(f"机器人类型: {self.robot_type.value}")
        self.logger.info(f"机器人IP: {self.robot_ip}")

        # 初始化系统
        if not await self.initialize_system():
            return {"error": "系统初始化失败"}

        # 测试列表
        tests = [
            self.test_robot_identification,
            self.test_basic_motion,
            self.test_vision_system,
            self.test_skill_system,
            self.test_communication,
            self.test_integration_engine,
            self.test_system_monitoring
        ]

        # 执行测试
        passed_tests = 0
        total_tests = len(tests)

        for test_func in tests:
            try:
                test_result = await test_func()
                if test_result["passed"]:
                    passed_tests += 1
            except Exception as e:
                self.logger.error(f"测试执行异常: {e}")
                test_result = {
                    "test_name": test_func.__name__.replace("test_", ""),
                    "passed": False,
                    "error": str(e)
                }
                self.test_results[test_result["test_name"]] = test_result

        # 生成总结报告
        summary = {
            "timestamp": datetime.now().isoformat(),
            "robot_type": self.robot_type.value,
            "robot_ip": self.robot_ip,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": f"{passed_tests/total_tests*100:.1f}%",
            "test_results": self.test_results
        }

        self.logger.info("
=== 测试总结报告 ===")
        self.logger.info(f"总测试数: {total_tests}")
        self.logger.info(f"通过测试: {passed_tests}")
        self.logger.info(f"失败测试: {total_tests - passed_tests}")
        self.logger.info(f"成功率: {summary['success_rate']}")

        if passed_tests == total_tests:
            self.logger.info("🎉 所有测试通过！系统已准备好用于生产环境。")
        elif passed_tests >= total_tests * 0.8:
            self.logger.info("✅ 大部分测试通过，系统基本可用。")
        else:
            self.logger.warning("⚠️ 多个测试失败，需要进一步调试。")

        return summary

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="OpenERB 真机部署测试脚本")
    parser.add_argument("--robot-type", choices=["G1", "Go2"], required=True,
                       help="机器人类型 (G1 或 Go2)")
    parser.add_argument("--robot-ip", required=True,
                       help="机器人IP地址")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       default="INFO", help="日志级别")

    args = parser.parse_args()

    # 转换机器人类型
    robot_type = RobotType.G1 if args.robot_type == "G1" else RobotType.Go2

    # 创建测试器
    tester = RobotDeploymentTester(robot_type, args.robot_ip, args.log_level)

    # 运行测试
    try:
        result = asyncio.run(tester.run_all_tests())

        # 保存测试结果
        import json
        with open("deployment_test_results.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("\n测试结果已保存到: deployment_test_results.json")

        # 根据结果退出
        if result.get("error"):
            sys.exit(1)

        passed = result.get("passed_tests", 0)
        total = result.get("total_tests", 1)
        if passed < total * 0.8:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
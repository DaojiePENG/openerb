#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for OpenERB Embodied Brain Interface.

Tests all brain-like capabilities:
1. Marker Routing — LLM produces correct markers or fallback catches them
2. Code Generation — produces reusable, parameterized, validator-safe code
3. Skill Persistence — new skills saved to JSON, loaded on restart
4. Skill Reuse — subsequent similar requests reuse existing skills
5. Skill Listing — [LIST_SKILLS] triggers table display
6. Multi-turn Memory — conversation context maintained
7. Multi-language — Chinese and English
8. Edge Cases — ambiguous input, follow-ups

Usage:
    python scripts/test_brain_e2e.py
"""

import asyncio
import json
import os
import sys
import time
import shutil
import re
from datetime import datetime
from io import StringIO
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openerb.interface.embodied_brain_interface import EmbodiedBrainInterface
from openerb.core.types import RobotType
from openerb.llm.base import Message


# ═══════════════════════════════════════════════════════════
# Test Framework
# ═══════════════════════════════════════════════════════════

@dataclass
class TestResult:
    name: str
    category: str
    input_text: str
    passed: bool
    details: str = ""
    marker_expected: Optional[str] = None
    marker_actual: Optional[str] = None
    llm_response: str = ""
    execution_output: str = ""
    duration: float = 0.0
    skill_persisted: bool = False
    skill_reused: bool = False
    code_generated: str = ""


@dataclass
class TestSuite:
    results: List[TestResult] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def total(self):
        return len(self.results)

    @property
    def passed(self):
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self):
        return sum(1 for r in self.results if not r.passed)

    @property
    def pass_rate(self):
        return self.passed / self.total * 100 if self.total else 0


class BrainTestHarness:
    """Automated test harness that drives EmbodiedBrainInterface programmatically."""

    def __init__(self, skill_library_path: Path):
        self.skill_library_path = skill_library_path
        self.interface: Optional[EmbodiedBrainInterface] = None
        self.suite = TestSuite()
        self.captured_output: List[str] = []
        self._original_print = None

    def _reset_skill_library(self):
        """Start with a clean skill library."""
        self.skill_library_path.parent.mkdir(parents=True, exist_ok=True)
        self.skill_library_path.write_text("{}")

    def _create_interface(self):
        """Create a fresh interface instance."""
        self.interface = EmbodiedBrainInterface(robot_body=RobotType.G1)
        # Redirect skill library to our test path
        if self.interface.cerebellum:
            self.interface.cerebellum.library._storage_path = self.skill_library_path
            self.interface.cerebellum.library.skills.clear()
            self.interface.cerebellum.library._load_from_disk()

    def _get_skill_library_contents(self) -> dict:
        """Read the current skill library JSON."""
        try:
            return json.loads(self.skill_library_path.read_text())
        except Exception:
            return {}

    def _capture_console_start(self):
        """Start capturing console output."""
        self.captured_output = []
        original_print = self.interface.console.print

        def capturing_print(*args, **kwargs):
            rendered_parts = []
            for a in args:
                # Rich renderables (Table, etc.) need special handling
                if hasattr(a, '__rich_console__') or hasattr(a, '__rich__'):
                    from io import StringIO
                    from rich.console import Console as TempConsole
                    buf = StringIO()
                    temp = TempConsole(file=buf, width=120, force_terminal=False)
                    temp.print(a)
                    rendered_parts.append(buf.getvalue())
                else:
                    rendered_parts.append(str(a))
            text = " ".join(rendered_parts)
            self.captured_output.append(text)
            original_print(*args, **kwargs)

        self._original_print = original_print
        self.interface.console.print = capturing_print

    def _capture_console_stop(self):
        """Stop capturing and restore original print."""
        if self._original_print:
            self.interface.console.print = self._original_print

    def _get_captured_text(self) -> str:
        return "\n".join(self.captured_output)

    async def _send_message(self, user_input: str) -> dict:
        """Send a message and capture all outputs and side effects.

        Returns a dict with:
        - llm_response: raw LLM response
        - marker: detected marker
        - console_output: all captured console text
        - skill_library: current skill library state
        - execution_success: whether action execution succeeded
        """
        self._capture_console_start()

        # Intercept LLM response
        original_chat = self.interface._chat_with_llm
        llm_response = None

        async def intercept_chat(inp):
            nonlocal llm_response
            resp = await original_chat(inp)
            llm_response = resp
            return resp

        self.interface._chat_with_llm = intercept_chat

        try:
            await self.interface._process_user_input(user_input)
        except Exception as e:
            self.captured_output.append(f"[ERROR] {e}")
        finally:
            self.interface._chat_with_llm = original_chat
            self._capture_console_stop()

        console_text = self._get_captured_text()

        # Detect marker
        marker = None
        if llm_response:
            marker = self.interface._extract_marker(llm_response)

        return {
            "llm_response": llm_response or "",
            "marker": marker,
            "console_output": console_text,
            "skill_library": self._get_skill_library_contents(),
            "execution_success": "Method:" in console_text and "⚠" not in console_text,
            "skill_persisted": "💾" in console_text,
            "skill_reused": "♻️" in console_text or "Found existing skill" in console_text,
            "validation_failed": "failed validation" in console_text.lower(),
        }

    # ═══════════════════════════════════════════════════════════
    # Test Categories
    # ═══════════════════════════════════════════════════════════

    async def test_marker_routing(self):
        """Category 1: Test that markers are correctly routed."""
        print("\n" + "=" * 60)
        print("📋 CATEGORY 1: Marker Routing")
        print("=" * 60)

        cases = [
            # (name, input, expected_marker)
            ("math_en", "calculate 8 + 8", "ACTION_REQUIRED"),
            ("math_cn", "计算 9 * 9", "ACTION_REQUIRED"),
            ("math_bare", "1 + 1", "ACTION_REQUIRED"),
            ("fibonacci_en", "generate first 10 fibonacci numbers", "ACTION_REQUIRED"),
            ("fibonacci_cn", "输出前10个斐波那契数列", "ACTION_REQUIRED"),
            ("skills_en", "show your skills", "LIST_SKILLS"),
            ("skills_cn", "技能列表", "LIST_SKILLS"),
            ("chat_en", "hello, how are you?", None),
            ("chat_cn", "你好，今天天气怎么样？", None),
        ]

        for name, inp, expected in cases:
            t0 = time.time()
            res = await self._send_message(inp)
            dt = time.time() - t0

            actual_marker = res["marker"]
            passed = actual_marker == expected

            result = TestResult(
                name=f"marker_{name}",
                category="Marker Routing",
                input_text=inp,
                passed=passed,
                marker_expected=expected,
                marker_actual=actual_marker,
                llm_response=str(res["llm_response"])[:200],
                duration=dt,
                details=f"Expected={expected}, Got={actual_marker}",
            )
            self.suite.results.append(result)
            status = "✅" if passed else "❌"
            print(f"  {status} {name}: input='{inp}' → marker={actual_marker} (expected={expected}) [{dt:.1f}s]")

    async def test_code_generation_quality(self):
        """Category 2: Test that generated code is reusable and passes validation."""
        print("\n" + "=" * 60)
        print("📋 CATEGORY 2: Code Generation Quality")
        print("=" * 60)

        # Reset for clean state
        self._reset_skill_library()
        self._create_interface()

        cases = [
            ("calc_8plus8", "calculate 8 + 8", ["def ", "print"]),
            ("fibonacci_10", "generate first 10 fibonacci numbers", ["def ", "fibonacci", "print"]),
        ]

        for name, inp, expected_patterns in cases:
            t0 = time.time()
            skills_before = set(self._get_skill_library_contents().keys())
            res = await self._send_message(inp)
            dt = time.time() - t0

            # Check skill library for the NEWLY generated code (not pre-existing)
            skills = res["skill_library"]
            generated_code = ""
            new_skill_ids = set(skills.keys()) - skills_before
            if new_skill_ids:
                newest_id = max(new_skill_ids)  # latest added
                generated_code = skills[newest_id].get("code", "")
            elif skills:
                # Fallback: get last skill
                generated_code = list(skills.values())[-1].get("code", "")

            pattern_checks = []
            for pat in expected_patterns:
                found = pat.lower() in generated_code.lower()
                pattern_checks.append((pat, found))

            all_patterns_found = all(f for _, f in pattern_checks)
            validation_ok = not res["validation_failed"]
            execution_ok = res["execution_success"]

            passed = all_patterns_found and validation_ok and execution_ok

            details_parts = []
            if not validation_ok:
                details_parts.append("VALIDATION_FAILED")
            if not execution_ok:
                details_parts.append("EXECUTION_FAILED")
            for pat, found in pattern_checks:
                if not found:
                    details_parts.append(f"MISSING_PATTERN: '{pat}'")

            result = TestResult(
                name=f"codegen_{name}",
                category="Code Generation",
                input_text=inp,
                passed=passed,
                details="; ".join(details_parts) if details_parts else "OK",
                execution_output=res["console_output"][:300],
                duration=dt,
                code_generated=generated_code[:500],
                skill_persisted=res["skill_persisted"],
            )
            self.suite.results.append(result)
            status = "✅" if passed else "❌"
            print(f"  {status} {name}: validation={validation_ok}, execution={execution_ok}, patterns={all_patterns_found} [{dt:.1f}s]")
            if generated_code:
                # Show first 3 lines of code
                code_preview = "\n".join(generated_code.split("\n")[:3])
                print(f"      Code: {code_preview}")

    async def test_skill_persistence(self):
        """Category 3: Test that skills are persisted and survive restart."""
        print("\n" + "=" * 60)
        print("📋 CATEGORY 3: Skill Persistence")
        print("=" * 60)

        # Clean start
        self._reset_skill_library()
        self._create_interface()

        # Teach a skill
        t0 = time.time()
        res = await self._send_message("calculate 2 + 3")
        dt = time.time() - t0

        skills_after_learn = self._get_skill_library_contents()
        has_skills = len(skills_after_learn) > 0

        result = TestResult(
            name="persist_learn",
            category="Skill Persistence",
            input_text="calculate 2 + 3",
            passed=has_skills and res["skill_persisted"],
            details=f"Skills in library: {len(skills_after_learn)}, persisted_flag: {res['skill_persisted']}",
            duration=dt,
            skill_persisted=res["skill_persisted"],
        )
        self.suite.results.append(result)
        status = "✅" if result.passed else "❌"
        print(f"  {status} persist_learn: skills_count={len(skills_after_learn)}, persisted={res['skill_persisted']} [{dt:.1f}s]")

        # Simulate restart — create new interface, check skills loaded
        self._create_interface()
        skills_after_restart = self._get_skill_library_contents()
        survived = len(skills_after_restart) > 0 and skills_after_restart == skills_after_learn

        result2 = TestResult(
            name="persist_survive_restart",
            category="Skill Persistence",
            input_text="(restart simulation)",
            passed=survived,
            details=f"Skills after restart: {len(skills_after_restart)}",
            duration=0,
        )
        self.suite.results.append(result2)
        status = "✅" if survived else "❌"
        print(f"  {status} persist_survive_restart: skills_count={len(skills_after_restart)}")

    async def test_skill_reuse(self):
        """Category 4: Test that existing skills are found and reused."""
        print("\n" + "=" * 60)
        print("📋 CATEGORY 4: Skill Reuse")
        print("=" * 60)

        # Must already have skills from Category 3 (persistence test)
        # or teach one fresh
        skills = self._get_skill_library_contents()
        if not skills:
            print("  ⚠ No skills in library, teaching one first...")
            self._reset_skill_library()
            self._create_interface()
            await self._send_message("calculate 5 + 5")
            skills = self._get_skill_library_contents()

        # Now ask a similar math question — should reuse
        t0 = time.time()
        res = await self._send_message("calculate 3 + 7")
        dt = time.time() - t0

        reused = res["skill_reused"]
        executed = res["execution_success"]

        result = TestResult(
            name="reuse_math",
            category="Skill Reuse",
            input_text="calculate 3 + 7",
            passed=reused and executed,
            details=f"reused={reused}, executed={executed}",
            duration=dt,
            skill_reused=reused,
            execution_output=res["console_output"][:300],
        )
        self.suite.results.append(result)
        status = "✅" if result.passed else "❌"
        print(f"  {status} reuse_math: reused={reused}, executed={executed} [{dt:.1f}s]")

        # Check that a second different math also reuses
        t0 = time.time()
        res2 = await self._send_message("9 * 9")
        dt2 = time.time() - t0

        reused2 = res2["skill_reused"]
        result2 = TestResult(
            name="reuse_math_different_op",
            category="Skill Reuse",
            input_text="9 * 9",
            passed=reused2,
            details=f"reused={reused2}",
            duration=dt2,
            skill_reused=reused2,
        )
        self.suite.results.append(result2)
        status = "✅" if result2.passed else "❌"
        print(f"  {status} reuse_math_different_op: reused={reused2} [{dt2:.1f}s]")

    async def test_skill_listing(self):
        """Category 5: Test that skill listing shows the table."""
        print("\n" + "=" * 60)
        print("📋 CATEGORY 5: Skill Listing")
        print("=" * 60)

        # Ensure we have skills
        skills = self._get_skill_library_contents()
        if not skills:
            await self._send_message("calculate 1 + 1")

        cases = [
            ("list_en", "show your skills"),
            ("list_cn", "技能列表"),
            ("list_what", "what can you do?"),
        ]

        for name, inp in cases:
            t0 = time.time()
            res = await self._send_message(inp)
            dt = time.time() - t0

            console = res["console_output"]
            # Check for table indicators
            has_table = "Skill Library" in console or "┏" in console or "┃" in console
            has_empty_msg = "empty" in console.lower()

            passed = has_table or has_empty_msg  # Either table or empty notice

            result = TestResult(
                name=f"listing_{name}",
                category="Skill Listing",
                input_text=inp,
                passed=passed,
                details=f"table_shown={has_table}, empty_msg={has_empty_msg}",
                duration=dt,
                marker_actual=res["marker"],
                execution_output=console[:300],
            )
            self.suite.results.append(result)
            status = "✅" if passed else "❌"
            print(f"  {status} {name}: table={has_table}, empty={has_empty_msg}, marker={res['marker']} [{dt:.1f}s]")

    async def test_multi_turn_conversation(self):
        """Category 6: Test multi-turn memory and context."""
        print("\n" + "=" * 60)
        print("📋 CATEGORY 6: Multi-turn Conversation")
        print("=" * 60)

        # Reset for clean multi-turn test
        self._reset_skill_library()
        self._create_interface()

        # Turn 1: greeting
        t0 = time.time()
        res1 = await self._send_message("我叫小明，请记住我的名字")
        dt1 = time.time() - t0

        # Turn 2: ask if it remembers
        t0 = time.time()
        res2 = await self._send_message("你还记得我叫什么吗？")
        dt2 = time.time() - t0

        llm_resp2 = str(res2["llm_response"]).lower()
        remembers_name = "小明" in llm_resp2 or "小明" in res2["console_output"]

        result = TestResult(
            name="multiturn_remember_name",
            category="Multi-turn",
            input_text="你还记得我叫什么吗？",
            passed=remembers_name,
            details=f"LLM mentions '小明': {remembers_name}",
            duration=dt1 + dt2,
            llm_response=str(res2["llm_response"])[:200],
        )
        self.suite.results.append(result)
        status = "✅" if result.passed else "❌"
        print(f"  {status} remember_name: remembers={remembers_name} [{dt1+dt2:.1f}s]")

    async def test_chinese_english(self):
        """Category 7: Test bilingual support."""
        print("\n" + "=" * 60)
        print("📋 CATEGORY 7: Chinese & English Support")
        print("=" * 60)

        # Chinese math
        t0 = time.time()
        res_cn = await self._send_message("计算 6 乘以 7")
        dt_cn = time.time() - t0

        cn_marker = res_cn["marker"]
        cn_ok = cn_marker == "ACTION_REQUIRED"

        result_cn = TestResult(
            name="bilingual_cn_math",
            category="Bilingual",
            input_text="计算 6 乘以 7",
            passed=cn_ok,
            marker_expected="ACTION_REQUIRED",
            marker_actual=cn_marker,
            duration=dt_cn,
        )
        self.suite.results.append(result_cn)
        status = "✅" if cn_ok else "❌"
        print(f"  {status} cn_math: marker={cn_marker} [{dt_cn:.1f}s]")

        # English greeting
        t0 = time.time()
        res_en = await self._send_message("Hi there! Tell me a joke.")
        dt_en = time.time() - t0

        en_marker = res_en["marker"]
        en_ok = en_marker is None  # should be chat

        result_en = TestResult(
            name="bilingual_en_chat",
            category="Bilingual",
            input_text="Hi there! Tell me a joke.",
            passed=en_ok,
            marker_expected="None",
            marker_actual=str(en_marker),
            duration=dt_en,
        )
        self.suite.results.append(result_en)
        status = "✅" if en_ok else "❌"
        print(f"  {status} en_chat: marker={en_marker} [{dt_en:.1f}s]")

    async def test_edge_cases(self):
        """Category 8: Edge cases and error resilience."""
        print("\n" + "=" * 60)
        print("📋 CATEGORY 8: Edge Cases")
        print("=" * 60)

        # Empty-ish input
        t0 = time.time()
        res = await self._send_message("...")
        dt = time.time() - t0
        passed = res["marker"] is None  # should be treated as chat
        result = TestResult(
            name="edge_ellipsis",
            category="Edge Cases",
            input_text="...",
            passed=passed,
            details=f"marker={res['marker']}",
            duration=dt,
        )
        self.suite.results.append(result)
        status = "✅" if passed else "❌"
        print(f"  {status} ellipsis: marker={res['marker']} [{dt:.1f}s]")

        # Very large number calculation
        t0 = time.time()
        res2 = await self._send_message("calculate 999999 * 999999")
        dt2 = time.time() - t0
        passed2 = res2["marker"] == "ACTION_REQUIRED"
        result2 = TestResult(
            name="edge_large_calc",
            category="Edge Cases",
            input_text="999999 * 999999",
            passed=passed2,
            details=f"marker={res2['marker']}, executed={res2['execution_success']}",
            duration=dt2,
        )
        self.suite.results.append(result2)
        status = "✅" if passed2 else "❌"
        print(f"  {status} large_calc: marker={res2['marker']} [{dt2:.1f}s]")

    # ═══════════════════════════════════════════════════════════
    # Report Generation
    # ═══════════════════════════════════════════════════════════

    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        s = self.suite
        duration = s.end_time - s.start_time

        lines = []
        lines.append("=" * 70)
        lines.append("  OpenERB Embodied Brain — Comprehensive E2E Test Report")
        lines.append(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Model: {os.environ.get('LLM_MODEL', 'unknown')}")
        lines.append(f"  Duration: {duration:.1f}s")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"  TOTAL: {s.total}  |  PASSED: {s.passed}  |  FAILED: {s.failed}  |  RATE: {s.pass_rate:.1f}%")
        lines.append("")

        # Group by category
        categories = {}
        for r in s.results:
            categories.setdefault(r.category, []).append(r)

        for cat, results in categories.items():
            cat_passed = sum(1 for r in results if r.passed)
            cat_total = len(results)
            lines.append(f"┌─ {cat} ({cat_passed}/{cat_total})")
            for r in results:
                icon = "✅" if r.passed else "❌"
                lines.append(f"│  {icon} {r.name}: {r.details}")
                if not r.passed and r.llm_response:
                    lines.append(f"│     LLM: {r.llm_response[:120]}")
                if not r.passed and r.code_generated:
                    lines.append(f"│     Code: {r.code_generated[:120]}")
            lines.append(f"└─")
            lines.append("")

        # Summary of failures
        failures = [r for r in s.results if not r.passed]
        if failures:
            lines.append("─" * 70)
            lines.append("  FAILURE DETAILS")
            lines.append("─" * 70)
            for r in failures:
                lines.append(f"  ❌ {r.name} ({r.category})")
                lines.append(f"     Input: {r.input_text}")
                lines.append(f"     Details: {r.details}")
                if r.llm_response:
                    lines.append(f"     LLM response: {r.llm_response[:200]}")
                if r.execution_output:
                    lines.append(f"     Console: {r.execution_output[:200]}")
                lines.append("")

        lines.append("=" * 70)
        lines.append("  END OF REPORT")
        lines.append("=" * 70)

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════
    # Main Runner
    # ═══════════════════════════════════════════════════════════

    async def run_all(self):
        """Run all test categories in order."""
        self.suite = TestSuite()
        self.suite.start_time = time.time()

        print("\n🧠 OpenERB Embodied Brain — Comprehensive E2E Test")
        print(f"   Model: {os.environ.get('LLM_MODEL', 'unknown')}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Skill library: {self.skill_library_path}")
        print()

        # Phase 1: Marker routing (clean state)
        self._reset_skill_library()
        self._create_interface()
        await self.test_marker_routing()

        # Phase 2: Code generation quality (clean state)
        await self.test_code_generation_quality()

        # Phase 3: Persistence (clean state)
        await self.test_skill_persistence()

        # Phase 4: Skill reuse (uses skills from Phase 3)
        await self.test_skill_reuse()

        # Phase 5: Skill listing (uses skills from Phase 3/4)
        await self.test_skill_listing()

        # Phase 6: Multi-turn conversation
        await self.test_multi_turn_conversation()

        # Phase 7: Bilingual
        self._create_interface()
        await self.test_chinese_english()

        # Phase 8: Edge cases
        await self.test_edge_cases()

        self.suite.end_time = time.time()

        # Generate and print report
        report = self.generate_report()
        print("\n")
        print(report)

        # Save report to file
        report_path = Path(__file__).resolve().parent.parent / "test_report_e2e.txt"
        report_path.write_text(report)
        print(f"\n📄 Report saved to: {report_path}")

        return self.suite


async def main():
    # Use a test-specific skill library path
    test_skill_path = Path(__file__).resolve().parent.parent / "openerb" / "skills" / "test_e2e_skill_library.json"

    harness = BrainTestHarness(skill_library_path=test_skill_path)

    try:
        suite = await harness.run_all()
    finally:
        # Clean up test skill library
        if test_skill_path.exists():
            test_skill_path.unlink()

    # Exit with code based on results
    sys.exit(0 if suite.failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())

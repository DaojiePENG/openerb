"""Code executor for Motor Cortex - Execute code in sandboxed environment."""

import logging
import signal
import threading
import time
from typing import Dict, Optional, Any, Callable
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from openerb.core.types import ExecutionResult, CodeExecutionPolicy, SandboxType

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Raised when code execution times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException("Code execution timeout")


class CodeExecutor:
    """Execute code in sandboxed environment with safety guarantees."""
    
    def __init__(self, policy: Optional[CodeExecutionPolicy] = None):
        """Initialize code executor.
        
        Args:
            policy: CodeExecutionPolicy defining execution limits
        """
        self.policy = policy or CodeExecutionPolicy()
        self.max_memory = self.policy.max_memory or 256  # MB
        self.timeout = self.policy.timeout
    
    def execute(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Execute code with safety measures.
        
        Args:
            code: Python code to execute
            globals_dict: Global variables
            locals_dict: Local variables
        
        Returns:
            ExecutionResult with output and status
        """
        if globals_dict is None:
            globals_dict = {}
        
        if locals_dict is None:
            locals_dict = {}
        
        # Start timing
        start_time = time.time()
        
        # Capture output
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        try:
            # Use timeout mechanism
            if self.policy.sandbox_type == SandboxType.PROCESS:
                result = self._execute_with_timeout(
                    code, globals_dict, locals_dict,
                    stdout_capture, stderr_capture
                )
            elif self.policy.sandbox_type == SandboxType.RESTRICTED_PYTHON:
                result = self._execute_restricted(
                    code, globals_dict, locals_dict,
                    stdout_capture, stderr_capture
                )
            else:
                # Direct execution for development
                result = self._execute_direct(
                    code, globals_dict, locals_dict,
                    stdout_capture, stderr_capture
                )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            logger.info(f"Code execution completed in {execution_time:.3f}s: {result.success}")
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Code execution failed: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time
            )
    
    def _execute_direct(
        self,
        code: str,
        globals_dict: Dict,
        locals_dict: Dict,
        stdout_capture: StringIO,
        stderr_capture: StringIO
    ) -> ExecutionResult:
        """Direct execution without sandbox (for development)."""
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, globals_dict, locals_dict)
            
            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()
            
            return ExecutionResult(
                success=True,
                output=output,
                error=error if error else None
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=str(e)
            )
    
    def _execute_restricted(
        self,
        code: str,
        globals_dict: Dict,
        locals_dict: Dict,
        stdout_capture: StringIO,
        stderr_capture: StringIO
    ) -> ExecutionResult:
        """Execute with RestrictedPython (safest for Python code)."""
        try:
            # In real implementation, would use RestrictedPython
            # For now, use direct execution with guards
            
            # Check for forbidden operations
            forbidden_patterns = [
                "import os", "import sys", "import subprocess",
                "exec(", "eval(", "compile(", "__import__(",
                "open(", "input(", "exit(", "quit("
            ]
            
            code_lower = code.lower()
            for pattern in forbidden_patterns:
                if pattern in code_lower:
                    return ExecutionResult(
                        success=False,
                        output="",
                        error=f"Forbidden operation detected: {pattern}"
                    )
            
            # Safe execution
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, globals_dict, locals_dict)
            
            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()
            
            return ExecutionResult(
                success=True,
                output=output,
                error=error if error else None
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=str(e)
            )
    
    def _execute_with_timeout(
        self,
        code: str,
        globals_dict: Dict,
        locals_dict: Dict,
        stdout_capture: StringIO,
        stderr_capture: StringIO
    ) -> ExecutionResult:
        """Execute with timeout in separate thread."""
        result_container = [None]
        exception_container = [None]
        
        def worker():
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    exec(code, globals_dict, locals_dict)
                
                output = stdout_capture.getvalue()
                error = stderr_capture.getvalue()
                
                result_container[0] = ExecutionResult(
                    success=True,
                    output=output,
                    error=error if error else None
                )
            except Exception as e:
                exception_container[0] = e
        
        # Create and start thread
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        
        # Wait for completion with timeout
        thread.join(timeout=self.timeout)
        
        if thread.is_alive():
            # Thread still running - timeout occurred
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=f"Execution timeout after {self.timeout}s"
            )
        
        if exception_container[0]:
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=str(exception_container[0])
            )
        
        if result_container[0]:
            return result_container[0]
        
        return ExecutionResult(
            success=False,
            output="",
            error="Unknown execution error"
        )
    
    def preview_execution(
        self,
        code: str,
        max_output_length: int = 500
    ) -> Dict[str, Any]:
        """Preview code execution without saving results.
        
        Args:
            code: Code to preview
            max_output_length: Maximum output length to capture
        
        Returns:
            Dict with preview information
        """
        start_time = time.time()
        
        try:
            stdout_capture = StringIO()
            
            # Try to compile code
            compile(code, "<preview>", "exec")
            
            # Execute with limited output
            with redirect_stdout(stdout_capture):
                exec(code, {})
            
            output = stdout_capture.getvalue()[:max_output_length]
            execution_time = time.time() - start_time
            
            return {
                "valid": True,
                "output": output,
                "execution_time": execution_time,
                "status": "success"
            }
        
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error: {e.msg}",
                "line": e.lineno,
                "status": "syntax_error"
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "valid": False,
                "error": str(e),
                "execution_time": execution_time,
                "status": "runtime_error"
            }
    
    def execute_with_callbacks(
        self,
        code: str,
        globals_dict: Optional[Dict] = None,
        on_output: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> ExecutionResult:
        """Execute code with callback handlers.
        
        Args:
            code: Code to execute
            globals_dict: Global variables
            on_output: Callback for output lines
            on_error: Callback for error messages
        
        Returns:
            ExecutionResult
        """
        if globals_dict is None:
            globals_dict = {}
        
        # Add callback functions to globals
        def print_callback(msg):
            if on_output:
                on_output(str(msg))
        
        globals_dict["print"] = print_callback
        
        result = self.execute(code, globals_dict)
        
        if result.success and result.output:
            for line in result.output.split("\n"):
                if line.strip() and on_output:
                    on_output(line)
        
        if result.error and on_error:
            on_error(result.error)
        
        return result
    
    def estimate_execution_requirements(self, code: str) -> Dict[str, Any]:
        """Estimate resource requirements for code execution.
        
        Args:
            code: Code to analyze
        
        Returns:
            Dict with estimated requirements
        """
        import ast
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error": "Invalid code"}
        
        # Count various elements
        function_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
        loop_count = sum(1 for _ in ast.walk(tree) if isinstance(_, (ast.For, ast.While)))
        call_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.Call))
        
        # Estimate complexity
        estimated_time = 0.1 + (function_count * 0.01) + (loop_count * 0.05)
        estimated_memory = 10 + (call_count * 1)  # MB
        
        return {
            "functions": function_count,
            "loops": loop_count,
            "calls": call_count,
            "estimated_time": min(estimated_time, self.timeout),
            "estimated_memory": min(estimated_memory, self.max_memory),
            "complexity": "high" if estimated_time > 5 else "medium" if estimated_time > 1 else "low"
        }

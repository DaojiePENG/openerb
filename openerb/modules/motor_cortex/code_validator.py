"""Code validator for Motor Cortex - AST-based code validation and security checking."""

import ast
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from openerb.core.types import CodeExecutionPolicy, SandboxType

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """A validation issue found during code analysis."""
    severity: str  # "error", "warning", "info"
    issue_type: str  # e.g., "forbidden_import", "unsafe_builtin"
    message: str
    line_number: Optional[int] = None
    node: Optional[ast.AST] = None


@dataclass
class ValidationResult:
    """Result of code validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: str = ""


class CodeValidator:
    """Validate code for syntax, security, and compatibility."""
    
    def __init__(self, policy: Optional[CodeExecutionPolicy] = None):
        """Initialize code validator.
        
        Args:
            policy: CodeExecutionPolicy defining allowed operations
        """
        self.policy = policy or CodeExecutionPolicy()
        self.allowed_imports = set(self.policy.allowed_imports)
        self.forbidden_modules = set(self.policy.forbidden_modules)
        self.forbidden_builtins = set(self.policy.forbidden_builtins)
    
    def validate(self, code: str) -> ValidationResult:
        """Validate code comprehensively.
        
        Args:
            code: Python code to validate
        
        Returns:
            ValidationResult with all issues found
        """
        result = ValidationResult(valid=True)
        
        # 1. Syntax check
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result.valid = False
            result.issues.append(ValidationIssue(
                severity="error",
                issue_type="syntax_error",
                message=f"Syntax error: {e.msg}",
                line_number=e.lineno
            ))
            result.details = f"Code has syntax error at line {e.lineno}: {e.msg}"
            return result
        
        # 2. Security checks
        visitor = SecurityVisitor(self.policy)
        visitor.visit(tree)
        
        result.issues.extend(visitor.issues)
        result.warnings.extend(visitor.warnings)
        
        # 3. Metrics analysis
        metrics_visitor = MetricsVisitor()
        metrics_visitor.visit(tree)
        result.metrics = metrics_visitor.get_metrics()
        
        # Determine overall validity
        result.valid = len(result.issues) == 0
        
        if result.valid and result.warnings:
            result.details = f"Valid code with {len(result.warnings)} warnings"
        elif result.valid:
            result.details = "Code passed validation"
        else:
            result.details = f"Code has {len(result.issues)} critical issues"
        
        logger.info(f"Validation result: {result.details}")
        return result
    
    def check_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Quick syntax check.
        
        Args:
            code: Python code
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
    
    def check_imports(self, code: str) -> List[Tuple[str, bool]]:
        """Check code imports against allowed list.
        
        Args:
            code: Python code
        
        Returns:
            List of (import_name, is_allowed) tuples
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]  # Get top-level module
                    is_allowed = module in self.allowed_imports
                    imports.append((module, is_allowed))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    is_allowed = module in self.allowed_imports
                    imports.append((module, is_allowed))
        
        return imports
    
    def check_forbidden_calls(self, code: str) -> List[Tuple[str, int]]:
        """Check for forbidden function calls.
        
        Args:
            code: Python code
        
        Returns:
            List of (function_name, line_number) tuples for forbidden calls
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        forbidden_calls = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.forbidden_builtins:
                        forbidden_calls.append((node.func.id, node.lineno))
                
                # Check for attributes like os.system()
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id in self.forbidden_modules:
                            forbidden_calls.append(
                                (f"{node.func.value.id}.{node.func.attr}", node.lineno)
                            )
        
        return forbidden_calls
    
    def estimate_complexity(self, code: str) -> Dict[str, Any]:
        """Estimate code complexity.
        
        Args:
            code: Python code
        
        Returns:
            Dict with complexity metrics
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"complexity": "unknown"}
        
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        return {
            "cyclomatic_complexity": visitor.complexity,
            "function_count": visitor.function_count,
            "loop_depth": visitor.max_loop_depth,
            "recursion_risk": visitor.has_recursion
        }


class SecurityVisitor(ast.NodeVisitor):
    """AST visitor for security checks."""
    
    def __init__(self, policy: CodeExecutionPolicy):
        """Initialize security visitor.
        
        Args:
            policy: CodeExecutionPolicy
        """
        self.policy = policy
        self.issues: List[ValidationIssue] = []
        self.warnings: List[ValidationIssue] = []
        self.allowed_imports = set(policy.allowed_imports)
        self.forbidden_modules = set(policy.forbidden_modules)
        self.forbidden_builtins = set(policy.forbidden_builtins)
    
    def visit_Import(self, node: ast.Import) -> None:
        """Check import statements."""
        for alias in node.names:
            module = alias.name.split('.')[0]
            
            if module in self.forbidden_modules:
                self.issues.append(ValidationIssue(
                    severity="error",
                    issue_type="forbidden_import",
                    message=f"Forbidden import: {module}",
                    line_number=node.lineno,
                    node=node
                ))
            elif module not in self.allowed_imports and self.policy.sandbox_type != SandboxType.DISABLED:
                self.warnings.append(ValidationIssue(
                    severity="warning",
                    issue_type="unlisted_import",
                    message=f"Unlisted import: {module}",
                    line_number=node.lineno,
                    node=node
                ))
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from...import statements."""
        if node.module:
            module = node.module.split('.')[0]
            
            if module in self.forbidden_modules:
                self.issues.append(ValidationIssue(
                    severity="error",
                    issue_type="forbidden_import",
                    message=f"Forbidden import: {module}",
                    line_number=node.lineno,
                    node=node
                ))
            elif module not in self.allowed_imports and self.policy.sandbox_type != SandboxType.DISABLED:
                self.warnings.append(ValidationIssue(
                    severity="warning",
                    issue_type="unlisted_import",
                    message=f"Unlisted import: {module}",
                    line_number=node.lineno,
                    node=node
                ))
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id in self.forbidden_builtins:
                self.issues.append(ValidationIssue(
                    severity="error",
                    issue_type="forbidden_builtin",
                    message=f"Forbidden builtin: {node.func.id}",
                    line_number=node.lineno,
                    node=node
                ))
            elif node.func.id == "input" and not self.policy.enable_network:
                self.issues.append(ValidationIssue(
                    severity="error",
                    issue_type="unsafe_operation",
                    message="input() not allowed",
                    line_number=node.lineno,
                    node=node
                ))
        
        # Check for attribute access like os.system()
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in self.forbidden_modules:
                    self.issues.append(ValidationIssue(
                        severity="error",
                        issue_type="forbidden_module_access",
                        message=f"Forbidden module access: {node.func.value.id}",
                        line_number=node.lineno,
                        node=node
                    ))
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check attribute access."""
        if isinstance(node.value, ast.Name):
            if node.value.id in self.forbidden_modules:
                self.issues.append(ValidationIssue(
                    severity="error",
                    issue_type="forbidden_module_access",
                    message=f"Access to forbidden module: {node.value.id}",
                    line_number=node.lineno,
                    node=node
                ))
        
        self.generic_visit(node)


class MetricsVisitor(ast.NodeVisitor):
    """AST visitor for code metrics."""
    
    def __init__(self):
        """Initialize metrics visitor."""
        self.lines = 0
        self.function_count = 0
        self.class_count = 0
        self.variable_count = 0
        self.max_loop_depth = 0
        self.current_loop_depth = 0
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Count functions."""
        self.function_count += 1
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Count classes."""
        self.class_count += 1
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For) -> None:
        """Track loop depth."""
        self.current_loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.current_loop_depth)
        self.generic_visit(node)
        self.current_loop_depth -= 1
    
    def visit_While(self, node: ast.While) -> None:
        """Track loop depth."""
        self.current_loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.current_loop_depth)
        self.generic_visit(node)
        self.current_loop_depth -= 1
    
    def visit_Name(self, node: ast.Name) -> None:
        """Count variable accesses."""
        self.variable_count += 1
        self.generic_visit(node)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return {
            "functions": self.function_count,
            "classes": self.class_count,
            "variables": self.variable_count,
            "max_loop_depth": self.max_loop_depth
        }


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for complexity analysis."""
    
    def __init__(self):
        """Initialize complexity visitor."""
        self.complexity = 1  # Base complexity
        self.function_count = 0
        self.max_loop_depth = 0
        self.current_loop_depth = 0
        self.has_recursion = False
        self.defined_functions = set()
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self.function_count += 1
        self.defined_functions.add(node.name)
        self.generic_visit(node)
    
    def visit_If(self, node: ast.If) -> None:
        """If statement increases complexity."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For) -> None:
        """For loop increases complexity."""
        self.complexity += 1
        self.current_loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.current_loop_depth)
        self.generic_visit(node)
        self.current_loop_depth -= 1
    
    def visit_While(self, node: ast.While) -> None:
        """While loop increases complexity."""
        self.complexity += 1
        self.current_loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.current_loop_depth)
        self.generic_visit(node)
        self.current_loop_depth -= 1
    
    def visit_Call(self, node: ast.Call) -> None:
        """Check for recursive calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id in self.defined_functions:
                self.has_recursion = True
        
        self.generic_visit(node)

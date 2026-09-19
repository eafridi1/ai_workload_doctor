from pathlib import Path
import ast


class WorkloadAnalyzer:
    """Analyze a Python AI workload without executing it."""

    def __init__(self, workload_path: str):
        self.workload_path = Path(workload_path)

    def analyze(self) -> dict:
        """Return a structured analysis of the workload."""

        if not self.workload_path.exists():
            raise FileNotFoundError(
                f"Workload not found: {self.workload_path}"
            )

        if self.workload_path.suffix != ".py":
            raise ValueError("Currently only Python workloads are supported.")

        source = self.workload_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imports = []
        functions = []
        classes = []
        tensor_operations = []
        model_operations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)

            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)

            elif isinstance(node, ast.Call):
                call_name = self._get_call_name(node)

                if call_name:
                    if self._looks_like_tensor_operation(call_name):
                        tensor_operations.append(call_name)

                    if self._looks_like_model_operation(call_name):
                        model_operations.append(call_name)

        imports = sorted(set(imports))
        tensor_operations = sorted(set(tensor_operations))
        model_operations = sorted(set(model_operations))

        return {
            "workload": self.workload_path.name,
            "language": "Python",
            "lines_of_code": len(source.splitlines()),

            "imports": imports,
            "functions": sorted(set(functions)),
            "classes": sorted(set(classes)),

            "frameworks": self._detect_frameworks(imports),

            "pytorch_detected": self._detect_pytorch(imports),
            "tensorflow_detected": self._detect_tensorflow(imports),

            "cuda_references": self._detect_cuda(source),
            "rocm_references": self._detect_rocm(source),
            "hip_references": self._detect_hip(source),

            "gpu_usage_detected": self._detect_gpu_usage(source),

            "tensor_operations": tensor_operations,
            "model_operations": model_operations,

            "workload_profile": self._build_workload_profile(
                source=source,
                imports=imports,
                tensor_operations=tensor_operations,
                model_operations=model_operations,
            ),
        }

    @staticmethod
    def _get_call_name(node: ast.Call) -> str | None:
        """Extract a readable function or method name from a call."""

        if isinstance(node.func, ast.Name):
            return node.func.id

        if isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func

            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value

            if isinstance(current, ast.Name):
                parts.append(current.id)
                return ".".join(reversed(parts))

        return None

    @staticmethod
    def _detect_pytorch(imports: list[str]) -> bool:
        return any(
            module == "torch" or module.startswith("torch.")
            for module in imports
        )

    @staticmethod
    def _detect_tensorflow(imports: list[str]) -> bool:
        return any(
            module == "tensorflow" or module.startswith("tensorflow.")
            for module in imports
        )

    @staticmethod
    def _detect_frameworks(imports: list[str]) -> list[str]:
        frameworks = []

        if any(
            module == "torch" or module.startswith("torch.")
            for module in imports
        ):
            frameworks.append("PyTorch")

        if any(
            module == "tensorflow" or module.startswith("tensorflow.")
            for module in imports
        ):
            frameworks.append("TensorFlow")

        return frameworks

    @staticmethod
    def _detect_cuda(source: str) -> bool:
        source_lower = source.lower()
        return "cuda" in source_lower

    @staticmethod
    def _detect_rocm(source: str) -> bool:
        source_lower = source.lower()
        return "rocm" in source_lower

    @staticmethod
    def _detect_hip(source: str) -> bool:
        source_lower = source.lower()
        return "hip" in source_lower

    @staticmethod
    def _detect_gpu_usage(source: str) -> bool:
        source_lower = source.lower()

        gpu_indicators = [
            "cuda",
            "rocm",
            "hip",
            "gpu",
            "device=",
            "torch.cuda",
            "tensorflow.device",
        ]

        return any(
            indicator in source_lower
            for indicator in gpu_indicators
        )

    @staticmethod
    def _looks_like_tensor_operation(call_name: str) -> bool:
        tensor_keywords = [
            "tensor",
            "randn",
            "rand",
            "zeros",
            "ones",
            "matmul",
            "mm",
            "bmm",
            "einsum",
            "reshape",
            "view",
            "transpose",
            "permute",
            "cat",
            "stack",
        ]

        name_lower = call_name.lower()

        return any(
            keyword in name_lower
            for keyword in tensor_keywords
        )

    @staticmethod
    def _looks_like_model_operation(call_name: str) -> bool:
        model_keywords = [
            "model",
            "forward",
            "predict",
            "generate",
            "inference",
            "train",
            "eval",
        ]

        name_lower = call_name.lower()

        return any(
            keyword in name_lower
            for keyword in model_keywords
        )

    @staticmethod
    def _build_workload_profile(
        source: str,
        imports: list[str],
        tensor_operations: list[str],
        model_operations: list[str],
    ) -> dict:
        """Build a simple deterministic workload profile."""

        lines = len(source.splitlines())

        has_pytorch = any(
            module == "torch" or module.startswith("torch.")
            for module in imports
        )

        has_tensorflow = any(
            module == "tensorflow" or module.startswith("tensorflow.")
            for module in imports
        )

        if has_pytorch or has_tensorflow:
            framework_type = "AI/ML framework detected"
        else:
            framework_type = "No major AI/ML framework detected"

        if len(tensor_operations) >= 5:
            complexity = "high"
        elif len(tensor_operations) >= 2:
            complexity = "medium"
        else:
            complexity = "low"

        return {
            "framework_type": framework_type,
            "tensor_operation_count": len(tensor_operations),
            "model_operation_count": len(model_operations),
            "code_size": (
                "large"
                if lines >= 300
                else "medium"
                if lines >= 100
                else "small"
            ),
            "estimated_complexity": complexity,
        }

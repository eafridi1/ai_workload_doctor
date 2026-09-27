import ast
from pathlib import Path


class WorkloadAnalyzer:
    """
    Deterministic static analyzer for AI workloads.

    The analyzer reports observable source-code characteristics.
    It does not claim that a GPU was actually used at runtime.
    """

    def __init__(self, workload_path: str):
        self.workload_path = Path(workload_path)

    def analyze(self) -> dict:
        if not self.workload_path.exists():
            raise FileNotFoundError(
                f"Workload not found: {self.workload_path}"
            )

        if self.workload_path.suffix != ".py":
            raise ValueError(
                "Currently only Python workloads are supported."
            )

        source = self.workload_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imports = []
        functions = []
        classes = []

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

        source_lower = source.lower()

        frameworks = []

        if "torch" in imports or "torch." in source_lower:
            frameworks.append("PyTorch")

        if "tensorflow" in imports or "tensorflow." in source_lower:
            frameworks.append("TensorFlow")

        cuda_references = (
            "cuda" in source_lower
            or "torch.cuda" in source_lower
        )

        rocm_references = (
            "rocm" in source_lower
            or "hip" in source_lower
        )

        tensor_operations = any(
            operation in source_lower
            for operation in [
                "torch.tensor",
                "torch.randn",
                "torch.zeros",
                "torch.ones",
                "matmul",
                "torch.matmul",
                " @ ",
            ]
        )

        model_operations = any(
            operation in source_lower
            for operation in [
                "model(",
                "model.forward",
                "torch.nn",
                "nn.module",
                "transformers",
            ]
        )

        # Static source-code signal only.
        # This does NOT prove that a GPU was actually used.
        gpu_usage = (
            cuda_references
            or rocm_references
            or "device=" in source_lower
            or ".to(" in source_lower
            or ".cuda(" in source_lower
        )

        return {
            "workload": self.workload_path.name,
            "language": "Python",
            "lines_of_code": len(source.splitlines()),
            "imports": sorted(set(imports)),
            "functions": functions,
            "classes": classes,
            "frameworks": frameworks,
            "cuda_references": cuda_references,
            "rocm_references": rocm_references,
            "gpu_usage": gpu_usage,
            "tensor_operations": tensor_operations,
            "model_operations": model_operations,
        }

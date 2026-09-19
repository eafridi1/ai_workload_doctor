import torch


def create_tensor():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tensor = torch.randn(1000, 1000, device=device)
    return tensor


def run_workload():
    tensor = create_tensor()
    result = tensor @ tensor
    return result


if __name__ == "__main__":
    output = run_workload()
    print(output.shape)

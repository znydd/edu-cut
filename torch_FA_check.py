import torch
from flash_attn import flash_attn_func

# Example dimensions (adjust as needed, ensure compatibility with your hardware)
batch_size = 1
seq_len_q = 16
seq_len_kv = 16
num_heads = 2
head_dim = 64

# Create dummy tensors (ensure they are on the correct device, e.g., CUDA)
if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    print("CUDA is not available. FlashAttention primarily targets GPUs.")
    # Fallback or error, as flash_attn is GPU-accelerated
    exit()

q = torch.randn(
    batch_size,
    seq_len_q,
    num_heads,
    head_dim,
    dtype=torch.float16,
    device=device,
    requires_grad=True,
)
k = torch.randn(
    batch_size,
    seq_len_kv,
    num_heads,
    head_dim,
    dtype=torch.float16,
    device=device,
    requires_grad=True,
)
v = torch.randn(
    batch_size,
    seq_len_kv,
    num_heads,
    head_dim,
    dtype=torch.float16,
    device=device,
    requires_grad=True,
)

try:
    # Perform a forward pass
    out = flash_attn_func(q, k, v)
    print("FlashAttention forward pass successful. Output shape:", out.shape)

    # Optional: Perform a backward pass if you need to test gradients
    # out.backward(torch.ones_like(out))
    # print("FlashAttention backward pass successful.")

except Exception as e:
    print(f"An error occurred during FlashAttention operation: {e}")
    print(
        "Ensure that your input tensors have compatible shapes, dtypes (often float16 or bfloat16), and are on the CUDA device."
    )
    print(
        "Also, check if your GPU architecture is supported by the installed FlashAttention version."
    )

# print(torch.__config__.show())

import torch
import flash_attn
from dotenv import set_key, dotenv_values
from pathlib import Path


def ensure_torch_FA():
    # print("Flash Attention check: ")
    # print(flash_attn.__version__)
    # print("=======================================")
    # print()
    # print("Pyorch check: ")
    # print(torch.__config__.show())
    torch_version = torch.__version__
    fa_version = flash_attn.__version__
    if torch_version and fa_version:
        print(f"Torch version: {torch_version}")
        print(f"Flash Attention cversion: {fa_version}")


def ensure_app_root_env():
    env_path = Path(".env")

    if not env_path.exists():
        env_path.touch()
        print(".env file created.")

    env_vars = dotenv_values(".env")

    if "APP_ROOT" not in env_vars:
        root_path = str(Path(__file__).resolve().parent)
        set_key(str(env_path), "APP_ROOT", root_path)
        print(f"APP_ROOT set to {root_path}")
    else:
        print(f"APP_ROOT already exists: {env_vars['APP_ROOT']}")


# Call this early in your main.py or __init__.py
if __name__ == "__main__":
    ensure_app_root_env()
    ensure_torch_FA()

import os
from dataclasses import dataclass


def load_dotenv(path: str = ".env") -> None:
    """Load simple KEY=VALUE pairs from .env without overriding real env vars."""
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if key.startswith("export "):
                key = key[len("export "):].strip()

            if value and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]

            os.environ.setdefault(key, value)


@dataclass
class LLMConfig:
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.7


@dataclass
class EmailConfig:
    smtp_server: str
    smtp_port: int
    sender: str
    receiver: str
    sender_password: str


@dataclass
class CommonConfig:
    description: str
    num_workers: int = 4
    save: bool = False
    save_dir: str = "./history"
    profile_hash: str = ""
    state_dir: str = "./state"

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def load_env_file(env_path: Path) -> None:
    """Carrega um arquivo .env simples (KEY=VALUE) para os.environ.

    Mantém compatibilidade com a lógica anterior do projeto sem adicionar dependências.
    """

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_file: Path
    host: str
    port: int
    debug: bool
    openai_api_key: str | None


def load_settings(project_root: Path | None = None) -> Settings:
    root = project_root or Path(__file__).resolve().parent.parent

    # Carregar .env se existir
    load_env_file(root / ".env")

    host = os.getenv("FLASK_HOST", "0.0.0.0")

    # Em produção (ex.: AWS) é comum expor a porta via PORT.
    port_raw = os.getenv("FLASK_PORT") or os.getenv("PORT") or "5000"
    try:
        port = int(port_raw)
    except ValueError:
        port = 5000

    debug = os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "y"}

    data_file = root / os.getenv("EVICHAIN_DATA_FILE", "data/blockchain_data.json")

    openai_api_key = os.getenv("OPENAI_API_KEY")

    return Settings(
        project_root=root,
        data_file=data_file,
        host=host,
        port=port,
        debug=debug,
        openai_api_key=openai_api_key,
    )

import os
import uuid


def create_workspace_db_path(prefix: str) -> str:
    # Keep test DB files under repository with flat paths; avoid temp directories
    # that can trigger permission issues in restricted environments.
    root = os.path.join(os.getcwd(), "backend", "database")
    os.makedirs(root, exist_ok=True)
    return os.path.join(root, f"{prefix}{uuid.uuid4().hex}.db")


def remove_file_if_exists(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        # Best-effort cleanup; tests should not fail because tmp cleanup failed.
        pass

import importlib.resources as pkg_resources
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import fire


def main():
    fire.Fire(
        dict(
            build=build,
        )
    )


def build(name: str, *, poetry_dir: str = "."):
    poetry_path = Path(poetry_dir).resolve().absolute()
    with pkg_resources.open_text("remote", "Dockerfile") as f:
        dockerfile = f.read()
    with TemporaryDirectory() as d:
        temp_dir = Path(d)
        (temp_dir / "Dockerfile").write_text(dockerfile)
        pyproject_path = poetry_path / "pyproject.toml"
        poetry_lock_path = poetry_path / "poetry.lock"
        assert pyproject_path.exists(), f"{pyproject_path} does not exist"
        assert poetry_lock_path.exists(), f"{poetry_lock_path} does not exist"
        (temp_dir / "pyproject.toml").write_text(pyproject_path.read_text())
        (temp_dir / "poetry.lock").write_text(poetry_lock_path.read_text())
        subprocess.run(
            ["docker", "build", "-t", name, "."],
            cwd=temp_dir,
        )

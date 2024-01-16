import importlib.resources as pkg_resources
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import fire
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

DATA_DIR = "/root/data"


def main():
    fire.Fire(
        dict(
            build=run_build,
            rsync=run_rsync,
            ssh=run_ssh,
            run=run_command,
        )
    )


def run_build(name: str, *, poetry_dir: str = "."):
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
        subprocess.run(
            ["docker", "push", name],
            cwd=temp_dir,
        )


def run_rsync(*, continuous: bool = False) -> None:
    instance = _get_instance()

    if not continuous:
        _run_rsync(instance)
        return

    observer = Observer()
    observer.schedule(
        event_handler=_RsyncEventHandler(instance),
        path=".",
        recursive=True,
    )
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def run_ssh(
    port_forward: int | None = None,
) -> None:
    instance = _get_instance()
    _run_ssh(instance, [], port_forward=port_forward)


def run_command(
    command: str,
    *,
    port_forward: int | None = None,
    tmux: str | None = None,
) -> None:
    print(repr(command))
    if tmux is None:
        command = f"cd {DATA_DIR} && {command}"
    else:
        command = (
            f"tmux new-session -s {tmux} bash -c "
            f'"cd {DATA_DIR} && {command} ; echo Press enter to exit ; read"'
        )
    _run_ssh(
        _get_instance(),
        [command],
        port_forward=port_forward,
    )


def _run_ssh(
    instance: "_Instance",
    commands: list[str],
    port_forward: int | None,
) -> None:
    ssh_args = [
        "ssh",
        f"root@{instance.ip}",
        "-t",
        "-p",
        str(instance.port),
    ]
    if port_forward is not None:
        ssh_args.extend(["-L", f"{port_forward}:localhost:{port_forward}"])
    ssh_args.extend(commands)
    os.execv("/usr/bin/ssh", ssh_args)


def _run_rsync(instance: "_Instance") -> None:
    subprocess.check_call(
        [
            "rsync",
            "-r",
            "-e",
            f"ssh -p {instance.port}",
            "--filter=:- .gitignore",
            "--filter=- .git",
            ".",
            f"root@{instance.ip}:{DATA_DIR}",
        ]
    )
    if (Path.cwd() / ".env").exists():
        subprocess.check_call(
            [
                "rsync",
                "-r",
                "-e",
                f"ssh -p {instance.port}",
                ".env",
                f"root@{instance.ip}:{DATA_DIR}/.env",
            ]
        )


@dataclass(frozen=True)
class _RsyncEventHandler(FileSystemEventHandler):
    instance: "_Instance"

    def on_any_event(self, event: FileSystemEvent):
        print("Files changed, running rsync")
        _run_rsync(self.instance)


@dataclass(frozen=True)
class _Instance:
    ip: str
    port: int


def _get_instance() -> _Instance:
    output = subprocess.check_output(
        ["poetry", "run", "vastai", "show", "instances", "--raw"],
    )
    output_json = json.loads(output.decode())
    assert len(output_json) == 1, f"Expected exactly one instance, found {output_json}"
    return _Instance(
        ip=output_json[0]["ssh_host"],
        port=output_json[0]["ssh_port"],
    )

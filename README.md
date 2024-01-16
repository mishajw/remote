# remote

Utilities for running Python code on remote instances.

## Features
- `remote build $NAME`: Builds a Docker image with CUDA installed, and all of the current directory's Python dependencies. Must be run from a Poetry package.
- `remote rsync`: Syncs the local files up to a vast.ai instance. Doesn't sync files in `.gitignore`, apart from `.env`.
- `remote rsync --continuous`: Syncs files every time a file change is detected in the current directory.
- `remote ssh`: SSHs into a vast.ai instance.
- `remote run '<command>'`: Runs a command on the vast.ai instance.

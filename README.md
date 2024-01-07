# remote

Utilities for running Python code on remote instances.

## Features
- `remote build $NAME`: Builds a Docker image with CUDA installed, and all of the current directory's Python dependencies. Must be run from a Poetry package.
- `remote rsync`: Syncs the local files up to a vast.ai instance. Doesn't sync files in `.gitignore`, apart from `.env`.
- `remote ssh`: SSHs into a vast.ai instance.

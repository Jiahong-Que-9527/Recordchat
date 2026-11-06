# [房玄龄·2026-11-03] source ops/env.sh inside WSL Ubuntu.
export PATH="/home/bill/.local/opt/node-v22.23.4-linux-x64/bin:$HOME/.local/bin:$PATH"
export DOCKER_HOST=unix:///run/recordchat-docker.sock
alias docker=recordchat-docker

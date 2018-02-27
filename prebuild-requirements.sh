#!/usr/bin/env sh
set -e

docker build -f Dockerfile-requirements -t antonkir/snailshell_control_panel_requirements:latest .
docker push antonkir/snailshell_control_panel_requirements:latest

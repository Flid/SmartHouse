#!/usr/bin/env sh
set -e

celery worker -A snailshell_cp.tasks -Q snailshell_cp_main -n celery-worker-1@%h -c1

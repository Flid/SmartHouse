#!/bin/bash
set -e

docker run -d -p 9000:9000 --restart always --name 'portainer_controller' -v /var/run/docker.sock:/var/run/docker.sock -v /opt/portainer:/data portainer/portainer


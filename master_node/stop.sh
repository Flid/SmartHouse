#!/bin/bash
set -e

RUNNING_ID=`docker ps --filter "name=portainer_controller" --format "{{.ID}}"`

if [ -z "$RUNNING_ID" ]
then
      echo "Not running"
else
      docker stop $RUNNING_ID > /dev/null
      docker rm $RUNNING_ID > /dev/null
      echo "Stopped and removed"
fi

#!/bin/bash
set -e

apt update
apt install lxc aufs-tools cgroup-lite apparmor docker.io curl python3

./stop.sh
rm -rf /opt/portainer/
./run.sh
sleep 2

echo "Seting up admin"
curl -XPOST http://localhost:9000/api/users/admin/init -H "Content-Type: application/json" -d "{\"Username\": \"admin\", \"Password\": \"$PORTAINER_ADMIN_PASSWORD\"}" --fail

echo "Authenticating"
AUTH_TOKEN=`curl -XPOST http://localhost:9000/api/auth -H "Content-Type: application/json" -d "{\"Username\": \"admin\", \"Password\": \"$PORTAINER_ADMIN_PASSWORD\"}" --fail 2>/dev/null | python3 -c "import sys, json; data=sys.stdin.read(); print(json.loads(data)['jwt'])"`

# Create an initial endpoint, ID=1
curl -XPOST http://localhost:9000/api/endpoints -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" -d '{"Name": "local", "URL": "unix:///var/run/docker.sock"}' --fail

echo "Portainer successfully setup, serving on port 9000"

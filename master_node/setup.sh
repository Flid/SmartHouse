#!/bin/bash
set -e

./stop.sh
rm -rf /opt/portainer/
./run.sh
sleep 1


echo "Seting up admin"
curl -XPOST http://localhost:9000/api/users/admin/init -H "Content-Type: application/json" -d "{\"Username\": \"admin\", \"Password\": \"$ADMIN_PASSWORD\"}" --fail
echo "$ADMIN_PASSWORD" > /opt/portainer/admin_password
chown root:root /opt/portainer/admin_password
chmod 0600 /opt/portainer/admin_password

echo "Authenticating"
AUTH_TOKEN=`./authenticate.sh`

# Create an initial endpoint, ID=1
curl -XPOST http://localhost:9000/api/endpoints -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" -d '{"Name": "local", "URL": "unix:///var/run/docker.sock"}' --fail

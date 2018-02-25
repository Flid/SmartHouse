#!/bin/bash
set -e

ADMIN_PASSWORD=`cat /opt/portainer/admin_password`
curl -XPOST http://localhost:9000/api/auth -H "Content-Type: application/json" -d "{\"Username\": \"admin\", \"Password\": \"$ADMIN_PASSWORD\"}" --fail 2>/dev/null | python -c "import sys, json; data=sys.stdin.read(); print(json.loads(data)['jwt'])"

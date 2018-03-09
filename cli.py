#!/usr/bin/env python3

import json

from snailshell_cp.clients.portainer import PortainerClient

client = PortainerClient('http://flid.ddns.net:10000')
client.authenticate('snailshell', 'snailshellpass')

print(json.dumps(client.get_container_info(1, 'ss_control_panel'), indent=2))

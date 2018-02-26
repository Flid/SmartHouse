SnailShell is an open platform for IoT - easy to set up and add new devices.

## Architecture
There's one master node, a heart of the system. This node has some general infrastructure services:
* Portainer to manage Docker containers in the system.
* Deployer - an external API, working on top of Portainer API to automate deploy process for the parts of the system.
* ZooKeeper - store the configuration of the system, topology and deploy rules.
* Kafka server - the heart of event-driven platform.
* Multiple nodes - workers doing some useful work.

NOTES: even though it's quite easy to do a multi-master setup for
 improved reliability and fault-tolerance - it's not required at the moment.

Sets up a Portainer (Docker control panel), deployer script (gives an interface to pull and start containers)

## Installation

* Set up master controller node:
```
export PORTAINER_ADMIN_PASSWORD=<megapassword>
sudo -E ./setup.sh
```

SnailShell is an open platform for IoT - easy to set up and add new devices.

## Architecture
There's one master node, a heart of the system. This node has some general infrastructure services:
* Portainer to manage Docker containers in the system.
* Control Panel - an external API, working on top of Portainer API to automate deploy process for the parts of the system.
* Postgres DB - a shared DB to store all the data needed, including some configs.
* RabbitMQ - the heart of event-driven platform.
* Multiple nodes - workers doing some useful work.

NOTES: even though it's quite easy to do a multi-master setup for
 improved reliability and fault-tolerance - it's not required at the moment.

Sets up a Portainer (Docker control panel), deployer script (gives an interface to pull and start containers)

## Installation

* Set up master controller node:
```
cp setenv-example setenv-mynode
```

Edit the new file. The first section has some parameters you need to overwrite,
other sections can be left as is.

Now install the requirements locally (you might want to use virtualenv)
and provision the master node. Define one host to ssh to,
user needs to have root access.

```
pip install -r requirements.txt

fab provision_master_node --hosts 'root@192.168.0.10:22'
```

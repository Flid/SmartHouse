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


## How master provisioning works

You pick one machine to be Master, it will have [Portainer](https://github.com/portainer/portainer),
PostgreSQL, RabbitMQ and Control Panel on it.

You need a machine with Ubuntu. Tested on 16.04.

The steps provisioning performs:
* Connect to `root@$MASTER_HOST:26` via SSH.
* Install some Ubuntu packages, including Docker
* Stop and delete all existing containers/images/volumes, if any.
* Install and configure Portainer.
Admin login is `$PORTAINER_ADMIN_USER`, password is `$PORTAINER_ADMIN_PASSWORD`.
* Setting up PostgreSQL
* Setting up RabbitMQ with management console. You can find it on `http://$MASTER_HOST:$RABBITMQ_MANAGEMENT_PORT`.
Login is `$RABBITMQ_USER`, password is `$RABBITMQ_PASSWORD`
* Setting up Control Panel - django admin panel to control nodes,
which also has an API to automate deploys. It starts on `$MASTER_HOST:$CONTROL_PANEL_PORT`.
Admin login is `$CONTROL_PANEL_ADMIN_USER`, password is `$CONTROL_PANEL_ADMIN_PASSWORD`

## Installation

Set up master controller node:
```
cp setenv-example setenv-mynode
```

Edit the new file. The first section has some parameters you need to overwrite,
other sections can be left as is.

Now install the requirements locally (you might want to use virtualenv)
and provision the master node. Define one host to ssh to,
user needs to have root access.

```
. ./setenv-mynode
pip install -r requirements.txt

fab provision_master_node -H root@$MASTER_HOST:22
```

The process will finish in a few minutes.


## How to contribute

First of all, don't forget to install some lovely useful tools:

```
pip install -r requirements-test.txt

pre-commit install
```

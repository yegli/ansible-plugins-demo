# Lab 1: Inventory plugin (Docker containers as hosts)

> Stop maintaining `hosts.ini` by hand. Ask the platform what exists.

This lab uses the inventory plugin `community.docker.docker_containers` to build the
inventory from whatever runs on your local Docker daemon.
Container labels `role` / `env` become groups `role_*` / `env_*`.

## What you'll learn

- How an inventory can be **generated** instead of written
- Labels -> groups (`keyed_groups`), conditions -> groups (`groups`), extra host variables (`compose`)
- How Ansible connects to containers via `docker exec`, no SSH at all
- That the inventory **follows reality**: stop a container and it changes group

## Files

```
01-inventory-plugin/
├── ansible.cfg             # points at the inventory file
├── compose.yml             # the "fleet": 5 python:alpine containers with labels
├── containers.docker.yml   # inventory plugin config (the interesting file)
└── ping.yml                # proves Ansible can reach every host
```

## Steps

Start in the **repository root**, then change into this lab's folder. All commands below are run from there:

```bash
cd 01-inventory-plugin
```

### 1. Start the fleet

```bash
docker compose up -d
docker ps --filter label=demo=inventory --format 'table {{.Names}}\t{{.Label "role"}}\t{{.Label "env"}}\t{{.Status}}'
```

Expected:

```
NAMES     role      env       STATUS
web1      web       prod      Up 3 seconds
web2      web       prod      Up 3 seconds
app1      app       prod      Up 3 seconds
db1       db        prod      Up 3 seconds
cache1    cache     dev       Up 3 seconds
```

### 2. Read the plugin config

```bash
cat containers.docker.yml
```

Look for:

- `plugin:` which inventory plugin parses this file
- `filters:` only our labelled containers, ignore everything else on your machine
- `keyed_groups:` one group per label value
- `groups:` groups based on a condition (running / stopped)
- `compose:` new host variables computed from `docker inspect` data

### 3. Let the plugin build the inventory

```bash
ansible-inventory --graph
```

Expected (abridged):

```
@all:
  |--@role_web:
  |  |--web1
  |  |--web2
  |--@role_db:
  |  |--db1
  |--@env_prod:
  ...
```

### 4. Inspect one host

Every variable below comes from `docker inspect`, nobody typed it:

```bash
ansible-inventory --host web1 | head -30
ansible-inventory --host web1 | grep -E 'container_(image|ip)'
```

### 5. Use the inventory

```bash
ansible-playbook ping.yml
ansible role_web -m ping
ansible env_dev -m ansible.builtin.command -a 'cat /etc/os-release'
```

### 6. Watch the inventory follow reality

```bash
docker stop db1
ansible-inventory --graph stopped
docker start db1
ansible-inventory --graph running
```

## Key takeaways

- Inventory plugins replace the old "dynamic inventory scripts" (an executable that prints JSON).
- The same pattern exists for AWS (`amazon.aws.aws_ec2`), Azure, VMware, NetBox, Kubernetes and more.
- The filename must end in `docker.yml` / `docker.yaml`, that is how the plugin recognises its file.
- `ansible-inventory` is the debugging tool for every inventory: `--graph`, `--host`, `--list`.

## Troubleshooting

- `connection_type: docker-cli` is set on purpose: the default `docker-api` can crash workers on macOS
  ("A worker was found in a dead state").
- The local `ansible.cfg` sets the inventory, so `-i containers.docker.yml` is optional here.
- The plugin needs the Python package `requests` in Ansible's Python environment.
- Linux: `permission denied` on `/var/run/docker.sock` means your user is not in the `docker` group.

## Cleanup

Continuing with **lab 4** later? Keep the containers running, just go back to the repository root:

```bash
cd ..
```

Done with Docker for now? Stop the containers, then go back to the repository root:

```bash
docker compose down
cd ..
```

# Ansible Plugin Demos

Hands-on examples that show **how to extend Ansible with your own Python plugins**.
Four short labs, each self-contained, all running locally from the command line in a few seconds.

| # | Lab | Plugin type | Runs where | What it does |
|---|-----|-------------|------------|--------------|
| 1 | [`01-inventory-plugin`](01-inventory-plugin/) | inventory | controller | Docker containers become Ansible hosts, labels become groups |
| 2 | [`02-filter-plugin`](02-filter-plugin/) | filter | controller | `{{ size \| human_bytes }}`, `{{ pw \| mask }}`, `{{ name \| slugify }}` |
| 3 | [`03-lookup-plugin`](03-lookup-plugin/) | lookup | controller | `{{ lookup('dotenv', 'DB_HOST') }}` reads a `.env` file |
| 4 | [`04-action-plugin`](04-action-plugin/) | action | controller **+** target | `preflight:` checks each host before deploying, writes a report locally |

## The big picture

```
            CONTROLLER (your machine)                          TARGETS (containers)
 ┌───────────────────────────────────────────┐
 │ inventory plugin  -> which hosts exist?   │
 │ lookup plugin     -> fetch data           │
 │ filter plugin     -> transform data       │
 │ action plugin     -> orchestrate a task ──┼── runs modules ──>  web1 web2 app1 db1 cache1
 └───────────────────────────────────────────┘
```

The one thing to remember: **all plugins run on the controller.** Only *modules* run on the targets.

## Where Ansible finds your plugins

No install, no packaging. Put a `.py` file into the right folder next to your playbook:

| Plugin type | Folder | ansible.cfg key | Required class name |
|-------------|--------|-----------------|---------------------|
| inventory | `inventory_plugins/` (or a collection) | `[inventory] enable_plugins` | `InventoryModule` |
| filter | `filter_plugins/` | `filter_plugins` | `FilterModule` |
| lookup | `lookup_plugins/` | `lookup_plugins` | `LookupModule` |
| action | `action_plugins/` | `action_plugins` | `ActionModule` |

When your plugins grow up, the same files move into a collection: `plugins/filter/`, `plugins/lookup/`, `plugins/action/`, ...

## Requirements

- **Ansible** (ansible-core 2.18 or newer), for example `pipx install --include-deps ansible` or `brew install ansible`
- **Docker** (Docker Desktop on macOS/Windows, Docker Engine on Linux), only needed for labs 1 and 4
- The **`community.docker`** collection, included in the full `ansible` package, otherwise:

```bash
ansible-galaxy collection install community.docker
```

Check your setup:

```bash
ansible --version
ansible-galaxy collection list | grep community.docker
docker info --format '{{.ServerVersion}}'
```

Tested on macOS with ansible-core 2.21, community.docker 5.2 and Docker Desktop.
Linux works the same (your user needs access to the Docker socket, for example via the `docker` group).

## Getting started

```bash
git clone <this-repo-url>
cd <repo-folder>                # you are now in the repository root
```

Work through the labs in order:

1. **Inventory**: starts the containers that lab 4 needs again
2. **Filter**: the simplest plugin type, about 10 lines of Python
3. **Lookup**: same idea, but *fetches* data instead of transforming it
4. **Action**: the most powerful one, controller logic plus remote modules

Every lab follows the same flow:

1. **Start in the repository root**
2. `cd` into the lab folder (first command of each lab)
3. Run the steps
4. `cd ..` back to the repository root (last command of each lab, under *Cleanup*)

This matters because each lab has its own `ansible.cfg` and Ansible only reads it from the **current directory**.

## Cleanup

From the repository root:

```bash
(cd 01-inventory-plugin && docker compose down)
rm -rf 04-action-plugin/reports /tmp/acme-shop.conf
```

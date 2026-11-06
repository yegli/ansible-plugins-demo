# Lab 4: Action plugin (`preflight`, check hosts before deploying)

> A module only sees the target. An action plugin sees **everything**: the controller, the target and the result.

`preflight` is a new task you can use in any playbook. Before deploying, it checks every host
for enough memory, enough CPUs and a recent Python, then writes a report file **on the controller**:

```yaml
- preflight:
    min_memory_mb: 2048
    min_cpus: 2
    min_python: "3.10"
    report_dir: reports
```

## What you'll learn

- An action plugin runs **on the controller** and can **call modules on the target**
- How to combine both worlds: remote facts + a local decision + a local file
- That failing hosts drop out of the play while healthy hosts continue to deploy
- How to set per-group thresholds with `group_vars` (databases need more RAM)
- That the same plugin works as a playbook task **and** as an ad-hoc `-m preflight`

## Prerequisite

The Docker containers from lab 1 must be running, this lab reuses its inventory.
From the repository root:

```bash
(cd 01-inventory-plugin && docker compose up -d)
```

## Files

```
04-action-plugin/
├── ansible.cfg                  # inventory = lab 1, action_plugins = ./action_plugins
├── action_plugins/
│   └── preflight.py             # the plugin
├── group_vars/
│   └── role_db.yml              # min_memory_mb: 65536 -> db1 is meant to FAIL
├── playbook.yml                 # preflight -> show result -> deploy
└── reports/                     # created by the plugin, on the controller
```

## How it works

```
 ansible-playbook  (controller)                              container (target)
 ┌──────────────────────────────────────────────────┐
 │ ActionModule.run()                               │
 │   1. self._execute_module("ansible.builtin.setup") ──────>  runs setup, returns facts
 │   2. compare facts with min_* args   <───────────────────── memtotal_mb, vcpus, python
 │   3. write reports/<host>.txt  (on the controller!)│
 │   4. return ok / failed                          │
 └──────────────────────────────────────────────────┘
```

```python
class ActionModule(ActionBase):                     # Ansible looks for exactly this class name
    _VALID_ARGS = frozenset(("min_memory_mb", "min_cpus", "min_python", "report_dir"))

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        setup = self._execute_module(module_name="ansible.builtin.setup", ...)   # on the target
        ...                                                                      # on the controller
        result["failed"] = bool(failed)
        return result
```

The **file name** (`preflight.py`) **is the task name**.

## Steps

Start in the **repository root**, then change into this lab's folder. All commands below are run from there:

```bash
cd 04-action-plugin
```

### 1. Read the plugin

```bash
cat action_plugins/preflight.py
cat group_vars/role_db.yml
```

### 2. Run the playbook

```bash
ansible-playbook playbook.yml
```

Expected (abridged):

```
TASK [Preflight checks (runs on the controller, talks to each container)] ***
ok: [web1]
ok: [web2]
ok: [app1]
ok: [cache1]
fatal: [db1]: FAILED! => {"checks": [{"actual": 23995, "check": "memory_mb", "ok": false, "required": 65536}, ...],
                          "msg": "preflight FAILED: memory_mb"}

TASK [Show what the plugin returned] ***
    "msg": "preflight passed, report: reports/web1.txt"

TASK [Deploy (only reached by hosts that passed preflight)] ***
changed: [web1]   ...   (no db1!)

PLAY RECAP ***
db1     : ok=0    changed=0    unreachable=0    failed=1
web1    : ok=3    changed=1    unreachable=0    failed=0
```

Your `actual` numbers will differ: containers see the memory and CPUs of your machine
(or of the Docker Desktop VM).

### 3. The reports were written on the controller, not in the containers

```bash
ls reports/
cat reports/db1.txt
cat reports/web1.txt
```

Expected:

```
Preflight report for db1  (2026-11-06 09:15:02)
  [FAIL] memory_mb  required >= 65536    actual = 23995
  [PASS] cpus       required >= 2        actual = 12
  [PASS] python     required >= 3.10     actual = 3.13.18
```

### 4. The deploy happened, but only on the healthy hosts

```bash
docker exec web1 cat /tmp/release.txt
docker exec db1 cat /tmp/release.txt          # -> cat: can't open '/tmp/release.txt': No such file or directory
```

### 5. Change the rules from the command line

```bash
# Lower the bar: extra vars (-e) beat group_vars, so now db1 passes too
ansible-playbook playbook.yml -e min_memory_mb=512

# Raise the bar: require a newer Python than the containers have, every host fails
ansible-playbook playbook.yml -e min_python=3.99 --limit role_web
```

### 6. Use the action plugin ad-hoc

```bash
ansible role_web -m preflight -a 'min_cpus=64'
ansible role_app -m preflight -a 'min_memory_mb=1024' -vvv | grep 'preflight:'
```

### 7. Typos are caught

```bash
ansible web1 -m preflight -a 'min_ram=1024'
```

Expected:

```
[ERROR]: Task failed: Invalid options for preflight: min_ram
```

That check comes for free from `_VALID_ARGS` in the plugin.

## Key takeaways

- **Module vs. action plugin:** a module is copied to the target and executed there.
  An action plugin runs on the controller and *decides* what gets executed where.
- Every task has an action plugin. Most tasks use the generic `normal` action, which simply runs the module.
  `template`, `copy`, `fetch`, `debug`, `assert` and `include_tasks` are custom action plugins.
- A common pattern in collections: `plugins/action/foo.py` + `plugins/modules/foo.py` with the same name.
  The action does the controller work (render, upload, validate), the module does the target work.
- `self._execute_module()` runs any module on the target. `self._loader` and `self._templar` give you
  files and templating on the controller.
- Return `failed`, `changed` and `msg` in the result dict, Ansible treats it exactly like a module result.

## Cleanup

Remove the reports, stop the lab 1 containers and go back to the repository root:

```bash
rm -rf reports
(cd ../01-inventory-plugin && docker compose down)
cd ..
```

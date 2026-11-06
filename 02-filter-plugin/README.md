# Lab 2: Filter plugin (`human_bytes`, `mask`, `slugify`)

> Jinja has around 50 built-in filters. When none fits, write your own in 10 lines of Python.

A filter transforms a value inside `{{ }}`: `{{ value | my_filter(arg) }}`.
This lab adds three filters that almost every ops team ends up needing:

| Filter | Input | Output |
|--------|-------|--------|
| `human_bytes` | `53687091200` | `50.0 GiB` |
| `mask` | `Sup3r-S3cret-Web!` | `*************Web!` |
| `slugify` | `App Server (EU) 01` | `app-server-eu-01` |

## What you'll learn

- A filter plugin is **just a Python function**, registered in a `FilterModule` class
- Ansible picks it up automatically from `filter_plugins/`, nothing to install
- Filters take arguments, chain with built-in filters and can fail with clean error messages
- They work in playbooks **and** in ad-hoc commands

## Files

```
02-filter-plugin/
├── ansible.cfg              # filter_plugins = ./filter_plugins (needed for ad-hoc commands)
├── filter_plugins/
│   └── acme.py              # the plugin: 3 functions + FilterModule
├── servers.yml              # sample data, like an export from a CMDB
└── playbook.yml             # before/after comparison + tests
```

## How it works

```python
def human_bytes(value, precision=1):      # value = left side of the pipe
    ...                                   # precision = argument in ( )

class FilterModule:                       # Ansible looks for exactly this class name
    def filters(self):
        return {"human_bytes": human_bytes, "mask": mask, "slugify": slugify}
```

The file name (`acme.py`) does not matter, the keys of the returned dict are the filter names.

## Steps

No Docker needed for this lab. Start in the **repository root**, then change into this lab's folder. All commands below are run from there:

```bash
cd 02-filter-plugin
```

### 1. Read the plugin

```bash
cat filter_plugins/acme.py
```

### 2. Try the filters directly on the command line

```bash
ansible localhost -m debug -a "msg={{ 1073741824 | human_bytes }}"
ansible localhost -m debug -a "msg={{ 'Hello World, Welcome!' | slugify }}"
ansible localhost -m debug -a "msg={{ 'my-api-token-123456' | mask(visible=6) }}"
```

Expected:

```
localhost | SUCCESS => {
    "msg": "1.0 GiB"
}
localhost | SUCCESS => {
    "msg": "hello-world-welcome"
}
localhost | SUCCESS => {
    "msg": "*************123456"
}
```

### 3. Run the playbook: raw data vs. filtered data

```bash
cat servers.yml
ansible-playbook playbook.yml
```

Expected (abridged):

```
TASK [Without filters (raw data, hard to read, leaks secrets)] ***
    "msg": "Web Frontend 01 | disk=53687091200 | pw=Sup3r-S3cret-Web!"

TASK [With our filters (human_bytes, mask, slugify)] ***
    "msg": "web-frontend-01 | disk=50.0 GiB | pw=*************Web!"

TASK [Filters take arguments and chain with built-in filters] ***
        "1.24 TiB total disk",
        "web-frontend-01, app-server-eu-01, postgres-primary",
        "#################56"
```

### 4. Bad input gives a clean error

```bash
ansible localhost -m debug -a "msg={{ 'lots' | human_bytes }}"
```

Expected:

```
[ERROR]: ... The filter plugin 'human_bytes' failed: human_bytes expects a number, got 'lots'
```

That readable message comes from raising `AnsibleFilterError` in the plugin.

### 5. Your turn: add a fourth filter

Add this function to `filter_plugins/acme.py`:

```python
def shout(value):
    return str(value).upper() + "!"
```

Register it inside `filters()` by adding `"shout": shout,` to the dict, then run:

```bash
ansible localhost -m debug -a "msg={{ 'ansible is fun' | shout }}"
```

## Key takeaways

- Filters run **on the controller** while templating, never on the target.
- Use filters to *transform* data you already have. To *fetch* data, use a lookup (lab 3).
- Raise `AnsibleFilterError` for bad input, so users see a message instead of a Python traceback.
- Check whether a filter already exists before writing one: `ansible-doc -t filter -l | grep -i <word>`
- Inside a collection, the file moves to `plugins/filter/acme.py` and is called as `my_namespace.my_collection.human_bytes`.

## Cleanup

Nothing to clean up, this lab only prints output. Go back to the repository root:

```bash
cd ..
```

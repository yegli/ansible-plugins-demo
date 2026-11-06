# Lab 3: Lookup plugin (`dotenv`, read values from a `.env` file)

> The developers keep their settings in a `.env` file. Don't copy them into Ansible variables, *look them up*.

A lookup **fetches data from outside Ansible** (files, APIs, vaults, DNS ...) and always runs on the controller.
This lab adds a `dotenv` lookup:

```yaml
"{{ lookup('dotenv', 'DB_HOST') }}"                    # -> db1.acme.internal
"{{ lookup('dotenv', 'DB_HOST', file='prod.env') }}"   # -> use1-db-pg-01.acme.internal
"{{ lookup('dotenv', 'REDIS_URL', default='none') }}"  # -> none
```

## What you'll learn

- A lookup is a `LookupModule` class with one method: `run(terms, variables, **kwargs)`
- The difference between `lookup()` (comma-joined string) and `query()` (real list)
- How keyword arguments (`file=`, `default=`) and error handling work
- How to reuse Ansible's file search path (the `files/` folder) with `find_file_in_search_path`
- How to print debug output that only shows up with `-vvv`

## Files

```
03-lookup-plugin/
├── ansible.cfg              # lookup_plugins = ./lookup_plugins (needed for ad-hoc commands)
├── lookup_plugins/
│   └── dotenv.py            # the plugin
├── files/
│   ├── app.env              # default file (staging values)
│   └── prod.env             # second file, selected with file='prod.env'
└── playbook.yml
```

## How it works

```python
class LookupModule(LookupBase):                          # Ansible looks for exactly this class name
    def run(self, terms, variables=None, file="app.env", default=None, **kwargs):
        path = self.find_file_in_search_path(variables, "files", file)
        ...                                              # parse KEY=VALUE lines
        return [env[term] for term in terms]             # ALWAYS return a list
```

- `terms` are the positional arguments: `lookup('dotenv', 'A', 'B')` -> `['A', 'B']`
- keyword arguments arrive as normal Python keyword arguments
- the **file name** (`dotenv.py`) **is the lookup name**

## Steps

No Docker needed for this lab. Start in the **repository root**, then change into this lab's folder. All commands below are run from there:

```bash
cd 03-lookup-plugin
```

### 1. Read the data and the plugin

```bash
cat files/app.env
cat lookup_plugins/dotenv.py
```

### 2. Try the lookup on the command line

```bash
ansible localhost -m debug -a "msg={{ lookup('dotenv', 'APP_ENV') }}"
ansible localhost -m debug -a "msg={{ lookup('dotenv', 'APP_ENV', file='prod.env') }}"
ansible localhost -m debug -a "msg={{ query('dotenv', 'DB_HOST', 'DB_PORT') }}"
```

Expected:

```
localhost | SUCCESS => {
    "msg": "staging"
}
localhost | SUCCESS => {
    "msg": "production"
}
localhost | SUCCESS => {
    "msg": [
        "db1.acme.internal",
        "5432"
    ]
}
```

### 3. Run the playbook

```bash
ansible-playbook playbook.yml
```

Expected (abridged):

```
TASK [Single value] ***
    "msg": "App acme-shop talks to db1.acme.internal"

TASK [lookup() returns a comma-joined string, query() returns a list] ***
        "lookup": "db1.acme.internal,5432,shop",
        "query": ["db1.acme.internal", "5432", "shop"]

TASK [Keyword arguments, default value and a different file] ***
        "missing_key": "redis://localhost:6379",
        "prod_db": "use1-db-pg-01.acme.internal",
        "prod_key": "*************5b4a"

TASK [Real use, render a config file from the .env values] ***
changed: [localhost]
```

### 4. Look at the result: a config file built from `.env` values

```bash
cat /tmp/acme-shop.conf
```

### 5. Change the source and rerun

```bash
sed -i.bak 's/^DB_HOST=.*/DB_HOST=db2.acme.internal/' files/app.env
ansible-playbook playbook.yml --diff
mv files/app.env.bak files/app.env          # restore the original
```

`--diff` shows exactly which line of the generated config changed:

```
-host = db1.acme.internal
+host = db2.acme.internal
```

### 6. Errors and debugging

```bash
ansible localhost -m debug -a "msg={{ lookup('dotenv', 'NOPE') }}"
ansible localhost -m debug -a "msg={{ lookup('dotenv', 'APP_ENV', file='missing.env') }}"
ansible localhost -m debug -a "msg={{ lookup('dotenv', 'APP_ENV') }}" -vvv | grep dotenv
```

Expected:

```
[ERROR]: ... The lookup plugin 'dotenv' failed: dotenv: 'NOPE' not found in .../files/app.env
[ERROR]: ... The lookup plugin 'dotenv' failed: dotenv: could not find 'missing.env'
dotenv: reading .../03-lookup-plugin/files/app.env
```

## Key takeaways

- Lookups run **on the controller**, even when the play targets hundreds of remote hosts.
  The `.env` file never has to exist on the targets.
- Lookups are **lazy**: a variable like `db_host: "{{ lookup(...) }}"` is evaluated again every time it is used.
  For expensive lookups, store the result once with `set_fact`.
- `lookup()` returns a string (joined with `,`), `query()` / `q()` returns a list. Use `query()` in `loop:`.
- Filter vs. lookup: a filter **transforms** a value you have, a lookup **fetches** a value you don't have yet.
- Built-in and collection lookups you'll see in real projects: `file`, `env`, `password`,
  `community.hashi_vault.hashi_vault`, `amazon.aws.aws_secret`. List them all with `ansible-doc -t lookup -l`.

## Cleanup

Remove the generated config file and go back to the repository root:

```bash
rm -f /tmp/acme-shop.conf
cd ..
```

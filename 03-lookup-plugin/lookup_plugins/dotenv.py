"""dotenv lookup: read values from a .env file on the CONTROLLER.

Usage:
  {{ lookup('dotenv', 'DB_HOST') }}                         -> "db1.acme.internal"
  {{ lookup('dotenv', 'DB_HOST', 'DB_PORT') }}              -> "db1.acme.internal,5432"
  {{ query('dotenv', 'DB_HOST', 'DB_PORT') }}               -> ["db1.acme.internal", "5432"]
  {{ lookup('dotenv', 'NOPE', default='fallback') }}        -> "fallback"
  {{ lookup('dotenv', 'API_KEY', file='prod.env') }}        -> value from files/prod.env

Ansible auto-loads every *.py in a `lookup_plugins/` folder next to the playbook
(or the folders listed under `lookup_plugins =` in ansible.cfg).
The contract: a class named `LookupModule` with a `run(terms, variables, **kwargs)`
method that ALWAYS returns a list.
"""
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, file="app.env", default=None, **kwargs):
        # Searches the usual places: ./files/, role files/, playbook dir ...
        path = self.find_file_in_search_path(variables, "files", file)
        if path is None:
            raise AnsibleError(f"dotenv: could not find '{file}'")
        display.vvv(f"dotenv: reading {path}")  # visible with -vvv

        env = {}
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip("'\"")

        values = []
        for term in terms:
            if term in env:
                values.append(env[term])
            elif default is not None:
                values.append(default)
            else:
                raise AnsibleError(f"dotenv: '{term}' not found in {path}")
        return values

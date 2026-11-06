"""Acme Corp custom Jinja2 filters.

Ansible auto-loads every *.py in a `filter_plugins/` folder next to the playbook
(or the folders listed under `filter_plugins =` in ansible.cfg).
The only contract: a class named `FilterModule` with a `filters()` method that
returns {"filter_name": python_function}.
"""
import re

from ansible.errors import AnsibleFilterError


def human_bytes(value, precision=1):
    """1536 -> '1.5 KiB'.  Usage: {{ disk_bytes | human_bytes }}"""
    try:
        size = float(value)
    except (TypeError, ValueError):
        raise AnsibleFilterError(f"human_bytes expects a number, got {value!r}")
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(size) < 1024 or unit == "TiB":
            return f"{size:.{precision}f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024


def mask(value, visible=4, char="*"):
    """'hunter2-secret' -> '**********cret'.  Usage: {{ password | mask }}"""
    value = str(value)
    if len(value) <= visible:
        return char * len(value)
    return char * (len(value) - visible) + value[-visible:]


def slugify(value):
    """'Acme Corp / Web Tier!' -> 'acme-corp-web-tier'.  Usage: {{ name | slugify }}"""
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


# def shout(value):
#     return str(value).upper() + "!"


class FilterModule:
    def filters(self):
        return {
            "human_bytes": human_bytes,
            "mask": mask,
            "slugify": slugify,
            # "shout": shout,
        }


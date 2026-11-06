"""preflight action plugin: check a host BEFORE we deploy to it.

Why an action plugin and not a module?
  A module runs ON THE TARGET and only sees the target.
  An action plugin runs ON THE CONTROLLER. It can:
    1. run modules on the target          (here: ansible.builtin.setup)
    2. use controller-only things          (here: write a report file on the controller)
    3. decide ok / failed centrally        (here: compare facts against thresholds)
  Built-in examples: template, copy, fetch, debug, assert are all action plugins.

Usage:
  - preflight:
      min_memory_mb: 2048
      min_cpus: 2
      min_python: "3.10"
      report_dir: reports      # relative to the playbook, on the controller

The file name (preflight.py) IS the task name. The class must be `ActionModule`.
"""
import os
from datetime import datetime

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(("min_memory_mb", "min_cpus", "min_python", "report_dir"))

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        args = self._task.args
        host = task_vars["inventory_hostname"]

        # 1. Run a real module ON THE TARGET and get its facts back
        display.vvv(f"preflight: gathering facts on {host}")
        setup = self._execute_module(
            module_name="ansible.builtin.setup",
            module_args={"gather_subset": ["!all", "!min", "hardware", "python"]},
            task_vars=task_vars,
        )
        if setup.get("failed"):
            return setup
        facts = setup["ansible_facts"]

        # 2. Decide ON THE CONTROLLER
        python = facts["ansible_python"]["version"]
        python_str = f"{python['major']}.{python['minor']}.{python['micro']}"
        min_python = str(args.get("min_python", "3.0"))
        checks = [
            ("memory_mb", int(args.get("min_memory_mb", 0)), facts["ansible_memtotal_mb"]),
            ("cpus", int(args.get("min_cpus", 1)), facts["ansible_processor_vcpus"]),
            ("python", min_python, python_str),
        ]
        rows = []
        for name, required, actual in checks:
            if name == "python":
                ok = _version(actual) >= _version(required)
            else:
                ok = actual >= required
            rows.append({"check": name, "required": required, "actual": actual, "ok": ok})
        failed = [r["check"] for r in rows if not r["ok"]]

        # 3. Write a report file ON THE CONTROLLER (a module could never do this)
        if args.get("report_dir"):
            report_dir = os.path.join(self._loader.get_basedir(), args["report_dir"])
            os.makedirs(report_dir, exist_ok=True)
            report = os.path.join(report_dir, f"{host}.txt")
            with open(report, "w") as f:
                f.write(f"Preflight report for {host}  ({datetime.now():%Y-%m-%d %H:%M:%S})\n")
                for r in rows:
                    f.write(f"  [{'PASS' if r['ok'] else 'FAIL'}] {r['check']:<10} "
                            f"required >= {r['required']:<8} actual = {r['actual']}\n")
            result["report"] = report

        result["checks"] = rows
        result["changed"] = False
        result["failed"] = bool(failed)
        result["msg"] = f"preflight FAILED: {', '.join(failed)}" if failed else "preflight passed"
        return result


def _version(text):
    """'3.10.2' -> (3, 10, 2) so versions compare correctly ('3.9' < '3.10')."""
    return tuple(int(part) for part in str(text).split("."))

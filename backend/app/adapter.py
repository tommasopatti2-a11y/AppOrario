from __future__ import annotations
import importlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List

from .config import settings
from .models import Job


def run_entrypoint(job: Job) -> int:
    assert job.workdir is not None
    assert job.log_path is not None
    inputs_dir = job.workdir.parent.parent / "inputs"
    input_paths = [str(p) for p in sorted(inputs_dir.glob("*.xlsx"))]

    # Prepare log file capture
    log_file = open(job.log_path, "a", encoding="utf-8")

    # Write a header
    log_file.write("=== Job {} ===\n".format(job.job_id))
    log_file.write("Inputs: {}\n".format(", ".join(Path(p).name for p in input_paths)))
    log_file.flush()

    # Progressive messages
    job.message = "Esecuzione entrypoint"
    job.progress = 25

    exit_code = 1
    try:
        ep = settings.PROGRAM_ENTRYPOINT
        if ":" in ep:
            mod_name, func_name = ep.split(":", 1)
            job.message = f"Import {mod_name}:{func_name}"
            job.progress = 35
            # Ensure project root is on sys.path so modules at repo root are importable
            try:
                # __file__ -> .../AppOrario/backend/app/adapter.py
                # parents[0]=.../backend/app, [1]=.../backend, [2]=.../AppOrario
                base_root = Path(__file__).resolve().parents[2]
                if str(base_root) not in sys.path:
                    sys.path.insert(0, str(base_root))
            except Exception:
                pass
            mod = importlib.import_module(mod_name.replace(".py", ""))
            fn = getattr(mod, func_name)
            job.message = "Esecuzione funzione"
            job.progress = 50
            result = fn(input_paths=input_paths, output_dir=str(job.workdir), **job.options)
            exit_code = 0 if (result is None or result == 0) else int(result)
        else:
            job.message = "Esecuzione subprocess"
            job.progress = 50
            cmd = [sys.executable, ep] if ep.endswith('.py') else shlex.split(ep)
            cmd += ["--inputs", json.dumps(input_paths), "--out", str(job.workdir), "--options", json.dumps(job.options)]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:  # type: ignore
                log_file.write(line)
            proc.wait()
            exit_code = proc.returncode
        job.progress = 90
        job.message = "Post-processing"
    except Exception as e:
        log_file.write(f"\n[ERROR] {e}\n")
        exit_code = 1
    finally:
        log_file.flush()
        log_file.close()
    return exit_code

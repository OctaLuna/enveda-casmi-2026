#!/usr/bin/env python3
"""
H50 - experiment-logger
Al finalizar el turno o sesión del agente (Stop / SubagentStop), si se modificaron
archivos en src/ o configs/, extrae las métricas reales de reports/latest_metrics.json
y añade una entrada en EXPERIMENTS.md.
Nunca inventa métricas: si no hay métricas calculadas, lo reporta explícitamente.
"""

from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def get_git_info() -> tuple:
    commit = "n/a"
    changed_src = False
    try:
        proc_hash = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False)
        if proc_hash.returncode == 0:
            commit = proc_hash.stdout.strip()
        proc_stat = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=False)
        for line in proc_stat.stdout.splitlines():
            if "src/" in line or "configs/" in line:
                changed_src = True
                break
    except Exception:
        pass
    return commit, changed_src


def log_experiment(root: Path, commit: str, config: dict) -> None:
    min_seeds = config.get("min_seeds", 3)
    exp_file = root / "EXPERIMENTS.md"
    metrics_file = root / "reports" / "latest_metrics.json"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    mrr_c1, mrr_c2, mrr_c3, mrr_all = "-", "-", "-", "-"
    seeds_count = 0
    cascade_time = "-"

    if metrics_file.is_file():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            mrr_all = f"{data.get('mrr_overall', data.get('mrr_at_25', '-')):.4f}" if isinstance(data.get('mrr_overall', data.get('mrr_at_25')), (int, float)) else "-"
            mrr_c1 = f"{data.get('mrr_clase1', '-'):.4f}" if isinstance(data.get('mrr_clase1'), (int, float)) else "-"
            mrr_c2 = f"{data.get('mrr_clase2', '-'):.4f}" if isinstance(data.get('mrr_clase2'), (int, float)) else "-"
            mrr_c3 = f"{data.get('mrr_clase3', '-'):.4f}" if isinstance(data.get('mrr_clase3'), (int, float)) else "-"
            seeds_count = len(data.get("seeds", []))
            cascade_time = f"{data.get('cascade_time_sec', '-')}s"
        except Exception as e:
            common.log_error("H50.experiment_logger", f"Error leyendo {metrics_file}: {e}")

    if seeds_count > 0 and seeds_count < min_seeds:
        common.warn(
            f"El experimento evaluó solo {seeds_count} semillas (< {min_seeds}). Podría haber sobreajuste a la semilla.",
            hook_id="H50"
        )

    row = f"| {now_str} | `{commit}` | Cambios en pipeline | {mrr_all} | {mrr_c1} | {mrr_c2} | {mrr_c3} | {seeds_count} | {cascade_time} |\n"

    try:
        if exp_file.is_file():
            content = exp_file.read_text(encoding="utf-8")
            if "| Fecha" in content:
                with open(exp_file, "a", encoding="utf-8") as f:
                    f.write(row)
                common.log_activity(f"[{now_str}] Experimento registrado en EXPERIMENTS.md (Commit {commit})")
    except Exception as e:
        common.log_error("H50.write_exp", f"Error escribiendo en EXPERIMENTS.md: {e}")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()

    commit, changed_src = get_git_info()
    if changed_src:
        log_experiment(root, commit, config)

    sys.exit(0)


if __name__ == "__main__":
    main()

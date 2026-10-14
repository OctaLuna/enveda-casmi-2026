#!/usr/bin/env python3
"""
H51 - submission-ledger
Registra automáticamente cada intento de envío a Kaggle ('kaggle competitions submit')
en reports/submissions.csv para auditoría de Leaderboard vs. Validación Local.
Modo: warn.
"""

import csv
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


def get_git_commit() -> str:
    try:
        proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False)
        return proc.stdout.strip() or "n/a"
    except Exception:
        return "n/a"


def record_submission(cmd: str, root: Path) -> None:
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    csv_file = reports_dir / "submissions.csv"

    # Extraer mensaje de submission del comando -m "..."
    msg = "Envío manual"
    if "-m" in cmd:
        parts = cmd.split("-m", 1)[1].strip()
        msg = parts.split('"')[1] if '"' in parts else parts.split("'")[1] if "'" in parts else parts.split()[0]

    commit = get_git_commit()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Leer métricas locales de reports/latest_metrics.json
    metrics_file = reports_dir / "latest_metrics.json"
    mrr_loc = "-"
    if metrics_file.is_file():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                d = json.load(f)
            mrr_loc = f"{d.get('mrr_overall', d.get('mrr_at_25', '-')):.4f}"
        except Exception:
            pass

    file_exists = csv_file.is_file()
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["fecha", "commit", "mensaje", "mrr_local", "mrr_publico_kaggle", "observaciones"])
        writer.writerow([now_str, commit, msg, mrr_loc, "PENDIENTE", "Anotar score de leaderboard"])

    print("\n[H51: ENVÍO REGISTRADO EN reports/submissions.csv]")
    print(f"  * Fecha: {now_str} | Commit: {commit} | MRR Local: {mrr_loc}")
    print("  * Recordatorio: En cuanto Kaggle evalúe el submission, completa la columna 'mrr_publico_kaggle'")
    print("    para detectar sobreajuste o discrepancias de clases (Clase 1 vs Clase 3).\n")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    cmd = payload.get("command", "")
    root = common.find_project_root() or Path.cwd()

    if "kaggle competitions submit" in cmd.lower():
        record_submission(cmd, root)

    sys.exit(0)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
H27 - time-budget-guard
Verifica que el presupuesto de tiempo de inferencia declarado en configs/budget.yaml
(o en configuración de cascada) no exceda el límite estricto de 9 horas de Kaggle,
incluyendo un margen de seguridad del 20% (time_margin = 0.20).
"""

from pathlib import Path
import re
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def parse_simple_yaml(path: Path) -> dict:
    """Parser liviano de YAML plano sin dependencias externas."""
    data = {}
    if not path.is_file():
        return data
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    val = v.strip().split("#")[0].strip()
                    try:
                        if "." in val:
                            data[k.strip()] = float(val)
                        else:
                            data[k.strip()] = int(val)
                    except ValueError:
                        data[k.strip()] = val
    except Exception as e:
        common.log_error("H27.yaml", f"Error leyendo {path}: {e}")
    return data


def validate_budget(budget_data: dict, config: dict) -> None:
    time_limit_h = config.get("time_limit_hours", 9)
    time_margin = config.get("time_margin", 0.20)
    max_total_minutes = time_limit_h * 60.0  # 540 min

    # Extraer minutos estimados por pilar o total
    # Pilares: pilar_a_minutes, pilar_b_minutes, pilar_c_minutes
    m_a = float(budget_data.get("pilar_a_minutes", budget_data.get("pilar_a_min", 60)))
    m_b = float(budget_data.get("pilar_b_minutes", budget_data.get("pilar_b_min", 150)))
    m_c = float(budget_data.get("pilar_c_minutes", budget_data.get("pilar_c_min", 210)))

    total_nominal = m_a + m_b + m_c
    total_with_margin = total_nominal * (1.0 + time_margin)
    margin_remaining = max_total_minutes - total_with_margin

    print("\n--- Presupuesto de Cómputo de Inferencia (CASMI 9h) ---")
    print(f"  * Pilar A (Retrieval FAISS):       {m_a:6.1f} min")
    print(f"  * Pilar B (Fingerprint MIST):     {m_b:6.1f} min")
    print(f"  * Pilar C (De Novo DiffMS/CFM):   {m_c:6.1f} min")
    print(f"  * Total Nominal:                  {total_nominal:6.1f} min ({(total_nominal/60):.2f} h)")
    print(f"  * Con Margen Seguridad ({int(time_margin*100)}%):    {total_with_margin:6.1f} min ({(total_with_margin/60):.2f} h)")
    print(f"  * Límite Kaggle:                  {max_total_minutes:6.1f} min ({time_limit_h} h)")
    print(f"  * Margen Restante:                {margin_remaining:6.1f} min")
    print("------------------------------------------------------\n")

    if total_with_margin > max_total_minutes:
        common.block(
            f"El presupuesto de tiempo con margen ({total_with_margin:.1f} min) excede las {time_limit_h} h permitidas ({max_total_minutes} min).",
            hook_id="H27",
            reason="Los notebooks de Kaggle son abortados con timeout fatal si superan 9 horas de ejecución.",
            solution="Reduce el número de candidatos de novo en Clase 3 o ajusta los umbrales de confianza de Pilar A/B."
        )


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()

    budget_files = []
    for p in payload.get("paths", []):
        p_obj = Path(p)
        if "budget" in p_obj.name.lower() and p_obj.suffix in (".yaml", ".yml"):
            budget_files.append(p_obj)

    if not budget_files:
        default_file = root / "configs" / "budget.yaml"
        if default_file.is_file():
            budget_files.append(default_file)

    for bf in budget_files:
        if bf.is_file():
            budget_data = parse_simple_yaml(bf)
            validate_budget(budget_data, config)

    sys.exit(0)


if __name__ == "__main__":
    main()

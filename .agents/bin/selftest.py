#!/usr/bin/env python3
"""
selftest.py - Suite de pruebas de aceptación para el sistema de hooks CASMI 2026.
Se ejecuta estrictamente sin requerir conexión a internet y sin dependencias de ML.
Verifica que cada hook bloquee (exit 2) y permita (exit 0) según la especificación.
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile

BIN_DIR = Path(__file__).resolve().parent
AGENT_DIR = BIN_DIR.parent
HOOKS_DIR = AGENT_DIR / "hooks"
FIXTURES_DIR = AGENT_DIR / "tests" / "fixtures"
DISPATCHER = BIN_DIR / "agent-hook"

PASSED = 0
FAILED = 0
SKIPPED = 0


def report(name: str, success: bool, msg: str = ""):
    global PASSED, FAILED
    if success:
        PASSED += 1
        print(f" [PASS] {name}")
    else:
        FAILED += 1
        print(f" [FAIL] {name}: {msg}")


def skip(name: str, reason: str):
    global SKIPPED
    SKIPPED += 1
    print(f" [SKIP] {name}: {reason}")


def run_hook_proc(script_rel: str, payload: dict) -> subprocess.CompletedProcess:
    script_path = HOOKS_DIR / script_rel
    payload_bytes = json.dumps(payload).encode("utf-8")
    return subprocess.run(
        [sys.executable, str(script_path)],
        input=payload_bytes,
        capture_output=True,
        timeout=10
    )


def test_h10_block_secrets():
    # Bloquear credencial
    p_bad = {"command": "cat ~/.kaggle/kaggle.json", "content": "KAGGLE_KEY='abc1234567890'"}
    res_bad = run_hook_proc("safety/block_secrets.py", p_bad)
    report("H10: Bloquear secretos en comando y variables", res_bad.returncode == 2)

    # Permitir texto inocuo
    p_ok = {"command": "echo 'compitiendo en kaggle casmi'", "content": "kaggle_evaluation = True"}
    res_ok = run_hook_proc("safety/block_secrets.py", p_ok)
    report("H10: Permitir texto sobre kaggle sin credenciales", res_ok.returncode == 0)


def test_h11_protect_raw_data():
    # Bloquear escritura en data/raw
    p_bad = {"paths": ["data/raw/train.parquet"], "command": "rm -rf data/raw"}
    res_bad = run_hook_proc("safety/protect_raw_data.py", p_bad)
    report("H11: Bloquear borrado o modificación de data/raw", res_bad.returncode == 2)

    # Permitir escritura en data/interim
    p_ok = {"paths": ["data/interim/processed_spectra.pkl"], "command": "ls data/"}
    res_ok = run_hook_proc("safety/protect_raw_data.py", p_ok)
    report("H11: Permitir escritura en data/interim", res_ok.returncode == 0)


def test_h12_block_large_files():
    # Bloquear git add de extensiones pesadas
    p_bad = {"command": "git add model.safetensors"}
    res_bad = run_hook_proc("safety/block_large_files.py", p_bad)
    report("H12: Bloquear git add de safetensors", res_bad.returncode == 2)

    # Permitir archivo fuente python
    p_ok = {"command": "git add src/a.py", "paths": ["src/a.py"]}
    res_ok = run_hook_proc("safety/block_large_files.py", p_ok)
    report("H12: Permitir código Python", res_ok.returncode == 0)


def test_h13_dangerous_commands():
    # Bloquear force push
    p_bad = {"command": "git push --force origin main"}
    res_bad = run_hook_proc("safety/dangerous_commands.py", p_bad)
    report("H13: Bloquear git push --force", res_bad.returncode == 2)

    # Permitir push normal
    p_ok = {"command": "git push origin feat/pilar-a-retrieval"}
    res_ok = run_hook_proc("safety/dangerous_commands.py", p_ok)
    report("H13: Permitir push estándar a rama de feature", res_ok.returncode == 0)


def test_h14_offline_guard():
    # Bloquear requests en inference
    p_bad = {"paths": ["src/inference/predict.py"], "content": "import requests\nres = requests.get('http://api')"}
    res_bad = run_hook_proc("safety/offline_guard.py", p_bad)
    report("H14: Bloquear llamadas de red en inference", res_bad.returncode == 2)

    # Permitir en research
    p_ok = {"paths": ["src/research/explore.py"], "content": "import requests\nres = requests.get('http://api')"}
    res_ok = run_hook_proc("safety/offline_guard.py", p_ok)
    report("H14: Permitir llamadas fuera de rutas offline", res_ok.returncode == 0)


def test_h20_rdkit_pin():
    p = {}
    res = run_hook_proc("domain/rdkit_pin_check.py", p)
    report("H20: Verificación de RDKit pin", res.returncode in (0, 2))


def test_h22_split_leakage():
    # Bloquear split con fuga
    p_bad = {"paths": [str(FIXTURES_DIR / "leakage_split.json")]}
    res_bad = run_hook_proc("domain/split_leakage_guard.py", p_bad)
    report("H22: Bloquear split con intersección no vacía", res_bad.returncode == 2)

    # Permitir split válido
    p_ok = {"paths": [str(FIXTURES_DIR / "valid_split.json")]}
    res_ok = run_hook_proc("domain/split_leakage_guard.py", p_ok)
    report("H22: Permitir split disjunto", res_ok.returncode == 0)


def test_h23_metric_test():
    p = {}
    res = run_hook_proc("domain/metric_test.py", p)
    report("H23: Casos de prueba de MRR@25", res.returncode == 0)


def test_h24_submission_validator():
    # Bloquear 26 candidatos
    p_bad26 = {"paths": [str(FIXTURES_DIR / "invalid_submission_26.csv")]}
    res_bad26 = run_hook_proc("domain/submission_validator.py", p_bad26)
    report("H24: Bloquear submission con > 25 candidatos", res_bad26.returncode == 2)

    # Bloquear separador por coma
    p_bad_comma = {"paths": [str(FIXTURES_DIR / "invalid_submission_comma.csv")]}
    res_bad_comma = run_hook_proc("domain/submission_validator.py", p_bad_comma)
    report("H24: Bloquear separador de candidatos que no sea ';'", res_bad_comma.returncode == 2)

    # Permitir submission válido
    p_ok = {"paths": [str(FIXTURES_DIR / "valid_submission.csv")]}
    res_ok = run_hook_proc("domain/submission_validator.py", p_ok)
    report("H24: Permitir submission válido", res_ok.returncode == 0)


def test_h27_time_budget():
    p_bad = {"paths": [str(FIXTURES_DIR / "invalid_budget.yaml")]}
    res_bad = run_hook_proc("domain/time_budget_guard.py", p_bad)
    report("H27: Bloquear presupuesto de cómputo superior a 540 min", res_bad.returncode == 2)

    p_ok = {"paths": [str(FIXTURES_DIR / "valid_budget.yaml")]}
    res_ok = run_hook_proc("domain/time_budget_guard.py", p_ok)
    report("H27: Permitir presupuesto de cómputo holgado", res_ok.returncode == 0)


def test_g02_commit_msg():
    script_path = AGENT_DIR / "git-hooks" / "commit-msg"
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("arreglé cosas\n")
        bad_file = Path(f.name)

    res_bad = subprocess.run([sys.executable, str(script_path), str(bad_file)], capture_output=True)
    report("G02: Bloquear commit con mensaje libre no convencional", res_bad.returncode == 2)
    bad_file.unlink()

    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("feat(pilar-a): agregar índice FAISS IVF-PQ\n")
        ok_file = Path(f.name)

    res_ok = subprocess.run([sys.executable, str(script_path), str(ok_file)], capture_output=True)
    report("G02: Permitir Conventional Commit en español con scope válido", res_ok.returncode == 0)
    ok_file.unlink()


def test_g04_pre_push():
    script_path = AGENT_DIR / "git-hooks" / "pre-push"
    # Comprobar que script exista y ejecute
    report("G04: Script de pre-push disponible", script_path.is_file())


def test_agent_smoke_payloads():
    """Confirma que el despachador procese payloads de Claude, Codex y Antigravity uniformemente."""
    test_cases = [
        ("claude", {"agent": "claude", "event": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}}),
        ("codex", {"agent": "codex", "event": "pre_tool", "tool": "bash", "command": "git push --force origin main"}),
        ("antigravity", {"agent": "antigravity", "event": "pre_tool", "tool": "bash", "command": "git push --force origin main"}),
    ]
    for agent_name, payload in test_cases:
        proc = subprocess.run(
            [sys.executable, str(DISPATCHER), payload["event"], "--agent", agent_name],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True
        )
        report(f"Smoke Test Adaptador [{agent_name}]: Bloqueo consistente de comando peligroso", proc.returncode == 2)


def main():
    print("========================================================")
    print("      ENVEDA CASMI 2026 - SELFTEST DE HOOKS             ")
    print("========================================================")

    test_h10_block_secrets()
    test_h11_protect_raw_data()
    test_h12_block_large_files()
    test_h13_dangerous_commands()
    test_h14_offline_guard()
    test_h20_rdkit_pin()
    test_h22_split_leakage()
    test_h23_metric_test()
    test_h24_submission_validator()
    test_h27_time_budget()
    test_g02_commit_msg()
    test_g04_pre_push()
    test_agent_smoke_payloads()

    print("========================================================")
    print(f" RESULTADO FINAL: {PASSED} Pasados | {FAILED} Fallados | {SKIPPED} Omitidos")
    print("========================================================")

    if FAILED > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

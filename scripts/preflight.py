"""Fail-closed local release gate for ProvenanceSeal."""
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "provenanceseal.py"
CONFIG = ROOT / "gltest.config.yaml"
SOURCES = sorted((ROOT / "contracts").glob("*.py"))
if SOURCES != [CONTRACT]:
    raise SystemExit(f"Expected exactly contracts/provenanceseal.py; found {[p.name for p in SOURCES]}")
config = CONFIG.read_text(encoding="utf-8")
if "default: studionet" not in config or "https://studio.genlayer.com/api" not in config:
    raise SystemExit("Preflight requires GenLayer Studionet as the only configured network")
ast.parse(CONTRACT.read_text(encoding="utf-8"), filename=str(CONTRACT))
candidate = Path(sys.executable).with_name("genvm-lint.exe" if os.name == "nt" else "genvm-lint")
lint = str(candidate) if candidate.exists() else (shutil.which("genvm-lint") or shutil.which("genvm-lint.exe"))
if not lint:
    raise SystemExit("genvm-lint not found; install pinned requirements")

env = os.environ.copy()

def run(command):
    print("+", " ".join(map(str, command)), flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)

run([sys.executable, "-m", "compileall", "-q", "contracts", "tests"])
run([sys.executable, "-m", "pytest", "tests", "-q"])
run([lint, "check", str(CONTRACT), "--json"])

target = ROOT / "artifacts" / "provenanceseal.abi.json"
target.parent.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="provenanceseal-abi-", dir=ROOT) as temporary:
    generated = Path(temporary) / "provenanceseal.abi.json"
    run([lint, "schema", str(CONTRACT), "--output", str(generated)])
    expected = generated.read_bytes().replace(b"\r\n", b"\n")
    actual = target.read_bytes().replace(b"\r\n", b"\n") if target.exists() else b""
    if actual and expected != actual:
        raise SystemExit("Generated ABI/schema differs from committed artifacts/provenanceseal.abi.json")
    if not isinstance(json.loads(expected.decode("utf-8")), dict):
        raise SystemExit("Generated ABI/schema is invalid")
    if not target.exists():
        target.write_bytes(expected)

print("ProvenanceSeal preflight PASS: deployable-source count, syntax, tests, lint, and ABI/schema")

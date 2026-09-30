"""
ArthSathi — Start all services.

Usage:
    python run.py              # starts backend only (default)
    python run.py --all        # starts backend + translation API + LM API + telegram bot
    python run.py --backend    # backend only
    python run.py --ml         # translation API + LM API only
    python run.py --bot        # telegram bot only
"""

import subprocess
import sys
import os
import time
import argparse
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
ML = ROOT / "arthsathi-ml"
BOT = ROOT / "bot"


def run_process(cmd: list, cwd: Path, name: str):
    print(f"\n[{name}] Starting: {' '.join(cmd)}")
    return subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all",     action="store_true")
    parser.add_argument("--backend", action="store_true")
    parser.add_argument("--ml",      action="store_true")
    parser.add_argument("--bot",     action="store_true")
    args = parser.parse_args()

    # Default: backend only
    if not any([args.all, args.backend, args.ml, args.bot]):
        args.backend = True

    processes = []

    if args.backend or args.all:
        p = run_process(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
            cwd=BACKEND,
            name="Backend API :8000"
        )
        processes.append(p)
        time.sleep(2)

    if args.ml or args.all:
        # Translation API
        p = run_process(
            [sys.executable, "-m", "uvicorn", "translation.serve:app", "--port", "5001"],
            cwd=ML,
            name="Translation API :5001"
        )
        processes.append(p)

        # Language Model API
        p = run_process(
            [sys.executable, "-m", "uvicorn", "language_model.serve:app", "--port", "5002"],
            cwd=ML,
            name="LM API :5002"
        )
        processes.append(p)

    if args.bot or args.all:
        env = os.environ.copy()
        env["BACKEND_URL"] = "http://localhost:8000"
        p = subprocess.Popen(
            [sys.executable, "src/index.js"],
            cwd=str(BOT),
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=env,
        )
        processes.append(p)

    if not processes:
        print("Nothing to start.")
        return

    print("\n" + "="*50)
    print("ArthSathi services running:")
    if args.backend or args.all:
        print("  Backend API  → http://localhost:8000")
        print("  API Docs     → http://localhost:8000/docs")
    if args.ml or args.all:
        print("  Translation  → http://localhost:5001")
        print("  Language LM  → http://localhost:5002")
    if args.bot or args.all:
        print("  Telegram Bot → running")
    print("="*50)
    print("Press Ctrl+C to stop all services\n")

    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\nStopping all services...")
        for p in processes:
            p.terminate()


if __name__ == "__main__":
    main()

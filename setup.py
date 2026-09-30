"""
One-time setup — installs all dependencies for backend and arthsathi-ml.

Run: python setup.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def run(cmd, cwd=None):
    print(f"\n>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        print(f"[WARNING] Command exited with code {result.returncode}")


def main():
    pip = [sys.executable, "-m", "pip", "install"]

    print("="*50)
    print("ArthSathi Setup")
    print("="*50)

    # Backend
    print("\n[1/3] Installing backend dependencies...")
    run(pip + ["-r", "requirements.txt"], cwd=ROOT / "backend")

    # arthsathi-ml
    print("\n[2/3] Installing arthsathi-ml dependencies...")
    run(pip + ["-r", "requirements.txt"], cwd=ROOT / "arthsathi-ml")

    # Data collection
    print("\n[3/3] Running data collection...")
    run([sys.executable, "data/scripts/collect_schemes.py"],   cwd=ROOT / "arthsathi-ml")
    run([sys.executable, "data/scripts/collect_insurance.py"], cwd=ROOT / "arthsathi-ml")
    run([sys.executable, "data/scripts/generate_synthetic.py"], cwd=ROOT / "arthsathi-ml")
    run([sys.executable, "data/scripts/clean_and_format.py"],  cwd=ROOT / "arthsathi-ml")

    print("\n" + "="*50)
    print("Setup complete!")
    print("\nTo start the backend:")
    print("  python run.py")
    print("\nTo start everything (after training):")
    print("  python run.py --all")
    print("\nAPI docs will be at: http://localhost:8000/docs")
    print("="*50)


if __name__ == "__main__":
    main()

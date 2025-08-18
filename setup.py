from pathlib import Path
import os, subprocess, sys

ROOT_DIR = Path(__file__).parent
BACKEND_DIR = ROOT_DIR / "server"
FRONTEND_DIR = ROOT_DIR / "client"
REQUIREMENTS_FILE = BACKEND_DIR / "requirements.txt"

def venv_paths(venv: Path):
    if os.name == "nt":
        py = venv / "Scripts" / "python.exe"
        pip = venv / "Scripts" / "pip.exe"
    else:
        py = venv / "bin" / "python"
        pip = venv / "bin" / "pip"
    return py, pip

def run(cmd, cwd: Path | None = None):
    print(f"Running {cmd} in {cwd}")
    subprocess.run(cmd, cwd=cwd, check=True, shell=isinstance(cmd, str))

def venv_check(dir: Path):
    """Check if a virtual environment exists, and return the python executable and pip path"""
    venv = dir / ".venv"
    if not venv.exists():
        print(f"Creating venv at {venv}")
        subprocess.run(["python", "-m", "venv", str(venv)], check=True)
    py, pip = venv_paths(venv)
    # Make sure pip is installed (should be there by default)
    if not pip.exists():
        subprocess.run([str(py), "-m", "ensurepip", "--upgrade"], check=True)
    return py

def main():
    try:
        # Step 1: Backend
        print(f"\n Installing Backend dependencies...: {BACKEND_DIR}")
        py = venv_check(BACKEND_DIR)
        # activate = temporary shell convenience for humans.
        # wheel = actual dependency that makes installs smoother.
        if REQUIREMENTS_FILE.exists():
            run([str(py), "-m", "pip", "install", "--upgrade", "pip", "wheel"], cwd=BACKEND_DIR)
            print(f"Requirements: {REQUIREMENTS_FILE}")
        else:
            print(f"No requirements.txt at {REQUIREMENTS_FILE} - skipping pip install")

        # Step 2: Frontend
        print(f"\n Installing Frontend dependencies...: {FRONTEND_DIR}")
        run(["npm", "install"], cwd=FRONTEND_DIR)

        # Step 3: Root
        print(f"\n Installing root-level dependencies...: {ROOT_DIR}")
        run(["npm", "install"], cwd=BACKEND_DIR)

        print('\n Setup complete. You can now run the app with: npm run dev\n')
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
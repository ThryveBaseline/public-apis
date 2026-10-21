"""Prepare an isolated runtime, reusing GB10's existing JJ scientific packages.

Does not change the paper venv, cron, systemd, account state or order authority.
"""
import os
from pathlib import Path
import site
import subprocess
import sys
import venv


def main():
    if sys.prefix == sys.base_prefix:
        raise SystemExit("Run with /home/buddy2/jj-venv/bin/python so the existing JJ packages can be reused.")
    destination = Path.home() / ".local/share/jj-live/venv"
    if not destination.exists():
        venv.EnvBuilder(with_pip=True).create(destination)
    python = destination / "bin/python"
    target_site = subprocess.check_output([str(python), "-c", "import site; print(site.getsitepackages()[0])"], text=True).strip()
    # Paths only; no copied packages or executable .pth statements.
    Path(target_site, "jj-existing-packages.pth").write_text("\n".join(site.getsitepackages())+"\n")
    subprocess.run([str(python), "-m", "pip", "--disable-pip-version-check", "install", "--no-deps", "websocket-client==1.9.2"], check=True)
    state = Path.home() / ".local/share/jj-live"
    state.chmod(0o700)
    print(f"Isolated runtime prepared: {python}")
    print("LIVE_DISABLED; no service installed or started.")


if __name__ == "__main__":
    main()

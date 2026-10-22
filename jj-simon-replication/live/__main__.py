from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import getpass
import json
import os
from pathlib import Path
import sys

from . import LIVE_STATUS
from .ironbeam import Ironbeam, protected_json
from .models import Blocked, UTC
from .probe import probe
from .strategy import verify_frozen

ROOT = Path(__file__).resolve().parent.parent


def setup(path):
    """Interactive owner terminal input only; never command arguments or shell history."""
    if not sys.stdin.isatty():
        raise Blocked("CREDENTIAL_SETUP_REQUIRES_OWNER_TERMINAL")
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if p.exists() or p.is_symlink():
        raise Blocked("CREDENTIAL_FILE_EXISTS_USE_NEW_PATH")
    print("Enter Ironbeam-issued API credentials. Inputs are hidden; nothing is sent during setup.")
    print("Standard account: enter the username, then the issued API key at the key prompt, then leave the Enterprise prompt empty.")
    credentials = {"username": getpass.getpass("API username: "),
                   "password": getpass.getpass("API key (standard) or API password (Enterprise): ")}
    enterprise = getpass.getpass("Enterprise API key (leave empty for a standard account): ")
    if not all(credentials.values()):
        raise Blocked("CREDENTIAL_FIELDS_MISSING")
    if enterprise:
        credentials["apikey"] = enterprise
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        json.dump(credentials, fh)
        fh.flush()
        os.fsync(fh.fileno())
    return {"credential_file": str(p), "status": "CLEAR", "live": LIVE_STATUS}


def main():
    parser = argparse.ArgumentParser(description="JJ V1 isolated demo integration; real orders hard-disabled")
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("status")
    for cmd in ("setup", "probe"):
        p = subs.add_parser(cmd)
        p.add_argument("--credentials", default="~/.config/jj-live/ironbeam-demo.json")
        if cmd == "probe":
            p.add_argument("--environment", choices=("demo", "live-readonly"), default="demo")
            p.add_argument("--account")
            p.add_argument("--symbol", action="append", default=[])
            p.add_argument("--stream", action="store_true")
    mock = subs.add_parser("mock-demo")
    mock.add_argument("--output", required=True)
    day = subs.add_parser("mock-day")
    day.add_argument("--output", required=True)
    run = subs.add_parser("run")
    run.add_argument("--config", required=True)
    recovery = subs.add_parser("recover")
    recovery.add_argument("--config", required=True)
    smoke = subs.add_parser("demo-smoke")
    smoke.add_argument("--config", required=True)
    smoke.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        verify_frozen(ROOT)
        if args.command == "setup":
            result = setup(args.credentials)
        elif args.command == "probe":
            result = probe(Ironbeam(args.environment), protected_json(args.credentials), account=args.account, symbols=args.symbol, sample_stream=args.stream)
        elif args.command == "mock-demo":
            from .verification import mock_demo
            result = mock_demo(args.output)
        elif args.command == "mock-day":
            from .operational_trial import full_day_mock
            result = full_day_mock(args.output)
        elif args.command == "run":
            from .runner import run_config
            result = run_config(args.config)
        elif args.command == "recover":
            from .runner import recover_config
            result = recover_config(args.config)
        elif args.command == "demo-smoke":
            from .demo_mechanics import demo_smoke
            result = demo_smoke(args.config,args.output)
        else:
            result = {"live": LIVE_STATUS, "frozen_strategy": "CLEAR", "broker_demo": "BLOCKED", "reason": "API_CREDENTIALS_AND_BROKER_DEMO_VERIFICATION_REQUIRED"}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result.get("status")=="BLOCKED" else 0
    except Blocked as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error), "live": LIVE_STATUS}))
        return 2
    except (OSError, ValueError, KeyError, TypeError):
        # No raw exception or traceback that could disclose URLs, headers or secrets.
        print(json.dumps({"status": "BLOCKED", "reason": "INVALID_OR_UNAVAILABLE_CONFIGURATION", "live": LIVE_STATUS}))
        return 2


if __name__ == "__main__":
    sys.exit(main())

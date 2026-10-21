"""Account-wide process lock shared by the runtime and broker mechanics harness."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path

from .models import Blocked, stable_id


@contextmanager
def account_lock(environment, account):
    folder = Path.home()/".local/share/jj-live/locks"
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = folder/(stable_id([environment, account])+".lock")
    with open(path,"a") as handle:
        os.chmod(path,0o600)
        try:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise Blocked("ANOTHER_RUNTIME_OWNS_ACCOUNT") from None
        yield

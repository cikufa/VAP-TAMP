"""Enter a project-local Gemini API key privately; never accept secrets as arguments."""
import getpass
import os
from pathlib import Path
import subprocess
import sys
import warnings

from dotenv import set_key

ROOT = Path(__file__).resolve().parents[1]


def save_key(path, key):
    if len(key) < 20 or not key.isascii() or any(char.isspace() for char in key):
        raise ValueError("Enter a Gemini API key without quotes or spaces.")
    if path.is_symlink():
        raise ValueError("Refusing to write credentials through a .env symlink.")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
    finally:
        os.close(fd)
    set_key(str(path), "GEMINI_API_KEY", key, quote_mode="always")
    set_key(str(path), "VAPTAMP_VLM_PROVIDER", "gemini", quote_mode="never")
    set_key(str(path), "VAPTAMP_GEMINI_MODEL", "gemini-3.5-flash-lite", quote_mode="never")
    path.chmod(0o600)


def main():
    if not sys.stdin.isatty():
        raise SystemExit("Run this command in your own interactive terminal.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            key = getpass.getpass("Gemini API key (hidden; replaces project key): ")
        save_key(ROOT / ".env", key)
    except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        raise SystemExit("\nCancelled; no key saved.") from None
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print("Saved Gemini configuration in project .env with owner-only permissions.")
    raise SystemExit(subprocess.call(
        [sys.executable, str(ROOT / "scripts/check_vlm_backend.py")]))


if __name__ == "__main__":
    main()

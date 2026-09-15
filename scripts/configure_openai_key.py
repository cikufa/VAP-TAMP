"""Enter a project-local API key privately; never accept secrets as arguments."""
import argparse
import getpass
import os
from pathlib import Path
import subprocess
import sys
import warnings

from dotenv import set_key

ROOT = Path(__file__).resolve().parents[1]


def save_key(path, key):
    if not key.startswith('sk-') or not key.isascii() or not all(
        char.isalnum() or char in '-_' for char in key
    ):
        raise ValueError('Enter an OpenAI API key, without quotes or spaces.')
    if path.is_symlink():
        raise ValueError('Refusing to write credentials through a .env symlink.')
    # Restrict an existing file before dotenv reads/replaces it. Newly created
    # files and dotenv's atomic replacement temporary file are private too.
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
    finally:
        os.close(fd)
    set_key(str(path), 'OPENAI_API_KEY', key, quote_mode='always')
    path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='Check access to the released gpt-4-turbo model after saving.')
    args = parser.parse_args()
    if not sys.stdin.isatty():
        raise SystemExit('Run this command in your own interactive terminal.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            key = getpass.getpass('OpenAI API key (hidden; replaces project key): ')
        save_key(ROOT / '.env', key)
    except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        raise SystemExit('\nCancelled; no key saved.') from None
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print('Saved project .env with owner-only permissions. Key was not printed.')
    if args.check:
        env = os.environ.copy()
        env['OPENAI_API_KEY'] = key
        raise SystemExit(subprocess.call(
            [sys.executable, str(ROOT / 'scripts/check_released_model.py')], env=env))


if __name__ == '__main__':
    main()

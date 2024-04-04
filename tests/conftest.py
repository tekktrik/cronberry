# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: GPL-3.0-or-later

"""Pytest configuration file."""

import pathlib
import subprocess
from typing import Union

import pytest

BACKUP_FILEPATH = "tests/backup/table_backup.tab"


def pytest_sessionstart(session: pytest.Session) -> None:
    """Save the current cron table before testing."""
    proc = subprocess.Popen(
        ["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    output, _ = proc.communicate()

    if output:  # pragma: no cover
        backup = pathlib.Path(BACKUP_FILEPATH)
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(output)

        proc = subprocess.Popen(
            ["crontab", "-r"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        proc.communicate()
        if proc.returncode:
            raise OSError("Error occurred while deleting the current crontab")


def pytest_sessionfinish(
    session: pytest.Session, exitstatus: Union[int, pytest.ExitCode]
) -> None:
    """Restore the previous cron table after testing."""
    proc = subprocess.Popen(
        ["crontab", "-r"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    proc.communicate()

    backup = pathlib.Path(BACKUP_FILEPATH)
    if backup.exists():  # pragma: no cover
        proc = subprocess.Popen(
            ["crontab", str(backup.resolve())],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.communicate()
        if proc.returncode:
            raise OSError("Error occurred while restoring the previous crontab")
        backup.unlink()

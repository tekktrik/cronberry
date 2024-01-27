# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: MIT

"""Tests for functionality related to cli functionality."""

import os
import subprocess

from click.testing import CliRunner

from cronberry.app import cli


def test_cronberry_clear() -> None:
    """Tests the clear command."""
    runner = CliRunner()
    proc = subprocess.Popen(
        ["crontab", "tests/tables/src.tab"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proc.communicate()

    result = runner.invoke(cli, ["clear"])
    assert result.exit_code == 0

    proc = subprocess.Popen(
        ["crontab", "-l"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    output, _ = proc.communicate()
    assert len(output) == 0


def test_cronberry_save() -> None:
    """Tests the save command."""
    src_filepath = "tests/tables/src.tab"
    dest_filepath = "tests/tables/temp.tab"
    runner = CliRunner()
    proc = subprocess.Popen(
        ["crontab", src_filepath],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proc.communicate()

    result = runner.invoke(cli, ["save", dest_filepath])
    assert result.exit_code == 0

    with open(src_filepath, "rb") as srcfile, open(
        dest_filepath, mode="rb"
    ) as destfile:
        src = srcfile.read()
        dest = destfile.read()
    assert src == dest

    os.remove(dest_filepath)

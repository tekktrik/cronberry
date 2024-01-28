# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: MIT

"""Tests for functionality related to cli functionality."""

import os
import subprocess
from typing import Tuple

from click.testing import CliRunner

from cronberry.app import cli


def crontab_remove() -> int:
    """Use crontab remove command."""
    proc = subprocess.Popen(
        ["crontab", "-r"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proc.communicate()
    return proc.returncode


def crontab_list() -> Tuple[int, bytes, bytes]:
    """Use crontab list command."""
    proc = subprocess.Popen(
        ["crontab", "-l"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = proc.communicate()
    return proc.returncode, output, error


def crontab_set(filepath: str) -> int:
    """Use crontab list command."""
    proc = subprocess.Popen(
        ["crontab", filepath],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proc.communicate()
    return proc.returncode


def test_cronberry_clear() -> None:
    """Tests the clear command."""
    src_filepath = "tests/tables/src.tab"
    runner = CliRunner()

    crontab_set(src_filepath)

    result = runner.invoke(cli, ["clear"])
    assert result.exit_code == 0

    _, output, _ = crontab_list()
    assert len(output) == 0


def test_cronberry_save() -> None:
    """Tests the save command."""
    src_filepath = "tests/tables/src.tab"
    dest_filepath = "tests/tables/temp.tab"
    runner = CliRunner()

    crontab_set(src_filepath)

    result = runner.invoke(cli, ["save", dest_filepath])
    assert result.exit_code == 0

    with open(src_filepath, "rb") as srcfile, open(
        dest_filepath, mode="rb"
    ) as destfile:
        src = srcfile.read()
        dest = destfile.read()
    assert src == dest

    os.remove(dest_filepath)


def test_cronberry_add() -> None:
    """Tests the add command."""
    src_filepath = "tests/tables/src.tab"
    new_filepath = "tests/tables/new.tab"
    comb_filepath = "tests/tables/combined.tab"
    runner = CliRunner()

    crontab_remove()

    result = runner.invoke(cli, ["add", src_filepath])
    assert result.exit_code == 0

    _, output, _ = crontab_list()
    with open(src_filepath, mode="rb") as srcfile:
        src_contents = srcfile.read()
    assert output == src_contents

    result = runner.invoke(cli, ["add", new_filepath])
    assert result.exit_code == 0

    _, output, _ = crontab_list()
    with open(comb_filepath, mode="rb") as combfile:
        comb_contents = combfile.read()
    assert output == comb_contents

    crontab_remove()


def test_cronberry_remove() -> None:
    """Tests removing remove command."""
    src_filepath = "tests/tables/src.tab"
    comb_filepath = "tests/tables/combined.tab"
    runner = CliRunner()

    crontab_set(comb_filepath)

    result = runner.invoke(cli, ["remove", "Test 5", "Test 6"])
    assert result.exit_code == 0

    _, output, _ = crontab_list()

    with open(src_filepath, mode="rb") as srcfile:
        src_contents = srcfile.read()

    assert src_contents == output

    # Test errors

    result = runner.invoke(cli, ["remove", "Duplicate", "Duplicate"])
    assert result.exit_code != 0

    result = runner.invoke(cli, ["remove", "Not in table"])
    assert result.exit_code != 0

    crontab_remove()


def test_cronberry_job() -> None:
    """Tests the job command."""
    src_filepath = "tests/tables/src.tab"
    bad_filepath = "tests/tables/bad.tab"
    expected_job = '3-45/3 * * */2 * echo "Test 3!"\n'
    runner = CliRunner()

    crontab_set(src_filepath)

    result = runner.invoke(cli, ["job", "Test 3"])
    assert result.exit_code == 0
    assert result.output == expected_job

    # Test errors

    result = runner.invoke(cli, ["job", "Not in table"])
    assert result.exit_code != 0

    crontab_set(bad_filepath)
    result = runner.invoke(cli, ["job", "Test 7"])
    assert result.exit_code != 0

    crontab_remove()


def test_cronberry_jobs() -> None:
    """Tests the jobs command."""
    src_filepath = "tests/tables/src.tab"
    expected_jobs = "Test 1\nTest 2\nTest 3\nTest 4\n"
    runner = CliRunner()

    crontab_set(src_filepath)

    result = runner.invoke(cli, ["jobs"])
    assert result.exit_code == 0
    assert result.output == expected_jobs

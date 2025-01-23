# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for functionality related to cli functionality."""

import os
import subprocess

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


def crontab_list() -> tuple[int, bytes, bytes]:
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

    with (
        open(src_filepath, "rb") as srcfile,
        open(dest_filepath, mode="rb") as destfile,
    ):
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

    # Test adding specific jobs
    crontab_set(new_filepath)
    result = runner.invoke(cli, ["add", new_filepath, "-t", "Job 5"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["add", new_filepath, "-t", "Job 6"])
    assert result.exit_code == 0

    _, output, _ = crontab_list()
    with open(new_filepath, mode="rb") as newfile:
        new_contents = newfile.read()
    assert output == new_contents

    # Test errors

    result = runner.invoke(cli, ["add", new_filepath])
    assert result.exit_code == 1

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


def test_cronberry_view() -> None:
    """Tests the view command."""
    src_filepath = "tests/tables/src.tab"
    bad_filepath = "tests/tables/bad.tab"
    expected_job = '3-45/3 * * */2 * echo "Test 3!"\n'
    runner = CliRunner()

    crontab_set(src_filepath)

    result = runner.invoke(cli, ["view", "Test 3"])
    assert result.exit_code == 0
    assert result.output == expected_job

    with open(src_filepath, encoding="utf-8") as srcfile:
        src_contents = srcfile.read()

    job_text = "\n".join(src_contents.split("\n")[16:24])

    result = runner.invoke(cli, ["view", "Test 3", "-v"])
    assert result.exit_code == 0
    assert result.output == job_text

    # Test errors

    result = runner.invoke(cli, ["view", "Not in table"])
    assert result.exit_code != 0

    crontab_set(bad_filepath)
    result = runner.invoke(cli, ["view", "Test 7"])
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

    crontab_remove()


def test_cronberry_enter() -> None:
    """Tests the enter command."""
    job_title = "Manual"
    command = "1 2 3 4 5 echo Test"
    mailto = ""
    mailfrom = "root"
    path = "/some/specific/dir"
    cron_tz = "Etc/Universal"
    runner = CliRunner()

    args = [
        "enter",
        job_title,
        command,
        "--mailto",
        mailto,
        "--mailfrom",
        mailfrom,
        "--path",
        path,
        "--cron-tz",
        cron_tz,
    ]

    result = runner.invoke(cli, args)
    assert result.exit_code == 0

    _, output, _ = crontab_list()
    assert (
        output.decode()
        == f'# [{job_title}]\nMAILTO=""\nMAILFROM={mailfrom}\nPATH={path}\nSHELL=/bin/sh\nCRON_TZ={cron_tz}\n{command}\n'
    )

    result = runner.invoke(cli, ["enter", "Manual", "1 2 3 4 5 echo Yes"])
    assert result.exit_code != 0

    crontab_remove()


def test_cronberry_list() -> None:
    """Tests the list command."""
    src_filepath = "tests/tables/src.tab"
    runner = CliRunner()

    crontab_set(src_filepath)

    with open(src_filepath, encoding="utf-8") as srcfile:
        file_contents = srcfile.read()

    jobs_fulltext = ""
    jobs_shorttext = ""
    for job_index in range(4):
        if job_index != 0:
            jobs_fulltext += "\n"
            jobs_shorttext += "\n"
        job_lines = file_contents.split("\n")[job_index * 8 : (job_index * 8) + 7]
        job_fulltext = "\n".join(job_lines) + "\n"
        job_shorttext = f"{job_lines[0]}\n{job_lines[-1]}\n"
        jobs_fulltext += job_fulltext
        jobs_shorttext += job_shorttext

    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert result.output == jobs_shorttext

    result = runner.invoke(cli, ["list", "-v"])
    assert result.exit_code == 0
    assert result.output == jobs_fulltext

    crontab_remove()

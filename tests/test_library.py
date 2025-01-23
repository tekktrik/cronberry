# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for functionality related to library functionality."""

import copy
import os
import tempfile

import pytest

import cronberry


def test_read_crontab() -> None:
    """Tests whether crontabs can be read correctly."""
    jobs = cronberry.parse_crontab("tests/tables/new.tab")

    first_job = jobs[0]

    assert first_job.title == "Test 5"
    assert first_job.command == 'echo "Test 5!"'

    timing = first_job.timing
    assert isinstance(timing, cronberry.fields.ExplicitTiming)
    assert timing.minute == [8]
    assert timing.hour == [8]
    assert timing.day_of_month == [3]
    assert timing.month == [7]
    assert timing.day_of_week == [2]

    assert first_job.mailto == ""
    assert first_job.mailfrom == "root"
    assert first_job.path == "/home/peep"
    assert first_job.shell == "/bin/sh"
    assert first_job.cron_tz == "Etc/UTC"

    second_job = jobs[1]

    assert second_job.title == "Test 6"
    assert second_job.command == 'echo "Test 6!"'

    timing = second_job.timing
    assert isinstance(timing, cronberry.fields.ExplicitTiming)
    assert timing.minute == [1]
    assert timing.hour == [1]
    assert timing.day_of_month == [1]
    assert timing.month == [None]
    assert timing.day_of_week == [None]

    assert second_job.mailto == "people@somewhere.com"
    assert second_job.mailfrom == "person@elsewhere.com"
    assert second_job.path == "/home/someone"
    assert second_job.shell == "/bin/bash"
    assert second_job.cron_tz == "Etc/Universal"


def test_cronjob_equality() -> None:
    """Test the equality of two CronJobs."""
    jobs = cronberry.parse_crontab("tests/tables/src.tab")

    original_job = jobs[0]
    copy_job = copy.deepcopy(original_job)
    copy_job2 = copy.deepcopy(original_job)

    assert copy_job == original_job

    temp_timing: list[cronberry.fields.DiscreteValue] = list(copy_job.timing)
    temp_timing[3] = [7, 8]
    altered_timing = cronberry.fields.ExplicitTiming(*temp_timing)
    assert altered_timing != copy_job.timing

    copy_job.timing = altered_timing
    assert copy_job != original_job

    copy_job2.mailfrom = "notused@notused.com"

    assert copy_job2 != original_job

    assert altered_timing.__eq__(42) is False
    assert copy_job.__eq__(42) is False
    assert cronberry.fields.ValueRange(1, 2).__eq__(42) is False
    assert cronberry.fields.StepValues(1, 2).__eq__(42) is False


def test_cronjob_str() -> None:
    """Test the ability to convert a CronJob to its string equivalent."""
    jobs = cronberry.parse_crontab("tests/tables/src.tab")
    job = jobs[0]

    with open("tests/tables/src.tab", encoding="utf-8") as textfile:
        cronjob_text = textfile.read().split("\n")[6]
    assert str(job) == cronjob_text.strip()


def test_bad_parse() -> None:
    """Tests that an error is raised when a bad values is parsed."""
    with pytest.raises(ValueError):
        cronberry.CronJob._parse_discrete_value("#42")


def test_write_crontab() -> None:
    """Tests the ability to (over)write a crontab."""
    overwrite_jobs = cronberry.parse_crontab("tests/tables/new.tab")
    cronberry.write_cronjobs(overwrite_jobs)
    read_jobs = cronberry.parse_crontab()
    assert read_jobs == overwrite_jobs


def test_clear_cronjobs() -> None:
    """Tests the ability to clear cronjobs from a crontab."""
    overwrite_jobs = cronberry.parse_crontab("tests/tables/new.tab")
    cronberry.write_cronjobs(overwrite_jobs)
    cronberry.clear_cronjobs()
    assert not cronberry.parse_crontab()


def test_writeread_equality() -> None:
    """Tests that writing a cronjob then reading it is lossless."""
    file_jobs = cronberry.parse_crontab("tests/tables/new.tab")
    cronberry.write_cronjobs(file_jobs)
    nonfile_jobs = cronberry.parse_crontab()
    assert nonfile_jobs == file_jobs
    cronberry.clear_cronjobs()


def test_remove_cronjob() -> None:
    """Tests removing a cronjob from a file."""
    file_jobs = cronberry.parse_crontab("tests/tables/src.tab")
    cronberry.write_cronjobs(file_jobs)
    cronberry.remove_cronjob("Test 2")
    remaining_jobs = cronberry.parse_crontab()
    remaining_jobs_dict = {job.title: job for job in remaining_jobs}
    for index, (key, exp) in enumerate(
        (
            ("Test 1", True),
            ("Test 2", False),
            ("Test 3", True),
            ("Test 4", True),
        )
    ):
        assert (key in remaining_jobs_dict) == exp
        if exp:
            assert remaining_jobs_dict[key] == file_jobs[index]

    with pytest.raises(ValueError):
        cronberry.remove_cronjob("Test 2")

    cronberry.clear_cronjobs()


def test_add_cronjob() -> None:
    """Tests adding a cronjob from a file."""
    file_jobs = cronberry.parse_crontab("tests/tables/src.tab")
    add_file_jobs = cronberry.parse_crontab("tests/tables/new.tab")
    cronberry.write_cronjobs(file_jobs)

    combined_jobs = file_jobs + add_file_jobs
    cronberry.add_cronjobs(add_file_jobs)

    assert cronberry.parse_crontab() == combined_jobs

    # Test errors

    with pytest.raises(RuntimeError):
        cronberry.add_cronjobs(add_file_jobs, "tests/tables/bad.tab")

    add_file_jobs[0].command = "echo \"This wasn't here before!"

    with pytest.raises(ValueError):
        cronberry.add_cronjobs(add_file_jobs)

    add_file_jobs[0].title = "Test 6"
    cronberry.clear_cronjobs()

    with pytest.raises(ValueError):
        cronberry.add_cronjobs(add_file_jobs)

    cronberry.clear_cronjobs()


def test_save_crontab() -> None:
    """Tests the ability to save a crontab file."""
    file_jobs = cronberry.parse_crontab("tests/tables/src.tab")
    cronberry.write_cronjobs(file_jobs)
    temp_file = tempfile.NamedTemporaryFile(mode="r+", encoding="utf-8", delete=False)
    cronberry.save_crontab(temp_file.name)
    temp_file.seek(0)

    with open("tests/tables/src.tab", mode="r+") as origfile:
        orig_contents = origfile.read()
        save_contents = temp_file.read()

    assert save_contents == orig_contents

    os.remove(temp_file.name)


def test_cronjob_repr() -> None:
    """Tests CrobJob.__repr__()."""
    EXPECTED_REPR = "CronJob(title='Test 4', mailto='root', mailfrom='root', path='/home/someone', shell='/bin/sh', cron_tz='Etc/Universal', timing=ShorthandSyntax.YEARLY, command='echo \"Test 4!\"')"
    target_job = cronberry.parse_crontab("tests/tables/src.tab")[-1]
    assert repr(target_job) == EXPECTED_REPR

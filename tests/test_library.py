# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: MIT

"""Test file for functionality mostly related to reading crontabs."""

import copy
from typing import List

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


def test_cronjob_equality() -> None:
    """Test the equality of two CronJobs."""
    jobs = cronberry.parse_crontab("tests/tables/src.tab")

    original_job = jobs[0]
    copy_job = copy.deepcopy(original_job)

    assert copy_job == original_job

    temp_timing: List[cronberry.fields.DiscreteValue] = list(copy_job.timing)
    temp_timing[3] = [7, 8]
    altered_timing = cronberry.fields.ExplicitTiming(*temp_timing)
    assert altered_timing != copy_job.timing

    copy_job.timing = altered_timing
    assert copy_job != original_job

    assert altered_timing.__eq__(42) is False
    assert copy_job.__eq__(42) is False
    assert cronberry.fields.ValueRange(1, 2).__eq__(42) is False
    assert cronberry.fields.StepValues(1, 2).__eq__(42) is False


def test_cronjob_str() -> None:
    """Test the ability to convert a CronJob to its string equivalent."""
    jobs = cronberry.parse_crontab("tests/tables/src.tab")
    job = jobs[0]

    with open("tests/tables/src.tab", encoding="utf-8") as textfile:
        cronjob_text = textfile.read().split("\n")[1]
    assert str(job) == cronjob_text.strip()


def test_bad_parse() -> None:
    """Tests that an error is raised when a bad values is parsed."""
    with pytest.raises(ValueError):
        cronberry.CronJob._parse_discrete_value("#42")


def test_cronjob_reduce() -> None:
    """Tests that the CronJob reduce functionality works."""
    with pytest.raises(NotImplementedError):
        job = cronberry.CronJob(
            "Test", cronberry.fields.ShorthandSyntax.DAILY, 'echo "Test!'
        )
        job.reduce()


def test_empty_crontab() -> None:
    """Tests that the ability to empty the crontab."""
    overwrite_jobs = cronberry.parse_crontab("tests/tables/new.tab")
    cronberry.overwrite_crontab(overwrite_jobs)
    read_jobs = cronberry.parse_crontab()
    assert read_jobs == overwrite_jobs

    cronberry.clear_cronjobs()
    assert not cronberry.parse_crontab()


def test_writeread_equality() -> None:
    """Tests that writing a cronjob then reading it is lossless."""
    # cronberry.

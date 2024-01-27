# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: MIT

"""CLI for working with multiple cron jobs within a single cron table."""

import functools
import os
import re
import subprocess
import tempfile
from typing import (
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)

from typing_extensions import TypeAlias

from . import fields

CRONJOB_REGEX = r"^# \[(.*)]\n(.*)$"


Timing: TypeAlias = Union[fields.ShorthandSyntax, fields.ExplicitTiming]
"""Type alias for any kind of timing specification."""

Command: TypeAlias = str
"""Type alias for the cron job command."""


class CronJob:
    """Cron job representation."""

    def __init__(self, title: str, timing: Timing, command: Command):
        """Initialize the cron job object."""
        self.title = title
        self.timing = timing
        self.command = command

    def reduce(self) -> None:
        """Reduce duplicate timing instructions."""
        raise NotImplementedError("This feature is not yet implemented.")

    def __str__(self) -> str:
        """Representation of the cron job as a string (cron job)."""
        return f"{self.timing} {self.command}"

    def __repr__(self) -> str:
        """Printable representation of the cron job."""
        return f"CronJob(title={self.title!r}, timing={self.timing}, command={self.command!r})"

    def __eq__(self, __value: object) -> bool:
        """Check equality."""
        if isinstance(__value, CronJob):
            if (
                self.title == __value.title
                and self.timing == __value.timing
                and self.command == __value.command
            ):
                return True
        return False

    @staticmethod
    def parse_cron_text(cron_text: str) -> Tuple[Timing, Command]:
        """Parse a cron job in textual format."""
        try:
            shorthand = cron_text.split(" ")[0]
            timing = fields.ShorthandSyntax(shorthand)
            remaining_cron_texts = cron_text.split()[1:]
            remaining_cron_text = " ".join(remaining_cron_texts)
        except ValueError:
            timing_list = []
            remaining_cron_text = cron_text
            for _ in range(5):
                comp, _, remaining_cron_text = remaining_cron_text.partition(" ")
                parsed_comp = CronJob._parse_discrete_value(comp)
                timing_list.append(parsed_comp)
            timing = fields.ExplicitTiming(*timing_list)
        return timing, remaining_cron_text

    @classmethod
    def from_job(cls, job_text: str, title: str) -> "CronJob":
        """Create a CronJob from a cron job in texual format with a provided title."""
        timing, command = cls.parse_cron_text(job_text)
        return cls(title, timing, command)

    @staticmethod
    def _parse_discrete_value(value: str) -> List[fields.DiscreteValue]:
        """Parse the timing field values, recursively if needed."""
        values = []
        list_values = value.split(",")
        for list_value in list_values:
            if "/" in list_value:
                duration, frequency = list_value.split("/")
                dur_comp = CronJob._parse_discrete_value(duration)[0]
                freq_comp = CronJob._parse_discrete_value(frequency)[0]
                values.append(fields.StepValues(dur_comp, freq_comp))
            elif "-" in list_value:
                start, end = list_value.split("-")
                start_comp = CronJob._parse_discrete_value(start)[0]
                end_comp = CronJob._parse_discrete_value(end)[0]
                values.append(fields.ValueRange(start_comp, end_comp))
            elif list_value == "*":
                values.append(None)
            else:
                try:
                    values.append(int(list_value))
                except ValueError as err:
                    raise ValueError(
                        f"Could not parse timing component: {list_value}"
                    ) from err

        return values

    def to_job(self) -> Tuple[str, str]:
        """Get the job syntax, with the accompanying title."""
        if isinstance(self.timing, fields.ShorthandSyntax):
            timing_text = self.timing.value
        else:
            timing_text = str(self.timing)
        return timing_text, self.command


def parse_crontab(filepath: Optional[str] = None) -> List[CronJob]:
    """Parse the user's crontab."""
    if filepath is None:
        proc = subprocess.Popen(
            ["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        output, _ = proc.communicate()
        text = output.decode()
    else:
        with open(filepath, encoding="utf-8") as jobfile:
            text = jobfile.read()

    re_matches: List[Tuple[str, str]] = re.findall(CRONJOB_REGEX, text, re.M)
    if not re_matches:
        return tuple()

    jobs = []
    for title, cron_text in re_matches:
        job = CronJob.from_job(cron_text, title)
        jobs.append(job)
    return jobs


def add_cronjobs(
    jobs: Iterable[CronJob], filepath: Optional[str] = None, *, overwrite: bool = False
) -> None:
    """Add the cron jobs to a crontab."""
    dest_crontab = parse_crontab(filepath)
    dest_titles = {dest_job.title for dest_job in dest_crontab}
    src_titles = {src_job.title for src_job in jobs}

    if len(src_titles) != len(jobs):
        raise ValueError("Cron jobs to be written contain duplicate titles")

    if len(dest_titles) != len(dest_crontab):
        raise RuntimeError(
            "Destination crontab already contains multiple entries, please remove duplicate"
        )

    has_overlap = dest_titles != dest_titles.difference(src_titles)
    if has_overlap and not overwrite:
        raise ValueError(
            "Destination crontab already contains title(s) provided, please remove duplicates"
        )

    writeable_jobs = {job.title: job for job in dest_crontab}
    add_jobs = {job.title: job for job in jobs}
    writeable_jobs.update(add_jobs)

    _update_crontab(writeable_jobs, filepath)


def remove_cronjobs(job_names: Iterable[str], filepath: Optional[str] = None) -> None:
    """Remove the cronjobs from a crontab."""
    dest_crontab = parse_crontab(filepath)
    current_jobs = {job.title: job for job in dest_crontab}

    for job_name in job_names:
        if job_name not in current_jobs:
            raise ValueError(
                f"Cron job '{job_name}' does not exist in the destination crontab"
            )
        del current_jobs[job_name]

    _update_crontab(current_jobs, filepath)


def _update_crontab(jobs: Dict[str, CronJob], filepath: Optional[str] = None) -> None:
    """Update the crontab file with the new contents."""
    tabtext = ""
    for index, job in enumerate(jobs.values()):
        if index != 0:
            tabtext += "\n"
        cron_timing, cron_cmd = job.to_job()
        tabtext += f"# [{job.title}]\n{cron_timing} {cron_cmd}\n"

    write_file = (
        functools.partial(tempfile.NamedTemporaryFile, delete=False)
        if filepath is None
        else functools.partial(open, filepath)
    )

    with write_file(mode="w", encoding="utf-8") as destfile:
        output_filepath = destfile.name
        destfile.write(tabtext)

    if filepath is None:
        proc = subprocess.Popen(
            ["crontab", destfile.name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.communicate()
        if proc.returncode:
            raise OSError("Could not finalize updating the crontab")


def clear_cronjobs(filepath: Optional[str] = None):
    """Clear all of the cronjobs in a crontab."""
    _update_crontab({}, filepath)


def overwrite_crontab(jobs: Iterable[CronJob], filepath: Optional[str] = None) -> None:
    """Overwrite a specific crontab with provided jobs."""
    job_dict = {job.title: job for job in jobs}
    print(job_dict)
    _update_crontab(job_dict, filepath)

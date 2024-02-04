# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: MIT

"""Library for working with multiple cron jobs within a single cron table."""

import functools
import getpass
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

CRONJOB_REGEX = r"^# \[(.*)]\n(.*)$\n(.*)$\n(.*)$\n(.*)$\n(.*)$\n(.*)$\n"
CURRENT_USER = getpass.getuser()
CURRENT_USER_PATH = os.path.expanduser("~")


Timing: TypeAlias = Union[fields.ShorthandSyntax, fields.ExplicitTiming]
"""Type alias for any kind of timing specification."""

Command: TypeAlias = str
"""Type alias for the cron job command."""


class CronJob:
    """Cron job representation."""

    def __init__(  # noqa: PLR0913
        self,
        title: str,
        timing: Timing,
        command: Command,
        *,
        mailto: str = CURRENT_USER,
        mailfrom: str = "root",
        path: str = CURRENT_USER_PATH,
        shell: str = "/bin/sh",
        cron_tz: str = "Etc/UTC",
    ):
        """Initialize the cron job object."""
        self.title = title
        self.timing = timing
        self.command = command
        self.mailto = mailto
        self.mailfrom = mailfrom
        self.path = path
        self.shell = shell
        self.cron_tz = cron_tz

    def __str__(self) -> str:
        """Representation of the cron job as a string (cron job)."""
        return f"{self.timing} {self.command}"

    def __repr__(self) -> str:
        """Printable representation of the cron job."""
        return f"CronJob(title={self.title!r}, mailto={self.mailto!r}, mailfrom={self.mailfrom!r}, path={self.path!r}, shell={self.shell!r}, cron_tz={self.cron_tz!r}, timing={self.timing}, command={self.command!r})"

    def __eq__(self, __value: object) -> bool:
        """Check equality."""
        if isinstance(__value, CronJob):
            if (
                self.title == __value.title
                and self.timing == __value.timing
                and self.command == __value.command
                and self.mailto == __value.mailto
                and self.mailfrom == __value.mailfrom
                and self.path == __value.path
                and self.shell == __value.shell
                and self.cron_tz == __value.cron_tz
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
    def from_job(cls, job_text: str, title: str, envvars: Dict[str, str]) -> "CronJob":
        """Create a CronJob from a cron job in texual format with a provided title."""
        timing, command = cls.parse_cron_text(job_text)
        return cls(title, timing, command, **envvars)

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

    def to_job(self) -> Tuple[str, str, Dict[str, str]]:
        """Get the job syntax, with the accompanying title."""
        if isinstance(self.timing, fields.ShorthandSyntax):
            timing_text = self.timing.value
        else:
            timing_text = str(self.timing)
        envvars = {
            "mailto": self.mailto,
            "mailfrom": self.mailfrom,
            "path": self.path,
            "shell": self.shell,
            "cron_tz": self.cron_tz,
        }
        for key, value in envvars.items():
            if value == "":
                envvars[key] = '""'
        return timing_text, self.command, envvars

    def to_file_text(self) -> str:
        """Get the cron job as it would be written in the crontab."""
        jobtext = ""
        cron_timing, cron_cmd, envvars = self.to_job()
        jobtext += f"# [{self.title}]\n"
        for key, value in envvars.items():
            write_value = value if value != "" else '""'
            jobtext += f"{key.upper()}={write_value}\n"
        jobtext += f"{cron_timing} {cron_cmd}\n"
        return jobtext


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
        return []

    jobs = []
    for items in re_matches:
        envvars = {}
        for item in items[1:6]:
            item_name, item_value = item.split("=")
            envvar_name = item_name.rstrip().lower()
            write_value = "" if item_value in ('""', "''") else item_value
            envvars[envvar_name] = write_value.lstrip()
        job = CronJob.from_job(items[6], items[0], envvars)
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


def remove_cronjob(
    job_name: str,
    filepath: Optional[str] = None,
    *,
    ignore_missing: bool = False,
) -> None:
    """Remove the cronjobs from a crontab."""
    dest_crontab = parse_crontab(filepath)
    current_jobs = {job.title: job for job in dest_crontab}

    if job_name not in current_jobs and not ignore_missing:
        raise ValueError(
            f"Cron job '{job_name}' does not exist in the destination crontab"
        )
    elif job_name in current_jobs:
        del current_jobs[job_name]

    _update_crontab(current_jobs, filepath)


def _update_crontab(jobs: Dict[str, CronJob], filepath: Optional[str] = None) -> None:
    """Update the crontab file with the new contents."""
    tabtext = ""
    for index, job in enumerate(jobs.values()):
        if index != 0:
            tabtext += "\n"
        tabtext += job.to_file_text()

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
            ["crontab", output_filepath],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.communicate()
        os.remove(output_filepath)


def clear_cronjobs(filepath: Optional[str] = None):
    """Clear all of the cronjobs in a crontab."""
    _update_crontab({}, filepath)


def write_cronjobs(jobs: Iterable[CronJob], filepath: Optional[str] = None) -> None:
    """(Over)write a specific crontab with provided jobs."""
    job_dict = {job.title: job for job in jobs}
    _update_crontab(job_dict, filepath)


def save_crontab(dest_filepath: str) -> None:
    """Save the current user's crontab to a file."""
    proc = subprocess.Popen(
        ["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    output, _ = proc.communicate()
    with open(dest_filepath, mode="wb") as outfile:
        outfile.write(output)

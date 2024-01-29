# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: MIT

"""CLI for working with cronberry library."""

from typing import Optional, Tuple

import click

import cronberry


@click.group()
def cli() -> None:
    """Entry point for the CLI."""


@cli.command()
@click.argument(
    "crontab",
    type=click.Path(dir_okay=False, resolve_path=True),
)
@click.option(
    "-f",
    "--filepath",
    type=click.Path(dir_okay=False, resolve_path=True),
    default=None,
    help="Filepath to use instead of the user's crontab",
)
@click.option(
    "-o",
    "--overwrite/--no-overwrite",
    default=False,
    help="Overwrite if the job currently exists in the crontab",
)
def add(crontab: str, filepath: Optional[str], overwrite: bool) -> None:
    """Add a job from CRONTAB to the crontab being used."""
    jobs = cronberry.parse_crontab(crontab)
    cronberry.add_cronjobs(jobs, filepath, overwrite=overwrite)


@cli.command()
@click.argument(
    "job_titles",
    nargs=-1,
)
@click.option(
    "-f",
    "--filepath",
    type=click.Path(dir_okay=False, resolve_path=True),
    default=None,
    help="Filepath to use instead of the user's crontab",
)
@click.option(
    "-i",
    "--ignore-missing/--no-ignore-missing",
    default=False,
    help="Ignore jobs missing from the crontab",
)
def remove(
    job_titles: Tuple[str], filepath: Optional[str], ignore_missing: bool
) -> None:
    """Remove JOB_TITLES from the crontab being used."""
    unique_titles = set(job_titles)
    if len(unique_titles) != len(job_titles):
        raise click.ClickException("Duplicate job titles provided")
    for job_title in job_titles:
        try:
            cronberry.remove_cronjob(job_title, filepath, ignore_missing=ignore_missing)
        except ValueError:
            raise click.ClickException(
                f"Job title {job_title} does not exist in the crontab"
            )


@cli.command()
@click.argument(
    "filepath",
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
)
def save(filepath: str) -> None:
    """Save the current crontab being used to FILEPATH."""
    cronberry.save_crontab(filepath)


@cli.command()
@click.option(
    "-f",
    "--filepath",
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    default=None,
    help="Filepath to use instead of the user's crontab",
)
def clear(filepath: Optional[str]) -> None:
    """Clear the current crontab being used."""
    cronberry.clear_cronjobs(filepath)


@cli.command()
@click.argument("job_title")
@click.option(
    "-f",
    "--filepath",
    type=click.Path(dir_okay=False, resolve_path=True),
    default=None,
    help="Filepath to use instead of the user's crontab",
)
def job(job_title: str, filepath: Optional[str]) -> None:
    """Get the cronbjob JOB_TITLE from a crontab."""
    all_jobs = cronberry.parse_crontab(filepath)
    selected_jobs = [any_job for any_job in all_jobs if any_job.title == job_title]
    if len(selected_jobs) < 1:
        raise click.ClickException(
            f"Job title {job_title} was not present in the crontab"
        )
    elif len(selected_jobs) > 1:
        raise click.ClickException(
            f"Job title {job_title} was found multiple times in the crontab"
        )
    selected_job = selected_jobs[0]
    formatted_command = f"{selected_job.timing!s} {selected_job.command!s}"
    click.echo(formatted_command)


@cli.command()
@click.option(
    "-f",
    "--filepath",
    type=click.Path(dir_okay=False, resolve_path=True),
    default=None,
    help="Filepath to use instead of the user's crontab",
)
def jobs(filepath: Optional[str]) -> None:
    """Get the jobs from a specific crontab."""
    jobs = cronberry.parse_crontab(filepath)
    for job in jobs:
        click.echo(job.title)

.. image:: https://img.shields.io/pypi/pyversions/cronberry
   :alt: PyPI - Python Version

.. image:: https://img.shields.io/github/actions/workflow/status/tekktrik/cronberry/push.yml
   :alt: GitHub Actions Workflow Status

.. image:: https://img.shields.io/codecov/c/github/tekktrik/cronberry
   :alt: Codecov

.. image:: https://img.shields.io/readthedocs/cronberry
   :alt: Read the Docs

.. image:: https://img.shields.io/pypi/wheel/cronberry
   :alt: PyPI - Wheel

.. image:: https://img.shields.io/pypi/dm/cronberry
   :alt: PyPI - Downloads

cronberry
---------

Library and CLI for working with multiple cron jobs within a single cron table

Example
^^^^^^^

.. code-block:: shell

    # The following examples assume you have the following example
    # crontab file jobs.tab.  Note that due to the way the examples
    # are laid out, they will not run in the order shown below.
    #
    # jobs.tab contents:
    # # [Frequent Job]
    # * * * * * echo "This runs frequently"
    #
    # # [Specific Job]
    # 1 2 3 4 5 echo "This runs... oddly specifically

    # Add a job to the crontab
    cronberry add jobs.tab

    # Add a specific job to the crontab
    cronberry add jobs.tab --title "Specific Job"

    # Remove a job from the crontab
    cronberry remove "Specific Job"

    # Clear the current crontab
    cronberry clear

    # Save the current crontab to a file
    cronberry save "saved.tab"

    # Get the specific job with the given title, from a dif
    cronberry job "Frequent Job"
    # Returns:
    # * * * * * echo "This runs frequently"

    # Get all the job titles from the crontab
    cronberry jobs
    # Returns:
    # Frequent Job
    # Specific Job

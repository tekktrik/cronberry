# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: MIT
#
# The following examples assume you have the following example
# crontab file jobs.tab.  Note that due to the way the examples
# are laid out, they will not run in the order shown below.
#
# jobs.tab contents:
# # [Frequent Job]
# MAILTO=user
# MAILFROM=root
# PATH=/home/user
# SHELL=/bin/sh
# CRON_TZ=/Etc/UTC
# * * * * * echo "This runs frequently"
#
# # [Specific Job]
# MAILTO=""
# MAILFROM="user"
# PATH=/some/specific/dir
# SHELL=/bin/bash
# CRON_TZ=/Etc/Universal
# 1 2 3 4 5 echo "This runs... oddly specifically

# Add a job to the crontab
cronberry add jobs.tab

# Add a specific job to the crontab
cronberry add jobs.tab --title "Specific Job"

# Add a job manually to the crontab
cronberry enter "Manually Added" '5 4 3 2 1 echo "Custom cronjob"'

# You can also pass environment variables
cronberry enter "With Env Vars" '1 1 2 3 5 echo "This uses bash!"' --shell /bin/bash

# Remove a job from the crontab
cronberry remove "Specific Job"

# Clear the current crontab
cronberry clear

# Save the current crontab to a file
cronberry save "saved.tab"

# Get the specific job with the given title, from a diff
cronberry view "Frequent Job"
# Returns:
# * * * * * echo "This runs frequently"

# See the environment variables of a given job as well
cronberry view "Frequect Job" -v
# Returns:
# [Frequent Job]
# MAILTO=user
# MAILFROM=root
# PATH=/home/user
# SHELL=/bin/sh
# CRON_TZ=/Etc/UTC
# * * * * * echo "This runs frequently"

# See all the jobs in crontab (you can also use the -v flag)
cronberry list
# Returns:
# jobs.tab contents:
# * * * * * echo "This runs frequently"
#
# # [Specific Job]
# 1 2 3 4 5 echo "This runs... oddly specifically

# Get all the job titles from the crontab
cronberry jobs
# Returns:
# Frequent Job
# Specific Job

# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: MIT
#
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

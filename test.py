import cronberry
import pprint

orig_jobs = cronberry.parse_crontab()

new_jobs = cronberry.parse_crontab("newcrontab2.tab")

#cronberry.add_cronjobs(new_jobs, "newcrontab.tab")

cronberry.remove_cronjobs(("Test 5",), "newcrontab.tab")

import os
import sys
from adjutant import test_settings
from django.core.management import execute_from_command_line

test_settings.ADDITIONAL_APPS.append("odoo_actions")
test_settings.ADDITIONAL_APPS.append("odoo_views")

# signup
test_settings.ACTIVE_TASKVIEWS.remove("CreateProject")
test_settings.ACTIVE_TASKVIEWS.append("OpenStackSignUp")

# contacts and account details
test_settings.ACTIVE_TASKVIEWS.append("AccountDetailsManagement")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adjutant.settings")

execute_from_command_line(sys.argv)

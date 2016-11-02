import os
import sys
from stacktask import test_settings
from django.core.management import execute_from_command_line

test_settings.ADDITIONAL_APPS.append("odoo_actions")
test_settings.ADDITIONAL_APPS.append("odoo_views")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stacktask.settings")

execute_from_command_line(sys.argv)

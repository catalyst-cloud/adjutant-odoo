import django
import sys
from django.conf import settings
from django.test.runner import DiscoverRunner
from stacktask import test_settings

test_settings.ADDITIONAL_APPS.append("odoo_actions")

settings.configure(**test_settings.conf_dict)

django.setup()
test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['odoo_actions'])
if failures:
    sys.exit(failures)

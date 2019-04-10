from django.conf import settings

from odoo_actions.odoo_client.client import OdooClient

DEFAULT_PHYSICAL_ADDRESS_CONTACT_NAME = "Physical Address"


cached_client = None


def get_odoo_client():
    global cached_client
    if not cached_client:
        # get odoo auth setting from settings
        conf = settings.PLUGIN_SETTINGS.get(
            "adjutant-odoo", {}).get('odoo_client', {})
        # setup client
        cached_client = OdooClient(conf)

    return cached_client

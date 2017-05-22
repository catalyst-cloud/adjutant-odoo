import odoorpc

from django.conf import settings

from .projects import CloudProjectManager
from .credits import CloudCreditManager
from .partners import PartnerManager
from .project_relationships import ProjectRelationshipManager
from .countries import CountryManager

cached_client = None


class OdooClient(object):
    """OpenStack-like wrapping for OdooRPC

    This client serves as a simple wrapper around
    OdooRPC to let us pretend this works like an
    OpenStack client, and to hide away some of the
    odd ways OdooRPC works.
    """

    def __init__(self, config):
        odoo_conf = config.get('odoo', {})
        self._odoo = odoorpc.ODOO(
            odoo_conf.get('hostname'),
            protocol=odoo_conf.get('protocol'),
            port=int(odoo_conf.get('port')),
            version=odoo_conf.get('version'))

        self._odoo.login(
            odoo_conf.get('database'),
            odoo_conf.get('user'),
            odoo_conf.get('password'))

        # TODO(adriant): Rename tenant to project once renamed in odoo:
        self._Project = self._odoo.env['cloud.tenant']
        self._Partner = self._odoo.env['res.partner']
        self._Credit = self._odoo.env['cloud.credit']
        self._PartnerRelationship = self._odoo.env['cloud.tenant_partner']
        self._Country = self._odoo.env['res.country']

        # Now setup the managers:
        self.projects = CloudProjectManager(self)
        self.credits = CloudCreditManager(self)
        self.partners = PartnerManager(self)
        self.project_relationships = ProjectRelationshipManager(self)
        self.countries = CountryManager(self)


def get_odoo_client():
    global cached_client
    if not cached_client:
        # get odoo auth setting from settings
        conf = settings.PLUGIN_SETTINGS.get(
            "adjutant-odoo", {}).get('odoorpc', {})
        # setup client
        cached_client = OdooClient(conf)

    return cached_client

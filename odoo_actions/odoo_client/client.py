import odoorpc

from .projects import CloudProjectManager
from .credits import CloudCreditManager
from .partners import PartnerManager
from .project_relationships import ProjectRelationshipManager
from .countries import CountryManager


class OdooClient(object):
    """OpenStack-like wrapping for OdooRPC

    This client serves as a simple wrapper around
    OdooRPC to let us pretend this works like an
    OpenStack client, and to hide away some of the
    odd ways OdooRPC works.
    """

    def __init__(self, config):
        odoo_conf = config.get('odoorpc', {})
        self._odoorpc = odoorpc.ODOO(
            odoo_conf.get('hostname'),
            protocol=odoo_conf.get('protocol'),
            port=int(odoo_conf.get('port')),
            version=odoo_conf.get('version'))

        self._odoorpc.login(
            odoo_conf.get('database'),
            odoo_conf.get('user'),
            odoo_conf.get('password'))

        # TODO(adriant): Rename tenant to project once renamed in odoo:
        self._Project = self._odoorpc.env['cloud.tenant']
        self._Partner = self._odoorpc.env['res.partner']
        self._Credit = self._odoorpc.env['cloud.credit']
        self._PartnerRelationship = self._odoorpc.env['cloud.tenant_partner']
        self._Country = self._odoorpc.env['res.country']

        self._MailMessage = self._odoorpc.env['mail.message']

        # Now setup the managers:
        self.projects = CloudProjectManager(self)
        self.credits = CloudCreditManager(self)
        self.partners = PartnerManager(self)
        self.project_relationships = ProjectRelationshipManager(self)
        self.countries = CountryManager(self)

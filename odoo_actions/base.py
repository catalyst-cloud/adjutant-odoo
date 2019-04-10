# Copyright (C) 2018 Catalyst IT Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from adjutant.api.v1.utils import create_notification

from odoo_actions import odoo_client


class OdooModelsIncorrect(BaseException):
    """Cloud data in Odoo is incorrect."""


class OdooMixin(object):

    def _validate_project_exists(self):
        """ Validates a project exists in odoo

        Expects:
            - self.project_id
        Sets:
            - self.odoo_project = <odoo project browsable model>
            - self.odoo_project_id
            - self.odoo_project_name
        """
        odooclient = odoo_client.get_odoo_client()
        try:
            search = [['tenant_id', '=', self.project_id]]
            project = odooclient.projects.list(search)[0]
            self.odoo_project = project
            self.odoo_project_id = project.id
            self.odoo_project_name = project.name
            self.add_note('Odoo project %s (%s) exists.'
                          % (self.odoo_project_name, self.odoo_project_id))
            return True
        except IndexError:
            self.add_note('Project %s does not exist in odoo'
                          % self.project_id)
        return False

    def _validate_partner_exists(self):
        """ Validates that a partner with the given id exists in odoo

        Expects:
            - self.partner_id
        Sets:
            - self.partner
        """
        odooclient = odoo_client.get_odoo_client()
        try:
            self.partner = odooclient.partners.get(self.partner_id)[0]
            self.add_note('Contact id %s exists. (%s)'
                          % (self.partner_id, self.partner.name))
            return True
        except IndexError:
            self.add_note('Partner with id %s does not exist.'
                          % self.partner_id)
        return False

    def _get_parent_id(self):
        """Get ID of the owner (company) for the project

        Expects:
            - self.project_id
            - self.odoo_project_id
        Sets:
            - self.odoo_owner
        """
        if getattr(self, 'odoo_owner', None):
            return self.odoo_owner.id

        odooclient = odoo_client.get_odoo_client()
        search = [
            ['cloud_tenant', '=', self.odoo_project_id],
            ['contact_type', '=', 'owner']
        ]
        all_relations = odooclient.project_relationships.list(search)
        if len(all_relations) > 1:
            note = ("WARNING! More than one owner found for '%s'"
                    % self.project_id)
            self.add_note(note)
            if not self.get_cache('multi_owner_error'):
                create_notification(
                    self.action.task, {'errors': [note]}, error=True)
                self.set_cache('multi_owner_error', True)

        if len(all_relations) < 1:
            note = ("WARNING! No owner found for '%s'" % self.project_id)
            self.add_note(note)
            if not self.get_cache('no_owner_error'):
                create_notification(
                    self.action.task, {'errors': [note]}, error=True)
                self.set_cache('no_owner_error', True)
            return None

        self.odoo_owner = all_relations[0].partner_id
        self.add_note("Found owner: %s" % self.odoo_owner.name)
        return self.odoo_owner.id

    def _get_odoo_project_owner(self):
        """
        Get the project owner partner.

        Expects:
            - self.project_id
        Sets:
            - self.odoo_project = <odoo project browsable model>
            - self.project_owner = <odoo partner browsable model>
        Returns: <odoo partner browsable model>
        """
        if not getattr(self, 'project_owner', None):
            odooclient = odoo_client.get_odoo_client()

            projects = odooclient.projects.list(
                [('tenant_id', '=', self.project_id)])
            if len(projects) == 0:
                raise OdooModelsIncorrect(
                    'Project "%s" is not set up in OpenERP.' % self.project_id)
            if len(projects) > 1:
                raise OdooModelsIncorrect(
                    'More than one project "%s" is set up in OpenERP.'
                    % self.project_id)

            self.odoo_project = projects[0]
            self.add_note("Odoo Project ID: %s" % self.odoo_project.id)

            project_rels = odooclient.project_relationships.list([
                ('cloud_tenant', '=', self.odoo_project.id),
                ('contact_type', '=', 'owner'),
            ])

            if len(project_rels) == 0:
                raise OdooModelsIncorrect(
                    'Project "%s" has no owner!' % self.project_id)
            elif len(project_rels) > 1:
                raise OdooModelsIncorrect(
                    'Project "%s" has more than one owner!' % self.project_id)

            self.project_owner = project_rels[0].partner_id

        self.add_note("Found owner: %s" % self.project_owner.name)
        return self.project_owner

    def _validate_owner_is_company(self):
        """
        Check if owner is a company.

        Expects:
            - self.individual_tag_id
        Returns: boolean
        """
        try:
            owner = self._get_odoo_project_owner()
            tags = [tag.id for tag in owner.category_id]
            if self.individual_tag_id in tags:
                self.add_note(
                    "Owner has individual tag.")
                return False
            else:
                self.add_note("Project owner is company.")
                return True
        except OdooModelsIncorrect:
            self.add_note("Project Owner not found")
        return False

    def _validate_odoo_owner(self):
        """
        Confirm owner is correctly setup for project.

        Returns: boolean
        """
        try:
            self._get_odoo_project_owner()
            return True
        except OdooModelsIncorrect:
            self.add_note("Could not find odoo owner")
            return False

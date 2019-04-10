# Copyright (C) 2015 Catalyst IT Ltd
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

from django.conf import settings
from django.utils import timezone

from rest_framework.response import Response

from adjutant.api.models import Task
from adjutant.api import utils
from adjutant.api.v1 import tasks
from adjutant.api.v1.utils import create_notification, add_task_id_for_roles
from adjutant.common import user_store

from odoo_actions import odoo_client
from odoo_views.utils import not_reseller_customer


class OpenStackSignUp(tasks.TaskView):

    default_actions = ['NewClientSignUpAction', 'NewProjectSignUpAction']
    task_type = 'signup'

    def get(self, request):
        """
        The OpenStackSignUp endpoint does not support GET.
        This returns a 404.
        """
        return Response(status=404)

    def post(self, request, format=None):
        """
        Unauthenticated endpoint bound primarily to NewClientSignUp
        and NewProjectSignUp.

        This task requires approval, so this will validate
        incoming data and create a task to be approved
        later.
        """
        self.logger.info("(%s) - Starting new OpenStackSignUp task." %
                         timezone.now())

        class_conf = settings.TASK_SETTINGS.get(self.task_type, {})

        # we need to set the region the resources will be created in:
        request.data['region'] = class_conf.get('default_region')
        # Will a default network be setup:
        request.data['setup_network'] = class_conf.get('setup_network', False)
        # domain_id for new project:
        request.data['domain_id'] = class_conf.get(
            'default_domain_id', 'default')
        # parent_id for new project, if null defaults to domain:
        request.data['parent_id'] = class_conf.get('default_parent_id')

        processed, status = self.process_actions(request)

        errors = processed.get('errors', None)
        if errors:
            self.logger.info("(%s) - Validation errors with task." %
                             timezone.now())
            return Response(errors, status=status)

        notes = {
            'notes':
                ['New OpenStackSignUp task.']
        }
        create_notification(processed['task'], notes)
        self.logger.info("(%s) - Task created." % timezone.now())

        response_dict = {'notes': ['Sign-up submitted.']}

        add_task_id_for_roles(request, processed, response_dict, ['admin'])

        return Response(response_dict, status=status)


def get_address_dict(odoo_owner):
    odooclient = odoo_client.get_odoo_client()
    if odoo_owner['country_id']:
        country = odooclient.countries.get(
            odoo_owner['country_id'][0], read=True)[0]
    else:
        country = {}
    return {
        'address_1': odoo_owner['street'] or "",
        'address_2': odoo_owner['street2'] or "",
        'postal_code': odoo_owner['zip'] or "",
        'city': odoo_owner['city'] or "",
        'country': country.get('code', ""),
        'country_name': country.get('name', ""),
    }


def is_root_project(project_id):
    id_manager = user_store.IdentityManager()
    project = id_manager.get_project(project_id)
    if project.parent_id:
        parent = id_manager.get_project(project.parent_id)
        if not parent.is_domain:
            return False
    return True


class AccountDetailsManagement(tasks.TaskView):
    default_actions = ['UpdateAccountDetailsAction', ]
    task_type = 'update_account_details'

    @utils.project_admin
    @not_reseller_customer
    def get(self, request):
        """ View Account Details """
        odooclient = odoo_client.get_odoo_client()
        project_id = request.keystone_user['project_id']

        project_search = [('tenant_id', '=', project_id)]

        try:
            odoo_project_id = odooclient.projects.list(
                project_search, read=True)[0]['id']
        except IndexError:
            return Response({'errors': ['Project not found']}, status=404)

        search = [
            ("cloud_tenant", "=", odoo_project_id),
            ("contact_type", "=", "owner"),
        ]
        owner_id = odooclient.project_relationships.list(
            search, read=True)[0]['partner_id'][0]
        owner = odooclient.partners.get(owner_id, read=True)[0]
        address = get_address_dict(owner)

        account_type = 'organisation'
        individual_tag_id = settings.PLUGIN_SETTINGS.get(
            'adjutant-odoo', {}).get("individual_tag_id", None)
        if individual_tag_id in [tag for tag in owner['category_id']]:
            account_type = 'individual'

        project_tasks = Task.objects.filter(
            project_id=project_id,
            task_type=AccountDetailsManagement.task_type,
            completed=0,
            cancelled=0).order_by('-created_on')

        address_tasks = []

        for task in project_tasks:
            task_data = {}
            for action in task.actions:
                task_data.update(action.action_data)

            if task_data['country'] != address['country']:
                address_tasks.append(task_data)

        # TODO(adriant): include if is root project (as can only edit address
        # for root projects)
        response_dict = {
            'account_type': account_type,
            'address': address,
            'customer_name': owner['name'],
            'is_root_project': is_root_project(project_id),
        }

        if address_tasks:
            response_dict['pending_details'] = address_tasks[0]
        return Response(response_dict)

    @utils.project_admin
    @not_reseller_customer
    def post(self, request):
        """ Update Account Details """
        self.logger.info("(%s) - Starting new AccountDetailsManageTask task." %
                         timezone.now())

        request.data['project_id'] = request.keystone_user['project_id']

        processed, status = self.process_actions(request)
        errors = processed.get('errors', None)
        if errors:
            self.logger.info("(%s) - Validation errors with task." %
                             timezone.now())
            return Response(errors, status=status)

        # cancel any old tasks
        project_tasks = Task.objects.filter(
            project_id=request.keystone_user['project_id'],
            task_type=self.task_type,
            completed=0,
            cancelled=0).exclude(uuid=processed['task'].uuid)

        for task in project_tasks:
            task.cancelled = True
            task.save()

        if processed.get('auto_approved', False):
            response_dict = {'notes': ['Updated Account Address']}
            return Response(response_dict, status=status)

        task = processed['task']
        action_models = task.actions
        valid = all([act.valid for act in action_models])
        if not valid:
            return Response({'errors': ['Actions invalid.']}, 400)

        # Action needs to be manually approved
        notes = {
            'notes':
                ['New task for AddressManagement.']
        }

        create_notification(processed['task'], notes)
        self.logger.info("(%s) - Task processed. Awaiting Aprroval"
                         % timezone.now())

        response_dict = {'notes': ['Task submitted.', 'Awaiting Approval.']}

        return Response(response_dict, status=202)

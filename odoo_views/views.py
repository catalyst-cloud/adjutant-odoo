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

from stacktask.api.v1 import tasks
from stacktask.api.v1.utils import create_notification, add_task_id_for_roles


class OpenStackSignUp(tasks.TaskView):

    default_actions = ['NewClientSignUp', 'NewProjectSignUp']
    task_type = 'signup'

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

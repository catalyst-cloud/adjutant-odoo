# Copyright (C) 2016 Catalyst IT Ltd
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


from stacktask.actions.serializers import BaseUserNameSerializer
from rest_framework import serializers


class NewClientSignUpSerializer(serializers.Serializer):

    # # this is used to double check what fields are required
    # 'signup_type',

    # # Individual or Primary business contact
    # 'first_name',  # required
    # 'last_name',  # required
    # 'email',  # required

    # # Individual or Company mobile contact
    # # if company, should this phone be associated with
    # # the primary contact, or the company?
    # 'phone',  # required

    # # company details
    # 'company_name',  # required for business
    # 'address_1',  # required for business
    # 'address_2',
    # 'city',  # required for business
    # 'region',
    # 'postal_code',  # required for business
    # 'payment_method',  # required for business

    # # If any required empty and is business, default to primary contact
    # 'bill_first_name',  # required in bill contact group
    # 'bill_last_name',  # required in bill contact group
    # 'bill_email',  # required in bill contact group

    # # If any required empty and is business, default to company address
    # 'bill_phone',  # required in bill address group
    # 'bill_address_1',  # required in bill address group
    # 'bill_address_2',
    # 'bill_city',  # required in bill address group
    # 'bill_region',
    # 'bill_postal_code',  # required in bill address group

    # # individual or business:
    # 'discount_code',

    signup_type = serializers.ChoiceField(
        choices=['individual', 'business'])

    # Indidividual or business
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=100)
    toc_agreed = serializers.BooleanField()
    discount_code = serializers.CharField(max_length=100, default="")
    payment_method = serializers.ChoiceField(
        choices=['invoice', 'credit_card'], default='credit_card')

    # business details
    company_name = serializers.CharField(max_length=100, default="")
    address_1 = serializers.CharField(max_length=200, default="")
    address_2 = serializers.CharField(max_length=200, default="")
    city = serializers.CharField(max_length=100, default="")
    region = serializers.CharField(max_length=100, default="")
    postal_code = serializers.CharField(max_length=100, default="")
    country = serializers.CharField(max_length=100, default="")

    primary_contact_is_billing = serializers.BooleanField(default=True)
    bill_first_name = serializers.CharField(max_length=100, default="")
    bill_last_name = serializers.CharField(max_length=100, default="")
    bill_email = serializers.EmailField(default="")
    bill_phone = serializers.CharField(max_length=100, default="")

    primary_address_is_billing = serializers.BooleanField(default=True)
    bill_address_1 = serializers.CharField(max_length=200, default="")
    bill_address_2 = serializers.CharField(max_length=200, default="")
    bill_city = serializers.CharField(max_length=100, default="")
    bill_region = serializers.CharField(max_length=100, default="")
    bill_postal_code = serializers.CharField(max_length=100, default="")
    bill_country = serializers.CharField(max_length=100, default="")

    def _check_field(self, errors, field, data):
        value = data.get(field)
        if not value:
            errors.append(field)
        return value

    def validate(self, data):

        if data['signup_type'] == 'business':

            missing_fields = []

            self._check_field(missing_fields, 'payment_method', data)
            self._check_field(missing_fields, 'company_name', data)

            self._check_field(missing_fields, 'first_name', data)
            self._check_field(missing_fields, 'last_name', data)
            self._check_field(missing_fields, 'email', data)
            self._check_field(missing_fields, 'phone', data)
            self._check_field(missing_fields, 'address_1', data)
            data.get('address_2')  # Not required
            self._check_field(missing_fields, 'city', data)
            data.get('region')  # Not required
            self._check_field(
                missing_fields, 'postal_code', data)
            self._check_field(missing_fields, 'country', data)

            primary_contact_is_billing = data.get('primary_contact_is_billing')
            primary_address_is_billing = data.get('primary_address_is_billing')

            if not primary_contact_is_billing:
                self._check_field(
                    missing_fields, 'bill_first_name', data)
                self._check_field(
                    missing_fields, 'bill_last_name', data)
                self._check_field(
                    missing_fields, 'bill_email', data)
                self._check_field(
                    missing_fields, 'bill_phone', data)

            if not primary_address_is_billing:
                self._check_field(
                    missing_fields, 'bill_address_1', data)
                self._check_field(
                    missing_fields, 'bill_city', data)
                self._check_field(
                    missing_fields, 'bill_region', data)
                self._check_field(
                    missing_fields, 'bill_postal_code', data)
                self._check_field(
                    missing_fields, 'bill_country', data)

            if missing_fields:
                raise serializers.ValidationError(
                    "These fields are required for businesses: %s" %
                    missing_fields)

        if not data['toc_agreed']:
            raise serializers.ValidationError(
                "Must agree to Terms and Conditions.")

        return data


# Extending class just for name clarity.
class NewProjectSignUpSerializer(BaseUserNameSerializer):
    pass

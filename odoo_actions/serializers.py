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

    # business details
    company_name = serializers.CharField(max_length=100, required=False)
    address_1 = serializers.CharField(max_length=200, required=False)
    address_2 = serializers.CharField(max_length=200, required=False)
    city = serializers.CharField(max_length=100, required=False)
    region = serializers.CharField(max_length=100, required=False)
    postal_code = serializers.CharField(max_length=100, required=False)
    country = serializers.CharField(max_length=100, required=False)
    payment_method = serializers.ChoiceField(
        choices=['invoice', 'credit_card'], required=False)
    bill_first_name = serializers.CharField(max_length=100, required=False)
    bill_last_name = serializers.CharField(max_length=100, required=False)
    bill_email = serializers.EmailField(required=False)
    bill_phone = serializers.CharField(max_length=100, required=False)
    bill_address_1 = serializers.CharField(max_length=200, required=False)
    bill_address_2 = serializers.CharField(max_length=200, required=False)
    bill_city = serializers.CharField(max_length=100, required=False)
    bill_region = serializers.CharField(max_length=100, required=False)
    bill_postal_code = serializers.CharField(max_length=100, required=False)
    bill_country = serializers.CharField(max_length=100, required=False)

    def _check_field(self, errors, field, data):
        value = data.get(field)
        if not value:
            errors.append(field)
        return value

    def validate(self, data):

        if not data['toc_agreed']:
            raise serializers.ValidationError(
                "Must agree to Terms and Conditions.")

        if data['signup_type'] == 'business':

            missing_fields = []

            self._check_field(missing_fields, 'payment_method', data)
            self._check_field(missing_fields, 'company_name', data)

            first_name = self._check_field(missing_fields, 'first_name', data)
            last_name = self._check_field(missing_fields, 'last_name', data)
            email = self._check_field(missing_fields, 'email', data)
            phone = self._check_field(missing_fields, 'phone', data)
            address_1 = self._check_field(missing_fields, 'address_1', data)
            address_2 = data.get('address_2')  # Not required
            data['address_2'] = address_2
            city = self._check_field(missing_fields, 'city', data)
            region = data.get('region')  # Not required
            data['region'] = region
            postal_code = self._check_field(
                missing_fields, 'postal_code', data)
            country = self._check_field(missing_fields, 'country', data)

            if missing_fields:
                raise serializers.ValidationError(
                    "These fields are required for businesses: %s" %
                    missing_fields)

            bill_first_name = data.get('bill_first_name')
            bill_last_name = data.get('bill_last_name')
            bill_email = data.get('bill_email')
            bill_phone = data.get('bill_phone')
            bill_address_1 = data.get('bill_address_1')
            bill_city = data.get('bill_city')
            bill_postal_code = data.get('bill_postal_code')
            bill_country = data.get('bill_country')

            # if any of these are not present, we will overwrite all
            # them with with the primary contact info
            if not (bill_first_name or bill_last_name or
                    bill_email or bill_phone or bill_address_1 or
                    bill_city or bill_postal_code or bill_country):
                data['bill_first_name'] = first_name
                data['bill_last_name'] = last_name
                data['bill_email'] = email
                data['bill_phone'] = phone
                data['bill_address_1'] = address_1
                data['bill_address_2'] = address_2
                data['bill_city'] = city
                data['bill_region'] = region
                data['bill_postal_code'] = postal_code
                data['bill_country'] = country

        return data


# Extending class just for name clarity.
class NewProjectSignUpSerializer(BaseUserNameSerializer):
    pass

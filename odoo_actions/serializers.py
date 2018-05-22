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


from adjutant.actions.v1.serializers import BaseUserNameSerializer
from rest_framework import serializers

from django_countries import countries


class NewClientSignUpActionSerializer(serializers.Serializer):

    signup_type = serializers.ChoiceField(
        choices=['individual', 'organisation'])

    # Indidividual or organisation
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=100)
    news_agreed = serializers.BooleanField(default=False)
    toc_agreed = serializers.BooleanField()
    discount_code = serializers.CharField(
        max_length=100, default="", allow_blank=True)

    # Change to credit_card as default with credit support
    payment_method = serializers.ChoiceField(
        choices=['invoice', 'credit_card'], default='invoice')
    stripe_token = serializers.CharField(
        max_length=100, default="", allow_blank=True)

    # organisation details
    company_name = serializers.CharField(
        max_length=100, default="", allow_blank=True)
    address_1 = serializers.CharField(
        max_length=200, default="", allow_blank=True)
    address_2 = serializers.CharField(
        max_length=200, default="", allow_blank=True)
    city = serializers.CharField(max_length=100, default="", allow_blank=True)
    postal_code = serializers.CharField(
        max_length=100, default="", allow_blank=True)
    country = serializers.ChoiceField(
        choices=countries, default="", allow_blank=True)

    primary_contact_is_billing = serializers.BooleanField(default=True)
    bill_name = serializers.CharField(
        max_length=200, default="", allow_blank=True)
    bill_email = serializers.EmailField(default="", allow_blank=True)
    bill_phone = serializers.CharField(
        max_length=100, default="", allow_blank=True)

    primary_address_is_billing = serializers.BooleanField(default=True)
    bill_address_1 = serializers.CharField(
        max_length=200, default="", allow_blank=True)
    bill_address_2 = serializers.CharField(
        max_length=200, default="", allow_blank=True)
    bill_city = serializers.CharField(
        max_length=100, default="", allow_blank=True)
    bill_postal_code = serializers.CharField(
        max_length=100, default="", allow_blank=True)
    bill_country = serializers.ChoiceField(
        choices=countries, default="", allow_blank=True)

    def _check_field(self, errors, field, data):
        value = data.get(field)
        if not value:
            errors.append(field)
        return value

    def validate(self, data):

        if data['signup_type'] == 'organisation':

            missing_fields = []

            payment_method = self._check_field(
                missing_fields, 'payment_method', data)
            self._check_field(missing_fields, 'company_name', data)

            self._check_field(missing_fields, 'name', data)
            self._check_field(missing_fields, 'email', data)
            self._check_field(missing_fields, 'phone', data)
            self._check_field(missing_fields, 'address_1', data)
            self._check_field(missing_fields, 'city', data)
            self._check_field(
                missing_fields, 'postal_code', data)
            self._check_field(missing_fields, 'country', data)

            primary_contact_is_billing = data.get('primary_contact_is_billing')
            primary_address_is_billing = data.get('primary_address_is_billing')

            if payment_method == 'credit_card':
                self._check_field(missing_fields, 'stripe_token', data)

            if not primary_contact_is_billing:
                self._check_field(
                    missing_fields, 'bill_name', data)
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
                    missing_fields, 'bill_postal_code', data)
                self._check_field(
                    missing_fields, 'bill_country', data)

            if missing_fields:
                raise serializers.ValidationError(
                    "These fields are required for organisations: %s" %
                    missing_fields)

        else:
            missing_fields = []

            # Uncomment with credit support
            # if data.get('payment_method') != 'credit_card':
            #     raise serializers.ValidationError(
            #         "Indidividuals can only pay by credit card.")
            # if not data.get('stripe_token'):
            #     raise serializers.ValidationError(
            #         "Must provide a stripe token.")

            # Remove with credit support
            payment_method = self._check_field(
                missing_fields, 'payment_method', data)

            self._check_field(
                missing_fields, 'bill_address_1', data)
            self._check_field(
                missing_fields, 'bill_city', data)
            self._check_field(
                missing_fields, 'bill_postal_code', data)
            self._check_field(
                missing_fields, 'bill_country', data)

            if missing_fields:
                raise serializers.ValidationError(
                    "These fields are required for individuals: %s" %
                    missing_fields)

        if not data['toc_agreed']:
            raise serializers.ValidationError(
                "Must agree to Terms and Conditions.")

        return data


class NewProjectSignUpActionSerializer(BaseUserNameSerializer):
    parent_id = serializers.CharField(
        max_length=64, default=None, allow_null=True, allow_blank=True)
    signup_type = serializers.ChoiceField(
        choices=['individual', 'organisation'])

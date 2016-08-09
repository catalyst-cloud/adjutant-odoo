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

    # # Individual or Company website
    # 'domain',

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

    # Indidividual or Primary business contact
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()

    # Individual or Company mobile contact
    # if company, should this phone be associated with
    # the primary contact, or the company?
    phone = serializers.CharField(max_length=100)

    # Individual or Company website
    domain = serializers.URLField(default="")

    # business details
    company_name = serializers.CharField(max_length=100, default="")
    address_1 = serializers.CharField(max_length=200, required=False)
    address_2 = serializers.CharField(max_length=200, default="")
    city = serializers.CharField(max_length=100, required=False)
    region = serializers.CharField(max_length=100, default="")
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

    # both business and individual
    discount_code = serializers.CharField(max_length=100, default="")
    toc_agreed = serializers.BooleanField()

    def validate(self, data):

        if not data['toc_agreed']:
            raise serializers.ValidationError(
                "Must agree to Terms and Conditions.")

        if data['signup_type'] == 'business':

            if not data.get('payment_method'):
                raise serializers.ValidationError(
                    "Payment method required for business signups.")

            try:
                first_name = data['first_name']
                last_name = data['last_name']
                email = data['email']
                phone = data['phone']
                address_1 = data['address_1']
                address_2 = data['address_2']
                city = data['city']
                region = data['region']
                postal_code = data['postal_code']
                country = data['country']

            # if any of the required primary address fields are missing
            # we throw a validation error.
            except KeyError:
                raise serializers.ValidationError(
                    "Address info required for business signups.")

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

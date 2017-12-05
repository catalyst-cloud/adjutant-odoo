from django.test import TestCase

from odoo_actions.serializers import NewClientSignUpActionSerializer


class SignupSerializerTests(TestCase):

    def test_signup_serializer_type(self):
        """
        Basic test to confirm serializer works.

        Although mainly to test that the test runner works at all.
        """

        data = {
            'signup_type': "not_a_valid_choice"
        }
        serializer = NewClientSignUpActionSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_signup_serializer_organisation_address_fail(self):
        """
        """

        data = {
            'signup_type': 'organisation',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true'
        }
        serializer = NewClientSignUpActionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors['non_field_errors'],
            ["These fields are required for organisations: " +
             "['company_name', 'address_1', 'city', 'postal_code', 'country']"]
        )

    def test_signup_serializer_organisation_address(self):
        """
        """

        data = {
            'signup_type': 'organisation',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'NZ',

        }
        serializer = NewClientSignUpActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_signup_serializer_organisation_address_billing_fail(self):
        """
        """

        data = {
            'signup_type': 'organisation',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'NZ',
            'primary_contact_is_billing': 'false',
            'primary_address_is_billing': 'false',

        }
        serializer = NewClientSignUpActionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors['non_field_errors'],
            ["These fields are required for organisations: " +
             "['bill_name', 'bill_email', " +
             "'bill_phone', 'bill_address_1', 'bill_city', " +
             "'bill_postal_code', 'bill_country']"]
        )

    def test_signup_serializer_organisation_address_billing(self):
        """
        """

        data = {
            'signup_type': 'organisation',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'NZ',
            'primary_contact_is_billing': 'false',
            'bill_name': 'Oz the Great and Powerful',
            'bill_email': 'oz@em.oz',
            'bill_phone': '123456',
            'primary_address_is_billing': 'false',
            'bill_address_1': 'yellow brick road',
            'bill_city': 'emerald city',
            'bill_postal_code': 'NW1',
            'bill_country': 'AU'

        }
        serializer = NewClientSignUpActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_signup_serializer_individual(self):
        """
        """

        data = {
            'signup_type': 'individual',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'stripe_token': "tok_stuff",
            'toc_agreed': 'true',
            'bill_address_1': 'yellow brick road',
            'bill_city': 'emerald city',
            'bill_postal_code': 'NW1',
            'bill_country': 'AU'

        }
        serializer = NewClientSignUpActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

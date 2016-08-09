from django.test import TestCase

from odoo_actions.serializers import NewClientSignUpSerializer


class SignupSerializerTests(TestCase):

    def test_signup_serializer_type(self):
        """
        Basic test to confirm serializer works.

        Although mainly to test that the test runner works at all.
        """

        data = {
            'signup_type': "not_a_valid_choice"
        }
        serializer = NewClientSignUpSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_signup_serializer_business_address_fail(self):
        """
        """

        data = {
            'signup_type': 'business',
            'first_name': 'jim',
            'last_name': 'james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true'
        }
        serializer = NewClientSignUpSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors['non_field_errors'],
            ['Address info required for business signups.'])

    def test_signup_serializer_business_address(self):
        """
        """

        data = {
            'signup_type': 'business',
            'first_name': 'jim',
            'last_name': 'james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'address_1': "a street",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'nz',

        }
        serializer = NewClientSignUpSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        self.assertEqual(
            serializer.validated_data['bill_address_1'],
            data['address_1'])
        self.assertEqual(
            serializer.validated_data['bill_city'],
            data['city'])
        self.assertEqual(
            serializer.validated_data['bill_postal_code'],
            data['postal_code'])
        self.assertEqual(
            serializer.validated_data['bill_country'],
            data['country'])

    def test_signup_serializer_individual(self):
        """
        """

        data = {
            'signup_type': 'individual',
            'first_name': 'jim',
            'last_name': 'james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'toc_agreed': 'true',

        }
        serializer = NewClientSignUpSerializer(data=data)
        self.assertTrue(serializer.is_valid())

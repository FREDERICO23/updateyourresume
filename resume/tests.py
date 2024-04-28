from django.test import Client, TestCase
from django.utils import timezone
from django.conf import settings
from unittest import mock

class TimeoutTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    # @mock.patch('.views.settings.DEFAULT_TIMEOUT', new=2)

    @mock.patch('django.conf.settings.DEFAULT_TIMEOUT', 4)  # Set a short timeout for testing
    def test_view_timeout(self):
        """
        Test that a view times out if it takes too long to respond.
        """
        # Mock a slow function that takes longer than the timeout
        slow_function_mock = mock.Mock(side_effect=lambda: time.sleep(3))

        # Replace the view function with the mocked slow function
        with mock.patch('resume.views.generate_resume', slow_function_mock):
            response = self.client.get('/generate-resume')
            self.assertEqual(response.status_code, 500)  # Expect an internal server error (500)

        with mock.patch('resume.views.resume_display', slow_function_mock):
            response = self.client.get('/display/1/')
            self.assertEqual(response.status_code, 500)  # Expect an internal server error (500)

        with mock.patch('resume.views.havard_resume', slow_function_mock):
            response = self.client.get('/havard_display/1/')
            self.assertEqual(response.status_code, 500)  # Expect an internal server error (500)

        with mock.patch('resume.views.generate_cover_letter', slow_function_mock):
            response = self.client.get('/generate-cover-letter/1/')
            self.assertEqual(response.status_code, 500)  # Expect an internal server error (500)

        with mock.patch('resume.views.cover_letter_display', slow_function_mock):
            response = self.client.get('/cover-letter/1/')
            self.assertEqual(response.status_code, 500)  # Expect an internal server error (500)

    def test_view_no_timeout(self):
        """
        Test that a view does not time out if it responds quickly.
        """
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)  # Expect a successful response (200)      

        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)  # Expect a successful response (200)

        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)  # Expect a successful response (200)

        response = self.client.get('/list-resumes/')
        self.assertEqual(response.status_code, 200)  # Expect a successful response (200)

        response = self.client.get('/pricing/')
        self.assertEqual(response.status_code, 200)  # Expect a successful response (200)
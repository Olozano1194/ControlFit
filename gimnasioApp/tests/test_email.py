"""Unit tests for send_welcome_email service.

Extracted from the original tests.py (lines 1129-1261).
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock

from .factories import create_gimnasio, create_admin_user


class EmailServiceTest(TestCase):
    """Unit tests for send_welcome_email service."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.admin = create_admin_user(self.gimnasio)

    @patch('gimnasioApp.services.email.requests.post')
    @patch('django.conf.settings.FRONTEND_URL', 'http://localhost:5173')
    @patch('django.conf.settings.SUPPORT_EMAIL', 'soporte@controlfit.app')
    @patch('django.conf.settings.RESEND_API_KEY', 're_test_key')
    @patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'ControlFit <noreply@controlfit.app>')
    def test_send_welcome_email_renders_templates(self, mock_post):
        """Test that send_welcome_email renders both HTML and text templates via Resend API."""
        from gimnasioApp.services.email import send_welcome_email
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        send_welcome_email(self.gimnasio.id, self.admin.id, 'TempPass123')
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify Resend API URL
        self.assertEqual(call_args.args[0], "https://api.resend.com/emails")
        
        # Verify payload structure
        payload = call_args.kwargs['json']
        self.assertIn('from', payload)
        self.assertIn('to', payload)
        self.assertIn('subject', payload)
        self.assertIn('html', payload)
        self.assertIn('text', payload)
        
        # Verify subject
        self.assertIn('Bienvenido a ControlFit', payload['subject'])
        self.assertIn('Test Gym', payload['subject'])
        
        # Verify recipient (factory creates admin@example.com)
        self.assertEqual(payload['to'], ['admin@example.com'])
        
        # Verify from email
        self.assertEqual(payload['from'], 'ControlFit <noreply@controlfit.app>')
        
        # Verify html and text content exist
        self.assertTrue(len(payload['html']) > 0)
        self.assertTrue(len(payload['text']) > 0)
        
        # Verify content includes key data
        html = payload['html']
        plain = payload['text']
        self.assertIn('Test Gym', html)
        self.assertIn('admin@example.com', html)
        self.assertIn('TempPass123', html)
        self.assertIn('http://localhost:5173/login', html)
        self.assertIn('soporte@controlfit.app', html)
        self.assertIn('Test Gym', plain)
        self.assertIn('admin@example.com', plain)
        self.assertIn('TempPass123', plain)
        self.assertIn('http://localhost:5173/login', plain)
        self.assertIn('soporte@controlfit.app', plain)

    @patch('gimnasioApp.services.email.requests.post')
    @patch('django.conf.settings.FRONTEND_URL', 'http://localhost:5173')
    @patch('django.conf.settings.SUPPORT_EMAIL', 'soporte@controlfit.app')
    @patch('django.conf.settings.RESEND_API_KEY', 're_test_key')
    @patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'ControlFit <noreply@controlfit.app>')
    def test_send_welcome_email_context_includes_all_fields(self, mock_post):
        """Test that template context includes all required fields."""
        from gimnasioApp.services.email import send_welcome_email
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        send_welcome_email(self.gimnasio.id, self.admin.id, 'MyTempPass')
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = call_args.kwargs['json']
        html = payload['html']
        plain = payload['text']
        
        # Verify all context fields appear in rendered templates
        self.assertIn('Test Gym', html)  # gym_name
        self.assertIn('admin@example.com', html)  # admin_email
        self.assertIn('MyTempPass', html)  # temp_password
        self.assertIn('http://localhost:5173/login', html)  # login_url
        self.assertIn('soporte@controlfit.app', html)  # support_email
        
        self.assertIn('Test Gym', plain)
        self.assertIn('admin@example.com', plain)
        self.assertIn('MyTempPass', plain)
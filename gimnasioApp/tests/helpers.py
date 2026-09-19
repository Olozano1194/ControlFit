"""Helper functions for test utilities.

Extracted from the original tests.py to eliminate duplication.
"""

import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory


def make_uploaded_image(filename='test.jpg', fmt='JPEG', size=(10, 10), color='red'):
    """Generate a valid image file using Pillow.

    Args:
        filename: Output filename
        fmt: Image format (JPEG, PNG)
        size: Tuple (width, height)
        color: Fill color

    Returns:
        SimpleUploadedFile instance
    """
    img = Image.new('RGB', size, color=color)
    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    return SimpleUploadedFile(
        filename,
        buffer.getvalue(),
        content_type='image/jpeg' if fmt == 'JPEG' else 'image/png'
    )


def make_request_with_gym(factory, method='get', path='/', user=None, gimnasio=None, data=None, format=None):
    """Create a request with user and gimnasio attached.

    Args:
        factory: APIRequestFactory or RequestFactory instance
        method: HTTP method (get, post, patch, put, delete)
        path: Request path
        user: User instance to attach
        gimnasio: Gimnasio instance to attach
        data: Request data
        format: Request format (json, multipart)

    Returns:
        Request instance with user and gimnasio attributes
    """
    method_func = getattr(factory, method.lower())
    request = method_func(path, data, format=format) if data is not None else method_func(path, format=format)
    if user is not None:
        request.user = user
    if gimnasio is not None:
        request.gimnasio = gimnasio
    return request
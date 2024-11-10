from django import template
import base64
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

register = template.Library()

@register.filter(name='base64encode')
def base64encode(value):
    if value:
        # Check if value is an InMemoryUploadedFile
        if isinstance(value, InMemoryUploadedFile):
            # Read the file content from InMemoryUploadedFile
            file_content = value.read()
            encoded_string = base64.b64encode(file_content).decode('utf-8')
            return f"data:image/png;base64,{encoded_string}"
    return ''

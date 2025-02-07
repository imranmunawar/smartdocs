from django.db import models
from .user import CustomUser
from .template import Template

class UserDocument(models.Model):
    name = models.CharField(max_length=30, help_text='Name of the Template')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    document_json = models.JSONField()
    template_file_name = models.CharField(max_length=300, default=None, null=True)
    template = models.ForeignKey(Template, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    is_synced = models.BooleanField(default=True)
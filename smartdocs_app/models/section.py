from django.db import models
from .template import Template

class Section(models.Model):

    name = models.CharField(max_length=50, help_text='Name of the Section')
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    parent_section = models.ForeignKey('self', null=True, blank=True, default=None, on_delete=models.CASCADE, related_name='children')
    is_active = models.BooleanField(default=True)
    sequence_id = models.IntegerField(default=0)
    vimeo_link = models.TextField(null=True, blank=True)
    vimeo_timestamp = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self) -> str:
        return self.name

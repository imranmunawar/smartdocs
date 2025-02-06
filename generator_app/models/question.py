from django.db import models
from .template import Template
from .section import Section
from django.utils.translation import gettext_lazy as _

class Question(models.Model):

    class QuestionTypes(models.TextChoices):
        TEXT = 'text', _('text')
        RADIO = 'radio', _('radio')
        MULTIPLE = 'multiple', _('multiple')
        DATE = 'date', _('date')
        PERCENTAGE = 'percentage', _('percentage')
        IMAGE = 'image', _('image')
        SINGLE_CHECKBOX = 'single_checkbox', _('single_checkbox')
        CURRENCY = 'currency', _('currency')

    
    question = models.TextField(null=False, help_text='Text of the question')
    placeholder = models.CharField(max_length=200, help_text='Place holder of the question')
    question_type = models.CharField(max_length=20, choices=QuestionTypes.choices, default=QuestionTypes.TEXT)
    parent_question = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    is_ai = models.BooleanField(default=False)
    ai_prompt = models.TextField(null=True, blank=True)
    na_applicable = models.BooleanField(default=False)
    helping_text = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sequence_id = models.IntegerField(default=0)
    vimeo_link = models.TextField(null=True, blank=True)
    vimeo_timestamp = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self) -> str:
        return f"{self.question[:20]}"

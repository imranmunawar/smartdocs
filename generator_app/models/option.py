from django.db import models
from .question import Question

class Option(models.Model):

    name = models.TextField(null=False, help_text='Text of the option')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options_question')
    child_questions = models.ManyToManyField(Question, blank=True, related_name='options_child_question')
    is_active = models.BooleanField(default=True)

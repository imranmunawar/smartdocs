from django.db import models
from .user_document import UserDocument
from .question import Question
from .section import Section

class Answer(models.Model):

    answer = models.TextField(null=False, help_text='Text of the answer')
    user_document = models.ForeignKey(UserDocument, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, null=True, on_delete=models.SET_NULL)
    section = models.ForeignKey(Section, null=True, on_delete=models.SET_NULL)

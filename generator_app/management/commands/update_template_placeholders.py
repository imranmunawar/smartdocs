from django.core.management.base import BaseCommand
from generator_app.models import Question


class Command(BaseCommand):
    help = 'Update placeholder of questions associated with template_id'

    def add_arguments(self, parser):
        parser.add_argument('template_id', type=int, help='Template ID')

    def handle(self, *args, **kwargs):
        template_id = kwargs['template_id']
        questions = Question.objects.filter(template_id=template_id)

        for question in questions:
            placeholder = question.placeholder
            placeholder = placeholder.replace("[", "${").replace("]", "}")
            print(f'Updating Placeholder: {question.placeholder} ---> {placeholder}')
            question.placeholder = placeholder
            question.save()

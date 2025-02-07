from copy import deepcopy
from ..models import UserDocument, Answer, Template


class DocumentDuplicate():
    """
    Helper Class for document duplication
    """

    def __init__(self, user_document_id:int, new_document_name:str):
        self.new_document_name = new_document_name
        self.user_document_id = user_document_id
        self.document_obj = UserDocument.objects.get(id=user_document_id)
        
    def duplicate(self):
        """
        Method executes the duplication process
        """

        self._duplicate_document()
        self._duplicate_answers()
    

    def _duplicate_document(self):
        """
        Private Method
        Creates a copy of the document
        """

        template = Template.objects.get(id=self.document_obj.template.id)
        self.new_document_obj = UserDocument.objects.create(
            name=self.new_document_name,
            template_file_name=self.document_obj.template_file_name,
            document_json=self.document_obj.document_json,
            user=self.document_obj.user,
            template= template
        )
        self.new_document_obj.save()


    def _duplicate_answers(self):
        """
        Private Method
        Duplicates all the answers for a document
        """

        for section in self.new_document_obj.document_json['sections']:
            for subsection in section['subsections']:
                for question in subsection['questions']:
                    self._clone_answer(question['question_id'], subsection['section_id'])
                    if question['type'] == 'radio':
                        self._clone_nested_answers(question, subsection['section_id'])

    
    def _clone_nested_answers(self, question, section_id):
        """
        Private Method
        Clones all the nested answers of a document
        """

        for option in question['options']:
            if 'questions' in option:
                for option_question in option['questions']:
                    self._clone_answer(option_question['question_id'], section_id)
                    if option_question['type'] == 'radio':
                        self._clone_nested_answers(option_question, section_id)


    def _clone_answer(self, question_id:int, section_id:int):
        """
        Private Method
        Clones a answer object and stores to db
        """

        old_answer_obj = Answer.objects.filter(
            section_id=section_id,
            question_id=question_id,
            user_document_id=self.user_document_id
        ).first()
        if old_answer_obj:
            new_answer_obj = Answer.objects.create(
                answer=old_answer_obj.answer,
                user_document_id=self.new_document_obj.id,
                section_id=section_id,
                question_id=question_id
            )
            new_answer_obj.save()

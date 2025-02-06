from django import template
from django.utils.safestring import mark_safe
from ..models import Answer, Question
from django.conf import settings

register = template.Library()

HELPER_TEXT_STYLING = "style='display: block; color: grey; margin-left: 20px; margin-bottom:12px; font-size: 14px;'"


def get_previous_answer_text_and_color(section_id:int, question_id:int, user_document_id:int) -> dict:
    """
    Gets the text answer from db and the color to set for the question ticker

    :param section_id: Id for the section for answer
    :type section_id: int
    :param question_id: Id for the question for answer
    :type question_id: int
    :param user_document_id: Id for the user document for answer
    :type user_document_id: int
    :return: The dict containing the answer and color
    :rtype: dict
    """

    answer = Answer.objects.filter(
        section_id=section_id,
        question_id=question_id,
        user_document_id=user_document_id
    ).first()
    
    if not answer:
        return {'text': '', 'color': 'black'}
    elif(answer.answer != ''):
        return {'text': answer.answer, 'color': 'green'}
    else:
        return {'text': answer.answer, 'color': 'red'}


def get_vimeo_html(question_id):

    question = Question.objects.get(id = question_id)

    if not question.vimeo_timestamp and not question.vimeo_link:
        
        return ''

    elif (question.vimeo_timestamp and question.vimeo_timestamp >= 0 and not question.vimeo_link
        and not question.section.vimeo_link and not question.section.parent_section.vimeo_link):
        
        return ''

    video_icon = f"<i class='fa fa-video' data-bs-toggle='modal' data-bs-target='#video_modal_{question_id}' style='cursor: pointer; margin-left: 10px;'></i>"
    video_modal = f"<div class='modal fade' id='video_modal_{question_id}' style='display: none;' aria-hidden='true'>\
        <div class='modal-dialog modal-dialog-centered'>\
            <div class='modal-content' style='background-color: black;'>\
                <div class='modal-body'>\
                    <div id='video_content_{question_id}'></div>\
                </div>\
            </div>\
        </div>\
    </div>"
    video_html = video_icon + video_modal

    return video_html


@register.simple_tag
def text_field_html(question:dict, section_id:int, user_document_id:int) -> str:
    """
    Returns the html generated for a text answer based question

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: HTML for the text field and question
    :rtype: str
    """

    question_text = question['question']
    help_html = ''
    na_applicable_html = ''
    ai_html = ''

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    if 'na_applicable' in question and question['na_applicable'] == True:
        na_applicable_html = f"<button style='margin-left: 20px;' class='btn btn-success mt-2' data-question-id={question['question_id']} onclick='buttonClick(this)'>NOT APPLICABLE</button>"
    
    if 'is_ai' in question and question['is_ai'] == True:
        if 'na_applicable' in question and question['na_applicable'] == True:
            modal_open_button = f"<button href='#generative_text_modal_{question['question_id']}' class='btn btn-success mt-2' data-bs-toggle='modal'>\
                                    </i> Use AI\
                                </button>\
                                "
        else:
            modal_open_button = f"<button href='#generative_text_modal_{question['question_id']}' style='margin-left: 20px;' class='btn btn-success mt-2' data-bs-toggle='modal'>\
                                    </i> Use AI\
                                </button>\
                                "

        modal_html = (f"<div class='modal fade' id='generative_text_modal_{question['question_id']}' style='display: none; z-index: 100000;' aria-hidden='true'>\
            <div class='modal-dialog modal-dialog-centered' role='document'>\
                <div class='modal-content'>\
                    <div class='modal-body'>\
                        <textarea style='height: 13rem;' id='prompt_{question['question_id']}' class='form-control mt-2' placeholder='Enter AI prompt here'>{question['ai_prompt']}</textarea>\
                        <button class='btn btn-success mt-2' data-question-id={question['question_id']} onclick='aiButtonClick(this)'>\
                        <span class='spinner-border spinner-border-sm d-none' role='status' aria-hidden='true'></span>\
                        Generate\
                        </button>\
                    </div>\
                </div>\
            </div>\
        </div>\
            ")

        ai_html = modal_open_button + modal_html


    video_html = get_vimeo_html(question['question_id'])

    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)

    placeholder_answer = answer['text']

    question_html = f"<div class='mb-3' data-question-id={question['question_id']} data-section-id={section_id}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <textarea style='margin-left: 20px; height: auto;' class='form-control atextarea' id='text_area_{question['question_id']}' value='{placeholder_answer}'>{placeholder_answer}</textarea>\
        {na_applicable_html}\
        {ai_html}\
    </div>"
    # <input type='text' class='form-control' value='{answer['text']}'>\
    return mark_safe(question_html)


@register.simple_tag
def radio_field_html(question:dict, section_id:int, user_document_id:int) -> str:
    """
    Returns the html generated for a radio answer based question and nested subquestions

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: HTML for the radio field question and nested subquestions
    :rtype: str
    """

    video_html = get_vimeo_html(question['question_id'])
    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id) 

    help_html = ''
    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    radio_text = f"<div class='mb-3' data-question-id={question['question_id']} data-section-id={section_id}>\
                         <label><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question['question']}</b>{video_html}</label>\
                        {help_html}\
                    <div class='col-md-10'>\
                "
    radio_text = radio_text + get_radio_options(question=question, answer=answer)
    radio_text = radio_text + f'</div>\
                                </div>'

    radio_text = radio_text + get_nested_questions(question, section_id, user_document_id)
    return mark_safe(radio_text)


def get_radio_options(question:dict, answer:dict) -> str:
    """
    Return the radio options for a radio field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param answer: Dict containing the answer of question from db if any
    :type answer: Dict
    :return: A string containing html for the options
    :rtype: str
    """

    options_html = ''
    for option in question['options']:
        if option['option_value'] == answer['text']:
            checked_value = 'checked'
        else:
            checked_value = ''

        options_html = options_html + f"<div class='radio' style='margin-left: 20px;'>\
                                            <label>\
                                                <input {checked_value} type='radio' name='radio-{question['question_id']}' data-radio-label='{option['option_value']}' data-question-id={question['question_id']} > {option['option_value']}\
                                            </label>\
                                        </div>\
                                    "
    return options_html


def get_nested_questions(question:dict, section_id:int, user_document_id:int) -> str:
    """
    Returns the html for the nested question

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: String containing the html for the nested questions
    :rtype: str
    """
    nested_html = ''
    for option in question['options']:
        if 'questions' in option:
            for option_question in option['questions']:
                if option_question['is_active']:
                    option_value = option['option_value']
                    if option_question['type'] == 'text':
                        nested_html = nested_html + child_text_field_html(option_question, option_value, section_id, question['question_id'], user_document_id)
                    elif option_question['type'] == 'multiple':
                        nested_html = nested_html + child_multiple_field_html(option_question, option_value, section_id, question['question_id'], user_document_id)
                    elif option_question['type'] == 'date':
                        nested_html = nested_html + child_date_field_html(option_question, option_value, section_id, question['question_id'], user_document_id)
                    elif option_question['type'] == 'percentage':
                        nested_html = nested_html + child_percentage_field_html(option_question, option_value, section_id, question['question_id'], user_document_id)
                    elif option_question['type'] == 'currency':
                        nested_html = nested_html + child_currency_field_html(option_question, option_value, section_id, question['question_id'], user_document_id)
                    elif option_question['type'] == 'image':
                        nested_html = nested_html + child_image_field_html(option_question, option_value, section_id, question['question_id'], user_document_id)
                    elif option_question['type'] == 'single_checkbox':
                        nested_html = nested_html + child_single_checkbox_field_html(option_question, option_value, section_id, question['question_id'], user_document_id)
                    else:
                        nested_html = nested_html + child_radio_field_html(option_question, option_value, section_id, question['question_id'], user_document_id)
        
    return nested_html


def child_multiple_field_html(question:dict, option_value:str, section_id:int, parent_question:int, user_document_id:int) -> str:
    """
    Returns the html for the nested child multiple field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param option_value: The value for the option if any
    :type option_value: str
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param parent_question: Id of the parent question
    :tpye parent_question: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: String containing the html for the nested multiple questions
    :rtype: str
    """
    
    index = 0
    video_html = get_vimeo_html(question['question_id'])
    question_text = question['question']
    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)

    hidden_attr = 'hidden'
    if is_option_selected(option_value, section_id, parent_question, user_document_id):
        hidden_attr = ''

    help_html = ''

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    multiple_answers = answer['text'].split('|')
    question_html = f"<div class='mb-3 child_question' data-parent-option='{option_value}' data-question-id={question['question_id']} data-section-id={section_id} data-parent-question={parent_question} {hidden_attr}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <div id='input-container'>\
        "
    for single_answer in multiple_answers:
        question_html = question_html + f"<div class='input-row'>\
            <input type='text' id='multiple-{question['question_id']}' style='margin-left: 20px;' class='dynamic-input form-control' value='{single_answer}' onblur='saveInputData(this)'>\
                "
        if index == 0:
            question_html = question_html + f"<button style='margin-left: 20px;' class='btn btn-sm btn-success mt-2' onclick='addInput(this)' data-question-id={question['question_id']}>+</button>\
            </div>\
            "
        else:
            question_html = question_html + f"<button style='margin-left: 20px;' class='btn btn-sm btn-success mt-2' onclick='removeInput(this)' data-question-id={question['question_id']}>-</button>\
            </div>\
            "
        index+=1
    question_html = question_html + f"</div>\
    </div>\
        "
    return mark_safe(question_html)


def child_text_field_html(question:dict, option_value:str, section_id:int, parent_question:int, user_document_id:int) -> str:
    """
    Returns the html for the nested child text field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param option_value: The value for the option if any
    :type option_value: str
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param parent_question: Id of the parent question
    :tpye parent_question: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: String containing the html for the nested text questions
    :rtype: str
    """

    question_html = ''
    question_text = question['question']
    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)
    
    hidden_attr = 'hidden'
    if is_option_selected(option_value, section_id, parent_question, user_document_id):
        hidden_attr = ''
    
    help_html = ''
    na_applicable_html = ''
    ai_html = ''
    video_html = get_vimeo_html(question['question_id'])

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    if 'na_applicable' in question and question['na_applicable'] == True:
        na_applicable_html = f"<button style='margin-left: 20px;' class='btn btn-success mt-2' data-question-id={question['question_id']} onclick='buttonClick(this)'>NOT APPLICABLE</button>"
    
    if 'is_ai' in question and question['is_ai'] == True:
        if 'na_applicable' in question and question['na_applicable'] == True:
            modal_open_button = f"<button href='#generative_text_modal_{question['question_id']}' style='margin-left: 20px;' class='btn btn-success mt-2' data-bs-toggle='modal'>\
                                    </i> Use AI\
                                </button>\
                                "
        else:
            modal_open_button = f"<button href='#generative_text_modal_{question['question_id']}' style='margin-left: 20px;' class='btn btn-success mt-2' data-bs-toggle='modal'>\
                                    </i> Use AI\
                                </button>\
                                "

        modal_html = (f"<div class='modal fade' id='generative_text_modal_{question['question_id']}' style='display: none; z-index: 100000;' aria-hidden='true'>\
            <div class='modal-dialog modal-dialog-centered' role='document'>\
                <div class='modal-content'>\
                    <div class='modal-body'>\
                        <textarea style='height: 13rem;' id='prompt_{question['question_id']}' class='form-control mt-2' placeholder='Enter AI prompt here'>{question['ai_prompt']}</textarea>\
                        <button class='btn btn-success mt-2' data-question-id={question['question_id']} onclick='aiButtonClick(this)'>\
                        <span class='spinner-border spinner-border-sm d-none' role='status' aria-hidden='true'></span>\
                        Generate\
                        </button>\
                    </div>\
                </div>\
            </div>\
        </div>\
            ")
            
        ai_html = modal_open_button + modal_html
    
    question_html = f"<div class='mb-3 child_question' data-parent-option='{option_value}' data-question-id={question['question_id']} data-section-id={section_id} data-parent-question={parent_question} {hidden_attr}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <textarea style='margin-left: 20px; height: auto;' class='form-control atextarea' id='text_area_{question['question_id']}' value='{answer['text']}'>{answer['text']}</textarea>\
        {na_applicable_html}\
        {ai_html}\
    </div>"

    # <input type='text' class='form-control' value='{answer['text']}'>\

    return question_html


def child_date_field_html(question:dict, option_value:str, section_id:int, parent_question:int, user_document_id:int) -> str:
    """
    Returns the html for the nested child date field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param option_value: The value for the option if any
    :type option_value: str
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param parent_question: Id of the parent question
    :tpye parent_question: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: String containing the html for the nested date questions
    :rtype: str
    """

    question_html = ''
    question_text = question['question']
    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)
    video_html = get_vimeo_html(question['question_id'])

    hidden_attr = 'hidden'
    if is_option_selected(option_value, section_id, parent_question, user_document_id):
        hidden_attr = ''
    
    help_html = ''

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

 
    question_html = f"<div class='mb-3 child_question' data-parent-option='{option_value}' data-question-id={question['question_id']} data-section-id={section_id} data-parent-question={parent_question} {hidden_attr}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <input type='date' style='margin-left: 20px;' class='form-control' value='{answer['text']}'>\
    </div>"

    # <input type='text' class='form-control' value='{answer['text']}'>\

    return question_html


def child_radio_field_html(question:dict, option_value:str, section_id:int, parent_question:int, user_document_id:int) -> str:
    """
    Returns the html for the nested radio text field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param option_value: The value for the option if any
    :type option_value: str
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param parent_question: Id of the parent question
    :tpye parent_question: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: String containing the html for the nested radio questions
    :rtype: str
    """

    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id) 
    video_html = get_vimeo_html(question['question_id'])

    hidden_attr = 'hidden'
    if is_option_selected(option_value, section_id, parent_question, user_document_id):
        hidden_attr = ''

    help_html = ''
    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    radio_text = f"<div class='mb-3 child_question' data-question-id={question['question_id']} data-section-id={section_id} data-parent-option='{option_value}' data-parent-question={parent_question} {hidden_attr}>\
                    <label><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question['question']}</b>{video_html}</label>\
                    {help_html}\
                    <div class='col-md-10'>\
                "
    radio_text = radio_text + get_radio_options(question=question, answer=answer)
    radio_text = radio_text + f'</div>\
                                </div>'

    radio_text = radio_text + get_nested_questions(question, section_id, user_document_id)
    return mark_safe(radio_text)


def is_option_selected(option_value:str, section_id:int, parent_question:int, user_document_id:int) -> bool:
    """
    Verifies for an option if the value of the option matches the one stored in db

    :param option_value: The value for the option
    :type option_value: str
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param parent_question: Id of the parent question
    :tpye parent_question: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: If the option matches the value in db or not
    :rtype: bool
    """
    
    parent_answer = get_previous_answer_text_and_color(section_id, parent_question, user_document_id) 
    return True if option_value == parent_answer['text'] else False


@register.simple_tag
def multiple_field_html(question:dict, section_id:int, user_document_id:int) -> str:
    """
    Returns the html generated for a multiple answer based question

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: HTML for the multiple field and question
    :rtype: str
    """

    index = 0
    question_text = question['question']
    video_html = get_vimeo_html(question['question_id'])
    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)    
    multiple_answers = answer['text'].split('|')

    help_html = ''
    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    question_html = f"<div class='mb-3' data-question-id={question['question_id']} data-section-id={section_id}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <div id='input-container'>\
        "
    for single_answer in multiple_answers:
        question_html = question_html + f"<div class='input-row'>\
            <input type='text' id='multiple-{question['question_id']}' style='margin-left: 20px;' class='dynamic-input form-control' value='{single_answer}' onblur='saveInputData(this)'>\
                "
        if index == 0:
            question_html = question_html + f"<button style='margin-left: 20px;' class='btn btn-sm btn-success mt-2' onclick='addInput(this)' data-question-id={question['question_id']}>+</button>\
            </div>\
            "
        else:
            question_html = question_html + f"<button class='btn btn-sm btn-danger' onclick='removeInput(this)' data-question-id={question['question_id']}>-</button>\
            </div>\
            "
        index+=1
    question_html = question_html + f"</div>\
    </div>\
        "
    return mark_safe(question_html)


@register.simple_tag
def date_field_html(question:dict, section_id:int, user_document_id:int) -> str:
    """
    Returns the html generated for a date answer based question

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: HTML for the date field and question
    :rtype: str
    """

    question_text = question['question']
    video_html = get_vimeo_html(question['question_id'])
    help_html = ''

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)    
    question_html = f"<div class='mb-3' data-question-id={question['question_id']} data-section-id={section_id}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <input type='date' style='margin-left: 20px;' class='form-control' value='{answer['text']}'>\
    </div>"
    # <input type='text' class='form-control' value='{answer['text']}'>\
    return mark_safe(question_html)


@register.simple_tag
def image_field_html(question:dict, section_id:int, user_document_id:int) -> str:
    """
    Returns the html generated for a image answer based question

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: HTML for the image field and question
    :rtype: str
    """

    question_text = question['question']
    video_html = get_vimeo_html(question['question_id'])
    help_html = ''

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"
    
    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)

    image_html = ''
    if answer['text'] != '':
        s3_url = f"/serve-image-from-s3/{answer['text']}/"
        image_html = f"<img class='avatar-img rounded' style='max-width: 600px; max-height: 400px;' alt='User Image' src='{s3_url}'>"

    question_html = f"<div class='mb-3' data-question-id={question['question_id']} data-section-id={section_id}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <input style='margin-left: 20px;' type='file' accept='image/*' id='file-{question['question_id']}' class='form-control' value='{answer['text']}'>\
        {image_html}\
    </div>"

    return mark_safe(question_html)


def child_image_field_html(question:dict, option_value:str, section_id:int, parent_question:int, user_document_id:int) -> str:
    """
    Returns the html for the nested child image field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param option_value: The value for the option if any
    :type option_value: str
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param parent_question: Id of the parent question
    :tpye parent_question: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: String containing the html for the nested image questions
    :rtype: str
    """

    question_html = ''
    question_text = question['question']
    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)
    video_html = get_vimeo_html(question['question_id'])

    hidden_attr = 'hidden'
    if is_option_selected(option_value, section_id, parent_question, user_document_id):
        hidden_attr = ''
    
    help_html = ''

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    image_html = ''
    if answer['text'] != '':
        s3_url = f"/serve-image-from-s3/{answer['text']}/"
        image_html = f"<img class='avatar-img rounded' style='max-width: 600px; max-height: 400px;' alt='User Image' src='{s3_url}'>"
    
    question_html = f"<div class='mb-3 child_question' data-parent-option='{option_value}' data-question-id={question['question_id']} data-section-id={section_id} data-parent-question={parent_question} {hidden_attr}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <input style='margin-left: 20px;' type='file' accept='image/*' id='file-{question['question_id']}' class='form-control' value='{answer['text']}'>\
        {image_html}\
    </div>"

    return question_html


@register.simple_tag
def single_checkbox_field_html(question:dict, section_id:int, user_document_id:int) -> str:
    """
    Returns the html generated for a single checkbox field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: HTML for the radio field question and nested subquestions
    :rtype: str
    """

    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id) 
    video_html = get_vimeo_html(question['question_id'])

    help_html = ''
    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    radio_text = f"<div class='mb-3' data-question-id={question['question_id']} data-section-id={section_id}>\
                         <label><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question['question']}</b>{video_html}</label>\
                        {help_html}\
                    <div class='col-md-10'>\
                "
    radio_text = radio_text + get_single_checkbox_options(question=question, answer=answer)
    radio_text = radio_text + f'</div>\
                                </div>'

    return mark_safe(radio_text)


def child_single_checkbox_field_html(question:dict, option_value:str, section_id:int, parent_question:int, user_document_id:int) -> str:
    """
    Returns the html for the nested single checkbox field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param option_value: The value for the option if any
    :type option_value: str
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param parent_question: Id of the parent question
    :tpye parent_question: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: String containing the html for the nested radio questions
    :rtype: str
    """

    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id) 
    video_html = get_vimeo_html(question['question_id'])

    hidden_attr = 'hidden'
    if is_option_selected(option_value, section_id, parent_question, user_document_id):
        hidden_attr = ''

    help_html = ''
    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    radio_text = f"<div class='mb-3 child_question' data-question-id={question['question_id']} data-section-id={section_id} data-parent-option='{option_value}' data-parent-question={parent_question} {hidden_attr}>\
                    <label><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question['question']}</b>{video_html}</label>\
                    {help_html}\
                    <div class='col-md-10'>\
                "
    radio_text = radio_text + get_single_checkbox_options(question=question, answer=answer)
    radio_text = radio_text + f'</div>\
                                </div>'

    return mark_safe(radio_text)


def get_single_checkbox_options(question:dict, answer:dict) -> str:
    """
    Return the options for a checkbox field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param answer: Dict containing the answer of question from db if any
    :type answer: Dict
    :return: A string containing html for the options
    :rtype: str
    """

    options_html = ''
    checkbox_options = ['True', 'False']
    for option in checkbox_options:
        if option == answer['text']:
            checked_value = 'checked'
        else:
            checked_value = ''

        options_html = options_html + f"<div class='radio' style='margin-left: 20px;'>\
                                            <label>\
                                                <input {checked_value} type='radio' name='radio-{question['question_id']}' data-radio-label='{option}' data-question-id={question['question_id']} > {option}\
                                            </label>\
                                        </div>\
                                    "
    return options_html


@register.simple_tag
def percentage_field_html(question:dict, section_id:int, user_document_id:int) -> str:
    """
    Returns the html generated for a percentage answer based question

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: HTML for the percentage field and question
    :rtype: str
    """

    question_text = question['question']
    help_html = ''
    video_html = get_vimeo_html(question['question_id'])

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)    
    question_html = f"<div class='mb-3' data-question-id={question['question_id']} data-section-id={section_id}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <div class='input-group'>\
        <input type='number' min='0' max='100' step='0.01' style='margin-left: 20px;' class='form-control' value='{answer['text']}'\
        oninput='if(value<0)value=0;if(value>100)value=100;'>\
        <span class='input-group-text'>%</span>\
        </div>\
    </div>"
    return mark_safe(question_html)


def child_percentage_field_html(question:dict, option_value:str, section_id:int, parent_question:int, user_document_id:int) -> str:
    """
    Returns the html for the nested child percentage field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param option_value: The value for the option if any
    :type option_value: str
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param parent_question: Id of the parent question
    :tpye parent_question: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: String containing the html for the nested percentage questions
    :rtype: str
    """

    question_html = ''
    question_text = question['question']
    video_html = get_vimeo_html(question['question_id'])
    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)
    
    hidden_attr = 'hidden'
    if is_option_selected(option_value, section_id, parent_question, user_document_id):
        hidden_attr = ''
    
    help_html = ''

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

 
    question_html = f"<div class='mb-3 child_question' data-parent-option='{option_value}' data-question-id={question['question_id']} data-section-id={section_id} data-parent-question={parent_question} {hidden_attr}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <div class='input-group'>\
        <input type='number' min='0' max='100' step='0.01' style='margin-left: 20px;' class='form-control' value='{answer['text']}'\
        oninput='if(value<0)value=0;if(value>100)value=100;'>\
        <span class='input-group-text'>%</span>\
        </div>\
    </div>"

    return question_html


@register.simple_tag
def currency_field_html(question:dict, section_id:int, user_document_id:int) -> str:
    """
    Returns the html generated for a currency answer based question

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: HTML for the currency field and question
    :rtype: str
    """

    question_text = question['question']
    video_html = get_vimeo_html(question['question_id'])
    help_html = ''

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)    
    question_html = f"<div class='mb-3' data-question-id={question['question_id']} data-section-id={section_id}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <div class='input-group'>\
        <input type='number' step='0.5' style='margin-left: 20px;' class='form-control' value='{answer['text']}'\
        oninput='if(value<0)value=0;'>\
        <span class='input-group-text'>$</span>\
        </div>\
    </div>"
    return mark_safe(question_html)


def child_currency_field_html(question:dict, option_value:str, section_id:int, parent_question:int, user_document_id:int) -> str:
    """
    Returns the html for the nested child currency field

    :param question: Dict containing the necessary question fields
    :type question: Dict
    :param option_value: The value for the option if any
    :type option_value: str
    :param section_id: Id of the section containing the question
    :type section_id: int
    :param parent_question: Id of the parent question
    :tpye parent_question: int
    :param document_id: Id of the document containing the question
    :type document_id: int
    :return: String containing the html for the nested currency questions
    :rtype: str
    """

    question_html = ''
    question_text = question['question']
    video_html = get_vimeo_html(question['question_id'])
    answer = get_previous_answer_text_and_color(section_id, question['question_id'], user_document_id)
    
    hidden_attr = 'hidden'
    if is_option_selected(option_value, section_id, parent_question, user_document_id):
        hidden_attr = ''
    
    help_html = ''

    if 'helping_text' in question and question['helping_text'] != None and question['helping_text'] != 'None':
        help_html = f"<label {HELPER_TEXT_STYLING}>{question['helping_text']}</label>"

 
    question_html = f"<div class='mb-3 child_question' data-parent-option='{option_value}' data-question-id={question['question_id']} data-section-id={section_id} data-parent-question={parent_question} {hidden_attr}>\
        <label class='mb-2'><i class='mb-2 fa-sharp fa-solid fa-check-circle' id={question['question_id']} style='color: {answer['color']}'></i> <b style='font-weight: 450;'>{question_text}</b>{video_html}</label>\
        {help_html}\
        <div class='input-group'>\
        <input type='number' step='0.5' style='margin-left: 20px;' class='form-control' value='{answer['text']}'\
        oninput='if(value<0)value=0;'>\
        <span class='input-group-text'>$</span>\
        </div>\
    </div>"

    return question_html

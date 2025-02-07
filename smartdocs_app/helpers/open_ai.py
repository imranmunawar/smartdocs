from openai import OpenAI
from django.conf import settings


class OPENAI():

    def __init__(self) -> None:
        open_ai_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=open_ai_key)

    def get_answer_response(self, question_prompt:str):
        """
        Executes OPENAPI based query in the prompt provided

        :param question_prompt: Text to send as prompt
        :type question_prompt: ste
        """
        
        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": question_prompt},
                # {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
            ]
        )
    
        return completion.choices[0].message

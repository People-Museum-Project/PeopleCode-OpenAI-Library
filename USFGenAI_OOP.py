import os
from openai import OpenAI

DEFAULT_MODEL = "gpt-3.5-turbo"


"""
TODO:
if assistant for this person exists:
1. retrieve the ass_id from db
2. continue to send questions to openAI 

if assistant for this person not exist:
1. create Assistant(conversation) for each person
2. store the assistant_id into datastore
3. send the context and question to openAI
4. generate follow up questions to update the frontend choices.

history auto managed by this assistant
"""


class OpenAIClient:
    # each assistant must belong to a person_id
    def __init__(self):
        self.__api_key = os.getenv('OPENAI_API_KEY')
        if not self.__api_key:
            raise Exception("Error: The API key is not set. Set the environment variable 'OPENAI_API_KEY'.")
        self.__client = OpenAI(api_key=self.__api_key)
        self.__settings = {"model": DEFAULT_MODEL}
        # self.__person_id = person_id
        #
        # # try to retrieve the previous conversation
        # self.__assistant_id = get_assistant(self.__person_id)
        #
        # if not self.__assistant_id:
        #     # get context and send to chat
        #     pass



    def __set_context(self):
        # telling the AI the incoming conversation is based on this context
        # ask_xxx(context)
        pass

    def set_model(self, model_name):
        """
        Sets the model for the OpenAI API.
        model_options: ["gpt-3.5-turbo", "gpt-4", "gpt-4o"]

        Args:
            model_name (str): The model name.
        """
        self.__settings['model'] = model_name

    def ask_question(self, conversation, question, instructions, assistant_id=None):
        """
        Asks a question to the OpenAI Chat API.

        Args:
            conversation (list): The conversation history.
            question (str): The question to ask.
            instructions (str): Instructions or system prompt for the chat.
            assistant_id (str): The ID of the existing assistant.

        Returns:
            dict: The response from the OpenAI Chat API,
                  containing the reply and updated conversation.
        """

        if assistant_id is not None:
            return self.__ask_assistant(conversation, question, instructions, assistant_id)
        else:
            return self.__ask_openai(conversation, instructions)

    def ask_assistant_question(self, conversation, question, instructions, assistant_id):
        """
        Asks a question to an OpenAI Assistant with a specified ID.

        Args:
            question (str): The question to ask.
            instructions (str): Instructions or system prompt for the chat.
            conversation (list): The conversation history.
            assistant_id (str): The ID of the existing assistant.
        """
        return self.ask_question(conversation, question, instructions, assistant_id)

    def generate_sample_prompts(self, context, num_samples, max_words, assistant_id=None, followups=None):
        """
        Generates a prompt based on the context.

        Args:
            context (str): The context for generating the prompt.
            num_samples (int): Number of prompts to generate.
            max_words (int): Maximum number of words for the prompt.
            assistant_id (str): The ID of the existing assistant.
            followups (bool): Whether the prompts are follow-up questions.

        Returns:
            list: A list of generated prompts.
        """
        if followups is not None:
            instructions = f"Generate {num_samples} follow-up questions from the user perspective based on the conversation. Each follow-up question should be no more than {max_words} words. Only provide the prompts in the response"
        else:
            instructions = f"Generate {num_samples} sample prompts from the user perspective based on the context. Each sample prompt should be no more than {max_words} words. Only provide the questions in the response."

        if assistant_id is not None:
            return self.__generate_assistant_prompts(context, instructions, assistant_id)
        else:
            response = self.__client.chat.completions.create(model=self.__settings["model"], messages=[
                                                          {"role": "system", "content": instructions},
                                                          {"role": "user", "content": context}
                                                      ])
            (dict(response).get('usage'))
            (response.model_dump_json(indent=2))
            prompts = response.choices[0].message.content.strip().split('\n')
            return prompts

    def generate_assistant_sample_prompts(self, context, num_samples, max_words, assistant_id):
        """
        Generates a prompt based on the OpenAI Assistant with a specified ID.

        Args:
            context (str): The context for generating the prompt.
            num_samples (int): Number of prompts to generate.
            max_words (int): Maximum number of words for the prompt.
            assistant_id (str): The ID of the existing assistant.
        """
        return self.generate_sample_prompts(context, num_samples, max_words, assistant_id)

    def generate_followups(self, question, response, num_samples, max_words, assistant_id=None):
        """
        Generates follow-up questions.

        Args:
            question (str): The previous question asked.
            response (str): The response to the previous question.
            num_samples (int): Number of follow-up questions to generate.
            max_words (int): Maximum number of words for each follow-up question.
            assistant_id (str): The ID of the existing assistant.

        Returns:
            list: A list of follow-up questions.
        """
        recent_history = f"User: {question}\nAssistant: {response}\n"
        return self.generate_sample_prompts(recent_history, num_samples, max_words, assistant_id, followups=True)

    def generate_assistant_followups(self, question, response, num_samples, max_words, assistant_id):
        """
        Generates follow-up questions based on the OpenAI Assistant with a specified ID.

        Args:
            question (str): The previous question asked.
            response (str): The response to the previous question.
            num_samples (int): Number of follow-up questions to generate.
            max_words (int): Maximum number of words for each follow-up question.
            assistant_id (str): The ID of the existing assistant.

        Returns:
            list: A list of follow-up questions.
        """
        return self.generate_followups(question, response, num_samples, max_words, assistant_id)

    def __ask_assistant(self, conversation, question, instructions, assistant_id):
        """
        Private function to ask a question to an OpenAI Assistant with a specified ID.

        Args:
            conversation (list): The conversation history.
            question (str): The question to ask.
            instructions (str): Instructions or system prompt for the chat.
            assistant_id (str): The ID of the existing assistant.

        Returns:
            dict: The response from the OpenAI Chat API,
                  containing the reply with citations and updated conversation.
        """
        # Create a new thread
        thread = self.__client.beta.threads.create()

        # Add the user's question to the thread
        self.__client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )

        # Run the assistant
        run = self.__client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            instructions=instructions
        )

        if run.status == 'completed':
            # List all messages in the thread
            messages = self.__client.beta.threads.messages.list(
                thread_id=thread.id
            )

            # Get the latest assistant message
            latest_message = None
            for message in messages.data:
                if message.role == "assistant":
                    latest_message = message.content[0].text.value
                    annotations = message.content[0].text.annotations
                    for index, annotation in enumerate(annotations):
                        if file_citation := getattr(annotation, "file_citation", None):
                            cited_file = self.__client.files.retrieve(file_citation.file_id)
                            latest_message = latest_message.replace(annotation.text, f"[{index}]({cited_file.filename})")
                            latest_message += f"\n[{index}] {cited_file.filename}"

            if latest_message:
                return {"reply": latest_message, "conversation": conversation}
            else:
                return {"reply": None, "conversation": conversation}
        else:
            return {"reply": None, "conversation": conversation}

    def __ask_openai(self, conversation, instructions):
        """
        Private function to ask a question to the OpenAI Chat API.

        Args:
            conversation (list): The conversation history.
            instructions (str): Instructions or system prompt for the chat.

        Returns:
            dict: The response from the OpenAI Chat API,
                  containing the reply and updated conversation.
        """
        response = self.__client.chat.completions.create(model=self.__settings["model"],
                                                  messages=[
                                                               {"role": "system", "content": instructions}
                                                           ] + conversation)
        (dict(response).get('usage'))
        (response.model_dump_json(indent=2))
        answer = response.choices[0].message.content.strip()
        conversation.append({"role": "assistant", "content": answer})
        return {"reply": answer, "conversation": conversation}

    def __generate_assistant_prompts(self, context, instructions, assistant_id):
        """
        Private function to generate prompts using an OpenAI Assistant.

        Args:
            context (str): The context for generating the prompt.
            instructions (str): Instructions or system prompt for the chat.
            assistant_id (str): The ID of the existing assistant.

        Returns:
            list: A list of generated prompts.
        """
        # Create a new thread
        thread = self.__client.beta.threads.create()

        # Add the user's question to the thread
        self.__client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=context
        )

        # Run the assistant
        run = self.__client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            instructions=instructions
        )

        if run.status == 'completed':
            # List all messages in the thread
            messages = self.__client.beta.threads.messages.list(
                thread_id=thread.id
            )

            # Get the latest assistant message
            prompts = []
            for message in messages.data:
                if message.role == "assistant":
                    prompts = message.content[0].text.value.split('\n')
            return prompts
        else:
            return []



# def text_to_speech(text, voice=None):
#     """
#     Converts text to speech using OpenAI's TTS model.
#
#     Args:
#         text (str): The text to convert to speech.
#         voice: The voice to use.
#
#     Returns:
#         object: The response object from OpenAI audio API.
#     """
#     if not voice:
#         voice = "alloy"
#     try:
#         speech_file_path = Path(__file__).parent / "speech.mp3"
#         response = client.audio.speech.create(
#             model="tts-1",
#             voice=voice,
#             input=text
#         )
#         response.stream_to_file(speech_file_path)
#         return response.content
#     except Exception as e:
#         print(f"Error converting text to speech: {e}")
#         return None
#
#
# def speech_recognition(file):
#     """
#     Converts speech to text using OpenAI's Whisper model.
#
#     Args:
#         file (str): Path to the audio file.
#
#     Returns:
#         str: The transcribed text.
#     """
#     with open(file, "rb") as audio_file:
#         translation = client.audio.translations.create(
#             model="whisper-1",
#             file=audio_file
#         )
#     return translation.text



if __name__ == "__main__":
    openai_client = OpenAIClient()
    openai_client.set_model("gpt-3.5-turbo")

    conversation = []
    response = openai_client.ask_question(conversation, "What is the capital of France?",
                                          "You are a helpful assistant.")
    print(response["reply"])

    prompts = openai_client.generate_sample_prompts("Tell me about climate change", 3, 10)
    print(prompts)

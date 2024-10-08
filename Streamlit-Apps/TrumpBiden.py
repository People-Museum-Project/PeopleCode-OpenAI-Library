# ChatAppStreamlit.py
# This creates a Streamlit application that interacts with OpenAI's language models.
# It allows users to select a model, ask questions, generate prompts, and handle follow-up questions.

import os
import streamlit as st
from PeopleCodeOpenAI import OpenAI_Conversation


def get_questions():
    return [
        "Compare Trump/Biden on Women's Rights",
        "Compare Trump/Biden on Civil Rights",
        "What are typical behaviors of an aspiring autocrat?",
        "Has Donald Trump exhibited the behavior of an aspiring autocrat?",
        "Is a peaceful transition to power important to a democracy?",
        "Did Trump facilitate the peaceful transition to power on Jan 6, 2021?"
    ]


# Function to handle question submission
def ask_it():
    if st.session_state.cur_question >= 0:
        # Use predefined questions
        question = questions[st.session_state.cur_question]
        response = conversation_manager.ask_question(st.session_state.conversation, question)
        st.text_area("OpenAI's Response:", response, height=300)

        # Additional information for the specific question index
        if st.session_state.cur_question == 5:
            st.text_area("Additional Information", """Democracy depends on elections, the rule of law, and a peaceful transition of power. On Jan 6, 2021, the transition of power was to take place, with the newly elected President, Joe Biden, to be officially confirmed as the new President. On that day, the outgoing President, Donald Trump, spoke to a rally of heavily armed supporters and implored them to go to the Capitol Building and stop the proceedings. He called his own Vice President, Mike Pence, a coward for performing his duties and confirming the new President. The crowd of supporters erected a hanging gallows and chanted for Pence to be hung.
                     """, height=160)
            st.image(
                "https://image.cnbcfm.com/api/v1/image/106823110-1610469786347-gettyimages-1230476983-horse-trumpsup210106_npiO7.jpeg?v=1641421093&w=740&h=416&ffmt=webp&vtcrop=y")
            st.text_area("", """Trump watched on television as the mob broke into the Capitol. The Congress members and Vice President fled and hid for their lives as the mob stormed into the chambers. Trump received reports of the activity from his colleagues and did nothing to call back the mob. Instead, he sent out the following tweet:
                     """, height=140)
            st.image("https://pbs.twimg.com/media/Et5lNX4XMAMAjH8.jpg")
            st.text_area("", """Casey Hutchinson, assistant to Trump’s Chief of Staff Mark Meadows, testified that Trump was chanting “Hang” as he watched the action on television. Here is some of her testimony to the Jan 6 commission (with Co-Chair, Republican Liz Cheney)
                    """)
            st.video("https://www.youtube.com/watch?v=q7aaXt3EARg")
    else:
        # Use user-provided input
        if st.session_state.text_input_value:
            response = conversation_manager.ask_question(st.session_state.conversation, st.session_state.text_input_value)
            st.text_area("OpenAI's Response:", response, height=300)


# Load API key from environment variable
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("Error: The API key is not set. Set the environment variable 'OPENAI_API_KEY'.")
    st.stop()

# Initialize OpenAI_Conversation
conversation_manager = OpenAI_Conversation(api_key=api_key)

# Initialize questions
questions = get_questions()

# Streamlit App
st.title("Election 2024: Is Voting Worth It?")

# Model selection
model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4o"]
selected_model = model_options[1]
conversation_manager.set_model(selected_model)

# Initialize session state variables
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

if 'text_input_value' not in st.session_state:
    st.session_state.text_input_value = ""

if 'cur_question' not in st.session_state:
    st.session_state.cur_question = -1

# Layout for predefined questions
container = st.container()
with container:
    cols = st.columns(3)
    for i, question in enumerate(questions[:6]):
        with cols[i % 3]:
            if st.button(question):
                st.session_state.text_input_value = question
                st.session_state.cur_question = i

# User prompt input
user_prompt = st.text_input("Your Question:", value=st.session_state.text_input_value, key='user_prompt')

# Update state when text input changes
if user_prompt != st.session_state.text_input_value:
    st.session_state.text_input_value = user_prompt
    st.session_state.cur_question = -1

# Ask button
if st.button("Ask"):
    ask_it()

from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

import streamlit as st

st.set_page_config(page_title="Reklaim AI Playground: Chatbot", page_icon="📖")
st.title("Reklaim AI Playground: Chatbot")

"""
Help, my peronal data was exposed in a breach, what should i do?

How do I setup two factor authentication on gmail?

What's a good password manager and can you help me setup it up?

Is this link safe?

What are some phishing and smishing attacks I should be aware of?

How do I know if I am at risk?

(The messages are stored in Session State across re-runs automatically. You can view the contents of Session State
in the expander below. )
"""

# Set up memory
msgs = StreamlitChatMessageHistory(key="langchain_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

view_messages = st.expander("View the message contents in session state")

# Get an OpenAI API Key before continuing
if "openai_api_key" in st.secrets:
    openai_api_key = st.secrets.openai_api_key
else:
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Enter an OpenAI API Key to continue")
    st.stop()

# Set up the LangChain, passing in Message History
sys_msg = """
Your purpose is to help users better understand and improve their security posture online. You are designed to assist individual users. When possible, tailor responses to the user's technical expertise and comfort level, which is inferred from their inquiries and interactions.

In general, aim to provide detailed responses with practical advice. Use real world  or realistic examples and step-by-step guidance. Provide specific security recommendations based on the user's operating system, when possible.
If explaining phishing or smishing attacks provide specific examples of the relevant messages and copy for that specific scam. 

When discussing anything requiring multiple steps, ask the user if they would  like to walk through it one step at a time.
For example, when providing guidance that involves multiple steps for the user, offer help on any individual step and offer help walking through with your guidance one step at a time..

It is also important that you are proactive with the user. When appropriate, ask them if they need more details or assistance setting things up.

If the user submits a link to an online privacy policy, without any other context, by default, explain the policy to the user like they were a 5 year old.



It is important to be up to date on online scams and able to help with basic security best practices to stay safe like proper password management and 2 factor authentication. 

Please use the articles at https://www.ic3.gov/Home/ConsumerAlerts?pressReleasesYear=_Current and https://www.ic3.gov/Home/ConsumerAlerts?pressReleasesYear=_2023 and https://consumer.ftc.gov/consumer-alerts?items_per_page=100&search=&field_author_value=&field_date_time_value%5Bmin%5D=&field_date_time_value%5Bmax%5D= 
https://firewalltimes.com/category/breaches/
https://www.bleepingcomputer.com/tag/phishing/

for recent information on some of the latest attacks, Breaches  and consumer alerts.

Please use the content at https://www.android.com/safety/, https://support.apple.com/guide/security/welcome/web and https://support.microsoft.com/en-us/security to provide users with the most up to date platform specific guidance.

Please use the content at https://www.reklaimyours.com for questions regarding data monetization
Please use the content at https://lifelabssettlement.kpmg.ca to answer any questions about the Life Labs data breach.

If the user asks a question regarding their secure posture or reducing their risk in general
then answer their question directly and offer to walk them through a quick 10 question assessment 

If the user wants to do a self assessment 
then please ask 10 questions, one at a time and provide a final score and recommendations once you have asked all questions
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", sys_msg),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

# chain = prompt | ChatOpenAI(api_key=openai_api_key)
api_key = st.secrets.groq_api_key
chain = prompt | ChatGroq(temperature=0, groq_api_key=api_key, model_name="llama3-70b-8192")
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: msgs,
    input_messages_key="question",
    history_messages_key="history",
)

# Render current messages from StreamlitChatMessageHistory
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

# If user inputs a new prompt, generate and draw a new response
if prompt := st.chat_input():
    st.chat_message("human").write(prompt)
    # Note: new messages are saved to history automatically by Langchain during run
    config = {"configurable": {"session_id": "any"}}
    response = chain_with_history.invoke({"question": prompt}, config)
    st.chat_message("ai").write(response.content)

# Draw the messages at the end, so newly generated ones show up immediately
with view_messages:
    """
    Message History initialized with:
    ```python
    msgs = StreamlitChatMessageHistory(key="langchain_messages")
    ```

    Contents of `st.session_state.langchain_messages`:
    """
    view_messages.json(st.session_state.langchain_messages)

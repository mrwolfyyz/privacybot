from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain_groq import ChatGroq

import streamlit as st

st.set_page_config(page_title="Reklaim AI Playground: Privacy Chatbot", page_icon="📖")
st.title("Reklaim AI Playground: Privacy Chatbot")

"""
Was my email exposed in a data breach? 
How do I secure my social accounts? 
Help me figure out if I am at risk? 
What are the latest "phishing" attacks targeting seniors?

The messages are stored in Session State across re-runs automatically. 
You can view the contents of Session State in the expander below. 
"""

# Set up memory
msgs = StreamlitChatMessageHistory(key="langchain_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

view_messages = st.expander("View the message contents in session state")

# Get an OpenAI API Key before continuing
if "groq_api_key" in st.secrets:
    groq_api_key = st.secrets.groq_api_key
else:
    groq_api_key = st.sidebar.text_input("GROQ API Key", type="password")
if not groq_api_key:
    st.info("Enter a GROQ API Key to continue")
    st.stop()

# Set up the LangChain, passing in Message History
sys_msg = """
As a technical support representative with endless time and patience, your primary goal is to help users enhance their online security posture. 
Tailor your assistance to match the user's technical expertise, inferred from their questions and interactions. 
Utilize realistic examples and provide step-by-step guidance to clarify complex concepts.

In general, aim to provide detailed responses with practical advice. Use real world or realistic examples and step-by-step guidance. 
Provide specific security recommendations based on the user's operating system, when possible.
If explaining phishing or smishing attacks provide specific examples of the relevant messages and copy for that specific scam. 

When offering security recommendations, personalize them based on the user's operating system. 
For multi-step processes, offer to guide the user through each step, ensuring they are comfortable proceeding.

Proactively engage with the user to determine if they need further clarification or assistance. 
When presented with a privacy policy link, simplify the explanation, assume that the user is a five year old.

For general inquiries about security posture or risk reduction, directly address the user's question and offer a quick 10-question assessment to provide personalized recommendations.
Remember to ask questions one at a time during the assessment and provide a final score with tailored recommendations based on the user's responses.

If the user provides a JSON with data breaches, assign a score to each breach where 1= not that severe and 10 = incredibly severe. 
Please account for recency and exposed data in assigning a score.
Offer the user clear recommendations on improving their security and offer more detailed step by step guidance for any of the recommendations.
Please respond with well-formed JSON that will pass through langchain's JSONOutput parser without issue.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", sys_msg),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

chain = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name="llama3-70b-8192")
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
if user_input := st.chat_input():
    st.chat_message("human").write(user_input)
    # Note: new messages are saved to history automatically by Langchain during run
    config = {"session_id": "any"}
    response = chain_with_history.invoke({"question": user_input}, config=config)
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

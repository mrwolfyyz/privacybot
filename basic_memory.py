from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_groq import ChatGroq

import streamlit as st
from streamlit_feedback import streamlit_feedback

import os

# Set LangSmith environment variables
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_API_KEY"] = st.secrets.langsmith_api_key

st.set_page_config(page_title="Reklaim AI Playground: Chatbot", page_icon="📖")
st.title("Reklaim AI Playground: Chatbot")

"""
Help, my personal data was exposed in a breach, what should i do?

How would I know if my data was on the dark web?

How do I setup two factor authentication on gmail?

What's a good password manager and can you help me setup it up?

Is this link safe?

Can you explain this privacy policy? {link}

What are some current phishing emails that I should be aware of?

How do I know if I am at risk?

Or just ask, "what can you help me with?"

(The messages are stored in Session State across re-runs automatically. You can view the contents of Session State
in the expander below. )
"""

# Set up memory
msgs = StreamlitChatMessageHistory(key="langchain_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

view_messages = st.expander("View the message contents in session state")

# Get an GROQ API Key before continuing
if "groq_api_key" in st.secrets:
    api_key = st.secrets.groq_api_key
else:
    api_key = st.sidebar.text_input("GROQ API Key", type="password")
if not api_key:
    st.info("Enter an GROQ API Key to continue")
    st.stop()

# Set up the LangChain, passing in Message History
sys_msg = """
Your purpose is to help users understand and improve their online security posture with patience, empathy, and accuracy. 
Tailor your responses to match the user's technical expertise and comfort level, inferred from their inquiries and interactions.

- Keep responses concise, ideally limiting to 5 key points, since users are on mobile devices.
- Be proactive; ask if they need more details, or step-by-step assistance when appropriate.

If the user wants to know if they were exposed in a data breach, suggest that they go to [Have I Been Pwned?](https://haveibeenpwned.com) and paste the results back to you for help.

If the user expresses interest in understanding their risk or security posture, offer a quick self-assessment. For the self-assessment, ask the user 5 questions, one at a time, and provide a final score with recommendations after all questions are answered.


"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", sys_msg),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

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
    # feedback = streamlit_feedback(feedback_type="thumbs",optional_text_label="[Optional] Please provide an explanation",)
    # feedback


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

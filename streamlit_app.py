import streamlit as st
import replicate
import requests
import os

# App title
st.set_page_config(page_title="🦙💬 Llama 2 Chatbot")

# API URL and headers
API_URL = "https://kvx8b7athbozllwt.us-east-1.aws.endpoints.huggingface.cloud"
headers = {
    "Content-Type": "application/json"
}

# Replicate Credentials
with st.sidebar:
    st.title('🦙💬 Bioscientist')

    # Check if Replicate API token is read from secrets
    if 'REPLICATE_API_TOKEN' in st.secrets:
        st.success('Replicate API key already provided!', icon='✅')
        replicate_api = st.secrets['REPLICATE_API_TOKEN']
    else:
        st.warning('Please enter your Replicate API token!', icon='⚠️')
        replicate_api = st.text_input('Enter Replicate API token:', type='password')
    
    # Check if Hugging Face API token is read from secrets
    if 'HUGGINGFACE_API_TOKEN' in st.secrets:
        st.success('Hugging Face API key already provided!', icon='✅')
        huggingface_token = st.secrets['HUGGINGFACE_API_TOKEN']
    else:
        st.warning('Please enter your Hugging Face API token!', icon='⚠️')
        huggingface_token = st.text_input('Enter Hugging Face API token:', type='password')

    # Store API tokens in environment variables
    os.environ['REPLICATE_API_TOKEN'] = replicate_api
    os.environ['HUGGINGFACE_API_TOKEN'] = huggingface_token

    st.subheader('Models and parameters')

    # Selected model and corresponding API endpoint
    selected_model = st.selectbox('Choose a Llama2 model', ['Llama2-7B', 'Llama2-13B', 'BioLlama2-7B'], key='selected_model')
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    elif selected_model == 'BioLlama2-7B':
        llm = 'https://kvx8b7athbozllwt.us-east-1.aws.endpoints.huggingface.cloud'  # API endpoint for BioLlama2-7B

    temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
    top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.sidebar.slider('max_length', min_value=32, max_value=1000, value=1000, step=8)
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')


def query(payload):
    headers["Authorization"] = f"Bearer {os.environ['HUGGINGFACE_API_TOKEN']}"
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def generate_llama2_response(prompt_input, model):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    if model == 'BioLlama2-7B':
        response = query({
            "inputs": f"{string_dialogue} {prompt_input} Assistant: ",
            "parameters": {"max_new_tokens": 1000},
        })
        output = [response[0]["generated_text"]]  # Output extraction for BioLlama2-7B
    else:
        output = replicate.run(llm, {
            "prompt": f"{string_dialogue} {prompt_input} Assistant: ",
            "temperature": temperature,
            "top_p": top_p,
            "max_length": max_length,
            "repetition_penalty": 1
        })
    return output


# Store LLM generated responses for each chat session
if "messages" not in st.session_state.keys():
    st.session_state.messages = {"session_1": [{"role": "assistant", "content": "How may I assist you today?"}]}


def chat_session(session_id):
    session_messages = st.session_state.messages[session_id]
    with st.expander(f"Chat Session {session_id}"):
        # Display or clear chat messages
        for message in session_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if prompt := st.chat_input(disabled=not replicate_api, key=f"chat_input_{session_id}"):
            session_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

        # Generate a new response if last message is not from assistant
        if session_messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = generate_llama2_response(prompt, selected_model)
                    placeholder = st.empty()
                    full_response = ''
                    for item in response:
                        full_response += item
                        placeholder.markdown(full_response)
                    placeholder.markdown(full_response)
            message = {"role": "assistant", "content": full_response}
            session_messages.append(message)

# # Generate a new response if last message is not from assistant
# if st.session_state.messages[-1]["role"] != "assistant":
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             response = generate_llama2_response(prompt)
#             placeholder = st.empty()
#             full_response = ''
#             for item in response:
#                 full_response += item
#                 placeholder.markdown(full_response)
#             placeholder.markdown(full_response)
#     message = {"role": "assistant", "content": full_response}
#     st.session_state.messages.append(message)


# Create a grid layout for chat sessions
num_sessions = 5
col1, col2, col3, col4, col5 = st.beta_columns(5)

# Chat Session 1
chat_session("session_1")
if col1.button("Delete Session"):
    st.session_state.messages.pop("session_1", None)

with col1:
    if col1.button("Add New Chat Session"):
        st.session_state.messages["session_2"] = [{"role": "assistant", "content": "How may I assist you today?"}]

# Chat Session 2
if "session_2" in st.session_state.messages:
    chat_session("session_2")
    if col2.button("Delete Session"):
        st.session_state.messages.pop("session_2", None)

    with col2:
        if col2.button("Add New Chat Session"):
            st.session_state.messages["session_3"] = [{"role": "assistant", "content": "How may I assist you today?"}]

# Chat Session 3
if "session_3" in st.session_state.messages:
    chat_session("session_3")
    if col3.button("Delete Session"):
        st.session_state.messages.pop("session_3", None)

    with col3:
        if col3.button("Add New Chat Session"):
            st.session_state.messages["session_4"] = [{"role": "assistant", "content": "How may I assist you today?"}]

# Chat Session 4
if "session_4" in st.session_state.messages:
    chat_session("session_4")
    if col4.button("Delete Session"):
        st.session_state.messages.pop("session_4", None)

    with col4:
        if col4.button("Add New Chat Session"):
            st.session_state.messages["session_5"] = [{"role": "assistant", "content": "How may I assist you today?"}]

# Chat Session 5
if "session_5" in st.session_state.messages:
    chat_session("session_5")
    if col5.button("Delete Session"):
        st.session_state.messages.pop("session_5", None)

# Generate LLM response for active chat sessions
for session_id, session_messages in st.session_state.messages.items():
    if session_messages[-1]["role"] != "assistant":
        with st.spinner("Thinking..."):
            response = generate_llama2_response(session_messages[-1]["content"], selected_model)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            session_messages.append({"role": "assistant", "content": full_response})

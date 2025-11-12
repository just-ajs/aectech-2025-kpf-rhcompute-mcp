import streamlit as st
import json
from strands import Agent
from strands.models import BedrockModel
from strands.models.ollama import OllamaModel
from strands.models.openai import OpenAIModel
from strands.models.gemini import GeminiModel
from strands_tools import calculator, current_time, http_request
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient
from contextlib import ExitStack


# ========== MCP SERVER CONFIGURATION ==========
# Add or remove MCP server URLs here
MCP_SERVER_URLS = [
    "http://localhost:8000/mcp"
    # Add more servers as needed:
    #"http://localhost:8001/mcp",
    #"http://localhost:8002/mcp",
]
# ==============================================

# Initialize MCP clients in session state
if "mcp_clients" not in st.session_state:
    st.session_state.mcp_clients = [
        MCPClient(lambda url=url: streamablehttp_client(url))
        for url in MCP_SERVER_URLS
    ]

# Initialize MCP tools in session state
if "mcp_tools" not in st.session_state:
    # Use all servers together to get tools
    with ExitStack() as stack:
        # Enter all client contexts
        for client in st.session_state.mcp_clients:
            stack.enter_context(client)
        
        # Combine tools from all servers
        all_tools = []
        for i, client in enumerate(st.session_state.mcp_clients):
            tools = client.list_tools_sync()
            all_tools.extend(tools)
            print(f"MCP Server {i+1} ({MCP_SERVER_URLS[i]})")
            for tool in tools:
                print(f"Tool: {tool.tool_name}")
        
        st.session_state.mcp_tools = all_tools

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add title on the page
st.title("Strands Agents and MCP servers")

# Define agent
system_prompt = """You are a helpful personal assistant that 
specializes in architectura design using Rhino 
and Grasshopper tools."""

# Create an Ollama model instance
ollama_model = OllamaModel(
    host="http://10.100.8.219:11434", 
    model_id="gpt-oss:120b" ,    
)

# OpenAI model instance
openai_model = OpenAIModel(
    client_args={
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    model_id="gpt-4o-mini",
    params={
        "temperature": 0.3,
        "max_tokens": 2048,
    }
)
# Gemini model instance
gemini_model = GeminiModel(
    client_args={
        "api_key": os.getenv("GOOGLE_API_KEY"),
    },
    model_id="gemini-2.5-flash",
    params={
        "temperature": 0.3,
        "max_output_tokens": 2048,
    }
)
# Bedrock model instance
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    max_tokens=2048,
    additional_request_fields={
        "thinking": {
            "type": "disabled",
        }
    },
)

# Initialize the agent
if "agent" not in st.session_state:
    st.session_state.agent = Agent(
        model=openai_model, ## pick the model you want to use
        system_prompt=system_prompt,
        tools=[
            current_time,
            calculator,
            http_request,
            st.session_state.mcp_tools
        ],
    )

# Display subtitle with current model info
subheader = "This demo shows how to use Strands to create an AI assistant and extend it with external tools."
if st.session_state.agent and hasattr(st.session_state.agent, 'model'):
    model_info = st.session_state.agent.model
    model_type = type(model_info).__name__.replace('Model', '')
    
    # Use get_config() method to retrieve model configuration
    try:
        config = model_info.get_config()
        model_name = config.get('model_id', 'Unknown Model')
    except:
        model_name = 'Unknown Model'
    
    st.write(f"{subheader} \n\n**Current Model:** {model_type} - `{model_name}`")
else:
    st.write(subheader)

# Keep track of the number of previous messages in the agent flow
if "start_index" not in st.session_state:
    st.session_state.start_index = 0

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.empty()  # This forces the container to render without adding visible content (workaround for streamlit bug)
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask your agent..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Clear previous tool usage details
    if "details_placeholder" in st.session_state:
        st.session_state.details_placeholder.empty()
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get response from agent (within MCP client contexts)
    with st.spinner("Thinking..."):
        with ExitStack() as stack:
            # Enter all client contexts
            for client in st.session_state.mcp_clients:
                stack.enter_context(client)
            
            response = st.session_state.agent(prompt)
    
    # Extract the assistant's response text
    assistant_response = ""
    for m in st.session_state.agent.messages:
        if m.get("role") == "assistant" and m.get("content"):
            for content_item in m.get("content", []):
                if "text" in content_item:
                    # We keep only the last response of the assistant
                    assistant_response = content_item["text"]
                    break
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
    # Display assistant response
    with st.chat_message("assistant"):
        
        start_index = st.session_state.start_index      

        # Display last messages from agent, with tool usage detail if any
        st.session_state.details_placeholder = st.empty()  # Create a new placeholder
        with st.session_state.details_placeholder.container():
            for m in st.session_state.agent.messages[start_index:]:
                if m.get("role") == "assistant":
                    for content_item in m.get("content", []):
                        if "text" in content_item:
                            st.write(content_item["text"])
                        elif "toolUse" in content_item:
                            tool_use = content_item["toolUse"]
                            tool_name = tool_use.get("name", "")
                            tool_input = tool_use.get("input", {})
                            st.info(f"Using tool: {tool_name}")
                            st.code(json.dumps(tool_input, indent=2))
            
                elif m.get("role") == "user":
                    for content_item in m.get("content", []):
                        if "toolResult" in content_item:
                            tool_result = content_item["toolResult"]
                            st.info(f"Tool Result: {tool_result.get('status', '')}")
                            for result_content in tool_result.get("content", []):
                                if "text" in result_content:
                                    st.code(result_content["text"])

        # Update the number of previous messages
        st.session_state.start_index = len(st.session_state.agent.messages)

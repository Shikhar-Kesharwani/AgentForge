import json
import os
from typing import Generator, Any
from google import genai
from google.genai import types
from agent.tools import AVAILABLE_TOOLS
from agent.memory import retrieve_memories, store_memory

# Gemini tool definitions
GEMINI_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="search",
                description="Search the web for information using DuckDuckGo.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(type=types.Type.STRING, description="The search query.")
                    },
                    required=["query"]
                )
            ),
            types.FunctionDeclaration(
                name="run_code",
                description="Execute Python code in a sandboxed subprocess and get the output.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "code": types.Schema(type=types.Type.STRING, description="The Python code to execute. Must be valid Python code.")
                    },
                    required=["code"]
                )
            ),
            types.FunctionDeclaration(
                name="read_file",
                description="Read the contents of a file from the workspace.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "filename": types.Schema(type=types.Type.STRING, description="The name of the file to read.")
                    },
                    required=["filename"]
                )
            ),
            types.FunctionDeclaration(
                name="write_file",
                description="Write contents to a file in the workspace.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "filename": types.Schema(type=types.Type.STRING, description="The name of the file to write to."),
                        "content": types.Schema(type=types.Type.STRING, description="The content to write to the file.")
                    },
                    required=["filename", "content"]
                )
            ),
            types.FunctionDeclaration(
                name="list_dir",
                description="List all files in the workspace directory."
            ),
            types.FunctionDeclaration(
                name="fetch_url",
                description="Fetch and extract plain text from a URL.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "url": types.Schema(type=types.Type.STRING, description="The URL to scrape.")
                    },
                    required=["url"]
                )
            )
        ]
    )
]

def build_context(task: str) -> str:
    """Build the system context with relevant memories."""
    memories = retrieve_memories(task, n_results=3)
    
    context = (
        "You are a helpful AI agent with access to tools (web search, python execution, file read/write). "
        "Use your tools to accomplish the user's task. If a tool fails, try to fix the error or use a different approach. "
        "After gathering enough information and completing the task, provide a final response summarizing the outcome to the user.\n\n"
    )
    
    if memories:
        context += "Here are some relevant memories from past tasks that might help you:\n"
        for mem in memories:
            context += f"- {mem}\n"
    
    return context

def run_agent_loop(task: str, history: list[dict] = None, max_iterations: int = 15) -> Generator[dict[str, Any], None, None]:
    """
    Run the custom orchestration loop.
    Yields intermediate steps (tool calls) and the final response.
    """
    if history is None:
        history = []
        
    client = genai.Client()
    system_instruction = build_context(task)
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=GEMINI_TOOLS,
        temperature=0.2,
    )
    
    # Initialize chat history with existing session history
    api_history = []
    for msg in history:
        # Convert custom roles to gemini roles if needed
        # Our frontend sends 'user-message' -> 'user', 'agent-message' -> 'model'
        role = "user" if msg["role"] == "user-message" else "model"
        api_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
        
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=config,
        history=api_history
    )
    
    iterations = 0
    consecutive_failures = 0
    last_failed_tool = None
    
    # Send the initial user task
    user_message = task
    
    yield {"type": "status", "content": "Starting agent loop..."}
    
    try:
        response_stream = chat.send_message_stream(user_message)
    except Exception as e:
        yield {"type": "error", "content": f"API Error: {str(e)}"}
        return

    while iterations < max_iterations:
        iterations += 1
        
        has_tool_call = False
        final_text_accumulator = ""
        
        try:
            for chunk in response_stream:
                if chunk.function_calls:
                    has_tool_call = True
                    function_responses = []
                    for function_call in chunk.function_calls:
                        tool_name = function_call.name
                        args = function_call.args
                        
                        yield {"type": "tool_call", "tool": tool_name, "args": args}
                        
                        # Execute the tool
                        try:
                            if tool_name in AVAILABLE_TOOLS:
                                tool_func = AVAILABLE_TOOLS[tool_name]
                                result = tool_func(**args)
                                is_error = "Error" in str(result)
                            else:
                                result = f"Error: Tool '{tool_name}' not found."
                                is_error = True
                        except Exception as e:
                            result = f"Error executing tool: {str(e)}"
                            is_error = True
                        
                        # Circuit Breaker Logic
                        if is_error:
                            if tool_name == last_failed_tool:
                                consecutive_failures += 1
                            else:
                                last_failed_tool = tool_name
                                consecutive_failures = 1
                                
                            if consecutive_failures >= 3:
                                msg = f"Circuit Breaker Triggered: Tool '{tool_name}' failed 3 times in a row. Halting agent."
                                yield {"type": "error", "content": msg}
                                return
                        else:
                            consecutive_failures = 0
                            last_failed_tool = None

                        yield {"type": "tool_result", "tool": tool_name, "result": result[:500] + ("..." if len(result) > 500 else "")}
                        
                        # Accumulate the response
                        function_responses.append(
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": result}
                            )
                        )
                    
                    # Set up the response for the next loop iteration with ALL function responses
                    response_stream = chat.send_message_stream(function_responses)
                    break # Break the chunk loop since we need to process the next response_stream
                elif chunk.text:
                    final_text_accumulator += chunk.text
                    yield {"type": "final_answer_chunk", "content": chunk.text}
        except Exception as e:
            yield {"type": "error", "content": f"API Error during stream: {str(e)}"}
            return
            
        if not has_tool_call:
            # Model provided a text response without tool calls, and stream is complete
            yield {"type": "final_answer", "content": ""} # Signal completion
            
            # Store the outcome in long-term memory
            store_memory(task, final_text_accumulator)
            break
            
    if iterations >= max_iterations:
        yield {"type": "error", "content": "Max iterations reached. Task stopped."}

from agent import byo_chatgpt
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
import os

# Load environment variables
load_dotenv()

def format_message(message):
    """Helper function to format different types of messages"""
    if isinstance(message, (HumanMessage, AIMessage)):
        return {
            "type": "human" if isinstance(message, HumanMessage) else "ai",
            "content": message.content
        }
    return str(message)

def main():
    print("Welcome to the LangChain Agent!")
    print("You can ask questions, request image generation, or execute Python code.")
    print("Type 'exit' to quit.")
    print("\nExample queries:")
    print("- 'What is the capital of France?'")
    print("- 'Generate an image of a sunset over mountains'")
    print("- 'What is 2 + 2?'")
    print("- 'Write a Python function to calculate fibonacci numbers'")
    print("\nEnter your query:")
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
            
        try:
            print("\nDebug: Sending request to agent...")
            response = byo_chatgpt.invoke({
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            })
            
            print("\nDebug: Response structure:")
            if isinstance(response, dict):
                for key, value in response.items():
                    print(f"\nKey: {key}")
                    if isinstance(value, list):
                        print(f"  Number of messages: {len(value)}")
                        print("\nDebug: Message flow:")
                        for i, item in enumerate(value):
                            print(f"\nStep {i + 1}:")
                            if isinstance(item, HumanMessage):
                                print(f"  Human: {item.content}")
                            elif isinstance(item, AIMessage):
                                print(f"  AI: {item.content}")
                                # Show tool calls if any
                                if item.additional_kwargs.get('tool_calls'):
                                    for tool_call in item.additional_kwargs['tool_calls']:
                                        print(f"  → Tool call: {tool_call['function']['name']}")
                                        print(f"    Arguments: {tool_call['function']['arguments']}")
                            elif hasattr(item, 'name') and hasattr(item, 'content'):  # ToolMessage
                                print(f"  Tool ({item.name}): {item.content}")
                        
                        # Find and show the final response
                        last_ai_message = None
                        for item in value:
                            if isinstance(item, AIMessage) and item.content and not item.additional_kwargs.get('tool_calls'):
                                last_ai_message = item
                        if last_ai_message:
                            print("\nFinal Response:")
                            print("Agent:", last_ai_message.content)
                        else:
                            print("\nAgent: No final response generated.")
                    else:
                        print(f"  Value: {format_message(value)}")
            else:
                print("\nAgent: No response generated.")
                
        except Exception as e:
            print(f"\nError: {str(e)}")
            import traceback
            print("\nDebug: Full traceback:")
            print(traceback.format_exc())

if __name__ == "__main__":
    main() 
"""
Command-line interface for the Real Estate Agent.
"""

import os
from dotenv import load_dotenv
from typing import Union, Dict, Any
import time

from langchain_core.messages import AIMessage, HumanMessage

from agent import create_agent

# Load environment variables (ANTHROPIC_API_KEY)
load_dotenv()

def main():
    """Run the Real Estate Agent CLI."""
    print("\n🏠 Welcome to the Real Estate Agent Assistant! 🏠")
    print("I can help you evaluate properties by providing detailed information about homes and neighborhoods.")
    print("Type 'exit' or 'quit' to end the conversation.\n")
    
    # Initialize conversation state
    conversation_state = {"messages": []}
    
    # Create agent
    graph = create_agent()
    
    while True:
        # Get user input
        user_input = input("You: ")
        
        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nThank you for using the Real Estate Agent Assistant. Goodbye!")
            break
        
        try:
            # Add user message to conversation
            user_message = HumanMessage(content=user_input)
            conversation_state["messages"].append(user_message)
            
            print("Thinking...")
            start_time = time.time()
            
            # Run the conversation through the graph
            result = graph.invoke(conversation_state)
            
            # Update our conversation state
            conversation_state = result
            
            elapsed_time = time.time() - start_time
            
            # Output the AI's response (last message)
            if len(result["messages"]) > 0:
                last_message = result["messages"][-1]
                
                # Handle different message types
                if isinstance(last_message, AIMessage):
                    print(f"Assistant: {last_message.content}")
                elif isinstance(last_message, dict) and last_message.get("role") == "assistant":
                    print(f"Assistant: {last_message['content']}")
                else:
                    print(f"Assistant: {str(last_message)}")
                    
                print(f"[Response time: {elapsed_time:.2f}s]")
                
        except Exception as e:
            print(f"\nError: Something went wrong. {str(e)}")
            print("Please try again or ask a different question.")
    
if __name__ == "__main__":
    main()
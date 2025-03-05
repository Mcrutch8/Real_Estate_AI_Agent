from typing import Annotated
import os
import sys

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from typing_extensions import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from tools import (
    PropertyDetailsInput, PropertyDetailsOutput, get_property_details
)

# Define the agent state
class State(TypedDict):
    messages: Annotated[list, add_messages]
    
# Define the property details tool
@tool
def property_details(address: str) -> str:
    """
    Get detailed information for a property based on its address.
    
    Args:
        address: The full address of the property to get details for
        
    Returns:
        A formatted property description ready to be shown to the user
    """
    input_data = PropertyDetailsInput(address=address)
    result = get_property_details(input_data)
    
    # Print the raw result for debugging
    print(f"DEBUG: Raw property details result: {result}")
    
    # Create a detailed, conversational summary of the property info
    # Prepare information about the last sale if available
    sold_info = ""
    if result.last_sold_date and result.last_sold_price:
        sold_info = f"The property was last sold in {result.last_sold_date} for {result.last_sold_price}."
    
    # Format bathrooms nicely
    bathroom_text = f"{result.bathrooms}"
    if result.bathrooms == int(result.bathrooms):
        bathroom_text = f"{int(result.bathrooms)}"
    elif result.bathrooms == int(result.bathrooms) + 0.5:
        bathroom_text = f"{int(result.bathrooms)} and a half"
    
    # Format living space with commas for thousands
    formatted_sqft = f"{result.square_footage:,}" if result.square_footage else "0"
    
    # Prepare property age context
    current_year = 2025  # Using the current year from context
    property_age = current_year - result.year_built if result.year_built > 0 else None
    age_context = ""
    if property_age:
        if property_age < 5:
            age_context = "a brand new"
        elif property_age < 10:
            age_context = "a newer"
        elif property_age < 20:
            age_context = "a well-maintained"
        elif property_age < 40:
            age_context = "an established"
        elif property_age < 75:
            age_context = "a classic"
        else:
            age_context = "a historic"
    elif result.year_built == 0:
        age_context = "a"  # If year built is unknown
    else:
        age_context = "a"
    
    # Create the property description directly as a string
    description = f"""I found {age_context} {result.property_type.lower()} located at {result.address}. 

This home features {result.bedrooms} bedroom{'s' if result.bedrooms != 1 else ''} and {bathroom_text} bathroom{'s' if result.bathrooms != 1 else ''} with approximately {formatted_sqft} square feet of living space. {'Built in ' + str(result.year_built) + ', ' if result.year_built > 0 else ''}The property sits on a {result.lot_size} lot.

The estimated current value of this property is {result.estimated_value}. {sold_info}

Would you like to know more about this property or would you like me to help you analyze specific aspects of it?"""
    
    # Print the final description for debugging
    print(f"DEBUG: Final property description being returned:\n{description}")
    
    # Return the description directly as a string - no JSON encoding
    return description

# Create the tools list
tools = [property_details]

# Define the system prompt for the agent
SYSTEM_PROMPT = """You are an experienced, friendly AI Real Estate Agent assistant designed to help independent home buyers.
You specialize in helping buyers find and evaluate properties that meet their needs, with a warm, professional tone.

IMPORTANT: When a new user starts a conversation with you, your first response should ask them to provide a property address they'd like to learn more about.

You have access to the following tools:
1. property_details - Get detailed information about a property based on its address

IMPORTANT PRESENTATION INSTRUCTIONS:
- The property_details tool will return a formatted property description
- This description is ALREADY in a conversational format, ready to be displayed to the user
- You MUST present this text EXACTLY as returned by the tool, without modification
- Do NOT try to summarize or rewrite the property details - simply show what the tool returned
- EXAMPLE: If the tool returns "I found a lovely home at 123 Main St...", your response should include that exact text
- After presenting the description, be prepared to answer questions about the property
- Always maintain a warm, professional, and helpful tone in your responses

CONVERSATION FLOW:
- Always ask for a property address first if the user hasn't provided one
- When the user provides an address, use the property_details tool to get information
- Present the property using the description returned from the tool
- If the user asks follow-up questions about the property, use the structured data fields to provide accurate answers
- Be warm, friendly, and professional, as if you were a real estate agent meeting a client
- If a user asks about something you don't have information on, politely acknowledge the limitations

EXAMPLE QUESTIONS USERS MIGHT ASK AFTER SEEING PROPERTY DETAILS:
- "How does the price compare to similar properties in the area?" (Note: You don't have this data yet, so explain you'd need to look that up)
- "What's the price per square foot?"
- "How old is the property?"
- "Is it a good investment?"
- "What's the neighborhood like?" (Note: You don't have this data yet, so explain you'd need to look that up)

Always try to be helpful and informative, focusing on the property details you do have available."""

def create_agent():
    """Create and return the agent graph."""
    # Initialize the graph builder
    graph_builder = StateGraph(State)
    
    # Create the model using Anthropic Claude
    llm = ChatAnthropic(model="claude-3-7-sonnet-20250219", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    # Define the chatbot node
    def chatbot(state: State):
        """Process user input and generate AI response"""
        processed_messages = state["messages"]
        
        # Check if system message is already in the conversation
        has_system_message = any(
            isinstance(msg, dict) and msg.get("role") == "system" or
            isinstance(msg, SystemMessage)
            for msg in processed_messages
        )
        
        if not has_system_message:
            # Add system message at the beginning if not already present
            processed_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + processed_messages
        
        # Generate AI response with tools
        response = llm_with_tools.invoke(processed_messages)
        
        # Return the AI message to be added to the state
        return {"messages": [response]}
    
    # Create tool node for processing tool executions
    tool_node = ToolNode(tools=tools)
    
    # Add nodes to the graph
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tool_node)
    
    # Add conditional edges based on tool usage
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")
    
    # Set the entry point
    graph_builder.set_entry_point("chatbot")
    
    # Compile the graph
    return graph_builder.compile()
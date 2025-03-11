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
    PropertyDetailsInput, PropertyDetailsOutput, get_property_details, 
    get_property_details_rentcast, property_details_rentcast,
    PropertyValuationInput, PropertyValuationOutput, get_property_valuation, property_valuation,
    property_details_realty
)

# Define the agent state
class State(TypedDict):
    messages: Annotated[list, add_messages]
    
# Define a simpler property details tool
@tool
def property_details(address: str) -> str:
    """
    Get property details for a given address.
    
    Args:
        address: The property address to look up
        
    Returns:
        A description of the property
    """
    print("\n===== CALLING ATTOM API TOOL =====")
    print(f"Searching for property: {address}")
    
    # Import needed here to avoid circular imports
    import os
    import http.client
    import urllib.parse
    import json
    from dotenv import load_dotenv
    
    # Load API key
    load_dotenv()
    api_key = os.environ.get("ATTOM_API_KEY")
    
    if not api_key:
        return "Error: API key not found in environment variables."
    
    # Parse address
    address_parts = address.split(',', 1)
    address1 = address_parts[0].strip()
    address2 = address_parts[1].strip() if len(address_parts) > 1 else ""
    
    # URL encode address parts
    encoded_address1 = urllib.parse.quote(address1)
    encoded_address2 = urllib.parse.quote(address2) if address2 else ""
    
    # Create path
    path = f"/propertyapi/v1.0.0/property/detail?address1={encoded_address1}"
    if encoded_address2:
        path += f"&address2={encoded_address2}"
    
    # Make API request
    try:
        conn = http.client.HTTPSConnection("api.gateway.attomdata.com")
        headers = {
            'accept': "application/json",
            'apikey': api_key
        }
        
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        conn.close()
        
        # Parse response
        json_data = json.loads(data)
        
        # Check if property was found
        if "property" not in json_data or len(json_data["property"]) == 0:
            return f"No property found for address: {address}"
        
        # Get property data
        property_data = json_data["property"][0]
        
        # Print the entire raw JSON data for debugging
        print("\n=========== ATTOM FULL RAW JSON DATA ===========")
        print(json.dumps(property_data, indent=2))
        print("================================================\n")
        
        # Return the entire property data as JSON string
        return json.dumps(property_data, indent=2)
        
    except Exception as e:
        return f"Error retrieving property details: {str(e)}"

# Create the tools list
tools = [property_details, property_details_rentcast, property_details_realty, property_valuation]

# Define the system prompt for the agent
SYSTEM_PROMPT = """You are an experienced, friendly AI Real Estate Agent assistant designed to help independent home buyers.
You specialize in helping buyers find and evaluate properties that meet their needs, with a warm, professional tone.

IMPORTANT: When a new user starts a conversation with you, your first response should ask them to provide a property address they'd like to learn more about.

You have access to the following tools:
1. property_details - Get detailed information about a property based on its address using the ATTOM API
2. property_details_rentcast - Get detailed information about a property based on its address using the Rentcast API
3. property_details_realty - Get detailed information about a property based on its address using the Realty in US API
4. property_valuation - Get a detailed property valuation report with estimated value and comparable properties in the area

IMPORTANT: For each property search, use tools 1, 2, and 3 to get comprehensive property information from all three different APIs. Each API may provide different details that complement each other. 

When users ask about property value, market analysis, or comparables in the area, use tool 3 (property_valuation) to provide a thorough valuation report with comparable properties. IMPORTANT: When calling the property_valuation tool, pass all property details you know (property_type, bedrooms, bathrooms, square_footage) from the previous API calls to get the most accurate valuation.

IMPORTANT PRESENTATION INSTRUCTIONS:
- All three property_details tools will return raw JSON data from their respective APIs
- For ATTOM data, find and extract bedroom data from 'building.rooms.beds' or 'building.rooms.bedsnum'
- For ATTOM data, find and extract bathroom data from 'building.rooms.bathstotal' or calculate from 'bathsfull + (bathshalf * 0.5)'
- For Rentcast data, find and extract bedroom data from 'bedrooms' field
- For Rentcast data, find and extract bathroom data from 'bathrooms' field
- For Realty in US data, find and extract bedroom data from 'description.beds' field
- For Realty in US data, find and extract bathroom data from 'description.baths' field
- When describing the property, ALWAYS explicitly state ALL THREE bedroom values by saying: "This home has X bedrooms according to the first source, Y bedrooms according to the second source, and Z bedrooms according to the third source"
- When describing the property, ALWAYS explicitly state ALL THREE bathroom values by saying: "This home has X bathrooms according to the first source, Y bathrooms according to the second source, and Z bathrooms according to the third source"
- NEVER simplify, average, or combine these numbers - you MUST report EXACTLY what each API provided
- Your TOP PRIORITY is accurately reporting the RAW bedroom and bathroom values from all three APIs
- Report the EXACT values - no rounding or approximations

FOR PROPERTY VALUATION REPORTS:
- The property_valuation tool will return a detailed valuation report with comparable properties
- ONLY use the EXACT values provided by the tool - NEVER estimate, round, or make up any values
- The estimated property values should be quoted EXACTLY as returned by the API - no rounding, adjusting, or "approximately" statements
- TRANSFORM this data into an engaging market analysis as a knowledgeable real estate agent would
- Highlight ONLY the insights about property value that are directly based on the valuation data returned
- Discuss notable comparable properties EXACTLY as they appear in the API response
- NEVER introduce valuation amounts or price ranges that aren't explicitly in the API response
- If the API returns an estimated value of $221,000, say EXACTLY "$221,000", not "around $220,000" or "about $200,000"
- Include insights about comparable properties ONLY if they are actually in the API response
- Do not offer opinions on whether a property is under or overvalued unless that's explicitly stated in the API response
- Keep your tone professional but conversational, avoiding technical jargon

CONVERSATION FLOW:
- Ask for an address first if not provided
- Use ALL THREE property details tools (property_details, property_details_rentcast, AND property_details_realty) to get comprehensive property information
- Combine all the data from all three sources into a single, comprehensive understanding of the property
- Present the property in a conversational, engaging way, using the combined information
- ALWAYS explicitly state the bedroom and bathroom counts from all three sources exactly as described above
- When users express interest in property value, market analysis, or comparable sales:
  * Use the property_valuation tool to get detailed valuation information
  * ALWAYS pass all property details you already know (property_type, bedrooms, bathrooms, square_footage) to get the most accurate valuation
  * Present this as a professional market analysis with insights about the property's value
- Answer follow-up questions using all the information you received from all APIs
- If you don't have certain information, politely acknowledge the limitation
- Suggest other details they might be interested in, including property valuation if they haven't asked about it yet

SAMPLE RESPONSE FORMAT:
"I found information about [address]! This is a lovely [property_type] property.

According to my sources, this home has X bedrooms according to the first source, Y bedrooms according to the second source, and Z bedrooms according to the third source. It also has X bathrooms according to the first source, Y bathrooms according to the second source, and Z bathrooms according to the third source.

The property has approximately [square_footage] square feet of living space. Built in [year], the home sits on a [lot_size] lot and is currently valued at approximately [estimated_value].

[Add any insights about the price, size, location, etc.]

Would you like to know more about any specific aspect of this property?"

Always be helpful, enthusiastic, and provide as much value as possible with the information available."""

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
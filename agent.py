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
    get_property_details_rentcast, property_details_rentcast
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
    print("==================================\n")
    # Import needed here to avoid circular imports
    import os
    import http.client
    import urllib.parse
    import json
    import re
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
        
        # Extract essential property details
        address_obj = property_data.get("address", {})
        full_address = f"{address_obj.get('line1', '')}, {address_obj.get('line2', '')}"
        
        building = property_data.get("building", {})
        rooms = building.get("rooms", {})
        bedrooms = rooms.get("beds", 0) or rooms.get("bedsnum", 0)
        bathrooms = rooms.get("bathstotal", 0)
        if not bathrooms:
            full_baths = rooms.get("bathsfull", 0) or 0
            half_baths = rooms.get("bathshalf", 0) or 0
            bathrooms = full_baths + (half_baths * 0.5)
            
        size = building.get("size", {})
        square_feet = size.get("livingsize", 0) or size.get("universalsize", 0) or 0
        year_built = building.get("yearbuilt", 0) or 0
        
        lot = property_data.get("lot", {})
        lot_size = f"{lot.get('lotsize1', 0)} {lot.get('lotsize1unit', 'sq ft')}"
        
        summary = property_data.get("summary", {})
        property_type = summary.get("proptype", "Unknown")
        if property_type == "SFR":
            property_type = "Single Family Residence"
        elif property_type == "CONDO":
            property_type = "Condominium"
        elif property_type == "TWNHS":
            property_type = "Townhouse"
            
        assessment = property_data.get("assessment", {})
        market = assessment.get("market", {})
        market_value = market.get("mktttlvalue")
        estimated_value = f"${market_value:,}" if market_value else "Not available"
        
        sale = property_data.get("sale", {})
        sale_date = sale.get("salesearchdate", "")
        amount = sale.get("amount", {})
        sale_price = amount.get("saleamt")
        last_sold_price = f"${sale_price:,}" if sale_price else "Unknown"
        
        # Format property details as bulleted list
        result = f"""PROPERTY DETAILS:
• Address: {full_address}
• Property Type: {property_type}
• Bedrooms: {bedrooms}
• Bathrooms: {bathrooms}
• Square Footage: {square_feet:,} sq ft
• Year Built: {year_built if year_built > 0 else "Unknown"}
• Lot Size: {lot_size}
• Estimated Value: {estimated_value}
• Last Sold: {sale_date} for {last_sold_price if sale_price else "Unknown"}
"""
        return result
        
    except Exception as e:
        return f"Error retrieving property details: {str(e)}"

# Create the tools list
tools = [property_details, property_details_rentcast]

# Define the system prompt for the agent
SYSTEM_PROMPT = """You are an experienced, friendly AI Real Estate Agent assistant designed to help independent home buyers.
You specialize in helping buyers find and evaluate properties that meet their needs, with a warm, professional tone.

IMPORTANT: When a new user starts a conversation with you, your first response should ask them to provide a property address they'd like to learn more about.

You have access to the following tools:
1. property_details - Get detailed information about a property based on its address using the ATTOM API
2. property_details_rentcast - Get detailed information about a property based on its address using the Rentcast API

IMPORTANT: For each property search, you should use BOTH tools to get comprehensive information. Each API may provide different details that complement each other. Use all available information from both tools when responding to users.

IMPORTANT PRESENTATION INSTRUCTIONS:
- Both property_details tools will return bulleted lists of property information
- COMBINE the information from both APIs and TRANSFORM the data into an engaging, conversational description
- Use ALL the information provided in both API responses, resolving any discrepancies by mentioning both data points
- If the two APIs provide different values for the same property attribute (e.g., different square footage or year built), mention both values
- DO NOT say "according to ATTOM" or "according to Rentcast" or reference the data sources directly
- DO NOT mention bullet points - speak naturally as a real estate agent
- Add professional real estate agent context and insights where appropriate
- For example, if it's an older home, mention charm/character; if newer, mention modern amenities
- Calculate and mention the price per square foot if both the estimated value and square footage are available
- Keep a warm, enthusiastic tone throughout your description
- End by asking if they'd like to know more about any specific aspect of the property

CONVERSATION FLOW:
- Ask for an address first if not provided
- Use BOTH the property_details AND property_details_rentcast tools to get comprehensive property information
- Combine all the data from both sources into a single, comprehensive understanding of the property
- Present the property in a conversational, engaging way, using the combined information
- Answer follow-up questions using all the information you received from both APIs
- If you don't have certain information, politely acknowledge the limitation
- Suggest other details they might be interested in

SAMPLE RESPONSE FORMAT:
"I found information about [address]! This is a lovely [property_type] featuring [bedrooms] bedrooms and [bathrooms] bathrooms, with approximately [square_footage] square feet of living space. Built in [year], the home sits on a [lot_size] lot and is currently valued at approximately [estimated_value].

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
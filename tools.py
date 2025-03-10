from typing import Dict, Any, List, Optional
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class PropertyDetailsInput(BaseModel):
    address: str = Field(..., description="The full address of the property to get details for")

class PropertyDetailsOutput(BaseModel):
    address: str = Field(..., description="The full address of the property")
    bedrooms: int = Field(..., description="Number of bedrooms in the property")
    bathrooms: float = Field(..., description="Number of bathrooms in the property")
    square_footage: int = Field(..., description="Total square footage of the property")
    year_built: int = Field(..., description="Year the property was built")
    lot_size: str = Field(..., description="Size of the lot")
    property_type: str = Field(..., description="Type of property (single family, condo, etc.)")
    estimated_value: str = Field(..., description="Estimated current value of the property")
    last_sold_date: Optional[str] = Field(None, description="Date the property was last sold")
    last_sold_price: Optional[str] = Field(None, description="Price the property was last sold for")
    photos: List[str] = Field(..., description="URLs to property photos")
    property_id: str = Field(..., description="The property ID for use in other API calls")

def get_property_details(input_data: PropertyDetailsInput) -> PropertyDetailsOutput:
    """
    Get detailed information for a property based on its address using the ATTOM API.
    
    Args:
        input_data: A PropertyDetailsInput object containing the address
        
    Returns:
        A PropertyDetailsOutput object with property details
    """
    import os
    import http.client
    import urllib.parse
    import json
    import re
    from dotenv import load_dotenv
    
    # Load environment variables to get API key
    load_dotenv()
    api_key = os.environ.get("ATTOM_API_KEY")
    
    if not api_key:
        raise ValueError("API key not found in environment variables. Please add ATTOM_API_KEY to your .env file.")
    
    print(f"DEBUG: Starting property search for address: '{input_data.address}'")
    
    # Parse the address into address1 and address2 parts (street and city/state)
    address_parts = input_data.address.split(',', 1)
    address1 = address_parts[0].strip()
    address2 = address_parts[1].strip() if len(address_parts) > 1 else ""
    
    print(f"DEBUG: Parsed address into: address1='{address1}', address2='{address2}'")
    
    # URL encode the address parameters
    encoded_address1 = urllib.parse.quote(address1)
    encoded_address2 = urllib.parse.quote(address2) if address2 else ""
    
    # Create the path with query parameters
    path = f"/propertyapi/v1.0.0/property/detail?address1={encoded_address1}"
    if encoded_address2:
        path += f"&address2={encoded_address2}"
    
    # Headers for the API call - exactly as in the example
    headers = {
        'accept': "application/json",
        'apikey': api_key
    }
    
    print(f"DEBUG: Using API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    print(f"DEBUG: Request path: {path}")
    print(f"DEBUG: Request headers: {headers}")
    
    try:
        # Create HTTP connection to ATTOM API
        conn = http.client.HTTPSConnection("api.gateway.attomdata.com")
        
        # Make the GET request - exactly as in the example
        conn.request("GET", path, headers=headers)
        
        # Get the response
        response = conn.getresponse()
        print(f"DEBUG: API response status: {response.status} {response.reason}")
        
        # Read the response data
        data = response.read()
        
        # Parse the JSON response
        search_data = json.loads(data.decode('utf-8'))
        print(f"DEBUG: API response parsed successfully")
        
        # Log the structure of the response for debugging
        print(f"DEBUG: Response structure: {list(search_data.keys()) if isinstance(search_data, dict) else 'Not a dictionary'}")
        
        # Check if we have properties in the response
        if not search_data.get("property") or len(search_data["property"]) == 0:
            print(f"DEBUG: No properties found in API response. Full response: {search_data}")
            raise ValueError(f"No properties found for address: {input_data.address}")
            
        print(f"DEBUG: Found {len(search_data['property'])} properties in response")
        
        # Close the connection
        conn.close()
        
    except http.client.HTTPException as e:
        print(f"DEBUG: HTTP error occurred: {str(e)}")
        raise ValueError(f"HTTP error when calling ATTOM API: {str(e)}")
        
    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to parse API response as JSON: {str(e)}")
        raise ValueError(f"Failed to parse ATTOM API response as JSON: {str(e)}")
        
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        raise ValueError(f"Unexpected error when calling ATTOM API: {str(e)}")
    
    # Get the first property from the results
    property_data = search_data["property"][0]
    
    # Print some of the property data for debugging
    print(f"DEBUG: First property data: {str(property_data)[:500]}...")
    
    # Extract property ID for future API calls
    identifier = property_data.get("identifier", {})
    property_id = identifier.get("attomId", "Unknown")
    
    print(f"DEBUG: Found property with ATTOM ID: {property_id}")
    
    # Get full address
    address_obj = property_data.get("address", {})
    full_address = f"{address_obj.get('line1', '')}, {address_obj.get('line2', '')}"
    
    # Extract building details
    building = property_data.get("building", {})
    rooms = building.get("rooms", {})
    size = building.get("size", {})
    
    # Get bedrooms - first check 'beds', then 'bedsnum' as a fallback
    bedrooms = rooms.get("beds")
    if bedrooms is None or bedrooms == 0:
        bedrooms = rooms.get("bedsnum", 0)
    
    # Get bathrooms - first check 'bathstotal', then 'bathsfull' + 'bathshalf'/2 as a fallback
    bathrooms = rooms.get("bathstotal")
    if bathrooms is None or bathrooms == 0:
        full_baths = rooms.get("bathsfull", 0)
        half_baths = rooms.get("bathshalf", 0)
        bathrooms = full_baths + (half_baths * 0.5)
    
    # Get square footage from 'livingsize' or 'universalsize' as fallback
    square_footage = size.get("livingsize")
    if square_footage is None or square_footage == 0:
        square_footage = size.get("universalsize", 0)
    
    # Get year built
    year_built = building.get("yearbuilt", 0)
    
    # Get lot size
    lot = property_data.get("lot", {})
    lot_size_value = lot.get("lotsize1", 0)
    lot_size_unit = lot.get("lotsize1unit", "sq ft")
    lot_size = f"{lot_size_value} {lot_size_unit}"
    
    # Get property type
    summary = property_data.get("summary", {})
    property_type = summary.get("proptype", "Unknown")
    
    # Try to get a more descriptive property type
    if property_type == "SFR":
        property_type = "Single Family Residence"
    elif property_type == "CONDO":
        property_type = "Condominium"
    elif property_type == "TWNHS":
        property_type = "Townhouse"
    
    # Get value information from assessment
    assessment = property_data.get("assessment", {})
    market = assessment.get("market", {})
    
    # Get market value, defaulting to total value if available
    market_value = market.get("mktttlvalue")
    if market_value is None:
        market_value = assessment.get("assessed", {}).get("assdttlvalue")
    
    estimated_value = f"${market_value:,}" if market_value else "Not available"
    
    # Get last sale information
    sale = property_data.get("sale", {})
    
    # Try to format the sale date nicely if it exists
    sales_search_date = sale.get("salesearchdate")
    if sales_search_date:
        # Try to parse the date format (if it's in YYYY-MM-DD format)
        date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', sales_search_date)
        if date_match:
            year, month, day = date_match.groups()
            # Convert month number to name
            months = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
            try:
                month_name = months[int(month) - 1]
                last_sold_date = f"{month_name} {int(day)}, {year}"
            except (IndexError, ValueError):
                last_sold_date = sales_search_date
        else:
            last_sold_date = sales_search_date
    else:
        last_sold_date = None
    
    # Get sale amount
    amount = sale.get("amount", {})
    sale_amount = amount.get("saleamt")
    last_sold_price = f"${sale_amount:,}" if sale_amount else None
    
    # ATTOM API doesn't provide photos directly in this endpoint
    photos = []
    
    # Print debug info for key fields
    print(f"DEBUG: Extracted address: {full_address}")
    print(f"DEBUG: Extracted bedrooms: {bedrooms}")
    print(f"DEBUG: Extracted bathrooms: {bathrooms}")
    print(f"DEBUG: Extracted square footage: {square_footage}")
    print(f"DEBUG: Extracted year built: {year_built}")
    print(f"DEBUG: Extracted property type: {property_type}")
    print(f"DEBUG: Extracted estimated value: {estimated_value}")
    print(f"DEBUG: Extracted last sold date: {last_sold_date}")
    print(f"DEBUG: Extracted last sold price: {last_sold_price}")
    
    # Create the output object
    output = PropertyDetailsOutput(
        address=full_address,
        bedrooms=int(bedrooms) if bedrooms else 0,
        bathrooms=float(bathrooms) if bathrooms else 0,
        square_footage=int(square_footage) if square_footage else 0,
        year_built=int(year_built) if year_built else 0,
        lot_size=lot_size,
        property_type=property_type,
        estimated_value=estimated_value,
        last_sold_date=last_sold_date,
        last_sold_price=last_sold_price,
        photos=photos,
        property_id=property_id
    )
    
    print(f"DEBUG: Final output object: {output}")
    return output
    
def parse_address(address: str) -> dict:
    """
    Parse an address string into components.
    
    Expected format examples:
    - "123 Main St, Anytown, CA 12345"
    - "456 Oak Ave, Somecity, TX"
    - "789 Pine Rd, 98765"
    """
    import re
    
    print(f"DEBUG: Parsing address: '{address}'")
    address_parts = {}
    
    # Normalize the address - uppercase state and convert to standard format
    address = address.strip()
    
    # Try to extract zip code
    zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address)
    if zip_match:
        address_parts["zip_code"] = zip_match.group(1)
        print(f"DEBUG: Found zip code: {address_parts['zip_code']}")
    
    # Try to extract state (2-letter code)
    # Look for a 2-letter uppercase state code that's either at the end or followed by a zip code
    state_match = re.search(r'\b([A-Z]{2})\b', address)
    if state_match:
        address_parts["state"] = state_match.group(1)
        print(f"DEBUG: Found state: {address_parts['state']}")
    
    # Split the address by commas
    address_components = [comp.strip() for comp in address.split(',')]
    print(f"DEBUG: Address components after splitting by commas: {address_components}")
    
    # Typical address format has 2-3 components:
    # [street, city, state+zip] or [street, city+state+zip]
    
    if len(address_components) >= 2:
        # The first component is almost always the street address
        address_parts["street_address"] = address_components[0].strip()
        print(f"DEBUG: Street address from components: {address_parts['street_address']}")
        
        # The second component is typically the city
        if len(address_components) >= 3:
            address_parts["city"] = address_components[1].strip()
            print(f"DEBUG: City from 3+ components: {address_parts['city']}")
        else:
            # For 2-component addresses, try to separate city from state/zip in the last component
            last_component = address_components[1].strip()
            
            # If we have a state match, everything before it in the last component is the city
            if state_match and state_match.string == last_component:
                city_part = last_component[:state_match.start()].strip()
                if city_part:
                    address_parts["city"] = city_part
                    print(f"DEBUG: City from last component before state: {address_parts['city']}")
            
            # If we have a zip match, everything before it could be city+state
            elif zip_match and zip_match.string == last_component:
                # Check if there's a state before the zip
                pre_zip = last_component[:zip_match.start()].strip()
                if pre_zip:
                    if state_match and state_match.string == pre_zip:
                        city_part = pre_zip[:state_match.start()].strip()
                        if city_part:
                            address_parts["city"] = city_part
                            print(f"DEBUG: City from last component before state+zip: {address_parts['city']}")
                    else:
                        # If no state, assume everything before zip is city
                        address_parts["city"] = pre_zip
                        print(f"DEBUG: City from last component before zip: {address_parts['city']}")
    else:
        # If there's only one component, it's likely just a street address
        address_parts["street_address"] = address.strip()
        print(f"DEBUG: Street address from single component: {address_parts['street_address']}")
    
    # Print and validate the final parsed address
    print(f"DEBUG: Final parsed address components: {address_parts}")
    
    # Validate that we have the minimum required components
    if "street_address" in address_parts:
        if ("city" in address_parts and "state" in address_parts) or "zip_code" in address_parts:
            print(f"DEBUG: Address parsing successful - have required components")
        else:
            print(f"DEBUG: Address parsing incomplete - missing city+state or zip_code")
    else:
        print(f"DEBUG: Address parsing failed - no street_address identified")
    
    return address_parts

# Function to test API connectivity directly
def test_corelogic_api(api_key: str = None):
    """
    Test function to check if the CoreLogic API is working correctly.
    
    Args:
        api_key: Optional API key, if not provided it will be loaded from environment
    """
    import os
    import http.client
    import urllib.parse
    import json
    from dotenv import load_dotenv
    
    if not api_key:
        # Load environment variables to get API key
        load_dotenv()
        api_key = os.environ.get("CORELOGIC_API_KEY") or os.environ.get("ATTOM_API_KEY")
    
    if not api_key:
        print("ERROR: No API key provided and no API key found in environment variables.")
        return
    
    # Test with a simple API call
    # Use properties/search endpoint for testing with a known address
    test_address = "77 N Nickajack, Santa Rosa Beach, FL 32459"
    
    # Create the payload
    payload = {
        "address": {
            "line1": test_address
        },
        "bestMatch": True
    }
    
    # Convert payload to JSON
    payload_json = json.dumps(payload)
    
    # Headers for the API call
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "apikey": api_key
    }
    
    print(f"Making test API call to CoreLogic API with API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    print(f"Host: property.corelogicapi.com")
    print(f"Endpoint: /v2/properties/search")
    print(f"Payload: {payload}")
    print(f"Headers: {headers}")
    
    try:
        # Create HTTP connection
        conn = http.client.HTTPSConnection("property.corelogicapi.com")
        
        # Make the POST request
        conn.request("POST", "/v2/properties/search", payload_json, headers)
        
        # Get the response
        response = conn.getresponse()
        
        print(f"Response Status: {response.status} {response.reason}")
        print(f"Response Headers: {dict(response.getheaders())}")
        
        # Read the response data
        data = response.read()
        
        # Try to parse as JSON
        try:
            json_data = json.loads(data.decode('utf-8'))
            
            # Print limited content to avoid overwhelming the console
            content = json.dumps(json_data, indent=2)[:1000] + ("..." if len(json.dumps(json_data)) > 1000 else "")
            print(f"Response Content: {content}")
            
            if "properties" in json_data and len(json_data["properties"]) > 0:
                print("Test SUCCESSFUL! API is working correctly and returning property data.")
                print(f"Found {len(json_data['properties'])} properties.")
                
                # Print some basic info about the first property
                if len(json_data["properties"]) > 0:
                    prop = json_data["properties"][0]
                    address = prop.get("address", {})
                    print(f"First property: {address.get('line1')}, {address.get('city')}, {address.get('stateCode')} {address.get('postalCode')}")
                    print(f"Property ID: {prop.get('propertyId')}")
            else:
                print("API returned successfully but no properties were found.")
                
        except json.JSONDecodeError:
            print("WARNING: Response is not valid JSON.")
            print(f"Raw response: {data.decode('utf-8')[:1000]}...")
            
        # Close the connection
        conn.close()
        
    except Exception as e:
        print(f"ERROR: Exception occurred while testing API: {str(e)}")

def get_property_details_rentcast(input_data: PropertyDetailsInput) -> PropertyDetailsOutput:
    """
    Get detailed information for a property based on its address using the Rentcast API.
    
    Args:
        input_data: A PropertyDetailsInput object containing the address
        
    Returns:
        A PropertyDetailsOutput object with property details
    """
    import os
    import json
    import requests
    import datetime
    from dotenv import load_dotenv
    
    # Load environment variables to get API key
    load_dotenv()
    api_key = os.environ.get("RENTCAST_API_KEY")
    
    if not api_key:
        raise ValueError("API key not found in environment variables. Please add RENTCAST_API_KEY to your .env file.")
    
    print(f"DEBUG: Starting property search for address: '{input_data.address}'")
    
    # Prepare API URL
    base_url = "https://api.rentcast.io/v1/properties"
    address_param = input_data.address
    
    # Prepare headers
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }
    
    print(f"DEBUG: Using API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    print(f"DEBUG: Request URL: {base_url}?address={address_param}")
    print(f"DEBUG: Request headers: {headers}")
    
    try:
        # Make the GET request to Rentcast API
        response = requests.get(
            f"{base_url}?address={address_param}",
            headers=headers
        )
        
        # Check for successful response
        response.raise_for_status()
        
        # Parse the JSON response
        search_data = response.json()
        print(f"DEBUG: API response parsed successfully")
        
        # Log the structure of the response for debugging
        print(f"DEBUG: Response structure: {search_data[:100] if isinstance(search_data, list) else 'Not a list'}")
        
        # Check if we have properties in the response
        if not search_data or len(search_data) == 0:
            print(f"DEBUG: No properties found in API response.")
            raise ValueError(f"No properties found for address: {input_data.address}")
            
        print(f"DEBUG: Found {len(search_data)} properties in response")
        
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: HTTP error occurred: {str(e)}")
        raise ValueError(f"HTTP error when calling Rentcast API: {str(e)}")
        
    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to parse API response as JSON: {str(e)}")
        raise ValueError(f"Failed to parse Rentcast API response as JSON: {str(e)}")
        
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        raise ValueError(f"Unexpected error when calling Rentcast API: {str(e)}")
    
    # Get the first property from the results
    property_data = search_data[0]
    
    # Print some of the property data for debugging
    print(f"DEBUG: First property data: {str(property_data)[:500]}...")
    
    # Extract property ID
    property_id = property_data.get("id", "Unknown")
    print(f"DEBUG: Found property with Rentcast ID: {property_id}")
    
    # Get full formatted address
    full_address = property_data.get("formattedAddress", "")
    
    # Extract property details
    bedrooms = property_data.get("bedrooms", 0)
    bathrooms = property_data.get("bathrooms", 0)
    square_footage = property_data.get("squareFootage", 0)
    year_built = property_data.get("yearBuilt", 0)
    
    # Get lot size
    lot_size_value = property_data.get("lotSize", 0)
    lot_size = f"{lot_size_value} sq ft"
    
    # Get property type
    property_type = property_data.get("propertyType", "Unknown")
    
    # Get estimated value - use the latest tax assessment if available
    tax_assessments = property_data.get("taxAssessments", {})
    estimated_value = "Not available"
    if tax_assessments:
        # Find the most recent tax assessment year
        latest_year = max([int(year) for year in tax_assessments.keys()], default=0)
        if latest_year > 0:
            latest_assessment = tax_assessments.get(str(latest_year), {})
            assessment_value = latest_assessment.get("value", 0)
            if assessment_value:
                estimated_value = f"${assessment_value:,}"
    
    # Get last sale information
    history = property_data.get("history", {})
    last_sold_date = None
    last_sold_price = None
    
    if history:
        # Find the most recent sale date
        sale_dates = [date for date in history.keys() if history[date].get("event") == "Sale"]
        if sale_dates:
            most_recent_sale_date = max(sale_dates)
            sale_info = history.get(most_recent_sale_date, {})
            
            # Format the date
            if "date" in sale_info:
                date_str = sale_info["date"]
                try:
                    # Parse the ISO date format
                    date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    last_sold_date = date_obj.strftime("%B %d, %Y")
                except (ValueError, TypeError):
                    last_sold_date = date_str
            
            # Get the sale price
            if "price" in sale_info:
                price = sale_info["price"]
                last_sold_price = f"${price:,}"
    
    # Rentcast API doesn't provide photos directly
    photos = []
    
    # Print debug info for key fields
    print(f"DEBUG: Extracted address: {full_address}")
    print(f"DEBUG: Extracted bedrooms: {bedrooms}")
    print(f"DEBUG: Extracted bathrooms: {bathrooms}")
    print(f"DEBUG: Extracted square footage: {square_footage}")
    print(f"DEBUG: Extracted year built: {year_built}")
    print(f"DEBUG: Extracted property type: {property_type}")
    print(f"DEBUG: Extracted estimated value: {estimated_value}")
    print(f"DEBUG: Extracted last sold date: {last_sold_date}")
    print(f"DEBUG: Extracted last sold price: {last_sold_price}")
    
    # Create the output object
    output = PropertyDetailsOutput(
        address=full_address,
        bedrooms=int(bedrooms) if bedrooms else 0,
        bathrooms=float(bathrooms) if bathrooms else 0,
        square_footage=int(square_footage) if square_footage else 0,
        year_built=int(year_built) if year_built else 0,
        lot_size=lot_size,
        property_type=property_type,
        estimated_value=estimated_value,
        last_sold_date=last_sold_date,
        last_sold_price=last_sold_price,
        photos=photos,
        property_id=property_id
    )
    
    print(f"DEBUG: Final output object: {output}")
    return output

# Add a tool that uses the Rentcast API for property details
@tool
def property_details_rentcast(address: str) -> str:
    """
    Get property details for a given address using the Rentcast API.
    
    Args:
        address: The property address to look up
        
    Returns:
        A description of the property
    """
    print("\n===== CALLING RENTCAST API TOOL =====")
    print(f"Searching for property: {address}")
    print("====================================\n")
    # Import needed here to avoid circular imports
    import os
    import requests
    import json
    import datetime
    from dotenv import load_dotenv
    
    # Load API key
    load_dotenv()
    api_key = os.environ.get("RENTCAST_API_KEY")
    
    if not api_key:
        return "Error: API key not found in environment variables. Please add RENTCAST_API_KEY to your .env file."
    
    # Prepare API URL
    base_url = "https://api.rentcast.io/v1/properties"
    address_param = address
    
    # Prepare headers
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }
    
    # Make the API request
    try:
        response = requests.get(
            f"{base_url}?address={address_param}",
            headers=headers
        )
        
        # Check for successful response
        response.raise_for_status()
        
        # Parse the JSON response
        json_data = response.json()
        
        # Check if property was found
        if not json_data or len(json_data) == 0:
            return f"No property found for address: {address}"
        
        # Get the first property from the results
        property_data = json_data[0]
        
        # Extract essential property details
        full_address = property_data.get("formattedAddress", "")
        bedrooms = property_data.get("bedrooms", 0)
        bathrooms = property_data.get("bathrooms", 0)
        square_footage = property_data.get("squareFootage", 0)
        year_built = property_data.get("yearBuilt", 0)
        
        # Get lot size
        lot_size = f"{property_data.get('lotSize', 0)} sq ft"
        
        # Get property type
        property_type = property_data.get("propertyType", "Unknown")
        
        # Get estimated value - use the latest tax assessment
        tax_assessments = property_data.get("taxAssessments", {})
        estimated_value = "Not available"
        if tax_assessments:
            # Find the most recent tax assessment year
            latest_year = max([int(year) for year in tax_assessments.keys()], default=0)
            if latest_year > 0:
                latest_assessment = tax_assessments.get(str(latest_year), {})
                assessment_value = latest_assessment.get("value", 0)
                if assessment_value:
                    estimated_value = f"${assessment_value:,}"
        
        # Get last sale information
        history = property_data.get("history", {})
        last_sold_date = "Unknown"
        last_sold_price = "Unknown"
        
        if history:
            # Find the most recent sale date
            sale_dates = [date for date in history.keys() if history[date].get("event") == "Sale"]
            if sale_dates:
                most_recent_sale_date = max(sale_dates)
                sale_info = history.get(most_recent_sale_date, {})
                
                # Get date
                if "date" in sale_info:
                    date_str = sale_info["date"]
                    try:
                        date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        last_sold_date = date_obj.strftime("%B %d, %Y")
                    except (ValueError, TypeError):
                        last_sold_date = date_str
                
                # Get price
                if "price" in sale_info:
                    price = sale_info["price"]
                    last_sold_price = f"${price:,}"
        
        # Format property details as bulleted list
        result = f"""PROPERTY DETAILS:
• Address: {full_address}
• Property Type: {property_type}
• Bedrooms: {bedrooms}
• Bathrooms: {bathrooms}
• Square Footage: {square_footage:,} sq ft
• Year Built: {year_built if year_built > 0 else "Unknown"}
• Lot Size: {lot_size}
• Estimated Value: {estimated_value}
• Last Sold: {last_sold_date} for {last_sold_price}
"""
        return result
        
    except requests.exceptions.HTTPError as e:
        return f"Error retrieving property details: HTTP error - {str(e)}"
    except json.JSONDecodeError as e:
        return f"Error retrieving property details: Invalid JSON response - {str(e)}"
    except Exception as e:
        return f"Error retrieving property details: {str(e)}"

# Function to test Rentcast API connectivity directly
def test_rentcast_api(api_key: str = None):
    """
    Test function to check if the Rentcast API is working correctly.
    
    Args:
        api_key: Optional API key, if not provided it will be loaded from environment
    """
    import os
    import requests
    import json
    from dotenv import load_dotenv
    
    if not api_key:
        # Load environment variables to get API key
        load_dotenv()
        api_key = os.environ.get("RENTCAST_API_KEY")
    
    if not api_key:
        print("ERROR: No API key provided and no API key found in environment variables.")
        return
    
    # Test with a simple API call
    test_address = "5500 Grand Lake Dr, San Antonio, TX 78244"
    base_url = "https://api.rentcast.io/v1/properties"
    
    # Headers for the API call
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }
    
    print(f"Making test API call to Rentcast API with API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    print(f"URL: {base_url}?address={test_address}")
    print(f"Headers: {headers}")
    
    try:
        # Make the request
        response = requests.get(
            f"{base_url}?address={test_address}",
            headers=headers
        )
        
        print(f"Response Status: {response.status_code} {response.reason}")
        
        # Check if response is successful
        if response.status_code == 200:
            # Try to parse as JSON
            try:
                json_data = response.json()
                
                # Print limited content to avoid overwhelming the console
                content = json.dumps(json_data, indent=2)[:1000] + ("..." if len(json.dumps(json_data)) > 1000 else "")
                print(f"Response Content: {content}")
                
                if json_data and len(json_data) > 0:
                    print("Test SUCCESSFUL! API is working correctly and returning property data.")
                    print(f"Found {len(json_data)} properties.")
                    
                    # Print some basic info about the first property
                    if len(json_data) > 0:
                        prop = json_data[0]
                        print(f"First property: {prop.get('formattedAddress', 'Unknown')}")
                        print(f"Property Type: {prop.get('propertyType', 'Unknown')}")
                        print(f"Bedrooms: {prop.get('bedrooms', 'Unknown')}")
                        print(f"Bathrooms: {prop.get('bathrooms', 'Unknown')}")
                else:
                    print("API returned successfully but no properties were found.")
                    
            except json.JSONDecodeError:
                print("WARNING: Response is not valid JSON.")
                print(f"Raw response: {response.text[:1000]}...")
            
        else:
            print(f"ERROR: API returned status code {response.status_code}")
            print(f"Response: {response.text[:1000]}...")
        
    except Exception as e:
        print(f"ERROR: Exception occurred while testing API: {str(e)}")

# Additional tools can be added here in the future
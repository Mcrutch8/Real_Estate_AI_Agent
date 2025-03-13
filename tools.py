"""
Property API Integration Tool Module

This module provides tools to fetch property details from various real estate data APIs:
1. ATTOM API - Industry standard property data API 
2. Rentcast API - Alternative property data API

Each API has two implementations:
- A detailed function (get_property_details*) that returns structured data
- A simplified tool function (property_details*) that returns formatted text

These tools are used by the real estate agent assistant to provide property information.
"""

from typing import List, Optional
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from security import safe_requests

# Input/Output models for property data APIs

class PropertyDetailsInput(BaseModel):
    """Input model for property details API calls."""
    address: str = Field(..., description="The full address of the property to get details for")

class PropertyDetailsOutput(BaseModel):
    """Output model containing standardized property details from any API source."""
    address: str = Field(..., description="The full address of the property")
    bedrooms: int = Field(..., description="Number of bedrooms in the property")
    bathrooms: float = Field(..., description="Number of bathrooms in the property")
    square_footage: int = Field(..., description="Total square footage of the property")
    year_built: int = Field(..., description="Year the property was built")
    lot_size: str = Field(..., description="Size of the lot")
    property_type: str = Field(..., description="Type of property (single family, condo, etc.)")
    estimated_value: str = Field(..., description="Estimated value of the property")
    last_sold: str = Field(..., description="Date and price of the last sale")
    photos: List[str] = Field(..., description="URLs to property photos")
    property_id: str = Field(..., description="The property ID for use in other API calls")

# ===== ATTOM API IMPLEMENTATION =====

def get_property_details(input_data: PropertyDetailsInput) -> PropertyDetailsOutput:
    """
    Get detailed information for a property based on its address using the ATTOM API.
    
    This is the detailed implementation that returns structured data. The simplified
    tool version for the agent to use is property_details in agent.py.
    
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
    
    # Parse address
    address_parts = parse_address(input_data.address)
    print(f"DEBUG: Parsed address: {address_parts}")
    
    # Prepare API URL and parameters
    host = "api.gateway.attomdata.com"
    endpoint = "/propertyapi/v1.0.0/property/basicprofile"
    
    # Build query parameters
    params = {
        "address1": address_parts["street_address"],
        "address2": f"{address_parts['city']}, {address_parts['state']} {address_parts['zip_code']}",
    }
    
    # Convert parameters to query string
    query_string = urllib.parse.urlencode(params)
    url = f"{endpoint}?{query_string}"
    
    print(f"DEBUG: Using API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    print(f"DEBUG: Host: {host}")
    print(f"DEBUG: URL: {url}")
    print(f"DEBUG: Query parameters: {params}")
    
    # Prepare headers with API key
    headers = {
        "apikey": api_key,
        "accept": "application/json",
    }
    
    try:
        # Make the API request
        print(f"DEBUG: Sending request to ATTOM API...")
        
        conn = http.client.HTTPSConnection(host)
        conn.request("GET", url, headers=headers)
        
        # Get response
        response = conn.getresponse()
        print(f"DEBUG: Response Status: {response.status} {response.reason}")
        
        # Read and parse response
        data = response.read().decode('utf-8')
        json_data = json.loads(data)
        
        # Extract status code
        status_code = json_data.get("status", {}).get("code", 0)
        if status_code != 0:
            error_message = json_data.get("status", {}).get("msg", "Unknown error")
            raise ValueError(f"API error: {error_message}")
        
        # Check if we have property data
        if "property" not in json_data or not json_data["property"]:
            raise ValueError(f"No property found for address: {input_data.address}")
        
        # Get property data
        property_data = json_data["property"][0]
        
        # Extract essential property details
        address_obj = property_data.get("address", {})
        full_address = f"{address_obj.get('line1', '')}, {address_obj.get('line2', '')}"
        
        building = property_data.get("building", {})
        rooms = building.get("rooms", {})
        bedrooms = rooms.get("beds", 0) or rooms.get("bedsnum", 0) or 0
        
        bathrooms = rooms.get("bathstotal", 0)
        if not bathrooms:
            full_baths = rooms.get("bathsfull", 0) or 0
            half_baths = rooms.get("bathshalf", 0) or 0
            bathrooms = full_baths + (half_baths * 0.5)
            
        size = building.get("size", {})
        square_feet = size.get("livingsize", 0) or size.get("universalsize", 0) or 0
        
        year_built = building.get("yearbuilt", 0) or 0
        
        lot = property_data.get("lot", {})
        lot_size_value = lot.get("lotsize1", 0) or 0
        lot_size_unit = lot.get("lotsize1unit", "sq ft") or "sq ft"
        lot_size = f"{lot_size_value} {lot_size_unit}"
        
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
        market_value = market.get("mktttlvalue") or 0
        estimated_value = f"${market_value:,}" if market_value else "Not available"
        
        sale = property_data.get("sale", {})
        sale_date = sale.get("salesearchdate", "")
        amount = sale.get("amount", {})
        sale_price = amount.get("saleamt") or 0
        last_sold_price = f"${sale_price:,}" if sale_price else "Unknown"
        last_sold = f"{sale_date} for {last_sold_price}"
        
        # Get property ID
        property_id = property_data.get("identifier", {}).get("attomId", "")
        print(f"DEBUG: Property ID: {property_id}")
        
        # Get photos (Note: ATTOM API doesn't provide photos, so we'll use an empty list)
        photos = []
        
        # Create the output object
        output = PropertyDetailsOutput(
            address=full_address,
            bedrooms=int(bedrooms) if bedrooms else 0,
            bathrooms=float(bathrooms) if bathrooms else 0.0,
            square_footage=int(square_feet) if square_feet else 0,
            year_built=int(year_built) if year_built else 0,
            lot_size=lot_size,
            property_type=property_type,
            estimated_value=estimated_value,
            last_sold=last_sold,
            photos=photos,
            property_id=str(property_id) if property_id else ""
        )
        
        print(f"DEBUG: Successfully parsed property data")
        print(f"DEBUG: Final output object: {output}")
        return output
        
    except http.client.HTTPException as e:
        print(f"DEBUG: HTTP error occurred: {str(e)}")
        raise ValueError(f"HTTP error when calling ATTOM API: {str(e)}")
        
    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to parse API response as JSON: {str(e)}")
        print(f"DEBUG: Non-JSON Response Content: {data[:1000] if 'data' in locals() else 'Unknown'}")
        raise ValueError(f"Failed to parse ATTOM API response as JSON: {str(e)}")
        
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise ValueError(f"Unexpected error when calling ATTOM API: {str(e)}")
    
# ===== ADDRESS PARSING UTILITY =====

def parse_address(address: str) -> dict:
    """
    Parse an address string into components.
    
    Utility function for breaking down addresses into structured components.
    Used by the property detail APIs to parse input addresses.
    
    Expected format examples:
    - "123 Main St, Anytown, CA 12345"
    - "456 Oak Ave, Somecity, TX"
    
    Args:
        address: The address string to parse
        
    Returns:
        A dictionary with address components
    """
    # Initialize default values
    address_parts = {
        "street_address": "",
        "city": "",
        "state": "",
        "zip_code": ""
    }
    
    try:
        # Try to parse the address based on commas (common format)
        parts = address.split(',')
        
        # Street address is the first part
        if len(parts) > 0:
            address_parts["street_address"] = parts[0].strip()
        
        # City is the second part
        if len(parts) > 1:
            address_parts["city"] = parts[1].strip()
        
        # State and ZIP are in the third part
        if len(parts) > 2:
            state_zip = parts[2].strip()
            
            # Try to extract state and ZIP based on space
            state_zip_parts = state_zip.split()
            
            # State is usually the first part (e.g., "CA")
            if len(state_zip_parts) > 0:
                address_parts["state"] = state_zip_parts[0].strip()
            
            # ZIP code is the remaining parts
            if len(state_zip_parts) > 1:
                address_parts["zip_code"] = ' '.join(state_zip_parts[1:]).strip()
        
        # Special case for non-comma format
        if not address_parts["city"] and ' ' in address:
            # Try to find the last word pair that might be "State ZIP"
            words = address.split()
            if len(words) >= 3:
                # Check if second-to-last word might be a state
                if words[-2].upper() == words[-2] and len(words[-2]) <= 2:
                    address_parts["state"] = words[-2]
                    address_parts["zip_code"] = words[-1]
                    address_parts["street_address"] = ' '.join(words[:-2])
                    
                    # Try to extract city
                    street_parts = address_parts["street_address"].split(',')
                    if len(street_parts) > 1:
                        address_parts["city"] = street_parts[-1].strip()
                        address_parts["street_address"] = ','.join(street_parts[:-1]).strip()
    
    except Exception as e:
        print(f"ERROR: Failed to parse address '{address}': {str(e)}")
        # Keep defaults for any parsing errors
    
    return address_parts

# ===== API TESTING UTILITIES =====

def test_corelogic_api(api_key: str = None):
    """
    Test function to check if the CoreLogic/ATTOM API is working correctly.
    
    Used by test_api.py for testing API connectivity.
    
    Args:
        api_key: Optional API key, if not provided it will be loaded from environment
    """
    import os
    import http.client
    import urllib.parse
    import json
    from dotenv import load_dotenv
    
    # Load environment variables if no API key provided
    if not api_key:
        load_dotenv()
        api_key = os.environ.get("ATTOM_API_KEY")
    
    if not api_key:
        print("ERROR: API key not provided and not found in environment variables")
        return
    
    print("=" * 80)
    print("TESTING CORELOGIC API CONNECTIVITY")
    print("=" * 80)
        
    # Test with a known address
    test_address = "4529 Winona Ct, Denver, CO 80212"
    address_parts = parse_address(test_address)
    
    # Prepare API URL and parameters
    host = "api.gateway.attomdata.com"
    endpoint = "/propertyapi/v1.0.0/property/basicprofile"
    
    # Build query parameters
    params = {
        "address1": address_parts["street_address"],
        "address2": f"{address_parts['city']}, {address_parts['state']} {address_parts['zip_code']}",
    }
    
    # Convert parameters to query string
    query_string = urllib.parse.urlencode(params)
    url = f"{endpoint}?{query_string}"
    
    print(f"Testing with API key: {api_key[:5]}...{api_key[-5:]}")
    print(f"Host: {host}")
    print(f"URL: {url}")
    print(f"Query params: {params}")
    
    # Prepare headers with API key
    headers = {
        "apikey": api_key,
        "accept": "application/json",
    }
    
    try:
        # Make the API request
        print("Sending request to API...")
        
        conn = http.client.HTTPSConnection(host)
        conn.request("GET", url, headers=headers)
        
        # Get response
        response = conn.getresponse()
        print(f"Response Status: {response.status} {response.reason}")
        
        # Read and parse response
        data = response.read().decode('utf-8')
        
        # Try to parse as JSON
        try:
            json_data = json.loads(data)
            print(f"Successfully parsed response as JSON")
            
            # Check for error status
            status_code = json_data.get("status", {}).get("code", None)
            if status_code is not None and status_code != 0:
                error_message = json_data.get("status", {}).get("msg", "Unknown error")
                print(f"API returned error: {error_message}")
            else:
                print("API request was successful")
                
                # Check if we have property data
                if "property" in json_data and json_data["property"]:
                    print(f"Found property data!")
                    property_data = json_data["property"][0]
                    
                    # Extract and print some details
                    address_obj = property_data.get("address", {})
                    full_address = f"{address_obj.get('line1', '')}, {address_obj.get('line2', '')}"
                    print(f"Property address: {full_address}")
                    
                    property_id = property_data.get("identifier", {}).get("attomId", "")
                    print(f"Property ID: {property_id}")
                    
                    property_type = property_data.get("summary", {}).get("proptype", "Unknown")
                    print(f"Property type: {property_type}")
                    
                    sale = property_data.get("sale", {})
                    amount = sale.get("amount", {})
                    sale_price = amount.get("saleamt")
                    if sale_price:
                        print(f"Last sale price: ${sale_price:,}")
                else:
                    print("No property data found in response")
        
        except json.JSONDecodeError:
            print("Response is not valid JSON:")
            print(data[:1000] + "..." if len(data) > 1000 else data)
            
    except Exception as e:
        print(f"ERROR: Exception occurred while testing API: {str(e)}")

# ===== RENTCAST API IMPLEMENTATIONS =====

def get_property_details_rentcast(input_data: PropertyDetailsInput) -> PropertyDetailsOutput:
    """
    Get detailed information for a property based on its address using the Rentcast API.
    
    This is the detailed implementation that returns structured data. The simplified
    tool version for the agent to use is property_details_rentcast.
    
    Args:
        input_data: A PropertyDetailsInput object containing the address
        
    Returns:
        A PropertyDetailsOutput object with property details
    """
    import os
    import requests
    import json
    import datetime
    from dotenv import load_dotenv
    
    # Load environment variables to get API key
    load_dotenv()
    api_key = os.environ.get("RENTCAST_API_KEY")
    
    if not api_key:
        raise ValueError("API key not found in environment variables. Please add RENTCAST_API_KEY to your .env file.")
    
    print(f"DEBUG: Starting Rentcast property search for address: '{input_data.address}'")
    
    # Prepare API URL and headers
    url = "https://api.rentcast.io/v1/properties"
    
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }
    
    # Prepare query parameters
    params = {
        "address": input_data.address
    }
    
    try:
        # Make the API request
        print(f"DEBUG: Sending request to Rentcast API: {url}")
        print(f"DEBUG: Parameters: {params}")
        
        response = safe_requests.get(
            url,
            headers=headers,
            params=params
        )
        
        # Print response details for debugging
        print(f"DEBUG: Response Status: {response.status_code}")
        
        # Check for successful response
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        print(f"DEBUG: Rentcast API response received")
        
        # Check if we have property data
        if not data or not isinstance(data, list) or len(data) == 0:
            raise ValueError(f"No property found for address: {input_data.address}")
        
        # Get the first property from the results
        property_data = data[0]
        
        # Debug print
        print(f"DEBUG: Property data: {type(property_data).__name__}")
        
        # Get full formatted address
        full_address = property_data.get("formattedAddress", "")
        
        # Extract property details with more robust handling
        bedrooms = property_data.get("bedrooms", 0)
        if bedrooms is None:
            bedrooms = 0
        elif not isinstance(bedrooms, (int, float)):
            try:
                bedrooms = int(bedrooms)
            except (ValueError, TypeError):
                bedrooms = 0
        
        bathrooms = property_data.get("bathrooms", 0)
        if bathrooms is None:
            bathrooms = 0
        elif not isinstance(bathrooms, (int, float)):
            try:
                bathrooms = float(bathrooms)
            except (ValueError, TypeError):
                bathrooms = 0
        
        square_footage = property_data.get("squareFootage", 0)
        if square_footage is None:
            square_footage = 0
        
        year_built = property_data.get("yearBuilt", 0)
        if year_built is None:
            year_built = 0
        
        # Get lot size
        lot_size_value = property_data.get("lotSize", 0)
        if lot_size_value is None or lot_size_value == 0:
            lot_size = "Not available"
        else:
            lot_size = f"{lot_size_value} sq ft"
        
        # Get property type
        property_type = property_data.get("propertyType", "Unknown")
        
        # Get estimated value - use the latest tax assessment
        tax_assessments = property_data.get("taxAssessments", {})
        tax_value = 0
        if tax_assessments:
            # Find the most recent tax assessment year
            try:
                latest_year = max([int(year) for year in tax_assessments.keys() if year.isdigit()], default=0)
                if latest_year > 0:
                    latest_assessment = tax_assessments.get(str(latest_year), {})
                    tax_value = latest_assessment.get("value", 0)
            except (ValueError, KeyError, TypeError):
                tax_value = 0
        
        # Also check for valuation field
        valuation = property_data.get("valuation", 0)
        estimated_value_num = tax_value or valuation or 0
        estimated_value = f"${estimated_value_num:,}" if estimated_value_num else "Not available"
        
        # Get last sale information
        history = property_data.get("history", {})
        last_sold_date = "Unknown"
        last_sold_price = 0
        
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
                    last_sold_price = sale_info["price"]
        
        last_sold_price_formatted = f"${last_sold_price:,}" if last_sold_price else "Unknown"
        last_sold = f"{last_sold_date} for {last_sold_price_formatted}"
        
        # Get photos
        photos = []
        images = property_data.get("images", [])
        if images:
            for img in images[:5]:  # Limit to first 5 images
                if img and isinstance(img, str):
                    photos.append(img)
        
        # Get property ID
        property_id = property_data.get("id", "")
        
        # Create the output object
        output = PropertyDetailsOutput(
            address=full_address,
            bedrooms=int(bedrooms),
            bathrooms=float(bathrooms),
            square_footage=int(square_footage),
            year_built=int(year_built),
            lot_size=lot_size,
            property_type=property_type,
            estimated_value=estimated_value,
            last_sold=last_sold,
            photos=photos,
            property_id=str(property_id)
        )
        
        print(f"DEBUG: Successfully parsed property data")
        print(f"DEBUG: Final output object: {output}")
        return output
        
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: HTTP error occurred: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"DEBUG: Error Response Status: {e.response.status_code}")
            print(f"DEBUG: Error Response Headers: {e.response.headers}")
            print(f"DEBUG: Error Response Content: {e.response.text[:1000]}...")
        raise ValueError(f"HTTP error when calling Rentcast API: {str(e)}")
        
    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to parse API response as JSON: {str(e)}")
        print(f"DEBUG: Non-JSON Response Content: {response.text[:1000]}...")
        raise ValueError(f"Failed to parse Rentcast API response as JSON: {str(e)}")
        
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise ValueError(f"Unexpected error when calling Rentcast API: {str(e)}")

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
    
    # Import needed here to avoid circular imports
    import os
    import requests
    import json
    from dotenv import load_dotenv
    
    # Load API key
    load_dotenv()
    api_key = os.environ.get("RENTCAST_API_KEY")
    
    if not api_key:
        return "Error: API key not found in environment variables. Please add RENTCAST_API_KEY to your .env file."
    
    # Prepare API URL
    base_url = "https://api.rentcast.io/v1/properties"
    
    # Prepare headers
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }
    
    # Make the API request
    try:
        response = safe_requests.get(
            f"{base_url}?address={address}",
            headers=headers
        )
        
        # Check for successful response
        response.raise_for_status()
        
        # Parse the JSON response
        json_data = response.json()
        
        # Check if we have property data
        if not json_data or not isinstance(json_data, list) or len(json_data) == 0:
            return f"No property found for address: {address}"
        
        # Get the first property from the results
        property_data = json_data[0]
        
        print("\n=========== RENTCAST FULL RAW JSON DATA ===========")
        print(json.dumps(property_data, indent=2))
        print("===================================================\n")
        
        # Return the entire property data as JSON
        return json.dumps(property_data, indent=2)
        
    except requests.exceptions.HTTPError as e:
        return f"Error retrieving property details: HTTP error - {str(e)}"
    except json.JSONDecodeError as e:
        return f"Error retrieving property details: Invalid JSON response - {str(e)}"
    except Exception as e:
        return f"Error retrieving property details: {str(e)}"

def test_rentcast_api(api_key: str = None):
    """
    Test function to check if the Rentcast API is working correctly.
    
    Used by test_api.py for testing API connectivity.
    
    Args:
        api_key: Optional API key, if not provided it will be loaded from environment
    """
    import os
    import json
    from dotenv import load_dotenv
    
    # Load environment variables if no API key provided
    if not api_key:
        load_dotenv()
        api_key = os.environ.get("RENTCAST_API_KEY")
    
    if not api_key:
        print("ERROR: API key not provided and not found in environment variables")
        return
    
    print("=" * 80)
    print("TESTING RENTCAST API CONNECTIVITY")
    print("=" * 80)
    
    # Test with a known address
    test_address = "4529 Winona Ct, Denver, CO 80212"
    
    # Prepare API URL
    base_url = "https://api.rentcast.io/v1/properties"
    
    # Prepare headers
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }
    
    print(f"Testing with API key: {api_key[:5]}...{api_key[-5:]}")
    print(f"Base URL: {base_url}")
    print(f"Test Address: {test_address}")
    
    try:
        # Make the API request
        print("Sending request to API...")
        
        response = safe_requests.get(
            f"{base_url}?address={test_address}",
            headers=headers
        )
        
        # Print response details
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Try to parse as JSON
        try:
            json_data = response.json()
            print(f"Successfully parsed response as JSON")
            
            # Check if we have property data
            if json_data and isinstance(json_data, list) and len(json_data) > 0:
                print(f"Found property data!")
                property_data = json_data[0]
                
                # Extract and print some details
                full_address = property_data.get("formattedAddress", "Unknown")
                print(f"Property address: {full_address}")
                
                property_id = property_data.get("id", "Unknown")
                print(f"Property ID: {property_id}")
                
                property_type = property_data.get("propertyType", "Unknown")
                print(f"Property type: {property_type}")
                
                bedrooms = property_data.get("bedrooms", "Unknown")
                bathrooms = property_data.get("bathrooms", "Unknown")
                square_footage = property_data.get("squareFootage", "Unknown")
                
                print(f"Details: {bedrooms} bed, {bathrooms} bath, {square_footage} sq ft")
                
                # Check for valuation
                tax_assessments = property_data.get("taxAssessments", {})
                if tax_assessments:
                    # Find the most recent tax assessment year
                    tax_years = [year for year in tax_assessments.keys() if year.isdigit()]
                    if tax_years:
                        latest_year = max(tax_years)
                        latest_assessment = tax_assessments.get(latest_year, {})
                        tax_value = latest_assessment.get("value", "Unknown")
                        print(f"Tax assessment ({latest_year}): ${tax_value:,}" if isinstance(tax_value, (int, float)) else f"Tax assessment: {tax_value}")
            else:
                print("No property data found in response")
                print(f"Response content: {json_data}")
        
        except json.JSONDecodeError:
            print("Response is not valid JSON:")
            print(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
            
    except Exception as e:
        print(f"ERROR: Exception occurred while testing API: {str(e)}")

# ===== PROPERTY VALUATION TOOL =====

class ComparableProperty(BaseModel):
    """Model for comparable property data in valuation responses."""
    address: str = Field(..., description="The full address of the comparable property")
    property_type: str = Field(..., description="Type of property (single family, condo, etc.)")
    bedrooms: int = Field(..., description="Number of bedrooms in the property")
    bathrooms: float = Field(..., description="Number of bathrooms in the property")
    square_footage: int = Field(..., description="Total square footage of the property")
    year_built: int = Field(..., description="Year the property was built")
    price: float = Field(..., description="Listed price of the comparable property")
    listing_type: str = Field(..., description="Type of listing (Standard, etc.)")
    days_on_market: int = Field(..., description="Number of days the property was on the market")
    distance: float = Field(..., description="Distance from subject property in miles")
    
class PropertyValuationInput(BaseModel):
    """Input model for property valuation API calls."""
    address: str = Field(..., description="The full address of the property to get valuation for")
    property_type: Optional[str] = Field(None, description="Type of property (Single Family, Condo, etc.)")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms in the property")
    bathrooms: Optional[float] = Field(None, description="Number of bathrooms in the property")
    square_footage: Optional[int] = Field(None, description="Total square footage of the property")

class PropertyValuationOutput(BaseModel):
    """Output model containing property valuation data."""
    address: str = Field(..., description="The full address of the property")
    estimated_value: float = Field(..., description="Estimated property value")
    value_range_low: float = Field(..., description="Lower bound of the value estimate range")
    value_range_high: float = Field(..., description="Upper bound of the value estimate range")
    comparables: List[ComparableProperty] = Field(..., description="List of comparable properties")

def get_property_valuation(input_data: PropertyValuationInput) -> PropertyValuationOutput:
    """
    Get property valuation data including estimated value and comparable properties from Rentcast API.
    
    This is the detailed implementation that returns structured data. The simplified
    tool version for the agent to use is property_valuation.
    
    Args:
        input_data: A PropertyValuationInput object containing the property address
        
    Returns:
        A PropertyValuationOutput object with valuation details and comparable properties
    """
    import os
    import json
    import requests
    import urllib.parse
    from dotenv import load_dotenv
    
    # Load environment variables to get API key
    load_dotenv()
    api_key = os.environ.get("RENTCAST_API_KEY")
    
    if not api_key:
        raise ValueError("API key not found in environment variables. Please add RENTCAST_API_KEY to your .env file.")
    
    print(f"DEBUG: Starting property valuation for address: '{input_data.address}'")
    print(f"DEBUG: Property Type: {input_data.property_type}")
    print(f"DEBUG: Bedrooms: {input_data.bedrooms}")
    print(f"DEBUG: Bathrooms: {input_data.bathrooms}")
    print(f"DEBUG: Square Footage: {input_data.square_footage}")
    
    # Prepare API URL and parameters
    base_url = "https://api.rentcast.io/v1/avm/value"
    params = {"address": input_data.address}
    
    # Add optional parameters if they're provided
    if input_data.property_type:
        params["propertyType"] = input_data.property_type
    if input_data.bedrooms is not None:  # Changed to handle 0 bedrooms
        params["bedrooms"] = input_data.bedrooms
    if input_data.bathrooms is not None:  # Changed to handle 0 bathrooms
        params["bathrooms"] = input_data.bathrooms
    if input_data.square_footage is not None:  # Changed to handle 0 square footage
        params["squareFootage"] = input_data.square_footage
    
    # Add compCount parameter to get comparable properties (default to 20)
    params["compCount"] = 20
    
    # Prepare headers
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }
    
    print(f"DEBUG: Using API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    print(f"DEBUG: Base URL: {base_url}")
    print(f"DEBUG: Request params: {params}")
    
    # Construct and print the full URL for debugging
    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"
    print(f"DEBUG: Full URL: {full_url}")
    
    try:
        print(f"DEBUG: Sending request to Rentcast AVM API...")
        response = safe_requests.get(
            base_url,
            params=params,
            headers=headers
        )
        
        # Print response details for debugging
        print(f"DEBUG: Response Status: {response.status_code}")
        print(f"DEBUG: Response Headers: {response.headers}")
        print(f"DEBUG: Response Content (first 500 chars): {response.text[:500]}...")
        
        # Check for successful response
        response.raise_for_status()
        
        # Parse the JSON response
        valuation_data = response.json()
        print(f"DEBUG: API response parsed successfully")
        
        # Log limited structure of the response for debugging
        print(f"DEBUG: Response keys: {list(valuation_data.keys()) if isinstance(valuation_data, dict) else 'Not a dictionary'}")
        
        # Extract valuation data
        subject_address = input_data.address  # Use input address as we might not get it in the response
        estimated_value = valuation_data.get("price", 0)
        value_range_low = valuation_data.get("priceRangeLow", 0)
        value_range_high = valuation_data.get("priceRangeHigh", 0)
        
        # Extract comparables
        comparable_properties = []
        raw_comparables = valuation_data.get("comparables", [])
        
        for comp in raw_comparables:
            # Create a ComparableProperty for each comparable
            comparable = ComparableProperty(
                address=comp.get("formattedAddress", "Unknown"),
                property_type=comp.get("propertyType", "Unknown"),
                bedrooms=comp.get("bedrooms", 0),
                bathrooms=comp.get("bathrooms", 0),
                square_footage=comp.get("squareFootage", 0),
                year_built=comp.get("yearBuilt", 0),
                price=comp.get("price", 0),
                listing_type=comp.get("listingType", "Unknown"),
                days_on_market=comp.get("daysOnMarket", 0),
                distance=comp.get("distance", 0)
            )
            comparable_properties.append(comparable)
        
        # Create the output object
        output = PropertyValuationOutput(
            address=subject_address,
            estimated_value=estimated_value,
            value_range_low=value_range_low,
            value_range_high=value_range_high,
            comparables=comparable_properties
        )
        
        print(f"DEBUG: Final valuation output created with {len(comparable_properties)} comparables")
        return output
        
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: HTTP error occurred: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"DEBUG: Error Response Status: {e.response.status_code}")
            print(f"DEBUG: Error Response Headers: {e.response.headers}")
            print(f"DEBUG: Error Response Content: {e.response.text[:1000]}...")
        raise ValueError(f"HTTP error when calling Rentcast API for valuation: {str(e)}")
        
    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to parse API response as JSON: {str(e)}")
        print(f"DEBUG: Non-JSON Response Content: {response.text[:1000]}...")
        raise ValueError(f"Failed to parse Rentcast API valuation response as JSON: {str(e)}")
        
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise ValueError(f"Unexpected error when calling Rentcast API for valuation: {str(e)}")

@tool
def property_valuation(address: str, property_type: str = None, bedrooms: int = None, bathrooms: float = None, square_footage: int = None) -> str:
    """
    Get a property valuation estimate and comparable properties for a given address using the Rentcast API.
    
    Args:
        address: The property address to look up
        property_type: Type of property (Single Family, Condo, etc.)
        bedrooms: Number of bedrooms in the property
        bathrooms: Number of bathrooms in the property
        square_footage: Total square footage of the property
        
    Returns:
        A valuation report with estimated value and comparable property information
    """
    print("\n===== CALLING RENTCAST VALUATION API TOOL =====")
    print(f"Getting valuation for property: {address}")
    print(f"Property Type: {property_type}")
    print(f"Bedrooms: {bedrooms}")
    print(f"Bathrooms: {bathrooms}")
    print(f"Square Footage: {square_footage}")
    print("=============================================\n")
    
    # Import needed here to avoid circular imports
    import os
    import requests
    import json
    import datetime
    import urllib.parse
    from dotenv import load_dotenv
    
    # Load API key
    load_dotenv()
    api_key = os.environ.get("RENTCAST_API_KEY")
    
    print(f"API Key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    
    if not api_key:
        return "Error: API key not found in environment variables. Please add RENTCAST_API_KEY to your .env file."
    
    # Prepare API URL and parameters
    base_url = "https://api.rentcast.io/v1/avm/value"
    params = {"address": address}
    
    # Add optional parameters if they're provided
    if property_type:
        params["propertyType"] = property_type
    if bedrooms is not None:  # Changed to handle 0 bedrooms
        params["bedrooms"] = bedrooms
    if bathrooms is not None:  # Changed to handle 0 bathrooms
        params["bathrooms"] = bathrooms
    if square_footage is not None:  # Changed to handle 0 square footage
        params["squareFootage"] = square_footage
        
    # Add compCount parameter to get comparable properties (default to 20)
    params["compCount"] = 20
    
    # Print detailed debug info
    print(f"DEBUG: Base URL: {base_url}")
    print(f"DEBUG: Query Parameters: {params}")
    
    # Construct and print the full URL for debugging
    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"
    print(f"DEBUG: Full URL: {full_url}")
    
    # Prepare headers
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }
    
    print(f"DEBUG: Request Headers: {headers}")
    
    # Make the API request
    try:
        print(f"DEBUG: Sending request to Rentcast AVM API...")
        response = safe_requests.get(
            base_url,
            params=params,
            headers=headers
        )
        
        # Print response status and headers
        print(f"DEBUG: Response Status: {response.status_code}")
        print(f"DEBUG: Response Headers: {response.headers}")
        
        # Print the first part of the response for debugging
        print(f"DEBUG: Response Content (first 500 chars): {response.text[:500]}...")
        
        # Check for successful response
        response.raise_for_status()
        
        # Parse the JSON response
        valuation_data = response.json()
        
        # Extract key valuation data with detailed debug info
        estimated_value = valuation_data.get("price", 0)
        print(f"DEBUG VALUATION: Raw estimated value from API: {estimated_value} (type: {type(estimated_value).__name__})")
        
        # Make sure estimated_value is a number
        if not isinstance(estimated_value, (int, float)):
            try:
                estimated_value = float(estimated_value)
                print(f"DEBUG VALUATION: Converted estimated_value to number: {estimated_value}")
            except (ValueError, TypeError):
                print(f"DEBUG VALUATION: Could not convert estimated_value to number, using 0")
                estimated_value = 0
        
        value_range_low = valuation_data.get("priceRangeLow", 0)
        print(f"DEBUG VALUATION: Value range low from API: {value_range_low}")
        
        value_range_high = valuation_data.get("priceRangeHigh", 0)
        print(f"DEBUG VALUATION: Value range high from API: {value_range_high}")
        
        # Extract comparables
        comparables = valuation_data.get("comparables", [])
        print(f"DEBUG VALUATION: Found {len(comparables)} comparable properties")
        if comparables:
            print(f"DEBUG VALUATION: First comparable price: {comparables[0].get('price', 'N/A')}")
        
        # Format the valuation report with exact values
        valuation_report = f"""PROPERTY VALUATION REPORT:
• Address: {address}
• EXACT Estimated Value: ${int(estimated_value):,}
• EXACT Value Range: ${int(value_range_low):,} to ${int(value_range_high):,}
• Data Source: Rentcast AVM (Automated Valuation Model)

COMPARABLE PROPERTIES ({len(comparables)} found):
"""
        
        # Add information about each comparable property
        for i, comp in enumerate(comparables[:5], 1):  # Limit to 5 comparables for readability
            comp_address = comp.get("formattedAddress", "Unknown")
            comp_price = comp.get("price", 0)
            comp_bedrooms = comp.get("bedrooms", 0)
            comp_bathrooms = comp.get("bathrooms", 0)
            comp_sqft = comp.get("squareFootage", 0)
            comp_year = comp.get("yearBuilt", 0)
            comp_distance = comp.get("distance", 0)
            comp_days = comp.get("daysOnMarket", 0)
            
            price_per_sqft = comp_price / comp_sqft if comp_sqft else 0
            
            valuation_report += f"""
Comparable #{i}:
• Address: {comp_address}
• EXACT Price: ${int(comp_price):,}
• EXACT Details: {int(comp_bedrooms)} bed, {comp_bathrooms} bath, {int(comp_sqft):,} sq ft
• EXACT Year Built: {int(comp_year)}
• EXACT Distance: {comp_distance:.2f} miles
• EXACT Days on Market: {comp_days}
"""
        
        # Add a market analysis summary with exact values
        avg_price = sum(comp.get("price", 0) for comp in comparables) / len(comparables) if comparables else 0
        avg_price_per_sqft = sum(comp.get("price", 0) / comp.get("squareFootage", 1) for comp in comparables) / len(comparables) if comparables else 0
        avg_days = sum(comp.get("daysOnMarket", 0) for comp in comparables) / len(comparables) if comparables else 0
        
        valuation_report += f"""
MARKET ANALYSIS SUMMARY (EXACT VALUES):
• EXACT Average Comparable Price: ${int(avg_price):,}
• EXACT Average Price per Square Foot: ${int(avg_price_per_sqft)}
• EXACT Average Days on Market: {int(avg_days)} days
• EXACT Number of Comparable Properties: {len(comparables)}
"""
        
        return valuation_report
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"Error retrieving property valuation: HTTP error - {str(e)}"
        print(f"DEBUG: {error_msg}")
        if hasattr(e, 'response') and e.response:
            print(f"DEBUG: Error Response Status: {e.response.status_code}")
            print(f"DEBUG: Error Response Headers: {e.response.headers}")
            print(f"DEBUG: Error Response Content: {e.response.text[:1000]}...")
        return error_msg
    except json.JSONDecodeError as e:
        error_msg = f"Error retrieving property valuation: Invalid JSON response - {str(e)}"
        print(f"DEBUG: {error_msg}")
        print(f"DEBUG: Non-JSON Response Content: {response.text[:1000]}...")
        return error_msg
    except Exception as e:
        error_msg = f"Error retrieving property valuation: {str(e)}"
        print(f"DEBUG: Unexpected exception: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return error_msg

# ===== REALTY API (ZILLOW VIA RAPIDAPI) IMPLEMENTATION =====

def get_property_details_realty(input_data: PropertyDetailsInput) -> PropertyDetailsOutput:
    """
    Get detailed information for a property based on its address using the RealtyInUS API via RapidAPI.
    
    This is the detailed implementation that returns structured data. The simplified
    tool version for the agent to use is property_details_realty.
    
    Args:
        input_data: A PropertyDetailsInput object containing the address
        
    Returns:
        A PropertyDetailsOutput object with property details
    """
    import os
    import http.client
    import json
    import urllib.parse
    from dotenv import load_dotenv
    
    # Load environment variables to get API key
    load_dotenv()
    api_key = os.environ.get("RAPIDAPI_KEY")
    
    if not api_key:
        raise ValueError("API key not found in environment variables. Please add RAPIDAPI_KEY to your .env file.")
    
    print(f"DEBUG: Starting RealtyInUS property search for address: '{input_data.address}'")
    
    # Parse address for better search results
    address = input_data.address
    parts = address.split(',')
    street_address = parts[0].strip() if len(parts) > 0 else ""
    city = parts[1].strip() if len(parts) > 1 else ""
    state_zip = parts[2].strip() if len(parts) > 2 else ""
    
    # Extract state and zip if possible
    state_zip_parts = state_zip.split()
    state = state_zip_parts[0].strip() if len(state_zip_parts) > 0 else ""
    zip_code = state_zip_parts[1].strip() if len(state_zip_parts) > 1 else ""
    
    print(f"DEBUG: Parsed address: Street: '{street_address}', City: '{city}', State: '{state}', ZIP: '{zip_code}'")
    
    try:
        # Common headers for all requests
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"
        }
        
        # Step 1: Search for properties by location
        search_url = "https://realty-in-us.p.rapidapi.com/properties/v2/list-for-sale"
        
        # Build the search parameters
        search_params = {
            "city": city,
            "state_code": state,
            "offset": "0",
            "limit": "10",
            "sort": "relevance"
        }
        
        # Add street address and postal code if available
        if street_address:
            search_params["address"] = street_address
        if zip_code:
            search_params["postal_code"] = zip_code
            
        print(f"DEBUG: Search URL: {search_url}")
        print(f"DEBUG: Search params: {search_params}")
        
        search_response = safe_requests.get(
            search_url,
            headers=headers,
            params=search_params
        )
        
        # Print response details for debugging
        print(f"DEBUG: Search response status: {search_response.status_code}")
        
        # Check for successful response
        search_response.raise_for_status()
        
        # Parse the JSON response
        search_data = search_response.json()
        print(f"DEBUG: RealtyInUS search API response received")
        
        # Check if properties were found
        properties = search_data.get("properties", [])
        if not properties:
            raise ValueError(f"No properties found for address: {input_data.address}")
        
        # Find the best matching property (first result)
        best_match = properties[0]
        
        # Step 2: Get property details for the best match
        property_id = best_match.get("property_id")
        if not property_id:
            raise ValueError(f"No property ID found for address: {input_data.address}")
            
        print(f"DEBUG: Found property with ID: {property_id}")
        
        property_url = "https://realty-in-us.p.rapidapi.com/properties/v2/detail"
        property_params = {
            "property_id": property_id
        }
        
        property_response = safe_requests.get(
            property_url,
            headers=headers,
            params=property_params
        )
        
        # Print response details for debugging
        print(f"DEBUG: Property details response status: {property_response.status_code}")
        
        # Check for successful response
        property_response.raise_for_status()
        
        # Parse the JSON response
        property_data = property_response.json()
        print(f"DEBUG: RealtyInUS property API response received")
        
        # Get the property information
        property_info = property_data.get("properties", [{}])[0]
        
        # Extract essential property details
        address_data = property_info.get("address", {})
        full_address = f"{address_data.get('line', '')}, {address_data.get('city', '')}, {address_data.get('state', '')} {address_data.get('postal_code', '')}"
        
        # Extract property details
        bedrooms = property_info.get("beds", 0)
        # Handle string or numeric values for bedrooms
        if isinstance(bedrooms, str):
            try:
                bedrooms = int(bedrooms)
            except ValueError:
                bedrooms = 0
        
        bathrooms = property_info.get("baths", 0.0)
        # Handle string or numeric values for bathrooms
        if isinstance(bathrooms, str):
            try:
                bathrooms = float(bathrooms)
            except ValueError:
                bathrooms = 0.0
        
        # Get square footage
        building_size = property_info.get("building_size", {})
        square_footage = building_size.get("size", 0)
        if isinstance(square_footage, str):
            try:
                square_footage = int(square_footage.replace(",", ""))
            except ValueError:
                square_footage = 0
        
        year_built = property_info.get("year_built", 0)
        if isinstance(year_built, str):
            try:
                year_built = int(year_built)
            except ValueError:
                year_built = 0
        
        # Get lot size
        lot_size_value = property_info.get("lot_size", {}).get("size", 0)
        lot_size_unit = property_info.get("lot_size", {}).get("units", "sq ft")
        lot_size = f"{lot_size_value} {lot_size_unit}"
        
        # Get property type
        property_type = property_info.get("prop_type", "Unknown")
        if "single" in property_type.lower():
            property_type = "Single Family Residence"
        
        # Get price/value
        price = property_info.get("price", 0)
        if isinstance(price, str):
            # Remove non-numeric characters
            price = ''.join(filter(lambda x: x.isdigit() or x == '.', price))
            try:
                price = float(price)
            except ValueError:
                price = 0
                
        estimated_value = f"${int(price):,}" if price else "Not available"
        
        # Get last sold info
        last_sold_date = property_info.get("last_sold_date", "Unknown")
        last_sold_price = property_info.get("last_sold_price", 0)
        if last_sold_price:
            if isinstance(last_sold_price, str):
                last_sold_price = ''.join(filter(lambda x: x.isdigit() or x == '.', last_sold_price))
                try:
                    last_sold_price = float(last_sold_price)
                except ValueError:
                    last_sold_price = 0
            last_sold_price = f"${int(last_sold_price):,}"
        else:
            last_sold_price = "Unknown"
            
        last_sold = f"{last_sold_date} for {last_sold_price}"
        
        # Get photos
        photos = []
        photo_data = property_info.get("photos", [])
        for photo in photo_data[:5]:  # Limit to first 5 images
            if isinstance(photo, dict) and "href" in photo:
                photos.append(photo["href"])
            elif isinstance(photo, str):
                photos.append(photo)
        
        # Create the output object
        output = PropertyDetailsOutput(
            address=full_address,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_footage=square_footage,
            year_built=year_built,
            lot_size=lot_size,
            property_type=property_type,
            estimated_value=estimated_value,
            last_sold=last_sold,
            photos=photos,
            property_id=str(property_id)
        )
        
        print(f"DEBUG: Successfully parsed property data")
        return output
        
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: HTTP error occurred: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"DEBUG: Error Response Status: {e.response.status_code}")
            print(f"DEBUG: Error Response Headers: {e.response.headers}")
            print(f"DEBUG: Error Response Content: {e.response.text[:1000]}...")
        raise ValueError(f"HTTP error when calling RealtyInUS API: {str(e)}")
        
    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to parse API response as JSON: {str(e)}")
        if 'response' in locals():
            print(f"DEBUG: Non-JSON Response Content: {response.text[:1000]}...")
        raise ValueError(f"Failed to parse RealtyInUS API response as JSON: {str(e)}")
        
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise ValueError(f"Unexpected error when calling RealtyInUS API: {str(e)}")

@tool
def property_details_realty(address: str) -> str:
    """
    Get property details for a given address using the Zillow API from RapidAPI.
    
    Args:
        address: The property address to look up
        
    Returns:
        A description of the property in a structured JSON format
    """
    print("\n===== CALLING ZILLOW API TOOL =====")
    print(f"Searching for property: {address}")
    
    # Import needed here to avoid circular imports
    import os
    import http.client
    import json
    import urllib.parse
    from dotenv import load_dotenv
    
    # Load API key
    load_dotenv()
    api_key = os.environ.get("RAPIDAPI_KEY")
    
    if not api_key:
        return "Error: API key not found in environment variables. Please add RAPIDAPI_KEY to your .env file."
    
    print(f"Using API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    
    try:
        # Using the http.client approach from the code snippet
        conn = http.client.HTTPSConnection("zillow-com1.p.rapidapi.com")
        
        # Prepare headers exactly as in the provided example
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': "zillow-com1.p.rapidapi.com"
        }
        
        # URL encode the address parameter
        encoded_address = urllib.parse.quote(address)
        
        # Build the request path
        request_path = f"/property?address={encoded_address}"
        
        print(f"Connection host: zillow-com1.p.rapidapi.com")
        print(f"Request path: {request_path}")
        print(f"Headers: {headers}")
        
        # Make the API request
        conn.request("GET", request_path, headers=headers)
        
        # Get the response
        res = conn.getresponse()
        
        # Print response details for debugging
        print(f"Response status: {res.status}")
        print(f"Response reason: {res.reason}")
        
        # Read response data
        data = res.read()
        
        # If we got a non-200 response, print the error
        if res.status != 200:
            error_text = data.decode('utf-8')
            print(f"Error response: {error_text[:500]}")
            return f"Error retrieving property details: {res.status} {res.reason} - {error_text[:200]}"
        
        # Decode and parse the JSON response
        response_text = data.decode('utf-8')
        property_data = json.loads(response_text)
        
        print("\n=========== ZILLOW PROPERTY FULL RAW JSON DATA ===========")
        print(json.dumps(property_data, indent=2))
        print("=========================================================\n")
        
        # Format the data in a structure matching what the agent expects
        # Extract address
        address_obj = {}
        if "streetAddress" in property_data:
            address_obj["line1"] = property_data.get("streetAddress", "")
        if "city" in property_data:
            address_obj["city"] = property_data.get("city", "")
        if "state" in property_data:
            address_obj["state"] = property_data.get("state", "")
        if "zipcode" in property_data:
            address_obj["postal_code"] = property_data.get("zipcode", "")
        
        # Extract property details
        description = {
            "type": property_data.get("homeType", ""),
            "beds": property_data.get("bedrooms", 0),
            "baths": property_data.get("bathrooms", 0),
            "sqft": property_data.get("livingArea", 0),
            "yearBuilt": property_data.get("yearBuilt", 0)
        }
        
        # Extract price information
        price_info = {
            "value": property_data.get("price", 0),
            "zestimate": property_data.get("zestimate", 0),
            "formatted": f"${property_data.get('price', 0):,}" if property_data.get('price') else "$0"
        }
        
        # Get photos if available
        photos = []
        if "imgSrc" in property_data and property_data["imgSrc"]:
            photos.append(property_data["imgSrc"])
        
        # Create the formatted result
        formatted_data = {
            "address": address_obj,
            "description": description,
            "price": price_info,
            "photos": photos,
            "property_id": property_data.get("zpid", "")
        }
        
        # Return the nicely formatted data
        formatted_json = json.dumps(formatted_data, indent=2)
        return formatted_json
        
    except http.client.HTTPException as e:
        error_msg = f"Error retrieving property details: HTTP error - {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except json.JSONDecodeError as e:
        error_msg = f"Error retrieving property details: Invalid JSON response - {str(e)}"
        print(f"DEBUG: {error_msg}")
        if 'response_text' in locals():
            print(f"DEBUG: Non-JSON Response Content: {response_text[:1000]}...")
        return error_msg
    except Exception as e:
        error_msg = f"Error retrieving property details: {str(e)}"
        print(f"DEBUG: Unexpected exception: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return error_msg

# End of property API tools module

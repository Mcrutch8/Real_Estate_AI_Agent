#!/usr/bin/env python3
"""
Test script specifically for the Zillow RapidAPI tool.
Run this script directly to test if the API is working properly.
"""

import os
import sys
import json
import http.client
import urllib.parse
from dotenv import load_dotenv

def test_zillow_api_directly():
    """Test the Zillow API directly using http.client."""
    # Check if we have a .env file
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        print(f"WARNING: No .env file found at {env_path}")
        print("You should create a .env file with your RAPIDAPI_KEY")
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("RAPIDAPI_KEY")
    
    if not api_key:
        print("ERROR: RAPIDAPI_KEY not found in environment variables.")
        print("Please add your API key to the .env file:")
        print("RAPIDAPI_KEY=your_api_key_here")
        return 1
    
    # Test address
    test_address = "2982 Kelham Grove Way, Birmingham, AL 35242"
    encoded_address = urllib.parse.quote(test_address)
    
    print("=" * 80)
    print("TESTING ZILLOW API DIRECTLY")
    print(f"Address: {test_address}")
    print(f"Encoded address: {encoded_address}")
    print("=" * 80)
    print(f"API Key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    
    try:
        # Setup the connection
        print("Connecting to zillow-com1.p.rapidapi.com...")
        conn = http.client.HTTPSConnection("zillow-com1.p.rapidapi.com")
        
        # Set headers
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': "zillow-com1.p.rapidapi.com"
        }
        
        # Build request path
        request_path = f"/property?address={encoded_address}"
        print(f"Request path: {request_path}")
        
        # Make the request
        print("Sending request...")
        conn.request("GET", request_path, headers=headers)
        
        # Get response
        res = conn.getresponse()
        print(f"Response status: {res.status} {res.reason}")
        
        # Read data
        data = res.read()
        response_text = data.decode('utf-8')
        
        # Check if successful
        if res.status == 200:
            print("SUCCESS! Parsing JSON response...")
            
            try:
                # Parse JSON
                property_data = json.loads(response_text)
                
                # Print pretty JSON
                print("\n=========== ZILLOW RAW JSON DATA ===========")
                print(json.dumps(property_data, indent=2)[:2000] + "...[truncated]" if len(json.dumps(property_data, indent=2)) > 2000 else json.dumps(property_data, indent=2))
                print("=============================================\n")
                
                # Extract key data points for verification
                print("\n=========== KEY DATA POINTS ===========")
                # Get address
                if "address" in property_data:
                    address = property_data.get("address", {})
                    print(f"Address: {address.get('streetAddress', 'N/A')}, {address.get('city', 'N/A')}, {address.get('state', 'N/A')} {address.get('zipcode', 'N/A')}")
                else:
                    print("Address: Not found in response")
                
                # Get basic details
                print(f"Bedrooms: {property_data.get('bedrooms', 'N/A')}")
                print(f"Bathrooms: {property_data.get('bathrooms', 'N/A')}")
                print(f"Square Footage: {property_data.get('livingArea', 'N/A')}")
                print(f"Year Built: {property_data.get('yearBuilt', 'N/A')}")
                print(f"Property Type: {property_data.get('homeType', 'N/A')}")
                
                # Get price data
                print(f"Price: {property_data.get('price', 'N/A')}")
                print(f"Zestimate: {property_data.get('zestimate', 'N/A')}")
                
                # Check for key missing fields
                missing_fields = []
                for field in ["address", "bedrooms", "bathrooms", "homeType", "livingArea"]:
                    if field not in property_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"\nWARNING: Missing expected fields: {', '.join(missing_fields)}")
                else:
                    print("\nAll expected fields are present in the response")
                
                print("=========================================\n")
                
                return 0
            except json.JSONDecodeError as e:
                print("ERROR: Failed to parse response as JSON")
                print(f"Raw response: {response_text[:500]}..." if len(response_text) > 500 else response_text)
                return 1
        else:
            print("ERROR: Request failed")
            print(f"Response content: {response_text[:500]}..." if len(response_text) > 500 else response_text)
            return 1
            
    except Exception as e:
        print(f"ERROR: Exception occurred while testing API: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

# Test the property_details_realty function from tools.py
def test_property_details_realty():
    """Test the property_details_realty function from tools.py."""
    # Import the function
    try:
        from tools import property_details_realty
        
        # Test address
        test_address = "2982 Kelham Grove Way, Birmingham, AL 35242"
        
        print("=" * 80)
        print("TESTING property_details_realty FUNCTION")
        print(f"Address: {test_address}")
        print("=" * 80)
        
        # Call the function
        print("Calling property_details_realty...")
        result = property_details_realty(test_address)
        
        # Print the result
        print("\n=========== FUNCTION RESULT ===========")
        print(f"Result type: {type(result).__name__}")
        print(f"Result length: {len(result)} characters")
        
        # Try to parse as JSON
        try:
            json_result = json.loads(result)
            print("Successfully parsed result as JSON")
            
            # Print the first part of the prettified JSON
            print("\nFirst 1000 characters of prettified JSON:")
            pretty_json = json.dumps(json_result, indent=2)
            print(pretty_json[:1000] + "...[truncated]" if len(pretty_json) > 1000 else pretty_json)
            
            # Extract key data points
            print("\nKey data points:")
            if "address" in json_result:
                address = json_result.get("address", {})
                print(f"Address: {address}")
            else:
                print("Address: Not found in result")
            
            # Check for missing fields
            if "description" in json_result:
                desc = json_result.get("description", {})
                print(f"Bedrooms: {desc.get('beds', 'N/A')}")
                print(f"Bathrooms: {desc.get('baths', 'N/A')}")
            else:
                print("Description fields not found in result")
            
        except json.JSONDecodeError:
            print("Result is not valid JSON. First 1000 characters:")
            print(result[:1000] + "...[truncated]" if len(result) > 1000 else result)
        
        print("=======================================\n")
        
        return 0
    except ImportError as e:
        print(f"ERROR: Failed to import property_details_realty function: {str(e)}")
        return 1
    except Exception as e:
        print(f"ERROR: Exception occurred while testing function: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Run tests for Zillow API."""
    print("\n\n" + "=" * 40)
    print("TESTING ZILLOW API IMPLEMENTATION")
    print("=" * 40 + "\n")
    
    # First test the API directly
    direct_api_result = test_zillow_api_directly()
    
    print("\n" + "=" * 40)
    print("DIRECT API TEST RESULT:", "SUCCESS" if direct_api_result == 0 else "FAILED")
    print("=" * 40 + "\n")
    
    # Then test the function
    function_result = test_property_details_realty()
    
    print("\n" + "=" * 40)
    print("FUNCTION TEST RESULT:", "SUCCESS" if function_result == 0 else "FAILED")
    print("=" * 40 + "\n")
    
    # Final summary
    if direct_api_result == 0 and function_result == 0:
        print("✅ All tests PASSED")
        return 0
    elif direct_api_result == 0:
        print("⚠️ Direct API test PASSED but function test FAILED")
        print("This suggests an issue with the function implementation, not the API itself.")
        return 1
    elif function_result == 0:
        print("⚠️ Function test PASSED but direct API test FAILED")
        print("This is unexpected and suggests a potential issue with the test implementation.")
        return 1
    else:
        print("❌ All tests FAILED")
        print("This suggests an issue with the API key or the API service itself.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
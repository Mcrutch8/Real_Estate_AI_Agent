#!/usr/bin/env python3
"""
Test script specifically for the property valuation tool.
Run this script directly to test if the Rentcast AVM API is working properly.
"""

import os
import sys
import json
import urllib.parse
from dotenv import load_dotenv
from security import safe_requests

def test_rentcast_avm_api():
    """Test the Rentcast AVM API directly."""
    # Check if we have a .env file
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        print(f"WARNING: No .env file found at {env_path}")
        print("You should create a .env file with your RENTCAST_API_KEY")
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("RENTCAST_API_KEY")
    
    if not api_key:
        print("ERROR: RENTCAST_API_KEY not found in environment variables.")
        print("Please add your API key to the .env file:")
        print("RENTCAST_API_KEY=your_api_key_here")
        return 1
    
    # Test parameters
    test_address = "5500 Grand Lake Dr, San Antonio, TX 78244"
    test_property_type = "Single Family"
    test_bedrooms = 3
    test_bathrooms = 2
    test_sqft = 1878
    
    print("=" * 80)
    print("TESTING RENTCAST AVM API DIRECTLY")
    print(f"Address: {test_address}")
    print(f"Property Type: {test_property_type}")
    print(f"Bedrooms: {test_bedrooms}")
    print(f"Bathrooms: {test_bathrooms}")
    print(f"Square Footage: {test_sqft}")
    print("=" * 80)
    
    # Prepare the API request
    base_url = "https://api.rentcast.io/v1/avm/value"
    
    # Test different parameter combinations to find what works
    test_variations = [
        {
            "name": "Address only with compCount",
            "params": {"address": test_address, "compCount": 5}
        },
        {
            "name": "All parameters with compCount",
            "params": {
                "address": test_address,
                "propertyType": test_property_type,
                "bedrooms": test_bedrooms,
                "bathrooms": test_bathrooms,
                "squareFootage": test_sqft,
                "compCount": 5
            }
        },
        {
            "name": "All parameters with lowercase property type",
            "params": {
                "address": test_address,
                "propertyType": test_property_type.lower(),
                "bedrooms": test_bedrooms,
                "bathrooms": test_bathrooms,
                "squareFootage": test_sqft,
                "compCount": 5
            }
        },
        {
            "name": "Address and property type only",
            "params": {
                "address": test_address,
                "propertyType": test_property_type,
                "compCount": 5
            }
        },
        {
            "name": "Address, bedrooms, and bathrooms only",
            "params": {
                "address": test_address,
                "bedrooms": test_bedrooms,
                "bathrooms": test_bathrooms,
                "compCount": 5
            }
        }
    ]
    
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }
    
    print(f"API Key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    
    # Test each variation
    success_found = False
    for variation in test_variations:
        print("\n" + "=" * 40)
        print(f"TESTING VARIATION: {variation['name']}")
        print("=" * 40)
        
        params = variation["params"]
        
        # Construct and print the full URL
        query_string = urllib.parse.urlencode(params)
        full_url = f"{base_url}?{query_string}"
        print(f"Request URL: {full_url}")
        print(f"Request Headers: {headers}")
        
        try:
            # Make the request
            response = safe_requests.get(
                base_url,
                params=params,
                headers=headers
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {response.headers}")
            
            # Check if the request was successful
            if response.status_code == 200:
                success_found = True
                print("SUCCESS! API call successful.")
                
                # Try to parse the JSON response
                try:
                    data = response.json()
                    print(f"Found data: {json.dumps(data, indent=2)[:1000]}...")
                    
                    # Check if essential fields are present
                    if "price" in data and "priceRangeLow" in data and "priceRangeHigh" in data:
                        print(f"Property Value: ${data['price']:,}")
                        print(f"Value Range: ${data['priceRangeLow']:,} to ${data['priceRangeHigh']:,}")
                        
                        if "comparables" in data and len(data["comparables"]) > 0:
                            print(f"Found {len(data['comparables'])} comparable properties")
                            print("SUCCESS! Full AVM data received.")
                        else:
                            print("WARNING: No comparable properties found in the response.")
                    else:
                        print("WARNING: Essential valuation fields missing from response.")
                        
                except json.JSONDecodeError:
                    print("ERROR: Response is not valid JSON.")
                    print(f"Raw response: {response.text[:1000]}...")
            else:
                print(f"ERROR: API returned status code {response.status_code}")
                print(f"Response: {response.text[:1000]}...")
                
        except Exception as e:
            print(f"ERROR: Exception occurred while testing API: {str(e)}")
    
    if success_found:
        print("\nAt least one variation was successful! Use the parameters from the successful test.")
        return 0
    else:
        print("\nAll variations failed. Check API key and endpoint details.")
        return 1

if __name__ == "__main__":
    sys.exit(test_rentcast_avm_api())

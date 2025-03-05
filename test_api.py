#!/usr/bin/env python3
"""
Test script for the ATTOM API integration.
Run this script directly to test if the API is working properly.
"""

import os
import sys
from dotenv import load_dotenv
from tools import test_attom_api, get_property_details, PropertyDetailsInput

def test_api_connectivity():
    """Test basic API connectivity."""
    # Check if we have a .env file
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        print(f"WARNING: No .env file found at {env_path}")
        print("You should create a .env file with your ATTOM API key")
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ATTOM_API_KEY")
    
    if not api_key:
        print("ERROR: ATTOM_API_KEY not found in environment variables.")
        print("Please add your API key to the .env file:")
        print("ATTOM_API_KEY=your_api_key_here")
        return 1
    
    print("=" * 80)
    print("TESTING ATTOM API CONNECTIVITY")
    print("=" * 80)
    
    # Run the API test
    test_attom_api(api_key)
    
    return 0

def test_property_details():
    """Test the property details function with a known address."""
    test_address = "4529 Winona Court, Denver, CO"
    
    print("=" * 80)
    print(f"TESTING PROPERTY DETAILS FOR: {test_address}")
    print("=" * 80)
    
    try:
        # Create input object
        input_data = PropertyDetailsInput(address=test_address)
        
        # Get property details
        result = get_property_details(input_data)
        
        # Print results
        print("\nProperty Details Results:")
        print(f"Address: {result.address}")
        print(f"Property Type: {result.property_type}")
        print(f"Bedrooms: {result.bedrooms}")
        print(f"Bathrooms: {result.bathrooms}")
        print(f"Square Footage: {result.square_footage} sq ft")
        print(f"Year Built: {result.year_built}")
        print(f"Lot Size: {result.lot_size}")
        print(f"Estimated Value: {result.estimated_value}")
        if result.last_sold_date and result.last_sold_price:
            print(f"Last Sold: {result.last_sold_date} for {result.last_sold_price}")
        print(f"Property ID: {result.property_id}")
        
        print("\nTest successful!")
        return 0
    
    except Exception as e:
        print(f"ERROR: Test failed with exception: {str(e)}")
        return 1

def main():
    """Run tests for the ATTOM API."""
    # Test API connectivity
    connectivity_result = test_api_connectivity()
    
    print("\n")
    
    # Test property details
    details_result = test_property_details()
    
    print("\nTests complete. If you see any errors above, check your API key and connectivity.")
    
    return connectivity_result or details_result

if __name__ == "__main__":
    sys.exit(main())
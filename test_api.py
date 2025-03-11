#!/usr/bin/env python3
"""
Test script for the ATTOM and Rentcast API integrations.
Run this script directly to test if the APIs are working properly.
"""

import os
import sys
from dotenv import load_dotenv
from tools import (
    test_corelogic_api as test_attom_api, test_rentcast_api, 
    get_property_details, get_property_details_rentcast, PropertyDetailsInput,
    property_valuation, PropertyValuationInput, get_property_valuation,
    property_details_realty
)

def test_attom_api_connectivity():
    """Test ATTOM API connectivity."""
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

def test_rentcast_api_connectivity():
    """Test Rentcast API connectivity."""
    # Check if we have a .env file
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        print(f"WARNING: No .env file found at {env_path}")
        print("You should create a .env file with your Rentcast API key")
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("RENTCAST_API_KEY")
    
    if not api_key:
        print("ERROR: RENTCAST_API_KEY not found in environment variables.")
        print("Please add your API key to the .env file:")
        print("RENTCAST_API_KEY=your_api_key_here")
        return 1
    
    print("=" * 80)
    print("TESTING RENTCAST API CONNECTIVITY")
    print("=" * 80)
    
    # Run the API test
    test_rentcast_api(api_key)
    
    return 0

def test_attom_property_details():
    """Test the ATTOM property details function with a known address."""
    test_address = "4529 Winona Court, Denver, CO"
    
    print("=" * 80)
    print(f"TESTING ATTOM PROPERTY DETAILS FOR: {test_address}")
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

def test_rentcast_property_details():
    """Test the Rentcast property details function with a known address."""
    test_address = "5500 Grand Lake Dr, San Antonio, TX 78244"
    
    print("=" * 80)
    print(f"TESTING RENTCAST PROPERTY DETAILS FOR: {test_address}")
    print("=" * 80)
    
    try:
        # Create input object
        input_data = PropertyDetailsInput(address=test_address)
        
        # Get property details
        result = get_property_details_rentcast(input_data)
        
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
        
def test_realty_property_details():
    """Test the Realty in US property details function with a known address."""
    test_address = "5500 Grand Lake Dr, San Antonio, TX 78244"
    
    print("=" * 80)
    print(f"TESTING REALTY IN US PROPERTY DETAILS FOR: {test_address}")
    print("=" * 80)
    
    # Check if RAPIDAPI_KEY is available
    load_dotenv()
    api_key = os.environ.get("RAPIDAPI_KEY", "")
    if not api_key:
        print("WARNING: RAPIDAPI_KEY not found in environment variables!")
        return 1
    else:
        print(f"API Key found: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    
    try:
        # Test the property_details_realty tool directly
        result = property_details_realty(test_address)
        
        # Print a sample of the results
        print("\nProperty Details Results (first 500 chars):")
        print(result[:500] + "..." if len(result) > 500 else result)
        
        print("\nTest successful!")
        return 0
    
    except Exception as e:
        print(f"ERROR: Test failed with exception: {str(e)}")
        return 1

def test_property_valuation():
    """Test the property valuation function with a known address."""
    test_address = "5500 Grand Lake Dr, San Antonio, TX 78244"
    test_property_type = "Single Family"
    test_bedrooms = 3
    test_bathrooms = 2
    test_sqft = 1878
    
    print("=" * 80)
    print(f"TESTING PROPERTY VALUATION FOR: {test_address}")
    print(f"Property Type: {test_property_type}")
    print(f"Bedrooms: {test_bedrooms}")
    print(f"Bathrooms: {test_bathrooms}")
    print(f"Square Footage: {test_sqft}")
    print("=" * 80)
    
    # Make sure the RENTCAST_API_KEY is available
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("RENTCAST_API_KEY", "")
    if not api_key:
        print("WARNING: RENTCAST_API_KEY not found in environment variables!")
    else:
        print(f"API Key found: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    
    try:
        # First test the detailed implementation
        print("\nTesting get_property_valuation:")
        
        # Create input object with additional parameters
        input_data = PropertyValuationInput(
            address=test_address,
            property_type=test_property_type,
            bedrooms=test_bedrooms,
            bathrooms=test_bathrooms,
            square_footage=test_sqft
        )
        
        # Get property valuation
        result = get_property_valuation(input_data)
        
        # Print results
        print("\nValuation Results:")
        print(f"Address: {result.address}")
        print(f"Estimated Value: ${result.estimated_value:,}")
        print(f"Value Range: ${result.value_range_low:,} to ${result.value_range_high:,}")
        print(f"Found {len(result.comparables)} comparable properties")
        
        if result.comparables:
            print("\nSample Comparable Property:")
            comp = result.comparables[0]
            print(f"Address: {comp.address}")
            print(f"Price: ${comp.price:,}")
            print(f"Details: {comp.bedrooms} bed, {comp.bathrooms} bath, {comp.square_footage} sq ft")
            print(f"Year Built: {comp.year_built}")
            print(f"Distance: {comp.distance} miles")
        
        # Now test the tool implementation
        print("\nTesting property_valuation tool:")
        valuation_text = property_valuation(
            address=test_address,
            property_type=test_property_type,
            bedrooms=test_bedrooms,
            bathrooms=test_bathrooms,
            square_footage=test_sqft
        )
        print("\nValuation Report Summary (first 500 chars):")
        print(valuation_text[:500] + "..." if len(valuation_text) > 500 else valuation_text)
        
        print("\nTest successful!")
        return 0
    
    except Exception as e:
        print(f"ERROR: Test failed with exception: {str(e)}")
        return 1

def main():
    """Run tests for all property APIs."""
    # Test ATTOM API connectivity
    attom_connectivity_result = test_attom_api_connectivity()
    
    print("\n")
    
    # Test Rentcast API connectivity
    rentcast_connectivity_result = test_rentcast_api_connectivity()
    
    print("\n")
    
    # Test ATTOM property details
    attom_details_result = test_attom_property_details()
    
    print("\n")
    
    # Test Rentcast property details
    rentcast_details_result = test_rentcast_property_details()
    
    print("\n")
    
    # Test Realty in US property details
    realty_details_result = test_realty_property_details()
    
    print("\n")
    
    # Test property valuation tool
    valuation_result = test_property_valuation()
    
    print("\nTests complete. If you see any errors above, check your API keys and connectivity.")
    
    return (attom_connectivity_result or 
            rentcast_connectivity_result or 
            attom_details_result or 
            rentcast_details_result or 
            realty_details_result or
            valuation_result)

if __name__ == "__main__":
    sys.exit(main())
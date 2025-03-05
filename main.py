"""
Entry point script for the Real Estate Agent.

This file serves as a simple entry point to the application. It imports and runs the main function
from app.py. This pattern is common in Python applications as it allows the application to be run
using either 'python main.py' or 'python app.py' depending on user preference.

Having this separate entry point can be useful for:
1. Package installations where the main module may be different from the entry point
2. Future compatibility with web frameworks (like Flask) that expect a specific entry point
3. Keeping a consistent entry point while the implementation details in app.py might change

For the interactive Real Estate Agent experience, this simply runs the main function from app.py.
"""

from app import main

if __name__ == "__main__":
    # Simply call the main function from app.py
    main()
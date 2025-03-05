# Real Estate Agent AI Assistant

A LangGraph-powered AI agent that helps independent home buyers with property evaluation, neighborhood information, and more.

## Project Overview

This project creates an AI assistant specifically designed to help independent home buyers navigate the real estate market. The agent can:

- Provide detailed property information based on an address
- Provide neighborhood information including schools, crime rates, and amenities
- Guide users through the home buying process

## Project Structure

- `app.py`: Command-line interface for running the agent
- `main.py`: Simple entry point that calls app.py
- `agent.py`: LangGraph agent implementation with tool calling capabilities
- `tools.py`: Tool implementations for property details and neighborhood information

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Create a `.env` file with your API keys:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ATTOM_API_KEY=your_attom_api_key_here
```

## Usage

Run the agent with:

```bash
python app.py
```

Example interactions:
- Start by greeting the agent - it will ask for an address
- Provide an address like "123 Main Street, Anytown, CA 90210"
- Ask for more information about the neighborhood
- Ask specific questions about the property or area

## API Integration

This project uses the ATTOM Property API to provide real property data. The integration includes:

1. **Property Detail**: Retrieves comprehensive property information using the address
2. **School Information**: Gets nearby schools and their details using the property ID
3. **Point of Interest**: Finds nearby amenities using property coordinates

The agent correctly formats API requests to ensure it gets the most accurate property data.

## Features

- **Property Details Tool**: Provides comprehensive information about a property including:
  - Bedrooms, bathrooms, square footage
  - Year built and lot size
  - Property type and estimated value
  - Last sold date and price
  - Property photos (when available from API)

- **Neighborhood Information Tool**: Provides data about the surrounding area:
  - School ratings and information
  - Crime index (when available)
  - Nearby amenities and points of interest

## Development Roadmap

- [x] Initial agent setup with LangGraph
- [x] CoreLogic API integration for property details
- [x] CoreLogic API integration for neighborhood information
- [ ] Add mortgage calculator functionality
- [ ] Create a web interface for easier interaction
- [ ] Add more detailed property search capabilities
- [ ] Implement home inspection checklist and guidance

## License

MIT License
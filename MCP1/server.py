#!/usr/bin/env python3
"""
Simple MCP Server with FastMCP
Provides one tool: weather lookup.
"""

import os
import requests
from typing import Any, Literal
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

# Create FastMCP server instance
mcp = FastMCP("Simple MCP Server-US Weather Service")

# Constants - National Weather Service API (US only)
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

## Helper functions
def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json()
    else:
        return None

##########################################################################

## T O O L S

##########################################################################

"""
Essential part of MCP servers are tools.
Tools are the actions that your MCP server can perform.
Tools are the core building blocks that allow your LLM to 
interact with external systems, execute code, and 
access data that isn’t in its training data. 
"""
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a US location. Only supports US coordinates.

    Args:
        latitude: Latitude of the US location (e.g. 40.7128 for NYC)
        longitude: Longitude of the US location (e.g. -74.0060 for NYC)
        
    Note: This tool only works for coordinates within the United States 
    as it uses the National Weather Service API.
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:10]:  # Only show next 10 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def get_current_weather(latitude: float, longitude: float) -> str:
    """Get current weather conditions for a US location. Only supports US coordinates.

    Args:
        latitude: Latitude of the US location (e.g. 40.7128 for NYC)  
        longitude: Longitude of the US location (e.g. -74.0060 for NYC)
        
    Note: This tool only works for coordinates within the United States
    as it uses the National Weather Service API.
    """
    # Get the current conditions from the nearest station
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch weather data for this location."

    # Get observation stations
    stations_url = points_data["properties"]["observationStations"]
    stations_data = make_nws_request(stations_url)

    if not stations_data or not stations_data.get("features"):
        return "Unable to find nearby weather stations."

    # Get observations from the first available station
    station_id = stations_data["features"][0]["properties"]["stationIdentifier"]
    observations_url = f"{NWS_API_BASE}/stations/{station_id}/observations/latest"
    
    observation_data = make_nws_request(observations_url)
    
    if not observation_data:
        return "Unable to fetch current observations."

    props = observation_data["properties"]
    
    # Format temperature
    temp_c = props.get("temperature", {}).get("value")
    temp_f = None
    if temp_c:
        temp_f = (temp_c * 9/5) + 32

    # Format other data
    humidity = props.get("relativeHumidity", {}).get("value")
    wind_speed = props.get("windSpeed", {}).get("value")
    wind_direction = props.get("windDirection", {}).get("value")
    description = props.get("textDescription", "No description available")

    result = f"""
Current Weather Conditions:
Description: {description}
Temperature: {temp_c:.1f}°C ({temp_f:.1f}°F)
Humidity: {humidity}%
Wind Speed: {wind_speed} m/s
Wind Direction: {wind_direction}°
"""
    
    return result.strip()

# Excercise 1
# Create a tool that returns the current user's information

# @mcp.tool()
# async def get_current_users_info() -> str:
#     """Get current user's information
#     Args:
#         None
#     Returns:
#         A string containing the current user's name and email
#     """
#     ## add your user_name and user_email below
#     
#     
#     return f"""Current user's name is {user_name} and email is {user_email}"""


##########################################################################

## R E S O U R C ES

##########################################################################
'''
Resources vs tools
MCP resources are read-only and addressable via URIs like note://xyz or stock://AAPL/earnings. 
They are designed to preload context into the agent’s working memory or support 
summarization and analysis workflows.

MCP tools are actionable and invoked by the client with parameters to 
perform an action like writing a file, placing an order, or creating a task.

To avoid decision paralysis, define resources according to what the client 
should know and tools according to what the client can do.
'''

# Add resources
@mcp.resource("weather://reference/conversions")
def unit_conversions():
    """Unit conversion formulas for weather data"""
    CONVERSIONS = {
        "temperature": {
            "nws_unit": "celsius",
            "display_units": ["celsius", "fahrenheit"],
            "formulas": {
                "c_to_f": "(°C × 9/5) + 32",
                "f_to_c": "(°F - 32) × 5/9"
            }
        },
        "wind": {
            "nws_unit": "meters_per_second", 
            "display_units": ["ms", "mph", "kmh"],
            "formulas": {
                "ms_to_mph": "m/s × 2.237",
                "ms_to_kmh": "m/s × 3.6"
            }
        }
    }
    return CONVERSIONS

@mcp.resource("weather://reference/coverage")  
def api_coverage():
    """NWS API coverage information"""
    return {
        "geographic_coverage": "United States only",
        "territories_included": ["Puerto Rico", "US Virgin Islands", "Guam"],
        "coordinate_system": "WGS84 (latitude/longitude)",
        "data_sources": "National Weather Service observation stations"
    }

##########################################################################

## P R O M P T S

##########################################################################
'''
Prompts vs tools
Prompts are a way to instruct the agent (e.g. Claude) on how to behave. 
They are not actionable and are not invoked by the client.

Tools: Actually fetch data (get_current_weather, get_forecast)
Prompts: Guide how to use tools effectively and what questions to ask

Why These Prompts Are Useful

Bridge the Gap: Your tools need coordinates, but users think in location names
Workflow Guidance: Shows the proper sequence (location → coordinates → weather data)
Complete Solutions: Combines both your tools for comprehensive reports
User-Friendly: Handles the technical details so users get what they actually want
Example:
"weather-by-location"
Users want to ask "What's the weather in Chicago?" not "What's the weather at 41.8781, -87.6298?"
This prompt teaches the client (Claude) to:
- Convert location names to coordinates
- Use your tools correctly
- Present results in a user-friendly way
'''

#
@mcp.prompt("weather-by-location")
def weather_by_location_prompt(location: str, report_type: str = "current"):
    """Get weather for a location by converting it to coordinates first"""
    
    return f"""I need weather information for {location}.

Since the weather tools require latitude and longitude coordinates, please:

1. First determine the coordinates for {location}
   - Look up the latitude and longitude for this location
   - For cities, use the city center coordinates
   - For addresses, convert to precise coordinates

2. Then get the weather data:
   {"- Use get_current_weather(latitude, longitude) for current conditions" if report_type in ["current", "both"] else ""}
   {"- Use get_forecast(latitude, longitude) for the forecast" if report_type in ["forecast", "both"] else ""}

3. Present the results clearly:
   - Show the location name and coordinates used
   - Display weather information in user-friendly format
   - Convert units to local preferences (Fahrenheit for US locations)

Example coordinates for reference:
- New York City: 40.7128, -74.0060
- Los Angeles: 34.0522, -118.2437
- Chicago: 41.8781, -87.6298"""



##########################################################################

### S A M P L I N G

##########################################################################
'''
MCP Sampling is a feature that allows MCP servers to make requests back to the LLM 
through the MCP client. It's essentially "reverse communication" - instead of 
just the client calling server tools, the server can ask the LLM to help with tasks.
Sampling lets your MCP server:
- Ask the LLM to generate text, analyze data, or make decisions
- Get help with complex processing that's better suited for an LLM
- Leverage the LLM's knowledge and reasoning capabilities
- Create more intelligent, context-aware tools

'''

@mcp.tool()
async def sampling_analyze_weather_trends(ctx: Context, latitude: float, longitude: float, days: int = 7)-> str:
    """Analyze weather patterns and provide insights
    Requires sampling enabled on the MCP client. Demo function only.
    Set MCP Inspector Configuration Timeouts to 60000 ms.
    Sample response from the client's LLM might look like this:
    ```
    The weather is expected to improve over the next few days, with temperatures rising to around 70°F by the end of the week. There is a slight chance of precipitation on Thursday, but the overall outlook is dry and sunny. The best days for outdoor activities are Tuesday and Friday, when the weather will be clear and warm. The worst days are Monday and Saturday, when there may be some cloud cover and a slight chance of rain.
    ```
    Args:
        latitude: Latitude of the US location (e.g. 40.7128 for NYC)
        longitude: Longitude of the US location (e.g. -74.0060 for NYC)
        days: Number of days to analyze (default is 7)
    """
    
    # Get extended forecast data
    #forecast_data = await fetch_nws_extended_forecast(latitude, longitude, days)
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = make_nws_request(forecast_url)
    
    prompt = f"""Analyze this {days}-day weather forecast and identify key patterns:

{str(forecast_data)}

Provide analysis on:
1. Overall weather trend (improving, deteriorating, stable)
2. Temperature patterns and any unusual changes
3. Precipitation likelihood and timing
4. Best days for outdoor activities
5. Days to avoid for travel or outdoor events
6. Any notable weather systems approaching

Focus on actionable insights for planning."""
    
    response = await ctx.sample(
        messages=[{
            "role": "user", 
            "content": {
                "type": "text",
                "text": prompt
            }
        }],
        max_tokens=400,
        temperature=0.2
    )
    
    return response.text

##########################################################################

## E L I C I T A T I O N

##########################################################################
'''
MCP Elicitations is a "human-in-the-loop" feature that allows your MCP server tools to 
pause execution and ask the user for additional information before continuing. 
It's like your tool saying "I need more info from you to proceed."
Servers request structured data from users with JSON schemas to validate responses.
'''
## JSON SCHEMA
'''
JSON schemas are a way to define the structure of the data that your MCP server tools will receive.
They are used to validate the data that the user provides.
'''
class TravelWeatherPreferences(BaseModel):
    """Schema for travel weather planning"""
    departure_date: str = Field(description="Departure date (YYYY-MM-DD)")
    return_date: str = Field(description="Return date (YYYY-MM-DD)")
    activity_type: str = Field(
        default="general",
        description="Type of activities planned (outdoor, business, vacation, etc.)"
    )
    weather_sensitivity: str = Field(
        default="moderate",
        description="Weather sensitivity (low, moderate, high)"
    )
@mcp.tool()
async def elicitation_plan_travel_weather(ctx: Context, departure_city: str, destination_city: str) -> str:
    """
    Plan travel with detailed weather considerations.
    Requires elicitation enabled on the MCP client. Demo function only.
    Set MCP Inspector Configuration Timeouts to 60000 ms.
    Args:
        departure_city: Departure city (e.g. New York)
        destination_city: Destination city (e.g. Los Angeles)
    """
    
    # Get travel preferences from user
    result = await ctx.elicit(
        f"Help me plan weather considerations for your trip from {departure_city} to {destination_city}",
        response_type=TravelWeatherPreferences
    )
    
    if result.action != "accept":
        return "Travel planning cancelled"
    
    prefs = result.data
    
    # Get weather data for both cities and date range
    # Your weather API calls here...
    
    return f"""Travel weather plan:
Route: {departure_city} → {destination_city}
Dates: {prefs.departure_date} to {prefs.return_date}
Activity focus: {prefs.activity_type}
Weather sensitivity: {prefs.weather_sensitivity}
[Weather analysis would go here...]"""

##########################################################################

## R O O T S

##########################################################################
''' 
MCP roots are context-defining URIs (Uniform Resource Identifiers) that establish operational boundaries for MCP servers. 
They function as “safe zones” or “allowed directories” that an AI agent can access when interacting with your system. 
When an MCP client provides roots for servers, it’s essentially saying, “You’re allowed to work within these specific areas.”
Roots vs tools
MCP roots define where operations can occur, MCP tools define what actions can be performed.
Examples:
Folders on your computer: file:///home/user/projects/myapp
Websites and APIs: https://api.example.com/v1
Database connections: db://mycompany/customers
'''
@mcp.tool()
async def roots_get_project_roots(ctx: Context) -> str:
    """
    Get the project roots from the client
    Requires roots enabled on the MCP client. Demo function only.
    Set roots in the MCP Inspector e.g. "file:///home/user/projects/myapp"
    Args:
        ctx: The context object
    Returns:
        A string containing the project roots
    """
    roots = await ctx.session.list_roots() 
    
    if not roots or not roots.roots:
        return "No project roots found"
    
    return "Project roots: " + str(roots)


##########################################################################

## R U N N I N G    T H E    S E R V E R

##########################################################################

if __name__ == "__main__":
    # Run the MCP server with HTTP transport (Streamable HTTP)
    mcp.run(
        transport="http", # HTTP or STDIO 
        host="0.0.0.0",  # Bind to all interfaces for external access (any IP is allowed to access the server), 127.0.0.1 allows only local access
        port=8000,       # HTTP port
        log_level="INFO" # Set logging level
    ) 
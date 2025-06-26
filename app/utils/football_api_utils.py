"""
Football API utility functions for making API calls and handling responses.
"""

from getpass import getpass
import os
import requests
import logging
from urllib.parse import urljoin
from typing import Literal, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import unicodedata

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(find_dotenv())
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY')
if not FOOTBALL_API_KEY:
    getpass("Enter API key for Football API: ")
FOOTBALL_API_BASE_URL = "https://v3.football.api-sports.io/"
FOOTBALL_API_HOST = "v3.football.api-sports.io"


class Response(BaseModel):
    """Base response class with validation."""
    pass


class ValidResponse(Response):
    """Valid response with data."""
    data: Any


class ErrorResponse(Response):
    """Error response with error message."""
    error: str
    status_code: Optional[int] = None


def check_api_response_status(response: requests.Response) -> dict:
    """
    Generic status check for API responses.
    
    Args:
        response: The requests.Response object from an API call
        
    Returns:
        Dictionary with success status and error information if applicable
    """
    if response.status_code == 200:
        try:
            data = response.json()
            return {"success": True, "data": data}
        except requests.exceptions.JSONDecodeError:
            return {
                "success": False, 
                "error": "Invalid JSON response",
                "status_code": response.status_code
            }
    elif response.status_code == 204:
        return {
            "success": False,
            "error": "No content available",
            "status_code": response.status_code
        }
    elif response.status_code == 499:
        return {
            "success": False,
            "error": "Request timeout",
            "status_code": response.status_code
        }
    elif response.status_code == 500:
        return {
            "success": False,
            "error": "Internal server error",
            "status_code": response.status_code
        }
    else:
        return {
            "success": False,
            "error": f"HTTP {response.status_code}: {response.reason}",
            "status_code": response.status_code
        }


def call_football_api(method: Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"], endpoint: str, data={}, params=None) -> Response:
    """
    Call the Football API with the given endpoint and parameters.
    Now includes proper status code checking and returns Response objects.
    
    Args:
        method: HTTP method to use
        endpoint: API endpoint to call
        data: Data to send in the request body
        params: Query parameters
        
    Returns:
        ValidResponse with data or ErrorResponse with error information
    """
    url = urljoin(FOOTBALL_API_BASE_URL, endpoint)
    headers = {
        'x-rapidapi-key': FOOTBALL_API_KEY,
        'x-rapidapi-host': FOOTBALL_API_HOST
    }
    
    # Normalize param values - replace accented characters with ASCII equivalents
    if params:
        normalized_params = {}
        for k, v in params.items():
            # Convert to string and normalize to ASCII
            normalized_value = unicodedata.normalize('NFD', str(v))
            normalized_value = ''.join(c for c in normalized_value if unicodedata.category(c) != 'Mn')
            normalized_params[k] = normalized_value
        params = normalized_params
    
    try:
        response = requests.request(method, url, headers=headers, data=data, params=params)
        result = check_api_response_status(response)
        
        if result["success"]:
            return ValidResponse(data=result["data"])
        else:
            logger.error(f"API call failed: {result['error']}")
            return ErrorResponse(
                error=result["error"], 
                status_code=result.get("status_code")
            )
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return ErrorResponse(error=f"Request failed: {str(e)}")

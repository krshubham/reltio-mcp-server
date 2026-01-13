import logging
from typing import List, Dict, Any
import yaml
from constants import ACTIVITY_CLIENT
from env import RELTIO_TENANT
from util.api import get_reltio_url, http_request, create_error_response, validate_connection_security
from util.auth import get_reltio_headers
from util.models import EntityInteractionsRequest, CreateInteractionRequest
from util.activity_log import ActivityLog
from tools.util import ActivityLogLabel, simplify_reltio_attributes

# Configure logging
logger = logging.getLogger("mcp.server.reltio")


async def get_entity_interactions(entity_id: str, max: int = 50, offset: int = 0, 
                                  order: str = "asc", sort: str = "", filter: str = "",
                                  tenant_id: str = RELTIO_TENANT) -> dict:
    """Get interactions for a Reltio entity by ID
    
    Args:
        entity_id (str): The ID of the entity to get interactions for
        max (int): Maximum number of interactions to return (default: 50)
        offset (int): Starting index for paginated results (default: 0)
        order (str): Sort order - 'asc' or 'desc' (default: 'asc')
        sort (str): Field to sort by (default: empty - sorts by timestamp)
        filter (str): Filter condition for interactions (default: empty)
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the interactions, totalFetched, and fetchedAll information
    
    Raises:
        Exception: If there's an error getting the entity interactions
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = EntityInteractionsRequest(
                entity_id=entity_id,
                max=max,
                offset=offset,
                order=order,
                sort=sort,
                filter=filter,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_entity_interactions: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        # Construct URL with validated entity ID
        url = get_reltio_url(f"entities/{request.entity_id}/_interactions", "api", request.tenant_id)
        
        try:
            headers = get_reltio_headers()
            
            # Validate connection security
            validate_connection_security(url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Prepare query parameters
        params = {
            "max": request.max,
            "offset": request.offset,
            "order": request.order
        }
        
        # Add optional parameters if provided
        if request.sort:
            params["sort"] = request.sort
        
        if request.filter:
            params["filter"] = request.filter
        
        # Make the request with timeout
        try:
            interactions = http_request(url, headers=headers, params=params)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check if it's a 404 error (entity not found)
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Entity with ID {request.entity_id} not found or no interactions available"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to retrieve entity interactions from Reltio API"
            )
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.USER_SEARCH.value,
                client_type=ACTIVITY_CLIENT,
                description=f"get_entity_interactions_tool : Successfully fetched interactions for entity {entity_id}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_entity_interactions: {str(log_error)}")
        
        # Process the interactions response
        if "interactions" in interactions:
            for interaction in interactions["interactions"]:
                if "attributes" in interaction:
                    interaction["attributes"] = simplify_reltio_attributes(interaction["attributes"])
        
        return yaml.dump(interactions, sort_keys=False)
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in get_entity_interactions: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while retrieving entity interactions"
        )


async def create_interactions(interactions: list, source_system: str = "configuration/sources/Reltio",
                              crosswalk_value: str = "", return_objects: bool = True, options: str = "",
                              tenant_id: str = RELTIO_TENANT) -> dict:
    """Create interactions in the Reltio Platform
    
    Args:
        interactions (list): List of interaction objects to create. Each must have a 'type' field.
        source_system (str): Source system for the interactions (default: 'configuration/sources/Reltio')
        crosswalk_value (str): Optional identifier of an interaction object in the source system
        return_objects (bool): Whether the response must include the created objects (default: True)
        options (str): Optional options for the request (e.g., 'sendHidden')
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the creation results for each interaction
    
    Raises:
        Exception: If there's an error creating the interactions
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = CreateInteractionRequest(
                interactions=interactions,
                source_system=source_system,
                crosswalk_value=crosswalk_value,
                return_objects=return_objects,
                options=options,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in create_interactions: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        # Construct URL
        url = get_reltio_url("interactions", "api", request.tenant_id)
        
        try:
            headers = get_reltio_headers()
            headers["Source-System"] = request.source_system
            # Add required headers for interaction creation
            headers["Content-Type"] = "application/json"
            headers["Globalid"] = ACTIVITY_CLIENT
            # Validate connection security
            validate_connection_security(url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Prepare query parameters
        params = {
            "returnObjects": str(request.return_objects).lower()
        }
        
        # Add optional parameters if provided
        if request.crosswalk_value:
            params["crosswalkValue"] = request.crosswalk_value
        
        if request.options:
            params["options"] = request.options
        
        # Make the POST request with timeout
        try:
            response = http_request(url, method="POST", headers=headers, params=params, data=request.interactions)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check for specific error responses
            error_message = str(e).lower()
            if "400" in error_message:
                return create_error_response(
                    "BAD_REQUEST",
                    "Invalid interaction data provided. Check that all required fields are present and valid."
                )
            elif "409" in error_message or "536" in error_message:
                return create_error_response(
                    "CONFLICT",
                    "Duplicate interaction ID or existing crosswalk. Interactions must have unique IDs and crosswalks."
                )
            elif "404" in error_message:
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    "One or more referenced entities or configuration elements not found"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to create interactions via Reltio API"
            )
        
        
        # Process the response to check for success/failure/warnings
        if isinstance(response, list):
            # Count successful, failed, and warning results
            success_count = sum(1 for result in response if result.get("status") == "OK")
            error_count = sum(1 for result in response if "error" in result or "errors" in result)
            warning_count = sum(1 for result in response if "warning" in result)
            
            logger.info(f"Interaction creation results: {success_count} successful, {error_count} failed, {warning_count} warnings")
        
        return yaml.dump(response, sort_keys=False)
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in create_interactions: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while creating interactions"
        )


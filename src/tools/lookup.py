import logging
import yaml
from constants import ACTIVITY_CLIENT
from env import RELTIO_TENANT
from util.api import (
    get_reltio_url,
    http_request,
    create_error_response,
    validate_connection_security
)
from util.auth import get_reltio_headers
from util.models import LookupListRequest
from util.activity_log import ActivityLog
from tools.util import ActivityLogLabel

# Configure logging
logger = logging.getLogger("mcp.server.reltio")


async def rdm_lookups_list(lookup_type: str, tenant_id: str = RELTIO_TENANT, max_results: int = 10,
                           display_name_prefix: str = "") -> dict:
    """List lookups by RDM lookup type
    
    Args:
        lookup_type (str): RDM lookup type (e.g., 'rdm/lookupTypes/VistaVegetarianOrVegan')
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
        max_results (int): Maximum number of results to return. Defaults to 10.
        display_name_prefix (str): Display name prefix to filter by. Defaults to "".
    
    Returns:
        A dictionary containing the lookups list
    
    Raises:
        Exception: If there's an error getting the lookups
    """
    try:
        # Validate and sanitize inputs using Pydantic model
        try:
            lookup_request = LookupListRequest(
                lookup_type=lookup_type,
                tenant_id=tenant_id,
                max_results=max_results,
                display_name_prefix=display_name_prefix
            )
        except ValueError as e:
            logger.warning(f"Validation error in rdm_lookups_list: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        # Construct URL for lookups list endpoint
        url = get_reltio_url("lookups/list", "api", lookup_request.tenant_id)
        
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
        
        # Build the payload
        payload = {
            "type": lookup_request.lookup_type if lookup_request.lookup_type != "all" else "",
            "max": lookup_request.max_results,
            "displayNamePrefix": lookup_request.display_name_prefix
        }
        
        # Make the request with timeout
        try:
            result = http_request(url, method='POST', headers=headers, data=payload)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "SERVER_ERROR",
                "Failed to retrieve lookups from Reltio API"
            )
        
        try:
            # Count the number of lookups returned
            lookup_count = len(result) if isinstance(result, list) else 0
            lookup_summary = f"{lookup_count} lookups found" if lookup_count > 0 else "no lookups found"
            
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.LOOKUP_LIST.value,
                client_type=ACTIVITY_CLIENT,
                description=f"rdm_lookups_list_tool : Successfully retrieved lookups: {lookup_summary} for lookup_type {lookup_type}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for rdm_lookups_list: {str(log_error)}")
        
        # Return the lookups in YAML format for better readability
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in rdm_lookups_list: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while processing your request"
        )


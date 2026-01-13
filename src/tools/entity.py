import logging
from typing import List, Dict, Any, Optional
import yaml
import json
import re
from constants import ACTIVITY_CLIENT, MAX_RESULTS_LIMIT
from env import RELTIO_TENANT
from util.api import get_reltio_url, get_reltio_export_job_url, http_request, create_error_response, validate_connection_security
from util.auth import get_reltio_headers
from util.exceptions import SecurityError
from util.models import (
    EntityIdRequest, UpdateEntityAttributesRequest, MergeEntitiesRequest, 
    RejectMatchRequest, UnmergeEntityRequest, EntityWithMatchesRequest,
    CreateEntitiesRequest, GetEntityParentsRequest
)
from util.activity_log import ActivityLog
from tools.util import ActivityLogLabel, simplify_reltio_attributes, slim_crosswalks, format_entity_matches, format_unified_entity_matches

# Configure logging
logger = logging.getLogger("mcp.server.reltio")
   

def filter_entity(entity: Dict[str, Any], filter_field: Optional[Dict[str, List[str]]]) -> Dict[str, Any]:
    if filter_field is None:
        return entity

    def is_valid(value: Any) -> bool:
        return value is not None and not (isinstance(value, (str, list, dict, set)) and len(value) == 0)

    filtered_entity = {}
    for field, subfields in filter_field.items():
        if field not in entity:
            continue
        value = entity[field]
        if not is_valid(value):
            continue

        # Handle subfield filtering for nested fields like "attributes"
        if isinstance(value, dict) and subfields:
            subvalue = {
                k: v for k, v in value.items()
                if k in subfields and is_valid(v)
            }
            if subvalue:
                filtered_entity[field] = subvalue
        elif isinstance(value, dict) and not subfields:
            # Include whole dict if subfields list is empty
            filtered_subdict = {k: v for k, v in value.items() if is_valid(v)}
            if filtered_subdict:
                filtered_entity[field] = filtered_subdict
        else:
            # For non-dict values (e.g., lists, strings, booleans)
            filtered_entity[field] = value
    return filtered_entity

async def get_entity_details(entity_id: str, filter_field: Dict[str, List[str]] = None, tenant_id: str = RELTIO_TENANT) -> dict:
    """Get detailed information about a Reltio entity by ID
    
    Args:
        entity_id (str): The ID of the entity to retrieve
        filter_field (Dict[str, List[str]]): Optional dictionary to filter specific fields in the entity response
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the entity details
    
    Raises:
        Exception: If there's an error getting the entity details
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = EntityIdRequest(
                entity_id=entity_id,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_entity_details: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid entity ID format: {str(e)}"
            )
        
        # Construct URL with validated entity ID
        url = get_reltio_url(f"entities/{request.entity_id}", "api", request.tenant_id)
        
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
        
        # Make the request with timeout
        try:
            entity = http_request(url, headers=headers)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check if it's a 404 error (entity not found)
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Entity with ID {request.entity_id} not found"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to retrieve entity details from Reltio API"
            )
        
        # Try to log activity for success
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.USER_PROFILE_VIEW.value,
                client_type=ACTIVITY_CLIENT,
                description=json.dumps({"uri":f"entities/{entity_id.split('/')[-1]}","label":entity.get("label","")}),
                items=[{"objectUri":f"entities/{entity_id.split('/')[-1]}"}]
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_entity_details: {str(log_error)}")
        
        filter_entity_data=filter_entity(entity, filter_field) if filter_field else entity
        result={"attributes":simplify_reltio_attributes(filter_entity_data.get("attributes",{}))}
        if "crosswalks" in filter_entity_data:
            result["crosswalks"]=slim_crosswalks(filter_entity_data["crosswalks"])

        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in get_entity_details: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while retrieving entity details"
        )

async def update_entity_attributes(entity_id: str, updates: List[Dict[str, Any]],options:str = "",always_create_dcr:bool = False,change_request_id:str = None, overwrite_default_crosswalk_value:bool = True,tenant_id: str = RELTIO_TENANT) -> dict:
    """Update specific attributes of an entity in Reltio
    
    Args:
        entity_id (str): Entity ID to update
        updates (List[Dict[str, Any]]): List of update operations as per Reltio API spec
        options (str): Optional comma-separated list of options. Available options:
            - sendHidden: Include hidden attributes in the response
            - updateAttributeUpdateDates: Update the updateDate and singleAttributeUpdateDates timestamps
            - addRefAttrUriToCrosswalk: Add reference attribute URIs to crosswalks during updates
            Example: options="sendHidden,updateAttributeUpdateDates"
        always_create_dcr (bool): If true, creates a DCR without updating the entity.(TO BE USED MOST OF THE TIME, SKIP IF Changes Seem minimal)
        change_request_id (str): If provided, all changes will be added to the DCR with this ID instead of updating the entity directly.
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the API response
    
    Raises:
        Exception: If there's an error during the update
    """
    try:
        # Validate request
        try:
            request = UpdateEntityAttributesRequest(
                entity_id=entity_id,
                updates=updates,
                options=options,
                tenant_id=tenant_id,
                always_create_dcr=always_create_dcr,
                change_request_id=change_request_id,
                overwrite_default_crosswalk_value=overwrite_default_crosswalk_value
            )
        except ValueError as e:
            logger.warning(f"Validation error in update_entity_attributes: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid request format: {str(e)}"
            )

        url = get_reltio_url(f"entities/{request.entity_id}/_update", "api", request.tenant_id)
        params={}
        if options and options.strip():
            params["options"] = options
        if request.always_create_dcr:
            params["alwaysCreateDCR"] = request.always_create_dcr
        if request.change_request_id:
            params["changeRequestId"] = request.change_request_id
        if request.overwrite_default_crosswalk_value:
            params["overwriteDefaultCrosswalkValue"] = request.overwrite_default_crosswalk_value
        try:
            headers = get_reltio_headers()
            headers["Content-Type"] = "application/json"
            headers["Globalid"] = ACTIVITY_CLIENT
            validate_connection_security(url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate or security requirements not met"
            )

        try:
            result = http_request(url, method="POST", headers=headers, data=request.updates,params=params if params else None)
        except Exception as e:
            logger.error(f"API request error in update_entity_attributes: {str(e)}")
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Entity with ID {request.entity_id} not found"
                )
            return create_error_response(
                "SERVER_ERROR",
                f"Failed to update entity attributes in Reltio API- {str(e)}"
            )  

        

        return yaml.dump(result, sort_keys=False)
    except Exception as e:
        logger.error(f"Unexpected error in update_entity_attributes: {str(e)}")
        return create_error_response(
            "SERVER_ERROR",
            f"An unexpected error occurred while updating entity attributes- {str(e)}"
        )

async def get_entity_matches(entity_id: str, tenant_id: str = RELTIO_TENANT, max_results: int = 25) -> dict:
    """Find potential matches for a specific entity with detailed comparisons
    
    Args:
        entity_id (str): Entity ID to find matches for
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
        max_results (int): Maximum number of results to return. Default to 25
    
    Returns:
        A dictionary containing the source entity and potential matches
    
    Raises:
        Exception: If there's an error getting the potential matches for an entity
    """   
    try:
        # Validate inputs using Pydantic model
        try:
            request = EntityIdRequest(
                entity_id=entity_id,
                tenant_id=tenant_id
            )
            
            # Validate max_results
            if max_results < 1:
                max_results = 1
            elif max_results > MAX_RESULTS_LIMIT:
                max_results = MAX_RESULTS_LIMIT
                logger.info(f"Max results limited to {MAX_RESULTS_LIMIT} for entity matches")
                
        except ValueError as e:
            logger.warning(f"Validation error in get_entity_matches: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid entity ID format: {str(e)}"
            )
        
        try:
            headers = get_reltio_headers()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Use the _transitiveMatches endpoint for a specific entity
        url = get_reltio_url(f"entities/{request.entity_id}/_transitiveMatches", "api", request.tenant_id)
        
        # Validate connection security
        try:
            validate_connection_security(url, headers)
        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        params = {
            "deep": 1,
            "markMatchedValues": "true",
            "sort": "score",
            "order": "desc",
            "activeness": "active",
            "limit": max_results
        }
        
        # Make the request with timeout
        try:
            matches_result = http_request(url, headers=headers, params=params)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check if it's a 404 error (entity not found)
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Entity with ID {request.entity_id} not found"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to retrieve matches from Reltio API"
            )
        
        # Check if we found any matches
        if not matches_result or len(matches_result) == 0:
            return {
                "message": f"No potential matches found for entity {request.entity_id}.",
                "matches": []
            }
        
        # Get the source entity
        source_url = get_reltio_url(f"entities/{request.entity_id}", "api", request.tenant_id)
        
        try:
            source_entity = http_request(source_url, headers=headers)
        except Exception as e:
            logger.error(f"Error retrieving source entity: {str(e)}")
            
            # We still have the matches, so return those with an error message about the source
            return {
                "message": f"Found matches but could not retrieve source entity details: {str(e)}",
                "matches": matches_result
            }
        
        # Combine results
        result = {
            "source_entity": request.entity_id,
            "matches": format_entity_matches(matches_result)
        }
        
        # Try to log activity for success
        try:
            source_entity_label = source_entity.get('label', '') if isinstance(source_entity, dict) else ''
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                description=f"get_entity_matches : Successfully fetched potential matches for entity: {entity_id}, label: {source_entity_label}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_entity_matches: {str(log_error)}")
        
        return yaml.dump(result, sort_keys=False)
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in get_entity_matches: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while retrieving entity matches"
        )

async def get_entity_match_history(entity_id: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Find the match history for a specific entity
    
    Args:
        entity_id (str): Entity ID to find matches for
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the source entity and match history for that entity
    
    Raises:
        Exception: If there's an error getting the match history for an entity
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = EntityIdRequest(
                entity_id=entity_id,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_entity_match_history: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid entity ID format: {str(e)}"
            )
        
        try:
            headers = get_reltio_headers()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Use the _crosswalkTree endpoint for a specific entity
        url = get_reltio_url(f"entities/{request.entity_id}/_crosswalkTree", "api", request.tenant_id)
        
        # Validate connection security
        try:
            validate_connection_security(url, headers)
        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        # Make the request with timeout
        try:
            match_history = http_request(url, headers=headers)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check if it's a 404 error (entity not found)
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Entity with ID {request.entity_id} not found"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to retrieve match history from Reltio API"
            )
        
        # Check if we found any match history
        if not match_history or len(match_history) == 0:
             # Try to log activity for no results
            try:
                await ActivityLog.execute_and_log_activity(
                    tenant_id=tenant_id,
                    label=ActivityLogLabel.USER_PROFILE_VIEW.value,
                    client_type=ACTIVITY_CLIENT,
                    description=json.dumps({"uri":f"entities/{entity_id.split('/')[-1]}","label":""}),
                    items=[{"objectUri":f"entities/{entity_id.split('/')[-1]}"}]
                )
            except Exception as log_error:
                logger.error(f"Activity logging failed for get_entity_match_history (no results): {str(log_error)}")
            
            return {
                "message": f"No match history found for entity {request.entity_id}.",
                "match_history": []
            }
        
        # Get the source entity
        source_url = get_reltio_url(f"entities/{request.entity_id}", "api", request.tenant_id)
        
        try:
            source_entity = http_request(source_url, headers=headers)
        except Exception as e:
            logger.error(f"Error retrieving source entity: {str(e)}")
            
            # We still have the match history, so return those with an error message about the source
            return {
                "message": f"Found match history but could not retrieve source entity details: {str(e)}",
                "match_history": match_history
            }
        
        # Try to log activity for success
        try:
            crosswalk_uris = []
            for cross_walk in match_history.get("crosswalks", []):
                crosswalk_uris.append(cross_walk.get("uri", ""))
            source_entity_label = source_entity.get('label', '') if isinstance(source_entity, dict) else ''
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                description=f"get_entity_match_history_tool : Successfully fetched match history for entity: {entity_id}, label: {source_entity_label}, crosswalk URIs: {crosswalk_uris}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_entity_match_history: {str(log_error)}")

        return yaml.dump(match_history, sort_keys=False)
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in get_entity_match_history: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while retrieving entity match history"
        )

async def merge_entities(entity_ids: List[str], tenant_id: str = RELTIO_TENANT) -> dict:
    """Merge two Reltio entities into one
    
    Args:
        entity_ids (List[str]): List of two entity IDs to merge
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the result of the merge operation
    
    Raises:
        Exception: If there's an error merging the entities
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = MergeEntitiesRequest(
                entity_ids=entity_ids,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in merge_entities: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid entity IDs: {str(e)}"
            )
        
        # Construct URL with validated entity IDs
        url = get_reltio_url(f"entities/_same", "api", request.tenant_id)
        
        try:
            headers = get_reltio_headers()
            headers["Globalid"] = ACTIVITY_CLIENT
            
            # Validate connection security
            validate_connection_security(url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Prepare the payload for merging entities
        payload = request.entity_ids
        
        # Make the POST request
        try:
            merge_result = http_request(
                url, 
                method='POST',
                data=payload,
                headers=headers
            )
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check for common errors
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"One or more entities not found"
                )
            elif "400" in str(e):
                return create_error_response(
                    "INVALID_REQUEST",
                    f"Invalid merge request: {str(e)}"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to merge entities"
            )
        

        return merge_result
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in merge_entities: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while merging entities"
        )

async def reject_entity_match(source_id: str, target_id: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Reject a potential match between two Reltio entities
    
    Args:
        source_id (str): The ID of the source entity
        target_id (str): The ID of the target entity to reject as a match
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the result of the reject operation
    
    Raises:
        Exception: If there's an error rejecting the match
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = RejectMatchRequest(
                source_id=source_id,
                target_id=target_id,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in reject_entity_match: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid entity ID format: {str(e)}"
            )
        
        # Construct URL with validated entity IDs
        base_url = get_reltio_url(f"entities/{request.source_id}/_notMatch", "api", request.tenant_id)
        
        # Add the target entity URI as a query parameter
        params = {
            "uri": f"entities/{request.target_id}"
        }
        
        try:
            headers = get_reltio_headers()
            headers["Globalid"] = ACTIVITY_CLIENT
            # Validate connection security
            validate_connection_security(base_url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Make the POST request with URL parameters
        try:
            reject_result = http_request(
                base_url, 
                method='POST',
                params=params,
                headers=headers
            )
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check for common errors
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"One or more entities not found"
                )
            elif "400" in str(e):
                return create_error_response(
                    "INVALID_REQUEST",
                    f"Invalid reject match request: {str(e)}"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to reject entity match"
            )
        
        # If we reach here, the operation was successful
        # The API might not return any content, so create a meaningful response
        

        if not reject_result:
            return {
                "success": True,
                "message": f"Successfully rejected match between entities {request.source_id} and {request.target_id}"
            }
        
        return reject_result
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in reject_entity_match: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while rejecting entity match"
        )

async def export_merge_tree(email_id: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Export the merge tree for all entities in a specific tenant.

    Args:
        email_id (str): This parameter indicates the valid email address to which the notification is sent after the export is completed.
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the scheduled export job ID and status
    
    Raises:
        Exception: If there's an error exporting the merge tree
    """
    try:
        url = get_reltio_export_job_url(f"entities/_crosswalksTree", tenant_id)

        try:
            headers = get_reltio_headers()
            headers["Content-Type"] = "application/json"
            validate_connection_security(url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate or security requirements not met"
            )

        payload = {
            "outputAsJsonArray": True
        }
        params = {
            "email": email_id
        }
        try:
            result = http_request(url, method="POST", headers=headers, data=payload, params=params)
        except Exception as e:
            logger.error(f"API request error in export_merge_tree: {str(e)}")
            return create_error_response(
                "SERVER_ERROR",
                "Failed to schedule export merge tree job"
            )
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.ENTITY_MERGE_TREE_EXPORT.value,
                client_type=ACTIVITY_CLIENT,
                description=f"export_merge_tree_tool : Successfully scheduled export merge tree job for all entities in tenant {tenant_id}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for export_merge_tree: {str(log_error)}")

        return result
    except Exception as e:
        logger.error(f"Unexpected error in export_merge_tree: {str(e)}")
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while Scheduling the export merge tree job"
        )

async def unmerge_entity_by_contributor(origin_entity_id: str, contributor_entity_id: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Unmerge a contributor entity from a merged entity, keeping any profiles merged beneath it intact.
    
    Args:
        origin_entity_id (str): The ID of the origin entity (the merged entity)
        contributor_entity_id (str): The ID of the contributor entity to unmerge from the origin entity
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the result of the unmerge operation with 'a' (modified origin) and 'b' (spawn) entities
    
    Raises:
        Exception: If there's an error during the unmerge operation
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = UnmergeEntityRequest(
                origin_entity_id=origin_entity_id,
                contributor_entity_id=contributor_entity_id,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in unmerge_entity_by_contributor: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid entity ID format: {str(e)}"
            )
            
        # Construct URL with validated entity IDs
        url = get_reltio_url(f"entities/{request.origin_entity_id}/_unmerge", "api", request.tenant_id)
        
        # Add the contributor entity URI as a query parameter
        params = {
            "contributorURI": f"entities/{request.contributor_entity_id}"
        }
        
        try:
            headers = get_reltio_headers()
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
        
        # Make the POST request with URL parameters
        try:
            unmerge_result = http_request(
                url, 
                method='POST',
                params=params,
                headers=headers
            )
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check for common errors
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"One or more entities not found"
                )
            elif "400" in str(e):
                return create_error_response(
                    "INVALID_REQUEST",
                    f"Invalid unmerge request: {str(e)}"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to unmerge entity"
            )

        return unmerge_result
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in unmerge_entity_by_contributor: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while unmerging entity"
        )

async def unmerge_entity_tree_by_contributor(origin_entity_id: str, contributor_entity_id: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Unmerge a contributor entity and all profiles merged beneath it from a merged entity.
    
    Args:
        origin_entity_id (str): The ID of the origin entity (the merged entity)
        contributor_entity_id (str): The ID of the contributor entity to unmerge from the origin entity
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the result of the unmerge operation with 'a' (modified origin) and 'b' (spawn) entities
    
    Raises:
        Exception: If there's an error during the unmerge operation
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = UnmergeEntityRequest(
                origin_entity_id=origin_entity_id,
                contributor_entity_id=contributor_entity_id,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in unmerge_entity_tree_by_contributor: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid entity ID format: {str(e)}"
            )
            
        # Construct URL with validated entity IDs
        url = get_reltio_url(f"entities/{request.origin_entity_id}/_treeUnmerge", "api", request.tenant_id)
        
        # Add the contributor entity URI as a query parameter
        params = {
            "contributorURI": f"entities/{request.contributor_entity_id}"
        }
        
        try:
            headers = get_reltio_headers()
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
        
        # Make the POST request with URL parameters
        try:
            unmerge_result = http_request(
                url, 
                method='POST',
                params=params,
                headers=headers
            )
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check for common errors
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"One or more entities not found"
                )
            elif "400" in str(e):
                return create_error_response(
                    "INVALID_REQUEST",
                    f"Invalid tree unmerge request: {str(e)}"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to tree unmerge entity"
            )
        
        return unmerge_result
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in unmerge_entity_tree_by_contributor: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while tree unmerging entity"
        )


async def get_entity_with_matches(
    entity_id: str, 
    attributes: List[str] = None, 
    include_match_attributes: bool = True,
    match_attributes: List[str] = None,
    match_limit: int = 5,
    tenant_id: str = RELTIO_TENANT
) -> dict:
    """Get detailed information about a Reltio entity along with its potential matches
    
    Args:
        entity_id (str): The ID of the entity to retrieve
        attributes (List[str]): Specific attributes to return for source entity. Empty/None returns all attributes
        include_match_attributes (bool): Whether to include full attribute details for matching entities
        match_attributes (List[str]): Specific attributes to return for matching entities (only used if include_match_attributes=True)
        match_limit (int): Maximum number of potential matches to return (1-5)
        tenant_id (str): Tenant ID for the Reltio environment
    
    Returns:
        A dictionary containing the source entity, matches, and total count
    
    Raises:
        Exception: If there's an error getting the entity or matches
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = EntityWithMatchesRequest(
                entity_id=entity_id,
                attributes=attributes or [],
                include_match_attributes=include_match_attributes,
                match_attributes=match_attributes or [],
                match_limit=match_limit,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_entity_with_matches: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid request parameters: {str(e)}"
            )
        
        try:
            headers = get_reltio_headers()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Get the source entity
        source_url = get_reltio_url(f"entities/{request.entity_id}", "api", request.tenant_id)
        
        try:
            validate_connection_security(source_url, headers)
        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        try:
            source_entity = http_request(source_url, headers=headers)
        except Exception as e:
            logger.error(f"API request error getting source entity: {str(e)}")
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Entity with ID {request.entity_id} not found"
                )
            return create_error_response(
                "SERVER_ERROR",
                "Failed to retrieve source entity from Reltio API"
            )
        
        # Get potential matches using _transitiveMatches endpoint
        matches_url = get_reltio_url(f"entities/{request.entity_id}/_transitiveMatches", "api", request.tenant_id)
        
        try:
            validate_connection_security(matches_url, headers)
        except SecurityError as e:
            logger.error(f"Security error for matches: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        params = {
            "deep": 1,
            "markMatchedValues": "true",
            "sort": "relevance",
            "order": "desc",
            "activeness": "active",
            "limit": request.match_limit
        }
        
        try:
            matches_result = http_request(matches_url, headers=headers, params=params)
        except Exception as e:
            logger.warning(f"Error retrieving matches: {str(e)}")
            # Continue without matches if the matches API fails
            matches_result = []
        
        # Get total count of matches (separate call without limit)
        total_count = 0
        try:
            total_params = {
                "deep": 1,
                "markMatchedValues": "true",
                "activeness": "active",
                "limit": 1000  # High limit to get accurate count
            }
            total_matches_result = http_request(matches_url, headers=headers, params=total_params)
            total_count = len(total_matches_result) if total_matches_result else 0
        except Exception as e:
            logger.warning(f"Error getting total matches count: {str(e)}")
            total_count = len(matches_result) if matches_result else 0
        
        # Fetch full entity details for matching entities if requested
        match_entities = {}
        if request.include_match_attributes and matches_result:
            for match in matches_result[:request.match_limit]:
                match_entity_id = match["object"]["uri"].split("/")[-1]
                try:
                    match_entity_url = get_reltio_url(f"entities/{match_entity_id}", "api", request.tenant_id)
                    match_entity = http_request(match_entity_url, headers=headers)
                    
                    # Filter match entity attributes if specified
                    filtered_match_entity = filter_entity(match_entity, {"attributes": request.match_attributes} if request.match_attributes else None)
                    match_entities[match["object"]["uri"]] = filtered_match_entity
                except Exception as e:
                    logger.warning(f"Failed to get details for match entity {match_entity_id}: {str(e)}")
                    # Continue with other matches even if one fails
                    continue
        
        # Filter source entity attributes if specified
        filtered_source_entity = filter_entity(source_entity, {"attributes": request.attributes} if request.attributes else None)
        
        # Prepare the result
        result = {
            "source_entity": {
                "uri": f"entities/{request.entity_id}",
                "label": source_entity.get("label", ""),
                "attributes": simplify_reltio_attributes(filtered_source_entity.get("attributes", {}))
            },
            "matches": format_unified_entity_matches(matches_result[:request.match_limit], match_entities),
            "total_matches": total_count
        }
        
        # Add crosswalks for source entity if present
        if "crosswalks" in filtered_source_entity:
            result["source_entity"]["crosswalks"] = slim_crosswalks(filtered_source_entity["crosswalks"])
        
        # Log activity for success
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.POTENTIAL_MATCHES_FOUND.value,
                client_type=ACTIVITY_CLIENT,
                description=json.dumps({
                    "uri": f"entities/{entity_id.split('/')[-1]}",
                    "label": source_entity.get("label", ""),
                    "total_matches": total_count
                }),
                items=[{"objectUri": f"entities/{entity_id.split('/')[-1]}"}]
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_entity_with_matches: {str(log_error)}")
        
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_entity_with_matches: {str(e)}")
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while retrieving entity with matches"
        )


async def create_entities(entities: List[Dict[str, Any]], return_objects: bool = False, execute_lca: bool = True, tenant_id: str = RELTIO_TENANT) -> dict:
    """Create one or more entities in Reltio
    
    Args:
        entities (List[Dict[str, Any]]): List of entity objects to create. Each entity must have a 'type' field.
        return_objects (bool): Whether the response contains created entities: true or false(default)
        execute_lca (bool): Whether to trigger all Lifecycle Actions during this request: true (default) or false
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the creation results for each entity
    
    Raises:
        Exception: If there's an error creating the entities
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = CreateEntitiesRequest(
                entities=entities,
                return_objects=return_objects,
                execute_lca=execute_lca,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in create_entities: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid entities data: {str(e)}"
            )
        
        # Construct URL
        url = get_reltio_url("entities", "api", request.tenant_id)
        
        try:
            headers = get_reltio_headers()
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
        params = {}
        params["returnObjects"] = str(request.return_objects).lower()
        if not request.execute_lca:
            params["executeLCA"] = "false"
        
        # Make the POST request
        try:
            create_result = http_request(
                url,
                method='POST',
                data=request.entities,
                headers=headers,
                params=params
            )
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check for common errors
            if "400" in str(e):
                return create_error_response(
                    "INVALID_REQUEST",
                    f"Invalid create entities request: {str(e)}"
                )
            elif "401" in str(e):
                return create_error_response(
                    "AUTHENTICATION_ERROR",
                    "Unauthorized - check your authentication token"
                )
            elif "403" in str(e):
                return create_error_response(
                    "AUTHORIZATION_ERROR",
                    "Forbidden - insufficient permissions to create entities"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to create entities"
            )
        
        # Process the response to extract only the required fields
        if isinstance(create_result, list):
            processed_results = []
            successful_count = 0
            failed_count = 0
            
            for result in create_result:
                processed_result = {
                    "index": result.get("index")
                }
                
                # Check if the entity creation was successful
                if result.get("successful"):
                    successful_count += 1
                    processed_result["successful"] = True
                    
                    # Add object details if returnObjects was true and object exists
                    if request.return_objects and "object" in result:
                        entity_obj = result["object"]
                        processed_result["object"] = {
                            "uri": entity_obj.get("uri"),
                            "type": entity_obj.get("type"),
                            "tags": entity_obj.get("tags"),
                            "createdBy": entity_obj.get("createdBy"),
                            "createdTime": entity_obj.get("createdTime"),
                            "updatedBy": entity_obj.get("updatedBy"),
                            "updatedTime": entity_obj.get("updatedTime"),
                            "isFavorite": entity_obj.get("isFavorite"),
                            "label": entity_obj.get("label"),
                            "crosswalks": entity_obj.get("crosswalks")
                        }
                        # Remove None values
                        processed_result["object"] = {k: v for k, v in processed_result["object"].items() if v is not None}
                    else:
                        processed_result["uri"] = result.get("uri")
                else:
                    failed_count += 1
                    processed_result["successful"] = False
                    # Include error information
                    if "errors" in result:
                        processed_result["errors"] = result["errors"]
                
                processed_results.append(processed_result)
            
            
            
            return yaml.dump(processed_results, sort_keys=False)
        else:
            # Handle unexpected response format
            logger.warning(f"Unexpected response format from create entities API: {type(create_result)}")
            return create_error_response(
                "UNEXPECTED_RESPONSE",
                "Unexpected response format from Reltio API"
            )
        
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in create_entities: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while creating entities"
        )


async def get_entity_hops(
    entity_id: str,
    select: str = "label,secondaryLabel,entities.attributes,relations.attributes",
    graph_type_uris: str = "",
    relation_type_uris: str = "",
    entity_type_uris: str = "",
    deep: int = 1,
    max_results: int = 100,
    activeness_enabled: bool = True,
    return_inactive: bool = False,
    filter_last_level: bool = True,
    return_data_anyway: bool = False,
    options: str = "ovOnly",
    tenant_id: str = RELTIO_TENANT
) -> dict:
    """Get entity graph (hops) for a specific entity with comprehensive filtering and traversal options
    
    Args:
        entity_id (str): The ID of the entity to get hops for
        select (str): Comma-separated list of properties to return. Defaults to "label,secondaryLabel,entities.attributes,relations.attributes"
        graph_type_uris (str): Comma-separated list of graph type URIs for graphs to be traversed
        relation_type_uris (str): Comma-separated list of relation type URIs for relations to be traversed
        entity_type_uris (str): Comma-separated list of entity type URIs for entities to be traversed
        deep (int): Limits traversing deep levels. Default is 1
        max_results (int): Limits the amount of entities to be returned. Default is 100, max is 1500
        activeness_enabled (bool): Flag to determine whether to return only active entities and relations. Default is True
        return_inactive (bool): Flag to traverse inactive entities/relationships. Default is False
        filter_last_level (bool): Flag to NOT count relationships from the last level. Default is True
        return_data_anyway (bool): Flag to return partial data when credit consumption limit is exceeded. Default is False
        options (str): Comma-separated list of options (sendHidden, ovOnly, nonOvOnly, sendMasked, showAppliedSurvivorshipRules)
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value
    
    Returns:
        A dictionary containing the entity hops (graph) details with simplified attributes
    
    Raises:
        Exception: If there's an error getting the entity hops
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = EntityIdRequest(
                entity_id=entity_id,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_entity_hops: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid entity ID format: {str(e)}"
            )
                
        # Construct URL with validated entity ID
        url = get_reltio_url(f"entities/{request.entity_id}/_hops", "api", request.tenant_id)
        
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
        
        # Validate and constrain max_results
        if max_results < 1:
            max_results = 1
        elif max_results > 1500:
            max_results = 1500
            logger.info(f"Max results limited to 1500 for entity hops")
        
        # Validate and constrain deep
        if deep < 1:
            deep = 1
        elif deep > 10:  # Reasonable upper limit to prevent excessive traversal
            deep = 10
            logger.info(f"Deep level limited to 10 for entity hops")
        
        # Build query parameters
        params = {
            "select": select,
            "deep": deep,
            "max": max_results,
            "activeness_enabled": str(activeness_enabled).lower(),
            "returnInactive": str(return_inactive).lower(),
            "filterLastLevel": str(filter_last_level).lower(),
            "returnDataAnyway": str(return_data_anyway).lower(),
            "options": options
        }
        
        # Add optional URI filters if provided
        if graph_type_uris.strip():
            params["graphTypeURIs"] = graph_type_uris.strip()
        
        if relation_type_uris.strip():
            params["relationTypeURIs"] = relation_type_uris.strip()
        
        if entity_type_uris.strip():
            params["entityTypeURIs"] = entity_type_uris.strip()
        
        # Make the request with timeout
        try:
            hops_data = http_request(url, method='GET', headers=headers, params=params)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            error_str = str(e)
            
            # Extract error message from JSON response if available
            error_message = ""
            try:
                json_match = re.search(r'\{.*\}', error_str)
                if json_match:
                    error_json = json.loads(json_match.group())
                    error_message = error_json.get("errorMessage", "")
            except (json.JSONDecodeError, AttributeError):
                pass
            
            # Check for specific error codes and return appropriate responses
            if "404" in error_str:
                if not error_message:
                    error_message = "Entity not found"
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Entity with ID {request.entity_id} not found: {error_message}"
                )
            elif "400" in error_str:
                if not error_message:
                    error_message = "Invalid request parameters"
                return create_error_response(
                    "INVALID_REQUEST",
                    f"Bad request: {error_message}"
                )
            
            # Generic server error for other cases
            if not error_message:
                error_message = "An error occurred while processing the request"
            
            return create_error_response(
                "SERVER_ERROR",
                f"Failed to retrieve entity hops from Reltio API: {error_message}"
            )
        
        # Try to log activity for success
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.ENTITY_HOPS.value,
                client_type=ACTIVITY_CLIENT,
                description=json.dumps({
                    "uri": f"entities/{entity_id.split('/')[-1]}",
                    "deep": deep,
                    "max_results": max_results,
                    "select": select,
                    "graph_type_uris": graph_type_uris,
                    "relation_type_uris": relation_type_uris,
                    "entity_type_uris": entity_type_uris
                }),
                items=[{"objectUri": f"entities/{entity_id.split('/')[-1]}"}]
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_entity_hops: {str(log_error)}")
        
        # Process the response to simplify attributes
        result = {
            "relations": hops_data.get("relations", []),
            "entities": [],
            "dataComplete": hops_data.get("dataComplete", True)
        }
        
        # Process entities and simplify their attributes
        for entity in hops_data.get("entities", []):
            processed_entity = {
                "URI": entity.get("uri"),
                "type": entity.get("type"),
                "label": entity.get("label"),
                "secondaryLabel": entity.get("secondaryLabel"),
                "traversedRelationsCount": entity.get("traversedRelations", 0),
                "untraversedRelationsCount": entity.get("untraversedRelations", 0)
            }
            
            # Simplify attributes using the existing function
            if "attributes" in entity:
                processed_entity["attributes"] = simplify_reltio_attributes(entity["attributes"])
            
            # Add crosswalks if present
            if "crosswalks" in entity:
                processed_entity["crosswalks"] = slim_crosswalks(entity["crosswalks"])
            
            result["entities"].append(processed_entity)
        
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_entity_hops: {str(e)}")
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while retrieving entity hops"
        )


async def get_entity_parents(
    entity_id: str,
    graph_type_uris: str,
    select: str = "uri,label,type,secondaryLabel",
    options: str = "",
    tenant_id: str = RELTIO_TENANT
) -> dict:
    """Get the parents of a specified entity from Reltio
    
    Args:
        entity_id (str): The ID of the entity to get parents for
        graph_type_uris (str): Comma-separated list of graph type URIs to traverse (required)
                            for example : OrganizationHierarchy,Hierarchy 
        select (str): Comma-separated list of properties to include in the response. Defaults to "uri,label,type,secondaryLabel"
        options (str): Comma-separated list of options affecting the response content:
            - sendHidden: Include hidden attributes in the response
            - ovOnly: Return only attribute values with the ov=true flag
            - nonOvOnly: Return only attribute values with the ov=false flag
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value
    
    Returns:
        A dictionary containing:
        - parentPaths: Array of parent paths, where each path is an array of entities with their relations
        - entities: Dictionary of entity details keyed by entity URI
        - relations: Dictionary of relation details keyed by relation URI
    
    Raises:
        Exception: If there's an error getting the entity parents
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = GetEntityParentsRequest(
                entity_id=entity_id,
                graph_type_uris=graph_type_uris,
                select=select,
                options=options,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_entity_parents: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid request parameters: {str(e)}"
            )
        
        # Construct URL with validated entity ID
        url = get_reltio_url(f"entities/{request.entity_id}/_parents", "api", request.tenant_id)
        
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
        
        # Build query parameters
        params = {
            "graphTypeURIs": request.graph_type_uris,
        }
        
        # Add optional parameters if provided
        if request.select and request.select.strip():
            params["select"] = request.select.strip()
        
        if request.options and request.options.strip():
            params["options"] = request.options.strip()
        
        # Make the request with timeout
        try:
            parents_data = http_request(url, method='GET', headers=headers, params=params)
        except Exception as e:
            logger.error(f"API request error: {e}")
            error_str = str(e)
            
            # Extract error message from JSON response if available
            error_message = ""
            error_code = None
            try:
                json_match = re.search(r'\{.*\}', error_str)
                if json_match:
                    error_json = json.loads(json_match.group())
                    error_message = error_json.get("errorMessage", "")
                    error_code = error_json.get("errorCode")
            except (json.JSONDecodeError, AttributeError):
                pass
            
            # Check for specific error codes and return appropriate responses
            if "404" in error_str or error_code == 119:
                if not error_message:
                    error_message = "Entity or graph type not found"
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Entity with ID {request.entity_id} or graph type not found: {error_message}"
                )
            elif "400" in error_str:
                if not error_message:
                    error_message = "Invalid request parameters"
                return create_error_response(
                    "INVALID_REQUEST",
                    f"Bad request: {error_message}"
                )
            
            # Generic server error for other cases
            if not error_message:
                error_message = "An error occurred while processing the request"
            
            return create_error_response(
                "SERVER_ERROR",
                f"Failed to retrieve entity parents from Reltio API: {error_message}"
            )
        
        # Try to log activity for success
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.USER_PROFILE_VIEW.value,
                client_type=ACTIVITY_CLIENT,
                description=json.dumps({
                    "uri": f"entities/{entity_id.split('/')[-1]}",
                    "graph_type_uris": graph_type_uris,
                    "select": select,
                    "options": options
                }),
                items=[{"objectUri": f"entities/{entity_id.split('/')[-1]}"}]
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_entity_parents: {str(log_error)}")
        
        # Process the response to match the actual API structure
        result = {
            "parentPaths": parents_data.get("parentPaths", []),
            "entities": {},
            "relations": parents_data.get("relations", {})
        }
        
        # Process entities from the entities object (not array)
        entities_data = parents_data.get("entities", {})
        for entity_uri, entity_data in entities_data.items():
            processed_entity = {
                "uri": entity_data.get("uri"),
                "type": entity_data.get("type"),
                "label": entity_data.get("label"),
                "secondaryLabel": entity_data.get("secondaryLabel")
            }
            # Simplify attributes using the existing function if present
            if "attributes" in entity_data:
                processed_entity["attributes"] = simplify_reltio_attributes(entity_data["attributes"])
            
            result["entities"][entity_uri] = processed_entity
        
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_entity_parents: {str(e)}")
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while retrieving entity parents"
        )

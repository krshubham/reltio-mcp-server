import logging
import yaml
import json
from constants import ACTIVITY_CLIENT
from env import RELTIO_TENANT
from util.api import get_reltio_url, http_request, create_error_response, validate_connection_security
from util.auth import get_reltio_headers
from util.exceptions import SecurityError
from util.models import MatchScoreRequest, ConfidenceLevelRequest, GetTotalMatchesRequest, GetMatchFacetsRequest, UnifiedMatchRequest, GetPotentialMatchApisRequest
from util.activity_log import ActivityLog
from tools.util import ActivityLogLabel


# Configure logging
logger = logging.getLogger("mcp.server.reltio")


async def find_matches_by_match_score(start_match_score: int = 0, end_match_score: int = 100,
                                     entity_type: str = "Individual", tenant_id: str = RELTIO_TENANT,
                                     max_results: int = 10, offset: int = 0) -> dict:
    """Find all potential matches by match score range
    
    Args:
        start_match_score (int): Minimum match score to filter matches. Default to 0.
        end_match_score (int): Maximum match score to filter matches. Default to 100.
        entity_type (str): Entity type to filter by. Default to 'Individual'.
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
        max_results (int): Maximum number of results to return. Default to 25.
    
    Returns:
        A dictionary containing the search results
    
    Raises:
        Exception: If there's an error getting the matches
    """  
    try:
        # Validate inputs using Pydantic model
        try:
            request = MatchScoreRequest(
                start_match_score=start_match_score,
                end_match_score=end_match_score,
                entity_type=entity_type,
                tenant_id=tenant_id,
                max_results=min(max_results, 10),
                offset=offset
            )
        except ValueError as e:
            logger.warning(f"Validation error in find_matches_by_match_score: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        try:
            headers = get_reltio_headers()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Special URL construction specifically for search endpoint
        url = get_reltio_url("entities/_search", "api", request.tenant_id)
        
        # Validate connection security
        try:
            validate_connection_security(url, headers)
        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        # Use exact string from Postman to ensure identical formatting but with validated inputs
        filter_expression = f"(range(potentialMatches.matchScore,{request.start_match_score},{request.end_match_score}) and equals(type,'configuration/entityTypes/{request.entity_type}')"
        
        # Build the payload to exactly match the Postman request
        payload = {
            "filter": filter_expression,
            "select": "uri,label,type,relevanceScores",
            "max":  min(request.max_results, 10),
            "offset": request.offset,
            "scoreEnabled": False,
            "options": "ovOnly",
            "activeness": "active"
        }
        try:
            result = http_request(url, method='POST', headers=headers, data=payload)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "SERVER_ERROR",
                f"Failed to retrieve matches: {str(e)}"
            ) 

        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                description=f"find_matches_by_match_score_tool : Successfully fetched potential matches for entity type {request.entity_type} with match score between {request.start_match_score} and {request.end_match_score}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for find_matches_by_match_score: {str(log_error)}")
       
        # Return appropriate response based on results
        if result and len(result) > 0:
            result=[{"uri":match["uri"],"label":match["label"],"type":match["type"]} for match in result]
            return yaml.dump(result,sort_keys=False)
        else:
            return {
                "message": f"No potential matches found for entity type {request.entity_type} with match score between {request.start_match_score} and {request.end_match_score}.",
                "results": []
            }
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in find_matches_by_match_score: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while searching for matches"
        )


async def find_matches_by_confidence(confidence_level: str = "Low confidence", entity_type: str = "Individual",
                                        tenant_id: str = RELTIO_TENANT, max_results: int = 10, offset: int = 0) -> dict:
    """Find all potential matches by confidence level
    
    Args:
        confidence_level (str): Confidence level for matches (e.g., 'Strong matches', 'Medium confidence', 'Low confidence', 'High confidence', 'Super strong matches'). Default to 'Low confidence'.
        entity_type (str): Entity type to filter by. Default to 'Individual'.
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
        max_results (int): Maximum number of results to return. Default to 25.
    
    Returns:
        A dictionary containing the search results

    Raises:
        Exception: If there's an error getting the matches
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = ConfidenceLevelRequest(
                confidence_level=confidence_level,
                entity_type=entity_type,
                tenant_id=tenant_id,
                max_results=min(max_results, 10),
                offset=offset
            )
        except ValueError as e:
            logger.warning(f"Validation error in find_matches_by_confidence: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        try:
            headers = get_reltio_headers()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Special URL construction specifically for search endpoint
        url = get_reltio_url("entities/_search", "api", request.tenant_id)
        
        # Validate connection security
        try:
            validate_connection_security(url, headers)
        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        filter_expression = f"(equals(type,'configuration/entityTypes/{request.entity_type}') and equals(relevanceScores.actionLabel,'{request.confidence_level}')) and equals(type,'configuration/entityTypes/{request.entity_type}')"
        
        # Build the payload to exactly match the Postman request
        payload = {
            "filter": filter_expression,
            "select": "uri,label,type,relevanceScores",
            "max": min(request.max_results, 10),
            "offset":  request.offset,
            "scoreEnabled": False,
            "options": "ovOnly",
            "activeness": "active"
        }
        try:
            result = http_request(url, method='POST', headers=headers, data=payload)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "SERVER_ERROR",
                f"Failed to retrieve matches: {str(e)}"
            )
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                description=f"find_matches_by_confidence_tool : Successfully fetched potential matches for entity type {request.entity_type} with confidence level {request.confidence_level}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for find_matches_by_confidence: {str(log_error)}")
        
        # Return appropriate response based on results
        if result and len(result) > 0:
            result=[{"uri":match["uri"],"label":match["label"],"type":match["type"]} for match in result]
            return yaml.dump(result,sort_keys=False)
        else:
            return {
                "message": f"No potential matches found for entity type {request.entity_type} with confidence level {request.confidence_level}.",
                "results": []
            }
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in find_matches_by_confidence: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while searching for matches by confidence"
        )


async def get_total_matches(min_matches: int = 0, tenant_id: str = RELTIO_TENANT) -> dict:
    """Get the total count of potential matches in the tenant
    
    Args:
        min_matches (int): Minimum number of matches to filter by. Returns total count of entities with greater than this many matches. Default to 0.
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the total count of potential matches
    
    Raises:
        Exception: If there's an error getting the total matches count
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = GetTotalMatchesRequest(
                min_matches=min_matches,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_total_matches: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        try:
            headers = get_reltio_headers()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Construct URL for the total endpoint
        url = get_reltio_url("entities/_total", "api", request.tenant_id)
        
        # Validate connection security
        try:
            validate_connection_security(url, headers)
        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        # Build the payload for the total request
        filter_expression = f"(gt(matches,'{request.min_matches}'))"
        
        payload = {
            "filter": filter_expression,
            "options": "searchByOv,ovOnly",
            "activeness": "active"
        }
        
        try:
            result = http_request(url, method='POST', headers=headers, data=payload)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "SERVER_ERROR",
                f"Failed to retrieve total matches count: {str(e)}"
            )
        
        # Return the total count
        if result and "total" in result:
            try:
                await ActivityLog.execute_and_log_activity(
                    tenant_id=tenant_id,
                    description=f"get_total_matches : Found {result['total']} entities with more than {request.min_matches} potential matches."
                )
            except Exception as log_error:
                logger.error(f"Activity logging failed for get_total_matches: {str(log_error)}")
            return {
                "total": result["total"],
                "min_matches": request.min_matches,
                "message": f"Found {result['total']} entities with more than {request.min_matches} potential matches."
            }
        else:
            return {
                "error": "RESPONSE_ERROR",
                "message": "API response did not contain a total count",
                "details": result
            }
            
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in get_total_matches: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while getting total matches count"
        )


async def get_total_matches_by_entity_type(min_matches: int = 0, tenant_id: str = RELTIO_TENANT) -> dict:
    """Get the facet counts of potential matches by entity type
    
    Args:
        min_matches (int): Minimum number of matches to filter by. Returns facet counts of entities with greater than this many matches. Default to 0.
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the counts of potential matches by entity type
    
    Raises:
        Exception: If there's an error getting the match facets
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = GetMatchFacetsRequest(
                min_matches=min_matches,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_total_matches_by_entity_type: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        try:
            headers = get_reltio_headers()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Construct the facets URL with query parameters
        # Need to escape % character in the filter query parameter
        filter_param = f"(gt(matches,'{request.min_matches}'))"
        
        # Using params dict for proper URL encoding
        params = {
            "activeness": "active",
            "filter": filter_param,
            "options": "searchByOv,ovOnly"
        }
        
        url = get_reltio_url("entities/_facets", "api", request.tenant_id)
        
        # Validate connection security
        try:
            validate_connection_security(url, headers)
        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        # Fixed payload for facets
        payload = [{"fieldName": "type", "pageSize": 101, "pageNo": 1}]
        
        try:
            result = http_request(url, method='POST', headers=headers, data=payload, params=params)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "SERVER_ERROR",
                f"Failed to retrieve match facets: {str(e)}"
            )
        
        # Return the facet counts
        if result and "type" in result:
            try:
                await ActivityLog.execute_and_log_activity(
                    tenant_id=tenant_id,
                    description=f"get_total_matches_by_entity_type : Found entities by type with more than {request.min_matches} potential matches."
                )
            except Exception as log_error:
                logger.error(f"Activity logging failed for get_total_matches_by_entity_type: {str(log_error)}")

            return {
                "type_counts": result["type"],
                "min_matches": request.min_matches,
                "message": f"Found entities by type with more than {request.min_matches} potential matches."
            }
        else:
            return {
                "error": "RESPONSE_ERROR",
                "message": "API response did not contain facet counts",
                "details": result
            }
            
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in get_total_matches_by_entity_type: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while getting match facets by entity type"
        )


async def find_potential_matches(search_type: str = "match_rule", filter: str = "", entity_type: str = "Individual",
                              tenant_id: str = RELTIO_TENANT, max_results: int = 10, offset: int = 0,
                              search_filters: str = "") -> dict:
    """Unified function to find all potential matches by match rule, score range, or confidence level
    
    Args:
        search_type (str): Type of search - 'match_rule' (default), 'score', or 'confidence'
        filter (str): Filter value based on search_type:
            - For 'match_rule': match rule ID (e.g., 'BaseRule05')
            - For 'score': comma-separated start,end range (e.g., '50,100')
            - For 'confidence': confidence level (e.g., 'High confidence')
        entity_type (str): Entity type to filter by. Default to 'Individual'.
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
        max_results (int): Maximum number of results to return. Default to 10, and is capped at 10.
        offset (int): Starting index for paginated results. Use 0 for the first page.
        search_filters (str): Additional search filters to apply (e.g., 'equals(attributes.FirstName,'John')')
    
    Returns:
        A dictionary containing the search results
    
    Raises:
        Exception: If there's an error getting the matches
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = UnifiedMatchRequest(
                search_type=search_type,
                filter=filter,
                entity_type=entity_type,
                tenant_id=tenant_id,
                max_results=min(max_results, 10),
                offset=offset,
                search_filters=search_filters
            )
        except ValueError as e:
            logger.warning(f"Validation error in find_potential_matches: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        try:
            headers = get_reltio_headers()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        # Special URL construction specifically for search endpoint
        url = get_reltio_url("entities/_search", "api", request.tenant_id)
        
        # Validate connection security
        try:
            validate_connection_security(url, headers)
        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        # Build filter expression based on search type
        if request.search_type == "match_rule":
            # For match rule: equals(matchRules,<match_rule_id>)
            match_filter = request.filter.split('/')[-1]
            primary_filter = f"equals(matchRules,'configuration/entityTypes/{request.entity_type}/matchGroups/{match_filter}')"
        elif request.search_type == "score":
            # For score: range(potentialMatches.matchScore,start,end)
            start_score, end_score = request.filter.split(',')
            start_score = int(start_score.strip())
            end_score = int(end_score.strip())
            primary_filter = f"range(relevanceScores.relevance,{(start_score)/100},{(end_score)/100})"
        elif request.search_type == "confidence":
            # For confidence: equals(relevanceScores.actionLabel,'confidence_level')
            primary_filter = f"equals(relevanceScores.actionLabel,'{request.filter}')"
        
        # Combine primary filter with entity type filter
        entity_type_filter = f"equals(type,'configuration/entityTypes/{request.entity_type}')"
        
        # Combine all filters
        filter_parts = [primary_filter, entity_type_filter]
        
        # Add additional search filters if provided
        if request.search_filters.strip():
            filter_parts.append(request.search_filters.strip())
        
        # Create final filter expression with proper parentheses
        filter_expression = f"({' and '.join(filter_parts)})"
        
        # Build the payload to match the pattern from existing functions
        payload = {
            "filter": filter_expression,
            "select": "uri,label,type,relevanceScores",
            "max": min(request.max_results, 10),
            "offset": request.offset,
            "scoreEnabled": False,
            "options": "ovOnly",
            "activeness": "active"
        }
        
        try:
            result = http_request(url, method='POST', headers=headers, data=payload)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "SERVER_ERROR",
                f"Failed to retrieve matches: {str(e)}"
            )
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.USER_SEARCH.value,
                client_type=ACTIVITY_CLIENT,
                description=json.dumps({
                    "activity": {
                        "query": f"filter={payload['filter']}",
                        "search_type": request.search_type
                    },
                    "version": '2.0'
                })
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for find_potential_matches: {str(log_error)}")

        # Return appropriate response based on results
        if result and len(result) > 0:
            result = [{"uri": match["uri"], "label": match["label"], "type": match["type"]} for match in result]
            return yaml.dump(result, sort_keys=False)
        else:
            return {
                "message": f"No potential matches found for entity type {request.entity_type} with {request.search_type} filter '{request.filter}'.",
                "results": []
            }
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in find_potential_matches: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while searching for matches"
        )


async def get_potential_match_apis(min_matches: int = 0, tenant_id: str = RELTIO_TENANT) -> dict:
    """Get total, entity-level, and match-rule-level counts of potential matches in the tenant
    
    Args:
        min_matches (int): Minimum number of matches to filter by. Returns total count of entities with greater than this many matches. Default to 0.
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing total, entity-level, and match-rule-level counts
    
    Raises:
        Exception: If there's an error getting the potential matches counts
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = GetPotentialMatchApisRequest(
                min_matches=min_matches,
                tenant_id=tenant_id
            )
        except Exception as e:
            logger.error(f"Validation error in get_potential_match_apis: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )

        try:
            headers = get_reltio_headers()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )

        url = get_reltio_url("entities/_facets", "api", request.tenant_id)
        try:
            validate_connection_security(url, headers)
        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return create_error_response(
                "SECURITY_ERROR",
                "Security requirements not met"
            )
        
        filter_expression = f"(gt(matches,'{request.min_matches}'))"
        params = {
            "filter": filter_expression,
            "facet": "matchRules,type",
            "activeness": "active",
            "options": "searchByOv,ovOnly"
        }
        try:
            result = http_request(url, headers=headers, params=params)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "SERVER_ERROR",
                f"Failed to retrieve potential match APIs: {str(e)}"
            )
        
        # Process the result to calculate sum of type values
        if result and "type" in result:
            type_dict = result["type"]
            if isinstance(type_dict, dict):
                # Calculate sum of all values in the type dictionary
                type_sum = sum(type_dict.values())
                
                # Add the sum to the result
                result["total_matches"] = type_sum
                
                try:
                    await ActivityLog.execute_and_log_activity(
                        tenant_id=tenant_id,
                        label=ActivityLogLabel.POTENTIAL_MATCHES_FOUND.value,
                        client_type=ACTIVITY_CLIENT,
                        description=f"get_potential_matches_stats_tool : Found total potential match  with type and match rules with more than {request.min_matches} matches."
                    )
                except Exception as log_error:
                    logger.error(f"Activity logging failed for get_potential_match_apis: {str(log_error)}")
        else:
            return {
                "error": "RESPONSE_ERROR",
                "message": "API response did not contain facet counts",
                "details": result
            }
        
        return result
        
        
    except Exception as e:
        logger.error(f"Unexpected error in get_potential_match_apis: {str(e)}")
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while getting potential match APIs"
        )
    
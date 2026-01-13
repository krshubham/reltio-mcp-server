import logging
from typing import List, Dict, Any, Optional
import yaml
from constants import ACTIVITY_CLIENT
from env import RELTIO_TENANT
from util.api import get_reltio_url, http_request, create_error_response, validate_connection_security
from util.auth import get_reltio_headers
from util.models import RelationIdRequest, CreateRelationsRequest, GetEntityRelationsRequest, RelationSearchRequest
from util.activity_log import ActivityLog
from tools.util import ActivityLogLabel, simplify_reltio_attributes

# Configure logging
logger = logging.getLogger("mcp.server.reltio")


async def get_relation_details(relation_id: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Get detailed information about a Reltio relation by ID
    
    Args:
        relation_id (str): The ID of the relation to retrieve
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the relation details
    
    Raises:
        Exception: If there's an error getting the relation details
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = RelationIdRequest(
                relation_id=relation_id,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_relation_details: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid relation ID format: {str(e)}"
            )
        
        # Construct URL with validated relation ID
        url = get_reltio_url(f"relations/{request.relation_id}", "api", request.tenant_id)
        
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
            relation = http_request(url, headers=headers)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check if it's a 404 error (relation not found)
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Relation with ID {request.relation_id} not found"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to retrieve relation details from Reltio API"
            )
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.RELATIONSHIP_SEARCH.value,
                client_type=ACTIVITY_CLIENT,
                description=f"get_relation_details_tool : Successfully fetched relation details for relation {relation_id}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_relation_details: {str(log_error)}")
        relation["attributes"]=simplify_reltio_attributes(relation["attributes"])
        return yaml.dump(relation, sort_keys=False)
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in get_relation_details: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while retrieving relation details"
        )


async def create_relationships(relations: list, options: str = None, tenant_id: str = RELTIO_TENANT) -> dict:
    """Create relationships between entities in Reltio
    
    Args:
        relations (list): List of relation objects to create. Each relation must include:
            - type: Relation type (mandatory)
            - startObject: Start object with type (mandatory) and either objectURI or crosswalks
            - endObject: End object with type (mandatory) and either objectURI or crosswalks
            - crosswalks: Optional list of crosswalks for the relation
        options (str): Optional comma-separated list of options (e.g., 'partialOverride', 'directMatchMode')
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the creation results
    
    Raises:
        Exception: If there's an error creating the relationships
        
    Examples:
        # Create a relationship between two entities using objectURIs
        create_relationships([{
            "type": "configuration/relationTypes/VistaGlobalMenuItemToVistaLocalMenuItem",
            "startObject": {
                "type": "configuration/entityTypes/VistaGlobalMenuItem",
                "objectURI": "entities/e1"
            },
            "endObject": {
                "type": "configuration/entityTypes/VistaLocalMenuItem", 
                "objectURI": "entities/e2"
            }
        }])
        
        # Create a relationship using crosswalks
        create_relationships([{
            "type": "configuration/relationTypes/VistaGlobalMenuItemToVistaLocalMenuItem",
            "crosswalks": [{
                "type": "configuration/sources/Agent",
                "value": "R|4QrP0xy|185asgAe"
            }],
            "startObject": {
                "type": "configuration/entityTypes/VistaGlobalMenuItem",
                "crosswalks": [{
                    "type": "configuration/sources/Reltio",
                    "value": "4QrP0xy"
                }]
            },
            "endObject": {
                "type": "configuration/entityTypes/VistaLocalMenuItem",
                "crosswalks": [{
                    "type": "configuration/sources/RFM",
                    "value": "CH|340"
                }]
            }
        }], options="partialOverride")
        
        # Create a relationship using crosswalks with sourceTable
        create_relationships([{
            "type": "configuration/relationTypes/AccountToContact",
            "startObject": {
                "type": "configuration/entityTypes/Account",
                "crosswalks": [{
                    "type": "configuration/sources/WI",
                    "sourceTable": "account",
                    "value": "0012J00002QQHJ9QAP"
                }]
            },
            "endObject": {
                "type": "configuration/entityTypes/Contact",
                "crosswalks": [{
                    "type": "configuration/sources/WI",
                    "sourceTable": "contact",
                    "value": "0032J00002AABBCCDD"
                }]
            }
        }])
        
        # Create a relationship using minimal crosswalks (with defaults)
        create_relationships([{
            "type": "configuration/relationTypes/AccountToContact",
            "startObject": {
                "type": "configuration/entityTypes/Account",
                "crosswalks": [{}]  # Uses defaults: type="configuration/sources/Reltio", sourceTable="", value=UUID4
            },
            "endObject": {
                "type": "configuration/entityTypes/Contact",
                "crosswalks": [{}]  # Uses defaults: type="configuration/sources/Reltio", sourceTable="", value=UUID4
            }
        }])
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = CreateRelationsRequest(
                relations=relations,
                options=options,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in create_relationships: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        # Construct URL 
        url = get_reltio_url("relations", "api", request.tenant_id)
        
        # Prepare query parameters as a dictionary
        params = {}
        if request.options:
            params["options"] = request.options
        
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
        
        # Prepare the payload - convert Pydantic models to dict
        payload = []
        for relation in request.relations:
            relation_dict = {
                "type": relation.type,
                "startObject": {
                    "type": relation.startObject.type
                },
                "endObject": {
                    "type": relation.endObject.type
                }
            }
            
            # Add startObject details
            if relation.startObject.objectURI:
                relation_dict["startObject"]["objectURI"] = relation.startObject.objectURI
            if relation.startObject.crosswalks:
                startObject_crosswalks = []
                for cw in relation.startObject.crosswalks:
                    cw_dict = {"type": cw.type, "value": cw.value}
                    if cw.sourceTable and cw.sourceTable.strip():  # Only include if not empty
                        cw_dict["sourceTable"] = cw.sourceTable
                    startObject_crosswalks.append(cw_dict)
                relation_dict["startObject"]["crosswalks"] = startObject_crosswalks
            
            # Add endObject details  
            if relation.endObject.objectURI:
                relation_dict["endObject"]["objectURI"] = relation.endObject.objectURI
            if relation.endObject.crosswalks:
                endObject_crosswalks = []
                for cw in relation.endObject.crosswalks:
                    cw_dict = {"type": cw.type, "value": cw.value}
                    if cw.sourceTable and cw.sourceTable.strip():  # Only include if not empty
                        cw_dict["sourceTable"] = cw.sourceTable
                    endObject_crosswalks.append(cw_dict)
                relation_dict["endObject"]["crosswalks"] = endObject_crosswalks
                
            # Add relation crosswalks if provided
            if relation.crosswalks:
                relation_crosswalks = []
                for cw in relation.crosswalks:
                    cw_dict = {"type": cw.type, "value": cw.value}
                    if cw.sourceTable and cw.sourceTable.strip():  # Only include if not empty
                        cw_dict["sourceTable"] = cw.sourceTable
                    relation_crosswalks.append(cw_dict)
                relation_dict["crosswalks"] = relation_crosswalks
            
            payload.append(relation_dict)
        
        # Make the API request
        try:
            result = http_request(url, method='POST', headers=headers, data=payload, params=params if params else None)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "SERVER_ERROR",
                "Failed to create relationships in Reltio API"
            )
        
        # Log activity
        try:
            relation_types = [rel.type.split('/')[-1] for rel in request.relations]
            relationship_summary = f"{len(request.relations)} relationship(s) of types: {', '.join(set(relation_types))}"
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.RELATIONSHIP_CREATE.value,
                client_type=ACTIVITY_CLIENT,
                description=f"create_relationships_tool : Successfully created {relationship_summary}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for create_relationships: {str(log_error)}")
        
        # Return the result as YAML for better readability
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in create_relationships: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while creating relationships"
        )


async def delete_relation(relation_id: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Delete a relation object from a tenant using the DELETE operation
    
    Args:
        relation_id (str): The ID of the relation to delete
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the result of the delete operation with:
        - status: result of operation; possible values are "OK" or "failed"  
        - error: if object can't be deleted for some reason. Contains details of the problem.
    
    Raises:
        Exception: If there's an error deleting the relation
    
    Examples:
        # Delete relation by ID  
        delete_relation("r1", "tenant_id")
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = RelationIdRequest(
                relation_id=relation_id,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in delete_relation: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid relation ID format: {str(e)}"
            )
        
        # Construct URL with validated relation ID
        url = get_reltio_url(f"relations/{request.relation_id}", "api", request.tenant_id)
        
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
        
        # Make the DELETE request
        try:
            result = http_request(url, method='DELETE', headers=headers)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check if it's a 404 error (relation not found)
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Relation with ID {request.relation_id} not found"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to delete relation from Reltio API"
            )
        
        # Return the result as YAML for better readability
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in delete_relation: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while deleting the relation"
        )


async def get_entity_relations(entity_id: str, entity_types: list, sort_by: str = "", 
                               in_relations: list = None, out_relations: list = None,
                               offset: int = 0, max: int = 10, show_relationship: str = "",
                               show_entity: str = "", next_entry: str = "",
                               groups: list = None, filter: str = "",
                               relation_filter: str = "", return_objects: bool = False,
                               return_dates: bool = False, return_labels: bool = True,
                               id: str = "", suggested: list = None,
                               limit_credits_consumption: bool = False,
                               return_data_anyway: bool = False,
                               tenant_id: str = RELTIO_TENANT) -> dict:
    """Get entity connections/relations using Reltio connections API
    
    Args:
        entity_id (str): The ID of the entity to get connections for
        entity_types (list): List of entity types that will be returned (mandatory)
        sort_by (str): How to sort the results (optional)
        in_relations (list): Types of relations that have endEntity equal to current entity (optional)
        out_relations (list): Types of relations that have startEntity equal to current entity (optional)
        offset (int): First element in the request (default = 0)
        max (int): Maximum numbers of elements (default = 10)
        show_relationship (str): URI of relationship to show specific page of connections (optional)
        show_entity (str): URI of connected entity to show specific page of connections (optional)
        next_entry (str): Next connection specification if connection path does not equal one hop (optional)
        groups (list): List of groups types that have entities as a member (optional)
        filter (str): Enables filtering of entities using a condition (optional)
        relation_filter (str): Enables filtering relations with searchRelationsWithFilter option (optional)
        return_objects (bool): Whether the whole object data would be put into result (default = false)
        return_dates (bool): Whether the activeness attributes would be put into result (default = false)
        return_labels (bool): Whether the entityLabel and relationLabel fields are contained in the response (default = true)
        id (str): Identifier for this connections group (optional)
        suggested (list): Other buckets from this connections request that must be mixed into this bucket (optional)
        limit_credits_consumption (bool): Whether to limit credits consumption (default = false)
        return_data_anyway (bool): Whether to return data anyway (default = false)
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the entity connections/relations
    
    Raises:
        Exception: If there's an error getting the entity relations
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = GetEntityRelationsRequest(
                entity_id=entity_id,
                entity_types=entity_types,
                sort_by=sort_by,
                in_relations=in_relations,
                out_relations=out_relations,
                offset=offset,
                max=max,
                show_relationship=show_relationship,
                show_entity=show_entity,
                next_entry=next_entry,
                groups=groups,
                filter=filter,
                relation_filter=relation_filter,
                return_objects=return_objects,
                return_dates=return_dates,
                return_labels=return_labels,
                id=id,
                suggested=suggested,
                limit_credits_consumption=limit_credits_consumption,
                return_data_anyway=return_data_anyway,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in get_entity_relations: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        # Construct URL 
        url = get_reltio_url(f"entities/{request.entity_id}/_connections", "api", request.tenant_id)
        
        # Prepare query parameters as a dictionary
        params = {}
        if request.limit_credits_consumption:
            params["limitCreditsConsumption"] = "true"
        if request.return_data_anyway:
            params["returnDataAnyway"] = "true"
        
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
        
        # Prepare the connection group object
        connection_group = {}
        
        # Add required entityTypes
        connection_group["entityTypes"] = request.entity_types
        
        # Add optional parameters if provided
        if request.sort_by and request.sort_by.strip():
            connection_group["sortBy"] = request.sort_by
        if request.in_relations:
            connection_group["inRelations"] = request.in_relations
        if request.out_relations:
            connection_group["outRelations"] = request.out_relations
        if request.offset > 0:
            connection_group["offset"] = request.offset
        if request.max != 10:  # Only include if different from default
            connection_group["max"] = request.max
        if request.show_relationship and request.show_relationship.strip():
            connection_group["showRelationship"] = request.show_relationship
        if request.show_entity and request.show_entity.strip():
            connection_group["showEntity"] = request.show_entity
        if request.next_entry and request.next_entry.strip():
            connection_group["nextEntry"] = request.next_entry
        if request.groups:
            connection_group["groups"] = request.groups
        if request.filter and request.filter.strip():
            connection_group["filter"] = request.filter
        if request.relation_filter and request.relation_filter.strip():
            connection_group["relationFilter"] = request.relation_filter
        if request.return_objects != False:  # Only include if different from default
            connection_group["returnObjects"] = request.return_objects
        if request.return_dates != False:  # Only include if different from default
            connection_group["returnDates"] = request.return_dates
        if request.return_labels != True:  # Only include if different from default
            connection_group["returnLabels"] = request.return_labels
        if request.id and request.id.strip():
            connection_group["id"] = request.id
        if request.suggested:
            connection_group["suggested"] = request.suggested
        
        # Prepare the payload as array with connection group object
        payload = [connection_group]
        
        # Make the API request
        try:
            result = http_request(url, method='POST', headers=headers, data=payload, params=params if params else None)
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
                "Failed to retrieve entity relations from Reltio API"
            )
        
        # Log activity
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.RELATIONSHIP_SEARCH.value,
                client_type=ACTIVITY_CLIENT,
                description=f"get_entity_relations_tool : Successfully fetched entity relations for entity {entity_id}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_entity_relations: {str(log_error)}")
        
        # Return the result as YAML for better readability
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in get_entity_relations: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while retrieving entity relations"
        )


async def search_relations(filter: str = "", select: str = "", max: int = 10, offset: int = 0,
                          sort: str = "", order: str = "asc", options: str = "", 
                          activeness: str = "active", tenant_id: str = RELTIO_TENANT) -> dict:
    """Search for relationships in a tenant using the Relation Search API
    
    This function searches for relationships by their start and/or end objects, attribute values, 
    tags, or type. It only works when relations indexing is enabled for the tenant.
    
    Args:
        filter (str): Enables relations filtering by a condition. Format: filter=({Condition Type}[AND/OR {Condition Type}]*)
        select (str): Comma-separated list of properties from relation structure to return
        max (int): Maximum number of relations to return (default=10, max=10000)
        offset (int): Starting element in result set for pagination (default=0)
        sort (str): Attribute or list of attributes for ordering (e.g., 'uri', 'uri&startObject')
        order (str): Sort order: 'asc' (ascending) or 'desc' (descending)
        options (str): Comma-separated options: nonOvOnly, ovOnly, searchByOv, sendHidden, resolveMergedEntities
        activeness (str): Activeness filter: 'active' (default), 'all', or 'not_active'
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the search results as YAML
    
    Raises:
        Exception: If there's an error searching relations
        
    Examples:
        # Search for all relationships of a specific entity
        search_relations(filter="(equals(startObject,'entities/1') or equals(endObject,'entities/1'))")
        
        # Search for relationships by type
        search_relations(filter="(equals(type,'configuration/relationTypes/Spouse'))")
        
        # Search with pagination and sorting
        search_relations(
            filter="(equals(startObject,'entities/2'))",
            max=20,
            offset=0,
            sort="uri",
            order="desc"
        )
        
        # Search with specific fields selection
        search_relations(
            filter="(equals(type,'configuration/relationTypes/HasAddress'))",
            select="uri,startObject,endObject",
            max=5
        )
    """
    try:
        # Validate inputs using Pydantic model
        try:
            request = RelationSearchRequest(
                filter=filter,
                select=select,
                max=max,
                offset=offset,
                sort=sort,
                order=order,
                options=options,
                activeness=activeness,
                tenant_id=tenant_id
            )
        except ValueError as e:
            logger.warning(f"Validation error in search_relations: {str(e)}")
            return create_error_response(
                "VALIDATION_ERROR",
                f"Invalid input parameters: {str(e)}"
            )
        
        # Construct URL for relation search
        url = get_reltio_url("relations/_search", "api", request.tenant_id)
        
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
        
        # Prepare the request body
        request_body = request.model_dump(
            exclude={"tenant_id"},
            exclude_none=True,  # Exclude None values
            exclude_unset=False  # Include fields with default values
        )
                
        # Make the API request using POST method as recommended by Reltio
        try:
            result = http_request(url, method='POST', headers=headers, data=request_body)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            
            # Check for specific error conditions
            if "404" in str(e):
                return create_error_response(
                    "RESOURCE_NOT_FOUND",
                    "Relations search endpoint not found or relations indexing is not enabled for this tenant"
                )
            elif "400" in str(e):
                return create_error_response(
                    "BAD_REQUEST",
                    "Invalid search parameters or relations indexing is not enabled for this tenant"
                )
            
            return create_error_response(
                "SERVER_ERROR",
                "Failed to search relations from Reltio API"
            )
        
        # Log activity
        try:
            search_summary = f"filter: {request.filter[:50]}..." if request.filter and len(request.filter) > 50 else f"filter: {request.filter}"
            if not request.filter:
                search_summary = "all relations"
            
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.RELATIONSHIP_SEARCH.value,
                client_type=ACTIVITY_CLIENT,
                description=f"search_relations_tool : Successfully searched relations with {search_summary}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for search_relations: {str(log_error)}")
        
        # Process the result to simplify attributes if present
        if isinstance(result, list):
            for relation in result:
                if isinstance(relation, dict) and "attributes" in relation:
                    relation["attributes"] = simplify_reltio_attributes(relation["attributes"])
        elif isinstance(result, dict) and "attributes" in result:
            result["attributes"] = simplify_reltio_attributes(result["attributes"])
        
        # Return the result as YAML for better readability
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in search_relations: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while searching relations"
        )

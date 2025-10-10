import logging
from typing import List, Dict, Any, Optional
import enum

from src.constants import RELEVANCE_SCORE_NOT_AVAILABLE

# Configure logging
logger = logging.getLogger("mcp.server.reltio")
   
def simplify_reltio_attributes(attributes_dict, preserve_metadata=False):
    """
    Simplifies a Reltio-style attributes dictionary by extracting 'value' fields,
    preserving the nested structure and handling multiple values.
    
    Args:
        attributes_dict: The attributes dictionary from Reltio API
        preserve_metadata: If True, preserve full attribute metadata including uri, type, ov, lookupCode, etc.
                          If False, only extract value fields (default behavior for backward compatibility)
    """
    if preserve_metadata:
        # Return full attribute details without simplification
        return attributes_dict
    
    # Original simplification logic
    result = {}
    for key, value_list in attributes_dict.items():
        if isinstance(value_list, list) and value_list:
            simplified_list = []
            for item in value_list:
                if isinstance(item, dict) and 'value' in item:
                    if isinstance(item['value'], dict):
                        simplified_list.append(simplify_reltio_attributes(item['value'], preserve_metadata))
                    else:
                        simplified_list.append(item['value'])
            
            if not simplified_list:
                continue

            if len(simplified_list) == 1:
                result[key] = simplified_list[0]
            else:
                result[key] = simplified_list
    return result

def slim_crosswalks(cws: List[Dict[str, Any]], preserve_details=False) -> List[Dict[str, Any]]:
    """
    Process crosswalks data based on preserve_details flag.
    
    Args:
        cws: List of crosswalk dictionaries from Reltio API
        preserve_details: If True, preserve full crosswalk details including uri, attributes, singleAttributeUpdateDates, etc.
                         If False, keep only id, type, value, createDate (default behavior for backward compatibility)
    """
    if preserve_details:
        # Return full crosswalk details without simplification
        return [cw for cw in cws if isinstance(cw, dict)]
    
    # Original slim logic
    out: List[Dict[str, Any]] = []
    for cw in cws:
        if not isinstance(cw, dict):
            continue
        
        # Extract ID from URI
        uri = cw.get("uri", "")
        if uri and "/" in uri:
            id_value = uri.rsplit("/", 1)[-1]
        else:
            id_value = cw.get("id")
        
        # Extract type (last part after /)
        type_value = cw.get("type", "")
        if type_value and "/" in type_value:
            type_value = type_value.rsplit("/", 1)[-1]
        # Extract createDate with fallbacks
        create_date = cw.get("createDate") or cw.get("createTime") or cw.get("createdTime")
        
        out.append({
            "id": id_value,
            "type": type_value,
            "value": cw.get("value"),
            "createDate": create_date,
        })
    return out


def format_entity_matches(matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {d["object"]["uri"]:{
        "matchRules":d["matchRules"],
        "createdTime":d["createdTime"],
        "relevance":d.get("relevance",RELEVANCE_SCORE_NOT_AVAILABLE),
        "label":d.get("label",None)} for d in matches}

def format_unified_entity_matches(matches: List[Dict[str, Any]], match_entities: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format matches for the unified entity with matches tool.
    
    Args:
        matches: List of match objects from _transitiveMatches API
        match_entities: Optional dict of full entity data keyed by entity URI
    
    Returns:
        Dictionary with formatted match data including metadata and optional full entity attributes
    """
    result = {}
    for match in matches:
        entity_uri = match["object"]["uri"]
        match_data = {
            "label": match.get("label"),
            "matchRules": match["matchRules"],
            "relevance": match.get("relevance",RELEVANCE_SCORE_NOT_AVAILABLE),
            "createdTime": match["createdTime"]
        }
        
        # Add full entity attributes if provided
        if match_entities and entity_uri in match_entities:
            entity_data = match_entities[entity_uri]
            match_data["attributes"] = simplify_reltio_attributes(entity_data.get("attributes", {}))
            if "crosswalks" in entity_data:
                match_data["crosswalks"] = slim_crosswalks(entity_data["crosswalks"])
        
        result[entity_uri] = match_data
    
    return result

def create_search_activity_description(filter: str = "", entity_type: str = "", options: str = "") -> dict:
    """
    Create activity log description for search operations.
    
    Args:
        filter (str): The search filter used
        entity_type (str): The entity type being searched
        options (str): Search options used
    
    Returns:
        dict: Activity log description in the required format
    """
    # Build the query string with filter and options
    query_parts = []
    if filter:
        query_parts.append(f"filter={filter}")
    if options:
        query_parts.append(f"options={options}")
    query_string = "&".join(query_parts)
    
    # Create activity log description in the new format
    activity_description = {
        "activity": {
            "query": query_string,
            "uiState": {
                "view": {
                    "searchResultsMode": "table",
                    "entityTypeTab": f"configuration/entityTypes/{entity_type}" if entity_type else None,
                    "tabs": None,
                    "previewPanelMode": None
                },
                "facets": {
                    "type": {
                        "fieldName": "type"
                    }
                },
                "currentTenant": None,
                "searchOptions": {
                    "searchByOv": "searchByOv" in options if options else False,
                    "ovOnly": "ovOnly" in options if options else False
                },
                "keyword": {
                    "value": filter if filter else "",
                    "isRawFilter": True
                },
                "map": None,
                "version": "2.0"
            }
        },
        "version": "2.0"
    }
    
    return activity_description

class ActivityLogLabel(enum.Enum):
    USER_SEARCH="USER_SEARCH"
    USER_PROFILE_VIEW="USER_PROFILE_VIEW"
    ENTITY_UPDATE="ENTITY_CHANGED"
    ENTITY_MERGED="ENTITIES_MERGED"
    ENTITY_UNMERGED="ENTITIES_UNMERGED" 
    ENTITY_MATCH_HISTORY="ENTITY_MATCH_HISTORY"
    ENTITY_MATCH_SCORE="ENTITY_MATCH_SCORE"
    ENTITY_CONFIDENCE_LEVEL="ENTITY_CONFIDENCE_LEVEL"
    ENTITY_TOTAL_MATCHES="ENTITY_TOTAL_MATCHES"
    NOT_MATCHES_SET="NOT_MATCHES_SET"
    POTENTIAL_MATCHES_FOUND="POTENTIAL_MATCHES_FOUND"
    NOT_MATCHES_RESET="NOT_MATCHES_RESET"
    ENTITY_MERGE_TREE_EXPORT="ENTITY_MERGE_TREE_EXPORT"
    RELATIONSHIP_SEARCH="RELATIONSHIP_SEARCH"
    TENANT_METADATA="TENANT_METADATA"
    DATA_MODEL_DEFINITION="DATA_MODEL_DEFINITION"
    ENTITY_TYPE_DEFINITION="ENTITY_TYPE_DEFINITION"
    CHANGE_REQUEST_TYPE_DEFINITION="CHANGE_REQUEST_TYPE_DEFINITION"
    RELATION_TYPE_DEFINITION="RELATION_TYPE_DEFINITION"
    INTERACTION_TYPE_DEFINITION="INTERACTION_TYPE_DEFINITION"
    GRAPH_TYPE_DEFINITION="GRAPH_TYPE_DEFINITION"
    GROUPING_TYPE_DEFINITION="GROUPING_TYPE_DEFINITION"
    TENANT_PERMISSIONS_METADATA="TENANT_PERMISSIONS_METADATA"
    GET_MERGE_ACTIVITIES="GET_MERGE_ACTIVITIES"
    USER_SUMMARY="USER_SUMMARY"
    USER_DETAILS="USER_DETAILS"
    WORKFLOW_TASKS="WORKFLOW_TASKS"
    LOOKUP_LIST="LOOKUP_LIST"
    ENTITY_HOPS="ENTITY_HOPS"
    RELATIONSHIP_CREATE="RELATIONSHIP_CREATE"
    RELATIONSHIP_DELETE="RELATIONSHIP_DELETE"
    USER_INTERACTION="USER_INTERACTION"

import logging
import time

from src.env import RELTIO_SERVER_NAME
from src.util.api import create_error_response

# Configure logging
logger = logging.getLogger("mcp.server.reltio")

async def list_capabilities() -> dict:
    """List all capabilities (resources, tools, and prompts) available in this server
    
    Returns:
        A dictionary containing information about available server capabilities
    
    Raises:
        Exception: If there's an error getting the server capabilities
    """
    try:
        # Build capabilities information
        capabilities = {
            "server_name": RELTIO_SERVER_NAME,
            "tools": [
                {
                    "name": "search_entities_tool",
                    "description": "Search for entities with advanced filtering",
                    "parameters": ["filter", "entity_type", "tenant_id", "max_results", "sort", "order", "select", "options", "activeness", "offset" ]
                },
                {
                    "name": "get_entity_tool",
                    "description": "Get detailed information about a Reltio entity by ID",
                    "parameters": ["entity_id", "tenant_id"]
                },
                {
                    "name": "update_entity_attributes_tool",
                    "description": "Update specific attributes of an entity in Reltio.",
                    "parameters": ["entity_id", "updates", "tenant_id"]
                },
                {
                    "name": "get_entity_match_history_tool",
                    "description": "Find the match history for a specific entity",
                    "parameters": ["entity_id", "tenant_id"]
                },
                {
                    "name": "get_relation_tool",
                    "description": "Get detailed information about a Reltio relation by ID",
                    "parameters": ["relation_id", "tenant_id"]
                },
                {
                    "name": "merge_entities_tool",
                    "description": "Merge multiple entities in Reltio",
                    "parameters": ["entity_ids", "tenant_id"]
                },
                {
                    "name": "reject_entity_match_tool",
                    "description": "Mark an entity as not a match (reject the potential duplicate)",
                    "parameters": ["source_id", "target_id", "tenant_id"]
                },
                {
                    "name": "export_merge_tree_tool",
                    "description": "Export the merge tree for all entities in a specific tenant",
                    "parameters": ["email_id", "tenant_id"]
                },
                {
                    "name": "get_business_configuration_tool",
                    "description": "Get the business configuration for a specific tenant",
                    "parameters": ["tenant_id"]
                },
                {
                    "name": "get_tenant_permissions_metadata_tool",
                    "description": "Get the permissions and security metadata for a specific tenant",
                    "parameters": ["tenant_id"]
                },
                {
                    "name": "get_merge_activities_tool",
                    "description": "Retrieve activity events related to entity merges with flexible filtering options",
                    "parameters": ["timestamp_gt", "event_types", "timestamp_lt", "entity_type", "user", "tenant_id", "offset", "max_results"]
                },
                {
                    "name": "get_tenant_metadata_tool",
                    "description": "Get the tenant metadata details from the business configuration for a specific tenant",
                    "parameters": ["tenant_id"]
                },
                {
                    "name": "get_data_model_definition_tool",
                    "description": "Get complete details about the data model definition from the business configuration for a specific tenant",
                    "parameters": ["object_type", "tenant_id"]
                },
                {
                    "name": "get_entity_type_definition_tool",
                    "description": "Get the entity type definition for a specified entity type from the business configuration of a specific tenant",
                    "parameters": ["entity_type", "tenant_id"]
                },
                {
                    "name": "get_change_request_type_definition_tool",
                    "description": "Get the change request type definition for a specified change request type from the business configuration of a specific tenant",
                    "parameters": ["change_request_type", "tenant_id"]
                },
                {
                    "name": "get_relation_type_definition_tool",
                    "description": "Get the relation type definition for a specified relation type from the business configuration of a specific tenant",
                    "parameters": ["relation_type", "tenant_id"]
                },
                {
                    "name": "get_interaction_type_definition_tool",
                    "description": "Get the interaction type definition for a specified interaction type from the business configuration of a specific tenant",
                    "parameters": ["interaction_type", "tenant_id"]
                },
                {
                    "name": "get_graph_type_definition_tool",
                    "description": "Get the graph type definition for a specified graph type from the business configuration of a specific tenant",
                    "parameters": ["graph_type", "tenant_id"]
                },
                {
                    "name": "get_grouping_type_definition_tool",
                    "description": "Get the grouping type definition for a specified grouping type from the business configuration of a specific tenant",
                    "parameters": ["grouping_type", "tenant_id"]
                },
                {
                    "name": "find_potential_matches_tool",
                    "description": "Unified tool to find all potential matches by match rule, score range, or confidence level",
                    "parameters": ["search_type", "filter", "entity_type", "tenant_id", "max_results", "offset", "search_filters"]
                },
                {
                    "name": "get_potential_matches_stats_tool",
                    "description": "Get the total, entity-level, and match-rule-level counts of potential matches in the tenant",
                    "parameters": ["min_matches", "tenant_id"]
                },
                {
                    "name": "get_entity_with_matches_tool",
                    "description": "Get detailed information about a Reltio entity along with its potential matches",
                    "parameters": ["entity_id", "attributes", "include_match_attributes", "match_attributes", "match_limit", "tenant_id"]
                },
                {
                    "name": "create_entity_tool",
                    "description": "Create one or more entities in a Reltio tenant using the Entities API",
                    "parameters": ["entities", "return_objects", "execute_lca", "tenant_id"]
                },
                {
                    "name": "get_entity_graph_tool",
                    "description": "Get entity graph (hops) for a specific entity with comprehensive filtering and traversal options",
                    "parameters": ["entity_id", "select", "graph_type_uris", "relation_type_uris", "entity_type_uris", "deep", "max_results", "activeness_enabled", "return_inactive", "filter_last_level", "return_data_anyway", "options", "tenant_id"]
                },
                {
                    "name": "get_entity_parents_tool",
                    "description": "Find all parent paths for a given entity, traversing the specified graph types",
                    "parameters": ["entity_id", "graph_type_uris", "select", "options", "tenant_id"]
                },
                {
                    "name": "create_relationships_tool",
                    "description": "Create relationships between entities in Reltio",
                    "parameters": ["relations", "options", "tenant_id"]
                },
                {
                    "name": "delete_relation_tool",
                    "description": "Delete a relation object from a tenant using the DELETE operation",
                    "parameters": ["relation_id", "tenant_id"]
                },
                {
                    "name": "get_entity_relations_tool",
                    "description": "Get entity connections/relations using Reltio connections API",
                    "parameters": ["entity_id", "entity_types", "sort_by", "in_relations", "out_relations", "offset", "max", "show_relationship", "show_entity", "next_entry", "groups", "filter", "relation_filter", "return_objects", "return_dates", "return_labels", "id", "suggested", "limit_credits_consumption", "return_data_anyway", "tenant_id"]
                },
                {
                    "name": "relation_search_tool",
                    "description": "Search for relationships in a tenant using the Relation Search API",
                    "parameters": ["filter", "select", "max", "offset", "sort", "order", "options", "activeness", "tenant_id"]
                },
                {
                    "name": "check_user_activity_tool",
                    "description": "Check if a user has been active in the system within a specified number of days",
                    "parameters": ["username", "days_back", "tenant_id"]
                },
                {
                    "name": "get_entity_interactions_tool",
                    "description": "Get interactions for a Reltio entity by ID",
                    "parameters": ["entity_id", "max", "offset", "order", "sort", "filter", "tenant_id"]
                },
                {
                    "name": "create_interaction_tool",
                    "description": "Create interactions in the Reltio Platform",
                    "parameters": ["interactions", "source_system", "crosswalk_value", "return_objects", "options", "tenant_id"]
                },
                {
                    "name": "rdm_lookups_list_tool",
                    "description": "List lookups based on the given RDM lookup type",
                    "parameters": ["lookup_type", "tenant_id", "max_results", "display_name_prefix"]
                },
                {
                    "name": "get_users_by_role_and_tenant_tool",
                    "description": "Get users by role and tenant",
                    "parameters": ["role", "tenant_id"]
                },
                {
                    "name": "get_users_by_group_and_tenant_tool",
                    "description": "Get users by group and tenant",
                    "parameters": ["group", "tenant_id"]
                },
                {
                    "name": "get_user_workflow_tasks_tool",
                    "description": "Get workflow tasks for a specific user with total count and detailed task information",
                    "parameters": ["assignee", "tenant_id", "offset", "max_results"]
                },
                {
                    "name": "reassign_workflow_task_tool",
                    "description": "Reassign a workflow task to a different user for load balancing and task distribution",
                    "parameters": ["task_id", "assignee", "tenant_id"]
                },
                {
                    "name": "get_possible_assignees_tool",
                    "description": "Get possible assignees for specific tasks or based on filter/exclude criteria",
                    "parameters": ["tenant_id", "tasks", "task_filter", "exclude"]
                },
                {
                    "name": "retrieve_tasks_tool",
                    "description": "Retrieve workflow tasks with comprehensive filtering options",
                    "parameters": ["tenant_id", "assignee", "process_instance_id", "process_type", "process_types", "offset", "max_results", "suspended", "created_by", "priority_class", "order_by", "ascending", "task_type", "created_after", "created_before", "state", "object_uris", "show_task_variables", "show_task_local_variables", "object_filter"]
                },
                {
                    "name": "get_task_details_tool",
                    "description": "Get complete details of a specific workflow task by ID",
                    "parameters": ["task_id", "tenant_id", "show_task_variables", "show_task_local_variables"]
                },
                {
                    "name": "start_process_instance_tool",
                    "description": "Start a process instance in Reltio workflow for any type of change requests created by user",
                    "parameters": ["process_type", "object_uris", "tenant_id", "comment", "variables"]
                },
                {
                    "name": "execute_task_action_tool",
                    "description": "Execute an action on a workflow task",
                    "parameters": ["task_id", "action", "tenant_id", "process_instance_comment"]
                },
                {
                    "name": "unmerge_entity_tool",
                    "description": "Unmerge a contributor entity from a merged entity with optional tree behavior",
                    "parameters": ["origin_entity_id", "contributor_entity_id", "tenant_id", "tree"]
                },
                {
                    "name": "health_check_tool",
                    "description": "Check if the MCP server is healthy",
                    "parameters": []
                },
                {
                    "name": "capabilities_tool",
                    "description": "Display this help information",
                    "parameters": []
                }
            ],
            "prompts": [
                {
                    "name": "duplicate_review",
                    "description": "Helps review potential duplicates for an entity"
                }
            ],
            "example_usage": [
                "search_entities_tool(filter=\"containsWordStartingWith(attributes,'John')\")",
                "search_entities_tool(filter=\"equals(type,'configuration/entityTypes/Individual')\")",
                "get_entity_tool(entity_id='118C6Ujm')",
                "update_entity_attributes_tool(entity_id='118C6Ujm', updates=[{'type': 'UPDATE_ATTRIBUTE', 'uri': 'entities/118C6Ujm/attributes/FirstName/3Z3Tq6BBE', 'newValue': [{'value': 'John'}]}])",
                "get_entity_match_history_tool(entity_id='118C6Ujm')",
                "get_relation_tool(relation_id='relation_id')",
                "find_matches_by_match_score_tool(start_match_score=50, end_match_score=100, entity_type='Individual', tenant_id='tenant_id', max_results=10)",
                "find_matches_by_confidence_tool(confidence_level='High confidence', entity_type='Individual', tenant_id='tenant_id', max_results=10)",
                "merge_entities_tool(entity_ids=['entities/123abc', 'entities/456def'], tenant_id='tenant_id')",
                "reject_entity_match_tool(source_id='123abc', target_id='456def', tenant_id='tenant_id')",
                "export_merge_tree_tool(email_id='dummy.svr@email.com', tenant_id='tenant_id')",
                "get_business_configuration_tool(tenant_id='tenant_id')",
                "get_tenant_permissions_metadata_tool(tenant_id='tenant_id')",
                "get_merge_activities_tool(timestamp_gt=1744191663000, event_types=['ENTITIES_MERGED_MANUALLY'], entity_type='Individual')",
                "get_tenant_metadata_tool(tenant_id='tenant_id')",
                "get_data_model_definition_tool(object_type=['entityTypes'], tenant_id='tenant_id')",
                "get_entity_type_definition_tool(entity_type='configuration/entityTypes/Organization', tenant_id='tenant_id')",
                "get_change_request_type_definition_tool(change_request_type='configuration/changeRequestTypes/default', tenant_id='tenant_id')",
                "get_relation_type_definition_tool(relation_type='configuration/relationTypes/OrganizationIndividual', tenant_id='tenant_id')",
                "get_interaction_type_definition_tool(interaction_type='configuration/interactionTypes/PurchaseOrder', tenant_id='tenant_id')",
                "get_graph_type_definition_tool(graph_type='configuration/graphTypes/Hierarchy', tenant_id='tenant_id')",
                "get_grouping_type_definition_tool(grouping_type='configuration/groupingTypes/Household', tenant_id='tenant_id')",
                "find_potential_matches_tool(search_type='match_rule', filter='BaseRule05', entity_type='Individual', tenant_id='tenant_id', max_results=10)",
                "find_potential_matches_tool(search_type='score', filter='50,100', entity_type='Individual', tenant_id='tenant_id', max_results=10)",
                "find_potential_matches_tool(search_type='confidence', filter='High confidence', entity_type='Individual', tenant_id='tenant_id', max_results=10)",
                "get_potential_matches_stats_tool(min_matches=0, tenant_id='tenant_id')",
                "get_entity_with_matches_tool(entity_id='entity_id', attributes=[], include_match_attributes=True, match_attributes=[], match_limit=5)",
                "create_entity_tool(entities=[{'type': 'configuration/entityTypes/Individual', 'attributes': {'FirstName': [{'value': 'John'}], 'LastName': [{'value': 'Smith'}]}}])",
                "get_entity_graph_tool(entity_id='entity_id', select='label', graph_type_uris='Hierarchy', deep=1)",
                "get_entity_parents_tool(entity_id='e41', graph_type_uris='Hierarchy')",
                "create_relationships_tool(relations=[{'type': 'configuration/relationTypes/OrganizationIndividual', 'startObject': {'type': 'configuration/entityTypes/Organization', 'objectURI': 'entities/e1'}, 'endObject': {'type': 'configuration/entityTypes/Individual', 'objectURI': 'entities/e2'}}])",
                "delete_relation_tool(relation_id='r1', tenant_id='tenant_id')",
                "get_entity_relations_tool(entity_id='0Gs6OmA', entity_types=['configuration/entityTypes/Individual'])",
                "relation_search_tool(filter=\"(equals(startObject,'entities/1'))\")",
                "check_user_activity_tool(username='john.doe', days_back=7, tenant_id='tenant_id')",
                "get_entity_interactions_tool(entity_id='entity_id', max=50, offset=0)",
                "create_interaction_tool(interactions=[{'type': 'configuration/interactionTypes/Email', 'attributes': {'DateEmailSent': [{'value': '2025-01-02'}]}, 'members': {'Individual': {'type': 'configuration/interactionTypes/Email/memberTypes/Individual', 'members': [{'objectURI': 'entities/0U3rzjF'}]}}}])",
                "rdm_lookups_list_tool(lookup_type='rdm/lookupTypes/CountryCode', tenant_id='tenant_id', max_results=10)",
                "get_users_by_role_and_tenant_tool(role='ROLE_REVIEWER', tenant_id='tenant_id')",
                "get_users_by_group_and_tenant_tool(group='GROUP_LOCAL_RO_ALL', tenant_id='tenant_id')",
                "get_user_workflow_tasks_tool(assignee='user.name', tenant_id='tenant_id', offset=0, max_results=10)",
                "reassign_workflow_task_tool(task_id='250740924', assignee='new.user', tenant_id='tenant_id')",
                "get_possible_assignees_tool(tenant_id='tenant_id', tasks=['23173985'])",
                "retrieve_tasks_tool(tenant_id='tenant_id', assignee='user.name', max_results=10)",
                "get_task_details_tool(task_id='9757836', tenant_id='tenant_id')",
                "start_process_instance_tool(process_type='dataChangeRequestReview', object_uris=['changeRequests/123', 'entities/123'], tenant_id='tenant_id')",
                "execute_task_action_tool(task_id='task123', action='Approve', tenant_id='tenant_id')",
                "unmerge_entity_tool(origin_entity_id='entity1', contributor_entity_id='entity2', tenant_id='tenant_id', tree=False)",
                "health_check_tool()",
                "capabilities_tool()"
            ]
        }
        
        return capabilities
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in list_capabilities: {str(e)}")
        
        # Return a sanitized error response
        return create_error_response(
            "SERVER_ERROR",
            "An unexpected error occurred while listing capabilities"
        )


async def health_check() -> dict:
    """Check if the MCP server is healthy
    
    Returns:
        A dictionary containing the health status with 'status' and 'message' keys
    
    Raises:
        Exception: If there's an error checking the server health
    """
    try:
        return {
            "status": "ok",
            "message": "MCP server is running",
            "timestamp": int(time.time() * 1000)
        }
    except Exception as e:
        logger.error(f"Error in health_check: {str(e)}")
        return create_error_response("ERROR", str(e))

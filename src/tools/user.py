import logging
import yaml
import time
from src.constants import ACTIVITY_CLIENT
from src.env import RELTIO_TENANT, RELTIO_AUTH_SERVER
from src.util.api import (
    http_request, 
    create_error_response, 
    validate_connection_security,
    get_reltio_url
)
from src.util.auth import get_reltio_headers
from src.util.activity_log import ActivityLog
from src.tools.util import ActivityLogLabel

# Configure logging
logger = logging.getLogger("mcp.server.reltio")


async def get_users_summary(tenant_id: str = RELTIO_TENANT) -> dict:
    """Get high-level users summary information
    
    Args:
        tenant_id (str): Tenant ID for activity logging. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing users summary information
    
    Raises:
        Exception: If there's an error getting the users summary
    """
    try:
        # Construct URL for auth server
        url = f"https://{RELTIO_AUTH_SERVER}/oauth/users/tenant/{tenant_id}"
        
        try:
            headers = get_reltio_headers()
            headers['Content-Type'] = 'application/json'
            
            # Validate connection security
            validate_connection_security(url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio Auth API"
            )
        
        try:
            users_data = http_request(url, headers=headers)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "API_REQUEST_ERROR",
                f"Failed to retrieve users: {str(e)}"
            )
        
        # Return only summary information - following get_business_configuration pattern
        response = {}
        response["total_users"] = len(users_data)
        response["enabled_users"] = len([u for u in users_data if u.get("enabled", False)])
        response["external_users"] = len([u for u in users_data if u.get("externalUser", False)])
        response["internal_users"] = len([u for u in users_data if not u.get("externalUser", True)])
        
        # Count users by role (summary stats)
        role_counts = {}
        for user in users_data:
            user_permissions = user.get("userPermissions", {})
            roles = user_permissions.get("roles", {})
            for role in roles.keys():
                role_counts[role] = role_counts.get(role, 0) + 1
        response["role_summary"] = role_counts
        
        # Count users by group (summary stats)
        group_counts = {}
        for user in users_data:
            groups = user.get("groups", [])
            for group in groups:
                group_counts[group] = group_counts.get(group, 0) + 1
        response["group_summary"] = group_counts
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                description=f"get_users_summary_tool : MCP server successfully fetched users summary"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_users_summary: {str(log_error)}")
            
        return yaml.dump(response, sort_keys=False)
        
    except Exception as e:
        logger.error(f"Error in get_users_summary: {str(e)}")
        return create_error_response(
            "INTERNAL_SERVER_ERROR",
            f"An error occurred while retrieving users summary: {str(e)}"
        )


# Utility functions for extracting user information

def get_user_details_util(user_data: dict) -> dict:
    """Utility function to extract specific user details from users data"""
    
    user_info = {
        "username": user_data.get("username", ""),
        "email": user_data.get("email", ""),
        "enabled": user_data.get("enabled", False),
        "externalUser": user_data.get("externalUser", False),
        "userPermissions": user_data.get("userPermissions", {}),
        "groups": user_data.get("groups", []),
        "lastLoginDate": user_data.get("lastLoginDate", None),
        "locale": user_data.get("locale", ""),
        "timezone": user_data.get("timezone", ""),
        "customer": user_data.get("customer", "")
    }
    return user_info


def filter_users_by_role_and_tenant_util(users_data: list, role: str, tenant_id: str) -> list:
    """Utility function to filter users by specific role and tenant"""
    filtered_users = []
    
    for user in users_data:
        user_permissions = user.get("userPermissions", {})
        roles = user_permissions.get("roles", {})
        
        # Check if user has the specified role
        if role in roles:
            # Check if the role includes the specified tenant
            tenant_list = roles[role]
            if tenant_id in tenant_list:
                user_info = {
                    "username": user.get("username", ""),
                    "email": user.get("email", ""),
                    "enabled": user.get("enabled", False),
                    "groups": user.get("groups", []),
                    "lastLoginDate": user.get("lastLoginDate", None),
                    "role": role,
                    "tenant": tenant_id
                }
                filtered_users.append(user_info)
    
    return filtered_users


def filter_users_by_group_util(users_data: list, group: str) -> list:
    """Utility function to filter users by specific group"""
    filtered_users = []
    
    for user in users_data:
        user_groups = user.get("groups") or []
        
        # Check if user has the specified group
        if group in user_groups:
            user_info = {
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "enabled": user.get("enabled", False),
                "groups": user.get("groups") or [],
                "lastLoginDate": user.get("lastLoginDate", None),
                "group": group
            }
            filtered_users.append(user_info)
    
    return filtered_users


async def get_user_details(username: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Get detailed information about a specific user
    
    Args:
        username (str): Username or email to search for
        tenant_id (str): Tenant ID for activity logging. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing the user details
    
    Raises:
        Exception: If there's an error getting the user details
    """
    try:
        url = f"https://{RELTIO_AUTH_SERVER}/oauth/users/{username}"
        
        try:
            headers = get_reltio_headers()
            headers['Content-Type'] = 'application/json'
            validate_connection_security(url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio Auth API"
            )
        
        try:
            users_data = http_request(url, headers=headers)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "API_REQUEST_ERROR",
                f"Failed to retrieve users: {str(e)}"
            )
        
        # Extract specific user details using utility function
        response = get_user_details_util(users_data)
        
        if not response:
            return create_error_response(
                "USER_NOT_FOUND",
                f"User '{username}' not found"
            )
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                description=f"get_user_details_tool : MCP server successfully fetched details for user {username}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_user_details: {str(log_error)}")
        
        return yaml.dump(response, sort_keys=False)
        
    except Exception as e:
        logger.error(f"Error in get_user_details: {str(e)}")
        return create_error_response(
            "INTERNAL_SERVER_ERROR",
            f"An error occurred while retrieving user details: {str(e)}"
        )


async def get_users_by_role_and_tenant(role: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Get users with specific role for a specific tenant
    
    Args:
        role (str): Role to filter by (e.g., 'ROLE_REVIEWER', 'ROLE_READONLY', 'ROLE_USER', 'ROLE_API')
        tenant_id (str): Tenant ID to filter by. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing filtered users information
    
    Raises:
        Exception: If there's an error getting the users by role and tenant
    """
    try:
        url = f"https://{RELTIO_AUTH_SERVER}/oauth/users/tenant/{tenant_id}"
        
        try:
            headers = get_reltio_headers()
            headers['Content-Type'] = 'application/json'
            validate_connection_security(url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio Auth API"
            )
        
        try:
            users_data = http_request(url, headers=headers)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "API_REQUEST_ERROR",
                f"Failed to retrieve users: {str(e)}"
            )
        
        # Filter users by role and tenant
        filtered_users = filter_users_by_role_and_tenant_util(users_data, role, tenant_id)
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.USER_DETAILS.value,
                client_type=ACTIVITY_CLIENT,
                description=f"get_users_by_role_and_tenant_tool : MCP server successfully fetched users with role {role} for tenant {tenant_id}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_users_by_role_and_tenant: {str(log_error)}")
        
        result = {
            "role": role,
            "tenant_id": tenant_id,
            "user_count": len(filtered_users),
            "users": filtered_users
        }
        
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        logger.error(f"Error in get_users_by_role_and_tenant: {str(e)}")
        return create_error_response(
            "INTERNAL_SERVER_ERROR",
            f"An error occurred while retrieving users by role and tenant: {str(e)}"
        )


async def get_users_by_group(group: str, tenant_id: str = RELTIO_TENANT) -> dict:
    """Get users with specific group
    
    Args:
        group (str): Group to filter by (e.g., 'GROUP_LOCAL_RO_ALL', 'GROUP_LOCAL_DA_PT')
        tenant_id (str): Tenant ID for activity logging. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing filtered users information
    
    Raises:
        Exception: If there's an error getting the users by group
    """
    try:
        url = f"https://{RELTIO_AUTH_SERVER}/oauth/users/tenant/{tenant_id}"
        
        try:
            headers = get_reltio_headers()
            headers['Content-Type'] = 'application/json'
            validate_connection_security(url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio Auth API"
            )
        
        try:
            users_data = http_request(url, headers=headers)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "API_REQUEST_ERROR",
                f"Failed to retrieve users: {str(e)}"
            )
        
        # Filter users by group
        filtered_users = filter_users_by_group_util(users_data, group)
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                label=ActivityLogLabel.USER_DETAILS.value,
                client_type=ACTIVITY_CLIENT,
                description=f"get_users_by_group_tool : MCP server successfully fetched users with group {group}"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for get_users_by_group: {str(log_error)}")
        
        result = {
            "group": group,
            "user_count": len(filtered_users),
            "users": filtered_users
        }
        
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        logger.error(f"Error in get_users_by_group: {str(e)}")
        return create_error_response(
            "INTERNAL_SERVER_ERROR",
            f"An error occurred while retrieving users by group: {str(e)}"
        )


async def check_user_activity(username: str, days_back: int = 7, tenant_id: str = RELTIO_TENANT) -> dict:
    """Check if a user has been active in the system within a specified number of days
    
    Args:
        username (str): Username to check for activity
        days_back (int): Number of days to look back for activity. Defaults to 7 days.
        tenant_id (str): Tenant ID for the Reltio environment. Defaults to RELTIO_TENANT env value.
    
    Returns:
        A dictionary containing activity status and details
    
    Raises:
        Exception: If there's an error checking user activity
    """
    try:
        # Calculate timestamp for days_back (Unix timestamp in milliseconds)
        current_time = int(time.time() * 1000)  # Current time in milliseconds
        days_back_ms = days_back * 24 * 60 * 60 * 1000  # Convert days to milliseconds
        timestamp_threshold = current_time - days_back_ms
        
        # Build the complex filter for user activities
        activity_types = [
            "startsWith(label, 'USER_LOGIN')",
            "startsWith(label, 'COMMENT_ADDED')",
            "startsWith(label, 'COMMENT_DELETED')",
            "startsWith(label, 'COMMENT_UPDATED')",
            "equals(items.data.type, NOT_MATCHES_SET)",
            "equals(items.data.type, NOT_MATCHES_RESET)",
            "equals(items.data.type, POTENTIAL_MATCHES_FOUND)",
            "equals(items.data.type, POTENTIAL_MATCHES_REMOVED)",
            "equals(items.data.type, ENTITY_CREATED)",
            "equals(items.data.type, ENTITIES_MERGED_MANUALLY)",
            "equals(items.data.type, ENTITY_REMOVED)",
            "equals(items.data.type, ENTITIES_SPLITTED)",
            "equals(items.data.type, ENTITY_CHANGED)",
            "startsWith(label, 'USER_PROFILE_VIEW')",
            "equals(items.data.type, RELATIONSHIP_CREATED)",
            "equals(items.data.type, RELATIONSHIP_REMOVED)",
            "equals(items.data.type, RELATIONSHIP_CHANGED)",
            "startsWith(label, 'USER_SEARCH')"
        ]
        
        # Combine all activity filters with OR
        activity_filter = " or ".join(activity_types)
        
        # Build complete filter
        complete_filter = (
            f"(equals(user, '{username}')) and "
            f"({activity_filter}) and "
            f"(gte(timestamp, {timestamp_threshold})) and "
            f"(not equals(user, 'collaboration-service'))"
        )
        
        # Construct URL with filter parameters
        base_url = get_reltio_url("activities", "api", tenant_id)
        params = {
            "filter": complete_filter,
            "max": 1,
            "offset": 0
        }
        
        try:
            headers = get_reltio_headers()
            headers['Content-Type'] = 'application/json'
            validate_connection_security(base_url, headers)
        except Exception as e:
            logger.error(f"Authentication or security error: {str(e)}")
            return create_error_response(
                "AUTHENTICATION_ERROR",
                "Failed to authenticate with Reltio API"
            )
        
        try:
            activities_response = http_request(base_url, params=params, headers=headers)
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return create_error_response(
                "API_REQUEST_ERROR",
                f"Failed to retrieve user activities: {str(e)}"
            )
        
        # Determine if user is active based on response
        is_active = len(activities_response) > 0
        
        # Build response
        result = {
            "username": username,
            "days_checked": days_back,
            "timestamp_threshold": timestamp_threshold,
            "is_active": is_active,
            "activity_found": len(activities_response),
            "last_activity": activities_response[0] if activities_response else None
        }
        
        try:
            await ActivityLog.execute_and_log_activity(
                tenant_id=tenant_id,
                description=f"check_user_activity_tool : MCP server checked activity for user {username} (active: {is_active})"
            )
        except Exception as log_error:
            logger.error(f"Activity logging failed for check_user_activity: {str(log_error)}")
        
        return yaml.dump(result, sort_keys=False)
        
    except Exception as e:
        logger.error(f"Error in check_user_activity: {str(e)}")
        return create_error_response(
            "INTERNAL_SERVER_ERROR",
            f"An error occurred while checking user activity: {str(e)}"
        )


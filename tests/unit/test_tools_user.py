import pytest
import yaml
from unittest.mock import patch, MagicMock
from src.tools.user import (
    get_users_summary,
    get_user_details,
    get_users_by_role_and_tenant,
    get_users_by_group,
    check_user_activity
)

TENANT_ID = "test-tenant"
USERNAME = "testuser"
ROLE = "admin"
GROUP = "developers"
DAYS_BACK = 7

# Mock user data for testing
MOCK_USERS_DATA = [
    {
        "username": "user1",
        "enabled": True,
        "externalUser": False,
        "userPermissions": {
            "roles": {
                "admin": ["tenant1", "tenant2"],
                "user": ["tenant1"]
            }
        },
        "groups": ["developers", "admins"]
    },
    {
        "username": "user2",
        "enabled": True,
        "externalUser": True,
        "userPermissions": {
            "roles": {
                "user": ["tenant2"],
                "admin": []
            }
        },
        "groups": ["users"]
    },
    {
        "username": "user3",
        "enabled": False,
        "externalUser": False,
        "userPermissions": {
            "roles": {
                "admin": ["tenant1"],
                "user": ["tenant1", "tenant2"]
            }
        },
        "groups": ["developers"]
    }
]

MOCK_SINGLE_USER = {
    "username": "user1",
    "email": "user1@example.com",
    "enabled": True,
    "externalUser": False,
    "userPermissions": {"roles": {"admin": ["tenant1"], "user": ["tenant2"]}},
    "groups": ["developers"],
    "lastLoginDate": "2024-01-01T10:00:00Z",
    "locale": "en-US",
    "timezone": "UTC",
    "customer": "cust1"
}

MOCK_ACTIVITY_DATA = [
    {
        "timestamp": "2024-01-01T10:00:00Z",
        "action": "login",
        "details": "User logged in"
    },
    {
        "timestamp": "2024-01-02T15:30:00Z",
        "action": "search",
        "details": "User performed search"
    }
]

MOCK_EMPTY_ACTIVITY_DATA = []


@pytest.mark.asyncio
class TestGetUsersSummary:

    @patch("src.tools.user.http_request")
    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    @patch("src.tools.user.ActivityLog.execute_and_log_activity")
    async def test_get_users_summary_success(self, mock_log, mock_validate, mock_headers, mock_request):
        """Test successful users summary retrieval"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_USERS_DATA
        mock_log.return_value = MOCK_USERS_DATA
        
        result = await get_users_summary(TENANT_ID)
        
        # Parse YAML result
        parsed_result = yaml.safe_load(result)
        
        assert isinstance(parsed_result, dict)
        assert parsed_result["total_users"] == 3
        assert parsed_result["enabled_users"] == 2
        assert parsed_result["external_users"] == 1
        assert parsed_result["internal_users"] == 2
        assert parsed_result["role_summary"]["admin"] == 3
        assert parsed_result["role_summary"]["user"] == 3
        assert parsed_result["group_summary"]["developers"] == 2
        assert parsed_result["group_summary"]["admins"] == 1
        
        mock_request.assert_called_once()
        mock_log.assert_called_once()

    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    async def test_get_users_summary_auth_error(self, mock_validate, mock_headers):
        """Test authentication error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_validate.side_effect = Exception("Auth failed")
        
        result = await get_users_summary(TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.user.http_request")
    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    async def test_get_users_summary_api_error(self, mock_validate, mock_headers, mock_request):
        """Test API request error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.side_effect = Exception("API failed")
        
        result = await get_users_summary(TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"

    @patch("src.tools.user.http_request")
    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    @patch("src.tools.user.ActivityLog.execute_and_log_activity")
    async def test_get_users_summary_empty_data(self, mock_log, mock_validate, mock_headers, mock_request):
        """Test users summary with empty data"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = []
        mock_log.return_value = []
        
        result = await get_users_summary(TENANT_ID)
        
        parsed_result = yaml.safe_load(result)
        assert parsed_result["total_users"] == 0
        assert parsed_result["enabled_users"] == 0


@pytest.mark.asyncio
class TestGetUserDetails:

    @patch("src.tools.user.http_request")
    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    @patch("src.tools.user.ActivityLog.execute_and_log_activity")
    async def test_get_user_details_success(self, mock_log, mock_validate, mock_headers, mock_request):
        """Test successful user details retrieval"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_SINGLE_USER
        mock_log.return_value = None
        
        result = await get_user_details(USERNAME, TENANT_ID)
        
        # Parse YAML result
        parsed_result = yaml.safe_load(result)
        
        assert isinstance(parsed_result, dict)
        assert parsed_result["username"] == MOCK_SINGLE_USER["username"]
        assert parsed_result["enabled"] == MOCK_SINGLE_USER["enabled"]
        assert parsed_result["externalUser"] == MOCK_SINGLE_USER["externalUser"]
        assert "admin" in parsed_result["userPermissions"]["roles"]
        assert "developers" in parsed_result["groups"]
        
        mock_request.assert_called_once()
        mock_log.assert_called_once()

    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    async def test_get_user_details_auth_error(self, mock_validate, mock_headers):
        """Test authentication error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_validate.side_effect = Exception("Auth failed")
        
        result = await get_user_details(USERNAME, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.user.http_request")
    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    async def test_get_user_details_api_error(self, mock_validate, mock_headers, mock_request):
        """Test API request error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.side_effect = Exception("API failed")
        
        result = await get_user_details(USERNAME, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


@pytest.mark.asyncio
class TestGetUsersByRoleAndTenant:

    @patch("src.tools.user.http_request")
    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    @patch("src.tools.user.ActivityLog.execute_and_log_activity")
    async def test_get_users_by_role_and_tenant_success(self, mock_log, mock_validate, mock_headers, mock_request):
        """Test successful users by role and tenant retrieval"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_USERS_DATA
        mock_log.return_value = None
        
        result = await get_users_by_role_and_tenant(ROLE, TENANT_ID)
        
        parsed_result = yaml.safe_load(result)
        assert isinstance(parsed_result, dict)
        assert "users" in parsed_result
        assert parsed_result["role"] == ROLE
        assert parsed_result["tenant_id"] == TENANT_ID
        mock_request.assert_called_once()

    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    async def test_get_users_by_role_and_tenant_auth_error(self, mock_validate, mock_headers):
        """Test authentication error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_validate.side_effect = Exception("Auth failed")
        
        result = await get_users_by_role_and_tenant(ROLE, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
class TestGetUsersByGroup:

    @patch("src.tools.user.http_request")
    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    @patch("src.tools.user.ActivityLog.execute_and_log_activity")
    async def test_get_users_by_group_success(self, mock_log, mock_validate, mock_headers, mock_request):
        """Test successful users by group retrieval"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_USERS_DATA
        mock_log.return_value = None
        
        result = await get_users_by_group(GROUP, TENANT_ID)
        
        parsed_result = yaml.safe_load(result)
        assert isinstance(parsed_result, dict)
        assert "users" in parsed_result
        assert parsed_result["group"] == GROUP
        mock_request.assert_called_once()

    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    async def test_get_users_by_group_auth_error(self, mock_validate, mock_headers):
        """Test authentication error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_validate.side_effect = Exception("Auth failed")
        
        result = await get_users_by_group(GROUP, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
class TestCheckUserActivity:

    @patch("src.tools.user.http_request")
    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    @patch("src.tools.user.ActivityLog.execute_and_log_activity")
    async def test_check_user_activity_success(self, mock_log, mock_validate, mock_headers, mock_request):
        """Test successful user activity check"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_ACTIVITY_DATA
        mock_log.return_value = None
        
        result = await check_user_activity(USERNAME, DAYS_BACK, TENANT_ID)
        
        parsed_result = yaml.safe_load(result)
        assert isinstance(parsed_result, dict)
        mock_request.assert_called_once()

    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    async def test_check_user_activity_auth_error(self, mock_validate, mock_headers):
        """Test authentication error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_validate.side_effect = Exception("Auth failed")
        
        result = await check_user_activity(USERNAME, DAYS_BACK, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.user.http_request")
    @patch("src.tools.user.get_reltio_headers")
    @patch("src.tools.user.validate_connection_security")
    @patch("src.tools.user.ActivityLog.execute_and_log_activity")
    async def test_check_user_activity_no_activity(self, mock_log, mock_validate, mock_headers, mock_request):
        """Test user activity check with no activity"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_EMPTY_ACTIVITY_DATA
        mock_log.return_value = None
        
        result = await check_user_activity(USERNAME, DAYS_BACK, TENANT_ID)
        
        parsed_result = yaml.safe_load(result)
        assert isinstance(parsed_result, dict)


import pytest
from unittest.mock import patch, MagicMock
import yaml
from src.tools.lookup import rdm_lookups_list

LOOKUP_TYPE = "rdm/lookupTypes/VistaVegetarianOrVegan"
TENANT_ID = "test-tenant"

@pytest.mark.asyncio
class TestRdmLookupsList:
    """Test cases for the rdm_lookups_list function"""
    
    @patch("src.tools.lookup.ActivityLog.execute_and_log_activity")
    @patch("src.tools.lookup.yaml.dump")
    @patch("src.tools.lookup.http_request")
    @patch("src.tools.lookup.validate_connection_security")
    @patch("src.tools.lookup.get_reltio_headers")
    @patch("src.tools.lookup.get_reltio_url")
    @patch("src.tools.lookup.LookupListRequest")
    async def test_rdm_lookups_list_success(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump, mock_activity_log):
        """Test successful lookup list retrieval"""
        # Mock the request model
        mock_request.return_value.lookup_type = LOOKUP_TYPE
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max_results = 10
        mock_request.return_value.display_name_prefix = ""
        
        mock_url.return_value = f"https://reltio.com/lookups/list"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = [
            {"id": "lookup1", "displayName": "Vegetarian", "value": "VEG"},
            {"id": "lookup2", "displayName": "Vegan", "value": "VEGAN"}
        ]
        mock_dump.return_value = "yaml_output"

        result = await rdm_lookups_list(LOOKUP_TYPE, TENANT_ID, 10, "")
        assert result == "yaml_output"
        mock_activity_log.assert_called_once()
        mock_dump.assert_called_once()

    @patch("src.tools.lookup.ActivityLog.execute_and_log_activity")
    @patch("src.tools.lookup.yaml.dump")
    @patch("src.tools.lookup.http_request")
    @patch("src.tools.lookup.validate_connection_security")
    @patch("src.tools.lookup.get_reltio_headers")
    @patch("src.tools.lookup.get_reltio_url")
    @patch("src.tools.lookup.LookupListRequest")
    async def test_rdm_lookups_list_with_prefix(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump, mock_activity_log):
        """Test lookup list retrieval with display name prefix"""
        # Mock the request model
        mock_request.return_value.lookup_type = LOOKUP_TYPE
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max_results = 5
        mock_request.return_value.display_name_prefix = "Veg"
        
        mock_url.return_value = f"https://reltio.com/lookups/list"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = [
            {"id": "lookup1", "displayName": "Vegetarian", "value": "VEG"}
        ]
        mock_dump.return_value = "yaml_output"

        result = await rdm_lookups_list(LOOKUP_TYPE, TENANT_ID, 5, "Veg")
        assert result == "yaml_output"
        mock_activity_log.assert_called_once()
        mock_dump.assert_called_once()

    @patch("src.tools.lookup.ActivityLog.execute_and_log_activity")
    @patch("src.tools.lookup.yaml.dump")
    @patch("src.tools.lookup.http_request")
    @patch("src.tools.lookup.validate_connection_security")
    @patch("src.tools.lookup.get_reltio_headers")
    @patch("src.tools.lookup.get_reltio_url")
    @patch("src.tools.lookup.LookupListRequest")
    async def test_rdm_lookups_list_empty_result(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump, mock_activity_log):
        """Test lookup list retrieval with empty result"""
        # Mock the request model
        mock_request.return_value.lookup_type = LOOKUP_TYPE
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max_results = 10
        mock_request.return_value.display_name_prefix = ""
        
        mock_url.return_value = f"https://reltio.com/lookups/list"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = []
        mock_dump.return_value = "yaml_output"

        result = await rdm_lookups_list(LOOKUP_TYPE, TENANT_ID, 10, "")
        assert result == "yaml_output"
        mock_activity_log.assert_called_once()
        mock_dump.assert_called_once()

    @patch("src.tools.lookup.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.lookup.yaml.dump")
    @patch("src.tools.lookup.http_request")
    @patch("src.tools.lookup.validate_connection_security")
    @patch("src.tools.lookup.get_reltio_headers")
    @patch("src.tools.lookup.get_reltio_url")
    @patch("src.tools.lookup.LookupListRequest")
    async def test_rdm_lookups_list_success_with_activity_log_failure(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump, mock_activity_log):
        """Test successful lookup list retrieval with activity logging failure"""
        # Mock the request model
        mock_request.return_value.lookup_type = LOOKUP_TYPE
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max_results = 10
        mock_request.return_value.display_name_prefix = ""
        
        mock_url.return_value = f"https://reltio.com/lookups/list"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = [
            {"id": "lookup1", "displayName": "Vegetarian", "value": "VEG"}
        ]
        mock_dump.return_value = "yaml_output"

        result = await rdm_lookups_list(LOOKUP_TYPE, TENANT_ID, 10, "")
        assert result == "yaml_output"
        mock_activity_log.assert_called_once()

    @patch("src.tools.lookup.LookupListRequest", side_effect=ValueError("Invalid lookup type"))
    async def test_rdm_lookups_list_validation_error(self, mock_request):
        """Test lookup list retrieval with validation error"""
        result = await rdm_lookups_list("invalid-lookup-type", TENANT_ID, 10, "")
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.lookup.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.lookup.get_reltio_headers")
    @patch("src.tools.lookup.get_reltio_url")
    @patch("src.tools.lookup.LookupListRequest")
    async def test_rdm_lookups_list_authentication_error(self, mock_request, mock_url, mock_headers, mock_validate):
        """Test lookup list retrieval with authentication error"""
        # Mock the request model
        mock_request.return_value.lookup_type = LOOKUP_TYPE
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max_results = 10
        mock_request.return_value.display_name_prefix = ""

        result = await rdm_lookups_list(LOOKUP_TYPE, TENANT_ID, 10, "")
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.lookup.http_request", side_effect=Exception("API error"))
    @patch("src.tools.lookup.validate_connection_security")
    @patch("src.tools.lookup.get_reltio_headers")
    @patch("src.tools.lookup.get_reltio_url")
    @patch("src.tools.lookup.LookupListRequest")
    async def test_rdm_lookups_list_api_error(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        """Test lookup list retrieval with API error"""
        # Mock the request model
        mock_request.return_value.lookup_type = LOOKUP_TYPE
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max_results = 10
        mock_request.return_value.display_name_prefix = ""

        result = await rdm_lookups_list(LOOKUP_TYPE, TENANT_ID, 10, "")
        assert result["error"]["code_key"] == "SERVER_ERROR"

    @patch("src.tools.lookup.LookupListRequest", side_effect=Exception("Unexpected error"))
    async def test_rdm_lookups_list_unexpected_error(self, mock_request):
        """Test lookup list retrieval with unexpected error"""
        result = await rdm_lookups_list(LOOKUP_TYPE, TENANT_ID, 10, "")
        assert result["error"]["code_key"] == "SERVER_ERROR"

    @patch("src.tools.lookup.ActivityLog.execute_and_log_activity")
    @patch("src.tools.lookup.yaml.dump")
    @patch("src.tools.lookup.http_request")
    @patch("src.tools.lookup.validate_connection_security")
    @patch("src.tools.lookup.get_reltio_headers")
    @patch("src.tools.lookup.get_reltio_url")
    @patch("src.tools.lookup.LookupListRequest")
    async def test_rdm_lookups_list_all_lookup_type(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump, mock_activity_log):
        """Test lookup list retrieval with 'all' lookup type"""
        # Mock the request model
        mock_request.return_value.lookup_type = "all"
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max_results = 10
        mock_request.return_value.display_name_prefix = ""
        
        mock_url.return_value = f"https://reltio.com/lookups/list"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = [
            {"id": "lookup1", "displayName": "Vegetarian", "value": "VEG"},
            {"id": "lookup2", "displayName": "Vegan", "value": "VEGAN"}
        ]
        mock_dump.return_value = "yaml_output"

        result = await rdm_lookups_list("all", TENANT_ID, 10, "")
        assert result == "yaml_output"
        mock_activity_log.assert_called_once()
        mock_dump.assert_called_once()


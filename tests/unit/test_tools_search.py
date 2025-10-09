import pytest
from unittest.mock import patch, MagicMock
from src.tools.search import search_entities

@pytest.mark.asyncio
async def test_search_entities_success_with_query_and_type():
    with patch("src.tools.search.EntitySearchRequest") as mock_request, \
         patch("src.tools.search.get_reltio_url") as mock_url, \
         patch("src.tools.search.get_reltio_headers") as mock_headers, \
         patch("src.tools.search.validate_connection_security"), \
         patch("src.tools.search.http_request") as mock_http, \
         patch("src.tools.search.ActivityLog.execute_and_log_activity"), \
         patch("src.tools.search.yaml.dump") as mock_yaml_dump:

        mock_request.return_value = MagicMock(
            filter="containsWordStartingWith(attributes,'John')",
            entity_type="Individual",
            tenant_id="tenant123",
            max_results=10,
            sort="",
            order="asc",
            select="uri,label,attributes",
            options="ovOnly",
            activeness="active",
            offset=0
        )
        mock_url.return_value = "https://reltio.com/entities/_search"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value =[
            {
                "uri": "entities/1",
                "label": "John Doe",
                "attributes": {"FirstName": [{"value": "John"}]}
            }
        ]
        mock_yaml_dump.return_value = "mocked_yaml_output"

        result = await search_entities("containsWordStartingWith(attributes,'John')", "Individual", "tenant123", 10)
        assert result == "mocked_yaml_output"

@pytest.mark.asyncio
async def test_search_entities_validation_error():
    with patch("src.tools.search.EntitySearchRequest", side_effect=ValueError("Invalid params")), \
         patch("src.tools.search.create_error_response") as mock_create_error:

        mock_create_error.return_value = {
            "error": "VALIDATION_ERROR",
            "message": "Invalid input parameters: Invalid params"
        }

        result = await search_entities("bad query")
        assert result["error"] == "VALIDATION_ERROR"

@pytest.mark.asyncio
async def test_search_entities_authentication_error():
    with patch("src.tools.search.EntitySearchRequest") as mock_request, \
         patch("src.tools.search.get_reltio_url"), \
         patch("src.tools.search.get_reltio_headers", side_effect=Exception("auth failed")), \
         patch("src.tools.search.create_error_response") as mock_create_error:

        mock_request.return_value = MagicMock(
            filter="containsWordStartingWith(attributes,'John')",
            entity_type="Individual",
            tenant_id="tenant123",
            max_results=10
        )
        mock_create_error.return_value = {
            "error": "AUTHENTICATION_ERROR",
            "message": "Failed to authenticate with Reltio API"
        }

        result = await search_entities("containsWordStartingWith(attributes,'John')", "Individual", "tenant123", 10)
        assert result["error"] == "AUTHENTICATION_ERROR"

@pytest.mark.asyncio
async def test_search_entities_api_failure():
    with patch("src.tools.search.EntitySearchRequest") as mock_request, \
         patch("src.tools.search.get_reltio_url"), \
         patch("src.tools.search.get_reltio_headers"), \
         patch("src.tools.search.validate_connection_security"), \
         patch("src.tools.search.http_request", side_effect=Exception("API failed")), \
         patch("src.tools.search.create_error_response") as mock_create_error:

        mock_request.return_value = MagicMock(
            filter="john",
            entity_type="Individual",
            tenant_id="tenant123",
            max_results=10
        )
        mock_create_error.return_value = {
            "error": "SERVER_ERROR",
            "message": "Failed to retrieve search results from Reltio API"
        }

        result = await search_entities("containsWordStartingWith(attributes,'John')", "Individual", "tenant123", 10)
        assert result["error"] == "SERVER_ERROR"

@pytest.mark.asyncio
async def test_search_entities_unexpected_error():
    with patch("src.tools.search.EntitySearchRequest", side_effect=Exception("Test error")), \
         patch("src.tools.search.create_error_response") as mock_create_error:

        mock_create_error.return_value = {
            "error": "SERVER_ERROR",
            "message": "An unexpected error occurred while processing your request"
        }

        result = await search_entities("test")
        assert result["error"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestSearchEntitiesComprehensive:
    """Comprehensive test suite for search_entities function"""

    @patch("src.tools.search.ActivityLog.execute_and_log_activity")
    @patch("src.tools.search.yaml.dump")
    @patch("src.tools.search.simplify_reltio_attributes")
    @patch("src.tools.search.http_request")
    @patch("src.tools.search.validate_connection_security")
    @patch("src.tools.search.get_reltio_headers")
    @patch("src.tools.search.get_reltio_url")
    @patch("src.tools.search.EntitySearchRequest")
    async def test_search_entities_with_attributes_processing(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_simplify, mock_dump, mock_activity_log):
        """Test total=False case with attributes processing"""
        mock_request_obj = MagicMock(
            filter="containsWordStartingWith(attributes,'John')",
            entity_type="Individual",
            tenant_id="test-tenant",
            max_results=10,
            select="uri,label,attributes",
            offset=0,
            sort="",
            order="asc",
            options="ovOnly",
            activeness="active"
        )
        mock_request.return_value = mock_request_obj
        
        # Mock entities with attributes
        mock_entities = [
            {
                "uri": "entities/123",
                "label": "John Doe",
                "attributes": {"Name": "John Doe", "Email": "john@example.com"}
            }
        ]
        
        mock_http.return_value = mock_entities
        mock_simplify.return_value = {"Name": "Test Name", "Email": "test@example.com"}
        mock_dump.return_value = "processed_yaml_output"
        mock_activity_log.return_value = None

        result = await search_entities(
            filter="containsWordStartingWith(attributes,'John')", 
            entity_type="Individual", 
            tenant_id="test-tenant", 
            max_results=10
        )
        
        assert result == "processed_yaml_output"
        mock_activity_log.assert_called_once()

    @patch("src.tools.search.ActivityLog.execute_and_log_activity")
    @patch("src.tools.search.yaml.dump")
    @patch("src.tools.search.http_request")
    @patch("src.tools.search.validate_connection_security")
    @patch("src.tools.search.get_reltio_headers")
    @patch("src.tools.search.get_reltio_url")
    @patch("src.tools.search.EntitySearchRequest")
    async def test_search_entities_empty_results(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump, mock_activity_log):
        """Test search with no results"""
        mock_request_obj = MagicMock(
            filter="containsWordStartingWith(attributes,'NonExistent')",
            entity_type="Individual",
            tenant_id="test-tenant",
            max_results=10,
            select="uri,label",
            offset=0,
            sort="",
            order="asc",
            options="ovOnly",
            activeness="active"
        )
        mock_request.return_value = mock_request_obj
        
        mock_http.return_value = []
        mock_dump.return_value = "[]"
        mock_activity_log.return_value = None

        result = await search_entities(filter="containsWordStartingWith(attributes,'NonExistent')", entity_type="Individual", tenant_id="test-tenant")
        
        assert result == "[]"
        mock_activity_log.assert_called_once()

    @patch("src.tools.search.EntitySearchRequest", side_effect=ValueError("Invalid filter syntax"))
    async def test_search_entities_invalid_filter(self, mock_request):
        """Test search with invalid filter syntax"""
        result = await search_entities(filter="invalid_filter", entity_type="Individual", tenant_id="test-tenant")
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.search.http_request", side_effect=Exception("Network timeout"))
    @patch("src.tools.search.validate_connection_security")
    @patch("src.tools.search.get_reltio_headers")
    @patch("src.tools.search.get_reltio_url")
    @patch("src.tools.search.EntitySearchRequest")
    async def test_search_entities_network_error(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        """Test network timeout handling"""
        mock_request.return_value = MagicMock(
            filter="containsWordStartingWith(attributes,'John')",
            entity_type="Individual",
            tenant_id="test-tenant"
        )
        
        result = await search_entities(filter="containsWordStartingWith(attributes,'John')", entity_type="Individual", tenant_id="test-tenant")
        assert result["error"]["code_key"] == "SERVER_ERROR"
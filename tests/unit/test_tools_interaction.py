import pytest
from unittest.mock import patch, AsyncMock
import yaml
from src.tools.interaction import get_entity_interactions, create_interactions

ENTITY_ID = "ent123"
TENANT_ID = "test-tenant"

@pytest.mark.asyncio
class TestGetEntityInteractions:
    @patch("src.tools.interaction.EntityInteractionsRequest")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.validate_connection_security")
    @patch("src.tools.interaction.http_request")
    @patch("src.tools.interaction.simplify_reltio_attributes")
    @patch("src.tools.interaction.yaml.dump")
    @patch("src.tools.interaction.ActivityLog.execute_and_log_activity")
    async def test_get_entity_interactions_success(self, mock_activity_log, mock_dump, mock_simplify, mock_http, mock_validate, mock_headers, mock_url, mock_request):
        # Setup mocks
        mock_request.return_value.entity_id = ENTITY_ID
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max = 50
        mock_request.return_value.offset = 0
        mock_request.return_value.order = "asc"
        mock_request.return_value.sort = ""
        mock_request.return_value.filter = ""
        
        mock_url.return_value = f"https://reltio.com/entities/{ENTITY_ID}/_interactions"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        interactions_response = {
            "interactions": [
                {
                    "URI": "interactions/int123",
                    "type": "Meeting",
                    "attributes": {"Place": [{"value": "Office"}]}
                }
            ],
            "totalFetched": 1,
            "fetchedAll": True
        }
        mock_http.return_value = interactions_response
        mock_dump.return_value = "yaml_output"
        mock_simplify.return_value = {"Place": "Office"}

        # Call the function
        result = await get_entity_interactions(ENTITY_ID, tenant_id=TENANT_ID)

        # Assertions
        assert result == "yaml_output"
        mock_url.assert_called_once_with(f"entities/{ENTITY_ID}/_interactions", "api", TENANT_ID)
        mock_http.assert_called_once()
        mock_activity_log.assert_called_once()
        mock_simplify.assert_called_once_with({"Place": [{"value": "Office"}]})
        mock_dump.assert_called_once()

    @patch("src.tools.interaction.EntityInteractionsRequest")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.validate_connection_security")
    @patch("src.tools.interaction.http_request")
    @patch("src.tools.interaction.simplify_reltio_attributes")
    @patch("src.tools.interaction.yaml.dump")
    @patch("src.tools.interaction.ActivityLog.execute_and_log_activity")
    async def test_get_entity_interactions_with_params(self, mock_activity_log, mock_dump, mock_simplify, mock_http, mock_validate, mock_headers, mock_url, mock_request):
        # Setup mocks with custom parameters
        mock_request.return_value.entity_id = ENTITY_ID
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max = 25
        mock_request.return_value.offset = 10
        mock_request.return_value.order = "desc"
        mock_request.return_value.sort = "timestamp"
        mock_request.return_value.filter = 'equals(type,"Meeting")'
        
        mock_url.return_value = f"https://reltio.com/entities/{ENTITY_ID}/_interactions"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        interactions_response = {"interactions": [], "totalFetched": 0, "fetchedAll": True}
        mock_http.return_value = interactions_response
        mock_dump.return_value = "yaml_output"

        # Call the function with custom parameters
        result = await get_entity_interactions(
            ENTITY_ID, 
            max=25, 
            offset=10, 
            order="desc", 
            sort="timestamp", 
            filter='equals(type,"Meeting")',
            tenant_id=TENANT_ID
        )

        # Verify the HTTP request was called with correct parameters
        expected_params = {
            "max": 25,
            "offset": 10,
            "order": "desc",
            "sort": "timestamp",
            "filter": 'equals(type,"Meeting")'
        }
        mock_http.assert_called_once()
        call_args = mock_http.call_args
        assert call_args[1]["params"] == expected_params
        assert result == "yaml_output"

    @patch("src.tools.interaction.EntityInteractionsRequest", side_effect=ValueError("Invalid entity ID"))
    async def test_get_entity_interactions_validation_error(self, mock_request):
        result = await get_entity_interactions("invalid-id", tenant_id=TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
        assert "Invalid input parameters" in result["error"]["message"]

    @patch("src.tools.interaction.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.EntityInteractionsRequest")
    async def test_get_entity_interactions_authentication_error(self, mock_request, mock_url, mock_headers, mock_validate):
        mock_request.return_value.entity_id = ENTITY_ID
        mock_request.return_value.tenant_id = TENANT_ID

        result = await get_entity_interactions(ENTITY_ID, tenant_id=TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
        assert "Failed to authenticate with Reltio API" in result["error"]["message"]

    @patch("src.tools.interaction.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.interaction.validate_connection_security")
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.EntityInteractionsRequest")
    async def test_get_entity_interactions_404_not_found(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        mock_request.return_value.entity_id = ENTITY_ID
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max = 50
        mock_request.return_value.offset = 0
        mock_request.return_value.order = "asc"
        mock_request.return_value.sort = ""
        mock_request.return_value.filter = ""

        result = await get_entity_interactions(ENTITY_ID, tenant_id=TENANT_ID)
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"
        assert "Entity with ID" in result["error"]["message"]
        assert "not found or no interactions available" in result["error"]["message"]

    @patch("src.tools.interaction.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.interaction.validate_connection_security")
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.EntityInteractionsRequest")
    async def test_get_entity_interactions_generic_server_error(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        mock_request.return_value.entity_id = ENTITY_ID
        mock_request.return_value.tenant_id = TENANT_ID
        mock_request.return_value.max = 50
        mock_request.return_value.offset = 0
        mock_request.return_value.order = "asc"
        mock_request.return_value.sort = ""
        mock_request.return_value.filter = ""

        result = await get_entity_interactions(ENTITY_ID, tenant_id=TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"
        assert "Failed to retrieve entity interactions from Reltio API" in result["error"]["message"]


@pytest.mark.asyncio
class TestCreateInteractions:
    @patch("src.tools.interaction.CreateInteractionRequest")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.validate_connection_security")
    @patch("src.tools.interaction.http_request")
    @patch("src.tools.interaction.yaml.dump")
    async def test_create_interactions_success(self, mock_dump, mock_http, mock_validate, mock_headers, mock_url, mock_request):
        # Setup test data
        interactions = [
            {
                "type": "configuration/interactionTypes/Email",
                "attributes": {
                    "DateEmailSent": [{"value": "2025-01-02"}]
                },
                "members": {
                    "Individual": {
                        "type": "configuration/interactionTypes/Email/memberTypes/Individual",
                        "members": [{"objectURI": "entities/0U3sCW1"}]
                    }
                }
            }
        ]
        
        # Setup mocks
        mock_request.return_value.interactions = interactions
        mock_request.return_value.source_system = "configuration/sources/Reltio"
        mock_request.return_value.crosswalk_value = None
        mock_request.return_value.return_objects = True
        mock_request.return_value.options = None
        mock_request.return_value.tenant_id = TENANT_ID
        
        mock_url.return_value = "https://reltio.com/interactions"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        # Mock successful response
        create_response = [
            {
                "index": 0,
                "URI": "interactions/01BThVh",
                "status": "OK",
                "object": {
                    "URI": "interactions/01BThVh",
                    "type": "configuration/interactionTypes/Email",
                    "attributes": {
                        "DateEmailSent": [{"value": "2025-01-02"}]
                    }
                }
            }
        ]
        mock_http.return_value = create_response
        mock_dump.return_value = "yaml_output"
        
        # Call the function
        result = await create_interactions(interactions, tenant_id=TENANT_ID)
        
        # Assertions
        assert result == "yaml_output"
        mock_url.assert_called_once_with("interactions", "api", TENANT_ID)
        mock_http.assert_called_once()
        
        # Verify correct HTTP method and headers
        call_args = mock_http.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
        assert call_args[1]["headers"]["Source-System"] == "configuration/sources/Reltio"
        assert call_args[1]["data"] == interactions
        
        mock_dump.assert_called_once_with(create_response, sort_keys=False)

    @patch("src.tools.interaction.CreateInteractionRequest", side_effect=ValueError("Invalid interaction data"))
    async def test_create_interactions_validation_error(self, mock_request):
        interactions = [{"invalid": "data"}]  # Missing required 'type' field
        
        result = await create_interactions(interactions, tenant_id=TENANT_ID)
        
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
        assert "Invalid input parameters" in result["error"]["message"]

    @patch("src.tools.interaction.http_request", side_effect=Exception("400 Bad Request"))
    @patch("src.tools.interaction.validate_connection_security")
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.CreateInteractionRequest")
    async def test_create_interactions_bad_request_error(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        interactions = [{"type": "configuration/interactionTypes/Email"}]
        mock_request.return_value.interactions = interactions
        mock_request.return_value.tenant_id = TENANT_ID
        
        result = await create_interactions(interactions, tenant_id=TENANT_ID)
        
        assert result["error"]["code_key"] == "BAD_REQUEST"
        assert "Invalid interaction data provided" in result["error"]["message"]

    @patch("src.tools.interaction.http_request", side_effect=Exception("409 Conflict - duplicate crosswalk"))
    @patch("src.tools.interaction.validate_connection_security")
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.CreateInteractionRequest")
    async def test_create_interactions_conflict_error(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        interactions = [{"type": "configuration/interactionTypes/Email"}]
        mock_request.return_value.interactions = interactions
        mock_request.return_value.tenant_id = TENANT_ID
        
        result = await create_interactions(interactions, tenant_id=TENANT_ID)
        
        assert result["error"]["code_key"] == "CONFLICT"
        assert "Duplicate interaction ID or existing crosswalk" in result["error"]["message"]

    @patch("src.tools.interaction.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.CreateInteractionRequest")
    async def test_create_interactions_authentication_error(self, mock_request, mock_url, mock_headers, mock_validate):
        interactions = [{"type": "configuration/interactionTypes/Email"}]
        mock_request.return_value.interactions = interactions
        mock_request.return_value.tenant_id = TENANT_ID
        
        result = await create_interactions(interactions, tenant_id=TENANT_ID)
        
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
        assert "Failed to authenticate with Reltio API" in result["error"]["message"]

    @patch("src.tools.interaction.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.interaction.validate_connection_security")
    @patch("src.tools.interaction.get_reltio_headers")
    @patch("src.tools.interaction.get_reltio_url")
    @patch("src.tools.interaction.CreateInteractionRequest")
    async def test_create_interactions_not_found_error(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        interactions = [{"type": "configuration/interactionTypes/Email"}]
        mock_request.return_value.interactions = interactions
        mock_request.return_value.tenant_id = TENANT_ID
        
        result = await create_interactions(interactions, tenant_id=TENANT_ID)
        
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"
        assert "One or more referenced entities or configuration elements not found" in result["error"]["message"]

    @patch("src.tools.interaction.CreateInteractionRequest", side_effect=Exception("Unexpected error"))
    async def test_create_interactions_unexpected_error(self, mock_request):
        interactions = [{"type": "configuration/interactionTypes/Email"}]
        
        result = await create_interactions(interactions, tenant_id=TENANT_ID)
        
        assert result["error"]["code_key"] == "SERVER_ERROR"
        assert "An unexpected error occurred while creating interactions" in result["error"]["message"]


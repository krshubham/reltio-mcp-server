import pytest
import yaml
from unittest.mock import patch, MagicMock
from src.tools.entity import (
    unmerge_entity_by_contributor,
    unmerge_entity_tree_by_contributor,
    merge_entities,
    export_merge_tree
)

TENANT_ID = "test-tenant"
ORIGIN_ENTITY_ID = "entity-123"
CONTRIBUTOR_ENTITY_ID = "entity-456"

# Mock unmerge response data
MOCK_UNMERGE_RESPONSE = {
    "a": {
        "uri": f"entities/{ORIGIN_ENTITY_ID}",
        "label": "Origin Entity",
        "attributes": {
            "name": "Origin Entity Name"
        }
    },
    "b": {
        "uri": f"entities/{CONTRIBUTOR_ENTITY_ID}",
        "label": "Contributor Entity",
        "attributes": {
            "name": "Contributor Entity Name"
        }
    }
}

MOCK_TREE_UNMERGE_RESPONSE = {
    "a": {
        "uri": f"entities/{ORIGIN_ENTITY_ID}",
        "label": "Origin Entity After Tree Unmerge",
        "attributes": {
            "name": "Origin Entity Name"
        }
    },
    "b": {
        "uri": f"entities/{CONTRIBUTOR_ENTITY_ID}",
        "label": "Contributor Entity Tree",
        "attributes": {
            "name": "Contributor Entity Name"
        },
        "children": [
            {
                "uri": "entities/child-1",
                "label": "Child Entity 1"
            },
            {
                "uri": "entities/child-2", 
                "label": "Child Entity 2"
            }
        ]
    }
}

MOCK_UNMERGE_RESPONSE_WITH_MISSING_FIELDS = {
    "a": {
        "uri": f"entities/{ORIGIN_ENTITY_ID}"
        # Missing label and attributes
    },
    "b": {
        "uri": f"entities/{CONTRIBUTOR_ENTITY_ID}"
        # Missing label and attributes
    }
}

MOCK_UNMERGE_RESPONSE_WITH_NULL_FIELDS = {
    "a": {
        "uri": f"entities/{ORIGIN_ENTITY_ID}",
        "label": None,
        "attributes": None
    },
    "b": {
        "uri": f"entities/{CONTRIBUTOR_ENTITY_ID}",
        "label": None,
        "attributes": None
    }
}


@pytest.mark.asyncio
class TestUnmergeEntityByContributor:

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_by_contributor_success(self, mock_validate, mock_headers, mock_request):
        """Test successful entity unmerge by contributor"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_UNMERGE_RESPONSE
        
        result = await unmerge_entity_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        parsed_result = result if isinstance(result, dict) else yaml.safe_load(result)
        
        assert isinstance(parsed_result, dict)
        assert "a" in parsed_result
        assert "b" in parsed_result
        assert parsed_result["a"]["uri"] == f"entities/{ORIGIN_ENTITY_ID}"
        assert parsed_result["b"]["uri"] == f"entities/{CONTRIBUTOR_ENTITY_ID}"
        
        mock_request.assert_called_once()

    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_by_contributor_auth_error(self, mock_validate, mock_headers):
        """Test authentication error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_validate.side_effect = Exception("Auth failed")
        
        result = await unmerge_entity_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_by_contributor_404_error(self, mock_validate, mock_headers, mock_request):
        """Test 404 error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.side_effect = Exception("404 Not Found")
        
        result = await unmerge_entity_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_by_contributor_400_error(self, mock_validate, mock_headers, mock_request):
        """Test 400 error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.side_effect = Exception("400 Bad Request")
        
        result = await unmerge_entity_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "INVALID_REQUEST"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_by_contributor_general_error(self, mock_validate, mock_headers, mock_request):
        """Test general error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.side_effect = Exception("Server error")
        
        result = await unmerge_entity_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "SERVER_ERROR"

    async def test_unmerge_entity_by_contributor_invalid_entity_id(self):
        """Test validation error for invalid entity ID"""
        result = await unmerge_entity_by_contributor("", CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_by_contributor_with_missing_fields(self, mock_validate, mock_headers, mock_request):
        """Test unmerge with missing fields in response"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_UNMERGE_RESPONSE_WITH_MISSING_FIELDS
        
        result = await unmerge_entity_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        parsed_result = result if isinstance(result, dict) else yaml.safe_load(result)
        assert isinstance(parsed_result, dict)
        assert "a" in parsed_result
        assert "b" in parsed_result
        assert parsed_result["a"]["uri"] == f"entities/{ORIGIN_ENTITY_ID}"
        assert parsed_result["b"]["uri"] == f"entities/{CONTRIBUTOR_ENTITY_ID}"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_by_contributor_with_null_fields(self, mock_validate, mock_headers, mock_request):
        """Test unmerge with null fields in response"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_UNMERGE_RESPONSE_WITH_NULL_FIELDS
        
        result = await unmerge_entity_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        parsed_result = result if isinstance(result, dict) else yaml.safe_load(result)
        assert isinstance(parsed_result, dict)
        assert "a" in parsed_result
        assert "b" in parsed_result
        assert parsed_result["a"]["label"] is None
        assert parsed_result["a"]["attributes"] is None


@pytest.mark.asyncio
class TestUnmergeEntityTreeByContributor:

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_tree_by_contributor_success(self, mock_validate, mock_headers, mock_request):
        """Test successful entity tree unmerge by contributor"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_TREE_UNMERGE_RESPONSE
        
        result = await unmerge_entity_tree_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        parsed_result = result if isinstance(result, dict) else yaml.safe_load(result)
        
        assert isinstance(parsed_result, dict)
        assert "a" in parsed_result
        assert "b" in parsed_result
        assert parsed_result["a"]["uri"] == f"entities/{ORIGIN_ENTITY_ID}"
        assert parsed_result["b"]["uri"] == f"entities/{CONTRIBUTOR_ENTITY_ID}"
        assert "children" in parsed_result["b"]
        assert len(parsed_result["b"]["children"]) == 2
        
        mock_request.assert_called_once()

    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_tree_by_contributor_auth_error(self, mock_validate, mock_headers):
        """Test authentication error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_validate.side_effect = Exception("Auth failed")
        
        result = await unmerge_entity_tree_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_tree_by_contributor_404_error(self, mock_validate, mock_headers, mock_request):
        """Test 404 error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.side_effect = Exception("404 Not Found")
        
        result = await unmerge_entity_tree_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_tree_by_contributor_400_error(self, mock_validate, mock_headers, mock_request):
        """Test 400 error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.side_effect = Exception("400 Bad Request")
        
        result = await unmerge_entity_tree_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "INVALID_REQUEST"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_tree_by_contributor_general_error(self, mock_validate, mock_headers, mock_request):
        """Test general error handling"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.side_effect = Exception("Server error")
        
        result = await unmerge_entity_tree_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "SERVER_ERROR"

    async def test_unmerge_entity_tree_by_contributor_invalid_entity_id(self):
        """Test validation error for invalid entity ID"""
        result = await unmerge_entity_tree_by_contributor("", CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        assert isinstance(result, dict)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_tree_by_contributor_with_params(self, mock_validate, mock_headers, mock_request):
        """Test that the correct URL parameters are passed"""
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_request.return_value = MOCK_TREE_UNMERGE_RESPONSE
        
        await unmerge_entity_tree_by_contributor(ORIGIN_ENTITY_ID, CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        
        # Verify the request was made with correct parameters
        call_args = mock_request.call_args
        params = call_args[1]['params']
        assert params['contributorURI'] == f"entities/{CONTRIBUTOR_ENTITY_ID}"


@pytest.mark.asyncio
class TestUnmergeValidation:

    async def test_unmerge_entity_by_contributor_empty_origin_id(self):
        """Test validation with empty origin entity ID"""
        result = await unmerge_entity_by_contributor("", CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    async def test_unmerge_entity_by_contributor_empty_contributor_id(self):
        """Test validation with empty contributor entity ID"""
        result = await unmerge_entity_by_contributor(ORIGIN_ENTITY_ID, "", TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    async def test_unmerge_entity_tree_by_contributor_empty_origin_id(self):
        """Test validation with empty origin entity ID"""
        result = await unmerge_entity_tree_by_contributor("", CONTRIBUTOR_ENTITY_ID, TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    async def test_unmerge_entity_tree_by_contributor_empty_contributor_id(self):
        """Test validation with empty contributor entity ID"""
        result = await unmerge_entity_tree_by_contributor(ORIGIN_ENTITY_ID, "", TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
class TestMergeEntities:

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.MergeEntitiesRequest")
    async def test_successful_merge(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        entity_ids = ["entity1", "entity2"]
        mock_request_model.return_value.entity_ids = entity_ids
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/_same"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"id": "merged_entity_id", "status": "success"}
        result = await merge_entities(entity_ids, TENANT_ID)
        parsed_result = result if isinstance(result, dict) else yaml.safe_load(result)
        assert isinstance(parsed_result, dict)
        assert parsed_result["id"] == "merged_entity_id"
        assert parsed_result["status"] == "success"
        mock_http.assert_called_once()
        
    @patch("src.tools.entity.MergeEntitiesRequest", side_effect=ValueError("Invalid entity IDs"))
    async def test_validation_error(self, _):
        result = await merge_entities(["entity1", "entity2"], TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
    
    @patch("src.tools.entity.get_reltio_headers", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.MergeEntitiesRequest")
    async def test_authentication_error(self, mock_request_model, mock_get_url, mock_headers):
        entity_ids = ["entity1", "entity2"]
        mock_request_model.return_value.entity_ids = entity_ids
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/_same"
        
        result = await merge_entities(entity_ids, TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
class TestExportMergeTree:
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity")
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        mock_get_url.return_value = "https://reltio.api/entities/export"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"status": "success", "jobId": "job123"}

        result = await export_merge_tree("test@example.com", TENANT_ID)

        parsed_result = result if isinstance(result, dict) else yaml.safe_load(result)
        assert isinstance(parsed_result, dict)
        assert parsed_result["status"] == "success"
        assert parsed_result["jobId"] == "job123"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        result = await export_merge_tree("test@example.com", TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.entity.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    async def test_server_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        result = await export_merge_tree("test@example.com", TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"


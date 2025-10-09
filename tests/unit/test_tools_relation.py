import pytest
from unittest.mock import patch, MagicMock
from src.tools.relation import (
    get_relation_details,
    create_relationships,
    delete_relation,
    get_entity_relations,
    search_relations
)

@pytest.mark.asyncio
async def test_get_relation_details_success():
    with patch("src.tools.relation.RelationIdRequest") as mock_request, \
         patch("src.tools.relation.get_reltio_url") as mock_url, \
         patch("src.tools.relation.get_reltio_headers") as mock_headers, \
         patch("src.tools.relation.validate_connection_security") as mock_validate, \
         patch("src.tools.relation.http_request") as mock_http:

        mock_request.return_value = MagicMock(relation_id="rel123", tenant_id="tenant")
        mock_url.return_value = "https://reltio.com/relations/rel123"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"id": "rel123", "type": "relation", "attributes": {}}

        result = await get_relation_details("rel123", "tenant")
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["id"] == "rel123"

@pytest.mark.asyncio
async def test_get_relation_details_validation_error():
    with patch("src.tools.relation.RelationIdRequest", side_effect=ValueError("Invalid ID")), \
         patch("src.tools.relation.create_error_response") as mock_create_error:
        
        mock_create_error.return_value = {"error": "VALIDATION_ERROR", "message": "Invalid relation ID format: Invalid ID"}

        result = await get_relation_details("bad-id")
        assert result["error"] == "VALIDATION_ERROR"

@pytest.mark.asyncio
async def test_get_relation_details_authentication_error():
    with patch("src.tools.relation.RelationIdRequest") as mock_request, \
         patch("src.tools.relation.get_reltio_url"), \
         patch("src.tools.relation.get_reltio_headers", side_effect=Exception("Auth failed")), \
         patch("src.tools.relation.create_error_response") as mock_create_error:
        
        mock_request.return_value = MagicMock(relation_id="rel123", tenant_id="tenant")
        mock_create_error.return_value = {"error": "AUTHENTICATION_ERROR", "message": "Failed to authenticate with Reltio API"}

        result = await get_relation_details("rel123")
        assert result["error"] == "AUTHENTICATION_ERROR"

@pytest.mark.asyncio
async def test_get_relation_details_404_not_found():
    with patch("src.tools.relation.RelationIdRequest") as mock_request, \
         patch("src.tools.relation.get_reltio_url"), \
         patch("src.tools.relation.get_reltio_headers"), \
         patch("src.tools.relation.validate_connection_security"), \
         patch("src.tools.relation.http_request", side_effect=Exception("404 Not Found")), \
         patch("src.tools.relation.create_error_response") as mock_create_error:

        mock_request.return_value = MagicMock(relation_id="rel123", tenant_id="tenant")
        mock_create_error.return_value = {"error": "RESOURCE_NOT_FOUND", "message": "Relation with ID rel123 not found"}

        result = await get_relation_details("rel123")
        assert result["error"] == "RESOURCE_NOT_FOUND"

@pytest.mark.asyncio
async def test_get_relation_details_generic_server_error():
    with patch("src.tools.relation.RelationIdRequest") as mock_request, \
         patch("src.tools.relation.get_reltio_url"), \
         patch("src.tools.relation.get_reltio_headers"), \
         patch("src.tools.relation.validate_connection_security"), \
         patch("src.tools.relation.http_request", side_effect=Exception("Some API error")), \
         patch("src.tools.relation.create_error_response") as mock_create_error:

        mock_request.return_value = MagicMock(relation_id="rel123", tenant_id="tenant")
        mock_create_error.return_value = {"error": "SERVER_ERROR", "message": "Failed to retrieve relation details from Reltio API"}

        result = await get_relation_details("rel123")
        assert result["error"] == "SERVER_ERROR"

@pytest.mark.asyncio
async def test_get_relation_details_unexpected_error():
    with patch("src.tools.relation.RelationIdRequest", side_effect=Exception("Boom")), \
         patch("src.tools.relation.create_error_response") as mock_create_error:
        
        mock_create_error.return_value = {"error": "SERVER_ERROR", "message": "An unexpected error occurred while retrieving relation details"}

        result = await get_relation_details("rel123")
        assert result["error"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestCreateRelationships:
    """Test cases for the create_relationships function"""
    
    SAMPLE_RELATIONS = [{
        "type": "configuration/relationTypes/VistaGlobalMenuItemToVistaLocalMenuItem",
        "startObject": {
            "type": "configuration/entityTypes/VistaGlobalMenuItem",
            "objectURI": "entities/e1"
        },
        "endObject": {
            "type": "configuration/entityTypes/VistaLocalMenuItem", 
            "objectURI": "entities/e2"
        }
    }]
    TENANT_ID = "test-tenant"

    @patch("src.tools.relation.ActivityLog.execute_and_log_activity")
    @patch("src.tools.relation.yaml.dump")
    @patch("src.tools.relation.http_request")
    @patch("src.tools.relation.validate_connection_security")
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.CreateRelationsRequest")
    async def test_create_relationships_success_with_objecturi(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump, mock_activity_log):
        # Mock the request model
        mock_request.return_value = MagicMock(
            relations=[MagicMock(
                type='configuration/relationTypes/VistaGlobalMenuItemToVistaLocalMenuItem',
                startObject=MagicMock(
                    type='configuration/entityTypes/VistaGlobalMenuItem',
                    objectURI='entities/e1',
                    crosswalks=None
                ),
                endObject=MagicMock(
                    type='configuration/entityTypes/VistaLocalMenuItem',
                    objectURI='entities/e2',
                    crosswalks=None
                ),
                crosswalks=None
            )],
            options=None,
            tenant_id=self.TENANT_ID
        )
        
        mock_url.return_value = "https://reltio.com/relations"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"created": True, "relationId": "rel123"}
        mock_dump.return_value = "yaml_output"

        result = await create_relationships(self.SAMPLE_RELATIONS, tenant_id=self.TENANT_ID)
        assert result == "yaml_output"
        mock_activity_log.assert_called_once()
        mock_dump.assert_called_once()

    @patch("src.tools.relation.CreateRelationsRequest", side_effect=ValueError("Invalid input"))
    async def test_create_relationships_validation_error(self, mock_request):
        result = await create_relationships([{"invalid": "data"}], tenant_id=self.TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.relation.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.CreateRelationsRequest")
    async def test_create_relationships_authentication_error(self, mock_request, mock_url, mock_headers, mock_validate):
        mock_request.return_value = MagicMock(
            relations=[MagicMock()],
            options=None,
            tenant_id=self.TENANT_ID
        )

        result = await create_relationships(self.SAMPLE_RELATIONS, tenant_id=self.TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.relation.http_request", side_effect=Exception("API error"))
    @patch("src.tools.relation.validate_connection_security")
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.CreateRelationsRequest")
    async def test_create_relationships_api_error(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        mock_request.return_value = MagicMock(
            relations=[MagicMock()],
            options=None,
            tenant_id=self.TENANT_ID
        )

        result = await create_relationships(self.SAMPLE_RELATIONS, tenant_id=self.TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestDeleteRelation:
    """Test cases for the delete_relation function"""
    
    RELATION_ID = "rel123"
    TENANT_ID = "test-tenant"

    @patch("src.tools.relation.yaml.dump")
    @patch("src.tools.relation.http_request")
    @patch("src.tools.relation.validate_connection_security")
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.RelationIdRequest")
    async def test_delete_relation_success(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump):
        """Test successful deletion of a relation"""
        mock_request.return_value = MagicMock(relation_id=self.RELATION_ID, tenant_id=self.TENANT_ID)
        mock_url.return_value = f"https://reltio.com/relations/{self.RELATION_ID}"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"status": "OK"}
        mock_dump.return_value = "status: OK"

        result = await delete_relation(self.RELATION_ID, self.TENANT_ID)
        
        assert result == "status: OK"
        mock_dump.assert_called_once()

    @patch("src.tools.relation.RelationIdRequest", side_effect=ValueError("Invalid ID format"))
    async def test_delete_relation_validation_error(self, mock_request):
        """Test validation error for invalid relation ID"""
        result = await delete_relation("invalid-id", self.TENANT_ID)
        
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.relation.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.RelationIdRequest")
    async def test_delete_relation_authentication_error(self, mock_request, mock_url, mock_headers, mock_validate):
        """Test authentication error during deletion"""
        mock_request.return_value = MagicMock(relation_id=self.RELATION_ID, tenant_id=self.TENANT_ID)

        result = await delete_relation(self.RELATION_ID, self.TENANT_ID)
        
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.relation.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.relation.validate_connection_security")
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.RelationIdRequest")
    async def test_delete_relation_404_not_found(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        """Test 404 error when relation doesn't exist"""
        mock_request.return_value = MagicMock(relation_id=self.RELATION_ID, tenant_id=self.TENANT_ID)

        result = await delete_relation(self.RELATION_ID, self.TENANT_ID)
        
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
class TestGetEntityRelations:
    """Test cases for the get_entity_relations function"""
    
    ENTITY_ID = "0Gs6OmA"
    ENTITY_TYPES = ["configuration/entityTypes/Individual", "configuration/entityTypes/Organization"]
    TENANT_ID = "test-tenant"

    @patch("src.tools.relation.ActivityLog.execute_and_log_activity")
    @patch("src.tools.relation.yaml.dump")
    @patch("src.tools.relation.http_request")
    @patch("src.tools.relation.validate_connection_security")
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.GetEntityRelationsRequest")
    async def test_get_entity_relations_success_basic(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump, mock_activity_log):
        # Mock the request model
        mock_request.return_value = MagicMock(
            entity_id=self.ENTITY_ID,
            entity_types=self.ENTITY_TYPES,
            sort_by="",
            in_relations=None,
            out_relations=None,
            offset=0,
            max=10,
            tenant_id=self.TENANT_ID
        )
        
        mock_url.return_value = f"https://reltio.com/entities/{self.ENTITY_ID}/_connections"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"connections": [{"entity": {"id": "entity1"}}]}
        mock_dump.return_value = "yaml_output"

        result = await get_entity_relations(self.ENTITY_ID, self.ENTITY_TYPES, tenant_id=self.TENANT_ID)
        assert result == "yaml_output"
        mock_activity_log.assert_called_once()
        mock_dump.assert_called_once()
        mock_http.assert_called_once()

    @patch("src.tools.relation.GetEntityRelationsRequest", side_effect=ValueError("Invalid entity ID"))
    async def test_get_entity_relations_validation_error(self, mock_request):
        result = await get_entity_relations("invalid-id", self.ENTITY_TYPES, tenant_id=self.TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.relation.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.GetEntityRelationsRequest")
    async def test_get_entity_relations_authentication_error(self, mock_request, mock_url, mock_headers, mock_validate):
        mock_request.return_value = MagicMock(
            entity_id=self.ENTITY_ID,
            entity_types=self.ENTITY_TYPES,
            tenant_id=self.TENANT_ID
        )

        result = await get_entity_relations(self.ENTITY_ID, self.ENTITY_TYPES, tenant_id=self.TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.relation.http_request", side_effect=Exception("API error"))
    @patch("src.tools.relation.validate_connection_security")
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.GetEntityRelationsRequest")
    async def test_get_entity_relations_api_error(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        mock_request.return_value = MagicMock(
            entity_id=self.ENTITY_ID,
            entity_types=self.ENTITY_TYPES,
            tenant_id=self.TENANT_ID
        )

        result = await get_entity_relations(self.ENTITY_ID, self.ENTITY_TYPES, tenant_id=self.TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestSearchRelations:
    """Test cases for the search_relations function"""
    
    TENANT_ID = "test-tenant"

    @patch("src.tools.relation.ActivityLog.execute_and_log_activity")
    @patch("src.tools.relation.yaml.dump")
    @patch("src.tools.relation.http_request")
    @patch("src.tools.relation.validate_connection_security")
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.RelationSearchRequest")
    async def test_search_relations_success(self, mock_request, mock_url, mock_headers, mock_validate, mock_http, mock_dump, mock_activity_log):
        mock_request.return_value = MagicMock(
            filter="",
            select="",
            max=10,
            offset=0,
            tenant_id=self.TENANT_ID
        )
        
        mock_url.return_value = "https://reltio.com/relations/_search"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = [{"id": "rel1", "type": "relation"}]
        mock_dump.return_value = "yaml_output"

        result = await search_relations(tenant_id=self.TENANT_ID)
        assert result == "yaml_output"
        mock_activity_log.assert_called_once()
        mock_dump.assert_called_once()

    @patch("src.tools.relation.RelationSearchRequest", side_effect=ValueError("Invalid filter"))
    async def test_search_relations_validation_error(self, mock_request):
        result = await search_relations(filter="invalid", tenant_id=self.TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.relation.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.RelationSearchRequest")
    async def test_search_relations_authentication_error(self, mock_request, mock_url, mock_headers, mock_validate):
        mock_request.return_value = MagicMock(
            filter="",
            tenant_id=self.TENANT_ID
        )

        result = await search_relations(tenant_id=self.TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.relation.http_request", side_effect=Exception("API error"))
    @patch("src.tools.relation.validate_connection_security")
    @patch("src.tools.relation.get_reltio_headers")
    @patch("src.tools.relation.get_reltio_url")
    @patch("src.tools.relation.RelationSearchRequest")
    async def test_search_relations_api_error(self, mock_request, mock_url, mock_headers, mock_validate, mock_http):
        mock_request.return_value = MagicMock(
            filter="",
            tenant_id=self.TENANT_ID
        )

        result = await search_relations(tenant_id=self.TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"
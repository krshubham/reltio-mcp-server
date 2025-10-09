import pytest
from unittest.mock import patch, MagicMock

from src.tools.tenant_config import (
    get_business_configuration, 
    get_tenant_permissions_metadata,
    get_tenant_metadata,
    get_data_model_definition,
    get_entity_type_definition,
    get_relation_type_definition,
    get_interaction_type_definition,
    get_change_request_type_definition,
    get_graph_type_definition,
    get_grouping_type_definition,
    get_entity_type_definition_util,
    get_change_request_type_definition_util,
    get_relation_type_definition_util,
    get_interaction_type_definition_util,
    get_graph_type_definition_util,
    get_grouping_type_definition_util
)

TENANT_ID = "test-tenant"

@pytest.mark.asyncio
class TestBusinessConfig:
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_get_url.return_value = "https://reltio.api/entities/123ABC"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {}
        result = await get_business_configuration(TENANT_ID)
        assert isinstance(result, dict)

    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        result = await get_business_configuration(TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.tenant_config.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_server_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        result = await get_business_configuration(TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"

@pytest.mark.asyncio
class TestTenantPermissionsMetadata:
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_get_url.return_value = "https://reltio.api/entities/123ABC"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"status": "completed"}

        result = await get_tenant_permissions_metadata(TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
        assert result["status"] == "completed"

    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        result = await get_tenant_permissions_metadata(TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.tenant_config.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_server_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        result = await get_tenant_permissions_metadata(TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


@pytest.mark.asyncio
class TestGetTenantMetadata:
    """Test cases for get_tenant_metadata function"""
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful tenant metadata retrieval"""
        mock_get_url.return_value = "https://reltio.api/config/metadata"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "uri": "config/test-tenant",
            "description": "Test tenant",
            "schemaVersion": "1.0"
        }
        mock_activity_log.return_value = None
        
        result = await get_tenant_metadata(TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
        mock_activity_log.assert_called_once()

    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test authentication error handling"""
        result = await get_tenant_metadata(TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.tenant_config.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_server_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test server error handling"""
        result = await get_tenant_metadata(TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


@pytest.mark.asyncio
class TestGetDataModelDefinition:
    """Test cases for get_data_model_definition function"""
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful data model definition retrieval"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "entityTypes": [{"uri": "configuration/entityTypes/Individual"}]
        }
        mock_activity_log.return_value = None
        
        result = await get_data_model_definition(["entityTypes"], TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)

    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test authentication error handling"""
        result = await get_data_model_definition(["entityTypes"], TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
class TestGetEntityTypeDefinition:
    """Test cases for get_entity_type_definition function"""
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful entity type definition retrieval"""
        mock_get_url.return_value = "https://reltio.api/config/entityTypes/Individual"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "uri": "configuration/entityTypes/Individual",
            "label": "Individual",
            "attributes": []
        }
        mock_activity_log.return_value = None
        
        result = await get_entity_type_definition("Individual", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)

    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate):
        """Test authentication error handling"""
        result = await get_entity_type_definition("Individual", TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
class TestGetRelationTypeDefinition:
    """Test cases for get_relation_type_definition function"""
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful relation type definition retrieval"""
        mock_get_url.return_value = "https://reltio.api/config/relationTypes/HasAddress"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "uri": "configuration/relationTypes/HasAddress",
            "label": "Has Address"
        }
        mock_activity_log.return_value = None
        
        result = await get_relation_type_definition("HasAddress", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)

    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate):
        """Test authentication error handling"""
        result = await get_relation_type_definition("HasAddress", TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
class TestGetInteractionTypeDefinition:
    """Test cases for get_interaction_type_definition function"""
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful interaction type definition retrieval"""
        mock_get_url.return_value = "https://reltio.api/config/interactionTypes/Call"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "uri": "configuration/interactionTypes/Call",
            "label": "Call"
        }
        mock_activity_log.return_value = None
        
        result = await get_interaction_type_definition("Call", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)

    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate):
        """Test authentication error handling"""
        result = await get_interaction_type_definition("Call", TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
class TestBusinessConfigurationExtended:
    """Extended test cases for get_business_configuration"""
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions in outer try-catch"""
        result = await get_business_configuration(TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
        assert "An error occurred while retrieving business configuration" in result["error"]["message"]
    
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response_with_full_data(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test successful response with all fields populated"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "uri": "config/test-tenant",
            "description": "Test tenant configuration",
            "schemaVersion": "1.0",
            "sources": [{"uri": "source1"}, {"uri": "source2"}]
        }
        
        result = await get_business_configuration(TENANT_ID)
        assert isinstance(result, dict)
        assert result["uri"] == "config/test-tenant"
        assert result["description"] == "Test tenant configuration"
        assert result["schemaVersion"] == "1.0"
        assert len(result["sources"]) == 2


@pytest.mark.asyncio
class TestTenantPermissionsMetadataExtended:
    """Extended test cases for get_tenant_permissions_metadata"""
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions in outer try-catch"""
        result = await get_tenant_permissions_metadata(TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
        assert "An error occurred while retrieving tenant permissions metadata" in result["error"]["message"]
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity log failures don't stop execution"""
        mock_get_url.return_value = "https://reltio.api/permissions"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"status": "success"}
        
        result = await get_tenant_permissions_metadata(TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
        assert result["status"] == "success"


@pytest.mark.asyncio
class TestTenantMetadataExtended:
    """Extended test cases for get_tenant_metadata"""
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions in outer try-catch"""
        result = await get_tenant_metadata(TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
        assert "An error occurred while retrieving tenant metadata" in result["error"]["message"]
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity log failures don't stop execution"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "uri": "config/test-tenant",
            "description": "Test tenant",
            "schemaVersion": "1.0",
            "sources": [{"uri": "source1"}],
            "label": "Test Label",
            "createdTime": "2023-01-01",
            "updatedTime": "2023-01-02",
            "createdBy": "admin",
            "updatedBy": "admin",
            "entityTypes": [{"uri": "entity1"}],
            "changeRequestTypes": [{"uri": "cr1"}],
            "relationTypes": [{"uri": "rel1"}],
            "interactionTypes": [{"uri": "int1"}],
            "graphTypes": [{"uri": "graph1"}],
            "survivorshipStrategies": [{"uri": "surv1"}],
            "groupingTypes": [{"uri": "group1"}]
        }
        
        result = await get_tenant_metadata(TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
        assert result["uri"] == "config/test-tenant"


@pytest.mark.asyncio
class TestDataModelDefinitionExtended:
    """Extended test cases for get_data_model_definition"""
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions in outer try-catch"""
        result = await get_data_model_definition([], TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
        assert "An error occurred while retrieving data model definition" in result["error"]["message"]
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_empty_object_type_returns_all(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test empty object_type list returns all types"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "entityTypes": [{"uri": "entity1", "label": "Entity 1", "description": "Desc 1"}],
            "changeRequestTypes": [{"uri": "cr1"}],
            "relationTypes": [{"uri": "rel1", "label": "Relation 1", "description": "Desc 1"}],
            "interactionTypes": [{"uri": "int1", "label": "Interaction 1"}],
            "graphTypes": [{"uri": "graph1", "label": "Graph 1", "relationshipTypeURIs": ["rel1"]}],
            "survivorshipStrategies": [{"uri": "surv1", "label": "Survivorship 1"}],
            "groupingTypes": [{"uri": "group1", "description": "Group 1"}]
        }
        mock_activity_log.return_value = None
        
        result = await get_data_model_definition([], TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
        assert "entityTypes" in result
        assert "changeRequestTypes" in result
        assert "relationTypes" in result
        assert "interactionTypes" in result
        assert "graphTypes" in result
        assert "survivorshipStrategies" in result
        assert "groupingTypes" in result
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_change_request_types_filter(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test filtering by changeRequestTypes"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "changeRequestTypes": [{"uri": "cr1"}, {"uri": "cr2"}]
        }
        mock_activity_log.return_value = None
        
        result = await get_data_model_definition(["changeRequestTypes"], TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert "changeRequestTypes" in result
        assert len(result["changeRequestTypes"]) == 2
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_relation_types_filter(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test filtering by relationTypes"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "relationTypes": [{"uri": "rel1", "label": "Relation 1", "description": "Desc 1"}]
        }
        mock_activity_log.return_value = None
        
        result = await get_data_model_definition(["relationTypes"], TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert "relationTypes" in result
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_interaction_types_filter(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test filtering by interactionTypes"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "interactionTypes": [{"uri": "int1", "label": "Interaction 1"}]
        }
        mock_activity_log.return_value = None
        
        result = await get_data_model_definition(["interactionTypes"], TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert "interactionTypes" in result
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_graph_types_filter(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test filtering by graphTypes"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "graphTypes": [{"uri": "graph1", "label": "Graph 1", "relationshipTypeURIs": ["rel1"]}]
        }
        mock_activity_log.return_value = None
        
        result = await get_data_model_definition(["graphTypes"], TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert "graphTypes" in result
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_survivorship_strategies_filter(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test filtering by survivorshipStrategies"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "survivorshipStrategies": [{"uri": "surv1", "label": "Survivorship 1"}]
        }
        mock_activity_log.return_value = None
        
        result = await get_data_model_definition(["survivorshipStrategies"], TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert "survivorshipStrategies" in result
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_grouping_types_filter(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test filtering by groupingTypes"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "groupingTypes": [{"uri": "group1", "description": "Group 1"}]
        }
        mock_activity_log.return_value = None
        
        result = await get_data_model_definition(["groupingTypes"], TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert "groupingTypes" in result
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity log failures don't stop execution"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "entityTypes": [{"uri": "entity1", "label": "Entity 1", "description": "Desc 1"}]
        }
        
        result = await get_data_model_definition(["entityTypes"], TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.http_request", side_effect=Exception("API Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_api_request_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test API request error handling"""
        result = await get_data_model_definition([], TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


@pytest.mark.asyncio
class TestEntityTypeDefinitionExtended:
    """Extended test cases for get_entity_type_definition"""
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions in outer try-catch"""
        result = await get_entity_type_definition("Individual", TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
        assert "An error occurred while retrieving entity type definition" in result["error"]["message"]
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity log failures don't stop execution"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "entityTypes": [
                {
                    "uri": "configuration/entityTypes/Individual",
                    "label": "Individual",
                    "description": "Individual entity",
                    "attributes": [
                        {
                            "label": "Name",
                            "name": "Name",
                            "description": "Person name",
                            "type": "String",
                            "required": True,
                            "searchable": True
                        }
                    ]
                }
            ]
        }
        
        result = await get_entity_type_definition("configuration/entityTypes/Individual", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.http_request", side_effect=Exception("API Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_api_request_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test API request error handling"""
        result = await get_entity_type_definition("Individual", TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


@pytest.mark.asyncio
class TestChangeRequestTypeDefinition:
    """Test cases for get_change_request_type_definition function"""
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful change request type definition retrieval"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "changeRequestTypes": [
                {"uri": "configuration/changeRequestTypes/TestCR"}
            ]
        }
        mock_activity_log.return_value = None
        
        result = await get_change_request_type_definition("configuration/changeRequestTypes/TestCR", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate):
        """Test authentication error handling"""
        result = await get_change_request_type_definition("TestCR", TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions"""
        result = await get_change_request_type_definition("TestCR", TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity log failures don't stop execution"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "changeRequestTypes": [{"uri": "TestCR"}]
        }
        
        result = await get_change_request_type_definition("TestCR", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.http_request", side_effect=Exception("API Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_api_request_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test API request error handling"""
        result = await get_change_request_type_definition("TestCR", TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


@pytest.mark.asyncio
class TestRelationTypeDefinitionExtended:
    """Extended test cases for get_relation_type_definition"""
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions"""
        result = await get_relation_type_definition("HasAddress", TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity log failures don't stop execution"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "relationTypes": [
                {
                    "uri": "configuration/relationTypes/HasAddress",
                    "label": "Has Address",
                    "description": "Address relation",
                    "startObject": {"objectTypeURI": "Individual"},
                    "endObject": {"objectTypeURI": "Address"},
                    "attributes": [
                        {
                            "label": "Type",
                            "name": "Type",
                            "description": "Address type",
                            "type": "String",
                            "required": False,
                            "searchable": True
                        }
                    ]
                }
            ]
        }
        
        result = await get_relation_type_definition("configuration/relationTypes/HasAddress", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.http_request", side_effect=Exception("API Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_api_request_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test API request error handling"""
        result = await get_relation_type_definition("HasAddress", TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


@pytest.mark.asyncio
class TestInteractionTypeDefinitionExtended:
    """Extended test cases for get_interaction_type_definition"""
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions"""
        result = await get_interaction_type_definition("Call", TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity log failures don't stop execution"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "interactionTypes": [
                {
                    "uri": "configuration/interactionTypes/Call",
                    "label": "Call",
                    "memberTypes": [{"name": "caller"}, {"name": "callee"}],
                    "attributes": [
                        {
                            "label": "Duration",
                            "name": "Duration",
                            "type": "Integer"
                        }
                    ]
                }
            ]
        }
        
        result = await get_interaction_type_definition("configuration/interactionTypes/Call", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.http_request", side_effect=Exception("API Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_api_request_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test API request error handling"""
        result = await get_interaction_type_definition("Call", TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


@pytest.mark.asyncio
class TestGraphTypeDefinition:
    """Test cases for get_graph_type_definition function"""
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful graph type definition retrieval"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "graphTypes": [
                {
                    "uri": "configuration/graphTypes/TestGraph",
                    "label": "Test Graph",
                    "relationshipTypeURIs": ["rel1", "rel2"]
                }
            ]
        }
        mock_activity_log.return_value = None
        
        result = await get_graph_type_definition("configuration/graphTypes/TestGraph", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate):
        """Test authentication error handling"""
        result = await get_graph_type_definition("TestGraph", TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions"""
        result = await get_graph_type_definition("TestGraph", TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity log failures don't stop execution"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "graphTypes": [{"uri": "TestGraph", "label": "Test", "relationshipTypeURIs": []}]
        }
        
        result = await get_graph_type_definition("TestGraph", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.http_request", side_effect=Exception("API Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_api_request_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test API request error handling"""
        result = await get_graph_type_definition("TestGraph", TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


@pytest.mark.asyncio
class TestGroupingTypeDefinition:
    """Test cases for get_grouping_type_definition function"""
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity")
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful grouping type definition retrieval"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "groupingTypes": [
                {
                    "uri": "configuration/groupingTypes/TestGroup",
                    "description": "Test grouping",
                    "source": "TestSource"
                }
            ]
        }
        mock_activity_log.return_value = None
        
        result = await get_grouping_type_definition("configuration/groupingTypes/TestGroup", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate):
        """Test authentication error handling"""
        result = await get_grouping_type_definition("TestGroup", TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.tenant_config.get_reltio_url", side_effect=Exception("Unexpected error"))
    async def test_unexpected_exception(self, mock_get_url):
        """Test handling of unexpected exceptions"""
        result = await get_grouping_type_definition("TestGroup", TENANT_ID)
        assert result["error"]["code_key"] == "INTERNAL_SERVER_ERROR"
    
    @patch("src.tools.tenant_config.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.tenant_config.http_request")
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity log failures don't stop execution"""
        mock_get_url.return_value = "https://reltio.api/config"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "groupingTypes": [{"uri": "TestGroup", "description": "Test", "source": "Source"}]
        }
        
        result = await get_grouping_type_definition("TestGroup", TENANT_ID)
        import yaml
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert isinstance(result, dict)
    
    @patch("src.tools.tenant_config.http_request", side_effect=Exception("API Error"))
    @patch("src.tools.tenant_config.validate_connection_security")
    @patch("src.tools.tenant_config.get_reltio_headers")
    @patch("src.tools.tenant_config.get_reltio_url")
    async def test_api_request_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test API request error handling"""
        result = await get_grouping_type_definition("TestGroup", TENANT_ID)
        assert result["error"]["code_key"] == "API_REQUEST_ERROR"


class TestUtilityFunctions:
    """Test cases for utility functions"""
    
    def test_get_entity_type_definition_util_found(self):
        """Test entity type definition utility when type is found"""
        entity_types = [
            {
                "uri": "configuration/entityTypes/Individual",
                "label": "Individual",
                "description": "Person entity",
                "attributes": [
                    {
                        "label": "Name",
                        "name": "Name",
                        "description": "Person name",
                        "type": "String",
                        "required": True,
                        "searchable": True
                    }
                ]
            }
        ]
        
        result = get_entity_type_definition_util("configuration/entityTypes/Individual", entity_types)
        assert result["uri"] == "configuration/entityTypes/Individual"
        assert result["label"] == "Individual"
        assert len(result["attributes"]) == 1
        assert result["attributes"][0]["name"] == "Name"
    
    def test_get_entity_type_definition_util_not_found(self):
        """Test entity type definition utility when type is not found"""
        entity_types = [{"uri": "configuration/entityTypes/Individual"}]
        result = get_entity_type_definition_util("configuration/entityTypes/Organization", entity_types)
        assert result == {}
    
    def test_get_change_request_type_definition_util_found(self):
        """Test change request type definition utility when type is found"""
        change_request_types = [
            {"uri": "configuration/changeRequestTypes/TestCR"}
        ]
        
        result = get_change_request_type_definition_util("configuration/changeRequestTypes/TestCR", change_request_types)
        assert result["uri"] == "configuration/changeRequestTypes/TestCR"
    
    def test_get_change_request_type_definition_util_not_found(self):
        """Test change request type definition utility when type is not found"""
        change_request_types = [{"uri": "configuration/changeRequestTypes/TestCR"}]
        result = get_change_request_type_definition_util("configuration/changeRequestTypes/Other", change_request_types)
        assert result == {}
    
    def test_get_relation_type_definition_util_found(self):
        """Test relation type definition utility when type is found"""
        relation_types = [
            {
                "uri": "configuration/relationTypes/HasAddress",
                "label": "Has Address",
                "description": "Address relation",
                "startObject": {"objectTypeURI": "Individual"},
                "endObject": {"objectTypeURI": "Address"},
                "attributes": [
                    {
                        "label": "Type",
                        "name": "Type",
                        "description": "Address type",
                        "type": "String",
                        "required": False,
                        "searchable": True
                    }
                ]
            }
        ]
        
        result = get_relation_type_definition_util("configuration/relationTypes/HasAddress", relation_types)
        assert result["uri"] == "configuration/relationTypes/HasAddress"
        assert result["startObject"] == "Individual"
        assert result["endObject"] == "Address"
        assert len(result["attributes"]) == 1
    
    def test_get_relation_type_definition_util_not_found(self):
        """Test relation type definition utility when type is not found"""
        relation_types = [{"uri": "configuration/relationTypes/HasAddress"}]
        result = get_relation_type_definition_util("configuration/relationTypes/HasPhone", relation_types)
        assert result == {}
    
    def test_get_interaction_type_definition_util_found(self):
        """Test interaction type definition utility when type is found"""
        interaction_types = [
            {
                "uri": "configuration/interactionTypes/Call",
                "label": "Call",
                "memberTypes": [{"name": "caller"}, {"name": "callee"}],
                "attributes": [
                    {
                        "label": "Duration",
                        "name": "Duration",
                        "type": "Integer"
                    }
                ]
            }
        ]
        
        result = get_interaction_type_definition_util("configuration/interactionTypes/Call", interaction_types)
        assert result["uri"] == "configuration/interactionTypes/Call"
        assert len(result["memberTypes"]) == 2
        assert result["memberTypes"][0]["name"] == "caller"
        assert len(result["attributes"]) == 1
    
    def test_get_interaction_type_definition_util_not_found(self):
        """Test interaction type definition utility when type is not found"""
        interaction_types = [{"uri": "configuration/interactionTypes/Call"}]
        result = get_interaction_type_definition_util("configuration/interactionTypes/Email", interaction_types)
        assert result == {}
    
    def test_get_graph_type_definition_util_found(self):
        """Test graph type definition utility when type is found"""
        graph_types = [
            {
                "uri": "configuration/graphTypes/TestGraph",
                "label": "Test Graph",
                "relationshipTypeURIs": ["rel1", "rel2"]
            }
        ]
        
        result = get_graph_type_definition_util("configuration/graphTypes/TestGraph", graph_types)
        assert result["uri"] == "configuration/graphTypes/TestGraph"
        assert result["label"] == "Test Graph"
        assert len(result["relationshipTypeURIs"]) == 2
    
    def test_get_graph_type_definition_util_not_found(self):
        """Test graph type definition utility when type is not found"""
        graph_types = [{"uri": "configuration/graphTypes/TestGraph"}]
        result = get_graph_type_definition_util("configuration/graphTypes/OtherGraph", graph_types)
        assert result == {}
    
    def test_get_grouping_type_definition_util_found(self):
        """Test grouping type definition utility when type is found"""
        grouping_types = [
            {
                "uri": "configuration/groupingTypes/TestGroup",
                "description": "Test grouping",
                "source": "TestSource"
            }
        ]
        
        result = get_grouping_type_definition_util("configuration/groupingTypes/TestGroup", grouping_types)
        assert result["uri"] == "configuration/groupingTypes/TestGroup"
        assert result["description"] == "Test grouping"
        assert result["source"] == "TestSource"
    
    def test_get_grouping_type_definition_util_not_found(self):
        """Test grouping type definition utility when type is not found"""
        grouping_types = [{"uri": "configuration/groupingTypes/TestGroup"}]
        result = get_grouping_type_definition_util("configuration/groupingTypes/OtherGroup", grouping_types)
        assert result == {}
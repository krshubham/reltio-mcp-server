import pytest
from unittest.mock import patch, MagicMock
import yaml

from src.tools.entity import (
    get_entity_details, 
    update_entity_attributes, 
    get_entity_match_history, 
    get_entity_matches, 
    merge_entities, 
    reject_entity_match, 
    export_merge_tree,
    unmerge_entity_by_contributor,
    unmerge_entity_tree_by_contributor,
    get_entity_with_matches,
    create_entities,
    get_entity_hops,
    get_entity_parents,
    filter_entity
)

ENTITY_ID = "123ABC"
TENANT_ID = "test-tenant"

@pytest.mark.asyncio
class TestGetEntityDetails:
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_successful_response(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/123ABC"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"id": ENTITY_ID, "name": "Test Entity"}

        result = await get_entity_details(ENTITY_ID, {"attributes": []}, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, (dict, list))

    @patch("src.tools.entity.EntityIdRequest", side_effect=ValueError("Invalid ID"))
    async def test_validation_error(self, _):
        result = await get_entity_details("!invalid_id!", {"attributes": []}, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_authentication_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID

        result = await get_entity_details(ENTITY_ID, {"attributes": []}, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.entity.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_entity_not_found(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID

        result = await get_entity_details(ENTITY_ID, {"attributes": []}, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"

    @patch("src.tools.entity.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_server_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID

        result = await get_entity_details(ENTITY_ID, {"attributes": []}, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "SERVER_ERROR"

@pytest.mark.asyncio
class TestUpdateEntityAttributes:
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.UpdateEntityAttributesRequest")
    async def test_successful_response(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/123ABC"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"id": ENTITY_ID, "name": "Test Entity"}

        result = await update_entity_attributes(ENTITY_ID, {'attributes': {'FirstName': 'John'}}, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, (dict, list))
        assert parsed_result["id"] == ENTITY_ID

    @patch("src.tools.entity.UpdateEntityAttributesRequest", side_effect=ValueError("Invalid ID"))
    async def test_validation_error(self, _):
        result = await update_entity_attributes("!invalid_id!", TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.UpdateEntityAttributesRequest")
    async def test_authentication_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID

        result = await update_entity_attributes(ENTITY_ID, {'attributes': {'FirstName': 'John'}}, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.entity.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.UpdateEntityAttributesRequest")
    async def test_entity_not_found(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID

        result = await update_entity_attributes(ENTITY_ID, {'attributes': {'FirstName': 'John'}}, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"

    @patch("src.tools.entity.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.UpdateEntityAttributesRequest")
    async def test_server_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID

        result = await update_entity_attributes(ENTITY_ID, {'attributes': {'FirstName': 'John'}}, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestGetEntityMatches:

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_successful_entity_matches(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.side_effect = [
            "https://api/entities/123ABC/_transitiveMatches",
            "https://api/entities/123ABC"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        # format_entity_matches expects a list of dicts, so mock accordingly
        mock_http.side_effect = [
            [
                {"object": {"uri": "entities/match1"}, "matchRules": [], "createdTime": "2024-01-01T00:00:00Z", "matchScore": 95, "label": "Match 1"},
                {"object": {"uri": "entities/match2"}, "matchRules": [], "createdTime": "2024-01-01T00:00:00Z", "matchScore": 90, "label": "Match 2"}
            ],
            {"id": ENTITY_ID}
        ]

        result = await get_entity_matches(ENTITY_ID, TENANT_ID, max_results=10)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
        assert len(parsed_result["matches"]) == 2

    @patch("src.tools.entity.EntityIdRequest", side_effect=ValueError("Invalid entity"))
    async def test_validation_error(self, _):
        result = await get_entity_matches("invalid", TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.entity.get_reltio_headers", side_effect=Exception("Auth fail"))
    @patch("src.tools.entity.EntityIdRequest")
    async def test_auth_error(self, mock_req, _):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID

        result = await get_entity_matches(ENTITY_ID, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.entity.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_entity_not_found(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.return_value = "https://api/entities/123ABC/_transitiveMatches"

        result = await get_entity_matches(ENTITY_ID, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"

    @patch("src.tools.entity.http_request", side_effect=[[], {"id": ENTITY_ID}])
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_no_matches_found(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.return_value = "https://api/entities/123ABC/_transitiveMatches"

        result = await get_entity_matches(ENTITY_ID, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "matches" in parsed_result
        assert parsed_result["matches"] == []

    @patch("src.tools.entity.http_request", side_effect=[["match1", "match2"], Exception("Source fetch failed")])
    @patch("src.tools.entity.get_reltio_url", side_effect=[
        "https://api/entities/123ABC/_transitiveMatches",
        "https://api/entities/123ABC"
    ])
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_source_entity_fetch_failure(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID

        result = await get_entity_matches(ENTITY_ID, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "matches" in parsed_result
        assert "source_entity" not in parsed_result
        assert "could not retrieve source entity details" in parsed_result["message"]


@pytest.mark.asyncio
class TestGetEntityMatchHistory:

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_successful_match_history(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.side_effect = [
            "https://api/entities/123ABC/_crosswalkTree",
            "https://api/entities/123ABC"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.side_effect = [
            [{"id": "match1"}],
            {"id": ENTITY_ID}
        ]

        result = await get_entity_match_history(ENTITY_ID, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, (dict, list))

    @patch("src.tools.entity.EntityIdRequest", side_effect=ValueError("Invalid"))
    async def test_validation_error(self, _):
        result = await get_entity_match_history("invalid!", TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"

    @patch("src.tools.entity.get_reltio_headers", side_effect=Exception("Bad token"))
    @patch("src.tools.entity.EntityIdRequest")
    async def test_auth_error(self, mock_req, _):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID

        result = await get_entity_match_history(ENTITY_ID, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.entity.http_request", side_effect=Exception("404"))
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_entity_not_found(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.return_value = "https://api/entities/123ABC/_crosswalkTree"

        result = await get_entity_match_history(ENTITY_ID, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"

    @patch("src.tools.entity.http_request", side_effect=[[], {"id": ENTITY_ID}])
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_no_match_history(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.return_value = "https://api/entities/123ABC/_crosswalkTree"

        result = await get_entity_match_history(ENTITY_ID, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "match_history" in parsed_result
        assert parsed_result["match_history"] == []

    @patch("src.tools.entity.http_request", side_effect=[[{"id": "h1"}], Exception("Source fetch error")])
    @patch("src.tools.entity.get_reltio_url", side_effect=[
        "https://api/entities/123ABC/_crosswalkTree",
        "https://api/entities/123ABC"
    ])
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_source_entity_fetch_failure(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID

        result = await get_entity_match_history(ENTITY_ID, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "match_history" in parsed_result
        assert "could not retrieve source entity details" in parsed_result["message"]

@pytest.mark.asyncio
class TestMergeEntities:
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.MergeEntitiesRequest")
    async def test_successful_merge(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        entity_ids = ["entity1", "entity2"]
        formatted_ids = ["entities/entity1", "entities/entity2"]
        mock_request_model.return_value.entity_ids = formatted_ids
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/_same"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"id": "merged_entity_id", "status": "success"}
        result = await merge_entities(entity_ids, TENANT_ID)
        assert isinstance(result, dict)
        assert result["id"] == "merged_entity_id"
        assert result["status"] == "success"
        mock_http.assert_called_once_with(
            mock_get_url.return_value,
            method='POST',
            data=formatted_ids,
            headers=mock_headers.return_value
        )
    
    @patch("src.tools.entity.MergeEntitiesRequest", side_effect=ValueError("Invalid entity IDs"))
    async def test_validation_error(self, _):
        result = await merge_entities(["only_one_id"], TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
    
    @patch("src.tools.entity.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.MergeEntitiesRequest")
    async def test_authentication_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate):
        entity_ids = ["entity1", "entity2"]
        formatted_ids = ["entities/entity1", "entities/entity2"]
        mock_request_model.return_value.entity_ids = formatted_ids
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/_same"
        
        result = await merge_entities(entity_ids, TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.MergeEntitiesRequest")
    async def test_entity_not_found(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        entity_ids = ["entity1", "entity2"]
        formatted_ids = ["entities/entity1", "entities/entity2"]
        mock_request_model.return_value.entity_ids = formatted_ids
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/_same"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await merge_entities(entity_ids, TENANT_ID)
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("400 Bad Request"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.MergeEntitiesRequest")
    async def test_invalid_request(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        entity_ids = ["entity1", "entity2"]
        formatted_ids = ["entities/entity1", "entities/entity2"]
        mock_request_model.return_value.entity_ids = formatted_ids
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/_same"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await merge_entities(entity_ids, TENANT_ID)
        assert result["error"]["code_key"] == "INVALID_REQUEST"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.MergeEntitiesRequest")
    async def test_server_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        entity_ids = ["entity1", "entity2"]
        formatted_ids = ["entities/entity1", "entities/entity2"]
        mock_request_model.return_value.entity_ids = formatted_ids
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/_same"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await merge_entities(entity_ids, TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"

@pytest.mark.asyncio
class TestRejectEntityMatch:
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.RejectMatchRequest")
    async def test_successful_rejection(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        source_id = "source123"
        target_id = "target456"
        mock_request_model.return_value.source_id = source_id
        mock_request_model.return_value.target_id = target_id
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://reltio.api/entities/{source_id}/_notMatch"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"status": "success"}
        result = await reject_entity_match(source_id, target_id, TENANT_ID)
        assert isinstance(result, dict)
        assert result["status"] == "success"
        mock_http.assert_called_once_with(
            mock_get_url.return_value,
            method='POST',
            params={"uri": f"entities/{target_id}"},
            headers=mock_headers.return_value
        )
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.RejectMatchRequest")
    async def test_successful_rejection_empty_response(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        source_id = "source123"
        target_id = "target456"
        mock_request_model.return_value.source_id = source_id
        mock_request_model.return_value.target_id = target_id
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://reltio.api/entities/{source_id}/_notMatch"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = None  # API returns empty response
        result = await reject_entity_match(source_id, target_id, TENANT_ID)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "Successfully rejected match" in result["message"]
    
    @patch("src.tools.entity.RejectMatchRequest", side_effect=ValueError("Invalid ID"))
    async def test_validation_error(self, _):
        result = await reject_entity_match("!invalid!", "target123", TENANT_ID)
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
    
    @patch("src.tools.entity.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.RejectMatchRequest")
    async def test_authentication_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate):
        source_id = "source123"
        target_id = "target456"
        mock_request_model.return_value.source_id = source_id
        mock_request_model.return_value.target_id = target_id
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://reltio.api/entities/{source_id}/_notMatch"
        
        result = await reject_entity_match(source_id, target_id, TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.RejectMatchRequest")
    async def test_entity_not_found(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        source_id = "source123"
        target_id = "target456"
        mock_request_model.return_value.source_id = source_id
        mock_request_model.return_value.target_id = target_id
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://reltio.api/entities/{source_id}/_notMatch"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await reject_entity_match(source_id, target_id, TENANT_ID)
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("400 Bad Request"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.RejectMatchRequest")
    async def test_invalid_request(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        source_id = "source123"
        target_id = "target456"
        mock_request_model.return_value.source_id = source_id
        mock_request_model.return_value.target_id = target_id
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://reltio.api/entities/{source_id}/_notMatch"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await reject_entity_match(source_id, target_id, TENANT_ID)
        assert result["error"]["code_key"] == "INVALID_REQUEST"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.RejectMatchRequest")
    async def test_server_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        source_id = "source123"
        target_id = "target456"
        mock_request_model.return_value.source_id = source_id
        mock_request_model.return_value.target_id = target_id
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://reltio.api/entities/{source_id}/_notMatch"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await reject_entity_match(source_id, target_id, TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"

@pytest.mark.asyncio
class TestExportMergeTree:
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    async def test_successful_response(self, mock_get_url, mock_headers, mock_validate, mock_http):
        mock_get_url.return_value = "https://reltio.api/entities/123ABC"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"status": "completed"}

        result = await export_merge_tree("dummy.svr@email.com", TENANT_ID)

        assert isinstance(result, dict)
        assert result["status"] == "completed"

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    async def test_authentication_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        result = await export_merge_tree("dummy.svr@email.com", TENANT_ID)
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"

    @patch("src.tools.entity.http_request", side_effect=Exception("Internal Server Error"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    async def test_server_error(self, mock_get_url, mock_headers, mock_validate, mock_http):
        result = await export_merge_tree("dummy.svr@email.com", TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"

@pytest.mark.asyncio
class TestUnmergeEntityByContributor:
    """Test cases for the unmerge_entity_by_contributor function."""

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_by_contributor_success(self, mock_validate_security, mock_get_headers, mock_http_request):
        """Test successful unmerge of a contributor entity."""
        # Setup mocks
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        
        # Mock result with 'a' (modified origin) and 'b' (spawn) entities
        mock_result = {
            "a": {"uri": "entities/origin", "attributes": {}},
            "b": {"uri": "entities/contributor", "attributes": {}}
        }
        mock_http_request.return_value = mock_result

        # Call the function
        result = await unmerge_entity_by_contributor("origin", "contributor", "test_tenant")

        # Assertions
        assert result == mock_result
        mock_validate_security.assert_called_once()
        mock_get_headers.assert_called_once()
        mock_http_request.assert_called_once()
        
        # Verify the URL and parameters are correct
        call_args, call_kwargs = mock_http_request.call_args
        assert "entities/origin/_unmerge" in call_args[0]
        assert call_kwargs["params"]["contributorURI"] == "entities/contributor"
        assert call_kwargs["method"] == "POST"

    @patch("src.tools.entity.UnmergeEntityRequest")
    async def test_unmerge_entity_by_contributor_validation_error(self, mock_request_model):
        """Test unmerge with validation error."""
        # Setup mock to raise a validation error
        mock_request_model.side_effect = ValueError("Invalid entity ID")
        
        # Call the function
        result = await unmerge_entity_by_contributor("invalid-id", "contributor", "test_tenant")

        # Assertions
        assert "error" in result
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
        assert "Invalid entity ID" in result["error"]["message"]

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_by_contributor_not_found(self, mock_validate_security, mock_get_headers, mock_http_request):
        """Test unmerge with entity not found error."""
        # Setup mocks
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_http_request.side_effect = Exception("API Error: 404 Not Found")

        # Call the function
        result = await unmerge_entity_by_contributor("origin", "contributor", "test_tenant")

        # Assertions
        assert "error" in result
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"
        assert "not found" in result["error"]["message"]

@pytest.mark.asyncio
class TestUnmergeEntityTreeByContributor:
    """Test cases for the unmerge_entity_tree_by_contributor function."""

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_tree_by_contributor_success(self, mock_validate_security, mock_get_headers, mock_http_request):
        """Test successful tree unmerge of a contributor entity."""
        # Setup mocks
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        
        # Mock result with 'a' (modified origin) and 'b' (spawn) entities
        mock_result = {
            "a": {"uri": "entities/origin", "attributes": {}},
            "b": {"uri": "entities/contributor", "attributes": {}}
        }
        mock_http_request.return_value = mock_result

        # Call the function
        result = await unmerge_entity_tree_by_contributor("origin", "contributor", "test_tenant")

        # Assertions
        assert result == mock_result
        mock_validate_security.assert_called_once()
        mock_get_headers.assert_called_once()
        mock_http_request.assert_called_once()
        
        # Verify the URL and parameters are correct
        call_args, call_kwargs = mock_http_request.call_args
        assert "entities/origin/_treeUnmerge" in call_args[0]
        assert call_kwargs["params"]["contributorURI"] == "entities/contributor"
        assert call_kwargs["method"] == "POST"

    @patch("src.tools.entity.UnmergeEntityRequest")
    async def test_unmerge_entity_tree_by_contributor_validation_error(self, mock_request_model):
        """Test tree unmerge with validation error."""
        # Setup mock to raise a validation error
        mock_request_model.side_effect = ValueError("Invalid entity ID")
        
        # Call the function
        result = await unmerge_entity_tree_by_contributor("invalid-id", "contributor", "test_tenant")

        # Assertions
        assert "error" in result
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
        assert "Invalid entity ID" in result["error"]["message"]

    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_unmerge_entity_tree_by_contributor_not_found(self, mock_validate_security, mock_get_headers, mock_http_request):
        """Test tree unmerge with entity not found error."""
        # Setup mocks
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_http_request.side_effect = Exception("API Error: 404 Not Found")

        # Call the function
        result = await unmerge_entity_tree_by_contributor("origin", "contributor", "test_tenant")

        # Assertions
        assert "error" in result
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"
        assert "not found" in result["error"]["message"]


@pytest.mark.asyncio
class TestGetEntityWithMatches:
    """Test suite for get_entity_with_matches function"""
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity")
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_successful_with_matches(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful retrieval of entity with matches"""
        # Setup mocks
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = True
        mock_request_model.return_value.match_attributes = []
        mock_request_model.return_value.match_limit = 5
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        # Source entity, matches result, total matches result
        mock_http.side_effect = [
            {"label": "Test Entity", "attributes": {"FirstName": [{"value": "John"}]}},
            [{"object": {"uri": f"entities/{ENTITY_ID}2"}, "label": "Match Entity", "matchRules": ["BaseRule05"], "relevance": 0.95, "createdTime": 1234567890}],
            [{"object": {"uri": f"entities/{ENTITY_ID}2"}, "label": "Match Entity", "matchRules": ["BaseRule05"], "relevance": 0.95, "createdTime": 1234567890}, {"object": {"uri": f"entities/{ENTITY_ID}3"}, "label": "Match Entity 2", "matchRules": ["BaseRule06"], "relevance": 0.90, "createdTime": 1234567891}]
        ]
        
        result = await get_entity_with_matches(ENTITY_ID, [], True, [], 5, TENANT_ID)
        
        # Verify result structure
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
        assert "matches" in parsed_result
        assert "total_matches" in parsed_result
    
    @patch("src.tools.entity.EntityWithMatchesRequest", side_effect=ValueError("Invalid entity ID"))
    async def test_validation_error(self, mock_request_model):
        """Test validation error handling"""
        result = await get_entity_with_matches("!invalid!", [], True, [], 5, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
    
    @patch("src.tools.entity.get_reltio_headers", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_authentication_error(self, mock_request_model, mock_headers):
        """Test authentication error handling"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        
        result = await get_entity_with_matches(ENTITY_ID, [], True, [], 5, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
class TestCreateEntities:
    """Test suite for create_entities function"""
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity")
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.CreateEntitiesRequest")
    async def test_successful_create(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful entity creation"""
        # Setup mocks
        entities = [{"type": "configuration/entityTypes/Individual", "attributes": {"FirstName": [{"value": "John"}]}}]
        mock_request_model.return_value.entities = entities
        mock_request_model.return_value.return_objects = False
        mock_request_model.return_value.execute_lca = True
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://api/entities"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = [{"index": 0, "successful": True, "uri": f"entities/{ENTITY_ID}"}]
        
        result = await create_entities(entities, False, True, TENANT_ID)
        
        # Verify result structure
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, list)
        assert parsed_result[0]["successful"] is True
    
    @patch("src.tools.entity.CreateEntitiesRequest", side_effect=ValueError("Invalid entities"))
    async def test_validation_error(self, mock_request_model):
        """Test validation error for invalid entities"""
        result = await create_entities([], False, True, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("400 Bad Request"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.CreateEntitiesRequest")
    async def test_invalid_request_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test 400 Bad Request handling"""
        entities = [{"type": "Invalid"}]
        mock_request_model.return_value.entities = entities
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.return_objects = False
        mock_request_model.return_value.execute_lca = True
        mock_get_url.return_value = "https://api/entities"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await create_entities(entities, False, True, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "INVALID_REQUEST"


@pytest.mark.asyncio
class TestGetEntityHops:
    """Test suite for get_entity_hops function"""
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity")
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_successful_hops(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful entity graph traversal"""
        # Setup mocks
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "entities": [{"uri": f"entities/{ENTITY_ID}", "label": "Test Entity", "attributes": {}}],
            "relations": [],
            "dataComplete": True
        }
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 100, True, False, True, False, "ovOnly", TENANT_ID)
        
        # Verify result structure
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "entities" in parsed_result
        assert "relations" in parsed_result
        assert "dataComplete" in parsed_result
    
    @patch("src.tools.entity.EntityIdRequest", side_effect=ValueError("Invalid entity ID"))
    async def test_validation_error(self, mock_request_model):
        """Test validation error for invalid entity ID"""
        result = await get_entity_hops("!invalid!", "label", "", "", "", 1, 100, True, False, True, False, "ovOnly", TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_entity_not_found(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test 404 Not Found handling"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 100, True, False, True, False, "ovOnly", TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
class TestGetEntityParents:
    """Test suite for get_entity_parents function"""
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity")
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.GetEntityParentsRequest")
    async def test_successful_parents(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test successful parent path retrieval"""
        # Setup mocks
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.graph_type_uris = "Hierarchy"
        mock_request_model.return_value.select = "uri,label,type"
        mock_request_model.return_value.options = ""
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_parents"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "parentPaths": [[{"entityUri": f"entities/{ENTITY_ID}"}]],
            "entities": {f"entities/{ENTITY_ID}": {"uri": f"entities/{ENTITY_ID}", "label": "Test"}},
            "relations": {}
        }
        
        result = await get_entity_parents(ENTITY_ID, "Hierarchy", "uri,label,type", "", TENANT_ID)
        
        # Verify result structure
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "parentPaths" in parsed_result
        assert "entities" in parsed_result
        assert "relations" in parsed_result
    
    @patch("src.tools.entity.GetEntityParentsRequest", side_effect=ValueError("Invalid parameters"))
    async def test_validation_error(self, mock_request_model):
        """Test validation error for invalid parameters"""
        result = await get_entity_parents("!invalid!", "", "uri", "", TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "VALIDATION_ERROR"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.GetEntityParentsRequest")
    async def test_entity_not_found(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test entity not found error handling"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.graph_type_uris = "Hierarchy"
        mock_request_model.return_value.select = "uri"
        mock_request_model.return_value.options = ""
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_parents"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_parents(ENTITY_ID, "Hierarchy", "uri", "", TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"


# Test filter_entity function
class TestFilterEntity:
    """Test suite for filter_entity helper function"""
    
    def test_filter_entity_none_filter(self):
        """Test that None filter returns entity as-is"""
        entity = {"id": "123", "name": "Test"}
        result = filter_entity(entity, None)
        assert result == entity
    
    def test_filter_entity_field_not_in_entity(self):
        """Test filtering when field doesn't exist in entity"""
        entity = {"id": "123", "name": "Test"}
        result = filter_entity(entity, {"nonexistent": []})
        assert result == {}
    
    def test_filter_entity_empty_value(self):
        """Test filtering with empty values"""
        entity = {"id": "123", "name": "", "data": []}
        result = filter_entity(entity, {"name": [], "data": []})
        assert result == {}
    
    def test_filter_entity_dict_with_subfields(self):
        """Test filtering dict with specific subfields"""
        entity = {
            "attributes": {
                "FirstName": [{"value": "John"}],
                "LastName": [{"value": "Doe"}],
                "Age": [{"value": "30"}]
            }
        }
        result = filter_entity(entity, {"attributes": ["FirstName", "Age"]})
        assert "attributes" in result
        assert "FirstName" in result["attributes"]
        assert "Age" in result["attributes"]
        assert "LastName" not in result["attributes"]
    
    def test_filter_entity_dict_without_subfields(self):
        """Test filtering dict without specific subfields (include all)"""
        entity = {
            "attributes": {
                "FirstName": [{"value": "John"}],
                "LastName": [{"value": "Doe"}]
            }
        }
        result = filter_entity(entity, {"attributes": []})
        assert "attributes" in result
        assert "FirstName" in result["attributes"]
        assert "LastName" in result["attributes"]
    
    def test_filter_entity_non_dict_value(self):
        """Test filtering non-dict values like lists and strings"""
        entity = {
            "tags": ["tag1", "tag2"],
            "type": "Individual"
        }
        result = filter_entity(entity, {"tags": [], "type": []})
        assert result["tags"] == ["tag1", "tag2"]
        assert result["type"] == "Individual"
    
    def test_filter_entity_invalid_subvalue(self):
        """Test filtering dict with invalid subvalues"""
        entity = {
            "attributes": {
                "FirstName": None,
                "LastName": "",
                "Age": []
            }
        }
        result = filter_entity(entity, {"attributes": ["FirstName", "LastName", "Age"]})
        assert result == {}
    
    def test_filter_entity_dict_with_empty_subfields(self):
        """Test filtering dict with empty subfields after validation"""
        entity = {
            "attributes": {
                "FirstName": "",
                "LastName": None
            }
        }
        result = filter_entity(entity, {"attributes": []})
        assert result == {}


@pytest.mark.asyncio
class TestGetEntityDetailsAdditional:
    """Additional test cases for get_entity_details to increase coverage"""
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_activity_log_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity logging failure doesn't break the function"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/123ABC"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "id": ENTITY_ID, 
            "label": "Test Entity",
            "attributes": {"FirstName": [{"value": "John"}]},
            "crosswalks": [{"type": "source1", "value": "123", "uri": "entities/123"}]
        }
        
        result = await get_entity_details(ENTITY_ID, None, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, (dict, list))
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_with_crosswalks(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test entity details with crosswalks"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/123ABC"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "id": ENTITY_ID,
            "attributes": {"FirstName": [{"value": "John"}]},
            "crosswalks": [{"type": "source1", "value": "123", "uri": "entities/123"}]
        }
        
        result = await get_entity_details(ENTITY_ID, {"attributes": [], "crosswalks": []}, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "crosswalks" in parsed_result
    
    @patch("src.tools.entity.EntityIdRequest")
    async def test_unexpected_exception(self, mock_request_model):
        """Test unexpected exception handling"""
        mock_request_model.side_effect = Exception("Unexpected error")
        
        result = await get_entity_details(ENTITY_ID, None, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestUpdateEntityAttributesAdditional:
    """Additional test cases for update_entity_attributes"""
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.UpdateEntityAttributesRequest")
    async def test_activity_log_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity logging failure doesn't break the function"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.updates = [{"op": "add", "path": "/attributes/FirstName", "value": "John"}]
        mock_get_url.return_value = "https://reltio.api/entities/123ABC/_update"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"id": ENTITY_ID, "label": "Test Entity"}
        
        result = await update_entity_attributes(ENTITY_ID, [{"op": "add"}], TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, (dict, list))
    
    @patch("src.tools.entity.UpdateEntityAttributesRequest")
    async def test_unexpected_exception(self, mock_request_model):
        """Test unexpected exception handling"""
        mock_request_model.side_effect = Exception("Unexpected error")
        
        result = await update_entity_attributes(ENTITY_ID, [], TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestGetEntityMatchesAdditional:
    """Additional test cases for get_entity_matches"""
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_max_results_below_min(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        """Test max_results constraint to minimum of 1"""
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.side_effect = [
            "https://api/entities/123ABC/_transitiveMatches",
            "https://api/entities/123ABC"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.side_effect = [
            [{"object": {"uri": "entities/match1"}, "matchRules": [], "createdTime": "2024-01-01", "matchScore": 95, "label": "Match"}],
            {"id": ENTITY_ID}
        ]
        
        result = await get_entity_matches(ENTITY_ID, TENANT_ID, max_results=0)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_max_results_above_limit(self, mock_req, mock_headers, mock_security, mock_url, mock_http):
        """Test max_results constraint to MAX_RESULTS_LIMIT"""
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.side_effect = [
            "https://api/entities/123ABC/_transitiveMatches",
            "https://api/entities/123ABC"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.side_effect = [
            [{"object": {"uri": "entities/match1"}, "matchRules": [], "createdTime": "2024-01-01", "matchScore": 95, "label": "Match"}],
            {"id": ENTITY_ID}
        ]
        
        result = await get_entity_matches(ENTITY_ID, TENANT_ID, max_results=10000)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
    
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_security_error(self, mock_req, mock_url, mock_headers, mock_security):
        """Test security error handling"""
        from src.util.exceptions import SecurityError
        mock_security.side_effect = SecurityError("Security error")
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.return_value = "https://api/entities/123ABC/_transitiveMatches"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_matches(ENTITY_ID, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "SECURITY_ERROR"
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_activity_log_failure(self, mock_req, mock_headers, mock_security, mock_url, mock_http, mock_activity_log):
        """Test activity logging failure doesn't break function"""
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.side_effect = [
            "https://api/entities/123ABC/_transitiveMatches",
            "https://api/entities/123ABC"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.side_effect = [
            [{"object": {"uri": "entities/match1"}, "matchRules": [], "createdTime": "2024-01-01", "matchScore": 95, "label": "Match"}],
            {"id": ENTITY_ID, "label": "Entity"}
        ]
        
        result = await get_entity_matches(ENTITY_ID, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
    
    @patch("src.tools.entity.EntityIdRequest")
    async def test_unexpected_exception(self, mock_req):
        """Test unexpected exception handling"""
        mock_req.side_effect = Exception("Unexpected error")
        
        result = await get_entity_matches(ENTITY_ID, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestGetEntityMatchHistoryAdditional:
    """Additional test cases for get_entity_match_history"""
    
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_security_error(self, mock_req, mock_url, mock_headers, mock_security):
        """Test security error handling"""
        from src.util.exceptions import SecurityError
        mock_security.side_effect = SecurityError("Security error")
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.return_value = "https://api/entities/123ABC/_crosswalkTree"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_match_history(ENTITY_ID, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "SECURITY_ERROR"
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_activity_log_failure_with_results(self, mock_req, mock_headers, mock_security, mock_url, mock_http, mock_activity_log):
        """Test activity logging failure doesn't break function when results exist"""
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.side_effect = [
            "https://api/entities/123ABC/_crosswalkTree",
            "https://api/entities/123ABC"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.side_effect = [
            {"crosswalks": [{"uri": "entities/123", "type": "source1"}]},
            {"id": ENTITY_ID, "label": "Entity"}
        ]
        
        result = await get_entity_match_history(ENTITY_ID, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, (dict, list))
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request", side_effect=[[], {"id": ENTITY_ID}])
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_activity_log_failure_no_results(self, mock_req, mock_headers, mock_security, mock_url, mock_http, mock_activity_log):
        """Test activity logging failure when no results"""
        mock_req.return_value.entity_id = ENTITY_ID
        mock_req.return_value.tenant_id = TENANT_ID
        mock_url.return_value = "https://api/entities/123ABC/_crosswalkTree"
        
        result = await get_entity_match_history(ENTITY_ID, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "match_history" in parsed_result
    
    @patch("src.tools.entity.EntityIdRequest")
    async def test_unexpected_exception(self, mock_req):
        """Test unexpected exception handling"""
        mock_req.side_effect = Exception("Unexpected error")
        
        result = await get_entity_match_history(ENTITY_ID, TENANT_ID)
        if isinstance(result, str):
            result = yaml.safe_load(result)
        assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestMergeEntitiesAdditional:
    """Additional test cases for merge_entities"""
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.MergeEntitiesRequest")
    async def test_activity_log_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity logging failure doesn't break the function"""
        entity_ids = ["entity1", "entity2"]
        formatted_ids = ["entities/entity1", "entities/entity2"]
        mock_request_model.return_value.entity_ids = formatted_ids
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://reltio.api/entities/_same"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"id": "merged_entity_id", "status": "success"}
        
        result = await merge_entities(entity_ids, TENANT_ID)
        assert isinstance(result, dict)
    
    @patch("src.tools.entity.MergeEntitiesRequest")
    async def test_unexpected_exception(self, mock_request_model):
        """Test unexpected exception handling"""
        mock_request_model.side_effect = Exception("Unexpected error")
        
        result = await merge_entities(["entity1", "entity2"], TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestRejectEntityMatchAdditional:
    """Additional test cases for reject_entity_match"""
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.RejectMatchRequest")
    async def test_activity_log_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity logging failure doesn't break the function"""
        source_id = "source123"
        target_id = "target456"
        mock_request_model.return_value.source_id = source_id
        mock_request_model.return_value.target_id = target_id
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://reltio.api/entities/{source_id}/_notMatch"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"status": "success"}
        
        result = await reject_entity_match(source_id, target_id, TENANT_ID)
        assert isinstance(result, dict)
    
    @patch("src.tools.entity.RejectMatchRequest")
    async def test_unexpected_exception(self, mock_request_model):
        """Test unexpected exception handling"""
        mock_request_model.side_effect = Exception("Unexpected error")
        
        result = await reject_entity_match("source", "target", TENANT_ID)
        assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestExportMergeTreeAdditional:
    """Additional test cases for export_merge_tree"""
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_export_job_url")
    async def test_activity_log_failure(self, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity logging failure doesn't break the function"""
        mock_get_url.return_value = "https://reltio.api/entities/_crosswalksTree"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"status": "completed"}
        
        result = await export_merge_tree("dummy.svr@email.com", TENANT_ID)
        assert isinstance(result, dict)
    
    async def test_unexpected_exception(self):
        """Test unexpected exception handling"""
        with patch("src.tools.entity.get_reltio_export_job_url", side_effect=Exception("Unexpected error")):
            result = await export_merge_tree("dummy.svr@email.com", TENANT_ID)
            assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestUnmergeEntityByContributorAdditional:
    """Additional test cases for unmerge_entity_by_contributor"""
    
    @patch("src.tools.entity.http_request", side_effect=Exception("400 Bad Request"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_invalid_request_error(self, mock_validate_security, mock_get_headers, mock_http_request):
        """Test unmerge with 400 Bad Request error"""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await unmerge_entity_by_contributor("origin", "contributor", "test_tenant")
        
        assert "error" in result
        assert result["error"]["code_key"] == "INVALID_REQUEST"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("500 Internal Server Error"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_server_error(self, mock_validate_security, mock_get_headers, mock_http_request):
        """Test unmerge with server error"""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await unmerge_entity_by_contributor("origin", "contributor", "test_tenant")
        
        assert "error" in result
        assert result["error"]["code_key"] == "SERVER_ERROR"
    
    @patch("src.tools.entity.get_reltio_headers", side_effect=Exception("Auth failed"))
    async def test_authentication_error(self, mock_get_headers):
        """Test unmerge with authentication error"""
        result = await unmerge_entity_by_contributor("origin", "contributor", "test_tenant")
        
        assert "error" in result
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_activity_log_failure(self, mock_validate_security, mock_get_headers, mock_http_request, mock_activity_log):
        """Test that activity logging failure doesn't break function"""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_http_request.return_value = {"a": {"uri": "entities/origin"}, "b": {"uri": "entities/contributor"}}
        
        result = await unmerge_entity_by_contributor("origin", "contributor", "test_tenant")
        assert isinstance(result, dict)
    
    async def test_unexpected_exception(self):
        """Test unexpected exception handling"""
        with patch("src.tools.entity.UnmergeEntityRequest", side_effect=Exception("Unexpected")):
            result = await unmerge_entity_by_contributor("origin", "contributor", "test_tenant")
            assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestUnmergeEntityTreeByContributorAdditional:
    """Additional test cases for unmerge_entity_tree_by_contributor"""
    
    @patch("src.tools.entity.http_request", side_effect=Exception("400 Bad Request"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_invalid_request_error(self, mock_validate_security, mock_get_headers, mock_http_request):
        """Test tree unmerge with 400 Bad Request error"""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await unmerge_entity_tree_by_contributor("origin", "contributor", "test_tenant")
        
        assert "error" in result
        assert result["error"]["code_key"] == "INVALID_REQUEST"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("500 Internal Server Error"))
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_server_error(self, mock_validate_security, mock_get_headers, mock_http_request):
        """Test tree unmerge with server error"""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await unmerge_entity_tree_by_contributor("origin", "contributor", "test_tenant")
        
        assert "error" in result
        assert result["error"]["code_key"] == "SERVER_ERROR"
    
    @patch("src.tools.entity.get_reltio_headers", side_effect=Exception("Auth failed"))
    async def test_authentication_error(self, mock_get_headers):
        """Test tree unmerge with authentication error"""
        result = await unmerge_entity_tree_by_contributor("origin", "contributor", "test_tenant")
        
        assert "error" in result
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.validate_connection_security")
    async def test_activity_log_failure(self, mock_validate_security, mock_get_headers, mock_http_request, mock_activity_log):
        """Test that activity logging failure doesn't break function"""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_http_request.return_value = {"a": {"uri": "entities/origin"}, "b": {"uri": "entities/contributor"}}
        
        result = await unmerge_entity_tree_by_contributor("origin", "contributor", "test_tenant")
        assert isinstance(result, dict)
    
    async def test_unexpected_exception(self):
        """Test unexpected exception handling"""
        with patch("src.tools.entity.UnmergeEntityRequest", side_effect=Exception("Unexpected")):
            result = await unmerge_entity_tree_by_contributor("origin", "contributor", "test_tenant")
            assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestGetEntityWithMatchesAdditional:
    """Additional test cases for get_entity_with_matches"""
    
    @patch("src.tools.entity.http_request", side_effect=Exception("404 Not Found"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_entity_not_found(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test entity not found error"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = True
        mock_request_model.return_value.match_attributes = []
        mock_request_model.return_value.match_limit = 5
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_with_matches(ENTITY_ID, [], True, [], 5, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("500 Server Error"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_server_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test server error handling"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = True
        mock_request_model.return_value.match_attributes = []
        mock_request_model.return_value.match_limit = 5
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_with_matches(ENTITY_ID, [], True, [], 5, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "SERVER_ERROR"
    
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_security_error_source(self, mock_request_model, mock_get_url, mock_headers, mock_validate):
        """Test security error for source entity"""
        from src.util.exceptions import SecurityError
        mock_validate.side_effect = SecurityError("Security error")
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = True
        mock_request_model.return_value.match_attributes = []
        mock_request_model.return_value.match_limit = 5
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_with_matches(ENTITY_ID, [], True, [], 5, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "SECURITY_ERROR"
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_security_error_matches(self, mock_request_model, mock_get_url, mock_headers, mock_validate_security, mock_http):
        """Test security error for matches"""
        from src.util.exceptions import SecurityError
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = True
        mock_request_model.return_value.match_attributes = []
        mock_request_model.return_value.match_limit = 5
        
        # First call for source entity succeeds, second call for matches security check fails
        mock_validate_security.side_effect = [None, SecurityError("Security error")]
        mock_get_url.side_effect = [
            f"https://api/entities/{ENTITY_ID}",
            f"https://api/entities/{ENTITY_ID}/_transitiveMatches"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"label": "Test Entity", "attributes": {}}
        
        result = await get_entity_with_matches(ENTITY_ID, [], True, [], 5, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "SECURITY_ERROR"
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_activity_log_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity logging failure doesn't break function"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = False
        mock_request_model.return_value.match_attributes = []
        mock_request_model.return_value.match_limit = 5
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.side_effect = [
            {"label": "Test Entity", "attributes": {}},
            [],
            []
        ]
        
        result = await get_entity_with_matches(ENTITY_ID, [], False, [], 5, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_matches_api_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test handling when matches API fails"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = True
        mock_request_model.return_value.match_attributes = []
        mock_request_model.return_value.match_limit = 5
        mock_get_url.side_effect = [
            f"https://api/entities/{ENTITY_ID}",
            f"https://api/entities/{ENTITY_ID}/_transitiveMatches"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        # Source entity succeeds, matches API fails, total count fails
        mock_http.side_effect = [
            {"label": "Test Entity", "attributes": {}},
            Exception("Matches API error"),
            Exception("Total count error")
        ]
        
        result = await get_entity_with_matches(ENTITY_ID, [], True, [], 5, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
        assert "matches" in parsed_result
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_total_count_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test handling when total count API fails"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = True
        mock_request_model.return_value.match_attributes = []
        mock_request_model.return_value.match_limit = 5
        mock_get_url.side_effect = [
            f"https://api/entities/{ENTITY_ID}",
            f"https://api/entities/{ENTITY_ID}/_transitiveMatches"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.side_effect = [
            {"label": "Test Entity", "attributes": {}},
            [{"object": {"uri": "entities/match1"}, "label": "Match", "matchRules": [], "relevance": 0.95, "createdTime": 123}],
            Exception("Total count error")
        ]
        
        result = await get_entity_with_matches(ENTITY_ID, [], True, [], 5, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
        assert "total_matches" in parsed_result
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_match_entity_fetch_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test handling when fetching match entity details fails"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = True
        mock_request_model.return_value.match_attributes = ["FirstName"]
        mock_request_model.return_value.match_limit = 5
        mock_get_url.side_effect = [
            f"https://api/entities/{ENTITY_ID}",
            f"https://api/entities/{ENTITY_ID}/_transitiveMatches",
            f"https://api/entities/match1"
        ]
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.side_effect = [
            {"label": "Test Entity", "attributes": {"FirstName": [{"value": "John"}]}},
            [{"object": {"uri": "entities/match1"}, "label": "Match", "matchRules": [], "relevance": 0.95, "createdTime": 123}],
            [{"object": {"uri": "entities/match1"}, "label": "Match", "matchRules": [], "relevance": 0.95, "createdTime": 123}],
            Exception("Match entity fetch error")
        ]
        
        result = await get_entity_with_matches(ENTITY_ID, [], True, ["FirstName"], 5, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityWithMatchesRequest")
    async def test_with_crosswalks(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test entity with matches including crosswalks"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.attributes = []
        mock_request_model.return_value.include_match_attributes = False
        mock_request_model.return_value.match_attributes = []
        mock_request_model.return_value.match_limit = 5
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.side_effect = [
            {
                "label": "Test Entity",
                "attributes": {},
                "crosswalks": [{"type": "source1", "value": "123", "uri": "entities/123"}]
            },
            [],
            []
        ]
        
        result = await get_entity_with_matches(ENTITY_ID, [], False, [], 5, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "source_entity" in parsed_result
        assert "crosswalks" in parsed_result["source_entity"]
    
    async def test_unexpected_exception(self):
        """Test unexpected exception handling"""
        with patch("src.tools.entity.EntityWithMatchesRequest", side_effect=Exception("Unexpected")):
            result = await get_entity_with_matches(ENTITY_ID, [], True, [], 5, TENANT_ID)
            assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestCreateEntitiesAdditional:
    """Additional test cases for create_entities"""
    
    @patch("src.tools.entity.http_request", side_effect=Exception("401 Unauthorized"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.CreateEntitiesRequest")
    async def test_unauthorized_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test 401 Unauthorized handling"""
        entities = [{"type": "Individual"}]
        mock_request_model.return_value.entities = entities
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.return_objects = False
        mock_request_model.return_value.execute_lca = True
        mock_get_url.return_value = "https://api/entities"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await create_entities(entities, False, True, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.entity.http_request", side_effect=Exception("403 Forbidden"))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.CreateEntitiesRequest")
    async def test_forbidden_error(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test 403 Forbidden handling"""
        entities = [{"type": "Individual"}]
        mock_request_model.return_value.entities = entities
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.return_objects = False
        mock_request_model.return_value.execute_lca = True
        mock_get_url.return_value = "https://api/entities"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await create_entities(entities, False, True, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "AUTHORIZATION_ERROR"
    
    @patch("src.tools.entity.get_reltio_headers", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.CreateEntitiesRequest")
    async def test_authentication_error(self, mock_request_model, mock_headers):
        """Test authentication error"""
        entities = [{"type": "Individual"}]
        mock_request_model.return_value.entities = entities
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.return_objects = False
        mock_request_model.return_value.execute_lca = True
        
        result = await create_entities(entities, False, True, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.CreateEntitiesRequest")
    async def test_activity_log_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity logging failure doesn't break function"""
        entities = [{"type": "Individual"}]
        mock_request_model.return_value.entities = entities
        mock_request_model.return_value.return_objects = False
        mock_request_model.return_value.execute_lca = True
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://api/entities"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = [{"index": 0, "successful": True, "uri": f"entities/{ENTITY_ID}"}]
        
        result = await create_entities(entities, False, True, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, list)
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.CreateEntitiesRequest")
    async def test_with_return_objects(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test create entities with return_objects=True"""
        entities = [{"type": "Individual"}]
        mock_request_model.return_value.entities = entities
        mock_request_model.return_value.return_objects = True
        mock_request_model.return_value.execute_lca = True
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://api/entities"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = [{
            "index": 0,
            "successful": True,
            "object": {
                "uri": f"entities/{ENTITY_ID}",
                "type": "configuration/entityTypes/Individual",
                "tags": [],
                "createdBy": "user",
                "createdTime": 123456789,
                "updatedBy": "user",
                "updatedTime": 123456789,
                "isFavorite": False,
                "label": "Test Entity",
                "crosswalks": []
            }
        }]
        
        result = await create_entities(entities, True, True, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, list)
        assert "object" in parsed_result[0]
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.CreateEntitiesRequest")
    async def test_failed_creation(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test create entities with failed creation"""
        entities = [{"type": "Individual"}]
        mock_request_model.return_value.entities = entities
        mock_request_model.return_value.return_objects = False
        mock_request_model.return_value.execute_lca = True
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://api/entities"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = [{
            "index": 0,
            "successful": False,
            "errors": [{"errorCode": "E001", "errorMessage": "Validation failed"}]
        }]
        
        result = await create_entities(entities, False, True, TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert isinstance(parsed_result, list)
        assert parsed_result[0]["successful"] is False
        assert "errors" in parsed_result[0]
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.CreateEntitiesRequest")
    async def test_unexpected_response_format(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test create entities with unexpected response format"""
        entities = [{"type": "Individual"}]
        mock_request_model.return_value.entities = entities
        mock_request_model.return_value.return_objects = False
        mock_request_model.return_value.execute_lca = True
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = "https://api/entities"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"unexpected": "format"}  # Not a list
        
        result = await create_entities(entities, False, True, TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "UNEXPECTED_RESPONSE"
    
    async def test_unexpected_exception(self):
        """Test unexpected exception handling"""
        with patch("src.tools.entity.CreateEntitiesRequest", side_effect=Exception("Unexpected")):
            result = await create_entities([{"type": "Individual"}], False, True, TENANT_ID)
            assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestGetEntityHopsAdditional:
    """Additional test cases for get_entity_hops"""
    
    @patch("src.tools.entity.get_reltio_headers", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.EntityIdRequest")
    async def test_authentication_error(self, mock_request_model, mock_headers):
        """Test authentication error"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 100, True, False, True, False, "ovOnly", TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_max_results_below_min(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test max_results constraint to minimum"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"entities": [], "relations": [], "dataComplete": True}
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 0, True, False, True, False, "ovOnly", TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "entities" in parsed_result
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_max_results_above_limit(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test max_results constraint to maximum"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"entities": [], "relations": [], "dataComplete": True}
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 2000, True, False, True, False, "ovOnly", TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "entities" in parsed_result
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_deep_below_min(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test deep constraint to minimum"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"entities": [], "relations": [], "dataComplete": True}
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 0, 100, True, False, True, False, "ovOnly", TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "entities" in parsed_result
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_deep_above_max(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test deep constraint to maximum"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"entities": [], "relations": [], "dataComplete": True}
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 20, 100, True, False, True, False, "ovOnly", TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "entities" in parsed_result
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_with_uri_filters(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test with URI filters"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"entities": [], "relations": [], "dataComplete": True}
        
        result = await get_entity_hops(
            ENTITY_ID, "label",
            "graph1,graph2",
            "relation1,relation2",
            "entity1,entity2",
            1, 100, True, False, True, False, "ovOnly", TENANT_ID
        )
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "entities" in parsed_result
    
    @patch("src.tools.entity.http_request", side_effect=Exception('{"errorMessage": "Entity not found"}'))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_json_error_message_extraction(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test extraction of error message from JSON response"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 100, True, False, True, False, "ovOnly", TENANT_ID)
        
        assert "error" in result
    
    @patch("src.tools.entity.http_request", side_effect=Exception('400 Bad Request: {"errorMessage": "Invalid parameters"}'))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_400_bad_request_with_message(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test 400 Bad Request with error message"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 100, True, False, True, False, "ovOnly", TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "INVALID_REQUEST"
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_with_entities_and_crosswalks(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test with entities that have attributes and crosswalks"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "entities": [{
                "uri": f"entities/{ENTITY_ID}",
                "type": "Individual",
                "label": "Test Entity",
                "secondaryLabel": "Secondary",
                "traversedRelations": 2,
                "untraversedRelations": 1,
                "attributes": {"FirstName": [{"value": "John"}]},
                "crosswalks": [{"type": "source1", "value": "123"}]
            }],
            "relations": [],
            "dataComplete": True
        }
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 100, True, False, True, False, "ovOnly", TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "entities" in parsed_result
        assert len(parsed_result["entities"]) == 1
        assert "crosswalks" in parsed_result["entities"][0]
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.EntityIdRequest")
    async def test_activity_log_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity logging failure doesn't break function"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_hops"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {"entities": [], "relations": [], "dataComplete": True}
        
        result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 100, True, False, True, False, "ovOnly", TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "entities" in parsed_result
    
    async def test_unexpected_exception(self):
        """Test unexpected exception handling"""
        with patch("src.tools.entity.EntityIdRequest", side_effect=Exception("Unexpected")):
            result = await get_entity_hops(ENTITY_ID, "label", "", "", "", 1, 100, True, False, True, False, "ovOnly", TENANT_ID)
            assert result["error"]["code_key"] == "SERVER_ERROR"


@pytest.mark.asyncio
class TestGetEntityParentsAdditional:
    """Additional test cases for get_entity_parents"""
    
    @patch("src.tools.entity.get_reltio_headers", side_effect=Exception("Auth failed"))
    @patch("src.tools.entity.GetEntityParentsRequest")
    async def test_authentication_error(self, mock_request_model, mock_headers):
        """Test authentication error"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.graph_type_uris = "Hierarchy"
        mock_request_model.return_value.select = "uri"
        mock_request_model.return_value.options = ""
        
        result = await get_entity_parents(ENTITY_ID, "Hierarchy", "uri", "", TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "AUTHENTICATION_ERROR"
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.GetEntityParentsRequest")
    async def test_with_options(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test with options parameter"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.graph_type_uris = "Hierarchy"
        mock_request_model.return_value.select = "uri,label"
        mock_request_model.return_value.options = "sendHidden,ovOnly"
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_parents"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "parentPaths": [],
            "entities": {},
            "relations": {}
        }
        
        result = await get_entity_parents(ENTITY_ID, "Hierarchy", "uri,label", "sendHidden,ovOnly", TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "parentPaths" in parsed_result
    
    @patch("src.tools.entity.http_request", side_effect=Exception('{"errorCode": 119, "errorMessage": "Graph type not found"}'))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.GetEntityParentsRequest")
    async def test_error_code_119(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test error code 119 (graph type not found)"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.graph_type_uris = "NonExistent"
        mock_request_model.return_value.select = "uri"
        mock_request_model.return_value.options = ""
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_parents"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_parents(ENTITY_ID, "NonExistent", "uri", "", TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "RESOURCE_NOT_FOUND"
    
    @patch("src.tools.entity.http_request", side_effect=Exception('400 Bad Request: {"errorMessage": "Invalid select"}'))
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.GetEntityParentsRequest")
    async def test_400_bad_request(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test 400 Bad Request"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.graph_type_uris = "Hierarchy"
        mock_request_model.return_value.select = "invalid"
        mock_request_model.return_value.options = ""
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_parents"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        
        result = await get_entity_parents(ENTITY_ID, "Hierarchy", "invalid", "", TENANT_ID)
        
        assert "error" in result
        assert result["error"]["code_key"] == "INVALID_REQUEST"
    
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.GetEntityParentsRequest")
    async def test_with_entity_attributes(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http):
        """Test with entities that have attributes"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.graph_type_uris = "Hierarchy"
        mock_request_model.return_value.select = "uri,label,attributes"
        mock_request_model.return_value.options = ""
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_parents"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "parentPaths": [[{"entityUri": f"entities/{ENTITY_ID}"}]],
            "entities": {
                f"entities/{ENTITY_ID}": {
                    "uri": f"entities/{ENTITY_ID}",
                    "type": "Individual",
                    "label": "Test",
                    "secondaryLabel": "Secondary",
                    "attributes": {"FirstName": [{"value": "John"}]}
                }
            },
            "relations": {}
        }
        
        result = await get_entity_parents(ENTITY_ID, "Hierarchy", "uri,label,attributes", "", TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "entities" in parsed_result
        entity_key = f"entities/{ENTITY_ID}"
        assert entity_key in parsed_result["entities"]
        assert "attributes" in parsed_result["entities"][entity_key]
    
    @patch("src.tools.entity.ActivityLog.execute_and_log_activity", side_effect=Exception("Logging failed"))
    @patch("src.tools.entity.http_request")
    @patch("src.tools.entity.validate_connection_security")
    @patch("src.tools.entity.get_reltio_headers")
    @patch("src.tools.entity.get_reltio_url")
    @patch("src.tools.entity.GetEntityParentsRequest")
    async def test_activity_log_failure(self, mock_request_model, mock_get_url, mock_headers, mock_validate, mock_http, mock_activity_log):
        """Test that activity logging failure doesn't break function"""
        mock_request_model.return_value.entity_id = ENTITY_ID
        mock_request_model.return_value.tenant_id = TENANT_ID
        mock_request_model.return_value.graph_type_uris = "Hierarchy"
        mock_request_model.return_value.select = "uri"
        mock_request_model.return_value.options = ""
        mock_get_url.return_value = f"https://api/entities/{ENTITY_ID}/_parents"
        mock_headers.return_value = {"Authorization": "Bearer token"}
        mock_http.return_value = {
            "parentPaths": [],
            "entities": {},
            "relations": {}
        }
        
        result = await get_entity_parents(ENTITY_ID, "Hierarchy", "uri", "", TENANT_ID)
        parsed_result = yaml.safe_load(result) if isinstance(result, str) else result
        assert "parentPaths" in parsed_result
    
    async def test_unexpected_exception(self):
        """Test unexpected exception handling"""
        with patch("src.tools.entity.GetEntityParentsRequest", side_effect=Exception("Unexpected")):
            result = await get_entity_parents(ENTITY_ID, "Hierarchy", "uri", "", TENANT_ID)
            assert result["error"]["code_key"] == "SERVER_ERROR"

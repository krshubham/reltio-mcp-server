import unittest
from unittest.mock import patch
from pydantic import ValidationError
import uuid

from src.util.models import (
    EntityIdRequest,
    UpdateEntityAttributesRequest,
    MergeEntitiesRequest,
    RejectMatchRequest,
    EntitySearchRequest,
    MatchScoreRequest,
    ConfidenceLevelRequest,
    GetTotalMatchesRequest,
    GetMatchFacetsRequest,
    RelationIdRequest,
    MergeActivitiesRequest,
    UnmergeEntityRequest,
    CrosswalkModel,
    RelationObjectModel,
    RelationModel,
    CreateRelationsRequest,
    DeleteRelationRequest,
    GetEntityRelationsRequest,
    RelationSearchRequest,
    CheckUserActivityRequest,
    EntityInteractionsRequest,
    CreateInteractionRequest,
    LookupListRequest,
    GetUsersByRoleRequest,
    GetUsersByGroupRequest,
    GetUserWorkflowTasksRequest,
    ReassignWorkflowTaskRequest,
    GetPossibleAssigneesRequest,
    RetrieveTasksRequest,
    GetTaskDetailsRequest,
    StartProcessInstanceRequest,
    ExecuteTaskActionRequest,
    EntityWithMatchesRequest,
    CreateEntitiesRequest,
    GetEntityParentsRequest,
    UnifiedMatchRequest,
    GetPotentialMatchApisRequest
)

class TestEntityIdRequest(unittest.TestCase):
    """Test EntityIdRequest model"""
    
    def test_valid_entity_id(self):
        """Test valid entity ID"""
        request = EntityIdRequest(entity_id="123abc")
        self.assertEqual(request.entity_id, "123abc")
    
    def test_entity_id_with_uri_extraction(self):
        """Test entity ID extraction from URI"""
        with patch('src.util.models.extract_entity_id', return_value='extracted123'):
            request = EntityIdRequest(entity_id="entities/extracted123")
            self.assertEqual(request.entity_id, "extracted123")
    
    def test_default_tenant_id(self):
        """Test default tenant ID"""
        request = EntityIdRequest(entity_id="123abc")
        self.assertIsNotNone(request.tenant_id)
    
    def test_custom_options(self):
        """Test custom options"""
        request = EntityIdRequest(entity_id="123abc", options="option1,option2")
        self.assertEqual(request.options, "option1,option2")


class TestUpdateEntityAttributesRequest(unittest.TestCase):
    """Test UpdateEntityAttributesRequest model"""
    
    def test_valid_update_request(self):
        """Test valid update request"""
        request = UpdateEntityAttributesRequest(
            entity_id="123abc",
            updates=[{"op": "add", "path": "/Name", "value": "Test"}]
        )
        self.assertEqual(request.entity_id, "123abc")
        self.assertEqual(len(request.updates), 1)
    
    def test_default_always_create_dcr(self):
        """Test default always_create_dcr value"""
        request = UpdateEntityAttributesRequest(
            entity_id="123abc",
            updates=[{"op": "add", "path": "/Name", "value": "Test"}]
        )
        self.assertTrue(request.always_create_dcr)
    
    def test_default_overwrite_default_crosswalk_value(self):
        """Test default overwrite_default_crosswalk_value"""
        request = UpdateEntityAttributesRequest(
            entity_id="123abc",
            updates=[{"op": "add", "path": "/Name", "value": "Test"}]
        )
        self.assertTrue(request.overwrite_default_crosswalk_value)
    
    def test_change_request_id_extraction(self):
        """Test change request ID extraction"""
        with patch('src.util.models.extract_change_request_id', return_value='cr123'):
            request = UpdateEntityAttributesRequest(
                entity_id="123abc",
                updates=[{"op": "add"}],
                change_request_id="changerequest/cr123"
            )
            self.assertEqual(request.change_request_id, "cr123")


class TestMergeEntitiesRequest(unittest.TestCase):
    """Test MergeEntitiesRequest model"""
    
    def test_valid_merge_request(self):
        """Test valid merge request with two entity IDs"""
        request = MergeEntitiesRequest(entity_ids=["123abc", "456def"])
        self.assertEqual(len(request.entity_ids), 2)
    
    def test_entity_ids_formatting(self):
        """Test entity IDs are properly formatted"""
        with patch('src.util.models.extract_entity_id', side_effect=lambda x: x):
            request = MergeEntitiesRequest(entity_ids=["123abc", "456def"])
            self.assertTrue(all(eid.startswith("entities/") for eid in request.entity_ids))
    
    def test_invalid_entity_count_too_few(self):
        """Test validation error when less than two entities"""
        with self.assertRaises(ValidationError):
            MergeEntitiesRequest(entity_ids=["123abc"])
    
    def test_invalid_entity_count_too_many(self):
        """Test validation error when more than two entities"""
        with self.assertRaises(ValidationError):
            MergeEntitiesRequest(entity_ids=["123abc", "456def", "789ghi"])


class TestRejectMatchRequest(unittest.TestCase):
    """Test RejectMatchRequest model"""
    
    def test_valid_reject_match_request(self):
        """Test valid reject match request"""
        request = RejectMatchRequest(source_id="123abc", target_id="456def")
        self.assertEqual(request.source_id, "123abc")
        self.assertEqual(request.target_id, "456def")
    
    def test_entity_id_extraction(self):
        """Test entity ID extraction for both source and target"""
        with patch('src.util.models.extract_entity_id', return_value='extracted'):
            request = RejectMatchRequest(
                source_id="entities/extracted",
                target_id="entities/extracted"
            )
            self.assertEqual(request.source_id, "extracted")
            self.assertEqual(request.target_id, "extracted")


class TestEntitySearchRequest(unittest.TestCase):
    """Test EntitySearchRequest model"""
    
    def test_valid_search_request(self):
        """Test valid search request"""
        request = EntitySearchRequest(query="test query")
        self.assertEqual(request.query, "test query")
    
    def test_default_max_results(self):
        """Test default max_results"""
        request = EntitySearchRequest()
        self.assertEqual(request.max_results, 10)
    
    def test_default_offset(self):
        """Test default offset"""
        request = EntitySearchRequest()
        self.assertEqual(request.offset, 0)
    
    def test_query_sanitization(self):
        """Test query sanitization removes dangerous characters"""
        request = EntitySearchRequest(query='test<>query')
        self.assertNotIn('<', request.query)
        self.assertNotIn('>', request.query)
    
    def test_filter_validation_balanced_parentheses(self):
        """Test filter validation for balanced parentheses"""
        with self.assertRaises(ValidationError):
            EntitySearchRequest(filter="equals(field, value")
    
    def test_valid_filter_with_balanced_parentheses(self):
        """Test valid filter with balanced parentheses"""
        request = EntitySearchRequest(filter="equals(field, value)")
        self.assertEqual(request.filter, "equals(field, value)")
    
    def test_order_validation_invalid(self):
        """Test order validation rejects invalid values"""
        with self.assertRaises(ValidationError):
            EntitySearchRequest(order="invalid")
    
    def test_order_validation_valid(self):
        """Test order validation accepts valid values"""
        request = EntitySearchRequest(order="desc")
        self.assertEqual(request.order, "desc")
    
    def test_offset_max_results_validation(self):
        """Test that offset + max_results cannot exceed 10000"""
        with self.assertRaises(ValidationError):
            EntitySearchRequest(offset=9995, max_results=10)
    
    def test_default_select(self):
        """Test default select value"""
        request = EntitySearchRequest()
        self.assertEqual(request.select, "uri,label")
    
    def test_default_activeness(self):
        """Test default activeness value"""
        request = EntitySearchRequest()
        self.assertEqual(request.activeness, "active")


class TestMatchScoreRequest(unittest.TestCase):
    """Test MatchScoreRequest model"""
    
    def test_valid_match_score_request(self):
        """Test valid match score request"""
        request = MatchScoreRequest(start_match_score=50, end_match_score=100)
        self.assertEqual(request.start_match_score, 50)
        self.assertEqual(request.end_match_score, 100)
    
    def test_default_entity_type(self):
        """Test default entity type"""
        request = MatchScoreRequest()
        self.assertEqual(request.entity_type, "Individual")
    
    def test_score_range_validation(self):
        """Test that start_match_score must be <= end_match_score"""
        with self.assertRaises(ValidationError):
            MatchScoreRequest(start_match_score=80, end_match_score=50)
    
    def test_score_out_of_range_high(self):
        """Test score cannot exceed 100"""
        with self.assertRaises(ValidationError):
            MatchScoreRequest(start_match_score=0, end_match_score=150)
    
    def test_score_out_of_range_low(self):
        """Test score cannot be negative"""
        with self.assertRaises(ValidationError):
            MatchScoreRequest(start_match_score=-10, end_match_score=50)
    
    def test_offset_max_validation(self):
        """Test offset + max_results validation"""
        with self.assertRaises(ValidationError):
            MatchScoreRequest(offset=9995, max_results=10)


class TestConfidenceLevelRequest(unittest.TestCase):
    """Test ConfidenceLevelRequest model"""
    
    def test_valid_confidence_level_request(self):
        """Test valid confidence level request"""
        request = ConfidenceLevelRequest(confidence_level="High confidence")
        self.assertEqual(request.confidence_level, "High confidence")
    
    def test_default_confidence_level(self):
        """Test default confidence level"""
        request = ConfidenceLevelRequest()
        self.assertEqual(request.confidence_level, "Low confidence")
    
    def test_default_entity_type(self):
        """Test default entity type"""
        request = ConfidenceLevelRequest()
        self.assertEqual(request.entity_type, "Individual")
    
    def test_offset_max_validation(self):
        """Test offset + max_results validation"""
        with self.assertRaises(ValidationError):
            ConfidenceLevelRequest(offset=9995, max_results=10)


class TestGetTotalMatchesRequest(unittest.TestCase):
    """Test GetTotalMatchesRequest model"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = GetTotalMatchesRequest(min_matches=5)
        self.assertEqual(request.min_matches, 5)
    
    def test_default_min_matches(self):
        """Test default min_matches"""
        request = GetTotalMatchesRequest()
        self.assertEqual(request.min_matches, 0)
    
    def test_negative_min_matches(self):
        """Test negative min_matches validation"""
        with self.assertRaises(ValidationError):
            GetTotalMatchesRequest(min_matches=-1)


class TestGetMatchFacetsRequest(unittest.TestCase):
    """Test GetMatchFacetsRequest model"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = GetMatchFacetsRequest(min_matches=3)
        self.assertEqual(request.min_matches, 3)
    
    def test_negative_min_matches(self):
        """Test negative min_matches validation"""
        with self.assertRaises(ValidationError):
            GetMatchFacetsRequest(min_matches=-5)


class TestRelationIdRequest(unittest.TestCase):
    """Test RelationIdRequest model"""
    
    def test_valid_relation_id(self):
        """Test valid relation ID"""
        request = RelationIdRequest(relation_id="rel123")
        self.assertEqual(request.relation_id, "rel123")
    
    def test_relation_id_extraction(self):
        """Test relation ID extraction"""
        with patch('src.util.models.extract_relation_id', return_value='rel123'):
            request = RelationIdRequest(relation_id="relations/rel123")
            self.assertEqual(request.relation_id, "rel123")


class TestMergeActivitiesRequest(unittest.TestCase):
    """Test MergeActivitiesRequest model"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = MergeActivitiesRequest(timestamp_gt=1000000)
        self.assertEqual(request.timestamp_gt, 1000000)
    
    def test_invalid_timestamp_gt_zero(self):
        """Test timestamp_gt must be positive"""
        with self.assertRaises(ValidationError):
            MergeActivitiesRequest(timestamp_gt=0)
    
    def test_invalid_timestamp_gt_negative(self):
        """Test timestamp_gt cannot be negative"""
        with self.assertRaises(ValidationError):
            MergeActivitiesRequest(timestamp_gt=-1000)
    
    def test_timestamp_range_validation(self):
        """Test timestamp_lt must be greater than timestamp_gt"""
        with self.assertRaises(ValidationError):
            MergeActivitiesRequest(timestamp_gt=2000000, timestamp_lt=1000000)
    
    def test_valid_timestamp_range(self):
        """Test valid timestamp range"""
        request = MergeActivitiesRequest(timestamp_gt=1000000, timestamp_lt=2000000)
        self.assertEqual(request.timestamp_gt, 1000000)
        self.assertEqual(request.timestamp_lt, 2000000)
    
    def test_default_offset(self):
        """Test default offset"""
        request = MergeActivitiesRequest(timestamp_gt=1000000)
        self.assertEqual(request.offset, 0)
    
    def test_default_max_results(self):
        """Test default max_results"""
        request = MergeActivitiesRequest(timestamp_gt=1000000)
        self.assertEqual(request.max_results, 100)


class TestUnmergeEntityRequest(unittest.TestCase):
    """Test UnmergeEntityRequest model"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = UnmergeEntityRequest(
            origin_entity_id="123abc",
            contributor_entity_id="456def"
        )
        self.assertEqual(request.origin_entity_id, "123abc")
        self.assertEqual(request.contributor_entity_id, "456def")
    
    def test_entity_id_extraction(self):
        """Test entity ID extraction"""
        with patch('src.util.models.extract_entity_id', return_value='extracted'):
            request = UnmergeEntityRequest(
                origin_entity_id="entities/extracted",
                contributor_entity_id="entities/extracted"
            )
            self.assertEqual(request.origin_entity_id, "extracted")
            self.assertEqual(request.contributor_entity_id, "extracted")


class TestCrosswalkModel(unittest.TestCase):
    """Test CrosswalkModel"""
    
    def test_default_values(self):
        """Test default values"""
        model = CrosswalkModel()
        self.assertEqual(model.type, "configuration/sources/Reltio")
        self.assertEqual(model.sourceTable, "")
        # Value should be a UUID
        uuid.UUID(model.value)  # Will raise ValueError if not valid UUID
    
    def test_custom_values(self):
        """Test custom values"""
        model = CrosswalkModel(
            type="custom/type",
            sourceTable="custom_table",
            value="custom_value"
        )
        self.assertEqual(model.type, "custom/type")
        self.assertEqual(model.sourceTable, "custom_table")
        self.assertEqual(model.value, "custom_value")


class TestRelationObjectModel(unittest.TestCase):
    """Test RelationObjectModel"""
    
    def test_valid_with_object_uri(self):
        """Test valid model with objectURI"""
        model = RelationObjectModel(
            type="configuration/entityTypes/Organization",
            objectURI="entities/e1"
        )
        self.assertEqual(model.type, "configuration/entityTypes/Organization")
        self.assertEqual(model.objectURI, "entities/e1")
    
    def test_valid_with_crosswalks(self):
        """Test valid model with crosswalks"""
        model = RelationObjectModel(
            type="configuration/entityTypes/Organization",
            crosswalks=[CrosswalkModel()]
        )
        self.assertIsNotNone(model.crosswalks)
    
    def test_invalid_without_identification(self):
        """Test validation error when neither objectURI nor crosswalks provided"""
        with self.assertRaises(ValidationError):
            RelationObjectModel(type="configuration/entityTypes/Organization")


class TestRelationModel(unittest.TestCase):
    """Test RelationModel"""
    
    def test_valid_relation(self):
        """Test valid relation"""
        model = RelationModel(
            type="configuration/relationTypes/OrganizationIndividual",
            startObject=RelationObjectModel(
                type="configuration/entityTypes/Organization",
                objectURI="entities/e1"
            ),
            endObject=RelationObjectModel(
                type="configuration/entityTypes/Individual",
                objectURI="entities/e2"
            )
        )
        self.assertEqual(model.type, "configuration/relationTypes/OrganizationIndividual")
        self.assertIsNotNone(model.startObject)
        self.assertIsNotNone(model.endObject)


class TestCreateRelationsRequest(unittest.TestCase):
    """Test CreateRelationsRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        relation = RelationModel(
            type="configuration/relationTypes/OrganizationIndividual",
            startObject=RelationObjectModel(
                type="configuration/entityTypes/Organization",
                objectURI="entities/e1"
            ),
            endObject=RelationObjectModel(
                type="configuration/entityTypes/Individual",
                objectURI="entities/e2"
            )
        )
        request = CreateRelationsRequest(relations=[relation])
        self.assertEqual(len(request.relations), 1)
    
    def test_empty_relations_list(self):
        """Test validation error with empty relations list"""
        with self.assertRaises(ValidationError):
            CreateRelationsRequest(relations=[])


class TestDeleteRelationRequest(unittest.TestCase):
    """Test DeleteRelationRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = DeleteRelationRequest(relation_id="rel123")
        self.assertEqual(request.relation_id, "rel123")
    
    def test_relation_id_extraction(self):
        """Test relation ID extraction"""
        with patch('src.util.models.extract_relation_id', return_value='rel123'):
            request = DeleteRelationRequest(relation_id="relations/rel123")
            self.assertEqual(request.relation_id, "rel123")


class TestGetEntityRelationsRequest(unittest.TestCase):
    """Test GetEntityRelationsRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = GetEntityRelationsRequest(
            entity_id="123abc",
            entity_types=["Individual", "Organization"]
        )
        self.assertEqual(request.entity_id, "123abc")
        self.assertEqual(len(request.entity_types), 2)
    
    def test_empty_entity_types(self):
        """Test validation error with empty entity_types"""
        with self.assertRaises(ValidationError):
            GetEntityRelationsRequest(entity_id="123abc", entity_types=[])
    
    def test_offset_max_validation(self):
        """Test offset + max validation"""
        with self.assertRaises(ValidationError):
            GetEntityRelationsRequest(
                entity_id="123abc",
                entity_types=["Individual"],
                offset=9995,
                max=10
            )
    
    def test_default_values(self):
        """Test default values"""
        request = GetEntityRelationsRequest(
            entity_id="123abc",
            entity_types=["Individual"]
        )
        self.assertEqual(request.offset, 0)
        self.assertEqual(request.max, 10)
        self.assertFalse(request.return_objects)
        self.assertFalse(request.return_dates)
        self.assertTrue(request.return_labels)


class TestRelationSearchRequest(unittest.TestCase):
    """Test RelationSearchRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = RelationSearchRequest(filter="equals(type, 'test')")
        self.assertEqual(request.filter, "equals(type, 'test')")
    
    def test_filter_validation_unbalanced_parentheses(self):
        """Test filter validation for unbalanced parentheses"""
        with self.assertRaises(ValidationError):
            RelationSearchRequest(filter="equals(type, 'test'")
    
    def test_order_validation(self):
        """Test order validation"""
        request = RelationSearchRequest(order="desc")
        self.assertEqual(request.order, "desc")
    
    def test_invalid_order(self):
        """Test invalid order value"""
        with self.assertRaises(ValidationError):
            RelationSearchRequest(order="invalid")
    
    def test_activeness_validation(self):
        """Test activeness validation"""
        request = RelationSearchRequest(activeness="all")
        self.assertEqual(request.activeness, "all")
    
    def test_invalid_activeness(self):
        """Test invalid activeness value"""
        with self.assertRaises(ValidationError):
            RelationSearchRequest(activeness="invalid")
    
    def test_offset_max_validation(self):
        """Test offset + max validation"""
        with self.assertRaises(ValidationError):
            RelationSearchRequest(offset=9995, max=10)


class TestCheckUserActivityRequest(unittest.TestCase):
    """Test CheckUserActivityRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = CheckUserActivityRequest(username="testuser", days_back=30)
        self.assertEqual(request.username, "testuser")
        self.assertEqual(request.days_back, 30)
    
    def test_default_days_back(self):
        """Test default days_back"""
        request = CheckUserActivityRequest(username="testuser")
        self.assertEqual(request.days_back, 7)
    
    def test_empty_username(self):
        """Test validation error with empty username"""
        with self.assertRaises(ValidationError):
            CheckUserActivityRequest(username="")
    
    def test_username_whitespace_stripping(self):
        """Test username whitespace stripping"""
        request = CheckUserActivityRequest(username="  testuser  ")
        self.assertEqual(request.username, "testuser")
    
    def test_days_back_out_of_range_low(self):
        """Test days_back cannot be less than 1"""
        with self.assertRaises(ValidationError):
            CheckUserActivityRequest(username="testuser", days_back=0)
    
    def test_days_back_out_of_range_high(self):
        """Test days_back cannot exceed 365"""
        with self.assertRaises(ValidationError):
            CheckUserActivityRequest(username="testuser", days_back=400)


class TestEntityInteractionsRequest(unittest.TestCase):
    """Test EntityInteractionsRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = EntityInteractionsRequest(entity_id="123abc")
        self.assertEqual(request.entity_id, "123abc")
    
    def test_default_max(self):
        """Test default max"""
        request = EntityInteractionsRequest(entity_id="123abc")
        self.assertEqual(request.max, 50)
    
    def test_default_offset(self):
        """Test default offset"""
        request = EntityInteractionsRequest(entity_id="123abc")
        self.assertEqual(request.offset, 0)
    
    def test_default_order(self):
        """Test default order"""
        request = EntityInteractionsRequest(entity_id="123abc")
        self.assertEqual(request.order, "asc")
    
    def test_order_validation(self):
        """Test order validation"""
        request = EntityInteractionsRequest(entity_id="123abc", order="desc")
        self.assertEqual(request.order, "desc")
    
    def test_invalid_order(self):
        """Test invalid order value"""
        with self.assertRaises(ValidationError):
            EntityInteractionsRequest(entity_id="123abc", order="invalid")
    
    def test_offset_max_validation(self):
        """Test offset + max validation"""
        with self.assertRaises(ValidationError):
            EntityInteractionsRequest(entity_id="123abc", offset=9995, max=10)


class TestCreateInteractionRequest(unittest.TestCase):
    """Test CreateInteractionRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        interactions = [{"type": "Email", "subject": "Test"}]
        request = CreateInteractionRequest(interactions=interactions)
        self.assertEqual(len(request.interactions), 1)
    
    def test_empty_interactions(self):
        """Test validation error with empty interactions"""
        with self.assertRaises(ValidationError):
            CreateInteractionRequest(interactions=[])
    
    def test_interaction_without_type(self):
        """Test validation error when interaction missing type"""
        with self.assertRaises(ValidationError):
            CreateInteractionRequest(interactions=[{"subject": "Test"}])
    
    def test_interaction_with_empty_type(self):
        """Test validation error when interaction type is empty"""
        with self.assertRaises(ValidationError):
            CreateInteractionRequest(interactions=[{"type": ""}])
    
    def test_default_source_system(self):
        """Test default source_system"""
        request = CreateInteractionRequest(
            interactions=[{"type": "Email"}]
        )
        self.assertEqual(request.source_system, "configuration/sources/Reltio")
    
    def test_default_return_objects(self):
        """Test default return_objects"""
        request = CreateInteractionRequest(
            interactions=[{"type": "Email"}]
        )
        self.assertTrue(request.return_objects)


class TestLookupListRequest(unittest.TestCase):
    """Test LookupListRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = LookupListRequest(
            lookup_type="rdm/lookupTypes/VistaVegetarianOrVegan"
        )
        self.assertEqual(request.lookup_type, "rdm/lookupTypes/VistaVegetarianOrVegan")
    
    def test_invalid_lookup_type_format(self):
        """Test validation error with invalid lookup type format"""
        with self.assertRaises(ValidationError):
            LookupListRequest(lookup_type="invalid/format")
    
    def test_empty_lookup_type(self):
        """Test validation error with empty lookup type"""
        with self.assertRaises(ValidationError):
            LookupListRequest(lookup_type="")
    
    def test_default_max_results(self):
        """Test default max_results"""
        request = LookupListRequest(
            lookup_type="rdm/lookupTypes/TestType"
        )
        self.assertEqual(request.max_results, 10)


class TestGetUsersByRoleRequest(unittest.TestCase):
    """Test GetUsersByRoleRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = GetUsersByRoleRequest(role="ROLE_USER")
        self.assertEqual(request.role, "ROLE_USER")
    
    def test_empty_role(self):
        """Test validation error with empty role"""
        with self.assertRaises(ValidationError):
            GetUsersByRoleRequest(role="")
    
    def test_role_whitespace_stripping(self):
        """Test role whitespace stripping"""
        request = GetUsersByRoleRequest(role="  ROLE_USER  ")
        self.assertEqual(request.role, "ROLE_USER")


class TestGetUsersByGroupRequest(unittest.TestCase):
    """Test GetUsersByGroupRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = GetUsersByGroupRequest(group="GROUP_LOCAL_RO_ALL")
        self.assertEqual(request.group, "GROUP_LOCAL_RO_ALL")
    
    def test_empty_group(self):
        """Test validation error with empty group"""
        with self.assertRaises(ValidationError):
            GetUsersByGroupRequest(group="")
    
    def test_group_whitespace_stripping(self):
        """Test group whitespace stripping"""
        request = GetUsersByGroupRequest(group="  GROUP_LOCAL_RO_ALL  ")
        self.assertEqual(request.group, "GROUP_LOCAL_RO_ALL")


class TestGetUserWorkflowTasksRequest(unittest.TestCase):
    """Test GetUserWorkflowTasksRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = GetUserWorkflowTasksRequest(assignee="testuser")
        self.assertEqual(request.assignee, "testuser")
    
    def test_empty_assignee(self):
        """Test validation error with empty assignee"""
        with self.assertRaises(ValidationError):
            GetUserWorkflowTasksRequest(assignee="")
    
    def test_default_values(self):
        """Test default values"""
        request = GetUserWorkflowTasksRequest(assignee="testuser")
        self.assertEqual(request.offset, 0)
        self.assertEqual(request.max_results, 10)
    
    def test_offset_max_validation(self):
        """Test offset + max_results validation"""
        with self.assertRaises(ValidationError):
            GetUserWorkflowTasksRequest(
                assignee="testuser",
                offset=9995,
                max_results=10
            )


class TestReassignWorkflowTaskRequest(unittest.TestCase):
    """Test ReassignWorkflowTaskRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = ReassignWorkflowTaskRequest(
            task_id="task123",
            assignee="newuser"
        )
        self.assertEqual(request.task_id, "task123")
        self.assertEqual(request.assignee, "newuser")
    
    def test_empty_task_id(self):
        """Test validation error with empty task_id"""
        with self.assertRaises(ValidationError):
            ReassignWorkflowTaskRequest(task_id="", assignee="user")
    
    def test_empty_assignee(self):
        """Test validation error with empty assignee"""
        with self.assertRaises(ValidationError):
            ReassignWorkflowTaskRequest(task_id="task123", assignee="")
    
    def test_whitespace_stripping(self):
        """Test whitespace stripping"""
        request = ReassignWorkflowTaskRequest(
            task_id="  task123  ",
            assignee="  user  "
        )
        self.assertEqual(request.task_id, "task123")
        self.assertEqual(request.assignee, "user")


class TestGetPossibleAssigneesRequest(unittest.TestCase):
    """Test GetPossibleAssigneesRequest"""
    
    def test_valid_request_with_tasks(self):
        """Test valid request with tasks"""
        request = GetPossibleAssigneesRequest(tasks=["task1", "task2"])
        self.assertEqual(len(request.tasks), 2)
    
    def test_valid_request_with_task_filter(self):
        """Test valid request with task_filter"""
        request = GetPossibleAssigneesRequest(
            task_filter={"processType": "review"}
        )
        self.assertIsNotNone(request.task_filter)
    
    def test_valid_request_with_exclude(self):
        """Test valid request with exclude"""
        request = GetPossibleAssigneesRequest(exclude=["task1"])
        self.assertEqual(len(request.exclude), 1)
    
    def test_invalid_tasks_with_task_filter(self):
        """Test validation error when using tasks with task_filter"""
        with self.assertRaises(ValidationError):
            GetPossibleAssigneesRequest(
                tasks=["task1"],
                task_filter={"processType": "review"}
            )
    
    def test_invalid_tasks_with_exclude(self):
        """Test validation error when using tasks with exclude"""
        with self.assertRaises(ValidationError):
            GetPossibleAssigneesRequest(
                tasks=["task1"],
                exclude=["task2"]
            )
    
    def test_invalid_no_parameters(self):
        """Test validation error when no parameters provided"""
        with self.assertRaises(ValidationError):
            GetPossibleAssigneesRequest()


class TestRetrieveTasksRequest(unittest.TestCase):
    """Test RetrieveTasksRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = RetrieveTasksRequest(assignee="testuser")
        self.assertEqual(request.assignee, "testuser")
    
    def test_default_values(self):
        """Test default values"""
        request = RetrieveTasksRequest()
        self.assertEqual(request.offset, 0)
        self.assertEqual(request.max_results, 10)
        self.assertEqual(request.order_by, "createTime")
        self.assertFalse(request.ascending)
        self.assertEqual(request.state, "valid")
    
    def test_invalid_priority_class(self):
        """Test validation error with invalid priority_class"""
        with self.assertRaises(ValidationError):
            RetrieveTasksRequest(priority_class="Invalid")
    
    def test_valid_priority_class(self):
        """Test valid priority_class values"""
        for priority in ["Urgent", "High", "Medium", "Low"]:
            request = RetrieveTasksRequest(priority_class=priority)
            self.assertEqual(request.priority_class, priority)
    
    def test_invalid_order_by(self):
        """Test validation error with invalid order_by"""
        with self.assertRaises(ValidationError):
            RetrieveTasksRequest(order_by="invalid")
    
    def test_valid_order_by(self):
        """Test valid order_by values"""
        for order_by in ["createTime", "assignee", "dueDate", "priority"]:
            request = RetrieveTasksRequest(order_by=order_by)
            self.assertEqual(request.order_by, order_by)
    
    def test_invalid_state(self):
        """Test validation error with invalid state"""
        with self.assertRaises(ValidationError):
            RetrieveTasksRequest(state="not_a_valid_state")
    
    def test_valid_state_values(self):
        """Test valid state values (valid, invalid, all)"""
        for state in ["valid", "invalid", "all"]:
            request = RetrieveTasksRequest(state=state)
            self.assertEqual(request.state, state)
    
    def test_timestamp_validation(self):
        """Test timestamp validation"""
        with self.assertRaises(ValidationError):
            RetrieveTasksRequest(created_after=-1)
    
    def test_timestamp_range_validation(self):
        """Test created_before must be greater than created_after"""
        with self.assertRaises(ValidationError):
            RetrieveTasksRequest(created_after=2000000, created_before=1000000)
    
    def test_offset_max_validation(self):
        """Test offset + max_results validation"""
        with self.assertRaises(ValidationError):
            RetrieveTasksRequest(offset=9995, max_results=10)


class TestGetTaskDetailsRequest(unittest.TestCase):
    """Test GetTaskDetailsRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = GetTaskDetailsRequest(task_id="task123")
        self.assertEqual(request.task_id, "task123")
    
    def test_empty_task_id(self):
        """Test validation error with empty task_id"""
        with self.assertRaises(ValidationError):
            GetTaskDetailsRequest(task_id="")
    
    def test_invalid_task_id_characters(self):
        """Test validation error with invalid characters"""
        with self.assertRaises(ValidationError):
            GetTaskDetailsRequest(task_id="task@123!")
    
    def test_valid_task_id_formats(self):
        """Test valid task_id formats"""
        valid_ids = ["task123", "task-123", "task_123", "TASK123"]
        for task_id in valid_ids:
            request = GetTaskDetailsRequest(task_id=task_id)
            self.assertEqual(request.task_id, task_id)
    
    def test_default_show_variables(self):
        """Test default show_task_variables and show_task_local_variables"""
        request = GetTaskDetailsRequest(task_id="task123")
        self.assertFalse(request.show_task_variables)
        self.assertFalse(request.show_task_local_variables)


class TestStartProcessInstanceRequest(unittest.TestCase):
    """Test StartProcessInstanceRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = StartProcessInstanceRequest(
            process_type="review",
            object_uris=["entities/e1"]
        )
        self.assertEqual(request.process_type, "review")
        self.assertEqual(len(request.object_uris), 1)
    
    def test_empty_process_type(self):
        """Test validation error with empty process_type"""
        with self.assertRaises(ValidationError):
            StartProcessInstanceRequest(
                process_type="",
                object_uris=["entities/e1"]
            )
    
    def test_empty_object_uris(self):
        """Test validation error with empty object_uris"""
        with self.assertRaises(ValidationError):
            StartProcessInstanceRequest(
                process_type="review",
                object_uris=[]
            )
    
    def test_process_type_whitespace_stripping(self):
        """Test process_type whitespace stripping"""
        request = StartProcessInstanceRequest(
            process_type="  review  ",
            object_uris=["entities/e1"]
        )
        self.assertEqual(request.process_type, "review")


class TestExecuteTaskActionRequest(unittest.TestCase):
    """Test ExecuteTaskActionRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = ExecuteTaskActionRequest(
            task_id="task123",
            action="Approve"
        )
        self.assertEqual(request.task_id, "task123")
        self.assertEqual(request.action, "Approve")
    
    def test_empty_action(self):
        """Test validation error with empty action"""
        with self.assertRaises(ValidationError):
            ExecuteTaskActionRequest(task_id="task123", action="")
    
    def test_action_whitespace_stripping(self):
        """Test action whitespace stripping"""
        request = ExecuteTaskActionRequest(
            task_id="task123",
            action="  Approve  "
        )
        self.assertEqual(request.action, "Approve")


class TestEntityWithMatchesRequest(unittest.TestCase):
    """Test EntityWithMatchesRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = EntityWithMatchesRequest(entity_id="123abc")
        self.assertEqual(request.entity_id, "123abc")
    
    def test_default_values(self):
        """Test default values"""
        request = EntityWithMatchesRequest(entity_id="123abc")
        self.assertEqual(request.attributes, [])
        self.assertTrue(request.include_match_attributes)
        self.assertEqual(request.match_attributes, [])
        self.assertEqual(request.match_limit, 5)
    
    def test_match_limit_out_of_range_low(self):
        """Test match_limit cannot be less than 1"""
        with self.assertRaises(ValidationError):
            EntityWithMatchesRequest(entity_id="123abc", match_limit=0)
    
    def test_match_limit_out_of_range_high(self):
        """Test match_limit cannot exceed 5"""
        with self.assertRaises(ValidationError):
            EntityWithMatchesRequest(entity_id="123abc", match_limit=10)


class TestCreateEntitiesRequest(unittest.TestCase):
    """Test CreateEntitiesRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        entities = [{"type": "configuration/entityTypes/Individual"}]
        request = CreateEntitiesRequest(entities=entities)
        self.assertEqual(len(request.entities), 1)
    
    def test_empty_entities(self):
        """Test validation error with empty entities"""
        with self.assertRaises(ValidationError):
            CreateEntitiesRequest(entities=[])
    
    def test_entity_without_type(self):
        """Test validation error when entity missing type"""
        with self.assertRaises(ValidationError):
            CreateEntitiesRequest(entities=[{"name": "Test"}])
    
    def test_entity_with_empty_type(self):
        """Test validation error when entity type is empty"""
        with self.assertRaises(ValidationError):
            CreateEntitiesRequest(entities=[{"type": ""}])
    
    def test_default_values(self):
        """Test default values"""
        request = CreateEntitiesRequest(
            entities=[{"type": "configuration/entityTypes/Individual"}]
        )
        self.assertFalse(request.return_objects)
        self.assertTrue(request.execute_lca)


class TestGetEntityParentsRequest(unittest.TestCase):
    """Test GetEntityParentsRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = GetEntityParentsRequest(
            entity_id="123abc",
            graph_type_uris="configuration/graphTypes/HCO"
        )
        self.assertEqual(request.entity_id, "123abc")
        self.assertEqual(request.graph_type_uris, "configuration/graphTypes/HCO")
    
    def test_empty_graph_type_uris(self):
        """Test validation error with empty graph_type_uris"""
        with self.assertRaises(ValidationError):
            GetEntityParentsRequest(entity_id="123abc", graph_type_uris="")
    
    def test_graph_type_uris_whitespace_stripping(self):
        """Test graph_type_uris whitespace stripping"""
        request = GetEntityParentsRequest(
            entity_id="123abc",
            graph_type_uris="  configuration/graphTypes/HCO  "
        )
        self.assertEqual(request.graph_type_uris, "configuration/graphTypes/HCO")


class TestUnifiedMatchRequest(unittest.TestCase):
    """Test UnifiedMatchRequest"""
    
    def test_valid_match_rule_request(self):
        """Test valid match_rule request"""
        request = UnifiedMatchRequest(
            search_type="match_rule",
            filter="rule123"
        )
        self.assertEqual(request.search_type, "match_rule")
        self.assertEqual(request.filter, "rule123")
    
    def test_valid_score_request(self):
        """Test valid score request"""
        request = UnifiedMatchRequest(
            search_type="score",
            filter="50,100"
        )
        self.assertEqual(request.search_type, "score")
        self.assertEqual(request.filter, "50,100")
    
    def test_valid_confidence_request(self):
        """Test valid confidence request"""
        request = UnifiedMatchRequest(
            search_type="confidence",
            filter="High confidence"
        )
        self.assertEqual(request.search_type, "confidence")
        self.assertEqual(request.filter, "High confidence")
    
    def test_invalid_search_type(self):
        """Test validation error with invalid search_type"""
        with self.assertRaises(ValidationError):
            UnifiedMatchRequest(search_type="invalid", filter="test")
    
    def test_invalid_score_filter_format(self):
        """Test validation error with invalid score filter format"""
        with self.assertRaises(ValidationError):
            UnifiedMatchRequest(search_type="score", filter="invalid")
    
    def test_invalid_score_filter_range(self):
        """Test validation error with invalid score range"""
        with self.assertRaises(ValidationError):
            UnifiedMatchRequest(search_type="score", filter="150,200")
    
    def test_invalid_score_filter_order(self):
        """Test validation error when start > end"""
        with self.assertRaises(ValidationError):
            UnifiedMatchRequest(search_type="score", filter="80,50")
    
    def test_empty_match_rule_filter(self):
        """Test validation error with empty match_rule filter"""
        with self.assertRaises(ValidationError):
            UnifiedMatchRequest(search_type="match_rule", filter="")
    
    def test_default_entity_type(self):
        """Test default entity_type"""
        request = UnifiedMatchRequest(
            search_type="match_rule",
            filter="rule123"
        )
        self.assertEqual(request.entity_type, "Individual")
    
    def test_offset_max_validation(self):
        """Test offset + max_results validation"""
        with self.assertRaises(ValidationError):
            UnifiedMatchRequest(
                search_type="match_rule",
                filter="rule123",
                offset=9995,
                max_results=10
            )


class TestGetPotentialMatchApisRequest(unittest.TestCase):
    """Test GetPotentialMatchApisRequest"""
    
    def test_valid_request(self):
        """Test valid request"""
        request = GetPotentialMatchApisRequest(min_matches=5)
        self.assertEqual(request.min_matches, 5)
    
    def test_default_min_matches(self):
        """Test default min_matches"""
        request = GetPotentialMatchApisRequest()
        self.assertEqual(request.min_matches, 0)
    
    def test_negative_min_matches(self):
        """Test negative min_matches validation"""
        with self.assertRaises(ValidationError):
            GetPotentialMatchApisRequest(min_matches=-1)


if __name__ == '__main__':
    unittest.main()


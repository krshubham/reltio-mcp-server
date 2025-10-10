"""
Tests for error handling in the server.py file.
"""
import pytest
from unittest.mock import patch

# Import the server module
import src.server


@pytest.mark.asyncio
class TestServerErrorHandling:
    """Tests for error handling in the server.py file."""
    
    @patch('src.tools.search.search_entities')
    async def test_search_entities_error_handling(self, mock_search_entities):
        """Test that search_entities properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_search_entities.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.search_entities_tool(filter="filter", entity_type="entity_type", tenant_id="tenant_id", max_results=10)
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result
    
    @patch('src.tools.entity.get_entity_details')
    async def test_get_entity_error_handling(self, mock_get_entity_details):
        """Test that get_entity properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_get_entity_details.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.get_entity_tool(entity_id="entity_id", tenant_id="tenant_id")
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result
    
    @patch('src.tools.entity.update_entity_attributes')
    async def test_update_entity_attributes_error_handling(self, mock_update_entity_attributes):
        """Test that update_entity_attributes properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_update_entity_attributes.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.update_entity_attributes_tool(entity_id="entity_id", updates={'attributes': {'FirstName': 'John'}}, tenant_id="tenant_id")
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result
    
    @patch('src.tools.entity.get_entity_match_history')
    async def test_get_entity_match_history_error_handling(self, mock_get_entity_match_history):
        """Test that get_match_history properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_get_entity_match_history.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.get_entity_match_history_tool(entity_id="entity_id", tenant_id="tenant_id")
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result
    
    @patch('src.tools.relation.get_relation_details')
    async def test_get_relation_error_handling(self, mock_get_relation_details):
        """Test that get_relation_details properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_get_relation_details.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.get_relation_details_tool(relation_id="relation_id", tenant_id="tenant_id")
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result
    
    @patch('src.tools.entity.merge_entities')
    async def test_merge_entities_error_handling(self, mock_merge_entities):
        """Test that merge_entities_tool properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_merge_entities.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.merge_entities_tool(
            entity_ids=["entity1", "entity2"],
            tenant_id="tenant_id"
        )
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result
    
    @patch('src.tools.entity.reject_entity_match')
    async def test_reject_entity_match_error_handling(self, mock_reject_entity_match):
        """Test that reject_entity_match_tool properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_reject_entity_match.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.reject_entity_match_tool(
            source_id="entity1",
            target_id="entity2",
            tenant_id="tenant_id"
        )
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result
    
    @patch('src.tools.entity.export_merge_tree')
    async def test_export_merge_tree_error_handling(self, mock_export_merge_tree):
        """Test that export_merge_tree properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_export_merge_tree.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.export_merge_tree_tool(email_id="email_id", tenant_id="tenant_id")
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result

    @patch('src.tools.tenant_config.get_business_configuration')
    async def test_get_business_configuration_error_handling(self, mock_get_business_configuration):
        """Test that get_business_configuration properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_get_business_configuration.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.get_business_configuration_tool(tenant_id="tenant_id")
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result

    @patch('src.tools.tenant_config.get_tenant_permissions_metadata')
    async def test_get_tenant_permissions_metadata_error_handling(self, mock_get_tenant_permissions_metadata):
        """Test that get_tenant_permissions_metadata properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_get_tenant_permissions_metadata.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.get_tenant_permissions_metadata_tool(tenant_id="tenant_id")
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result

    @patch('src.server.list_capabilities')
    async def test_capabilities_error_handling(self, mock_list_capabilities):
        """Test that capabilities properly handles errors from the tool."""
        # Setup mock to raise an exception
        mock_list_capabilities.side_effect = Exception("Test error")
        
        # Call the function
        result = await src.server.capabilities_tool()
        
        # Verify the function handled the error and returned a result
        assert isinstance(result, dict)
        assert "error" in result
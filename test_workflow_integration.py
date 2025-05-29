#!/usr/bin/env python3
"""
Integration test to verify that the workflow fixes are working correctly.
This script tests:
1. Both workflows can be imported without crashes
2. Channel normalizer works correctly
3. No circular dependencies or Streamlit import issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_workflow_imports():
    """Test that both workflows can be imported without errors."""
    print("Testing workflow imports...")
    
    try:
        from src.ui.data_collection.refresh_channel_workflow import RefreshChannelWorkflow
        print("✅ RefreshChannelWorkflow imported successfully")
    except Exception as e:
        print(f"❌ Failed to import RefreshChannelWorkflow: {e}")
        return False
    
    try:
        from src.ui.data_collection.new_channel_workflow import NewChannelWorkflow
        print("✅ NewChannelWorkflow imported successfully")
    except Exception as e:
        print(f"❌ Failed to import NewChannelWorkflow: {e}")
        return False
    
    return True

def test_channel_normalizer():
    """Test that the channel normalizer works correctly."""
    print("\nTesting channel normalizer...")
    
    try:
        from src.utils.data_collection.channel_normalizer import normalize_channel_data_for_save
        print("✅ Channel normalizer imported successfully")
        
        # Test data normalization
        test_data = {
            'channel_id': 'UCtest123',
            'channel_name': 'Test Channel',
            'subscribers': '1500',  # String input
            'views': '75000',      # String input
            'total_videos': 42,    # Integer input
            'is_linked': 'true',   # String boolean
            'made_for_kids': False, # Boolean
            'custom_url': '@testchannel'
        }
        
        result = normalize_channel_data_for_save(test_data, "test_workflow")
        
        # Verify type conversions
        assert isinstance(result['subscribers'], int), "Subscribers should be integer"
        assert isinstance(result['views'], int), "Views should be integer"
        assert isinstance(result['total_videos'], int), "Total videos should be integer"
        assert isinstance(result['is_linked'], bool), "is_linked should be boolean"
        assert isinstance(result['made_for_kids'], bool), "made_for_kids should be boolean"
        
        # Verify values
        assert result['subscribers'] == 1500, "Subscribers conversion incorrect"
        assert result['views'] == 75000, "Views conversion incorrect"
        assert result['total_videos'] == 42, "Total videos incorrect"
        assert result['is_linked'] == True, "is_linked conversion incorrect"
        assert result['made_for_kids'] == False, "made_for_kids incorrect"
        
        # Verify required fields exist
        required_fields = ['channel_id', 'channel_name', 'fetched_at', 'updated_at']
        for field in required_fields:
            assert field in result, f"Required field {field} missing"
        
        print("✅ Channel normalizer working correctly")
        print(f"   Input subscribers: {test_data['subscribers']} ({type(test_data['subscribers'])})")
        print(f"   Output subscribers: {result['subscribers']} ({type(result['subscribers'])})")
        return True
        
    except Exception as e:
        print(f"❌ Channel normalizer test failed: {e}")
        return False

def test_no_duplicate_imports():
    """Test that there are no problematic duplicate imports."""
    print("\nTesting for clean import structure...")
    
    # Check that old duplicate normalizer was removed
    old_normalizer_path = "src/ui/data_collection/utils/data_normalizer.py"
    if os.path.exists(old_normalizer_path):
        print(f"❌ Duplicate normalizer still exists at {old_normalizer_path}")
        return False
    else:
        print("✅ Old duplicate normalizer successfully removed")
    
    # Check that test files were cleaned up
    test_files = ["test_workflow_fixes.py", "verify_fixes.py"]
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"❌ Cruft file still exists: {test_file}")
            return False
        else:
            print(f"✅ Cruft file cleaned up: {test_file}")
    
    return True

def main():
    """Run all integration tests."""
    print("=" * 60)
    print("YTDataHub Workflow Integration Test")
    print("=" * 60)
    
    tests = [
        test_workflow_imports,
        test_channel_normalizer,
        test_no_duplicate_imports
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All integration tests PASSED!")
        print("✅ Refresh workflow logic should now be working correctly")
        print("✅ No more Python crashes when importing workflows")
        print("✅ Data normalization ensures consistent format between workflows")
    else:
        print("❌ Some integration tests FAILED!")
        print("   Please check the errors above and fix any remaining issues.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

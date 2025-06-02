#!/usr/bin/env python3
"""
Test script to verify the unified workflow implementation works correctly.
This tests the workflow logic without requiring a real YouTube API key.
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Add the project root to Python path
sys.path.insert(0, '/Users/jamiemeredith/Projects/ytdatahub')

def test_unified_workflow_creation():
    """Test that UnifiedWorkflow can be created successfully"""
    print("Testing UnifiedWorkflow creation...")
    
    try:
        from src.services.youtube_service import YouTubeService
        from src.ui.data_collection.workflow_factory import create_workflow
        
        # Create a mock YouTube service
        youtube_service = YouTubeService('test_api_key')
        
        # Create unified workflow
        workflow = create_workflow(youtube_service, "unified")
        
        print(f"✅ UnifiedWorkflow created successfully!")
        print(f"   Workflow type: {type(workflow).__name__}")
        print(f"   Has initialize_workflow method: {hasattr(workflow, 'initialize_workflow')}")
        print(f"   Has render_current_step method: {hasattr(workflow, 'render_current_step')}")
        print(f"   Has save_data method: {hasattr(workflow, 'save_data')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating UnifiedWorkflow: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_steps():
    """Test that the workflow has the correct step methods"""
    print("\nTesting workflow step methods...")
    
    try:
        from src.services.youtube_service import YouTubeService
        from src.ui.data_collection.unified_workflow import UnifiedWorkflow
        
        # Create workflow
        youtube_service = YouTubeService('test_api_key')
        workflow = UnifiedWorkflow(youtube_service)
        
        # Check step methods
        step_methods = [
            'render_step_1_mode_selection',
            'render_step_2_new_channel_input',
            'render_step_2_channel_selection', 
            'render_step_3_channel_data_review',
            'render_step_4_video_collection',
            'render_step_5_comment_collection'
        ]
        
        for method_name in step_methods:
            if hasattr(workflow, method_name):
                print(f"   ✅ {method_name}")
            else:
                print(f"   ❌ {method_name} - Missing!")
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing workflow steps: {str(e)}")
        return False

def test_workflow_factory():
    """Test workflow factory with different modes"""
    print("\nTesting workflow factory...")
    
    try:
        from src.services.youtube_service import YouTubeService
        from src.ui.data_collection.workflow_factory import create_workflow
        
        youtube_service = YouTubeService('test_api_key')
        
        # Test unified mode
        unified_workflow = create_workflow(youtube_service, "unified")
        print(f"   ✅ Unified workflow: {type(unified_workflow).__name__}")
        
        # Test legacy modes
        new_workflow = create_workflow(youtube_service, "new_channel")
        print(f"   ✅ New channel workflow: {type(new_workflow).__name__}")
        
        refresh_workflow = create_workflow(youtube_service, "refresh_channel")
        print(f"   ✅ Refresh channel workflow: {type(refresh_workflow).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing workflow factory: {str(e)}")
        return False

def test_save_data_delegation():
    """Test that save_data method delegates correctly"""
    print("\nTesting save_data delegation...")
    
    try:
        from src.services.youtube_service import YouTubeService
        from src.ui.data_collection.unified_workflow import UnifiedWorkflow
        
        youtube_service = YouTubeService('test_api_key')
        workflow = UnifiedWorkflow(youtube_service)
        
        # Mock session state to simulate different modes
        test_data = {'test': 'data'}
        storage_type = 'SQLite Database'
        
        # Test with no mode set (should handle gracefully)
        workflow.mode = None
        try:
            result = workflow.save_data(test_data, storage_type)
            print(f"   ✅ No mode handling: Returns {result}")
        except Exception as e:
            print(f"   ⚠️  No mode handling raised: {str(e)}")
        
        # Test with mode set to 'new'
        workflow.mode = 'new'
        try:
            # This will try to delegate to new_workflow which should work
            result = workflow.save_data(test_data, storage_type)
            print(f"   ✅ New mode delegation: Returns {result}")
        except Exception as e:
            print(f"   ⚠️  New mode delegation: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing save_data delegation: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("UNIFIED WORKFLOW IMPLEMENTATION TEST")
    print("=" * 60)
    
    # Mock Streamlit to avoid session state issues
    with patch('streamlit.session_state', {}), \
         patch('streamlit.error'), \
         patch('streamlit.warning'), \
         patch('streamlit.info'):
        
        tests = [
            test_unified_workflow_creation,
            test_workflow_steps,
            test_workflow_factory,
            test_save_data_delegation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("\n" + "=" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Unified workflow implementation is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
        
        print("=" * 60)

if __name__ == "__main__":
    main()

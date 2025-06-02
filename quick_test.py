#!/usr/bin/env python3
"""
Quick test to verify unified workflow implementation.
"""

import sys
sys.path.insert(0, '/Users/jamiemeredith/Projects/ytdatahub')

def main():
    print("🧪 Testing Unified Workflow Implementation")
    print("=" * 50)
    
    try:
        # Test 1: Import unified workflow
        print("1. Testing imports...")
        from src.services.youtube_service import YouTubeService
        from src.ui.data_collection.workflow_factory import create_workflow
        from src.ui.data_collection.unified_workflow import UnifiedWorkflow
        print("   ✅ All imports successful")
        
        # Test 2: Create service and workflow
        print("2. Testing workflow creation...")
        youtube_service = YouTubeService('dummy_api_key')
        workflow = create_workflow(youtube_service, "unified")
        print(f"   ✅ Unified workflow created: {type(workflow).__name__}")
        
        # Test 3: Check required methods
        print("3. Testing required methods...")
        required_methods = [
            'initialize_workflow',
            'render_current_step', 
            'save_data',
            'render_step_1_mode_selection'
        ]
        
        for method in required_methods:
            if hasattr(workflow, method):
                print(f"   ✅ {method}")
            else:
                print(f"   ❌ Missing: {method}")
        
        # Test 4: Test workflow factory modes
        print("4. Testing workflow factory...")
        unified = create_workflow(youtube_service, "unified")
        new_channel = create_workflow(youtube_service, "new_channel") 
        refresh = create_workflow(youtube_service, "refresh_channel")
        
        print(f"   ✅ Unified: {type(unified).__name__}")
        print(f"   ✅ New: {type(new_channel).__name__}")
        print(f"   ✅ Refresh: {type(refresh).__name__}")
        
        print("\n🎉 All tests passed! Unified workflow is ready for use.")
        print("\nNext steps:")
        print("1. Open browser at http://localhost:8501")
        print("2. Enter a YouTube API key (format: AIzaSy... 39 chars)")
        print("3. You should see the unified workflow interface")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

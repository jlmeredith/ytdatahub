"""
Test data configuration module.

This module defines test data paths and loader utilities for test fixtures.
"""

import os
import json
import yaml
import pytest


# Test data paths
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "data")
API_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "api_responses")
SAMPLE_CHANNELS_PATH = os.path.join(TEST_DATA_DIR, "sample_channels.json")
SAMPLE_VIDEOS_PATH = os.path.join(TEST_DATA_DIR, "sample_videos.json")
SAMPLE_COMMENTS_PATH = os.path.join(TEST_DATA_DIR, "sample_comments.json")


def load_test_data(filename):
    """Load test data from a JSON or YAML file in the test data directory.
    
    Args:
        filename (str): Name of the file to load (with extension)
        
    Returns:
        dict: Loaded test data
    """
    filepath = os.path.join(TEST_DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        pytest.skip(f"Test data file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        if filename.endswith('.json'):
            return json.load(f)
        elif filename.endswith(('.yaml', '.yml')):
            return yaml.safe_load(f)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()


def load_api_fixture(fixture_name):
    """Load an API fixture from the fixtures directory.
    
    Args:
        fixture_name (str): Name of the fixture file (with extension)
        
    Returns:
        dict: Loaded API fixture data
    """
    filepath = os.path.join(API_FIXTURES_DIR, fixture_name)
    
    if not os.path.exists(filepath):
        pytest.skip(f"API fixture file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

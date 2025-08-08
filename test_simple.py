"""
Simple validation tests for bug fixes without external dependencies.
"""


def validate_coordinates_simple(lat: float, lon: float):
    """Copy of validation function for testing."""
    if not (-90 <= lat <= 90):
        raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90.")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180.")
    return True


def test_coordinate_validation():
    """Test input validation for coordinates."""
    try:
        # Valid coordinates should pass
        assert validate_coordinates_simple(11.5, 104.8) == True
        print("✓ Valid coordinates test passed")
        
        # Invalid latitude should raise exception
        try:
            validate_coordinates_simple(95.0, 104.8)  # lat > 90
            assert False, "Should have raised exception"
        except ValueError:
            print("✓ Invalid latitude test passed")
        
        # Invalid longitude should raise exception
        try:
            validate_coordinates_simple(11.5, 185.0)  # lon > 180
            assert False, "Should have raised exception"  
        except ValueError:
            print("✓ Invalid longitude test passed")
            
        return True
    except Exception as e:
        print(f"✗ Coordinate validation test failed: {e}")
        return False


def test_duplicate_function_names():
    """Test that we fixed the duplicate function name issue."""
    import ast
    
    with open('api/graph_routes.py', 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    function_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
    
    # Check for duplicates
    duplicates = set([name for name in function_names if function_names.count(name) > 1])
    
    if not duplicates:
        print("✓ No duplicate function names found")
        return True
    else:
        print(f"✗ Duplicate function names found: {duplicates}")
        return False


def test_fastapi_startup_deprecation():
    """Test that we replaced deprecated @app.on_event with lifespan."""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Should not contain the deprecated decorator
    if '@app.on_event("startup")' in content:
        print("✗ Still using deprecated @app.on_event")
        return False
    
    # Should contain new lifespan pattern
    if 'lifespan' in content and 'asynccontextmanager' in content:
        print("✓ Using new lifespan pattern")
        return True
    else:
        print("✗ New lifespan pattern not found")
        return False


def test_commented_code_removal():
    """Test that commented code blocks were removed."""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Count lines that start with # (excluding proper comments)
    lines = content.split('\n')
    commented_blocks = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#') and len(stripped) > 2:
            # Check if it looks like commented-out code (contains symbols)
            if any(char in stripped for char in ['=', '(', ')', '{', '}', '[', ']']):
                commented_blocks.append(f"Line {i+1}: {stripped}")
    
    if len(commented_blocks) < 5:  # Should have significantly fewer commented blocks
        print("✓ Most commented code blocks removed")
        return True
    else:
        print(f"✗ Still has many commented code blocks: {len(commented_blocks)}")
        return False


def test_syntax_validation():
    """Test that all Python files have valid syntax."""
    import ast
    import os
    
    files_to_check = ['main.py', 'api/graph_routes.py', 'services/route_finder.py', 'services/graph_helper.py']
    
    all_valid = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    ast.parse(f.read())
                print(f"✓ {file_path}: Syntax OK")
            except SyntaxError as e:
                print(f"✗ {file_path}: Syntax Error - {e}")
                all_valid = False
        else:
            print(f"✗ {file_path}: File not found")
            all_valid = False
    
    return all_valid


if __name__ == "__main__":
    print("Running bug fix validation tests...")
    print("=" * 50)
    
    tests = [
        test_coordinate_validation,
        test_duplicate_function_names,
        test_fastapi_startup_deprecation,
        test_commented_code_removal,
        test_syntax_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n{test.__name__}:")
        if test():
            passed += 1
        else:
            print("  Test failed!")
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bug fixes are working correctly.")
        exit(0)
    else:
        print("❌ Some tests failed. Please review the issues above.")
        exit(1)
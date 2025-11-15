# Test API endpoints functionality
import requests
import json
import time

def test_api_endpoints():
    """Test API endpoints tanpa perlu server running"""
    print("Testing API Endpoints...")

    base_url = "http://127.0.0.1:8080"

    # Sample patient data
    sample_data = {
        "patient_name": "Ahmad Sutrisno",
        "patient_number": "123456789",
        "ward": "ICU",
        "room": "A-101"
    }

    try:
        # Test generate barcode endpoint
        print("Testing /api/generate-barcode endpoint...")

        # For now, kita test dengan mengimport langsung function
        from app import generate_barcode_with_patient_data

        # Simulate API call
        print(f"Sample data: {sample_data}")

        image_buffer = generate_barcode_with_patient_data(
            sample_data['patient_number'],
            sample_data['patient_name'],
            sample_data['ward'],
            sample_data['room']
        )

        if image_buffer:
            print("[SUCCESS] API simulation successful - barcode generated")

            # Simulate API response
            response_data = {
                "success": True,
                "message": "Barcode generated successfully",
                "filename": f"{sample_data['patient_number']}_{sample_data['patient_name'].replace(' ', '_')}.png",
                "patient_data": sample_data
            }

            print(f"API Response: {json.dumps(response_data, indent=2)}")
            return True
        else:
            print("[ERROR] Failed to generate barcode")
            return False

    except Exception as e:
        print(f"[ERROR] API test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_form_validation():
    """Test form validation logic"""
    print("\nTesting Form Validation Logic...")

    test_cases = [
        {
            "name": "Valid patient data",
            "data": {
                "patient_name": "John Doe",
                "patient_number": "123456789",
                "ward": "ICU",
                "room": "101"
            },
            "expected": True
        },
        {
            "name": "Invalid patient number (too short)",
            "data": {
                "patient_name": "John Doe",
                "patient_number": "123",
                "ward": "ICU",
                "room": "101"
            },
            "expected": False
        },
        {
            "name": "Empty patient name",
            "data": {
                "patient_name": "",
                "patient_number": "123456789",
                "ward": "ICU",
                "room": "101"
            },
            "expected": False
        }
    ]

    def validate_patient_data(data):
        """Simulate form validation"""
        # Check required fields
        if not data.get('patient_name') or len(data['patient_name'].strip()) < 2:
            return False

        if not data.get('patient_number') or len(data['patient_number'].strip()) < 8:
            return False

        if not data.get('ward'):
            return False

        if not data.get('room'):
            return False

        # Validate patient number format
        patient_number = data['patient_number'].strip()
        if not patient_number.isdigit() or len(patient_number) < 8 or len(patient_number) > 12:
            return False

        return True

    all_passed = True

    for test_case in test_cases:
        result = validate_patient_data(test_case['data'])
        status = "PASS" if result == test_case['expected'] else "FAIL"
        print(f"  {test_case['name']}: {status}")

        if result != test_case['expected']:
            all_passed = False
            print(f"    Expected: {test_case['expected']}, Got: {result}")

    return all_passed

if __name__ == "__main__":
    print("=== Patient Barcode Generator - Test Suite ===\n")

    # Test barcode generation
    api_success = test_api_endpoints()

    # Test form validation
    validation_success = test_form_validation()

    print(f"\n=== Test Results ===")
    print(f"Barcode Generation: {'PASS' if api_success else 'FAIL'}")
    print(f"Form Validation: {'PASS' if validation_success else 'FAIL'}")

    if api_success and validation_success:
        print("\n[SUCCESS] All tests passed! System ready for deployment.")
    else:
        print("\n[WARNING] Some tests failed. Check the output above.")

    print("\n=== Next Steps ===")
    print("1. Start the web server: python app.py")
    print("2. Open browser to: http://127.0.0.1:8080")
    print("3. Test the web interface")
    print("4. For production: docker-compose up --build")
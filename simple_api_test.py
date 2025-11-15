#!/usr/bin/env python3
"""
Simple API test for Patient Barcode Generator
"""

import requests
import json
import time

API_BASE = "http://127.0.0.1:8090"

def test_single_request():
    """Test a single barcode generation request"""
    print("Testing single barcode generation...")

    test_data = {
        "patient_name": "Test Patient",
        "patient_number": "12345678",
        "ward": "ICU",
        "room": "101"
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/api/generate-barcode",
            json=test_data,
            timeout=10
        )
        end_time = time.time()

        print(f"Response time: {end_time - start_time:.2f}s")
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Single barcode generation")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_batch_processing():
    """Test batch processing"""
    print("\nTesting batch processing...")

    patients = [
        {"patient_name": "John Doe", "patient_number": "11111111", "ward": "ICU", "room": "101"},
        {"patient_name": "Jane Smith", "patient_number": "22222222", "ward": "Bedah", "room": "A-202"},
        {"patient_name": "Ahmad Rahman", "patient_number": "33333333", "ward": "Anak", "room": "B-101"}
    ]

    start_time = time.time()
    success_count = 0

    for i, patient in enumerate(patients):
        print(f"Processing patient {i+1}: {patient['patient_name']}")

        try:
            response = requests.post(
                f"{API_BASE}/api/generate-barcode",
                json=patient,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    success_count += 1
                    print("  SUCCESS")
                else:
                    print(f"  FAILED: {result.get('error')}")
            else:
                print(f"  HTTP ERROR: {response.status_code}")

        except Exception as e:
            print(f"  EXCEPTION: {e}")

    end_time = time.time()
    print(f"\nTotal time: {end_time - start_time:.2f}s")
    print(f"Success rate: {success_count}/{len(patients)} ({success_count/len(patients)*100:.1f}%)")

    return success_count == len(patients)

def test_download_functionality():
    """Test download functionality"""
    print("\nTesting download functionality...")

    test_data = {
        "patient_name": "Download Test",
        "patient_number": "99999999",
        "ward": "Test",
        "room": "Test"
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/download-barcode",
            json=test_data,
            timeout=15
        )

        if response.status_code == 200:
            print(f"SUCCESS: Download working")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Length: {len(response.content)} bytes")
            return True
        else:
            print(f"FAILED: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("Patient Barcode Generator - API Test")
    print("=" * 50)

    # Run tests
    tests = [
        ("Single Request", test_single_request),
        ("Batch Processing", test_batch_processing),
        ("Download Functionality", test_download_functionality)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:<25} {status}")

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"\nOverall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("All tests passed!")
    else:
        print("Some tests failed - issues identified.")

    return results

if __name__ == "__main__":
    main()
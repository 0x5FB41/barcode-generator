#!/usr/bin/env python3
"""
Comprehensive test for Patient Barcode Generator API endpoints
Tests for the issues identified in the troubleshooting analysis
"""

import requests
import json
import time
import concurrent.futures
from threading import Thread

API_BASE = "http://127.0.0.1:8090"

def test_api_health():
    """Test if the API server is responding"""
    print("🔍 Testing API Health...")
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        if response.status_code == 200:
            print("✅ API server is responding")
            return True
        else:
            print(f"❌ API server responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API server connection failed: {e}")
        return False

def test_single_barcode_generation():
    """Test single barcode generation API"""
    print("\n🔍 Testing Single Barcode Generation...")

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

        print(f"⏱️  Response time: {end_time - start_time:.2f}s")
        print(f"📊 Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Single barcode generation successful")
            print(f"📄 Response: {json.dumps(result, indent=2)}")

            # Test if we can immediately download this barcode
            print("\n🔍 Testing immediate download...")
            download_response = requests.post(
                f"{API_BASE}/api/download-barcode",
                json=test_data,
                timeout=10
            )

            if download_response.status_code == 200:
                print("✅ Download API working")
                print(f"📄 Content-Type: {download_response.headers.get('content-type')}")
                print(f"📦 Content-Length: {len(download_response.content)} bytes")
                return True
            else:
                print(f"❌ Download API failed: {download_response.status_code}")
                return False
        else:
            print(f"❌ Generate API failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_batch_processing():
    """Test batch processing with multiple patients"""
    print("\n🔍 Testing Batch Processing...")

    batch_data = [
        {
            "patient_name": "John Doe",
            "patient_number": "11111111",
            "ward": "ICU",
            "room": "101"
        },
        {
            "patient_name": "Jane Smith",
            "patient_number": "22222222",
            "ward": "Bedah",
            "room": "A-202"
        },
        {
            "patient_name": "Ahmad Rahman",
            "patient_number": "33333333",
            "ward": "Anak",
            "room": "B-101"
        }
    ]

    print(f"📊 Testing with {len(batch_data)} patients...")

    # Test sequential processing (current implementation)
    start_time = time.time()
    success_count = 0

    for i, patient in enumerate(batch_data):
        print(f"🔄 Processing patient {i+1}/{len(batch_data)}: {patient['patient_name']}")

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
                    print(f"  ✅ Success")
                else:
                    print(f"  ❌ Failed: {result.get('error')}")
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"  ❌ Timeout")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error: {e}")

    end_time = time.time()
    print(f"\n⏱️  Total time: {end_time - start_time:.2f}s")
    print(f"📊 Success rate: {success_count}/{len(batch_data)} ({success_count/len(batch_data)*100:.1f}%)")

    return success_count == len(batch_data)

def test_error_handling():
    """Test various error scenarios"""
    print("\n🔍 Testing Error Handling...")

    error_cases = [
        {
            "name": "Empty data",
            "data": {},
            "expected_status": 400
        },
        {
            "name": "Missing patient name",
            "data": {
                "patient_number": "12345678",
                "ward": "ICU",
                "room": "101"
            },
            "expected_status": 400
        },
        {
            "name": "Invalid patient number (too short)",
            "data": {
                "patient_name": "Test",
                "patient_number": "123",
                "ward": "ICU",
                "room": "101"
            },
            "expected_status": 200  # Backend accepts it, frontend validates
        },
        {
            "name": "Very long name",
            "data": {
                "patient_name": "A" * 200,
                "patient_number": "12345678",
                "ward": "ICU",
                "room": "101"
            },
            "expected_status": 200
        }
    ]

    all_passed = True

    for case in error_cases:
        print(f"🧪 Testing: {case['name']}")
        try:
            response = requests.post(
                f"{API_BASE}/api/generate-barcode",
                json=case['data'],
                timeout=5
            )

            if response.status_code == case['expected_status']:
                print(f"  ✅ Expected status {case['expected_status']}")
            else:
                print(f"  ❌ Expected {case['expected_status']}, got {response.status_code}")
                all_passed = False

        except Exception as e:
            print(f"  ❌ Exception: {e}")
            all_passed = False

    return all_passed

def test_concurrent_requests():
    """Test concurrent request handling"""
    print("\n🔍 Testing Concurrent Requests...")

    def make_request(patient_id):
        data = {
            "patient_name": f"Concurrent Test {patient_id}",
            "patient_number": f"4444{patient_id:04d}",
            "ward": "Test",
            "room": f"Room {patient_id}"
        }

        try:
            response = requests.post(
                f"{API_BASE}/api/generate-barcode",
                json=data,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

    # Test with 5 concurrent requests
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    end_time = time.time()
    success_count = sum(results)

    print(f"⏱️  Concurrent processing time: {end_time - start_time:.2f}s")
    print(f"📊 Success rate: {success_count}/5 ({success_count/5*100:.1f}%)")

    return success_count == 5

def main():
    """Run all tests and provide analysis"""
    print("Patient Barcode Generator - API Troubleshooting Test")
    print("=" * 60)

    # Run all tests
    tests = [
        ("API Health", test_api_health),
        ("Single Barcode Generation", test_single_barcode_generation),
        ("Batch Processing", test_batch_processing),
        ("Error Handling", test_error_handling),
        ("Concurrent Requests", test_concurrent_requests)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"\nOverall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Issues identified.")

    return results

if __name__ == "__main__":
    main()
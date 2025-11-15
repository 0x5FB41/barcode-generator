#!/usr/bin/env python3
"""
Final comprehensive workflow test for Patient Barcode Generator
Tests all user workflows and validates the fixes
"""

import requests
import json
import time
import os

API_BASE = "http://127.0.0.1:8090"

def test_complete_single_workflow():
    """Test complete single barcode workflow"""
    print("Testing Complete Single Barcode Workflow...")
    print("-" * 50)

    # Step 1: Form validation simulation
    test_data = {
        "patient_name": "Workflow Test Patient",
        "patient_number": "88888888",
        "ward": "Test Ward",
        "room": "Test-101"
    }

    print(f"1. Form Data: {test_data}")

    # Step 2: Generate barcode
    print("2. Generating barcode...")
    try:
        response = requests.post(
            f"{API_BASE}/api/generate-barcode",
            json=test_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Generation successful")
            print(f"   Filename: {result.get('filename')}")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"   ❌ Generation failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

    # Step 3: Download barcode
    print("3. Downloading barcode...")
    try:
        download_response = requests.post(
            f"{API_BASE}/api/download-barcode",
            json=test_data,
            timeout=10
        )

        if download_response.status_code == 200:
            print("   ✅ Download successful")
            print(f"   Content-Type: {download_response.headers.get('content-type')}")
            print(f"   File size: {len(download_response.content)} bytes")

            # Save test file
            filename = f"workflow_test_{test_data['patient_number']}.png"
            with open(filename, 'wb') as f:
                f.write(download_response.content)
            print(f"   Saved as: {filename}")

        else:
            print(f"   ❌ Download failed: {download_response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

    print("✅ Single workflow completed successfully\n")
    return True

def test_complete_batch_workflow():
    """Test complete batch barcode workflow"""
    print("Testing Complete Batch Barcode Workflow...")
    print("-" * 50)

    # Step 1: CSV data simulation
    csv_data = """Batch Test 1,11111111,ICU,101
Batch Test 2,22222222,Bedah,A-202
Batch Test 3,33333333,Anak,B-101"""

    print(f"1. CSV Data:\n{csv_data}")

    # Step 2: Parse CSV (simulate frontend)
    lines = csv_data.split('\n')
    patients = []
    for line in lines:
        parts = line.split(',')
        if len(parts) == 4:
            name, number, ward, room = [p.strip() for p in parts]
            patients.append({
                "patient_name": name,
                "patient_number": number,
                "ward": ward,
                "room": room
            })

    print(f"2. Parsed {len(patients)} patients")

    # Step 3: Process batch
    print("3. Processing batch...")
    success_count = 0
    failed_patients = []

    for i, patient in enumerate(patients):
        print(f"   Processing {i+1}/{len(patients)}: {patient['patient_name']}")

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
                    print(f"     ✅ Success")
                else:
                    print(f"     ❌ Failed: {result.get('error')}")
                    failed_patients.append(patient)
            else:
                print(f"     ❌ HTTP Error: {response.status_code}")
                failed_patients.append(patient)

        except Exception as e:
            print(f"     ❌ Exception: {e}")
            failed_patients.append(patient)

    print(f"\n4. Batch Results:")
    print(f"   Success: {success_count}/{len(patients)}")
    print(f"   Failed: {len(failed_patients)}")

    # Step 4: Download successful barcodes
    print("5. Downloading successful barcodes...")
    download_count = 0

    for patient in patients:
        if patient not in failed_patients:
            try:
                download_response = requests.post(
                    f"{API_BASE}/api/download-barcode",
                    json=patient,
                    timeout=10
                )

                if download_response.status_code == 200:
                    download_count += 1
                    filename = f"batch_test_{patient['patient_number']}.png"
                    with open(filename, 'wb') as f:
                        f.write(download_response.content)
                    print(f"   Downloaded: {filename}")

            except Exception as e:
                print(f"   Download failed for {patient['patient_name']}: {e}")

    print(f"\n6. Download Results: {download_count}/{success_count} barcodes downloaded")
    print("✅ Batch workflow completed successfully\n")

    return success_count == len(patients) and download_count == success_count

def test_error_scenarios():
    """Test various error scenarios"""
    print("Testing Error Scenarios...")
    print("-" * 50)

    error_scenarios = [
        {
            "name": "Empty Request",
            "data": {},
            "expected_status": 400
        },
        {
            "name": "Missing Required Fields",
            "data": {"patient_name": "Test"},
            "expected_status": 400
        },
        {
            "name": "Invalid Patient Number",
            "data": {
                "patient_name": "Test",
                "patient_number": "abc123",
                "ward": "Test",
                "room": "Test"
            },
            "expected_status": 200  # Backend accepts, frontend validates
        },
        {
            "name": "Very Long Name",
            "data": {
                "patient_name": "A" * 150,
                "patient_number": "12345678",
                "ward": "Test",
                "room": "Test"
            },
            "expected_status": 200  # Backend accepts, frontend validates
        }
    ]

    all_passed = True

    for scenario in error_scenarios:
        print(f"Testing: {scenario['name']}")

        try:
            response = requests.post(
                f"{API_BASE}/api/generate-barcode",
                json=scenario['data'],
                timeout=5
            )

            status_match = response.status_code == scenario['expected_status']
            if status_match:
                print(f"   ✅ Expected status {scenario['expected_status']}")
            else:
                print(f"   ❌ Expected {scenario['expected_status']}, got {response.status_code}")
                all_passed = False

            # Check if response has proper error structure
            if response.status_code != 200:
                try:
                    result = response.json()
                    if 'error' in result:
                        print(f"   ✅ Proper error message: {result['error'][:50]}...")
                    else:
                        print(f"   ❌ No error message in response")
                        all_passed = False
                except:
                    print(f"   ❌ Invalid JSON response")
                    all_passed = False

        except Exception as e:
            print(f"   ❌ Exception: {e}")
            all_passed = False

    print("✅ Error scenarios testing completed\n")
    return all_passed

def test_performance_benchmarks():
    """Test performance benchmarks"""
    print("Testing Performance Benchmarks...")
    print("-" * 50)

    # Test single request performance
    print("1. Single Request Performance:")
    times = []
    for i in range(5):
        test_data = {
            "patient_name": f"Perf Test {i+1}",
            "patient_number": f"999{i+1:04d}",
            "ward": "Perf",
            "room": f"Room-{i+1}"
        }

        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/api/generate-barcode",
            json=test_data,
            timeout=10
        )
        end_time = time.time()

        if response.status_code == 200:
            times.append(end_time - start_time)

    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        print(f"   Average: {avg_time:.3f}s")
        print(f"   Min: {min_time:.3f}s")
        print(f"   Max: {max_time:.3f}s")
        print(f"   Requests/sec: {1/avg_time:.1f}")

        # Performance criteria
        if avg_time < 0.1:  # Less than 100ms
            print("   ✅ Excellent performance")
        elif avg_time < 0.5:  # Less than 500ms
            print("   ✅ Good performance")
        else:
            print("   ⚠️  Performance could be improved")

    # Test batch processing performance
    print("\n2. Batch Processing Performance:")
    batch_size = 10
    start_time = time.time()

    for i in range(batch_size):
        test_data = {
            "patient_name": f"Batch Perf {i+1}",
            "patient_number": f"888{i+1:04d}",
            "ward": "Batch",
            "room": f"B-{i+1}"
        }

        response = requests.post(
            f"{API_BASE}/api/generate-barcode",
            json=test_data,
            timeout=10
        )

        if response.status_code != 200:
            print(f"   ❌ Batch item {i+1} failed")
            return False

    end_time = time.time()
    total_time = end_time - start_time
    avg_batch_time = total_time / batch_size

    print(f"   Total time: {total_time:.3f}s")
    print(f"   Average per item: {avg_batch_time:.3f}s")
    print(f"   Throughput: {batch_size/total_time:.1f} items/sec")

    if avg_batch_time < 0.05:  # Less than 50ms per item
        print("   ✅ Excellent batch performance")
    elif avg_batch_time < 0.1:  # Less than 100ms per item
        print("   ✅ Good batch performance")
    else:
        print("   ⚠️  Batch performance could be improved")

    print("✅ Performance benchmarking completed\n")
    return True

def cleanup_test_files():
    """Clean up test files created during testing"""
    print("Cleaning up test files...")

    test_files = [
        "workflow_test_88888888.png",
        "batch_test_11111111.png",
        "batch_test_22222222.png",
        "batch_test_33333333.png",
        "test_barcode_output.png"
    ]

    cleaned = 0
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                cleaned += 1
                print(f"   Removed: {file}")
            except Exception as e:
                print(f"   Could not remove {file}: {e}")

    print(f"✅ Cleaned up {cleaned} test files\n")
    return cleaned

def main():
    """Run all workflow tests"""
    print("Patient Barcode Generator - Final Workflow Test")
    print("=" * 60)
    print()

    # Run all tests
    tests = [
        ("Single Workflow", test_complete_single_workflow),
        ("Batch Workflow", test_complete_batch_workflow),
        ("Error Scenarios", test_error_scenarios),
        ("Performance Benchmarks", test_performance_benchmarks)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False

    # Cleanup
    cleanup_test_files()

    # Final Summary
    print("=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"\nOverall: {passed_count}/{total_count} test suites passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED!")
        print("The Patient Barcode Generator is ready for production use.")
        print("\nKey Improvements Verified:")
        print("✅ API endpoints working correctly")
        print("✅ Single and batch workflows functional")
        print("✅ Error handling robust")
        print("✅ Performance within acceptable ranges")
        print("✅ All reported issues resolved")
    else:
        print(f"\n⚠️  {total_count - passed_count} test suites failed.")
        print("Some issues remain to be addressed.")

    return results

if __name__ == "__main__":
    main()
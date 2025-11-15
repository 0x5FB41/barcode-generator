# Test script untuk barcode generator functionality
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import generate_barcode_with_patient_data

def test_barcode_generation():
    """Test barcode generation dengan sample data"""
    print("Testing Barcode Generation...")

    sample_data = {
        'patient_number': '012345678',
        'patient_name': 'Test Patient',
        'ward': 'ICU',
        'room': '101'
    }

    try:
        # Generate barcode
        image_buffer = generate_barcode_with_patient_data(
            sample_data['patient_number'],
            sample_data['patient_name'],
            sample_data['ward'],
            sample_data['room']
        )

        # Save test file
        filename = "test_barcode_output.png"
        with open(filename, 'wb') as f:
            f.write(image_buffer.getvalue())

        print(f"[SUCCESS] Barcode berhasil dibuat: {filename}")
        print(f"   Data pasien: {sample_data}")

        # Check file size
        file_size = os.path.getsize(filename)
        print(f"   File size: {file_size} bytes")

        if file_size > 1000:  # Should be at least 1KB for a valid image
            print("[SUCCESS] Test successful - File size looks valid")
        else:
            print("[WARNING] File size seems small")

        return True

    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_barcode_generation()
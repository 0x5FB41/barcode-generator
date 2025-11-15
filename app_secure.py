from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import re
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os
from datetime import datetime
import bleach

app = Flask(__name__)
# Configure CORS for specific domains only in production
CORS(app, origins=['http://localhost:8090', 'http://127.0.0.1:8090'])

def validate_input(input_string, pattern, max_length=100):
    """Enhanced input validation"""
    if not input_string or len(input_string) > max_length:
        return False

    # Remove potentially dangerous characters
    cleaned = bleach.clean(input_string.strip())

    # Check if pattern matches
    if not re.match(pattern, cleaned):
        return False

    return cleaned

def generate_barcode_with_patient_data(patient_number, patient_name, ward, room, filename=None):
    """Generate barcode with enhanced security"""
    # Validate all inputs
    patient_number = validate_input(patient_number, r'^[a-zA-Z0-9_-]+$', 50)
    patient_name = validate_input(patient_name, r'^[a-zA-Z\s\-\.\']+$', 100)
    ward = validate_input(ward, r'^[a-zA-Z0-9\s\-\.\']+$', 50)
    room = validate_input(room, r'^[a-zA-Z0-9\s\-\.\']+$', 20)

    if not all([patient_number, patient_name, ward, room]):
        raise ValueError("Invalid input parameters")

    # Generate the barcode without text (we'll add our own)
    options = {
        'module_width': 0.3,
        'module_height': 12,
        'quiet_zone': 3,
        'background': 'white',
        'foreground': 'black',
    }

    code = Code128(patient_number, writer=ImageWriter())

    # Save to bytes buffer
    buffer = io.BytesIO()
    code.write(buffer, options=options)
    buffer.seek(0)

    # Open the barcode image
    barcode_img = Image.open(buffer)

    # Create a new image with space for all patient information
    barcode_width, barcode_height = barcode_img.size
    padding = 40

    # Calculate space needed for all text elements
    name_height = 40
    info_height = 30
    number_height = 40

    total_width = barcode_width + (padding * 2)
    total_height = barcode_height + name_height + info_height + number_height + 20

    final_img = Image.new('RGB', (total_width, total_height), 'white')

    # Paste the barcode in the middle
    barcode_x = (total_width - barcode_width) // 2
    barcode_y = name_height + info_height + 10
    final_img.paste(barcode_img, (barcode_x, barcode_y))

    # Setup drawing
    draw = ImageDraw.Draw(final_img)

    # Try to load fonts with fallback options
    try:
        name_font = ImageFont.truetype("arial.ttf", 24)
        info_font = ImageFont.truetype("arial.ttf", 18)
        number_font = ImageFont.truetype("arial.ttf", 28)
    except:
        try:
            name_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
            info_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
            number_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
        except:
            name_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
            number_font = ImageFont.load_default()

    # Draw patient name at the top (centered)
    name_bbox = draw.textbbox((0, 0), patient_name, font=name_font)
    name_width = name_bbox[2] - name_bbox[0]
    name_x = (total_width - name_width) // 2
    name_y = 10
    draw.text((name_x, name_y), patient_name, fill='black', font=name_font)

    # Draw ward and room information in the middle (centered)
    ward_room_text = f"Ward: {ward} | Room: {room}"
    info_bbox = draw.textbbox((0, 0), ward_room_text, font=info_font)
    info_width = info_bbox[2] - info_bbox[0]
    info_x = (total_width - info_width) // 2
    info_y = name_height + 15
    draw.text((info_x, info_y), ward_room_text, fill='black', font=info_font)

    # Draw patient number at the bottom (centered)
    number_bbox = draw.textbbox((0, 0), patient_number, font=number_font)
    number_width = number_bbox[2] - number_bbox[0]
    number_x = (total_width - number_width) // 2
    number_y = barcode_y + barcode_height + 15
    draw.text((number_x, number_y), patient_number, fill='black', font=number_font)

    # Save or return the final image
    if filename:
        final_img.save(filename)
        return final_img, filename
    else:
        # Return as bytes for web response
        output_buffer = io.BytesIO()
        final_img.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        return output_buffer

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/generate-barcode', methods=['POST'])
def api_generate_barcode():
    """API endpoint to generate barcode for patient with enhanced security"""
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data'
            }), 400

        # Enhanced validation
        patient_name = data.get('patient_name', '').strip()
        patient_number = data.get('patient_number', '').strip()
        ward = data.get('ward', '').strip()
        room = data.get('room', '').strip()

        # Server-side validation
        if not all([patient_name, patient_number, ward, room]):
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400

        # Pattern validation
        if not re.match(r'^[a-zA-Z\s\-\.\']{2,50}$', patient_name):
            return jsonify({
                'success': False,
                'error': 'Invalid patient name format'
            }), 400

        if not re.match(r'^[a-zA-Z0-9_-]{8,12}$', patient_number):
            return jsonify({
                'success': False,
                'error': 'Patient number must be 8-12 alphanumeric characters'
            }), 400

        if not re.match(r'^[a-zA-Z0-9\s\-\.\']{1,30}$', ward):
            return jsonify({
                'success': False,
                'error': 'Invalid ward format'
            }), 400

        if not re.match(r'^[a-zA-Z0-9\s\-\.\']{1,20}$', room):
            return jsonify({
                'success': False,
                'error': 'Invalid room format'
            }), 400

        # Generate barcode
        image_buffer = generate_barcode_with_patient_data(
            patient_number, patient_name, ward, room
        )

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', patient_name)
        filename = f"{patient_number}_{safe_name}_{timestamp}.png"

        return jsonify({
            'success': True,
            'message': 'Barcode generated successfully',
            'filename': filename,
            'patient_data': {
                'name': patient_name,
                'number': patient_number,
                'ward': ward,
                'room': room
            }
        })

    except Exception as e:
        # Log error for monitoring
        app.logger.error(f"Barcode generation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/download-barcode', methods=['POST'])
def api_download_barcode():
    """API endpoint to download generated barcode with enhanced security"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data'
            }), 400

        # Enhanced validation
        patient_name = data.get('patient_name', '').strip()
        patient_number = data.get('patient_number', '').strip()
        ward = data.get('ward', '').strip()
        room = data.get('room', '').strip()

        # Validate inputs
        if not all([patient_name, patient_number, ward, room]):
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400

        # Apply same validation patterns as generation
        if not re.match(r'^[a-zA-Z\s\-\.\']{2,50}$', patient_name):
            return jsonify({
                'success': False,
                'error': 'Invalid patient name format'
            }), 400

        if not re.match(r'^[a-zA-Z0-9_-]{8,12}$', patient_number):
            return jsonify({
                'success': False,
                'error': 'Invalid patient number format'
            }), 400

        # Generate barcode image
        image_buffer = generate_barcode_with_patient_data(
            patient_number, patient_name, ward, room
        )

        # Generate safe filename
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', patient_name)
        filename = f"{patient_number}_{safe_name}.png"

        return send_file(
            image_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='image/png'
        )

    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files with security checks"""
    # Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': 'Invalid file path'}), 400

    try:
        return send_file(f'static/{filename}')
    except:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    print("Starting SECURE Patient Barcode Generator Web Application...")
    print("Access the application at: http://localhost:8090")

    # Only use development server in debug mode
    if os.getenv('FLASK_ENV') == 'production':
        # In production, use gunicorn
        from waitress import serve
        serve(app, host='127.0.0.1', port=8090)
    else:
        app.run(debug=False, host='127.0.0.1', port=8090)
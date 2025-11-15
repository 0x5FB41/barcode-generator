from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re
import sys
from datetime import datetime
import logging
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security configurations
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'  # Change this!
app.config['UPLOAD_FOLDER'] = 'generated_barcodes'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# CORS configuration - RESTRICT IN PRODUCTION
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],  # Restrict to your domain in production
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "max_age": 3600
    }
})

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return ""
    # Remove HTML tags and entities
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    return text.strip()

def validate_patient_data(patient_name, patient_number, ward, room):
    """Enhanced input validation"""
    errors = []

    # Name validation
    if not patient_name or len(patient_name) < 2:
        errors.append("Nama pasien minimal 2 karakter")
    elif len(patient_name) > 50:
        errors.append("Nama pasien maksimal 50 karakter")
    elif not re.match(r'^[a-zA-Z\s\-.]+$', patient_name):
        errors.append("Nama pasien hanya boleh huruf, spasi, titik, dan strip")

    # Number validation
    if not patient_number:
        errors.append("Nomor pasien harus diisi")
    elif not re.match(r'^\d{8,12}$', patient_number):
        errors.append("Nomor pasien harus 8-12 digit angka")

    # Ward validation
    if not ward or len(ward.strip()) < 1:
        errors.append("Ruangan harus diisi")
    elif len(ward.strip()) > 30:
        errors.append("Ruangan maksimal 30 karakter")

    # Room validation
    if not room or len(room.strip()) < 1:
        errors.append("Kamar harus diisi")
    elif len(room.strip()) > 20:
        errors.append("Kamar maksimal 20 karakter")

    return errors

def generate_barcode_with_patient_data(patient_number, patient_name, ward, room, filename=None):
    """Generate barcode with enhanced error handling"""
    try:
        logger.info(f"Generating barcode: {patient_name} ({patient_number})")

        # Sanitize all inputs
        patient_name = sanitize_input(patient_name)[:50]
        patient_number = re.sub(r'[^\d]', '', str(patient_number))
        ward = sanitize_input(ward)[:30]
        room = sanitize_input(room)[:20]

        # Generate barcode
        options = {
            'module_width': 0.3,
            'module_height': 12,
            'quiet_zone': 3,
            'background': 'white',
            'foreground': 'black',
        }

        code = Code128(patient_number, writer=ImageWriter())
        buffer = io.BytesIO()
        code.write(buffer, options=options)
        buffer.seek(0)

        barcode_img = Image.open(buffer)
        barcode_width, barcode_height = barcode_img.size
        padding = 40

        # Calculate dimensions
        name_height = 40
        info_height = 30
        number_height = 40
        total_width = barcode_width + (padding * 2)
        total_height = barcode_height + name_height + info_height + number_height + 20

        final_img = Image.new('RGB', (total_width, total_height), 'white')
        barcode_x = (total_width - barcode_width) // 2
        barcode_y = name_height + info_height + 10
        final_img.paste(barcode_img, (barcode_x, barcode_y))

        # Text rendering with DejaVu Sans font (standard on Linux)
        draw = ImageDraw.Draw(final_img)

        # Try to load DejaVu Sans first, then fallback to default
        try:
            # DejaVu Sans is standard on most Linux systems
            name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            number_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            try:
                # Fallback to Arial (Windows/macOS)
                name_font = ImageFont.truetype("arial.ttf", 28)
                info_font = ImageFont.truetype("arial.ttf", 20)
                number_font = ImageFont.truetype("arial.ttf", 24)
            except:
                # Last resort: default font with larger sizes
                name_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
                number_font = ImageFont.load_default()

        # Layout: Name on top, Barcode in middle, Room/Number at bottom
        padding = 40

        # Calculate dimensions
        name_height = 50
        info_height = 35
        number_height = 35
        total_height = barcode_height + name_height + info_height + number_height + 60
        final_img = Image.new('RGB', (total_width, total_height), 'white')

        # Redraw barcode on resized canvas
        draw = ImageDraw.Draw(final_img)
        barcode_x = (total_width - barcode_width) // 2
        barcode_y = name_height + 30
        final_img.paste(barcode_img, (barcode_x, barcode_y))

        # Draw text elements
        # 1. Patient name at top (larger)
        name_bbox = draw.textbbox((0, 0), patient_name, font=name_font)
        name_x = (total_width - (name_bbox[2] - name_bbox[0])) // 2
        draw.text((name_x, 15), patient_name, fill='black', font=name_font)

        # 2. Ward and Room at bottom (medium)
        ward_room_text = f"Ruangan: {ward} | Kamar: {room}"
        info_bbox = draw.textbbox((0, 0), ward_room_text, font=info_font)
        info_x = (total_width - (info_bbox[2] - info_bbox[0])) // 2
        draw.text((info_x, total_height - number_height - 15), ward_room_text, fill='black', font=info_font)

        # 3. Patient number under barcode (medium)
        number_bbox = draw.textbbox((0, 0), patient_number, font=number_font)
        number_x = (total_width - (number_bbox[2] - number_bbox[0])) // 2
        draw.text((number_x, barcode_y + barcode_height + 15), patient_number, fill='black', font=number_font)

        # Save or return
        if filename:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            final_img.save(filepath)
            logger.info(f"Barcode saved: {filepath}")
            return final_img, filename
        else:
            output_buffer = io.BytesIO()
            final_img.save(output_buffer, format='PNG')
            output_buffer.seek(0)
            return output_buffer

    except Exception as e:
        logger.error(f"Barcode generation error: {str(e)}")
        raise

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/generate-barcode', methods=['POST'])
def api_generate_barcode():
    """Generate barcode API with security"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON required'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Extract and validate data
        patient_name = sanitize_input(data.get('patient_name', ''))
        patient_number = data.get('patient_number', '').strip()
        ward = sanitize_input(data.get('ward', ''))
        room = sanitize_input(data.get('room', ''))

        # Enhanced validation
        errors = validate_patient_data(patient_name, patient_number, ward, room)
        if errors:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400

        # Generate barcode
        try:
            image_buffer = generate_barcode_with_patient_data(
                patient_number, patient_name, ward, room
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = secure_filename(patient_name).replace(' ', '_')
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
            logger.error(f"Barcode generation failed: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Barcode generation failed: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/download-barcode', methods=['POST'])
def api_download_barcode():
    """Download barcode API"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON required'}), 400

        data = request.get_json()
        patient_name = sanitize_input(data.get('patient_name', ''))
        patient_number = data.get('patient_number', '').strip()
        ward = sanitize_input(data.get('ward', ''))
        room = sanitize_input(data.get('room', ''))

        # Validation
        errors = validate_patient_data(patient_name, patient_number, ward, room)
        if errors:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400

        try:
            image_buffer = generate_barcode_with_patient_data(
                patient_number, patient_name, ward, room
            )

            safe_name = secure_filename(patient_name).replace(' ', '_')
            filename = f"{patient_number}_{safe_name}.png"

            return send_file(
                image_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='image/png'
            )

        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Download failed: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"Download API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Download failed'
        }), 500

@app.route('/health')
def health_check():
    """Health check for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'success': False, 'error': 'Method not allowed'}), 405

@app.errorhandler(413)
def too_large(error):
    return jsonify({'success': False, 'error': 'Request too large'}), 413

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {str(error)}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    logger.info("Starting Patient Barcode Generator - SECURED VERSION")
    logger.info("Access: http://localhost:8090")

    # Production-ready server
    app.run(
        host='0.0.0.0',
        port=8090,
        debug=False,  # NO DEBUG IN PRODUCTION
        threaded=True
    )
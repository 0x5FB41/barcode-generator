from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re
import threading
import time
import schedule
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
    elif not re.match(r'^\d+$', patient_number):
        errors.append("Nomor pasien harus berupa angka")
    elif len(patient_number) > 8:
        errors.append("Nomor pasien maksimal 8 digit")
    elif len(patient_number) < 1:
        errors.append("Nomor pasien minimal 1 digit")

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

def clear_generated_barcodes():
    """Clear all generated barcode files - runs automatically at midnight"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_folder):
            files = os.listdir(upload_folder)
            deleted_count = 0
            for file in files:
                file_path = os.path.join(upload_folder, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
            logger.info(f"Auto-clear: Deleted {deleted_count} barcode files at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logger.info("Auto-clear: Upload folder does not exist, nothing to clear")
    except Exception as e:
        logger.error(f"Auto-clear error: {str(e)}")

def run_scheduler():
    """Run the scheduler in a separate thread"""
    schedule.every().day.at("00:00").do(clear_generated_barcodes)
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

class NoTextWriter(ImageWriter):
    """Custom ImageWriter that completely disables text rendering"""

    def paint_text(self, xpos, ypos):
        """Override paint_text to do nothing - no text will be rendered"""
        pass

def generate_barcode_with_patient_data(patient_number, patient_name, ward, room, filename=None):
    """Generate barcode with enhanced error handling"""
    try:
        logger.info(f"Generating barcode: {patient_name} ({patient_number})")

        # Sanitize all inputs
        patient_name = sanitize_input(patient_name)[:50]
        patient_number = re.sub(r'[^\d]', '', str(patient_number))
        # Pad patient number to 8 digits with leading zeros
        patient_number = patient_number.zfill(8)
        ward = sanitize_input(ward)[:30]
        room = sanitize_input(room)[:20]

        # Create barcode with custom writer that has NO text rendering
        writer = NoTextWriter()
        code = Code128(patient_number, writer=writer)

        # Generate barcode
        temp_buffer = io.BytesIO()
        code.write(temp_buffer, options={
            'module_width': 0.3,
            'module_height': 12,
            'quiet_zone': 3,
            # Remove font_size=0 to avoid ppem error, rely on custom writer instead
        })
        temp_buffer.seek(0)

        barcode_img = Image.open(temp_buffer)
        barcode_width, barcode_height = barcode_img.size

        # Calculate dimensions for more rectangular shape
        name_height = 60  # Reduced for tighter spacing
        info_height = 40  # Reduced for tighter spacing
        padding = 30  # Reduced horizontal padding
        total_width = barcode_width + (padding * 2)
        total_height = barcode_height + name_height + info_height + 30  # Reduced overall height

        # Create final image with proper dimensions
        final_img = Image.new('RGB', (total_width, total_height), 'white')
        draw = ImageDraw.Draw(final_img)

        # Paste barcode centered with tighter spacing
        barcode_x = (total_width - barcode_width) // 2
        barcode_y = name_height + 10  # Reduced spacing between name and barcode
        final_img.paste(barcode_img, (barcode_x, barcode_y))

        # Try to load fonts with multiple fallback paths for cross-platform consistency
        font_loaded = False

        # Try standard Linux DejaVu paths
        dejavu_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf"
        ]

        for name_path in dejavu_paths:
            try:
                if "Bold" in name_path:
                    name_font = ImageFont.truetype(name_path, 38)  # Larger name font
                    info_font = ImageFont.truetype(name_path.replace("-Bold", ""), 20)  # Info font to 20pt
                    font_loaded = True
                    break
            except:
                continue

        if not font_loaded:
            try:
                # Fallback to Arial (Windows/macOS)
                name_font = ImageFont.truetype("arial.ttf", 38)
                info_font = ImageFont.truetype("arial.ttf", 20)
                font_loaded = True
            except:
                try:
                    # Try system default fonts
                    name_font = ImageFont.truetype("arialbd.ttf", 38)  # Arial Bold
                    info_font = ImageFont.truetype("arial.ttf", 20)
                    font_loaded = True
                except:
                    # Last resort: PIL default font
                    name_font = ImageFont.load_default()
                    info_font = ImageFont.load_default()
                    font_loaded = True

        logger.info(f"Font loading status: {font_loaded}")

  
        # Draw patient name (larger font, moved closer to top)
        name_bbox = draw.textbbox((0, 0), patient_name, font=name_font)
        name_x = (total_width - (name_bbox[2] - name_bbox[0])) // 2
        draw.text((name_x, 10), patient_name, fill='black', font=name_font)  # Moved up to 10

        # Draw ward and room info at bottom in two lines (smaller font)
        ward_text = f"Ruangan: {ward}"
        room_text = f"Kamar: {room}"

        # Ward text (first line) - very close to barcode
        ward_bbox = draw.textbbox((0, 0), ward_text, font=info_font)
        ward_x = (total_width - (ward_bbox[2] - ward_bbox[0])) // 2
        draw.text((ward_x, barcode_y + barcode_height + 5), ward_text, fill='black', font=info_font)

        # Room text (second line) - positioned below ward text with tight spacing
        room_bbox = draw.textbbox((0, 0), room_text, font=info_font)
        room_x = (total_width - (room_bbox[2] - room_bbox[0])) // 2
        draw.text((room_x, barcode_y + barcode_height + 25), room_text, fill='black', font=info_font)

        # DEBUG: Log what we're actually drawing
        logger.info(f"DEBUG: Drawing ward_text='{ward_text}' at position ({ward_x}, {barcode_y + barcode_height + 5})")
        logger.info(f"DEBUG: Drawing room_text='{room_text}' at position ({room_x}, {barcode_y + barcode_height + 25})")
        logger.info(f"DEBUG: Patient name='{patient_name}' at position ({name_x}, 10)")

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

        # Apply zero-padding before validation for consistency
        patient_number_clean = re.sub(r'[^\d]', '', str(patient_number))
        patient_number_padded = patient_number_clean.zfill(8)

        # Enhanced validation
        errors = validate_patient_data(patient_name, patient_number, ward, room)
        if errors:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400

        # Generate barcode using padded number
        try:
            image_buffer = generate_barcode_with_patient_data(
                patient_number_padded, patient_name, ward, room
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = secure_filename(patient_name).replace(' ', '_')
            filename = f"{patient_number_padded}_{safe_name}_{timestamp}.png"

            return jsonify({
                'success': True,
                'message': 'Barcode generated successfully',
                'filename': filename,
                'patient_data': {
                    'name': patient_name,
                    'number': patient_number_padded,  # Return padded number
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

        # Apply zero-padding before validation for consistency
        patient_number_clean = re.sub(r'[^\d]', '', str(patient_number))
        patient_number_padded = patient_number_clean.zfill(8)

        # Validation
        errors = validate_patient_data(patient_name, patient_number, ward, room)
        if errors:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400

        try:
            image_buffer = generate_barcode_with_patient_data(
                patient_number_padded, patient_name, ward, room
            )

            safe_name = secure_filename(patient_name).replace(' ', '_')
            filename = f"{patient_number_padded}_{safe_name}.png"

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

    # Start the auto-clearing scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Auto-clearing scheduler started - will clear generated barcodes daily at midnight")

    logger.info("Starting Patient Barcode Generator - SECURED VERSION")
    logger.info("Access: http://localhost:8091")

    # Development server with debug for troubleshooting
    app.run(
        host='0.0.0.0',
        port=8091,  # Change port to avoid conflicts
        debug=True,  # Enable debug to see errors
        threaded=True
    )
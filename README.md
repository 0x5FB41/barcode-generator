# Patient Barcode Generator - Rumah Sakit

Sistem web-based untuk generate barcode pasien rumah sakit dengan informasi lengkap nama, nomor pasien, ruangan, dan kamar.

## Fitur Utama

- ✅ **Form Input Pasien**: Input data pasien dengan validasi real-time
- ✅ **Generator Barcode**: Buat barcode Code128 untuk data pasien
- ✅ **Informasi Lengkap**: Termasuk nama, nomor pasien, ruangan (ward), dan kamar
- ✅ **Preview Real-time**: Lihat preview barcode sebelum download
- ✅ **Download Barcode**: Simpan barcode dalam format PNG
- ✅ **Interface Bahasa Indonesia**: Interface user-friendly dalam bahasa Indonesia
- ✅ **Responsive Design**: Bekerja di desktop dan mobile
- ✅ **Docker Support**: Mudah deployment dengan Docker

## Teknologi yang Digunakan

### Backend
- **Python 3.9+**
- **Flask** - Web framework
- **Flask-CORS** - Cross-origin resource sharing
- **python-barcode** - Library untuk generate barcode
- **Pillow** - Image processing
- **Gunicorn** - WSGI server (production)

### Frontend
- **HTML5** + **CSS3** + **JavaScript**
- **Bootstrap 5** - UI framework
- **Font Awesome** - Icons

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Orchestration

## Cara Menjalankan

### Metode 1: Docker (Recommended)

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd patient-barcode-generator
   ```

2. **Build dan run dengan Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Akses aplikasi**
   ```
   http://localhost:5000
   ```

### Metode 2: Manual Setup

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Jalankan aplikasi**
   ```bash
   python app.py
   ```

3. **Akses aplikasi**
   ```
   http://localhost:5000
   ```

## Struktur Project

```
patient-barcode-generator/
├── app.py                    # Flask application
├── generate_barcode.py       # Original barcode generator
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
├── README.md               # Project documentation
├── templates/
│   └── index.html          # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css       # Custom CSS styles
│   └── js/
│       └── app.js          # JavaScript functionality
└── *.png                   # Generated barcodes
```

## API Endpoints

### Generate Barcode
```
POST /api/generate-barcode
Content-Type: application/json

Request Body:
{
    "patient_name": "Nama Pasien",
    "patient_number": "012345678",
    "ward": "ICU",
    "room": "101"
}

Response:
{
    "success": true,
    "message": "Barcode generated successfully",
    "filename": "012345678_Nama_Pasien_20231214_143022.png",
    "patient_data": {
        "name": "Nama Pasien",
        "number": "012345678",
        "ward": "ICU",
        "room": "101"
    }
}
```

### Download Barcode
```
POST /api/download-barcode
Content-Type: application/json

Request Body:
{
    "patient_name": "Nama Pasien",
    "patient_number": "012345678",
    "ward": "ICU",
    "room": "101"
}

Response: PNG file (binary)
```

## Format Barcode

- **Type**: Code128
- **Content**: Patient number (8-12 digit angka)
- **Layout**:
  - Top: Patient name (24pt font)
  - Middle: Ward & Room information (18pt font)
  - Center: Barcode image
  - Bottom: Patient number (28pt font)
- **Output**: PNG dengan white background

## Validasi Input

### Nama Pasien
- Required: Yes
- Length: 2-50 karakter
- Characters: Letters, spaces, punctuation

### Nomor Pasien
- Required: Yes
- Length: 8-12 digit
- Format: Numeric only

### Ruangan (Ward)
- Required: Yes
- Options: ICU, IGD, Bedah, Penyakit Dalam, Kebidanan, Anak, Syaraf, Jantung, Paru, Gigi & Mulut

### Kamar (Room)
- Required: Yes
- Length: 1-20 karakter
- Format: Alphanumeric (contoh: 101, A-2, VIP-1)

## Deployment dengan Docker

### Build Image
```bash
docker build -t patient-barcode-generator .
```

### Run Container
```bash
docker run -p 5000:5000 patient-barcode-generator
```

### Production dengan Docker Compose
```bash
# Environment variable
export FLASK_ENV=production

# Run detached
docker-compose up -d --build
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Flask environment (development/production) |
| `PYTHONUNBUFFERED` | `1` | Python output buffering |
| `PORT` | `5000` | Application port |

## Troubleshooting

### Common Issues

1. **Font not found error**
   - Docker includes fallback to default fonts
   - Windows/Linux should have Arial font available

2. **Permission denied**
   - Ensure Docker has proper permissions
   - Check volume mount permissions

3. **Port already in use**
   - Change port in docker-compose.yml
   - Kill existing process on port 5000

4. **Barcode generation failed**
   - Check patient number format (8-12 digits)
   - Ensure all required fields are filled

### Debug Mode
```bash
# Set development environment
export FLASK_ENV=development
python app.py
```

## Monitoring dan Logging

- **Flask debug mode**: Development debugging
- **Console logging**: Basic operation logs
- **Error handling**: Try-catch blocks with user feedback
- **Statistics tracking**: Local storage for generation counts

## Security Considerations

- Input validation untuk semua user inputs
- CORS enabled untuk API endpoints
- No file system access vulnerabilities
- Rate limiting bisa ditambahkan untuk production

## Kontribusi

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License - bisa digunakan untuk keperluan komersial dan non-komersial

## Support

Untuk pertanyaan atau isu:
- Create issue di repository
- Email: [your-email@domain.com]

## Changelog

### v1.0.0
- Initial release
- Basic barcode generation
- Web interface with form validation
- Docker support
- Bahasa Indonesia interface
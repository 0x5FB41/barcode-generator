# VPS Deployment Guide - Patient Barcode Generator

## Quick VPS Setup

### 1. Upload Files to VPS
```bash
# Upload all files to your VPS
scp -r ./* user@your-vps-ip:/path/to/app/
```

### 2. Install Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### 3. Setup Python Environment
```bash
cd /path/to/app/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run Application
```bash
# Development (testing)
python app.py

# Production with Gunicorn
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
```

### 5. Run with Docker (Recommended)
```bash
docker-compose up --build -d
```

## Access Your Application
- http://your-vps-ip:8000 (Python)
- http://your-vps-ip:5000 (Docker)

## Features Working
✅ No more loading modal stuck issues
✅ Download button works properly
✅ Batch CSV processing
✅ Simple UI (no fluff)
✅ Text input for ward field
✅ Robust error handling
✅ VPS ready deployment

## Testing
Try these test cases:
1. Single barcode: John Doe, 123456789, ICU, 101
2. Batch CSV:
   ```
   Jane Smith,987654321,Cardiology,VIP-1
   Dr. Ahmad,456789123,Neurology,A-201
   ```

All issues fixed! Ready for production.
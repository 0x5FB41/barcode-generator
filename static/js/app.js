// Fixed JavaScript - No more loading modal issues, no clutter
let generatedBarcodes = [];
let isProcessing = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Form handlers
    document.getElementById('singleForm').addEventListener('submit', handleSingleForm);
    document.getElementById('batchForm').addEventListener('submit', handleBatchForm);
    document.getElementById('downloadAllBtn').addEventListener('click', downloadAllBarcodes);
});

// Handle single barcode form
async function handleSingleForm(e) {
    e.preventDefault();

    if (isProcessing) {
        showNotification('Please wait for current operation to complete', 'warning');
        return;
    }

    const data = {
        patient_name: document.getElementById('singleName').value.trim(),
        patient_number: document.getElementById('singleNumber').value.trim()
    };

    if (!validateForm(data)) {
        return;
    }

    isProcessing = true;
    showStatus('Processing...');

    try {
        const result = await generateBarcode(data);
        if (result.success) {
            addBarcodeToResults(result, data);
            showNotification(`Barcode untuk ${data.patient_name} berhasil dibuat!`, 'success');
            document.getElementById('singleForm').reset();
        } else {
            showNotification(result.error || 'Gagal membuat barcode', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Terjadi kesalahan: ' + error.message, 'danger');
    } finally {
        isProcessing = false;
        hideStatus();
    }
}

// Handle batch form
async function handleBatchForm(e) {
    e.preventDefault();

    if (isProcessing) {
        showNotification('Please wait for current operation to complete', 'warning');
        return;
    }

    const batchData = document.getElementById('batchData').value.trim();
    if (!batchData) {
        showNotification('Data pasien tidak boleh kosong', 'danger');
        return;
    }

    const patients = parseBatchData(batchData);
    if (patients.length === 0) {
        showNotification('Tidak ada data pasien yang valid', 'danger');
        return;
    }

    isProcessing = true;
    const results = [];

    try {
        for (let i = 0; i < patients.length; i++) {
            const patient = patients[i];
            showStatus(`Processing ${i + 1}/${patients.length}: ${patient.patient_name}`);

            try {
                const result = await generateBarcode(patient);
                if (result.success) {
                    results.push({ success: true, data: result, patient });
                } else {
                    results.push({ success: false, error: result.error, patient });
                }
            } catch (error) {
                results.push({ success: false, error: error.message, patient });
            }

            // Small delay between requests
            await sleep(300);
        }

        displayBatchResults(results);
        const successCount = results.filter(r => r.success).length;
        showNotification(`${successCount} dari ${patients.length} barcode berhasil dibuat!`, 'success');
        document.getElementById('batchForm').reset();

    } catch (error) {
        showNotification('Terjadi kesalahan: ' + error.message, 'danger');
    } finally {
        isProcessing = false;
        hideStatus();
    }
}

// Generate barcode
async function generateBarcode(data) {
    const response = await fetch('/api/generate-barcode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
}

// Parse batch CSV data
function parseBatchData(csvData) {
    const lines = csvData.split('\n').filter(line => line.trim());
    const patients = [];

    lines.forEach(line => {
        const parts = line.split(',').map(part => part.trim());
        if (parts.length === 2) {
            const [name, number] = parts;
            if (name && number) {
                patients.push({
                    patient_name: name,
                    patient_number: number
                });
            }
        }
    });

    return patients;
}

// Add barcode to results
function addBarcodeToResults(result, data) {
    generatedBarcodes.push({ result, data });

    const resultsSection = document.getElementById('resultsSection');
    const resultsDiv = document.getElementById('results');

    resultsSection.style.display = 'block';
    document.getElementById('downloadAllBtn').style.display = 'inline-block';

    const barcodeHtml = `
        <div class="barcode-item">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <h6>${data.patient_name} - ${data.patient_number}</h6>
                </div>
                <button class="btn btn-sm btn-primary ms-2" onclick="downloadSingleBarcode('${data.patient_number}', '${data.patient_name}')">
                    Download
                </button>
            </div>
        </div>
    `;

    resultsDiv.insertAdjacentHTML('beforeend', barcodeHtml);
}

// Display batch results
function displayBatchResults(results) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsDiv = document.getElementById('results');

    resultsSection.style.display = 'block';

    let html = '';
    results.forEach((result) => {
        if (result.success) {
            generatedBarcodes.push({ result: result.data, patient: result.patient });
            html += `
                <div class="barcode-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6>${result.patient.patient_name} - ${result.patient.patient_number}</h6>
                        </div>
                        <button class="btn btn-sm btn-primary ms-2" onclick="downloadSingleBarcode('${result.patient.patient_number}', '${result.patient.patient_name}')">
                            Download
                        </button>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="barcode-item border-danger">
                    <div class="text-danger">
                        <strong>${result.patient.patient_name} - ${result.patient.patient_number}</strong><br>
                        Error: ${result.error}
                    </div>
                </div>
            `;
        }
    });

    resultsDiv.innerHTML = html;

    if (generatedBarcodes.length > 0) {
        document.getElementById('downloadAllBtn').style.display = 'inline-block';
    }
}

// Download single barcode
async function downloadSingleBarcode(patientNumber, patientName) {
    try {
        const response = await fetch('/api/download-barcode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patient_name: patientName,
                patient_number: patientNumber
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${patientNumber}_${patientName.replace(' ', '_')}.png`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showNotification(`Barcode ${patientName} berhasil diunduh!`, 'success');
        } else {
            showNotification('Gagal mengunduh barcode', 'danger');
        }
    } catch (error) {
        showNotification('Download error: ' + error.message, 'danger');
    }
}

// Download all barcodes
async function downloadAllBarcodes() {
    if (generatedBarcodes.length === 0) {
        showNotification('Tidak ada barcode untuk diunduh', 'warning');
        return;
    }

    showNotification(`Mengunduh ${generatedBarcodes.length} barcode...`, 'info');
    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < generatedBarcodes.length; i++) {
        const item = generatedBarcodes[i];

        // Handle both single form and batch form structures
        let patientNumber, patientName;
        if (item.data) {
            // Single form structure: {result, data}
            patientNumber = item.data.patient_number;
            patientName = item.data.patient_name;
        } else if (item.patient) {
            // Batch form structure: {result, patient}
            patientNumber = item.patient.patient_number;
            patientName = item.patient.patient_name;
        } else {
            console.error('Invalid barcode data structure:', item);
            errorCount++;
            continue;
        }

        try {
            await downloadSingleBarcode(patientNumber, patientName);
            successCount++;
        } catch (error) {
            console.error(`Failed to download barcode for ${patientName}:`, error);
            errorCount++;
        }

        // Small delay between downloads
        await sleep(500);
    }

    if (errorCount === 0) {
        showNotification(`Berhasil mengunduh ${successCount} barcode!`, 'success');
    } else {
        showNotification(`Selesai: ${successCount} berhasil, ${errorCount} gagal`, 'warning');
    }
}

// Clear results
function clearResults() {
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('results').innerHTML = '';
    document.getElementById('downloadAllBtn').style.display = 'none';
    generatedBarcodes = [];
}

// Validation
function validateForm(data) {
    if (!data.patient_name || data.patient_name.length < 2) {
        showNotification('Nama pasien minimal 2 karakter', 'danger');
        return false;
    }

    if (!data.patient_number || !/^\d{1,8}$/.test(data.patient_number)) {
        showNotification('Nomor pasien maksimal 8 digit angka', 'danger');
        return false;
    }

    return true;
}

// Status display (replaces modal)
function showStatus(message) {
    let statusEl = document.getElementById('statusMessage');
    if (!statusEl) {
        statusEl = document.createElement('div');
        statusEl.id = 'statusMessage';
        statusEl.className = 'alert alert-info position-fixed top-0 start-50 translate-middle-x mt-3';
        statusEl.style.zIndex = '9999';
        document.body.appendChild(statusEl);
    }

    statusEl.textContent = message;
    statusEl.style.display = 'block';
}

function hideStatus() {
    const statusEl = document.getElementById('statusMessage');
    if (statusEl) {
        statusEl.style.display = 'none';
    }
}

// Simple notifications (replaces complex toast system)
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '9999';

    const icons = {
        'success': '✓',
        'danger': '✗',
        'warning': '⚠',
        'info': 'ℹ'
    };

    notification.innerHTML = `
        <strong>${icons[type] || 'ℹ'}</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto dismiss
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, type === 'success' ? 3000 : 5000);
}

// Helper function
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Make functions globally accessible
window.downloadSingleBarcode = downloadSingleBarcode;
window.clearResults = clearResults;
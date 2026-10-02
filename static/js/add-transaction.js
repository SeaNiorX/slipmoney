const dropzoneArea = document.getElementById('dropzoneArea');
const slipFileInput = document.getElementById('slipFileInput');
const dropzonePrompt = document.getElementById('dropzonePrompt');
const ocrLoader = document.getElementById('ocrLoader');
const slipPreviewContainer = document.getElementById('slipPreviewContainer');
const slipPreviewImg = document.getElementById('slipPreviewImg');
const hiddenSlipFilename = document.getElementById('hiddenSlipFilename');
const hiddenRefNo = document.getElementById('hiddenRefNo');
const refNoGroup = document.getElementById('refNoGroup');
const refNoDisplay = document.getElementById('refNoDisplay');

const ocrNoticeSuccess = document.getElementById('ocrNoticeSuccess');
const ocrNoticePartial = document.getElementById('ocrNoticePartial');
const ocrNoticeFailed = document.getElementById('ocrNoticeFailed');
const ocrNoticeDuplicate = document.getElementById('ocrNoticeDuplicate');
const duplicateWarningText = document.getElementById('duplicateWarningText');

const amountInput = document.getElementById('amountInput');
const dateInput = document.getElementById('dateInput');
const timeInput = document.getElementById('timeInput');
const saveBtn = document.querySelector('.btn-save-action');

// Drag and drop event listeners
if (dropzoneArea) {
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzoneArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneArea.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzoneArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneArea.classList.remove('dragover');
        });
    });

    dropzoneArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            processUploadFile(files[0]);
        }
    });
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files && files.length > 0) {
        processUploadFile(files[0]);
    }
}

function hideAllBanners() {
    if (ocrNoticeSuccess) ocrNoticeSuccess.style.display = 'none';
    if (ocrNoticePartial) ocrNoticePartial.style.display = 'none';
    if (ocrNoticeFailed) ocrNoticeFailed.style.display = 'none';
    if (ocrNoticeDuplicate) ocrNoticeDuplicate.style.display = 'none';
    if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.classList.remove('disabled');
    }
}

function processUploadFile(file) {
    // Validate file type
    if (!file.type.match('image.*')) {
        alert('Please select an image file (JPG, JPEG, PNG)');
        return;
    }

    hideAllBanners();

    // Show scanner loader UI
    if (dropzonePrompt) dropzonePrompt.style.display = 'none';
    if (slipPreviewContainer) slipPreviewContainer.style.display = 'none';
    if (ocrLoader) ocrLoader.style.display = 'flex';

    // Prepare FormData for OCR API
    const formData = new FormData();
    formData.append('slip', file);

    fetch(window.ocrEndpointUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network error during OCR');
        }
        return response.json();
    })
    .then(data => {
        // Hide loader
        if (ocrLoader) ocrLoader.style.display = 'none';

        // Display slip preview
        if (data.file_url) {
            slipPreviewImg.src = data.file_url;
            slipPreviewContainer.style.display = 'block';
            hiddenSlipFilename.value = data.filename;
        }

        // Auto-fill extracted data
        let detected = [];

        if (data.amount) {
            amountInput.value = data.amount;
            highlightField(amountInput);
            detected.push((window.currencySymbol || '฿') + data.amount);
        }

        if (data.date) {
            dateInput.value = data.date;
            highlightField(dateInput);
            detected.push(data.date);
        }

        if (data.time) {
            timeInput.value = data.time;
            highlightField(timeInput);
            detected.push(data.time);
        }

        if (data.ref_no) {
            if (hiddenRefNo) hiddenRefNo.value = data.ref_no;
            if (refNoDisplay) refNoDisplay.value = data.ref_no;
            if (refNoGroup) refNoGroup.style.display = 'block';
            detected.push('Ref: ' + data.ref_no);
        } else {
            if (hiddenRefNo) hiddenRefNo.value = '';
            if (refNoDisplay) refNoDisplay.value = '';
            if (refNoGroup) refNoGroup.style.display = 'none';
        }

        // Show appropriate banner
        if (data.is_duplicate && data.duplicate_info) {
            // Duplicate slip detected!
            const dup = data.duplicate_info;
            if (ocrNoticeDuplicate && duplicateWarningText) {
                duplicateWarningText.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-danger"></i> สลิปนี้มีบันทึกในระบบแล้ว (ID: #${dup.id})<br>` +
                    `<i class="fa-regular fa-calendar"></i> <strong>${dup.date} ${dup.time}</strong> &nbsp;|&nbsp; ` +
                    `<i class="fa-solid fa-coins"></i> <strong>${window.currencySymbol || '฿'}${dup.amount}</strong><br>` +
                    `รหัสอ้างอิง: <strong style="font-family: monospace;">${dup.ref_no}</strong>`;
                ocrNoticeDuplicate.style.display = 'flex';
            }
            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.title = 'ไม่สามารถบันทึกสลิปซ้ำได้';
            }
        } else if (data.amount || data.date || data.time) {
            if (ocrNoticeSuccess) {
                ocrNoticeSuccess.style.display = 'flex';
                // If detected details exist, show them clearly
                if (detected.length > 0) {
                    const detailSpan = ocrNoticeSuccess.querySelector('span');
                    if (detailSpan) {
                        const originalText = detailSpan.getAttribute('data-original') || detailSpan.textContent;
                        detailSpan.setAttribute('data-original', originalText);
                        detailSpan.innerHTML = `${originalText}<br><small style="opacity: 0.9; font-weight: 600;"><i class="fa-solid fa-check"></i> สแกนพบ: ${detected.join(' | ')}</small>`;
                    }
                }
            }
        } else if (data.success) {
            // Text was found, but key values were unclear
            if (ocrNoticePartial) ocrNoticePartial.style.display = 'flex';
        } else {
            if (ocrNoticeFailed) ocrNoticeFailed.style.display = 'flex';
        }
    })
    .catch(err => {
        console.error('OCR Error:', err);
        if (ocrLoader) ocrLoader.style.display = 'none';
        if (dropzonePrompt) dropzonePrompt.style.display = 'flex';
        if (ocrNoticeFailed) ocrNoticeFailed.style.display = 'flex';
    });
}

function removeSlip() {
    hiddenSlipFilename.value = '';
    if (hiddenRefNo) hiddenRefNo.value = '';
    if (refNoDisplay) refNoDisplay.value = '';
    if (refNoGroup) refNoGroup.style.display = 'none';
    slipFileInput.value = '';
    slipPreviewImg.src = '';
    slipPreviewContainer.style.display = 'none';
    dropzonePrompt.style.display = 'flex';
    hideAllBanners();
}

function highlightField(el) {
    if (!el) return;
    el.classList.remove('field-highlight');
    // Force DOM reflow to retrigger animation
    void el.offsetWidth;
    el.classList.add('field-highlight');
}

function resetFormState() {
    removeSlip();
    hideAllBanners();
}

function handleTypeChange(type) {
    // If user changes to salary, can auto-select salary category
    const categorySelect = document.getElementById('categorySelect');
    if (categorySelect && type === 'income' && categorySelect.value === 'food') {
        categorySelect.value = 'salary';
    } else if (categorySelect && type === 'expense' && categorySelect.value === 'salary') {
        categorySelect.value = 'food';
    }
}

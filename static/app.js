// Trading Tools - JavaScript

// WebSocket connection
let ws = null;

// Tab ID to log ID mapping (main log)
const TAB_LOG_MAP = {
    'generate-signals': 'gs-log-main',
    'pnl-calculator': 'pnl-log',
    'printlvl': 'pl-log'
};

// Tab ID to FC log ID mapping (FeaturesCalculator log)
const TAB_FC_LOG_MAP = {
    'generate-signals': 'gs-log-fc'
};

// Initialize WebSocket
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
        console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        setTimeout(initWebSocket, 5000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    console.log('WebSocket message:', data);

    // Handle log messages (main log)
    if (data.type === 'log') {
        const tabId = data.tab_id || (document.querySelector('.tab.active')?.getAttribute('data-tab'));
        const logId = TAB_LOG_MAP[tabId];
        const logElement = logId ? document.getElementById(logId) : null;
        
        if (logElement) {
            const message = data.message;
            let messageClass = 'log-info';
            
            if (message.includes('❌') || message.includes('✗') || message.includes('Error') || message.includes('ERROR')) {
                messageClass = 'log-error';
            } else if (message.includes('⚠') || message.includes('Warning') || message.includes('WARNING')) {
                messageClass = 'log-warning';
            } else if (message.includes('✓') || message.includes('✔') || message.includes('Complete')) {
                messageClass = 'log-success';
            }
            
            logElement.innerHTML += `<span class="${messageClass}">${message}</span>\n`;
            logElement.scrollTop = logElement.scrollHeight;
        }
    }

    // Handle FeaturesCalculator log messages
    if (data.type === 'log_fc') {
        const tabId = data.tab_id || 'generate-signals';
        const logId = TAB_FC_LOG_MAP[tabId];
        const logElement = logId ? document.getElementById(logId) : null;
        
        if (logElement) {
            logElement.innerHTML += `<span class="log-info">${data.message}</span>\n`;
            logElement.scrollTop = logElement.scrollHeight;
        }
    }

    // Handle result messages
    if (data.type === 'result') {
        const tabId = data.tab_id;
        const result = data.result;

        if (tabId === 'pnl-calculator' && result.status === 'success' && result.results) {
            const tbody = document.getElementById('pnl-tbody');
            if (tbody) {
                tbody.innerHTML = '';
                result.results.forEach(row => {
                    const tr = document.createElement('tr');
                    const isTotal = row.date === 'ИТОГО';
                    if (isTotal) {
                        tr.style.fontWeight = 'bold';
                        tr.style.backgroundColor = '#1a5a1a';
                    }
                    tr.innerHTML = `
                        <td>${row.date}</td>
                        <td data-value="${row.combo}">${row.combo.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td data-value="${row.type1}">${row.type1.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td data-value="${row.type2}">${row.type2.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td data-value="${row.type3}">${row.type3.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td data-value="${row.type4}">${row.type4.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td data-value="${row.type5}">${row.type5.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td data-value="${row.type6}">${row.type6.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }

        if (tabId === 'printlvl' && result.status === 'success' && result.total_slides) {
            const savePdfButton = document.getElementById('pl-save-pdf');
            if (savePdfButton) {
                savePdfButton.disabled = false;
            }
        }
    }

    // Handle error messages
    if (data.type === 'error') {
        const tabId = data.tab_id || (document.querySelector('.tab.active')?.getAttribute('data-tab'));
        const logId = TAB_LOG_MAP[tabId];
        const logElement = logId ? document.getElementById(logId) : null;
        
        if (logElement) {
            logElement.innerHTML += `<span class="log-error">❌ Ошибка: ${data.message}</span>\n`;
            logElement.scrollTop = logElement.scrollHeight;
        }
    }
}

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const tabId = tab.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
    });
});

// Log tab switching
document.querySelectorAll('.log-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const logContainer = tab.closest('.log-container');
        logContainer.querySelectorAll('.log-tab').forEach(t => t.classList.remove('active'));
        logContainer.querySelectorAll('.log-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const logTabId = tab.getAttribute('data-log-tab');
        if (logTabId === 'main') {
            document.getElementById('gs-log-main').classList.add('active');
        } else if (logTabId === 'fc') {
            document.getElementById('gs-log-fc').classList.add('active');
        }
    });
});

// ==================== LocalStorage ====================

function saveToLocalStorage() {
    const elements = document.querySelectorAll('[data-save="true"]');
    const data = {};
    elements.forEach(el => {
        const id = el.id;
        if (el.type === 'checkbox') {
            data[id] = el.checked;
        } else if (el.tagName === 'SELECT') {
            data[id] = el.value;
        } else {
            data[id] = el.value;
        }
    });
    localStorage.setItem('trading-tools-forms', JSON.stringify(data));
}

function loadFromLocalStorage() {
    const saved = localStorage.getItem('trading-tools-forms');
    if (!saved) return;
    try {
        const data = JSON.parse(saved);
        Object.keys(data).forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            if (el.type === 'checkbox') {
                el.checked = data[id];
            } else if (el.tagName === 'SELECT') {
                el.value = data[id];
            } else {
                el.value = data[id];
            }
        });
    } catch (e) {
        console.error('Error loading from localStorage:', e);
    }
}

// ==================== Date Format Conversion ====================

function formatDate(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
}

function parseDate(dateStr) {
    const parts = dateStr.split('.');
    if (parts.length !== 3) return null;
    const day = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const year = parseInt(parts[2], 10);
    if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
    return new Date(year, month, day);
}

// ==================== Initialize Flatpickr ====================

function initFlatpickr() {
    const dateInputs = document.querySelectorAll('.date-input');
    dateInputs.forEach(input => {
        flatpickr(input, {
            locale: 'ru',
            dateFormat: 'd.m.Y',
            allowInput: true,
            clickOpens: true,
            disableMobile: true,
            onChange: function(selectedDates, dateStr, instance) {
                if (dateStr) {
                    input.value = dateStr;
                    saveToLocalStorage();
                }
            },
            onOpen: function(selectedDates, dateStr, instance) {
                const currentValue = input.value;
                if (currentValue) {
                    const date = parseDate(currentValue);
                    if (date) {
                        instance.setDate(date);
                    }
                }
            }
        });
    });
}

// ==================== Generate Signals ====================

document.getElementById('gs-run').addEventListener('click', async () => {
    const startDate = document.getElementById('gs-start-date').value;
    const endDate = document.getElementById('gs-end-date').value;
    const runFeatures = document.getElementById('gs-features').checked;
    const runRscript = document.getElementById('gs-rscript').checked;
    const runProcessing = document.getElementById('gs-processing').checked;
    const runCleanup = document.getElementById('gs-cleanup').checked;

    if (!startDate || !endDate) {
        alert('Пожалуйста, выберите даты');
        return;
    }

    const logMain = document.getElementById('gs-log-main');
    const logFc = document.getElementById('gs-log-fc');
    logMain.innerHTML = '🚀 Запуск генерации сигналов...\n';
    logFc.innerHTML = '';

    try {
        const response = await fetch('/api/generate-signals/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate,
                run_features_calculator: runFeatures,
                run_rscript: runRscript,
                run_signal_processing: runProcessing,
                run_cleanup: runCleanup,
                tab_id: 'generate-signals'
            })
        });

        const data = await response.json();

        if (data.status === 'started') {
            logMain.innerHTML += `✓ ${data.message}\n`;
            logMain.innerHTML += `📅 Период: ${startDate} - ${endDate}\n`;
        } else {
            logMain.innerHTML += `❌ Ошибка: ${data.message}\n`;
        }
    } catch (error) {
        logMain.innerHTML += `❌ Ошибка: ${error.message}\n`;
    }
});

// ==================== PnL Calculator ====================

document.getElementById('pnl-calculate').addEventListener('click', async () => {
    const startDate = document.getElementById('pnl-start-date').value;
    const endDate = document.getElementById('pnl-end-date').value;

    if (!startDate || !endDate) {
        alert('Пожалуйста, выберите даты');
        return;
    }

    const log = document.getElementById('pnl-log');
    const tbody = document.getElementById('pnl-tbody');
    log.innerHTML = '🔄 Расчёт PnL...\n';
    tbody.innerHTML = '';

    try {
        const response = await fetch('/api/pnl-calculator/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate,
                tab_id: 'pnl-calculator'
            })
        });

        const data = await response.json();

        if (data.status === 'started') {
            log.innerHTML += `✓ ${data.message}\n`;
            log.innerHTML += `📅 Период: ${startDate} - ${endDate}\n`;
        } else {
            log.innerHTML += `❌ Ошибка: ${data.message}\n`;
        }
    } catch (error) {
        log.innerHTML += `❌ Ошибка: ${error.message}\n`;
    }
});

// ==================== PrintLvl ====================

document.getElementById('pl-run').addEventListener('click', async () => {
    const ticker = document.getElementById('pl-ticker').value;
    const date = document.getElementById('pl-date').value;
    const time = document.getElementById('pl-time').value;
    const startOffset = document.getElementById('pl-start-offset').value;
    const endOffset = document.getElementById('pl-end-offset').value;

    if (!ticker || !date || !time) {
        alert('Пожалуйста, заполните все обязательные поля');
        return;
    }

    const log = document.getElementById('pl-log');
    const savePdfButton = document.getElementById('pl-save-pdf');
    log.innerHTML = '🚀 Запуск PrintLvl pipeline...\n';
    savePdfButton.disabled = true;

    try {
        const response = await fetch('/api/printlvl/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ticker: ticker,
                date: date,
                time: time,
                start_time_offset: startOffset,
                end_time_offset: endOffset,
                tab_id: 'printlvl'
            })
        });

        const data = await response.json();

        if (data.status === 'started') {
            log.innerHTML += `✓ ${data.message}\n`;
            log.innerHTML += `📊 Ticker: ${ticker}\n`;
            log.innerHTML += `📅 Дата: ${date}\n`;
            log.innerHTML += `⏰ Время: ${time}\n`;
        } else {
            log.innerHTML += `❌ Ошибка: ${data.message}\n`;
        }
    } catch (error) {
        log.innerHTML += `❌ Ошибка: ${error.message}\n`;
    }
});

document.getElementById('pl-save-pdf').addEventListener('click', async () => {
    const ticker = document.getElementById('pl-ticker').value;
    const date = document.getElementById('pl-date').value;

    if (!ticker || !date) {
        alert('Сначала запустите pipeline');
        return;
    }

    const defaultPath = `C:\\Users\\user\\Documents\\Cursor_coding\\trading-tools\\Plots\\${ticker}_${date}.pdf`;
    const outputPath = prompt('Введите путь для сохранения PDF:', defaultPath);

    if (!outputPath) return;

    const log = document.getElementById('pl-log');
    log.innerHTML += '\n💾 Сохранение PDF...\n';

    try {
        const response = await fetch('/api/printlvl/save-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ output_path: outputPath })
        });

        const data = await response.json();

        if (data.status === 'started') {
            log.innerHTML += `✓ ${data.message}\n`;
            log.innerHTML += `📁 Путь: ${outputPath}\n`;
        } else {
            log.innerHTML += `❌ Ошибка: ${data.message}\n`;
        }
    } catch (error) {
        log.innerHTML += `❌ Ошибка: ${error.message}\n`;
    }
});

// ==================== Initialize ====================

document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    loadFromLocalStorage();
    initFlatpickr();
    
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(today.getDate() - 7);

    if (!document.getElementById('gs-start-date').value) {
        document.getElementById('gs-start-date').value = formatDate(weekAgo);
    }
    if (!document.getElementById('gs-end-date').value) {
        document.getElementById('gs-end-date').value = formatDate(today);
    }

    if (!document.getElementById('pnl-start-date').value) {
        document.getElementById('pnl-start-date').value = formatDate(weekAgo);
    }
    if (!document.getElementById('pnl-end-date').value) {
        document.getElementById('pnl-end-date').value = formatDate(today);
    }

    if (!document.getElementById('pl-ticker').value) {
        document.getElementById('pl-ticker').value = 'MGNT_TQBR';
    }
    if (!document.getElementById('pl-date').value) {
        document.getElementById('pl-date').value = formatDate(today);
    }
    if (!document.getElementById('pl-time').value) {
        document.getElementById('pl-time').value = '22:59:51.000';
    }
    
    document.querySelectorAll('[data-save="true"]').forEach(el => {
        el.addEventListener('change', saveToLocalStorage);
        el.addEventListener('input', saveToLocalStorage);
    });
});

// ==================== PnL Calculator Updates ====================

document.querySelectorAll('.calendar-icon').forEach(icon => {
    icon.addEventListener('click', (e) => {
        const inputId = icon.getAttribute('data-for');
        const input = document.getElementById(inputId);
        if (input && input._flatpickr) {
            input._flatpickr.open();
        }
    });
    icon.style.cursor = 'pointer';
});

let isSelecting = false;
let startCell = null;
let selectedCells = [];

document.addEventListener('mousedown', (e) => {
    if (e.shiftKey) return;
    if (e.target.tagName === 'TD' && e.target.closest('#pnl-tbody')) {
        isSelecting = true;
        startCell = e.target;
        clearSelection();
        e.target.classList.add('selected');
        selectedCells = [e.target];
        e.preventDefault();
    }
});

document.addEventListener('mousemove', (e) => {
    if (isSelecting && e.target.tagName === 'TD' && e.target.closest('#pnl-tbody') && startCell) {
        clearSelection();
        selectRange(startCell, e.target);
    }
});

document.addEventListener('mouseup', () => {
    isSelecting = false;
});

document.addEventListener('click', (e) => {
    if (e.target.tagName === 'TD' && e.target.closest('#pnl-tbody')) {
        if (e.shiftKey && startCell) {
            e.preventDefault();
            clearSelection();
            selectColumn(startCell, e.target);
        } else {
            startCell = e.target;
        }
    }
});

function selectColumn(start, end) {
    const tbody = document.getElementById('pnl-tbody');
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const startRowIndex = rows.indexOf(start.parentElement);
    const endRowIndex = rows.indexOf(end.parentElement);
    const startColIndex = Array.from(start.parentElement.children).indexOf(start);
    const endColIndex = Array.from(end.parentElement.children).indexOf(end);
    const minRow = Math.min(startRowIndex, endRowIndex);
    const maxRow = Math.max(startRowIndex, endRowIndex);
    const minCol = Math.min(startColIndex, endColIndex);
    const maxCol = Math.max(startColIndex, endColIndex);
    for (let r = minRow; r <= maxRow; r++) {
        const cells = rows[r].children;
        for (let c = minCol; c <= maxCol; c++) {
            if (cells[c]) {
                cells[c].classList.add('selected');
                selectedCells.push(cells[c]);
            }
        }
    }
}

function clearSelection() {
    document.querySelectorAll('#pnl-table td.selected, #pnl-table td.selecting, #pnl-tbody td.selected').forEach(cell => {
        cell.classList.remove('selected', 'selecting');
    });
    selectedCells = [];
}

function selectRange(start, end) {
    const tbody = document.getElementById('pnl-tbody');
    if (!tbody) return;
    const startRow = start.parentElement;
    const endRow = end.parentElement;
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const startRowIndex = rows.indexOf(startRow);
    const endRowIndex = rows.indexOf(endRow);
    const startColIndex = Array.from(startRow.children).indexOf(start);
    const endColIndex = Array.from(endRow.children).indexOf(end);
    const minRow = Math.min(startRowIndex, endRowIndex);
    const maxRow = Math.max(startRowIndex, endRowIndex);
    const minCol = Math.min(startColIndex, endColIndex);
    const maxCol = Math.max(startColIndex, endColIndex);
    for (let r = minRow; r <= maxRow; r++) {
        const cells = rows[r].children;
        for (let c = minCol; c <= maxCol; c++) {
            cells[c].classList.add('selected');
            selectedCells.push(cells[c]);
        }
    }
}

document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'c' && selectedCells.length > 0) {
        copySelectedCells();
        e.preventDefault();
    }
});

function copySelectedCells() {
    if (selectedCells.length === 0) return;
    const tbody = document.getElementById('pnl-tbody');
    if (!tbody) return;
    const rows = {};
    selectedCells.forEach(cell => {
        const rowIndex = Array.from(tbody.querySelectorAll('tr')).indexOf(cell.parentElement);
        const colIndex = Array.from(cell.parentElement.children).indexOf(cell);
        if (!rows[rowIndex]) rows[rowIndex] = {};
        rows[rowIndex][colIndex] = cell.dataset.value || cell.textContent;
    });
    const sortedRows = Object.keys(rows).sort((a, b) => a - b);
    const lines = sortedRows.map(rowIndex => {
        const row = rows[rowIndex];
        const sortedCols = Object.keys(row).sort((a, b) => a - b);
        return sortedCols.map(colIndex => row[colIndex]).join("\t");
    }).join("\n");
    const textarea = document.createElement('textarea');
    textarea.value = lines;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    const n = document.createElement('div');
    n.textContent = 'Copied ' + selectedCells.length + ' cells';
    n.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#1a5a1a;color:white;padding:10px 20px;border-radius:5px;z-index:10000';
    document.body.appendChild(n);
    setTimeout(() => n.remove(), 2000);
}

document.addEventListener('contextmenu', (e) => {
    if (e.target.tagName === 'TD' && e.target.closest('#pnl-tbody') && selectedCells.length > 0) {
        e.preventDefault();
        copySelectedCells();
    }
});

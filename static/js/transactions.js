// static/js/transactions.js - Transactions Table interactions

let currentDetailTx = null;

function openDetailModal(tx) {
    currentDetailTx = tx;
    const modal = document.getElementById('detailModal');
    if (!modal) return;

    // Type
    const typeElem = document.getElementById('detailType');
    if (typeElem) {
        if (tx.type === 'income') {
            typeElem.innerHTML = `<span class="badge badge-income">${window.langIncomeText || 'Income'}</span>`;
        } else {
            typeElem.innerHTML = `<span class="badge badge-expense">${window.langExpenseText || 'Expense'}</span>`;
        }
    }

    // Amount
    const amountElem = document.getElementById('detailAmount');
    if (amountElem) {
        const sign = tx.type === 'income' ? '+' : '-';
        const colorClass = tx.type === 'income' ? 'text-success' : 'text-danger';
        amountElem.className = `detail-value font-bold ${colorClass}`;
        amountElem.textContent = `${sign}${window.currencySymbol || '฿'}${Number(tx.amount).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }

    // Date & Time
    const dateElem = document.getElementById('detailDate');
    if (dateElem) dateElem.textContent = tx.date;

    const timeElem = document.getElementById('detailTime');
    if (timeElem) timeElem.textContent = tx.time;

    // Category
    const categoryElem = document.getElementById('detailCategory');
    if (categoryElem) {
        const translatedCat = (window.categoryNamesMap && window.categoryNamesMap[tx.category]) || tx.category;
        categoryElem.textContent = translatedCat;
    }

    // Description
    const descElem = document.getElementById('detailDescription');
    if (descElem) descElem.textContent = tx.description || '-';

    // Slip Image
    const slipWrapper = document.getElementById('detailSlipWrapper');
    const slipImg = document.getElementById('detailSlipImg');
    if (slipWrapper && slipImg) {
        if (tx.slip_filename) {
            slipImg.src = `/uploads/${tx.slip_filename}`;
            slipWrapper.style.display = 'block';
        } else {
            slipWrapper.style.display = 'none';
        }
    }

    modal.classList.add('open');
}

function closeDetailModal(event) {
    if (event && event.target && event.target.id !== 'detailModal' && !event.target.classList.contains('btn-close-modal') && !event.target.classList.contains('btn-secondary')) {
        return;
    }
    const modal = document.getElementById('detailModal');
    if (modal) {
        modal.classList.remove('open');
    }
}

function viewSlipFromDetail() {
    if (currentDetailTx && currentDetailTx.slip_filename) {
        closeDetailModal();
        openSlipModal(`/uploads/${currentDetailTx.slip_filename}`);
    }
}

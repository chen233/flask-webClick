let modal;
let currentEditingId = null;

document.addEventListener('DOMContentLoaded', () => {
    modal = new bootstrap.Modal(document.getElementById('dataModal'));
    bindEvents();
    loadCentres();
});

function bindEvents() {
    document.getElementById('addBtn').addEventListener('click', openAddModal);
    document.getElementById('saveBtn').addEventListener('click', saveData);
    document.getElementById('region').addEventListener('change', loadCentres);
    document.getElementById('dataTableBody').addEventListener('click', handleTableAction);
}

function openAddModal() {
    currentEditingId = null;
    document.getElementById('modalTitle').textContent = 'Add New Record（新增记录）';
    document.getElementById('dataForm').reset();
    modal.show();
}

function loadCentres() {
    const region = document.getElementById('region').value;
    axios.get('/api/region_centres', { params: { region } })
        .then(response => {
            const centreSelect = document.getElementById('centre');
            centreSelect.innerHTML = '';
            response.data.forEach(centre => {
                const option = document.createElement('option');
                option.value = centre;
                option.textContent = centre;
                centreSelect.appendChild(option);
            });
        });
}

function handleTableAction(e) {
    const licenceNumber = e.target.getAttribute('data-id');
    if (!licenceNumber) return;

    if (e.target.classList.contains('edit-btn')) {
        currentEditingId = licenceNumber;
        axios.get('/api/data', { params: { licence_number: licenceNumber } })
            .then(response => {
                if (response.data.status === 'success') {
                    fillFormData(response.data.data);
                    document.getElementById('modalTitle').textContent = 'Edit Record（编辑记录）';
                    modal.show();
                }
            });
    } else if (e.target.classList.contains('delete-btn')) {
        if (confirm('Are you sure you want to delete this record?（确认删除该记录吗？）')) {
            axios.delete('/api/data', { params: { licence_number: licenceNumber } })
                .then(() => {
                    const row = document.querySelector(`tr[data-id="${licenceNumber}"]`);
                    if (row) row.remove();
                });
        }
    }
}

function fillFormData(data) {
    document.getElementById('licence_number').value = data.licence_number;
    document.getElementById('contact_name').value = data.contact_name;
    document.getElementById('contact_phone').value = data.contact_phone;
    document.getElementById('test_type').value = data.test_type;
    document.getElementById('region').value = data.region;
    document.getElementById('centre').value = data.centre;
    document.getElementById('card_number').value = data.card_number;
    document.getElementById('expiry_month').value = data.expiry_month;
    document.getElementById('expiry_yy').value = data.expiry_yy;
    document.getElementById('cvv').value = data.cvv;
    document.getElementById('email').value = data.email;

    if (data.booking_time) {
        const [startPart, endPart] = data.booking_time.split(' - ');
        const [startDate, startTime] = startPart.split(' ');
        const [endDate, endTime] = endPart.split(' ');
        document.getElementById('start_date').value = startDate;
        document.getElementById('start_time').value = startTime;
        document.getElementById('end_date').value = endDate;
        document.getElementById('end_time').value = endTime;
    }
}

function saveData() {
    const formData = {
        licence_number: document.getElementById('licence_number').value,
        contact_name: document.getElementById('contact_name').value,
        contact_phone: document.getElementById('contact_phone').value,
        test_type: document.getElementById('test_type').value,
        region: document.getElementById('region').value,
        centre: document.getElementById('centre').value,
        booking_time: `${document.getElementById('start_date').value} ${document.getElementById('start_time').value} - ${document.getElementById('end_date').value} ${document.getElementById('end_time').value}`,
        card_number: document.getElementById('card_number').value,
        expiry_month: document.getElementById('expiry_month').value,
        expiry_yy: document.getElementById('expiry_yy').value,
        cvv: document.getElementById('cvv').value,
        email: document.getElementById('email').value
    };

    if (currentEditingId) {
        axios.put('/api/data', formData)
            .then(() => {
                const row = document.querySelector(`tr[data-id="${currentEditingId}"]`);
                if (row) {
                    row.innerHTML = `
                        <td>${formData.licence_number}</td>
                        <td>${formData.contact_name}</td>
                        <td>${formData.contact_phone}</td>
                        <td>${formData.test_type}</td>
                        <td>${formData.region}</td>
                        <td>${formData.centre}</td>
                        <td>${formData.booking_time}</td>
                        <td>
                            <button class="btn btn-sm edit-btn" data-id="${formData.licence_number}">Edit（编辑）</button>
                            <button class="btn btn-sm delete-btn" data-id="${formData.licence_number}">Delete（删除）</button>
                        </td>
                    `;
                    row.setAttribute('data-id', formData.licence_number);
                }
                modal.hide();
            });
    } else {
        axios.post('/api/data', formData)
            .then(() => {
                const tbody = document.getElementById('dataTableBody');
                tbody.innerHTML += `
                    <tr data-id="${formData.licence_number}">
                        <td>${formData.licence_number}</td>
                        <td>${formData.contact_name}</td>
                        <td>${formData.contact_phone}</td>
                        <td>${formData.test_type}</td>
                        <td>${formData.region}</td>
                        <td>${formData.centre}</td>
                        <td>${formData.booking_time}</td>
                        <td>
                            <button class="btn btn-sm edit-btn" data-id="${formData.licence_number}">Edit（编辑）</button>
                            <button class="btn btn-sm delete-btn" data-id="${formData.licence_number}">Delete（删除）</button>
                        </td>
                    </tr>
                `;
                modal.hide();
            });
    }
}
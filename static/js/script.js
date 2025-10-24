let modal;
let currentEditingId = null; // 统一使用currentEditingId变量

document.addEventListener('DOMContentLoaded', () => {
    modal = new bootstrap.Modal(document.getElementById('dataModal'));
    const initialData = JSON.parse(document.getElementById('initialData').textContent);
    bindEvents();
    loadCentres(); // 页面加载时加载考试中心
});

function bindEvents() {
    document.getElementById('addBtn').addEventListener('click', openAddModal);
    document.getElementById('region').addEventListener('change', loadCentres);
    document.getElementById('dataTableBody').addEventListener('click', handleTableAction);
}
// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化考试类型下拉框
    initTestTypes();

    // 初始化区域下拉框
    initRegions();

    // 绑定区域选择变化事件
    document.getElementById('region').addEventListener('change', loadCentres);

    // 绑定添加按钮事件
    document.getElementById('addBtn').addEventListener('click', openAddModal);


    // 绑定删除按钮事件
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const licenceNumber = this.getAttribute('data-id');
            if (confirm('确定要删除这条记录吗？')) {
                deleteRecord(licenceNumber);
            }
        });
    });
});

// 初始化考试类型下拉框
function initTestTypes() {
    const testTypeSelect = document.getElementById('test_type');
    // 从后端获取考试类型数据
    axios.get('/')
        .then(response => {
            // 实际项目中应该有专门的API获取考试类型
            // 这里假设我们可以从全局变量获取
            window.testTypes.forEach(type => {
                const option = document.createElement('option');
                option.value = type.value;
                option.textContent = type.label;
                testTypeSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('加载考试类型失败:', error);
        });
}

// 初始化区域下拉框
function initRegions() {
    const regionSelect = document.getElementById('region');
    // 从后端获取区域数据
    axios.get('/api/region_centres')
        .then(response => {
            // 获取所有区域
            const regions = Object.keys(window.regionCentreMap);
            regions.forEach(region => {
                const option = document.createElement('option');
                option.value = region;
                option.textContent = region;
                regionSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('加载区域失败:', error);
        });
}

// 根据选择的区域加载考试中心
// 保留唯一的loadCentres函数并返回Promise
function loadCentres() {
    return new Promise((resolve, reject) => {
        const region = document.getElementById('region').value;
        const centreSelect = document.getElementById('centre');

        centreSelect.innerHTML = '<option value="">加载中...</option>';
        centreSelect.disabled = true;

        if (!region) {
            centreSelect.innerHTML = '<option value="">请先选择区域...</option>';
            resolve();
            return;
        }

        axios.get('/api/region_centres', { params: { region } })
            .then(response => {
                centreSelect.innerHTML = '';
                const emptyOption = document.createElement('option');
                emptyOption.value = '';
                emptyOption.textContent = '请选择考试中心';
                centreSelect.appendChild(emptyOption);

                response.data.forEach(centre => {
                    const option = document.createElement('option');
                    option.value = centre;
                    option.textContent = centre;
                    centreSelect.appendChild(option);
                });

                centreSelect.disabled = false;
                resolve(); // 加载完成后resolve
            })
            .catch(error => {
                console.error('加载考试中心失败：', error);
                centreSelect.innerHTML = '<option value="">加载失败，请重试</option>';
                reject(error);
            });
    });
}



// 打开编辑记录的模态框
function openEditModal(licenceNumber) {
    axios.get(`/api/data?licence_number=${encodeURIComponent(licenceNumber)}`)
        .then(response => {
            if (response.data.status === 'success') {
                const data = response.data.data;
                // 填充表单基础数据
                document.getElementById('licence_number').value = data.licence_number;
                document.getElementById('contact_name').value = data.contact_name;
                document.getElementById('contact_phone').value = data.contact_phone;
                document.getElementById('test_type').value = data.test_type;

                // 关键修复：先设置区域，再加载中心并选中
                const regionSelect = document.getElementById('region');
                regionSelect.value = data.region;

                // 等待loadCentres完成后再设置考试中心
                loadCentres().then(() => {
                    document.getElementById('centre').value = data.centre;
                });

                // 处理日期时间（移至fillFormData统一处理）
                fillFormData(data);

                document.getElementById('modalTitle').textContent = 'Edit Record（编辑记录）';
                new bootstrap.Modal(document.getElementById('dataModal')).show();
            }
        })
        .catch(error => {
            console.error('获取记录数据失败:', error);
            alert('加载记录失败，请重试');
        });
}
// 保存数据（新增或编辑）
function saveData() {
    // 表单验证
    const form = document.getElementById('dataForm');
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }

    // 收集表单数据
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

    // 判断是新增还是编辑
    const isEdit = document.getElementById('modalTitle').textContent.includes('Edit');

    // 发送请求
    const promise = isEdit
        ? axios.put('/api/data', formData)
        : axios.post('/api/data', formData);

    promise.then(response => {
        if (response.data.status === 'success') {
            // 关闭模态框
            bootstrap.Modal.getInstance(document.getElementById('dataModal')).hide();
            // 刷新页面
            location.reload();
        }
    }).catch(error => {
        console.error('保存数据失败:', error);
        alert('保存失败: ' + (error.response?.data?.message || '未知错误'));
    });
}

// 删除记录
function deleteRecord(licenceNumber) {
    axios.delete(`/api/data?licence_number=${encodeURIComponent(licenceNumber)}`)
        .then(response => {
            if (response.data.status === 'success') {
                // 从表格中移除该行
                document.querySelector(`tr[data-id="${licenceNumber}"]`).remove();
            }
        })
        .catch(error => {
            console.error('删除记录失败:', error);
            alert('删除失败，请重试');
        });
}

// 从HTML中获取初始数据
function loadInitialData() {
    const initialData = document.getElementById('initialData');
    if (initialData) {
        try {
            return JSON.parse(initialData.textContent);
        } catch (e) {
            console.error('解析初始数据失败:', e);
            return [];
        }
    }
    return [];
}
// 打开添加记录的模态框
function openAddModal() {
    document.getElementById('modalTitle').textContent = 'Add New Record（新增记录）';
    document.getElementById('dataForm').reset();
    // 显示模态框
    new bootstrap.Modal(document.getElementById('dataModal')).show();
}
// 删除原 openEditModal 函数，保留 editData 函数并完善：
function editData(licenceNumber) {
    const form = document.getElementById('dataForm');
    form.classList.remove('was-validated');
    currentEditingId = licenceNumber; // 关键：设置编辑ID
    axios.get('/api/data', { params: { licence_number: licenceNumber } })
        .then(response => {
            const data = response.data.data;
            fillFormData(data);
            document.getElementById('modalTitle').textContent = 'Edit Record（编辑记录）';
            // 使用全局 modal 实例显示，避免重复创建
            modal.show();
        })
        .catch(error => {
            console.error('获取编辑数据失败：', error);
            alert('加载数据失败，请重试');
        });
    modal.show(); // 这里的modal是全局初始化的bootstrap.Modal实例

}

// 表格操作处理函数（修复缺失问题）
function handleTableAction(e) {
    const target = e.target;
    const row = target.closest('tr'); // 找到点击所在的行
    if (!row) return; // 不是行内元素则退出
    const licenceNumber = row.dataset.id; // 从行的data-id获取编号

    // 编辑按钮点击
    if (target.classList.contains('edit-btn')) {
        editData(licenceNumber);
    }
    // 删除按钮点击
    else if (target.classList.contains('delete-btn')) {
        if (confirm('Are you sure you want to delete this record?（确认删除该记录吗？）')) {
            axios.delete('/api/data', { params: { licence_number: licenceNumber } })
                .then(() => {
                    row.remove(); // 从表格中移除该行
                    alert('删除成功');
                })
                .catch(error => {
                    console.error('删除失败：', error);
                    alert('删除失败，请重试');
                });
        }
    }
}

// 填充表单数据
function fillFormData(data) {
    const currentCentre = data.centre || '';
    document.getElementById('licence_number').value = data.licence_number || '';
    document.getElementById('contact_name').value = data.contact_name || '';
    document.getElementById('contact_phone').value = data.contact_phone || '';
    document.getElementById('test_type').value = data.test_type || '';
    document.getElementById('region').value = data.region || '';
    loadCentres().then(() => {
        document.getElementById('centre').value = data.centre || '';
            });
    document.getElementById('centre').value = data.centre || '';
    document.getElementById('card_number').value = data.card_number || '';
    document.getElementById('expiry_month').value = data.expiry_month || '';
    document.getElementById('expiry_yy').value = data.expiry_yy || '';
    document.getElementById('cvv').value = data.cvv || '';
    document.getElementById('email').value = data.email || '';

    // 处理预约时间
    if (data.booking_time) {
        // 正确拆分格式："2024-05-01至2024-05-05 09:00-17:00"
        const [datePart, timePart] = data.booking_time.split(' '); // 按空格拆分日期和时间部分

        if (datePart && timePart) {
            // 拆分日期范围（例如：2024-05-01至2024-05-05）
            const [startDate, endDate] = datePart.split('至');
            // 拆分时间范围（例如：09:00-17:00）
            const [startTime, endTime] = timePart.split('-');

            // 填充到表单
            document.getElementById('start_date').value = startDate || '';
            document.getElementById('end_date').value = endDate || '';
            document.getElementById('start_time').value = startTime || '';
            document.getElementById('end_time').value = endTime || '';
        } else {
            console.warn('预约时间格式不正确:', data.booking_time);
        }
    }
}

// 模态框关闭事件
document.getElementById('dataModal').addEventListener('hidden.bs.modal', function() {
    const form = document.getElementById('dataForm');
    form.reset();
    form.classList.remove('was-validated');
    currentEditingId = null; // 重置编辑ID
});

// 保存数据（新增/更新）
function saveData() {
    const form = document.getElementById('dataForm');
    const licenceNumber = document.getElementById('licence_number').value;

    // 表单验证
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        const firstInvalid = form.querySelector(':invalid');
        firstInvalid?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
    }

    // 构建预约时间（保持不变）
    const startDate = document.getElementById('start_date').value;
    const startTime = document.getElementById('start_time').value;
    const endDate = document.getElementById('end_date').value;
    const endTime = document.getElementById('end_time').value;
    const dateRange = `${startDate}至${endDate}`;
    const dailyTimeRange = `${startTime}-${endTime}`;
    const bookingTime = `${dateRange} ${dailyTimeRange}`;

    // 构建表单数据
    const formData = {
        licence_number: licenceNumber,
        contact_name: document.getElementById('contact_name').value,
        contact_phone: document.getElementById('contact_phone').value,
        test_type: document.getElementById('test_type').value,
        region: document.getElementById('region').value,
        centre: document.getElementById('centre').value,
        booking_time: bookingTime,
        card_number: document.getElementById('card_number').value,
        expiry_month: document.getElementById('expiry_month').value,
        expiry_yy: document.getElementById('expiry_yy').value,
        cvv: document.getElementById('cvv').value,
        email: document.getElementById('email').value
    };

    // 提交数据：严格根据 currentEditingId 判断操作类型
    let promise;
    if (currentEditingId) {
        // 编辑：使用 PUT 请求
        promise = axios.put('/api/data', formData);
    } else {
        // 新增：使用 POST 请求
        promise = axios.post('/api/data', formData);
    }

    promise.then(response => {
        alert(currentEditingId ? '更新成功！' : '新增成功！');
        location.reload();
    }).catch(error => {
        // 优化错误提示，显示具体原因
        const errorMsg = error.response
            ? error.response.data.message || `状态码：${error.response.status}`
            : '网络错误或服务器无响应';
        alert(`${currentEditingId ? '更新' : '新增'}失败：${errorMsg}`);
    });

    modal.hide();
}
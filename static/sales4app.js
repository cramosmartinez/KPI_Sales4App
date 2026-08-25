// Configuración base
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";

const API_BASE = '/api/sales4app';
let charts = {};

// Instancias de Chart.js
const initCharts = () => {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { labels: { color: '#f8fafc' } }
        },
        scales: {
            x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } },
            y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } }
        }
    };

    // 1. Tendencia
    const ctxTendencia = document.getElementById('chart-tendencia').getContext('2d');
    charts.tendencia = new Chart(ctxTendencia, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            ...commonOptions,
            interaction: { mode: 'index', intersect: false },
        }
    });

    // 2. Grupos
    const ctxGrupos = document.getElementById('chart-grupos').getContext('2d');
    charts.grupos = new Chart(ctxGrupos, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: {
            ...commonOptions,
            indexAxis: 'y', // Horizontal bar
        }
    });

    // 3. Empresas (Donut)
    const ctxEmpresas = document.getElementById('chart-empresas').getContext('2d');
    charts.empresas = new Chart(ctxEmpresas, {
        type: 'doughnut',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { color: '#f8fafc' } }
            }
        }
    });

    // 4. Estatus
    const ctxEstatus = document.getElementById('chart-estatus').getContext('2d');
    charts.estatus = new Chart(ctxEstatus, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: {
            ...commonOptions
        }
    });
};

const getFilterParams = () => {
    const getMultiVals = (id) => {
        const checkboxes = document.querySelectorAll(`.chk-${id}:checked`);
        const vals = Array.from(checkboxes).map(chk => chk.value).filter(v => v !== "");
        return vals.join(',');
    };
    
    const params = new URLSearchParams({
        anio: getMultiVals('anio'),
        mes: getMultiVals('mes'),
        empresa: getMultiVals('empresa'),
        grupo: getMultiVals('grupo')
    });
    return params.toString();
};

const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
};

const loadKPIs = async (queryStr) => {
    try {
        const res = await fetch(`${API_BASE}/kpis?${queryStr}`);
        if (!res.ok) throw new Error('Error al cargar KPIs');
        const data = await res.json();
        
        document.getElementById('kpi-app-orders').innerText = data.app_orders;
        document.getElementById('kpi-total-orders').innerText = `de ${data.total_orders} órdenes totales`;
        
        document.getElementById('kpi-adoption-rate').innerText = `${data.adoption_rate}%`;
        
        document.getElementById('kpi-total-amount').innerText = formatCurrency(data.total_amount_app);
        
        document.getElementById('kpi-active-sellers').innerText = data.active_sellers;
    } catch (e) {
        console.error(e);
    }
};

const updateChartsData = async (queryStr) => {
    try {
        const res = await fetch(`${API_BASE}/graficos?${queryStr}`);
        if (!res.ok) throw new Error('Error al cargar gráficos');
        const data = await res.json();
        
        // Update Tendencia
        charts.tendencia.data.labels = data.tendencia.labels;
        charts.tendencia.data.datasets = [
            {
                label: 'Dynamics Tradicional',
                data: data.tendencia.tradicional,
                borderColor: '#94a3b8',
                tension: 0.4
            },
            {
                label: 'Sales4App',
                data: data.tendencia.app,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                fill: true,
                tension: 0.4
            }
        ];
        charts.tendencia.update();

        // Update Grupos
        charts.grupos.data.labels = data.grupos.labels;
        charts.grupos.data.datasets = [{
            label: '% Adopción',
            data: data.grupos.adopcion,
            backgroundColor: '#8b5cf6'
        }];
        charts.grupos.update();

        // Update Empresas
        charts.empresas.data.labels = data.empresas.labels;
        charts.empresas.data.datasets = [{
            data: data.empresas.data,
            backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']
        }];
        charts.empresas.update();

        // Update Estatus
        charts.estatus.data.labels = data.estatus.labels;
        charts.estatus.data.datasets = [{
            label: 'OVs',
            data: data.estatus.data,
            backgroundColor: '#10b981'
        }];
        charts.estatus.update();
        
    } catch (e) {
        console.error(e);
    }
};

const loadVendedores = async (queryStr) => {
    try {
        const res = await fetch(`${API_BASE}/vendedores?${queryStr}`);
        if (!res.ok) throw new Error('Error al cargar tabla');
        const data = await res.json();
        
        const tbody = document.getElementById('vendedores-tbody');
        tbody.innerHTML = '';
        
        window.allVendedores = data; // Guardar para el buscador cliente
        renderTable(data);
    } catch (e) {
        console.error(e);
    }
};

const renderTable = (data) => {
    const tbody = document.getElementById('vendedores-tbody');
    tbody.innerHTML = '';
    
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;">No hay datos para esta selección</td></tr>';
        return;
    }
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        
        // Estilo especial para adopciones altas
        let badgeClass = 'badge-low';
        if (row.adopcion >= 80) badgeClass = 'badge-high';
        else if (row.adopcion >= 50) badgeClass = 'badge-medium';
        
        tr.innerHTML = `
            <td style="font-weight: 600;">${row.vendedor}</td>
            <td>${row.secretario}</td>
            <td>${row.ovs_app}</td>
            <td>${row.ovs_tradicional}</td>
            <td><span class="badge ${badgeClass}">${row.adopcion}%</span></td>
            <td>${row.lineas_promedio}</td>
            <td>${formatCurrency(row.ticket_promedio)}</td>
            <td style="color: var(--success); font-weight: 600;">${formatCurrency(row.monto_app)}</td>
            <td style="color: var(--danger); font-weight: 600;">${formatCurrency(row.monto_tradicional)}</td>
            <td style="font-weight: bold;">${formatCurrency(row.monto_app + row.monto_tradicional)}</td>
        `;
        tbody.appendChild(tr);
    });
};

const handleSearch = (e) => {
    const term = e.target.value.toLowerCase();
    if (!window.allVendedores) return;
    
    const filtered = window.allVendedores.filter(item => 
        (item.vendedor && item.vendedor.toLowerCase().includes(term)) ||
        (item.secretario && item.secretario.toLowerCase().includes(term))
    );
    renderTable(filtered);
};

const refreshDashboard = () => {
    const queryStr = getFilterParams();
    loadKPIs(queryStr);
    updateChartsData(queryStr);
    loadVendedores(queryStr);
};

const exportData = () => {
    const queryStr = getFilterParams();
    window.location.href = `${API_BASE}/export?${queryStr}`;
};

const loadEmpresasFilters = async () => {
    try {
        const res = await fetch(`${API_BASE}/empresas`);
        if (!res.ok) throw new Error('Error al cargar empresas');
        const data = await res.json();
        
        const dropdown = document.getElementById('dropdown-empresa');
        
        // Guardar seleccionados actuales
        const currentChecked = Array.from(document.querySelectorAll('.chk-empresa:checked')).map(c => c.value);
        
        dropdown.innerHTML = '';
        
        data.forEach(empresa => {
            const label = document.createElement('label');
            const checkedAttr = currentChecked.includes(empresa) ? 'checked' : '';
            label.innerHTML = `<input type="checkbox" value="${empresa}" class="chk-empresa" ${checkedAttr}> ${empresa.toUpperCase()}`;
            dropdown.appendChild(label);
        });
        
        setupCheckboxListeners('empresa', 'Todas las empresas');
    } catch (e) {
        console.error(e);
    }
};

// Dropdown Logic
const toggleDropdown = (id) => {
    document.getElementById(`dropdown-${id}`).classList.toggle('show');
};

const setupCheckboxListeners = (id, defaultText) => {
    const checkboxes = document.querySelectorAll(`.chk-${id}`);
    const textSpan = document.getElementById(`text-${id}`);
    
    const updateText = () => {
        const checked = document.querySelectorAll(`.chk-${id}:checked`);
        if (checked.length === 0) {
            textSpan.textContent = defaultText;
        } else if (checked.length === 1) {
            textSpan.textContent = checked[0].parentNode.textContent.trim();
        } else {
            textSpan.textContent = `${checked.length} seleccionados`;
        }
        // No llamamos refreshDashboard() aquí para esperar al botón Aplicar
    };
    
    checkboxes.forEach(chk => {
        chk.removeEventListener('change', updateText); // avoid duplicates
        chk.addEventListener('change', updateText);
    });
};

window.onclick = function(event) {
    if (!event.target.closest('.custom-select')) {
        const dropdowns = document.getElementsByClassName("dropdown-content");
        for (let i = 0; i < dropdowns.length; i++) {
            if (dropdowns[i].classList.contains('show')) {
                dropdowns[i].classList.remove('show');
            }
        }
    }
}

const syncCache = async () => {
    const btn = document.getElementById('btn-sync');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sincronizando...';
    btn.disabled = true;
    
    try {
        const res = await fetch(`${API_BASE}/sync_now`, { method: 'POST' });
        if (!res.ok) throw new Error('Falló sincronización');
        
        // Refrescar datos y filtros
        refreshDashboard();
        loadEmpresasFilters();
        alert('Caché sincronizada exitosamente desde Dynamics.');
    } catch (e) {
        console.error(e);
        alert('Hubo un error al sincronizar. Por favor, revisa los logs del servidor.');
    } finally {
        btn.innerHTML = '<i class="fa-solid fa-rotate"></i> Sincronizar Caché';
        btn.disabled = false;
    }
};

// Listeners
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    loadEmpresasFilters();
    
    setupCheckboxListeners('anio', 'Todos los años');
    setupCheckboxListeners('mes', 'Todos los meses');
    setupCheckboxListeners('grupo', 'Todos los grupos');
    
    refreshDashboard();
    
    // Asignar listener al botón Aplicar Filtros
    document.getElementById('btn-aplicar').addEventListener('click', refreshDashboard);
    
    // Buscador
    document.getElementById('table-search').addEventListener('input', handleSearch);
    
    // Acciones
    document.getElementById('btn-sync').addEventListener('click', syncCache);
    document.getElementById('btn-export').addEventListener('click', exportData);
});

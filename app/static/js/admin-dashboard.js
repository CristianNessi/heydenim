/* ── Heydemin Admin Dashboard ── */

let chartDaily = null;
let chartClicks = null;

const COLORS = ['#3b82f6','#10b981','#8b5cf6','#f59e0b','#06b6d4','#ef4444','#ec4899','#84cc16'];

function fmt(n) {
  return Number(n).toLocaleString('es-ES');
}

async function loadMetrics() {
  document.getElementById('last-updated').textContent = 'Actualizando…';

  let data;
  try {
    const res = await fetch('/analytics/metrics');
    if (!res.ok) throw new Error('unauthorized');
    data = await res.json();
  } catch {
    document.getElementById('last-updated').textContent = 'Error al cargar métricas';
    return;
  }

  const { totals, daily_views, top_products, click_elements, referrers, top_pages, heatmap } = data;

  // ── KPIs ──────────────────────────────────────────────────────
  document.getElementById('kpi-total').textContent   = fmt(totals.total_views);
  document.getElementById('kpi-today').textContent   = fmt(totals.views_today);
  document.getElementById('kpi-unique').textContent  = fmt(totals.unique_today);
  document.getElementById('kpi-clicks').textContent  = fmt(totals.total_clicks);
  document.getElementById('kpi-7d').textContent      = fmt(totals.views_7d);

  const now = new Date().toLocaleString('es-ES', { dateStyle: 'medium', timeStyle: 'short' });
  document.getElementById('last-updated').textContent = `Última actualización: ${now}`;

  // ── Gráfico: visitas diarias ───────────────────────────────────
  const labels = daily_views.map(d => {
    const [y, m, day] = d.day.split('-');
    return `${day}/${m}`;
  });
  const values = daily_views.map(d => d.views);

  if (chartDaily) chartDaily.destroy();
  chartDaily = new Chart(document.getElementById('chart-daily'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Visitas',
        data: values,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.08)',
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: '#3b82f6',
        fill: true,
        tension: 0.4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 }, maxTicksLimit: 10 } },
        y: { beginAtZero: true, ticks: { precision: 0, font: { size: 11 } }, grid: { color: '#f0f0f0' } },
      },
    },
  });

  // ── Gráfico: clics por elemento ────────────────────────────────
  if (chartClicks) chartClicks.destroy();
  if (click_elements.length) {
    chartClicks = new Chart(document.getElementById('chart-clicks'), {
      type: 'doughnut',
      data: {
        labels: click_elements.map(c => c.element),
        datasets: [{
          data: click_elements.map(c => c.count),
          backgroundColor: COLORS,
          borderWidth: 2,
          borderColor: '#fff',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 12 } },
        },
      },
    });
  }

  // ── Bar lists ──────────────────────────────────────────────────
  renderBarList('top-products', top_products, 'name', 'clicks', '#8b5cf6');
  renderBarList('referrers', referrers, 'source', 'count', '#10b981');
  renderBarList('top-pages', top_pages, 'path', 'count', '#f59e0b');

  // ── Heatmap ────────────────────────────────────────────────────
  renderHeatmap(heatmap);
}

function renderBarList(containerId, items, nameKey, countKey, color) {
  const el = document.getElementById(containerId);
  if (!items.length) {
    el.innerHTML = '<p style="font-size:0.82rem;color:#9ca3af;padding:8px 0">Sin datos aún</p>';
    return;
  }
  const max = Math.max(...items.map(i => i[countKey]));
  el.innerHTML = items.map(item => {
    const pct = max > 0 ? Math.round((item[countKey] / max) * 100) : 0;
    return `
      <div class="bar-item">
        <div class="bar-item__header">
          <span class="bar-item__name" title="${item[nameKey]}">${item[nameKey]}</span>
          <span class="bar-item__count">${fmt(item[countKey])}</span>
        </div>
        <div class="bar-item__track">
          <div class="bar-item__fill" style="width:${pct}%;background:${color}"></div>
        </div>
      </div>`;
  }).join('');
}

function renderHeatmap(points) {
  const canvas = document.getElementById('heatmap-canvas');
  const emptyMsg = document.getElementById('heatmap-empty');

  if (!points.length) {
    emptyMsg.style.display = 'flex';
    return;
  }
  emptyMsg.style.display = 'none';

  const ctx = canvas.getContext('2d');
  const W = canvas.offsetWidth  || 800;
  const H = canvas.offsetHeight || 300;
  canvas.width  = W;
  canvas.height = H;

  ctx.clearRect(0, 0, W, H);

  const maxCount = Math.max(...points.map(p => p.count));

  points.forEach(({ x, y, count }) => {
    const px = (x / 100) * W;
    const py = (y / 100) * H;
    const radius = 28 + (count / maxCount) * 40;
    const alpha  = 0.15 + (count / maxCount) * 0.55;

    const grad = ctx.createRadialGradient(px, py, 0, px, py, radius);
    grad.addColorStop(0, `rgba(239,68,68,${alpha})`);
    grad.addColorStop(1, 'rgba(239,68,68,0)');

    ctx.beginPath();
    ctx.arc(px, py, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();
  });
}

// Cargar al iniciar — movido al final del archivo

/* ── Ventas ── */
let chartRevenue = null;

async function loadSales() {
  let data;
  try {
    const res = await fetch('/analytics/sales');
    if (!res.ok) return;
    data = await res.json();
  } catch { return; }

  const { totals, daily_sales, top_sold, recent } = data;

  document.getElementById('kpi-revenue').textContent = `€${fmt(totals.total_revenue)}`;
  document.getElementById('kpi-orders').textContent = fmt(totals.total_orders);
  document.getElementById('kpi-revenue-30d').textContent = `€${fmt(totals.revenue_30d)} últimos 30 días`;

  // Gráfico ingresos diarios
  if (chartRevenue) chartRevenue.destroy();
  if (daily_sales.length) {
    chartRevenue = new Chart(document.getElementById('chart-revenue'), {
      type: 'bar',
      data: {
        labels: daily_sales.map(d => { const [y,m,day] = d.day.split('-'); return `${day}/${m}`; }),
        datasets: [{
          label: 'Ingresos €',
          data: daily_sales.map(d => d.revenue),
          backgroundColor: 'rgba(16,185,129,0.7)',
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 11 }, maxTicksLimit: 10 } },
          y: { beginAtZero: true, ticks: { font: { size: 11 } }, grid: { color: '#f0f0f0' } },
        },
      },
    });
  }

  // Top vendidos
  renderBarList('top-sold', top_sold, 'name', 'revenue', '#10b981');

  // Historial
  const tbody = document.getElementById('sales-tbody');
  if (!recent.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="td-empty">Sin ventas registradas aún</td></tr>';
  } else {
    tbody.innerHTML = recent.map(s => `
      <tr>
        <td><strong>${s.product}</strong></td>
        <td>€${s.price.toFixed(2)}</td>
        <td>${s.discount ? `<span style="color:#d97706;font-weight:600">${s.discount}%</span>` : '—'}</td>
        <td>€${s.final_price.toFixed(2)}</td>
        <td>${s.qty}</td>
        <td>${s.size || '—'}</td>
        <td><strong>€${s.total.toFixed(2)}</strong></td>
        <td style="color:#9ca3af;font-size:0.78rem">${s.date}</td>
      </tr>`).join('');
  }
}

/* ── Descuentos y destacados ── */
async function loadDiscounts() {
  let products;
  try {
    const res = await fetch('/analytics/products-list');
    if (!res.ok) return;
    products = await res.json();
  } catch { return; }

  const container = document.getElementById('discounts-list');
  if (!products.length) {
    container.innerHTML = '<p style="color:#9ca3af;font-size:0.85rem">No hay productos cargados.</p>';
    return;
  }

  container.innerHTML = products.map(p => `
    <div class="discount-card" id="dc-${p.id}">
      <img src="${p.image || ''}" alt="${p.name}" class="discount-card__img" onerror="this.style.display='none'">
      <div class="discount-card__body">
        <p class="discount-card__name">${p.name}</p>
        <p class="discount-card__price">€${p.price.toFixed(2)} · Stock: ${p.stock}</p>
        <div class="discount-card__controls">
          <label class="discount-label">Descuento %</label>
          <input type="number" min="0" max="100" value="${p.discount}"
            class="discount-input" id="disc-${p.id}" placeholder="0">
          <label class="discount-label" style="display:flex;align-items:center;gap:6px;cursor:pointer;">
            <input type="checkbox" id="feat-${p.id}" ${p.is_featured ? 'checked' : ''}
              style="width:16px;height:16px;accent-color:#111;cursor:pointer;">
            Destacado
          </label>
          <button onclick="saveDiscount(${p.id})" class="discount-save-btn">
            <i class="fa-solid fa-check"></i> Guardar
          </button>
        </div>
        <p class="discount-feedback" id="fb-${p.id}"></p>
      </div>
    </div>`).join('');
}

async function saveDiscount(productId) {
  const discount = parseInt(document.getElementById(`disc-${productId}`).value) || 0;
  const is_featured = document.getElementById(`feat-${productId}`).checked;
  const fb = document.getElementById(`fb-${productId}`);

  try {
    const res = await fetch('/analytics/set-discount', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, discount, is_featured }),
    });
    if (res.ok) {
      fb.textContent = '✓ Guardado';
      fb.style.color = '#10b981';
    } else {
      fb.textContent = 'Error al guardar';
      fb.style.color = '#ef4444';
    }
  } catch {
    fb.textContent = 'Error de conexión';
    fb.style.color = '#ef4444';
  }
  setTimeout(() => { fb.textContent = ''; }, 2500);
}

// Cargar todo al iniciar
document.addEventListener('DOMContentLoaded', () => {
  // Pequeño delay para que el layout esté completamente pintado
  // antes de que Chart.js calcule las dimensiones del canvas
  setTimeout(() => {
    loadMetrics();
    loadSales();
    loadDiscounts();
  }, 50);
});

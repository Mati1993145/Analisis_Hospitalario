const API_BASE = "";
const REFRESH_MS = 300000;

let refreshTimer = null;
let predictionData = [];

const colors = {
  canvas: "#0E1117",
  card: "#1A1F2E",
  border: "#2A3142",
  title: "#FFFFFF",
  secondary: "#9CA3AF",
  muted: "#6B7280",
  cyan: "#22D3EE",
  green: "#34D399",
  amber: "#FBBF24",
  red: "#F87171",
  violet: "#A78BFA",
};

const plotConfig = { responsive: true, displayModeBar: false };

const darkLayout = {
  paper_bgcolor: colors.canvas,
  plot_bgcolor: colors.canvas,
  font: { color: colors.secondary, family: "Segoe UI, system-ui" },
  margin: { l: 56, r: 38, t: 28, b: 48 },
  hovermode: "x unified",
  legend: {
    orientation: "h",
    y: 1.12,
    x: 0,
    bgcolor: "rgba(14,17,23,0)",
    font: { color: colors.secondary },
  },
  xaxis: {
    gridcolor: colors.border,
    zerolinecolor: colors.border,
    tickfont: { color: colors.secondary },
  },
  yaxis: {
    gridcolor: colors.border,
    zerolinecolor: colors.border,
    tickfont: { color: colors.secondary },
  },
};

function showError(message) {
  const banner = document.getElementById("error-banner");
  banner.textContent = message;
  banner.classList.remove("hidden");
}

function clearError() {
  const banner = document.getElementById("error-banner");
  banner.textContent = "";
  banner.classList.add("hidden");
}

async function fetchData(endpoint) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) {
      showError(`No se pudo cargar ${endpoint}: HTTP ${response.status}`);
      return null;
    }
    return await response.json();
  } catch (error) {
    showError(`No se pudo conectar con ${endpoint}: ${error.message}`);
    return null;
  }
}

// Formateadores centralizados para mantener los KPI y tooltips consistentes.
function formatPercent(value, digits = 1) {
  return Number.isFinite(Number(value)) ? `${Number(value).toFixed(digits)}%` : "--";
}

function formatNumber(value) {
  return Number.isFinite(Number(value)) ? Number(value).toLocaleString("es-CL") : "--";
}

function formatDecimal(value, digits = 1) {
  return Number.isFinite(Number(value)) ? Number(value).toLocaleString("es-CL", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }) : "--";
}

function monthLabel(row) {
  return `${row.periodo}-${String(row.mes).padStart(2, "0")}`;
}

function sortByPeriodMonth(a, b) {
  return Number(a.periodo) - Number(b.periodo) || Number(a.mes) - Number(b.mes);
}

function mergedLayout(overrides = {}) {
  return {
    ...darkLayout,
    ...overrides,
    xaxis: { ...darkLayout.xaxis, ...(overrides.xaxis || {}) },
    yaxis: { ...darkLayout.yaxis, ...(overrides.yaxis || {}) },
  };
}

async function renderKPIs() {
  const data = await fetchData("/api/resumen");
  if (!data || !data.length) return;

  const item = data[0];
  document.getElementById("kpi-ocupacion").textContent = formatPercent(item.indice_ocupacional_prom, 1);
  document.getElementById("kpi-egresos").textContent = formatNumber(item.total_egresos);
  document.getElementById("kpi-letalidad").textContent = formatPercent(item.letalidad_nacional, 2);
  document.getElementById("kpi-estada").textContent = `${formatDecimal(item.promedio_dias_estada_prom, 1)} días`;
}

async function renderEvolucion() {
  const data = await fetchData("/api/evolucion");
  if (!data) return;

  const rows = [...data].sort(sortByPeriodMonth);
  const trace = {
    x: rows.map(monthLabel),
    y: rows.map((row) => row.indice_ocupacional_prom),
    type: "scatter",
    mode: "lines",
    name: "Índice ocupacional",
    line: { color: colors.cyan, width: 3 },
  };

  Plotly.react("chart-evolucion", [trace], mergedLayout({
    yaxis: { title: "Índice ocupacional (%)", ticksuffix: "%" },
  }), plotConfig);
}

async function renderCovid() {
  const data = await fetchData("/api/covid");
  if (!data) return;

  const rows = [...data].sort(sortByPeriodMonth);
  const x = rows.map(monthLabel);
  const ocupacion = rows.map((row) => Number(row.indice_ocupacional_prom));
  const letalidad = rows.map((row) => Number(row.letalidad_prom));

  const minOcupacion = rows.reduce((min, row) => (
    Number(row.indice_ocupacional_prom) < Number(min.indice_ocupacional_prom) ? row : min
  ), rows[0]);
  const maxLetalidad = rows.reduce((max, row) => (
    Number(row.letalidad_prom) > Number(max.letalidad_prom) ? row : max
  ), rows[0]);

  // Los KPI de apoyo se calculan desde la misma serie del gráfico COVID.
  document.getElementById("kpi-caida-ocupacion").textContent =
    `${formatPercent(minOcupacion.indice_ocupacional_prom, 1)} · ${monthLabel(minOcupacion)}`;
  document.getElementById("kpi-peak-letalidad").textContent =
    `${formatPercent(maxLetalidad.letalidad_prom, 2)} · ${monthLabel(maxLetalidad)}`;

  const traces = [
    {
      x,
      y: ocupacion,
      type: "scatter",
      mode: "lines",
      name: "Ocupación",
      line: { color: colors.cyan, width: 3 },
      yaxis: "y",
    },
    {
      x,
      y: letalidad,
      type: "scatter",
      mode: "lines",
      name: "Letalidad",
      line: { color: colors.red, width: 3 },
      yaxis: "y2",
    },
  ];

  Plotly.react("chart-covid", traces, mergedLayout({
    shapes: [{
      type: "rect",
      xref: "x",
      yref: "paper",
      x0: "2020-01",
      x1: "2021-12",
      y0: 0,
      y1: 1,
      fillcolor: colors.red,
      opacity: 0.12,
      line: { width: 0 },
      layer: "below",
    }],
    yaxis: { title: "Ocupación (%)", ticksuffix: "%" },
    yaxis2: {
      title: "Letalidad (%)",
      ticksuffix: "%",
      overlaying: "y",
      side: "right",
      gridcolor: "rgba(42,49,66,0)",
      zerolinecolor: colors.border,
      tickfont: { color: colors.secondary },
      titlefont: { color: colors.secondary },
    },
  }), plotConfig);
}

function renderRankingTable(data) {
  const container = document.getElementById("tabla-ranking");
  if (!data) return;
  if (!data.length) {
    container.innerHTML = '<div class="empty-state">Sin datos para el periodo seleccionado.</div>';
    return;
  }

  const maxIdx = Math.max(...data.map((row) => Number(row.idx_ocup_prom) || 0), 1);
  const rows = data.map((row) => {
    const idx = Number(row.idx_ocup_prom) || 0;
    const width = Math.max(2, (idx / maxIdx) * 100);
    return `
      <tr>
        <td>${row.ranking}</td>
        <td>${row.establecimiento}</td>
        <td class="bar-cell">
          <div class="bar-track">
            <span class="bar-fill" style="width: ${width}%"></span>
            <span class="bar-value">${formatPercent(idx, 1)}</span>
          </div>
        </td>
        <td>${formatNumber(row.numero_egresos)}</td>
      </tr>
    `;
  }).join("");

  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Ranking</th>
          <th>Establecimiento</th>
          <th>Índice ocupacional promedio</th>
          <th>Egresos</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderClusters(data) {
  const container = document.getElementById("clusters-container");
  if (!data) return;

  container.innerHTML = data.map((cluster) => `
    <article class="cluster-card cluster-${cluster.cluster}">
      <h3>Cluster ${cluster.cluster}: ${cluster.etiqueta}</h3>
      <p>${cluster.descripcion}</p>
    </article>
  `).join("");
}

async function renderLetalidadArea(periodo) {
  const data = await fetchData(`/api/letalidad-area?periodo=${periodo}`);
  if (!data) return;

  const rows = [...data]
    .sort((a, b) => Number(b.letalidad_pct) - Number(a.letalidad_pct))
    .slice(0, 12)
    .reverse();

  const trace = {
    x: rows.map((row) => row.letalidad_pct),
    y: rows.map((row) => row.area_funcional),
    type: "bar",
    orientation: "h",
    marker: { color: colors.red },
    name: "Letalidad",
    text: rows.map((row) => formatPercent(row.letalidad_pct, 2)),
    textposition: "auto",
  };

  Plotly.react("chart-letalidad-area", [trace], mergedLayout({
    margin: { l: 180, r: 26, t: 18, b: 42 },
    xaxis: { title: "Letalidad (%)", ticksuffix: "%" },
    yaxis: { automargin: true },
    showlegend: false,
  }), plotConfig);
}

async function renderEstablecimientos(periodo) {
  const [ranking, clusters] = await Promise.all([
    fetchData(`/api/ranking?periodo=${periodo}`),
    fetchData("/api/clusters"),
  ]);

  renderRankingTable(ranking);
  renderClusters(clusters);
  await renderLetalidadArea(periodo);
}

function seriesKey(row) {
  return `${row.ESTABLECIMIENTO} · ${row.AREA_FUNCIONAL}`;
}

function populatePredictionSelect(data) {
  const select = document.getElementById("select-serie");
  const current = select.value;
  const unique = [...new Set(data.map(seriesKey))].sort((a, b) => a.localeCompare(b, "es"));

  // Se preserva la selección actual cuando el auto-refresh trae la misma serie.
  select.innerHTML = unique.map((key) => `<option value="${key}">${key}</option>`).join("");
  if (unique.includes(current)) {
    select.value = current;
  }
}

function drawPredictionSeries(key) {
  const rows = predictionData
    .filter((row) => seriesKey(row) === key)
    .sort((a, b) => Number(a.MES) - Number(b.MES));

  const realRows = rows.filter((row) => row.VALOR_REAL !== null && row.VALOR_REAL !== undefined);

  const traces = [
    {
      x: realRows.map((row) => row.MES),
      y: realRows.map((row) => row.VALOR_REAL),
      type: "scatter",
      mode: "lines+markers",
      name: "Real",
      line: { color: colors.cyan, width: 3 },
      marker: { color: colors.cyan, size: 6 },
    },
    {
      x: rows.map((row) => row.MES),
      y: rows.map((row) => row.INDICE_OCUPACIONAL_PREDICHO),
      type: "scatter",
      mode: "lines+markers",
      name: "Predicho",
      line: { color: colors.violet, width: 3, dash: "dot" },
      marker: { color: colors.violet, size: 6 },
    },
  ];

  Plotly.react("chart-predicciones", traces, mergedLayout({
    xaxis: { title: "Mes", dtick: 1 },
    yaxis: { title: "Índice ocupacional (%)", ticksuffix: "%" },
  }), plotConfig);
}

async function renderPredicciones() {
  const data = await fetchData("/api/predicciones");
  if (!data) return;

  predictionData = data;
  populatePredictionSelect(predictionData);
  const select = document.getElementById("select-serie");
  if (select.value) drawPredictionSeries(select.value);
}

function activateTab(tabName) {
  document.querySelectorAll(".tab-section").forEach((section) => {
    section.classList.toggle("hidden", section.id !== `tab-${tabName}`);
  });
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabName);
  });
  window.dispatchEvent(new Event("resize"));
}

async function refreshAll() {
  clearError();
  const periodo = document.getElementById("select-periodo-ranking").value;
  await Promise.all([
    renderKPIs(),
    renderEvolucion(),
    renderCovid(),
    renderEstablecimientos(periodo),
    renderPredicciones(),
  ]);

  const now = new Date();
  document.getElementById("last-update").textContent =
    `Última actualización: ${now.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit" })}`;
}

function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(refreshAll, REFRESH_MS);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => activateTab(button.dataset.tab));
  });

  document.getElementById("select-periodo-ranking").addEventListener("change", (event) => {
    renderEstablecimientos(event.target.value);
  });

  document.getElementById("select-serie").addEventListener("change", (event) => {
    drawPredictionSeries(event.target.value);
  });

  activateTab("resumen");
  refreshAll();
  startAutoRefresh();
});

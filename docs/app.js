const state = {
  rows: [], filtered: [], page: 1, pageSize: 50,
  sortColumn: "sample", sortDirection: 1,
};

const byId = (id) => document.getElementById(id);

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const columns = lines.shift().split(",");
  return lines.map((line) => Object.fromEntries(
    columns.map((column, index) => [column, line.split(",")[index]]),
  ));
}

function compareRows(leftRow, rightRow) {
  const left = leftRow[state.sortColumn];
  const right = rightRow[state.sortColumn];
  const difference = typeof left === "number" ? left - right : left.localeCompare(right);
  return difference * state.sortDirection;
}

function renderFrequencyTable() {
  const pages = Math.max(1, Math.ceil(state.filtered.length / state.pageSize));
  state.page = Math.min(state.page, pages);
  const start = (state.page - 1) * state.pageSize;
  const rows = state.filtered.slice(start, start + state.pageSize);

  byId("frequency-body").innerHTML = rows.map((row) => `
    <tr>
      <td>${row.sample}</td><td>${row.total_count.toLocaleString()}</td>
      <td>${row.population}</td><td>${row.count.toLocaleString()}</td>
      <td>${row.percentage.toFixed(2)}%</td>
    </tr>
  `).join("");

  byId("page-summary").textContent = state.filtered.length
    ? `${(start + 1).toLocaleString()}–${Math.min(start + state.pageSize, state.filtered.length).toLocaleString()} of ${state.filtered.length.toLocaleString()}`
    : "No matching rows";
  byId("previous-page").disabled = state.page === 1;
  byId("next-page").disabled = state.page === pages;
}

function applyFilters() {
  const search = byId("sample-search").value.trim().toLowerCase();
  const population = byId("population-filter").value;
  state.filtered = state.rows
    .filter((row) => row.sample.toLowerCase().includes(search)
      && (!population || row.population === population))
    .sort(compareRows);
  state.page = 1;
  renderFrequencyTable();
}

async function loadFrequencyData() {
  try {
    const response = await fetch("data/relative-frequency.csv");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.rows = parseCsv(await response.text()).map((row) => ({
      ...row,
      total_count: Number(row.total_count),
      count: Number(row.count),
      percentage: Number(row.percentage),
    }));

    const populations = [...new Set(state.rows.map((row) => row.population))].sort();
    populations.forEach((population) => byId("population-filter").add(new Option(population, population)));
    byId("sample-count").textContent = new Set(state.rows.map((row) => row.sample)).size.toLocaleString();
    byId("population-count").textContent = populations.length.toLocaleString();
    byId("row-count").textContent = state.rows.length.toLocaleString();
    byId("status").textContent = "";
    applyFilters();
  } catch (error) {
    byId("status").textContent = "Could not load Part 2 data. Run `make pipeline`, then restart the dashboard.";
  }
}

function renderStatistics(rows) {
  byId("statistics-body").innerHTML = rows.map((row) => {
    const significant = row.significant === "True";
    const prefix = Number(row.mean_difference) > 0 ? "+" : "";
    return `
      <tr>
        <td>${row.population}</td>
        <td>${Number(row.responder_mean).toFixed(2)}%</td>
        <td>${Number(row.nonresponder_mean).toFixed(2)}%</td>
        <td>${prefix}${Number(row.mean_difference).toFixed(2)} pp</td>
        <td>${Number(row.t_statistic).toFixed(3)}</td>
        <td>${Number(row.p_value).toFixed(4)}</td>
        <td><span class="badge ${significant ? "text-bg-success" : "text-bg-secondary"}">${significant ? "Yes" : "No"}</span></td>
      </tr>
    `;
  }).join("");
}

async function loadResponderData() {
  try {
    const response = await fetch("data/responder-statistics.csv");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const rows = parseCsv(await response.text());
    byId("responder-count").textContent = Number(rows[0].responder_n).toLocaleString();
    byId("nonresponder-count").textContent = Number(rows[0].nonresponder_n).toLocaleString();
    byId("significant-count").textContent = rows.filter((row) => row.significant === "True").length;
    byId("part3-status").textContent = "";
    renderStatistics(rows);
  } catch (error) {
    byId("part3-status").textContent = "Could not load Part 3 data. Run `make pipeline`, then restart the dashboard.";
  }
}

function showView() {
  const requested = location.hash.slice(1);
  const selected = ["part2", "part3", "part4"].includes(requested) ? requested : "part2";
  document.querySelectorAll(".view").forEach((section) => { section.hidden = section.id !== selected; });
  document.querySelectorAll("nav a").forEach((link) => { link.classList.toggle("active", link.dataset.view === selected); });
  bootstrap.Offcanvas.getInstance(byId("sidebar"))?.hide();
}

function bindEvents() {
  byId("sample-search").addEventListener("input", applyFilters);
  byId("population-filter").addEventListener("change", applyFilters);
  byId("page-size").addEventListener("change", (event) => {
    state.pageSize = Number(event.target.value);
    state.page = 1;
    renderFrequencyTable();
  });
  byId("previous-page").addEventListener("click", () => { state.page -= 1; renderFrequencyTable(); });
  byId("next-page").addEventListener("click", () => { state.page += 1; renderFrequencyTable(); });
  document.querySelectorAll("th button[data-sort]").forEach((button) => {
    button.addEventListener("click", () => {
      state.sortDirection = state.sortColumn === button.dataset.sort ? -state.sortDirection : 1;
      state.sortColumn = button.dataset.sort;
      applyFilters();
    });
  });
  window.addEventListener("hashchange", showView);
}

bindEvents();
showView();
loadFrequencyData();
loadResponderData();

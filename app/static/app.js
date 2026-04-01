const fmtUSD = (value) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

const riskClass = (score) => {
  if (score >= 70) return 'risk-high';
  if (score >= 40) return 'risk-medium';
  return 'risk-low';
};

async function loadDashboard() {
  const data = await fetch('/api/dashboard').then((r) => r.json());
  const cards = document.getElementById('metric-cards');
  if (!cards) return;

  cards.innerHTML = `
    <div class="card"><div class="metric-label">Real-Time Risk Score</div><div class="metric-value ${riskClass(data.real_time_risk_score)}">${data.real_time_risk_score}</div></div>
    <div class="card"><div class="metric-label">Local Volatility</div><div class="metric-value">${data.local_volatility}</div></div>
    <div class="card"><div class="metric-label">Traffic Density</div><div class="metric-value">${data.traffic_density}%</div></div>
    <div class="card"><div class="metric-label">Forensic History Risk</div><div class="metric-value">${data.forensic_history_risk}%</div></div>
    <div class="card"><div class="metric-label">Approval Rate</div><div class="metric-value">${data.approval_rate}%</div></div>
    <div class="card"><div class="metric-label">Payout Exposure</div><div class="metric-value">${fmtUSD(data.payout_exposure_usd)}</div></div>
  `;

  const ctx = document.getElementById('riskChart');
  if (ctx) {
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.risk_trend.map((_, i) => `T${i + 1}`),
        datasets: [{
          label: 'Risk Trend',
          data: data.risk_trend,
          borderColor: '#00F2FF',
          backgroundColor: 'rgba(0,242,255,0.2)',
          tension: 0.35
        }]
      },
      options: { plugins: { legend: { labels: { color: '#f5f5f5' } } }, scales: { y: { ticks: { color: '#9da2a6' } }, x: { ticks: { color: '#9da2a6' } } } }
    });
  }
}

async function loadDrivers() {
  const rows = document.getElementById('driver-rows');
  if (!rows) return;
  const drivers = await fetch('/api/drivers').then((r) => r.json());
  rows.innerHTML = drivers.map((d) => `
    <tr>
      <td>${d.driver_id}</td>
      <td>${d.display_name}</td>
      <td>${d.strikes}</td>
      <td>${d.forensic_history_score}%</td>
      <td class="${d.restricted ? 'risk-high' : 'risk-low'}">${d.restricted ? 'RESTRICTED' : 'ACTIVE'}</td>
    </tr>
  `).join('');
}

async function loadClaims() {
  const rows = document.getElementById('claim-rows');
  if (!rows) return;
  const claims = await fetch('/api/claims').then((r) => r.json());
  rows.innerHTML = claims.map((c) => `
    <tr>
      <td>${c.claim_id}</td>
      <td>${c.driver_id}</td>
      <td>${c.status}</td>
      <td>${c.oracle.observed_condition}</td>
      <td>${fmtUSD(c.payout_usd)}</td>
      <td>${c.strikes_after_decision}</td>
    </tr>
  `).join('');
}

async function bindClaimForm() {
  const form = document.getElementById('claim-form');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(form).entries());
    const response = await fetch('/api/claims/submit', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });

    const out = document.getElementById('claim-output');
    if (!response.ok) {
      const err = await response.json();
      out.innerHTML = `<span class="risk-high">${err.detail}</span>`;
      return;
    }

    const decision = await response.json();
    out.innerHTML = `<span class="${decision.status === 'APPROVED' ? 'risk-low' : 'risk-high'}">${decision.status}</span> — ${decision.reason} | Payout: ${fmtUSD(decision.payout_usd)}`;
    await loadClaims();
    await loadDrivers();
    await loadDashboard();
  });
}

async function loadPolicy() {
  const container = document.getElementById('policy-content');
  if (!container) return;
  const policy = await fetch('/api/policy').then((r) => r.json());
  const payoutRows = Object.entries(policy.payout_rules).map(([k, v]) => `<li>${k}: ${fmtUSD(v)}/hour</li>`).join('');
  const consensus = policy.consensus_description.map((r) => `<li><strong>${r.title}:</strong> ${r.detail}</li>`).join('');
  const strikes = policy.strike_policy.map((r) => `<li><strong>${r.title}:</strong> ${r.detail}</li>`).join('');
  container.innerHTML = `
    <div class="card"><h3>Automated Payout Engine</h3><ul>${payoutRows}</ul></div>
    <div class="card"><h3>Consensus Engine</h3><ul>${consensus}</ul></div>
    <div class="card"><h3>3-Strike Fraud Policy</h3><ul>${strikes}</ul></div>
  `;
}

window.addEventListener('DOMContentLoaded', async () => {
  await Promise.all([loadDashboard(), loadDrivers(), loadClaims(), loadPolicy(), bindClaimForm()]);
});

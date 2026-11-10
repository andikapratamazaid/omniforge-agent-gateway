// Dashboard OmniForge: coba /api/status (gateway live), fallback ke data/status.json (seed).
async function load() {
  let data;
  try {
    const r = await fetch('/api/status');
    if (!r.ok) throw new Error('no gateway');
    data = await r.json();
  } catch (e) {
    const r = await fetch('data/status.json');
    data = await r.json();
  }
  const stats = data.stats || {};
  const cards = [
    ['Identitas', stats.identities], ['Tautan platform', stats.links],
    ['Pesan tersimpan', stats.messages], ['Tugas cron', stats.cron_jobs],
    ['Eksekusi', stats.executions], ['Mode', data.mode]
  ];
  document.getElementById('cards').innerHTML = cards.map(c =>
    `<div class="card"><b>${c[1] ?? 0}</b>${c[0]}</div>`).join('');
  document.getElementById('platforms').innerHTML =
    ['telegram', 'discord', 'slack', 'whatsapp', 'signal', 'cli']
      .map(p => `<span class="chip">${p}</span>`).join('');
  document.querySelector('#backends tbody').innerHTML = (data.backends || []).map(b =>
    `<tr><td>${b.name}</td><td>${b.status}</td><td>${b.note}</td></tr>`).join('');
}
load();

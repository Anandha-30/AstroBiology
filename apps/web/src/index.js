// Simple client for API endpoints
const apiBase = 'http://localhost:8000';

// Health
const healthEl = document.getElementById('health');
if (healthEl) {
  (async () => {
    try {
      const res = await fetch(`${apiBase}/health`);
      const data = await res.json();
      healthEl.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } catch (e) {
      healthEl.innerHTML = `<p style=\"color:#b91c1c\">Failed to reach API on ${apiBase}. Start it with:</p><pre>uvicorn services.api.main:app --reload</pre>`;
    }
  })();
}

// Summarization
const sumBtn = document.getElementById('run-summarize');
const sumText = document.getElementById('sum-text');
const sumLang = document.getElementById('sum-lang');
const sumResult = document.getElementById('sum-result');

if (sumBtn) sumBtn.addEventListener('click', async () => {
  sumResult.textContent = 'Running summarization...';
  try {
    const res = await fetch(`${apiBase}/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: sumText.value, language: (sumLang?.value || 'en') })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    sumResult.innerHTML = `
      <h3>Abstract</h3>
      <p>${data.abstract || ''}</p>
      <h3>Key Takeaways</h3>
      <ul>${(data.key_takeaways || []).map(x => `<li>${x}</li>`).join('')}</ul>
      <h3>AI Tags</h3>
      <p>${(data.ai_tags || []).join(', ')}</p>
    `;
  } catch (e) {
    sumResult.innerHTML = `<p style="color:#b91c1c">Summarization failed: ${e.message}</p>`;
  }
});

// Semantic Search
const searchBtn = document.getElementById('run-search');
const searchQuery = document.getElementById('search-query');
const searchResult = document.getElementById('search-result');
const filterOrganism = document.getElementById('filter-organism');
const filterMission = document.getElementById('filter-mission');
const filterYear = document.getElementById('filter-year');

if (searchBtn) searchBtn.addEventListener('click', async () => {
  searchResult.textContent = 'Searching...';
  const filters = {};
  if (filterOrganism.value) filters.organism = filterOrganism.value;
  if (filterMission.value) filters.mission = filterMission.value;
  if (filterYear.value) filters.year = filterYear.value;

  try {
    const res = await fetch(`${apiBase}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: searchQuery.value, filters })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const rows = (data.results || []).map(r => `
      <div class="row">
        <div>
          <strong>${r.title}</strong>
          <div class="meta">${r.meta?.organism || ''} · ${r.meta?.mission || ''} · ${r.meta?.year || ''}</div>
          <div class="snippet">${r.snippet || ''}</div>
        </div>
        <div class="score" title="${data.note || ''}">${r.score?.toFixed ? r.score.toFixed(3) : r.score}</div>
      </div>
    `).join('');
    searchResult.innerHTML = rows || '<p>No results.</p>';
  } catch (e) {
    searchResult.innerHTML = `<p style=\"color:#b91c1c\">Search failed: ${e.message}</p>`;
  }
});

// Buddy Chat
const buddyMessages = document.getElementById('buddy-messages');
const buddyInput = document.getElementById('buddy-input');
const buddySend = document.getElementById('buddy-send');
const renderBubble = (text, who='assistant') => {
  const div = document.createElement('div');
  div.className = `bubble ${who === 'user' ? 'user' : 'assistant'}`;
  div.textContent = text;
  buddyMessages.appendChild(div);
  buddyMessages.scrollTop = buddyMessages.scrollHeight;
};
if (buddySend) {
  buddySend.addEventListener('click', async () => {
    const q = buddyInput.value.trim();
    if (!q) return;
    renderBubble(q, 'user');
    buddyInput.value = '';
    try {
      const res = await fetch(`${apiBase}/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [{ role: 'user', content: q }] })
      });
      const data = await res.json();
      renderBubble(data.reply || 'No reply');
    } catch (e) {
      renderBubble(`Chat failed: ${e.message}`);
    }
  });
}

// Gap Analysis
const gapBtn = document.getElementById('gap-run');
const gapTopic = document.getElementById('gap-topic');
const gapResult = document.getElementById('gap-result');
if (gapBtn) {
  gapBtn.addEventListener('click', async () => {
    gapResult.textContent = 'Analyzing gaps...';
    try {
      const res = await fetch(`${apiBase}/gap_analyze`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: gapTopic.value })
      });
      const data = await res.json();
      gapResult.innerHTML = `<pre>${(data.gaps || '').replaceAll('<', '&lt;')}</pre>`;
    } catch (e) {
      gapResult.innerHTML = `<p style="color:#b91c1c">Gap analysis failed: ${e.message}</p>`;
    }
  });
}

// Timeline
const timelineBtn = document.getElementById('timeline-load');
const timelineResult = document.getElementById('timeline-result');
if (timelineBtn) {
  timelineBtn.addEventListener('click', async () => {
    timelineResult.textContent = 'Loading timeline...';
    try {
      const res = await fetch(`${apiBase}/timeline`);
      const data = await res.json();
      const html = (data.missions || []).map(m => `
        <div class="card" style="margin-top:.5rem">
          <h3>${m.mission} (${m.count})</h3>
          ${m.summary ? `<p>${m.summary}</p>` : ''}
          <ul>${(m.items||[]).map(i => `<li>${i.year} · ${i.organism} · ${i.title}</li>`).join('')}</ul>
        </div>
      `).join('');
      timelineResult.innerHTML = html || '<p>No missions found.</p>';
    } catch (e) {
      timelineResult.innerHTML = `<p style="color:#b91c1c">Timeline failed: ${e.message}</p>`;
    }
  });
}

// Personalization (local-only demo)
let userProfile = { role: 'student', interests: '' };
const roleSel = document.getElementById('user-role');
const interestsInput = document.getElementById('user-interests');
const saveBtn = document.getElementById('user-save');
const recoBtn = document.getElementById('reco-run');
const recoResult = document.getElementById('reco-result');
if (saveBtn) {
  saveBtn.addEventListener('click', () => {
    userProfile = { role: roleSel.value, interests: interestsInput.value };
    recoResult.textContent = 'Profile saved locally.';
  });
}
if (recoBtn) {
  recoBtn.addEventListener('click', async () => {
    searchQuery.value = userProfile.interests;
    filterMission.value = '';
    filterOrganism.value = '';
    filterYear.value = '';
    await searchBtn.click();
    recoResult.textContent = 'Recommendations loaded in search results.';
  });
}

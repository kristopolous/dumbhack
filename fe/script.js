const personas = [
  { id: 'cool-dude', emoji: '😎', desc: 'Cool Dude - The laid-back party starter' },
  { id: 'nerd', emoji: '🤓', desc: 'Nerd - The trivia master' },
  { id: 'singer', emoji: '🎤', desc: 'Singer - The karaoke queen' },
  { id: 'chef', emoji: '👨‍🍳', desc: 'Chef - The recipe whisperer' },
  { id: 'dancer', emoji: '💃', desc: 'Dancer - The groove guru' }
];

const urlInput = document.getElementById('urlInput');
const callButton = document.getElementById('callButton');
const personasGrid = document.getElementById('personasGrid');
const callControls = document.getElementById('callControls');
const callIdDisplay = document.getElementById('callIdDisplay');

let currentCallId = null;
let selectedPersonas = new Set();

// Populate personas
personas.forEach(persona => {
  const card = document.createElement('div');
  card.className = 'persona-card';
  card.innerHTML = `
    <input type="checkbox" id="${persona.id}" aria-label="Toggle ${persona.desc}">
    <label for="${persona.id}" class="persona-content" tabindex="0">
      <span class="persona-emoji">${persona.emoji}</span>
      <div class="persona-desc">${persona.desc}</div>
    </label>
    <div class="action-buttons" style="display: none;">
      <button class="add-button" data-persona="${persona.id}">Add to Call</button>
      <button class="hangup-button" data-persona="${persona.id}">Hangup</button>
    </div>
  `;
  personasGrid.appendChild(card);

  const checkbox = card.querySelector('input[type="checkbox"]');
  const label = card.querySelector('.persona-content');
  const actions = card.querySelector('.action-buttons');

  // Toggle functionality
  checkbox.addEventListener('change', () => {
    if (checkbox.checked) {
      selectedPersonas.add(persona.id);
    } else {
      selectedPersonas.delete(persona.id);
    }
    updateCallButton();
    if (currentCallId) {
      toggleActions(actions, checkbox.checked);
    }
  });

  // Keyboard support for label
  label.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      checkbox.checked = !checkbox.checked;
      checkbox.dispatchEvent(new Event('change'));
    }
  });

  // Post-call actions
  const addBtn = card.querySelector('.add-button');
  const hangupBtn = card.querySelector('.hangup-button');

  addBtn.addEventListener('click', () => addToCall(persona.id));
  hangupBtn.addEventListener('click', () => removeFromCall(persona.id));
});

// Update call button state
function updateCallButton() {
  callButton.disabled = !urlInput.value || selectedPersonas.size === 0;
  callButton.textContent = `Call the Party Line (${selectedPersonas.size} persona${selectedPersonas.size !== 1 ? 's' : ''})`;
}

// Initial call
callButton.addEventListener('click', async () => {
  if (!urlInput.value || selectedPersonas.size === 0) return;

  callButton.disabled = true;
  callButton.textContent = 'Calling...';

  try {
    // Mock response since backend not built; in production, fetch('/api/create-call')
    const response = await new Promise(resolve => {
      setTimeout(() => resolve({ id: 'call-' + Math.random().toString(36).substr(2, 9) }), 1000);
    });

    currentCallId = response.id;
    callIdDisplay.textContent = currentCallId;
    callControls.style.display = 'block';

    // Show initial actions for selected
    document.querySelectorAll('.persona-card input:checked').forEach(checkbox => {
      const card = checkbox.closest('.persona-card');
      const actions = card.querySelector('.action-buttons');
      toggleActions(actions, true);
    });

    // Update toggles to reflect initial selection as "in call"
    selectedPersonas.forEach(id => {
      const checkbox = document.getElementById(id);
      if (checkbox) checkbox.checked = true;
    });

  } catch (error) {
    console.error('Call failed:', error);
    alert('Call failed—check console for details.');
  } finally {
    callButton.disabled = false;
    callButton.textContent = 'Reset Call';
    callButton.onclick = resetCall; // Allow reset
  }
});

// Add to call
async function addToCall(personaId) {
  if (!currentCallId) return;

  try {
    // Mock; in prod: await fetch('/api/add-to-call', { method: 'POST', body: JSON.stringify({ id: currentCallId, persona: personaId }) });
    await new Promise(resolve => setTimeout(resolve, 500));
    const checkbox = document.getElementById(personaId);
    checkbox.checked = true;
    selectedPersonas.add(personaId);
    toggleActions(checkbox.closest('.persona-card').querySelector('.action-buttons'), true);
    announceStatus(`Added ${personaId} to call.`);
  } catch (error) {
    console.error('Add failed:', error);
  }
}

// Remove from call
async function removeFromCall(personaId) {
  if (!currentCallId) return;

  try {
    // Mock; in prod: await fetch('/api/remove-from-call', { method: 'POST', body: JSON.stringify({ id: currentCallId, persona: personaId }) });
    await new Promise(resolve => setTimeout(resolve, 500));
    const checkbox = document.getElementById(personaId);
    checkbox.checked = false;
    selectedPersonas.delete(personaId);
    toggleActions(checkbox.closest('.persona-card').querySelector('.action-buttons'), false);
    announceStatus(`Hung up on ${personaId}.`);
  } catch (error) {
    console.error('Remove failed:', error);
  }
}

// Toggle action buttons visibility
function toggleActions(actions, show) {
  actions.style.display = show ? 'flex' : 'none';
  if (show) {
    actions.querySelector('.add-button').style.display = 'none'; // Hide add if already in
    actions.querySelector('.hangup-button').style.display = 'block';
  } else {
    actions.querySelector('.add-button').style.display = 'block';
    actions.querySelector('.hangup-button').style.display = 'none';
  }
}

// Reset call
function resetCall() {
  currentCallId = null;
  selectedPersonas.clear();
  callControls.style.display = 'none';
  document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.checked = false;
    const actions = cb.closest('.persona-card').querySelector('.action-buttons');
    toggleActions(actions, false);
  });
  callButton.textContent = 'Call the Party Line';
  callButton.onclick = null; // Restore original
  callButton.disabled = true;
  urlInput.value = '';
}

// ARIA live announcements
function announceStatus(message) {
  const live = document.createElement('div');
  live.setAttribute('aria-live', 'polite');
  live.style.position = 'absolute';
  live.style.left = '-9999px';
  live.textContent = message;
  document.body.appendChild(live);
  setTimeout(() => document.body.removeChild(live), 1000);
}

// Input validation
urlInput.addEventListener('input', updateCallButton);

// Initial state
updateCallButton();

// === Configuration ===
const API_BASE_URL = 'http://localhost:8000';
const API_USERNAME = 'lpbd_user';
const API_PASSWORD = 'changeme123';

// === State Management ===
let currentSessionId = null;
let messageCount = 0;
let selectedAgent = null;
let isProcessing = false;
let isInside = false;

// === DOM Elements ===
const elements = {
    doorClickable: document.getElementById('door-clickable'),
    userInput: document.getElementById('user-input'),
    charCount: document.getElementById('char-count'),
    inputPanel: document.getElementById('input-panel'),
    sessionStatus: document.getElementById('session-status'),
    speechBubblesContainer: document.getElementById('speech-bubbles-container'),
    statusMessage: document.getElementById('status-message'),
    agentPortraits: document.querySelectorAll('.agent-portrait'),
    comicPanel: document.getElementById('comic-panel'),
    agentBar: document.querySelector('.agent-bar')
};

// === Utility Functions ===

function getAuthHeader() {
    const credentials = btoa(`${API_USERNAME}:${API_PASSWORD}`);
    return `Basic ${credentials}`;
}

function showStatus(message, type = 'info') {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status-message visible ${type}`;
    
    setTimeout(() => {
        elements.statusMessage.classList.remove('visible');
    }, 5000);
}

function updateCharCount() {
    const length = elements.userInput.value.length;
    elements.charCount.textContent = `${length}/500`;
    
    if (length > 450) {
        elements.charCount.className = 'char-count danger';
    } else if (length > 400) {
        elements.charCount.className = 'char-count warning';
    } else {
        elements.charCount.className = 'char-count';
    }
}

function enterBar() {
    isInside = true;
    
    // Switch background from exterior to interior
    elements.comicPanel.classList.remove('exterior');
    elements.comicPanel.classList.add('interior');
    
    // Show interior elements
    elements.speechBubblesContainer.style.display = 'flex';
    elements.userInput.style.display = 'block';
    elements.charCount.style.display = 'inline';
    document.getElementById('input-panel').style.display = 'block';
    
    // Show all agent portraits
    elements.agentPortraits.forEach(portrait => {
        portrait.style.display = 'flex';
    });
}

function addSpeechBubble(content, agent = null, isUser = false) {
    elements.speechBubblesContainer.innerHTML = '';
    const bubble = document.createElement('div');
    bubble.className = 'speech-bubble';
    
    if (isUser) {
        bubble.className += ' user-bubble';
        bubble.innerHTML = `<p>${escapeHtml(content)}</p>`;
    } else {
        bubble.className += ' agent-bubble';
        bubble.setAttribute('data-speaker', agent);  // Use data-speaker, not data-agent
        bubble.innerHTML = `
            <span class="agent-name-tag">${agent.toUpperCase()}</span>
            <p>${escapeHtml(content)}</p>
        `;
    }
    
    elements.speechBubblesContainer.appendChild(bubble);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function clearConversation() {
    elements.speechBubblesContainer.innerHTML = '';
}

function setUIState(state) {
    switch(state) {
        case 'initial':
            elements.userInput.disabled = true;
            break;
            
        case 'active':
            elements.userInput.disabled = false;
            elements.userInput.focus();
            break;
            
        case 'ended':
            elements.userInput.disabled = true;
            break;
            
        case 'processing':
            elements.userInput.disabled = true;
            break;
            
        case 'ready':
            elements.userInput.disabled = false;
            break;
    }
}

// === API Functions ===

async function startSession() {
    try {
        setUIState('processing');
        showStatus('Connecting...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/session/start`, {
            method: 'POST',
            headers: {
                'Authorization': getAuthHeader()
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Store session state
        currentSessionId = data.session_id;
        // Weather is fetched but not displayed - will be shown through window in final art
        
        // Transition to interior
        enterBar();
        clearConversation();
        
        setUIState('active');
        showStatus('Connected', 'success');
        
    } catch (error) {
        console.error('Failed to start session:', error);
        showStatus(`Connection failed: ${error.message}`, 'error');
        setUIState('initial');
    }
}

async function sendMessage() {
    const messageText = elements.userInput.value.trim();
    
    if (!messageText) {
        showStatus('Please enter a message', 'warning');
        return;
    }
    
    if (!currentSessionId) {
        showStatus('No active session. Please start a new session.', 'error');
        return;
    }
    
    try {
        isProcessing = true;
        setUIState('processing');
        
        // Add user message to UI immediately
        addSpeechBubble(messageText, null, true);
        elements.userInput.value = '';
        updateCharCount();
        
        // Send to API
        const response = await fetch(`${API_BASE_URL}/message`, {
            method: 'POST',
            headers: {
                'Authorization': getAuthHeader(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                content: messageText,
                selected_agent: selectedAgent
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add agent response
        addSpeechBubble(data.message, data.agent, false);
        
        // Update agent portraits (muted state)
        updateAgentStates(data.agents_available, data.agents_muted);
        
        // Check session status
        if (data.session_status === 'ended' || data.message_count >= 30) {
            setUIState('ended');
            showStatus('Session ended. Start a new session to continue.', 'warning');
        } else {
            setUIState('active');
        }
        
        // Warning for last call
        if (data.message_count === 25) {
            showStatus('Last call! Five messages remaining.', 'warning');
        }
        
    } catch (error) {
        console.error('Failed to send message:', error);
        showStatus(`Error: ${error.message}`, 'error');
        setUIState('active');
    } finally {
        isProcessing = false;
    }
}

function updateAgentStates(available, muted) {
    elements.agentPortraits.forEach(portrait => {
        const agent = portrait.dataset.agent;
        
        if (muted.includes(agent)) {
            portrait.classList.add('muted');
        } else {
            portrait.classList.remove('muted');
        }
    });
}

// === Event Listeners ===

const doorClickable = document.getElementById('door-clickable');
doorClickable.addEventListener('click', startSession);

elements.userInput.addEventListener('input', updateCharCount);

// Send on Enter (but allow Shift+Enter for newlines)
elements.userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isProcessing) {
        e.preventDefault();
        sendMessage();
    }
});

// Agent selection
elements.agentPortraits.forEach(portrait => {
    portrait.addEventListener('click', () => {
        if (portrait.classList.contains('muted')) {
            return; // Can't select muted agents
        }
        
        // Toggle selection
        const agent = portrait.dataset.agent;
        
        if (selectedAgent === agent) {
            // Deselect
            selectedAgent = null;
            portrait.classList.remove('selected');
        } else {
            // Select new agent
            elements.agentPortraits.forEach(p => p.classList.remove('selected'));
            portrait.classList.add('selected');
            selectedAgent = agent;
            showStatus(`Selected: ${agent.toUpperCase()}`, 'info');
        }
    });
});

// === Initialization ===

console.log('Le Pale Blue Dot - Frontend Initialized');
console.log('API Base URL:', API_BASE_URL);

// Set initial UI state
setUIState('initial');
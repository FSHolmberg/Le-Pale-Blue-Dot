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
let onboardingInProgress = false;
let isApproved = false;
let anonymousId = generateAnonymousId(); // Generate on page load

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

function generateAnonymousId() {
    // Check localStorage first
    let id = localStorage.getItem('lpbd_anonymous_id');
    if (!id) {
        id = 'anon_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('lpbd_anonymous_id', id);
    }
    return id;
}

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

// === Onboarding Functions ===

async function startOnboarding() {
    onboardingInProgress = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/onboard`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': getAuthHeader()
            },
            body: JSON.stringify({
                anonymous_id: anonymousId,
                message: null
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        displayOnboardingMessage('blanca', data.message);
        
        if (data.continue_onboarding) {
            showExteriorChatInput();
        } else if (data.approved) {
            isApproved = true;
            setTimeout(() => {
                showStatus('Click door to enter', 'success');
            }, 2000);
        } else {
            displayRejectionMessage();
        }
    } catch (error) {
        console.error('Onboarding failed:', error);
        showStatus('Connection failed', 'error');
    }
}

async function sendOnboardingMessage(userMessage) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/onboard`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': getAuthHeader()
            },
            body: JSON.stringify({
                anonymous_id: anonymousId,
                message: userMessage
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        displayOnboardingMessage('blanca', data.message);
        
        if (data.approved) {
            isApproved = true;
            hideExteriorChatInput();
        } else if (!data.continue_onboarding) {
            displayRejectionMessage();
            hideExteriorChatInput();
        }
    } catch (error) {
        console.error('Onboarding message failed:', error);
        showStatus('Message failed', 'error');
    }
}

function displayOnboardingMessage(speaker, message) {
    // Clear old bubbles FIRST
    const oldBubbles = elements.comicPanel.querySelectorAll('.onboarding-bubble');
    oldBubbles.forEach(b => b.remove());
    
    const bubble = document.createElement('div');
    bubble.className = 'speech-bubble onboarding-bubble';
    bubble.textContent = message;
    bubble.style.position = 'absolute';
    
    // Position bubble above Blanca (she's on the right side)
    if (speaker === 'blanca') {
        bubble.style.bottom = '55%';  // Above her head
        bubble.style.right = '15%';    // Right side where she stands
        bubble.style.left = 'auto';
    } else {
        // User bubble - center bottom
        bubble.style.bottom = '20%';
        bubble.style.left = '50%';
        bubble.style.transform = 'translateX(-50%)';
    }
    
    bubble.style.maxWidth = '400px';
    bubble.style.padding = '15px';
    bubble.style.background = 'rgba(0,0,0,0.8)';
    bubble.style.color = '#00ffcc';
    bubble.style.borderRadius = '8px';
    
    elements.comicPanel.appendChild(bubble);
}

function showExteriorChatInput() {
    const inputContainer = document.createElement('div');
    inputContainer.id = 'exterior-input';
    inputContainer.style.position = 'absolute';
    inputContainer.style.bottom = '5%';
    inputContainer.style.left = '50%';
    inputContainer.style.transform = 'translateX(-50%)';
    inputContainer.style.display = 'flex';
    inputContainer.style.gap = '10px';
    
    inputContainer.innerHTML = `
        <input type="text" id="onboarding-input" placeholder="Type your response..." 
               style="width: 300px; padding: 10px; font-size: 16px;">
        <button id="onboarding-send" style="padding: 10px 20px; cursor: pointer;">Send</button>
    `;
    
    elements.comicPanel.appendChild(inputContainer);
    
    // Add event listeners
    document.getElementById('onboarding-send').addEventListener('click', handleOnboardingSubmit);
    document.getElementById('onboarding-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleOnboardingSubmit();
        }
    });
    
    document.getElementById('onboarding-input').focus();
}

function hideExteriorChatInput() {
    const input = document.getElementById('exterior-input');
    if (input) input.remove();
}

async function handleOnboardingSubmit() {
    const input = document.getElementById('onboarding-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    displayOnboardingMessage('user', message);
    input.value = '';
    
    await sendOnboardingMessage(message);
}

function displayRejectionMessage() {
    const msg = document.createElement('div');
    msg.textContent = "You cannot enter tonight.";
    msg.style.position = 'absolute';
    msg.style.top = '50%';
    msg.style.left = '50%';
    msg.style.transform = 'translate(-50%, -50%)';
    msg.style.color = '#ff0000';
    msg.style.fontSize = '24px';
    msg.style.fontWeight = 'bold';
    
    elements.comicPanel.appendChild(msg);
}

// === Interior Functions ===

function enterBar() {
    isInside = true;
    
    // Clear onboarding UI
    hideExteriorChatInput();
    const bubbles = elements.comicPanel.querySelectorAll('.onboarding-bubble');
    bubbles.forEach(b => b.remove());
    
    // Switch background
    elements.comicPanel.classList.remove('exterior');
    elements.comicPanel.classList.add('interior');
    
    // Show interior elements
    elements.speechBubblesContainer.style.display = 'flex';
    elements.userInput.style.display = 'block';
    elements.charCount.style.display = 'inline';
    elements.inputPanel.style.display = 'block';
    
    elements.agentPortraits.forEach(portrait => {
        portrait.style.display = 'flex';
    });
    
    // Start actual session
    startSession();
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
        bubble.setAttribute('data-speaker', agent);
        bubble.innerHTML = `
            <span class="agent-name-tag">${agent.toUpperCase()}</span>
            <p>${escapeHtml(content)}</p>
        `;
    }
    
    elements.speechBubblesContainer.appendChild(bubble);
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
        currentSessionId = data.session_id;
        
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
        
        addSpeechBubble(messageText, null, true);
        elements.userInput.value = '';
        updateCharCount();
        
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
        
        addSpeechBubble(data.message, data.agent, false);
        updateAgentStates(data.agents_available, data.agents_muted);
        
        if (data.session_status === 'ended' || data.message_count >= 30) {
            setUIState('ended');
            showStatus('Session ended. Start a new session to continue.', 'warning');
        } else {
            setUIState('active');
        }
        
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

elements.doorClickable.addEventListener('click', async () => {
    if (!onboardingInProgress && !isApproved) {
        await startOnboarding();
    } else if (isApproved) {
        enterBar();
    }
});

elements.userInput.addEventListener('input', updateCharCount);

elements.userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isProcessing) {
        e.preventDefault();
        sendMessage();
    }
});

elements.agentPortraits.forEach(portrait => {
    portrait.addEventListener('click', () => {
        if (portrait.classList.contains('muted')) {
            return;
        }
        
        const agent = portrait.dataset.agent;
        
        if (selectedAgent === agent) {
            selectedAgent = null;
            portrait.classList.remove('selected');
        } else {
            elements.agentPortraits.forEach(p => p.classList.remove('selected'));
            portrait.classList.add('selected');
            selectedAgent = agent;
            showStatus(`Selected: ${agent.toUpperCase()}`, 'info');
        }
    });
});

// === Initialization ===

console.log('Le Pale Blue Dot - Frontend Initialized');
console.log('Anonymous ID:', anonymousId);
setUIState('initial');
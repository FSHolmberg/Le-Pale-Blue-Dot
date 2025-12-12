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

let onboardingData = {
    responses: []
};

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
            onboardingInProgress = false;
            setTimeout(() => {
            }, 2000);
        } else {
            displayRejectionMessage();
            onboardingInProgress = false;
        }
    } catch (error) {
        console.error('Onboarding failed:', error);
        showStatus('Connection failed', 'error');
    }
}

async function sendOnboardingMessage(userMessage) {
    // Store the response
    onboardingData.responses.push(userMessage);
    try {
        const response = await fetch(`${API_BASE_URL}/api/onboard`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': getAuthHeader()
            },
            body: JSON.stringify({
                anonymous_id: anonymousId,
                message: userMessage,
                context: onboardingData  // SEND IT TO BACKEND
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        displayOnboardingMessage('blanca', data.message);
        
        if (data.approved) {
            isApproved = true;
            onboardingInProgress = false;  // Only end it when approved
            hideExteriorChatInput();
        } else if (!data.continue_onboarding) {
            displayRejectionMessage();
            onboardingInProgress = false;  // Or rejected
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
        bubble.style.bottom = '55%';
        bubble.style.right = '15%';
        bubble.style.left = 'auto';
    } else {
        // User bubble - center bottom
        bubble.style.bottom = '20%';
        bubble.style.left = '50%';
        bubble.style.transform = 'translateX(-50%)';
    }
    
    bubble.style.maxWidth = '400px';
    bubble.style.padding = '15px';
    bubble.style.background = 'rgba(255, 255, 255, 0.95)';  // White
    bubble.style.color = '#000';  // Black text
    bubble.style.border = '3px solid #000';  // Black border
    bubble.style.borderRadius = '12px';
    
    elements.comicPanel.appendChild(bubble);
}

function showExteriorChatInput() {
    // Clone the existing input panel structure
    const inputContainer = document.createElement('div');
    inputContainer.id = 'exterior-input';
    inputContainer.className = 'input-panel'; // Use same class
    inputContainer.style.display = 'block';
    inputContainer.style.zIndex = '1000';
    
    const textarea = document.createElement('textarea');
    textarea.id = 'onboarding-input';
    textarea.placeholder = 'Type your response...';
    textarea.maxLength = 500;
    textarea.style.width = '100%';
    textarea.style.minHeight = '80px';
    textarea.style.background = 'rgba(22, 27, 34, 0.95)';
    textarea.style.color = '#c9d1d9';
    textarea.style.border = '1px solid rgba(88, 166, 255, 0.3)';
    textarea.style.borderRadius = '6px';
    textarea.style.padding = '12px';
    textarea.style.fontFamily = 'inherit';
    textarea.style.fontSize = '0.95em';
    textarea.style.resize = 'none';
    
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'input-controls';
    
    const charCount = document.createElement('span');
    charCount.id = 'onboarding-char-count';
    charCount.className = 'char-count';
    charCount.textContent = '0/500';
    
    controlsDiv.appendChild(charCount);
    inputContainer.appendChild(textarea);
    inputContainer.appendChild(controlsDiv);
    elements.comicPanel.appendChild(inputContainer);
    
    // Event listeners
    textarea.addEventListener('input', () => {
        charCount.textContent = `${textarea.value.length}/500`;
    });
    
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const message = textarea.value.trim();
            if (message) {
                displayOnboardingMessage('user', message);
                textarea.value = '';
                charCount.textContent = '0/500';
                sendOnboardingMessage(message);
            }
        }
    });
    
    textarea.focus();
}

function hideExteriorChatInput() {
    // Hide it again
    elements.inputPanel.style.display = 'none';
    elements.userInput.dataset.onboardingMode = 'false';
    elements.userInput.placeholder = 'Type your message...';
    elements.userInput.value = '';
}

async function handleOnboardingSubmit() {
    const message = elements.userInput.value.trim();
    
    if (!message) return;
    
    displayOnboardingMessage('user', message);
    elements.userInput.value = '';
    updateCharCount();
    
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

async function enterBar() {
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

    // Start actual session WITH onboarding context
    await startSession();

    // Get Bart's greeting
    const greeting = await fetch(`${API_BASE_URL}/message`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': getAuthHeader()
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            content: "::USER_ENTERED_BAR::",
            onboarding_context: onboardingData  // PASS IT HERE
        })
    });

    const bartGreeting = await greeting.json();
    addSpeechBubble(bartGreeting.message, bartGreeting.agent, false);
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
                'Authorization': getAuthHeader(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                anonymous_id: anonymousId 
            })  
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
    } else if (isApproved && !isInside) {
        enterBar();
    }
});

elements.userInput.addEventListener('input', updateCharCount);

elements.userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isProcessing) {
        e.preventDefault();
        
        if (elements.userInput.dataset.onboardingMode === 'true') {
            handleOnboardingSubmit();
        } else {
            sendMessage();
        }
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

// DEV ONLY - Reset onboarding with Ctrl+Shift+R
document.addEventListener('keydown', async (e) => {
    if (e.key === 'R' && e.shiftKey && e.ctrlKey) {
        console.log('Resetting anonymous ID...');
        
        // End session if active
        if (currentSessionId) {
            console.log('Ending active session first...');
            // Optionally call an end session endpoint here
        }
        
        localStorage.removeItem('lpbd_anonymous_id');
        location.reload();
    }
});
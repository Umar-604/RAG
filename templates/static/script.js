document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const questionInput = document.getElementById('question-input');
    const sendBtn = document.getElementById('send-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const voiceBtn = document.getElementById('voice-btn');
    const clearBtn = document.getElementById('clear-btn');
    const clearDocsBtn = document.getElementById('clear-docs-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const documentStatus = document.getElementById('document-status');
    const statusText = document.querySelector('.status-text');
    const documentCount = document.getElementById('document-count');

    // Voice Recognition Setup
    let recognition = null;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
    }

    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
    voiceBtn.addEventListener('click', toggleVoiceInput);
    clearBtn.addEventListener('click', clearChat);
    clearDocsBtn.addEventListener('click', clearDocuments);

    // Voice Recognition Events
    if (recognition) {
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            questionInput.value = transcript;
            voiceBtn.classList.remove('recording');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            voiceBtn.classList.remove('recording');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            showNotification('Voice recognition error: ' + event.error, 'error');
        };

        recognition.onend = function() {
            voiceBtn.classList.remove('recording');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        };
    }

    // Functions
    function sendMessage() {
        const question = questionInput.value.trim();
        if (!question) return;

        // Add user message
        addMessage('user', question);
        questionInput.value = '';

        // Show loading
        showLoading(true);

        // Send to backend
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            if (data.error) {
                addMessage('bot', `Error: ${data.error}`, 'error');
            } else {
                addMessage('bot', data.response);
            }
        })
        .catch(error => {
            showLoading(false);
            console.error('Error:', error);
            addMessage('bot', 'Sorry, I encountered an error while processing your question.', 'error');
        });
    }

    function addMessage(type, content, messageType = 'normal') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const avatar = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        let messageClass = '';
        if (messageType === 'error') {
            messageClass = 'error-message';
        }

        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-avatar">
                    ${avatar}
                </div>
                <div class="message-text ${messageClass}">
                    ${formatMessage(content)}
                </div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
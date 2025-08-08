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
                // Add cache indicator if response was cached
                let responseText = data.response;
                if (data.cached) {
                    responseText += `\n\n💾 *Cached response (${data.response_time.toFixed(2)}s)*`;
                } else {
                    responseText += `\n\n⚡ *Response time: ${data.response_time.toFixed(2)}s*`;
                }
                addMessage('bot', responseText);
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

    function formatMessage(content) {
        // Convert plain text to formatted HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/📄 \*\*From: (.*?)\*\*/g, '<div class="source-header">📄 <strong>From: $1</strong></div>')
            .replace(/---/g, '<hr>');
    }

    function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Show loading
        showLoading(true);

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            if (data.success) {
                addMessage('bot', `✅ ${data.message}`);
                updateDocumentStatus(data.document_count);
                showNotification('Document uploaded successfully!', 'success');
            } else {
                addMessage('bot', `❌ Error uploading document: ${data.error}`, 'error');
                showNotification('Error uploading document', 'error');
            }
        })
        .catch(error => {
            showLoading(false);
            console.error('Upload error:', error);
            addMessage('bot', '❌ Error uploading document. Please try again.', 'error');
            showNotification('Upload failed', 'error');
        });

        // Clear file input
        event.target.value = '';
    }

    function updateDocumentStatus(count) {
        if (count > 0) {
            statusText.textContent = 'Documents loaded';
            documentCount.textContent = count;
            clearDocsBtn.style.display = 'flex';
        } else {
            statusText.textContent = 'No documents loaded';
            documentCount.textContent = '0';
            clearDocsBtn.style.display = 'none';
        }
    }

    function clearDocuments() {
        if (confirm('Are you sure you want to clear all documents? This will remove all uploaded documents from the collection.')) {
            fetch('/clear-documents', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addMessage('bot', `🧹 ${data.message}`);
                    updateDocumentStatus(0);
                    showNotification('All documents cleared', 'success');
                } else {
                    showNotification('Error clearing documents', 'error');
                }
            })
            .catch(error => {
                console.error('Clear documents error:', error);
                showNotification('Error clearing documents', 'error');
            });
        }
    }

    function toggleVoiceInput() {
        if (!recognition) {
            showNotification('Voice recognition is not supported in your browser.', 'error');
            return;
        }

        if (voiceBtn.classList.contains('recording')) {
            recognition.stop();
        } else {
            recognition.start();
            voiceBtn.classList.add('recording');
            voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        }
    }

    function clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            chatMessages.innerHTML = `
                <div class="message bot-message">
                    <div class="message-content">
                        <div class="message-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-text">
                            <h3>Chat cleared! 🧹</h3>
                            <p>Ready for new questions. Upload documents or ask me anything!</p>
                        </div>
                    </div>
                </div>
            `;
            showNotification('Chat cleared', 'success');
        }
    }

    function showLoading(show) {
        if (show) {
            loadingOverlay.classList.remove('hidden');
        } else {
            loadingOverlay.classList.add('hidden');
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Check initial document status
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            updateDocumentStatus(data.document_count);
        })
        .catch(error => {
            console.error('Status check error:', error);
        });
}); 
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const voiceBtn = document.getElementById('voice-btn');
    const recordingIndicator = document.getElementById('recording-indicator');
    const connectionStatus = document.getElementById('connection-status');
    const currentTimeElement = document.getElementById('current-time');
    const themeToggle = document.querySelector('.theme-toggle');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    
    // State
    let isRecording = false;
    let recognition;
    let speechSynthesis = window.speechSynthesis;
    
    // Initialize the app
    function init() {
        updateCurrentTime();
        setInterval(updateCurrentTime, 60000); // Update time every minute
        setupEventListeners();
        checkConnection();
        loadThemePreference();
        
        // Initialize Web Speech API
        initSpeechRecognition();
        
        // Add welcome message if chat is empty
        if (chatBox.children.length <= 1) { // Only welcome message
            addWelcomeMessage();
        }
    }
    
    // Set up event listeners
    function setupEventListeners() {
        // Send message on button click or Enter key
        sendBtn.addEventListener('click', (e) => {
            e.preventDefault();
            handleSendMessage();
        });
        
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });
        
        // Auto-resize textarea
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = (userInput.scrollHeight) + 'px';
        });
        
        // Voice input
        voiceBtn.addEventListener('click', toggleVoiceRecognition);
        
        // Theme toggle
        themeToggle.addEventListener('click', toggleTheme);
        
        // Suggestion buttons
        suggestionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const message = e.target.textContent;
                userInput.value = message;
                userInput.focus();
            });
        });
        
        // Handle clicks on the document to close recording if clicking outside
        document.addEventListener('click', (e) => {
            if (isRecording && !e.target.closest('.icon-btn')) {
                stopVoiceRecognition();
            }
        });
    }
    
    // Initialize speech recognition
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('Speech recognition not supported in this browser');
            voiceBtn.style.display = 'none';
            return;
        }
        
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = () => {
            isRecording = true;
            voiceBtn.classList.add('active');
            recordingIndicator.classList.add('active');
            console.log('Voice recognition started');
        };
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('Voice input:', transcript);
            userInput.value = transcript;
            stopVoiceRecognition();
            handleSendMessage(transcript);
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            stopVoiceRecognition();
            addSystemMessage('Error: Could not process voice input');
        };
        
        recognition.onend = () => {
            stopVoiceRecognition();
        };
    }
    
    // Toggle voice recognition
    function toggleVoiceRecognition() {
        if (isRecording) {
            stopVoiceRecognition();
        } else {
            startVoiceRecognition();
        }
    }
    
    // Start voice recognition
    function startVoiceRecognition() {
        if (!recognition) {
            addSystemMessage('Voice recognition not available');
            return;
        }
        
        try {
            recognition.start();
        } catch (error) {
            console.error('Error starting voice recognition:', error);
            addSystemMessage('Error starting voice recognition');
        }
    }
    
    // Stop voice recognition
    function stopVoiceRecognition() {
        isRecording = false;
        if (recognition) {
            try {
                recognition.stop();
            } catch (error) {
                console.error('Error stopping recognition:', error);
            }
        }
        voiceBtn.classList.remove('active');
        recordingIndicator.classList.remove('active');
    }
    
    // Handle sending a message
    function handleSendMessage(message = null) {
        const messageText = message || userInput.value.trim();
        if (!messageText) return;
        
        // Add user message to chat
        addMessage(messageText, true);
        
        // Clear input and reset height if this is a text input
        if (!message) {
            userInput.value = '';
            userInput.style.height = 'auto';
        }
        
        // Show typing indicator
        const typingIndicator = showTypingIndicator();
        
        // Send to server
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `message=${encodeURIComponent(messageText)}`
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            if (typingIndicator && typingIndicator.parentNode) {
                typingIndicator.remove();
            }
            
            // Add assistant's response
            if (data.response) {
                addMessage(data.response, false);
                
                // Speak the response if it's not too long
                if (data.response.length < 200) {
                    speak(data.response);
                }
            } else if (data.error) {
                addSystemMessage(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Remove typing indicator
            if (typingIndicator && typingIndicator.parentNode) {
                typingIndicator.remove();
            }
            addSystemMessage('Sorry, I encountered an error. Please try again.');
        });
    }
    
    // Add a message to the chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Create a container for the message content
        const contentContainer = document.createElement('div');
        contentContainer.innerHTML = formatMessageContent(content);
        
        // Add any links to open in new tab
        const links = contentContainer.getElementsByTagName('a');
        Array.from(links).forEach(link => {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        });
        
        messageContent.appendChild(contentContainer);
        
        // Add timestamp
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(timeDiv);
        
        // Add to chat box with smooth scroll
        chatBox.appendChild(messageDiv);
        scrollToBottom();
        
        return messageDiv;
    }
    
    // Add a system message (error, info, etc.)
    function addSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        messageDiv.appendChild(messageContent);
        chatBox.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        // Remove any existing typing indicators
        const existingIndicators = document.querySelectorAll('.typing-indicator');
        existingIndicators.forEach(indicator => indicator.remove());
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        
        // Add typing dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dot.className = 'typing-dot';
            typingDiv.appendChild(dot);
        }
        
        // Add to chat box
        chatBox.appendChild(typingDiv);
        scrollToBottom();
        
        return typingDiv;
    }
    
    // Format message content (URLs, line breaks, etc.)
    function formatMessageContent(content) {
        if (!content) return '';
        
        // Escape HTML to prevent XSS
        let escapedContent = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Replace URLs with clickable links
        let formattedContent = escapedContent.replace(
            /(https?:\/\/[^\s]+)/g, 
            url => `<a href="${url}">${url}</a>`
        );
        
        // Replace newlines with <br>
        formattedContent = formattedContent.replace(/\n/g, '<br>');
        
        return formattedContent;
    }
    
    // Speak text using the Web Speech API
    function speak(text) {
        if (!text || !speechSynthesis) return;
        
        // Cancel any ongoing speech
        speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Set voice if available
        const voices = speechSynthesis.getVoices();
        if (voices.length > 0) {
            // Try to find a natural-sounding voice
            const preferredVoice = voices.find(voice => 
                voice.lang.includes('en') && voice.name.includes('Natural')
            );
            
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            } else if (voices[0]) {
                utterance.voice = voices[0];
            }
        }
        
        // Set speech properties
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Speak
        speechSynthesis.speak(utterance);
    }
    
    // Scroll chat to bottom
    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    // Update current time in the status bar
    function updateCurrentTime() {
        if (currentTimeElement) {
            currentTimeElement.textContent = new Date().toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
    }
    
    // Check server connection
    function checkConnection() {
        fetch('/')
            .then(() => {
                connectionStatus.className = 'connected';
                connectionStatus.title = 'Connected to server';
            })
            .catch(() => {
                connectionStatus.className = 'disconnected';
                connectionStatus.title = 'Disconnected from server';
            });
    }
    
    // Toggle between light and dark theme
    function toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Update theme
        html.setAttribute('data-theme', newTheme);
        
        // Update icon
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
        
        // Save preference
        localStorage.setItem('theme', newTheme);
    }
    
    // Load user's theme preference
    function loadThemePreference() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // Update icon
        const icon = themeToggle?.querySelector('i');
        if (icon) {
            icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
    
    // Add welcome message
    function addWelcomeMessage() {
        const welcomeMessage = `Hello! I'm your AI assistant. How can I help you today?`;
        
        // Add welcome message
        addMessage(welcomeMessage, false);
        scrollToBottom();
    }
    
    // Initialize the app
    init();
    
    // Initialize speech synthesis voices when they become available
    if (speechSynthesis && speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = function() {
            // Voices are now available
        };
    }
});

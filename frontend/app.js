// Global Auth Interceptor
(function() {
    const originalFetch = window.fetch;
    window.fetch = async function (url, options = {}) {
        const token = localStorage.getItem('auth_token');
        if (token) {
            options.headers = options.headers || {};
            if (options.headers instanceof Headers) {
                options.headers.set('Authorization', `Bearer ${token}`);
            } else if (Array.isArray(options.headers)) {
                const hasAuth = options.headers.some(h => h[0].toLowerCase() === 'authorization');
                if (!hasAuth) {
                    options.headers.push(['Authorization', `Bearer ${token}`]);
                }
            } else {
                options.headers['Authorization'] = `Bearer ${token}`;
            }
        }
        const response = await originalFetch(url, options);
        if (response.status === 401 && !url.includes('/api/auth/')) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_email');
            const authOverlay = document.getElementById('auth-overlay');
            if (authOverlay) authOverlay.style.display = 'flex';
        }
        return response;
    };
})();

// State Variables
let currentThreadId = null;
let conversations = [];

// DOM Elements
const conversationsList = document.getElementById('conversations-list');
const newChatBtn = document.getElementById('new-chat-btn');
const activeChatTitle = document.getElementById('active-chat-title');
const messagesContainer = document.getElementById('messages-container');
const welcomeScreen = document.getElementById('welcome-screen');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const attachBtn = document.getElementById('attach-btn');
const fileInput = document.getElementById('file-input');
const attachmentPreview = document.getElementById('attachment-preview');

// Rename Modal DOM
const renameModal = document.getElementById('rename-modal');
const renameInput = document.getElementById('rename-input');
const renameCancelBtn = document.getElementById('rename-cancel-btn');
const renameSaveBtn = document.getElementById('rename-save-btn');
let threadToRename = null;

// Abort Controller for streams
let chatAbortController = null;

// Initial Setup
document.addEventListener('DOMContentLoaded', () => {
    // Auth DOM Elements
    const authOverlay = document.getElementById('auth-overlay');
    const authForm = document.getElementById('auth-form');
    const authTitle = document.getElementById('auth-title');
    const authSubtitle = document.getElementById('auth-subtitle');
    const authEmailInput = document.getElementById('auth-email');
    const authPasswordInput = document.getElementById('auth-password');
    const authSubmitBtn = document.getElementById('auth-submit-btn');
    const authSwitchBtn = document.getElementById('auth-switch-btn');
    const authSwitchText = document.getElementById('auth-switch-text');
    const authErrorMsg = document.getElementById('auth-error-msg');
    const togglePasswordBtn = document.getElementById('toggle-password-btn');
    
    const logoutBtn = document.getElementById('logout-btn');
    const userNameDisplay = document.getElementById('user-name');
    const userAvatarDisplay = document.getElementById('user-avatar');

    let isLoginMode = true;

    // Toggle Password Visibility
    togglePasswordBtn.addEventListener('click', () => {
        const type = authPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        authPasswordInput.setAttribute('type', type);
        const icon = togglePasswordBtn.querySelector('i');
        if (type === 'password') {
            icon.className = 'fa-regular fa-eye';
        } else {
            icon.className = 'fa-regular fa-eye-slash';
        }
    });

    // Switch between Login and Register Mode
    authSwitchBtn.addEventListener('click', (e) => {
        e.preventDefault();
        isLoginMode = !isLoginMode;
        authErrorMsg.textContent = '';
        authErrorMsg.style.color = '#ef4444';
        if (isLoginMode) {
            authTitle.textContent = 'Welcome Back';
            authSubtitle.textContent = 'Log in to manage your chats privately.';
            authSubmitBtn.textContent = 'Log In';
            authSwitchText.textContent = "Don't have an account?";
            authSwitchBtn.textContent = 'Sign Up';
        } else {
            authTitle.textContent = 'Create Account';
            authSubtitle.textContent = 'Sign up to keep your conversations secure.';
            authSubmitBtn.textContent = 'Sign Up';
            authSwitchText.textContent = 'Already have an account?';
            authSwitchBtn.textContent = 'Log In';
        }
    });

    // Handle Form Submit (Login or Register)
    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        authErrorMsg.textContent = '';
        authErrorMsg.style.color = '#ef4444';
        const emailVal = authEmailInput.value.trim();
        const passwordVal = authPasswordInput.value;

        const endpoint = isLoginMode ? '/api/auth/login' : '/api/auth/register';
        
        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: emailVal, password: passwordVal })
            });
            const data = await res.json();
            
            if (!res.ok) {
                authErrorMsg.textContent = data.detail || 'Authentication failed.';
                return;
            }

            if (isLoginMode) {
                // Save credentials and load chats
                localStorage.setItem('auth_token', data.token);
                localStorage.setItem('user_email', data.email);
                
                userNameDisplay.textContent = data.email;
                userAvatarDisplay.textContent = data.email.substring(0, 2).toUpperCase();
                
                authOverlay.style.display = 'none';
                loadConversations();
            } else {
                // Switch to login mode
                isLoginMode = true;
                authTitle.textContent = 'Welcome Back';
                authSubtitle.textContent = 'Log in to manage your chats privately.';
                authSubmitBtn.textContent = 'Log In';
                authSwitchText.textContent = "Don't have an account?";
                authSwitchBtn.textContent = 'Sign Up';
                authErrorMsg.style.color = '#10b981'; // Green color for success
                authErrorMsg.textContent = 'Registration successful! Please log in.';
                authPasswordInput.value = '';
                authPasswordInput.setAttribute('type', 'password');
                togglePasswordBtn.querySelector('i').className = 'fa-regular fa-eye';
            }
        } catch (err) {
            authErrorMsg.textContent = 'Connection error. Please try again.';
        }
    });

    // Handle Logout
    logoutBtn.addEventListener('click', async () => {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
        } catch (err) {}
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_email');
        location.reload();
    });

    // Initial auth state check
    const token = localStorage.getItem('auth_token');
    const userEmail = localStorage.getItem('user_email');
    if (!token) {
        authOverlay.style.display = 'flex';
    } else {
        authOverlay.style.display = 'none';
        userNameDisplay.textContent = userEmail;
        userAvatarDisplay.textContent = userEmail.substring(0, 2).toUpperCase();
        loadConversations();
    }
    
    newChatBtn.addEventListener('click', startNewChat);
    chatForm.addEventListener('submit', handleMessageSubmit);
    
    // PDF Attach button → open file picker
    attachBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelected);

    // Auto-growing textarea & Enter-to-Submit behavior
    userInput.addEventListener('input', autoGrowTextarea);
    userInput.addEventListener('keydown', handleTextareaKeydown);
    
    // Suggestion Cards listener
    document.querySelectorAll('.suggestion-card').forEach(card => {
        card.addEventListener('click', () => {
            const query = card.dataset.query;
            if (query) {
                userInput.value = query;
                autoGrowTextarea();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    });
    
    // Modal Listeners
    renameCancelBtn.addEventListener('click', closeRenameModal);
    renameSaveBtn.addEventListener('click', saveRename);
    
    // Close modal when clicking outside
    renameModal.addEventListener('click', (e) => {
        if (e.target === renameModal) closeRenameModal();
    });
});

// ── PDF Upload Logic ────────────────────────────────────────────────
async function handleFileSelected(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Only PDF files are supported.');
        fileInput.value = '';
        return;
    }
    
    fileInput.value = '';
    
    // If no active conversation session, create one first
    if (!currentThreadId) {
        try {
            const res = await fetch('/api/conversations', { method: 'POST' });
            const data = await res.json();
            currentThreadId = data.thread_id;
            
            // De-select other items and reload list
            loadConversations();
        } catch (err) {
            console.error('Failed to create session for upload:', err);
            alert('Failed to initialize conversation for upload.');
            return;
        }
    }
    
    const pillId = `upload-${Date.now()}`;
    showPill(file.name, 'uploading', pillId);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('thread_id', currentThreadId);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const responseText = await res.text();
        let data;
        try {
            data = JSON.parse(responseText);
        } catch {
            alert(`Upload failed (HTTP ${res.status}):\n${responseText.substring(0, 400)}`);
            removePill(pillId);
            return;
        }
        if (res.ok) {
            showPill(file.name, 'success', pillId);
        } else {
            alert(`Upload failed: ${data.detail || 'Unknown error'}`);
            removePill(pillId);
        }
    } catch (err) {
        console.error('Upload error:', err);
        alert(`Upload failed: ${err.message}`);
        removePill(pillId);
    }
}

function showPill(filename, cssClass, pillId) {
    // Remove existing pill with same id
    const existing = document.getElementById(`pill-${pillId}`);
    if (existing) existing.remove();

    const pill = document.createElement('div');
    pill.className = `attachment-pill ${cssClass}`;
    pill.id = `pill-${pillId}`;
    pill.innerHTML = `
        <i class="fa-regular fa-file-pdf"></i>
        <span>${filename}</span>
        <span class="pill-remove" onclick="removePill('${pillId}')"><i class="fa-solid fa-xmark"></i></span>
    `;
    attachmentPreview.appendChild(pill);
}

window.removePill = function(pillId) {
    const pill = document.getElementById(`pill-${pillId}`);
    if (pill) pill.remove();
};

// Auto grow textarea
function autoGrowTextarea() {
    userInput.style.height = '24px';
    userInput.style.height = (userInput.scrollHeight - 4) + 'px';
}

// Handle keypresses in the textarea
function handleTextareaKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
}

// Load Sidebar Threads
async function loadConversations() {
    try {
        const response = await fetch('/api/conversations');
        if (!response.ok) throw new Error('Failed to load conversations');
        
        conversations = await response.json();
        renderConversations();
    } catch (err) {
        console.error('Error loading conversations:', err);
        conversationsList.innerHTML = '<p class="error-msg" style="padding: 10px; font-size: 0.8rem; color: var(--text-secondary);">Error loading chats</p>';
    }
}

// Render Threads list in Sidebar
function renderConversations() {
    if (conversations.length === 0) {
        conversationsList.innerHTML = '<p class="no-threads-msg" style="font-size: 0.75rem; color: #676767; text-align: center; margin-top: 10px;">No chats yet</p>';
        return;
    }
    
    conversationsList.innerHTML = '';
    conversations.forEach(convo => {
        const convoItem = document.createElement('div');
        convoItem.className = `convo-item ${convo.thread_id === currentThreadId ? 'active' : ''}`;
        convoItem.dataset.id = convo.thread_id;
        
        convoItem.innerHTML = `
            <div class="convo-info">
                <i class="fa-regular fa-message"></i>
                <span class="convo-title" title="${convo.title}">${convo.title}</span>
            </div>
            <div class="convo-actions">
                <button class="btn-icon rename-btn" title="Rename"><i class="fa-solid fa-pen"></i></button>
                <button class="btn-icon delete-btn" title="Delete"><i class="fa-solid fa-trash-can"></i></button>
            </div>
        `;
        
        // Open Thread click
        convoItem.addEventListener('click', (e) => {
            if (e.target.closest('.btn-icon')) return;
            openConversation(convo.thread_id);
        });
        
        // Rename click
        convoItem.querySelector('.rename-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            openRenameModal(convo.thread_id, convo.title);
        });
        
        // Delete click
        convoItem.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteConversation(convo.thread_id);
        });
        
        conversationsList.appendChild(convoItem);
    });
}

// Open Specific Conversation
async function openConversation(threadId) {
    currentThreadId = threadId;
    
    // Highlight active in sidebar
    document.querySelectorAll('.convo-item').forEach(item => {
        item.classList.toggle('active', item.dataset.id === threadId);
    });
    
    // Load messages
    messagesContainer.innerHTML = '<div class="loading-spinner"></div>';
    welcomeScreen.style.display = 'none';
    
    try {
        const response = await fetch(`/api/conversations/${threadId}/messages`);
        if (!response.ok) throw new Error('Failed to fetch messages');
        
        const data = await response.json();
        
        // Update header if exists
        const headerTitle = document.querySelector('.model-badge');
        if (headerTitle) {
            headerTitle.innerHTML = `ChatGPT - ${data.title || 'Conversation'} <i class="fa-solid fa-chevron-down"></i>`;
        }
        
        messagesContainer.innerHTML = '';
        if (data.messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="no-messages-msg" style="text-align: center; color: var(--text-secondary); margin-top: 50px; font-size: 0.9rem;">
                    No messages in this chat.
                </div>`;
        } else {
            data.messages.forEach(msg => appendMessage(msg.role, msg.content));
        }
        scrollToBottom();
    } catch (err) {
        console.error(err);
        messagesContainer.innerHTML = '<p class="error-msg">Error loading messages</p>';
    }
}

// Initialize New Chat Session
function startNewChat() {
    if (chatAbortController) {
        chatAbortController.abort();
        chatAbortController = null;
    }
    
    currentThreadId = null;
    pendingUploadFile = null;
    attachmentPreview.innerHTML = '';
    
    const headerTitle = document.querySelector('.model-badge');
    if (headerTitle) {
        headerTitle.innerHTML = `RBot AI <i class="fa-solid fa-chevron-down"></i>`;
    }
    
    messagesContainer.innerHTML = '';
    welcomeScreen.style.display = 'flex';
    messagesContainer.appendChild(welcomeScreen);
    
    // De-select active conversations in the sidebar
    document.querySelectorAll('.convo-item').forEach(item => {
        item.classList.remove('active');
    });
    
    userInput.value = '';
    autoGrowTextarea();
    userInput.focus();
}

// Handle Message submission and SSE Streaming
async function handleMessageSubmit(e) {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;
    
    // Check for uploaded files in preview area
    const uploadedPills = attachmentPreview.querySelectorAll('.attachment-pill.success');
    let attachmentPrefix = "";
    if (uploadedPills.length > 0) {
        const filenames = Array.from(uploadedPills).map(pill => {
            return pill.querySelector('span').textContent.trim();
        });
        attachmentPrefix = `[Attachment: ${filenames.join(', ')}]`;
    }
    
    const fullMessage = attachmentPrefix ? `${attachmentPrefix}\n\n${text}` : text;
    
    userInput.value = '';
    autoGrowTextarea();
    attachmentPreview.innerHTML = '';
    
    // Remove welcome screen if it's there
    if (welcomeScreen.parentNode === messagesContainer) {
        messagesContainer.innerHTML = '';
    }
    
    // 1. Append User Message
    appendMessage('user', fullMessage);
    scrollToBottom();
    
    // 2. Append Typing Indicator
    const typingIndicator = appendTypingIndicator();
    scrollToBottom();
    
    try {
        if (chatAbortController) {
            chatAbortController.abort();
        }
        chatAbortController = new AbortController();
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                thread_id: currentThreadId,
                message: fullMessage
            }),
            signal: chatAbortController.signal
        });
        
        if (!response.ok) throw new Error('Failed to initialize stream');
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        let assistantRow = null;
        let assistantContent = '';
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (let line of lines) {
                if (line.startsWith('event: ')) {
                    const eventType = line.replace('event: ', '').trim();
                } else if (line.startsWith('data: ')) {
                    let dataStr = line.slice(6).trim();
                    
                    if (dataStr === 'done') {
                        break;
                    }
                    
                    try {
                        const parsed = JSON.parse(dataStr);
                        if (parsed.thread_id) {
                            currentThreadId = parsed.thread_id;
                            const headerTitle = document.querySelector('.model-badge');
                            if (headerTitle) {
                                headerTitle.innerHTML = `RBot - ${parsed.title} <i class="fa-solid fa-chevron-down"></i>`;
                            }
                        } else if (parsed.content !== undefined) {
                            // Remove typing indicator
                            if (typingIndicator && typingIndicator.parentNode) {
                                typingIndicator.remove();
                            }
                            
                            if (!assistantRow) {
                                assistantRow = appendMessage('assistant', '');
                            }
                            
                            assistantContent += parsed.content;
                            renderContentMarkdown(assistantRow.querySelector('.message-content-box'), assistantContent);
                            scrollToBottom();
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE line:', e, dataStr);
                    }
                }
            }
        }
        
        // Refresh sidebar
        loadConversations();
        
    } catch (err) {
        if (err.name === 'AbortError') {
            console.log('Stream aborted');
            return;
        }
        console.error('Streaming error:', err);
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.remove();
        }
        appendMessage('assistant', 'Sorry, I encountered an error while processing your request.');
        scrollToBottom();
    }
}

// Append message node in ChatGPT structure
function appendMessage(role, content) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    
    const avatarContent = role === 'user' ? 'U' : '<i class="fa-solid fa-circle-nodes"></i>';
    
    row.innerHTML = `
        <div class="message-wrapper">
            <div class="message-avatar">
                ${avatarContent}
            </div>
            <div class="message-content-box"></div>
        </div>
    `;
    
    messagesContainer.appendChild(row);
    
    const contentBox = row.querySelector('.message-content-box');
    
    let displayContent = content;
    if (role === 'user' && content.startsWith('[Attachment:')) {
        const match = content.match(/^\[Attachment:\s*(.+?)\](?:\n\n)?([\s\S]*)$/);
        if (match) {
            const filesStr = match[1];
            displayContent = match[2];
            
            const files = filesStr.split(',').map(f => f.trim());
            files.forEach(filename => {
                const card = document.createElement('div');
                card.className = 'message-attachment-card';
                card.innerHTML = `
                    <i class="fa-regular fa-file-pdf"></i>
                    <span class="attachment-name">${filename}</span>
                `;
                contentBox.appendChild(card);
            });
        }
    }
    
    if (role === 'user') {
        const textNode = document.createElement('div');
        textNode.className = 'message-text';
        textNode.textContent = displayContent;
        contentBox.appendChild(textNode);
    } else {
        renderContentMarkdown(contentBox, displayContent);
    }
    
    return row;
}

// Append Typing indicator bubble inside message wrapper
function appendTypingIndicator() {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.innerHTML = `
        <div class="message-wrapper">
            <div class="message-avatar">
                <i class="fa-solid fa-circle-nodes"></i>
            </div>
            <div class="message-content-box">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(row);
    return row;
}

// Render markdown content using marked.js library
function renderContentMarkdown(container, rawText) {
    if (!rawText) {
        container.innerHTML = '';
        return;
    }

    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true
        });
        container.innerHTML = marked.parse(rawText);
        styleCodeBlocks(container);
    } else {
        container.textContent = rawText;
    }
}

// Post-process pre-wrapped code tags to apply block headers and copy actions
function styleCodeBlocks(container) {
    const preElements = container.querySelectorAll('pre');
    preElements.forEach(pre => {
        if (pre.parentElement.classList.contains('code-block-container')) return;
        
        const code = pre.querySelector('code');
        if (!code) return;
        
        let lang = 'code';
        const classes = code.className.split(' ');
        const langClass = classes.find(c => c.startsWith('language-'));
        if (langClass) {
            lang = langClass.replace('language-', '');
        }
        
        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-container';
        
        const header = document.createElement('div');
        header.className = 'code-header';
        header.innerHTML = `
            <span>${lang}</span>
            <button class="copy-btn" onclick="copyToClipboard(this)">
                <i class="fa-regular fa-clipboard"></i> Copy code
            </button>
        `;
        
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(header);
        wrapper.appendChild(pre);
    });
}

// Clipboard copying utility
window.copyToClipboard = function(btn) {
    const codeElement = btn.closest('.code-block-container').querySelector('code');
    if (!codeElement) return;
    
    navigator.clipboard.writeText(codeElement.textContent).then(() => {
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        setTimeout(() => {
            btn.innerHTML = originalHTML;
        }, 2000);
    }).catch(err => {
        console.error('Copy failed:', err);
    });
};

// Delete Thread Handler
async function deleteConversation(threadId) {
    if (!confirm('Are you sure you want to delete this conversation?')) return;
    
    // Optimistically update UI to fix "icon won't work" feeling if fetch is slow
    const convoEl = document.querySelector(`.convo-item[data-id="${threadId}"]`);
    if (convoEl) convoEl.style.display = 'none';

    try {
        const response = await fetch(`/api/conversations/${threadId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete');
        
        if (currentThreadId === threadId) {
            startNewChat();
        }
        
        loadConversations();
    } catch (err) {
        console.error(err);
        if (convoEl) convoEl.style.display = 'flex'; // Revert on failure
        alert('Failed to delete conversation.');
    }
}

// Rename Modal Handling
function openRenameModal(threadId, currentTitle) {
    threadToRename = threadId;
    renameInput.value = currentTitle;
    renameModal.classList.add('active');
    renameInput.focus();
}

function closeRenameModal() {
    renameModal.classList.remove('active');
    threadToRename = null;
}

async function saveRename() {
    const newTitle = renameInput.value.trim();
    if (!newTitle || !threadToRename) return;
    
    try {
        const response = await fetch(`/api/conversations/${threadToRename}/rename`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        
        if (!response.ok) throw new Error('Failed to rename');
        
        if (currentThreadId === threadToRename) {
            const headerTitle = document.querySelector('.model-badge');
            if (headerTitle) {
                headerTitle.innerHTML = `ChatGPT - ${newTitle} <i class="fa-solid fa-chevron-down"></i>`;
            }
        }
        
        closeRenameModal();
        loadConversations();
    } catch (err) {
        console.error(err);
    }
}

// Helpers
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

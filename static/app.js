const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatContainer = document.getElementById('chat-container');
const sendBtn = document.getElementById('send-btn');
const agentStatus = document.getElementById('agent-status');
const statusDot = document.querySelector('.status-dot');
const newChatBtn = document.getElementById('new-chat-btn');

let chatHistory = [];
let typingIndicator = null;

// Initialize Lucide Icons
lucide.createIcons();

// Initialize particles.js
particlesJS('particles-js',
  {
    "particles": {
      "number": {
        "value": 60,
        "density": { "enable": true, "value_area": 800 }
      },
      "color": { "value": "#06b6d4" },
      "shape": { "type": "circle" },
      "opacity": {
        "value": 0.3,
        "random": false
      },
      "size": {
        "value": 3,
        "random": true
      },
      "line_linked": {
        "enable": true,
        "distance": 150,
        "color": "#8b5cf6",
        "opacity": 0.2,
        "width": 1
      },
      "move": {
        "enable": true,
        "speed": 1,
        "direction": "none",
        "random": false,
        "straight": false,
        "out_mode": "out",
        "bounce": false,
      }
    },
    "interactivity": {
      "detect_on": "canvas",
      "events": {
        "onhover": { "enable": true, "mode": "grab" },
        "onclick": { "enable": true, "mode": "push" },
        "resize": true
      },
      "modes": {
        "grab": { "distance": 140, "line_linked": { "opacity": 0.5 } },
        "push": { "particles_nb": 4 }
      }
    },
    "retina_detect": true
  }
);

// Ensure suggestions fill input
window.setInput = (text) => {
    userInput.value = text;
    userInput.focus();
};

// Reset Chat
newChatBtn.addEventListener('click', () => {
    chatHistory = [];
    chatContainer.innerHTML = `
        <div class="welcome-message">
            <h2>Welcome to AgentForge</h2>
            <p>I am a tool-calling AI agent. I can search the web, scrape urls, execute Python code, and read/write files.</p>
            <div class="suggestion-chips">
                <button class="chip" onclick="setInput('Research the latest advancements in AI agents and write a summary to summary.txt')">Research & Summarize</button>
                <button class="chip" onclick="setInput('Write a python script that uses a loop and print the code.')">Code Example</button>
                <button class="chip" onclick="setInput('List the files in the workspace.')">List Files</button>
            </div>
        </div>
    `;
    userInput.value = '';
    setStatus('Ready', '');
});

function showTyping() {
    if (!typingIndicator) {
        typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        chatContainer.appendChild(typingIndicator);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function removeTyping() {
    if (typingIndicator) {
        typingIndicator.remove();
        typingIndicator = null;
    }
}

// Markdown config with highlight.js — marked v12 uses marked.use()
marked.use({
    breaks: true,
    gfm: true
});

// Override renderer for code blocks to use highlight.js and add Copy button
const renderer = new marked.Renderer();
renderer.code = function(code, lang) {
    const language = (lang && hljs.getLanguage(lang)) ? lang : 'plaintext';
    const codeText = typeof code === 'object' ? code.text : code;
    const highlighted = hljs.highlight(codeText, { language }).value;
    return `<div class="code-block-wrapper" style="position: relative;">
        <button class="copy-btn" onclick="navigator.clipboard.writeText(decodeURIComponent('${encodeURIComponent(codeText)}')); this.textContent='Copied!'; setTimeout(()=>this.textContent='Copy', 2000)" style="position: absolute; right: 8px; top: 8px; padding: 4px 8px; background: rgba(255,255,255,0.1); border: none; border-radius: 4px; color: #fff; cursor: pointer; font-size: 12px; z-index: 10;">Copy</button>
        <pre><code class="hljs language-${language}">${highlighted}</code></pre>
    </div>`;
};
marked.use({ renderer });

function addMessage(content, type, isStream = false) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    if (!isStream) {
        div.innerHTML = marked.parse(content);
    }
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return div;
}

window.toggleTool = function(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.toggle('expanded');
    }
};

function addToolCall(toolName, args) {
    const id = 'tool-' + Date.now();
    const div = document.createElement('div');
    div.className = 'tool-call';
    div.id = id;
    
    let argsStr = '';
    if (typeof args === 'object') {
        argsStr = JSON.stringify(args, null, 2);
    } else {
        argsStr = args;
    }

    div.innerHTML = `
        <div class="tool-header hover-3d" onclick="toggleTool('${id}')">
            <div class="tool-header-left">
                <i data-lucide="chevron-down" class="tool-toggle-icon"></i>
                <span><i data-lucide="wrench" style="width: 16px; height: 16px; margin-right: 4px; vertical-align: middle;"></i>${toolName}</span>
            </div>
            <span class="tool-status">Running...</span>
        </div>
        <div class="tool-content">
            <div class="tool-args">${argsStr}</div>
            <div class="tool-result" style="display: none;"></div>
        </div>
    `;
    
    chatContainer.appendChild(div);
    lucide.createIcons({ root: div });
    
    // Initialize VanillaTilt on the new element
    const toolHeader = div.querySelector('.tool-header');
    if (window.VanillaTilt) {
        VanillaTilt.init(toolHeader, { max: 10, speed: 400, glare: true, "max-glare": 0.1 });
    }
    
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return id;
}

function updateToolResult(id, result) {
    const toolCall = document.getElementById(id);
    if (toolCall) {
        const resultDiv = toolCall.querySelector('.tool-result');
        const statusSpan = toolCall.querySelector('.tool-status');
        
        statusSpan.textContent = 'Completed';
        statusSpan.style.color = '#10b981'; // accent color
        
        resultDiv.textContent = result;
        resultDiv.style.display = 'block';
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function setStatus(text, type) {
    agentStatus.textContent = text;
    statusDot.className = 'status-dot';
    if (type) statusDot.classList.add(type);
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const text = userInput.value.trim();
    if (!text) return;
    
    // Hide welcome message if present
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.style.display = 'none';

    addMessage(text, 'user-message');
    chatHistory.push({ role: 'user-message', content: text });
    
    userInput.value = '';
    sendBtn.disabled = true;
    setStatus('Agent working...', 'working');
    showTyping();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-API-Key': 'default-dev-key'
            },
            body: JSON.stringify({ message: text, history: chatHistory.slice(0, -1) })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        
        let currentToolId = null;
        let streamingDiv = null;
        let finalAnswerAcc = "";
        let buffer = ""; // Buffer to handle partial SSE lines across network chunks

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // Process all complete lines in the buffer
            let eolIndex;
            while ((eolIndex = buffer.indexOf('\n')) >= 0) {
                const line = buffer.slice(0, eolIndex).trim();
                buffer = buffer.slice(eolIndex + 1);
                
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        
                        if (data.type === 'tool_call') {
                            removeTyping();
                            currentToolId = addToolCall(data.tool, data.args);
                            chatHistory.push({ role: 'model-function-call', name: data.tool, args: data.args });
                            setStatus(`Running ${data.tool}...`, 'working');
                        } 
                        else if (data.type === 'tool_result') {
                            if (currentToolId) {
                                updateToolResult(currentToolId, data.result);
                                currentToolId = null;
                            }
                            chatHistory.push({ role: 'user-function-response', name: data.tool, response: { result: data.result } });
                            setStatus('Agent thinking...', 'working');
                            showTyping();
                        }
                        else if (data.type === 'final_answer_chunk') {
                            removeTyping();
                            if (!streamingDiv) {
                                streamingDiv = addMessage('', 'agent-message', true);
                            }
                            finalAnswerAcc += data.content;
                            // Parse markdown live while streaming
                            streamingDiv.innerHTML = marked.parse(finalAnswerAcc);
                            // Highlight code blocks inside the streaming div
                            streamingDiv.querySelectorAll('pre code').forEach((block) => {
                                hljs.highlightElement(block);
                            });
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                        }
                        else if (data.type === 'final_answer') {
                            removeTyping();
                            if (!streamingDiv && finalAnswerAcc === "") {
                                // Fallback if no chunks were sent
                                addMessage(data.content, 'agent-message');
                                chatHistory.push({ role: 'agent-message', content: data.content });
                            } else {
                                chatHistory.push({ role: 'agent-message', content: finalAnswerAcc });
                            }
                        }
                        else if (data.type === 'error') {
                            removeTyping();
                            addMessage(`⚠️ ${data.content}`, 'error-message');
                        }
                        else if (data.type === 'status') {
                            setStatus(data.content, 'working');
                        }
                    } catch (e) {
                        console.warn("Could not parse SSE line:", line, e);
                    }
                }
            }
        }
        
    } catch (error) {
        removeTyping();
        addMessage('Failed to connect to the agent server.', 'error-message');
        console.error(error);
    } finally {
        removeTyping();
        sendBtn.disabled = false;
        setStatus('Ready', '');
        userInput.focus();
    }
});

// Initialize VanillaTilt for existing elements on load
document.addEventListener('DOMContentLoaded', () => {
    if (window.VanillaTilt) {
        VanillaTilt.init(document.querySelectorAll(".hover-3d"), {
            max: 10,
            speed: 400,
            glare: true,
            "max-glare": 0.1
        });
    }
});

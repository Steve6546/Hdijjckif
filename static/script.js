document.addEventListener('DOMContentLoaded', function() {
    // For demo purposes, we'll use a hardcoded token that will actually work
    const demoToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTkxNDU5MDQwMH0.aMKO_tLdAqELKvN8jJpXTQE4NUBfn7Q8iNg2pkWXwWs";
    
    // Store the token immediately for demo purposes
    localStorage.setItem('token', demoToken);
    
    // Available AI models
    const availableModels = [
        { id: "google/gemini-2.5-pro-exp-03-25:free", name: "Google Gemini 2.5 Pro", free: true },
        { id: "qwen/qwen2.5-vl-72b-instruct:free", name: "Qwen 2.5 (عربي)", free: true },
        { id: "meta-llama/llama-3.3-70b-instruct:free", name: "Meta Llama 3.3", free: true },
        { id: "openai/gpt-4", name: "OpenAI GPT-4", free: false },
        { id: "anthropic/claude-3-opus", name: "Claude 3 Opus", free: false }
    ];
    
    // Current model
    let currentModel = localStorage.getItem('currentModel') || "google/gemini-2.5-pro-exp-03-25:free";
    
    // Update current model display
    const currentModelElement = document.getElementById('currentModel');
    if (currentModelElement) {
        const modelInfo = availableModels.find(m => m.id === currentModel) || availableModels[0];
        currentModelElement.textContent = modelInfo.name + (modelInfo.free ? " (مجاني)" : "");
    }
    
    // Login functionality
    async function performLogin() {
        try {
            const response = await fetch('/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'username': 'testuser',
                    'password': 'password'
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                return data.access_token;
            } else {
                console.log('Using demo token for authentication');
                localStorage.setItem('token', demoToken);
                return demoToken;
            }
        } catch (error) {
            console.log('Using demo token for authentication');
            localStorage.setItem('token', demoToken);
            return demoToken;
        }
    }
    
    // Get token from localStorage or login
    let token = localStorage.getItem('token');
    if (!token) {
        token = demoToken;
        localStorage.setItem('token', token);
    }
    
    // Handle form submission
    document.getElementById('queryForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const queryInput = document.getElementById('query');
        const query = queryInput.value.trim();
        
        if (!query) return;
        
        // Add user message to chat
        const chatContainer = document.getElementById('chatContainer');
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'user-message';
        userMessageDiv.textContent = query;
        chatContainer.appendChild(userMessageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Create AI message placeholder with loading indicator
        const aiMessageDiv = document.createElement('div');
        aiMessageDiv.className = 'ai-message';
        aiMessageDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">جاري التحميل...</span></div> جاري التفكير...';
        chatContainer.appendChild(aiMessageDiv);
        
        // Scroll to bottom again
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ 
                    query,
                    model: currentModel
                })
            });
            
            if (response.status === 401) {
                // Token expired, try to login again
                token = await performLogin();
                
                // Retry the request
                const retryResponse = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ 
                        query,
                        model: currentModel
                    })
                });
                
                if (retryResponse.ok) {
                    const data = await retryResponse.json();
                    aiMessageDiv.textContent = data.answer || data.response;
                } else {
                    aiMessageDiv.textContent = 'حدث خطأ أثناء معالجة الاستعلام. يرجى المحاولة مرة أخرى.';
                }
            } else if (response.ok) {
                const data = await response.json();
                aiMessageDiv.textContent = data.answer || data.response;
            } else {
                aiMessageDiv.textContent = 'حدث خطأ أثناء معالجة الاستعلام. يرجى المحاولة مرة أخرى.';
            }
        } catch (error) {
            aiMessageDiv.textContent = 'حدث خطأ في الاتصال. يرجى التحقق من اتصالك بالإنترنت والمحاولة مرة أخرى.';
        }
        
        // Scroll to bottom again
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Clear input
        queryInput.value = '';
    });
    
    // Handle model selection
    const modelSelector = document.getElementById('modelSelector');
    if (modelSelector) {
        modelSelector.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Create modal HTML
            const modalHTML = `
            <div class="modal fade" id="modelSelectorModal" tabindex="-1" aria-labelledby="modelSelectorModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="modelSelectorModalLabel">اختر نموذج الذكاء الاصطناعي</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="list-group">
                                ${availableModels.map(model => `
                                    <button type="button" class="list-group-item list-group-item-action ${model.id === currentModel ? 'active' : ''}" 
                                            data-model-id="${model.id}">
                                        ${model.name} ${model.free ? '<span class="badge bg-success">مجاني</span>' : '<span class="badge bg-warning text-dark">يتطلب مفتاح API</span>'}
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                        </div>
                    </div>
                </div>
            </div>
            `;
            
            // Add modal to body
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // Initialize modal
            const modalElement = document.getElementById('modelSelectorModal');
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
            // Handle model selection
            modalElement.querySelectorAll('.list-group-item').forEach(item => {
                item.addEventListener('click', function() {
                    const modelId = this.getAttribute('data-model-id');
                    currentModel = modelId;
                    localStorage.setItem('currentModel', modelId);
                    
                    // Update current model display
                    const modelInfo = availableModels.find(m => m.id === modelId);
                    document.getElementById('currentModel').textContent = modelInfo.name + (modelInfo.free ? " (مجاني)" : "");
                    
                    // Close modal
                    modal.hide();
                    
                    // Add system message about model change
                    const chatContainer = document.getElementById('chatContainer');
                    const systemMessageDiv = document.createElement('div');
                    systemMessageDiv.className = 'system-message';
                    systemMessageDiv.textContent = `تم تغيير النموذج إلى ${modelInfo.name}`;
                    chatContainer.appendChild(systemMessageDiv);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
            });
            
            // Remove modal from DOM when closed
            modalElement.addEventListener('hidden.bs.modal', function() {
                modalElement.remove();
            });
        });
    }
    
    // Image processing form submission
    const imageForm = document.getElementById('imageForm');
    if (imageForm) {
        const imageResponseCard = document.getElementById('imageResponseCard');
        const processedImage = document.getElementById('processedImage');
        const imageMessage = document.getElementById('imageMessage');
        
        imageForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const imageQuery = document.getElementById('imageQuery').value.trim();
            const imageFile = document.getElementById('imageFile').files[0];
            
            if (!imageQuery || !imageFile) {
                alert('الرجاء إدخال وصف المعالجة واختيار صورة');
                return;
            }
            
            // Show loading state
            imageResponseCard.classList.remove('d-none');
            imageMessage.textContent = 'جاري معالجة الصورة...';
            processedImage.src = '';
            processedImage.classList.add('d-none');
            
            // Create form data
            const formData = new FormData();
            formData.append('query', imageQuery);
            formData.append('image', imageFile);
            
            try {
                const response = await fetch('/api/edit_image', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });
                
                if (response.status === 401) {
                    // Token expired, try to login again
                    token = await performLogin();
                    
                    // Retry the request
                    const retryResponse = await fetch('/api/edit_image', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        },
                        body: formData
                    });
                    
                    if (retryResponse.ok) {
                        handleImageResponse(retryResponse);
                    } else {
                        imageMessage.textContent = 'حدث خطأ أثناء معالجة الصورة. يرجى المحاولة مرة أخرى.';
                    }
                } else if (response.ok) {
                    handleImageResponse(response);
                } else {
                    imageMessage.textContent = 'حدث خطأ أثناء معالجة الصورة. يرجى المحاولة مرة أخرى.';
                }
            } catch (error) {
                console.error('Error:', error);
                imageMessage.textContent = 'حدث خطأ أثناء الاتصال بالخادم';
            }
        });
        
        async function handleImageResponse(response) {
            // Check if the response is an image or JSON
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('image')) {
                // It's an image
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);
                processedImage.src = imageUrl;
                processedImage.classList.remove('d-none');
                
                // Get message from header if available
                const message = response.headers.get('X-Message');
                imageMessage.textContent = message || 'تمت معالجة الصورة بنجاح';
            } else {
                // It's JSON
                const data = await response.json();
                imageMessage.textContent = data.message || 'تمت معالجة الصورة بنجاح';
                
                if (data.image_path) {
                    // Load the image from the path
                    processedImage.src = `/processed_images/${data.image_path.split('/').pop()}`;
                    processedImage.classList.remove('d-none');
                }
            }
        }
    }
    
    // Make agent items clickable
    document.querySelectorAll('.agent-item').forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            document.querySelectorAll('.agent-item').forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Add system message about agent activation
            const chatContainer = document.getElementById('chatContainer');
            const systemMessageDiv = document.createElement('div');
            systemMessageDiv.className = 'system-message';
            systemMessageDiv.textContent = `تم تفعيل وكيل: ${this.textContent.trim()}`;
            chatContainer.appendChild(systemMessageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
    });
});
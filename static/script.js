document.addEventListener('DOMContentLoaded', function() {
    // For demo purposes, we'll use a hardcoded token that will actually work
    const demoToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTkxNDU5MDQwMH0.aMKO_tLdAqELKvN8jJpXTQE4NUBfn7Q8iNg2pkWXwWs";
    
    // Store the token immediately for demo purposes
    localStorage.setItem('token', demoToken);
    
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
        performLogin().then(newToken => {
            token = newToken;
        });
    }
    
    // Query form submission
    const queryForm = document.getElementById('queryForm');
    const responseCard = document.getElementById('responseCard');
    const responseElement = document.getElementById('response');
    
    queryForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const query = document.getElementById('query').value.trim();
        if (!query) {
            alert('الرجاء كتابة استعلام');
            return;
        }
        
        // Show loading state
        responseElement.innerHTML = 'جاري معالجة الاستعلام...';
        responseCard.classList.remove('d-none');
        
        // Ensure we have a token
        if (!token) {
            token = await performLogin();
        }
        
        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ query })
            });
            
            // If unauthorized, try to login again
            if (response.status === 401) {
                token = await performLogin();
                // Retry the request
                const retryResponse = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ query })
                });
                
                const data = await retryResponse.json();
                if (retryResponse.ok) {
                    responseElement.innerHTML = data.answer;
                } else {
                    responseElement.innerHTML = `خطأ: ${data.detail || 'حدث خطأ أثناء معالجة الاستعلام'}`;
                }
                return;
            }
            
            const data = await response.json();
            
            if (response.ok) {
                responseElement.innerHTML = data.answer;
            } else {
                responseElement.innerHTML = `خطأ: ${data.detail || 'حدث خطأ أثناء معالجة الاستعلام'}`;
            }
        } catch (error) {
            console.error('Error:', error);
            responseElement.innerHTML = 'حدث خطأ أثناء الاتصال بالخادم';
        }
    });
    
    // Image processing form submission
    const imageForm = document.getElementById('imageForm');
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
        processedImage.src = '';
        imageMessage.textContent = 'جاري معالجة الصورة...';
        
        // Ensure we have a token
        if (!token) {
            token = await performLogin();
        }
        
        try {
            const formData = new FormData();
            formData.append('file', imageFile);
            formData.append('query', imageQuery);
            
            const response = await fetch('/api/edit_image', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });
            
            // If unauthorized, try to login again
            if (response.status === 401) {
                token = await performLogin();
                // Retry the request
                const retryResponse = await fetch('/api/edit_image', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });
                
                handleImageResponse(retryResponse);
                return;
            }
            
            await handleImageResponse(response);
            
        } catch (error) {
            console.error('Error:', error);
            imageMessage.textContent = 'حدث خطأ أثناء الاتصال بالخادم';
        }
    });
    
    async function handleImageResponse(response) {
        if (response.ok) {
            // If the response is an image
            if (response.headers.get('content-type').startsWith('image/')) {
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);
                processedImage.src = imageUrl;
                imageMessage.textContent = response.headers.get('X-Message') || 'تمت معالجة الصورة بنجاح';
            } else {
                // If the response is JSON (error message)
                const data = await response.json();
                imageMessage.textContent = data.message || 'تمت معالجة الصورة بنجاح';
                if (data.image_path) {
                    processedImage.src = data.image_path;
                }
            }
        } else {
            try {
                const data = await response.json();
                imageMessage.textContent = `خطأ: ${data.detail || 'حدث خطأ أثناء معالجة الصورة'}`;
            } catch (e) {
                imageMessage.textContent = `خطأ: حدث خطأ أثناء معالجة الصورة (${response.status})`;
            }
        }
    }
});

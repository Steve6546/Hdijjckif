document.addEventListener('DOMContentLoaded', function() {
    // Get token from localStorage or redirect to login
    const token = localStorage.getItem('token');
    
    // For demo purposes, we'll use a hardcoded token
    const demoToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vIiwiZXhwIjoxNzE0NTkwNDAwfQ.signature";
    
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
        
        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token || demoToken}`
                },
                body: JSON.stringify({ query })
            });
            
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
        
        try {
            const formData = new FormData();
            formData.append('file', imageFile);
            formData.append('query', imageQuery);
            
            const response = await fetch('/api/edit_image', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token || demoToken}`
                },
                body: formData
            });
            
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
                const data = await response.json();
                imageMessage.textContent = `خطأ: ${data.detail || 'حدث خطأ أثناء معالجة الصورة'}`;
            }
        } catch (error) {
            console.error('Error:', error);
            imageMessage.textContent = 'حدث خطأ أثناء الاتصال بالخادم';
        }
    });
});

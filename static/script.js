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
        { id: "meta-llama/llama-4-maverick:free", name: "Meta Llama 4 Maverick", free: true },
        { id: "openai/gpt-4", name: "OpenAI GPT-4", free: false },
        { id: "anthropic/claude-3-opus", name: "Claude 3 Opus", free: false }
    ];
    
    // Current model
    let currentModel = localStorage.getItem('currentModel') || "google/gemini-2.5-pro-exp-03-25:free";
    
    // Active project
    let activeProject = null;
    
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
    
    // Handle message form submission
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        messageForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessage('user', message);
            
            // Clear input
            messageInput.value = '';
            
            // Add AI thinking message
            const thinkingMessage = addMessage('system', '<div class="spinner-border spinner-border-sm" role="status"></div> جاري التفكير...');
            
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ 
                        query: message,
                        model: currentModel,
                        temperature: 0.7,
                        top_p: 0.9
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
                            query: message,
                            model: currentModel,
                            temperature: 0.7,
                            top_p: 0.9
                        })
                    });
                    
                    if (retryResponse.ok) {
                        const data = await retryResponse.json();
                        // Remove thinking message
                        thinkingMessage.remove();
                        // Add AI response
                        addMessage('ai', data.answer || data.response);
                    } else {
                        // Remove thinking message
                        thinkingMessage.remove();
                        // Add error message
                        addMessage('system', 'حدث خطأ أثناء معالجة الاستعلام. يرجى المحاولة مرة أخرى.');
                    }
                } else if (response.ok) {
                    const data = await response.json();
                    // Remove thinking message
                    thinkingMessage.remove();
                    // Add AI response
                    addMessage('ai', data.answer || data.response);
                    
                    // Check if this is a project creation request
                    if (message.includes('إنشاء مشروع') || message.includes('create project') || 
                        message.includes('بناء تطبيق') || message.includes('build app')) {
                        // Show project preview after a delay
                        setTimeout(() => {
                            showProjectPreview({
                                id: 'demo-project-' + Date.now(),
                                name: 'مشروع تجريبي',
                                description: message
                            });
                        }, 1500);
                    }
                } else {
                    // Remove thinking message
                    thinkingMessage.remove();
                    // Add error message
                    addMessage('system', 'حدث خطأ أثناء معالجة الاستعلام. يرجى المحاولة مرة أخرى.');
                }
            } catch (error) {
                console.error('Error:', error);
                // Remove thinking message
                thinkingMessage.remove();
                // Add error message
                addMessage('system', 'حدث خطأ في الاتصال. يرجى التحقق من اتصالك بالإنترنت والمحاولة مرة أخرى.');
            }
        });
    }
    
    // Helper function to add a message to the chat
    function addMessage(type, content) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = content;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    // Handle file upload button
    const uploadButton = document.getElementById('uploadButton');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadButton && fileInput) {
        uploadButton.addEventListener('click', function() {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const file = this.files[0];
                
                // Add system message about file upload
                addMessage('system', `تم رفع الملف: ${file.name}`);
                
                // If it's an image, show preview
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        addMessage('user', `<img src="${e.target.result}" alt="Uploaded image" style="max-width: 100%; max-height: 300px;">`);
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    }
    
    // Handle model selector button
    const modelSelector = document.getElementById('modelSelector');
    if (modelSelector) {
        modelSelector.addEventListener('click', function() {
            const modelModal = new bootstrap.Modal(document.getElementById('modelModal'));
            modelModal.show();
        });
    }
    
    // Handle model selection
    const modelList = document.getElementById('modelList');
    if (modelList) {
        modelList.querySelectorAll('.list-group-item').forEach(item => {
            item.addEventListener('click', function() {
                const modelId = this.getAttribute('data-model');
                
                // Remove active class from all items
                modelList.querySelectorAll('.list-group-item').forEach(i => {
                    i.classList.remove('active');
                });
                
                // Add active class to selected item
                this.classList.add('active');
                
                // Update current model
                currentModel = modelId;
                localStorage.setItem('currentModel', modelId);
            });
        });
    }
    
    // Handle select model button
    const selectModelBtn = document.getElementById('selectModelBtn');
    if (selectModelBtn) {
        selectModelBtn.addEventListener('click', function() {
            const modelModal = bootstrap.Modal.getInstance(document.getElementById('modelModal'));
            modelModal.hide();
            
            // Add system message about model change
            const modelInfo = availableModels.find(m => m.id === currentModel) || availableModels[0];
            addMessage('system', `تم تغيير النموذج إلى ${modelInfo.name}`);
        });
    }
    
    // Handle create project button
    const createProject = document.getElementById('createProject');
    if (createProject) {
        createProject.addEventListener('click', function() {
            const createProjectModal = new bootstrap.Modal(document.getElementById('createProjectModal'));
            createProjectModal.show();
        });
    }
    
    // Handle create project form submission
    const createProjectBtn = document.getElementById('createProjectBtn');
    if (createProjectBtn) {
        createProjectBtn.addEventListener('click', function() {
            const projectName = document.getElementById('projectNameInput').value.trim();
            const projectType = document.getElementById('projectTypeSelect').value;
            const projectDescription = document.getElementById('projectDescriptionInput').value.trim();
            
            if (!projectName || !projectDescription) {
                alert('الرجاء إدخال اسم ووصف المشروع');
                return;
            }
            
            // Close modal
            const createProjectModal = bootstrap.Modal.getInstance(document.getElementById('createProjectModal'));
            createProjectModal.hide();
            
            // Add system message about project creation
            addMessage('system', `جاري إنشاء مشروع "${projectName}"...`);
            
            // Simulate project creation
            setTimeout(() => {
                // Add AI message about project creation
                addMessage('ai', `تم إنشاء مشروع "${projectName}" بنجاح! سأقوم الآن بإنشاء هيكل المشروع وتوليد الملفات اللازمة.`);
                
                // Show project preview
                showProjectPreview({
                    id: 'project-' + Date.now(),
                    name: projectName,
                    type: projectType,
                    description: projectDescription
                });
                
                // Generate project files after a delay
                setTimeout(() => {
                    generateProjectFiles(projectType);
                }, 1500);
            }, 2000);
        });
    }
    
    // Function to show project preview
    function showProjectPreview(project) {
        // Set active project
        activeProject = project;
        
        // Update project name
        document.getElementById('projectName').textContent = project.name;
        
        // Show project preview
        document.getElementById('projectPreview').style.display = 'block';
        
        // Initialize empty file tree
        document.getElementById('fileTree').innerHTML = '<div class="text-center">جاري إنشاء ملفات المشروع...</div>';
        
        // Initialize empty code display
        document.getElementById('codeDisplay').textContent = '// سيتم عرض الكود هنا عند اختيار ملف';
        
        // Initialize empty logs display
        document.getElementById('logsDisplay').textContent = '// سيتم عرض سجلات التشغيل هنا';
        
        // Add system message about project preview
        addMessage('system', `تم فتح معاينة المشروع: ${project.name}`);
    }
    
    // Function to generate project files
    function generateProjectFiles(projectType) {
        let fileTree = '';
        let files = {};
        
        switch (projectType) {
            case 'web':
                // Generate web project files
                fileTree = `
                <div class="folder">📁 ${activeProject.name}/</div>
                <div class="file" data-file="index.html">📄 index.html</div>
                <div class="file" data-file="style.css">📄 style.css</div>
                <div class="file" data-file="script.js">📄 script.js</div>
                <div class="folder">📁 assets/</div>
                <div class="file" data-file="README.md">📄 README.md</div>
                `;
                
                files = {
                    'index.html': '<!DOCTYPE html>\n<html lang="ar" dir="rtl">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>' + activeProject.name + '</title>\n    <link rel="stylesheet" href="style.css">\n</head>\n<body>\n    <header>\n        <h1>' + activeProject.name + '</h1>\n    </header>\n    <main>\n        <p>مرحبًا بكم في تطبيق الويب الخاص بنا!</p>\n    </main>\n    <footer>\n        <p>جميع الحقوق محفوظة &copy; 2025</p>\n    </footer>\n    <script src="script.js"></script>\n</body>\n</html>',
                    'style.css': '/* Main styles */\nbody {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 0;\n    background-color: #f5f5f5;\n}\n\nheader {\n    background-color: #333;\n    color: white;\n    padding: 1rem;\n    text-align: center;\n}\n\nmain {\n    padding: 2rem;\n    max-width: 800px;\n    margin: 0 auto;\n}\n\nfooter {\n    background-color: #333;\n    color: white;\n    padding: 1rem;\n    text-align: center;\n}',
                    'script.js': '// Main JavaScript file\ndocument.addEventListener("DOMContentLoaded", function() {\n    console.log("Application loaded!");\n    \n    // Add your JavaScript code here\n});',
                    'README.md': '# ' + activeProject.name + '\n\n' + activeProject.description + '\n\n## كيفية التشغيل\n\n1. افتح ملف `index.html` في متصفح الويب\n2. استمتع بالتطبيق!\n\n## الميزات\n\n- واجهة مستخدم بسيطة وسهلة الاستخدام\n- تصميم متجاوب يعمل على جميع الأجهزة\n- سهولة التخصيص والتعديل'
                };
                break;
                
            case 'api':
                // Generate API project files
                fileTree = `
                <div class="folder">📁 ${activeProject.name}/</div>
                <div class="file" data-file="app.py">📄 app.py</div>
                <div class="file" data-file="requirements.txt">📄 requirements.txt</div>
                <div class="folder">📁 models/</div>
                <div class="file" data-file="models/user.py">📄 models/user.py</div>
                <div class="folder">📁 routes/</div>
                <div class="file" data-file="routes/api.py">📄 routes/api.py</div>
                <div class="file" data-file="README.md">📄 README.md</div>
                `;
                
                files = {
                    'app.py': 'from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\nimport uvicorn\n\napp = FastAPI(title="' + activeProject.name + '")\n\n# Enable CORS\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=["*"],\n    allow_credentials=True,\n    allow_methods=["*"],\n    allow_headers=["*"],\n)\n\n# Import routes\nfrom routes.api import router as api_router\n\n# Include routers\napp.include_router(api_router, prefix="/api")\n\n@app.get("/")\nasync def root():\n    return {"message": "Welcome to ' + activeProject.name + ' API"}\n\nif __name__ == "__main__":\n    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)',
                    'requirements.txt': 'fastapi==0.103.1\nuvicorn==0.23.2\npydantic==2.3.0\npython-dotenv==1.0.0\nsqlalchemy==2.0.20',
                    'models/user.py': 'from pydantic import BaseModel\nfrom typing import Optional\n\nclass User(BaseModel):\n    id: Optional[int] = None\n    username: str\n    email: str\n    is_active: bool = True\n    \nclass UserCreate(BaseModel):\n    username: str\n    email: str\n    password: str',
                    'routes/api.py': 'from fastapi import APIRouter, HTTPException, Depends\nfrom models.user import User, UserCreate\n\nrouter = APIRouter()\n\n@router.get("/users", response_model=list[User])\nasync def get_users():\n    # This is a demo endpoint that returns mock data\n    return [\n        User(id=1, username="user1", email="user1@example.com"),\n        User(id=2, username="user2", email="user2@example.com")\n    ]\n\n@router.get("/users/{user_id}", response_model=User)\nasync def get_user(user_id: int):\n    # This is a demo endpoint that returns mock data\n    if user_id == 1:\n        return User(id=1, username="user1", email="user1@example.com")\n    elif user_id == 2:\n        return User(id=2, username="user2", email="user2@example.com")\n    else:\n        raise HTTPException(status_code=404, detail="User not found")\n\n@router.post("/users", response_model=User)\nasync def create_user(user: UserCreate):\n    # This is a demo endpoint that returns mock data\n    return User(id=3, username=user.username, email=user.email)',
                    'README.md': '# ' + activeProject.name + ' API\n\n' + activeProject.description + '\n\n## كيفية التشغيل\n\n1. قم بتثبيت المتطلبات: `pip install -r requirements.txt`\n2. قم بتشغيل الخادم: `python app.py`\n3. افتح المتصفح على العنوان: `http://localhost:8000/docs`\n\n## نقاط النهاية API\n\n- `GET /api/users`: الحصول على قائمة المستخدمين\n- `GET /api/users/{user_id}`: الحصول على مستخدم محدد\n- `POST /api/users`: إنشاء مستخدم جديد'
                };
                break;
                
            case 'mobile':
                // Generate mobile project files
                fileTree = `
                <div class="folder">📁 ${activeProject.name}/</div>
                <div class="file" data-file="App.js">📄 App.js</div>
                <div class="file" data-file="package.json">📄 package.json</div>
                <div class="folder">📁 components/</div>
                <div class="file" data-file="components/HomeScreen.js">📄 components/HomeScreen.js</div>
                <div class="folder">📁 assets/</div>
                <div class="file" data-file="README.md">📄 README.md</div>
                `;
                
                files = {
                    'App.js': 'import React from "react";\nimport { NavigationContainer } from "@react-navigation/native";\nimport { createStackNavigator } from "@react-navigation/stack";\nimport HomeScreen from "./components/HomeScreen";\n\nconst Stack = createStackNavigator();\n\nexport default function App() {\n  return (\n    <NavigationContainer>\n      <Stack.Navigator initialRouteName="Home">\n        <Stack.Screen \n          name="Home" \n          component={HomeScreen} \n          options={{ title: "' + activeProject.name + '" }} \n        />\n      </Stack.Navigator>\n    </NavigationContainer>\n  );\n}',
                    'package.json': '{\n  "name": "' + activeProject.name.toLowerCase().replace(/\s+/g, '-') + '",\n  "version": "1.0.0",\n  "main": "node_modules/expo/AppEntry.js",\n  "scripts": {\n    "start": "expo start",\n    "android": "expo start --android",\n    "ios": "expo start --ios",\n    "web": "expo start --web"\n  },\n  "dependencies": {\n    "@react-navigation/native": "^6.1.7",\n    "@react-navigation/stack": "^6.3.17",\n    "expo": "~49.0.8",\n    "expo-status-bar": "~1.6.0",\n    "react": "18.2.0",\n    "react-native": "0.72.4"\n  },\n  "devDependencies": {\n    "@babel/core": "^7.20.0"\n  },\n  "private": true\n}',
                    'components/HomeScreen.js': 'import React, { useState } from "react";\nimport { StyleSheet, Text, View, Button, TextInput, FlatList } from "react-native";\nimport { StatusBar } from "expo-status-bar";\n\nexport default function HomeScreen() {\n  const [text, setText] = useState("");\n  const [items, setItems] = useState([]);\n\n  const addItem = () => {\n    if (text.trim() === "") return;\n    setItems([...items, { id: Date.now().toString(), text }]);\n    setText("");\n  };\n\n  return (\n    <View style={styles.container}>\n      <Text style={styles.title}>مرحبًا بك في تطبيق {activeProject.name}!</Text>\n      \n      <View style={styles.inputContainer}>\n        <TextInput\n          style={styles.input}\n          value={text}\n          onChangeText={setText}\n          placeholder="أدخل نصًا هنا..."\n        />\n        <Button title="إضافة" onPress={addItem} />\n      </View>\n      \n      <FlatList\n        data={items}\n        keyExtractor={(item) => item.id}\n        renderItem={({ item }) => (\n          <View style={styles.item}>\n            <Text>{item.text}</Text>\n          </View>\n        )}\n      />\n      \n      <StatusBar style="auto" />\n    </View>\n  );\n}\n\nconst styles = StyleSheet.create({\n  container: {\n    flex: 1,\n    backgroundColor: "#fff",\n    alignItems: "center",\n    padding: 20,\n  },\n  title: {\n    fontSize: 24,\n    fontWeight: "bold",\n    marginVertical: 20,\n    textAlign: "center",\n  },\n  inputContainer: {\n    flexDirection: "row",\n    width: "100%",\n    marginBottom: 20,\n  },\n  input: {\n    flex: 1,\n    borderWidth: 1,\n    borderColor: "#ccc",\n    padding: 10,\n    marginRight: 10,\n  },\n  item: {\n    backgroundColor: "#f9f9f9",\n    padding: 15,\n    borderRadius: 5,\n    marginVertical: 5,\n    width: "100%",\n  },\n});',
                    'README.md': '# ' + activeProject.name + ' - تطبيق جوال\n\n' + activeProject.description + '\n\n## كيفية التشغيل\n\n1. قم بتثبيت المتطلبات: `npm install`\n2. قم بتشغيل التطبيق: `npm start`\n3. استخدم تطبيق Expo Go على هاتفك لمسح رمز QR\n\n## الميزات\n\n- واجهة مستخدم بسيطة وسهلة الاستخدام\n- يعمل على أنظمة Android و iOS\n- مبني باستخدام React Native و Expo'
                };
                break;
                
            default:
                // Generate default project files
                fileTree = `
                <div class="folder">📁 ${activeProject.name}/</div>
                <div class="file" data-file="README.md">📄 README.md</div>
                <div class="file" data-file="main.py">📄 main.py</div>
                <div class="folder">📁 src/</div>
                <div class="file" data-file="src/app.py">📄 src/app.py</div>
                `;
                
                files = {
                    'README.md': '# ' + activeProject.name + '\n\n' + activeProject.description + '\n\n## كيفية التشغيل\n\n1. قم بتثبيت المتطلبات: `pip install -r requirements.txt`\n2. قم بتشغيل البرنامج: `python main.py`\n\n## الميزات\n\n- سهل الاستخدام\n- قابل للتخصيص\n- مفتوح المصدر',
                    'main.py': '#!/usr/bin/env python3\n"""\nMain entry point for ' + activeProject.name + '\n"""\n\nimport sys\nfrom src.app import App\n\ndef main():\n    """Main function"""\n    print("Starting ' + activeProject.name + '...")\n    app = App()\n    app.run()\n    return 0\n\nif __name__ == "__main__":\n    sys.exit(main())',
                    'src/app.py': '"""\nMain application class for ' + activeProject.name + '\n"""\n\nclass App:\n    """Main application class"""\n    \n    def __init__(self):\n        """Initialize the application"""\n        self.name = "' + activeProject.name + '"\n        self.version = "1.0.0"\n        print(f"Initializing {self.name} v{self.version}")\n    \n    def run(self):\n        """Run the application"""\n        print(f"Running {self.name}...")\n        print("Hello, World!")\n        return True'
                };
        }
        
        // Update file tree
        document.getElementById('fileTree').innerHTML = fileTree;
        
        // Add click event listeners to files
        document.querySelectorAll('.file').forEach(fileElement => {
            fileElement.addEventListener('click', function() {
                const filePath = this.getAttribute('data-file');
                if (filePath && files[filePath]) {
                    // Update code display
                    document.getElementById('codeDisplay').textContent = files[filePath];
                    
                    // Remove selected class from all files
                    document.querySelectorAll('.file').forEach(f => f.classList.remove('selected'));
                    
                    // Add selected class to clicked file
                    this.classList.add('selected');
                }
            });
        });
        
        // Add system message about project files
        addMessage('system', `تم إنشاء ملفات المشروع بنجاح!`);
    }
    
    // Handle run project button
    const runProject = document.getElementById('runProject');
    if (runProject) {
        runProject.addEventListener('click', function() {
            if (!activeProject) return;
            
            // Add system message about running project
            addMessage('system', `جاري تشغيل المشروع: ${activeProject.name}...`);
            
            // Update logs display
            document.getElementById('logsDisplay').textContent = `[${new Date().toLocaleTimeString()}] Starting ${activeProject.name}...\n[${new Date().toLocaleTimeString()}] Installing dependencies...\n[${new Date().toLocaleTimeString()}] Running project...`;
            
            // Switch to logs tab
            document.querySelector('a[href="#logsTab"]').click();
            
            // Simulate project running
            setTimeout(() => {
                // Update logs display
                document.getElementById('logsDisplay').textContent += `\n[${new Date().toLocaleTimeString()}] Project started successfully!\n[${new Date().toLocaleTimeString()}] Server running at http://localhost:8000`;
                
                // Update preview frame
                document.getElementById('previewFrame').src = 'about:blank';
                
                // Switch to preview tab
                document.querySelector('a[href="#previewTab"]').click();
                
                // Add system message about project running
                addMessage('system', `تم تشغيل المشروع بنجاح! يمكنك الآن معاينة المشروع في تبويب المعاينة.`);
            }, 2000);
        });
    }
    
    // Handle stop project button
    const stopProject = document.getElementById('stopProject');
    if (stopProject) {
        stopProject.addEventListener('click', function() {
            if (!activeProject) return;
            
            // Add system message about stopping project
            addMessage('system', `جاري إيقاف المشروع: ${activeProject.name}...`);
            
            // Update logs display
            document.getElementById('logsDisplay').textContent += `\n[${new Date().toLocaleTimeString()}] Stopping project...\n[${new Date().toLocaleTimeString()}] Project stopped successfully!`;
            
            // Switch to logs tab
            document.querySelector('a[href="#logsTab"]').click();
            
            // Add system message about project stopped
            addMessage('system', `تم إيقاف المشروع بنجاح!`);
        });
    }
    
    // Handle close preview button
    const closePreview = document.getElementById('closePreview');
    if (closePreview) {
        closePreview.addEventListener('click', function() {
            // Hide project preview
            document.getElementById('projectPreview').style.display = 'none';
            
            // Reset active project
            activeProject = null;
            
            // Add system message about closing preview
            addMessage('system', `تم إغلاق معاينة المشروع.`);
        });
    }
    
    // Make agent buttons clickable
    document.querySelectorAll('.agent-btn').forEach(button => {
        button.addEventListener('click', function() {
            const agentName = this.textContent.trim();
            const agentType = this.getAttribute('data-agent');
            
            // Remove active class from all buttons
            document.querySelectorAll('.agent-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Add system message about agent activation
            addMessage('system', `تم تفعيل ${agentName}`);
            
            // Add AI message about agent activation
            setTimeout(() => {
                addMessage('ai', `مرحبًا! أنا ${agentName}. كيف يمكنني مساعدتك اليوم؟`);
            }, 500);
        });
    });
});
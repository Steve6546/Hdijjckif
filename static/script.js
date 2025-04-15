function createWebsite() {
    fetch('/api/createWebsite', { method: 'POST' })
        .then(response => response.json())
        .then(data => alert(data.message));
}

function smartUpdates() {
    fetch('/api/smartUpdates', { method: 'POST' })
        .then(response => response.json())
        .then(data => alert(data.message));
}

function manageAgents() {
    fetch('/api/manageAgents', { method: 'POST' })
        .then(response => response.json())
        .then(data => alert(data.message));
}

async function analyzeImage(input) {
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/analyze-image', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();
    alert(data.analysis);
}
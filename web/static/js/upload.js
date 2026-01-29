document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const modelSelect = document.getElementById('model-select');
    const modelNameInput = document.getElementById('model-name-input');
    const modelModeInputs = document.querySelectorAll('input[name="model_mode"]');
    const fileInput = document.getElementById('file-input');
    const uploadButton = document.getElementById('upload-button');
    const progressContainer = document.getElementById('upload-progress-container');
    const progressBar = document.getElementById('upload-progress');
    const progressText = document.getElementById('progress-text');
    const uploadResults = document.getElementById('upload-results');

    const setMode = (mode) => {
        const isExisting = mode === 'existing';
        if (modelSelect) {
            modelSelect.disabled = !isExisting;
        }
        if (modelNameInput) {
            modelNameInput.disabled = isExisting;
        }
    };

    modelModeInputs.forEach((input) => {
        input.addEventListener('change', (event) => setMode(event.target.value));
    });
    setMode('existing');

    const loadModels = async () => {
        try {
            const response = await fetch('/api/models/', {
                credentials: "same-origin",
            });
            if (!response.ok) {
                throw new Error('Failed to load models');
            }
            const models = await response.json();
            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">Select a model</option>';
                models.forEach((model) => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = model.name;
                    modelSelect.appendChild(option);
                });
            }
        } catch (error) {
            displayMessage('error', 'Could not load models. Try refreshing the page.');
            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">Failed to load</option>';
            }
        }
    };

    loadModels();

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission

        uploadResults.innerHTML = ''; // Clear previous results
        progressContainer.style.display = 'none'; // Hide progress bar initially
        progressBar.value = 0;
        progressText.textContent = '0% Uploaded';
        uploadButton.disabled = true;

        const selectedMode = document.querySelector('input[name="model_mode"]:checked')?.value || 'existing';
        const modelId = selectedMode === 'existing' ? (modelSelect ? modelSelect.value : '') : '';
        const modelName = selectedMode === 'new' ? (modelNameInput ? modelNameInput.value.trim() : '') : '';
        const files = fileInput.files;

        if (selectedMode === 'existing' && !modelId) {
            displayMessage('error', 'Please choose a model.');
            uploadButton.disabled = false;
            return;
        }

        if (selectedMode === 'new' && !modelName) {
            displayMessage('error', 'Please enter a model name.');
            uploadButton.disabled = false;
            return;
        }

        if (files.length === 0) {
            displayMessage('error', 'Please select at least one file.');
            uploadButton.disabled = false;
            return;
        }

        if (files.length > 50) {
            displayMessage('error', 'You can upload a maximum of 50 files at once.');
            uploadButton.disabled = false;
            return;
        }

        const formData = new FormData();
        if (modelId) {
            formData.append('model_id', modelId);
        } else if (modelName) {
            formData.append('model_name', modelName);
        }
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        progressContainer.style.display = 'block'; // Show progress bar

        try {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/media/upload', true);

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.value = percent;
                    progressText.textContent = `${percent}% Uploaded`;
                }
            };

            xhr.onload = () => {
                uploadButton.disabled = false;
                if (xhr.status >= 200 && xhr.status < 300) {
                    const response = JSON.parse(xhr.responseText);
                    displayMessage('success', `Successfully uploaded ${response.length} file(s).`);
                    response.forEach(media => {
                        uploadResults.innerHTML += `
                            <article>
                                <header>Uploaded: ${media.file_path.split('/').pop()}</header>
                                <p>Model ID: ${media.model_id}, Media ID: ${media.id}</p>
                            </article>
                        `;
                    });
                } else {
                    const errorResponse = JSON.parse(xhr.responseText);
                    displayMessage('error', `Upload failed: ${errorResponse.detail || xhr.statusText}`);
                }
            };

            xhr.onerror = () => {
                uploadButton.disabled = false;
                displayMessage('error', 'Network error during upload.');
            };

            xhr.send(formData);

        } catch (error) {
            uploadButton.disabled = false;
            displayMessage('error', `An unexpected error occurred: ${error.message}`);
        }
    });

    function displayMessage(type, message) {
        const p = document.createElement('p');
        p.className = `message ${type}`;
        p.textContent = message;
        uploadResults.prepend(p);
    }
});

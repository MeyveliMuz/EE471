document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('text-input');
    const synthesizeBtn = document.getElementById('synthesize-btn');
    const btnText = document.getElementById('btn-text');
    const spinner = document.getElementById('spinner');
    const iconRight = document.querySelector('.icon-right');
    const errorBox = document.getElementById('error-box');
    const outputGroup = document.getElementById('output-group');
    const audioOut = document.getElementById('audio-out');
    const downloadBtn = document.getElementById('download-btn');
    
    // Theme Toggle Functionality
    const themeBtn = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    
    // Default is dark mode in initial HTML setup
    let isDarkMode = true;
    
    themeBtn.addEventListener('click', () => {
        isDarkMode = !isDarkMode;
        if (isDarkMode) {
            document.body.classList.remove('light-mode');
            document.body.classList.add('dark-mode');
            themeIcon.classList.replace('fa-moon', 'fa-sun'); // Show sun in dark mode
        } else {
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
            themeIcon.classList.replace('fa-sun', 'fa-moon'); // Show moon in light mode
        }
    });

    // Synthesize API Call
    synthesizeBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        
        if (!text) {
            showError("Please enter some text to generate speech.");
            return;
        }
        
        // Setup UI loading state
        errorBox.style.display = 'none';
        synthesizeBtn.disabled = true;
        btnText.textContent = "Processing...";
        iconRight.style.display = 'none';
        spinner.style.display = 'block';
        outputGroup.style.display = 'none';
        
        try {
            const response = await fetch('/synthesize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text, voice_type: document.getElementById('voice-select').value })
            });
            
            if (response.ok) {
                // The API returned the audio binary file successfully
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                
                audioOut.src = url;
                downloadBtn.href = url; // Attachment URL applied directly to Download link
                downloadBtn.download = "synthesized_speech.mp3";
                
                outputGroup.style.display = 'block';
                errorBox.style.display = 'none';
                
                // Reset file downloaded once they modify text
                textInput.addEventListener('input', () => {
                    outputGroup.style.display = 'none';
                }, { once: true });
                
            } else {
                const errData = await response.json();
                showError(errData.error || "An error occurred during speech synthesis.");
            }
        } catch (err) {
            console.error("Fetch Error:", err);
            showError("Network error. Could not connect to the backend API.");
        } finally {
            // Revert loading state button UI
            synthesizeBtn.disabled = false;
            btnText.textContent = "Generate Speech";
            iconRight.style.display = 'inline-block';
            spinner.style.display = 'none';
        }
    });

    function showError(message) {
        errorBox.textContent = message;
        errorBox.style.display = 'block';
    }
});

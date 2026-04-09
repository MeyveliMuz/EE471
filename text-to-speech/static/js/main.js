document.addEventListener('DOMContentLoaded', () => {
    // --- Theme Toggle ---
    const themeBtn = document.getElementById('theme-toggle');
    const icon = themeBtn.querySelector('i');
    themeBtn.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        if (document.body.classList.contains('light-mode')) {
            icon.classList.replace('fa-sun', 'fa-moon');
        } else {
            icon.classList.replace('fa-moon', 'fa-sun');
        }
    });

    // --- Tabs Logic ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const panels = document.querySelectorAll('.panel');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
        });
    });

    // --- TTS Logic ---
    const ttsBtn = document.getElementById('synthesize-btn');
    const ttsInput = document.getElementById('text-input');
    const ttsVoice = document.getElementById('voice-select');
    const ttsStatus = document.querySelector('.tts-status');
    const ttsError = document.querySelector('.tts-error');
    const ttsOutput = document.querySelector('.tts-output');
    const audioOut = document.getElementById('audio-out');
    const downloadBtn = document.getElementById('download-btn');

    ttsBtn.addEventListener('click', async () => {
        const text = ttsInput.value.trim();
        if (!text) {
            showError(ttsError, "Please enter some text.", ttsStatus, ttsOutput);
            return;
        }

        ttsStatus.style.display = 'flex';
        ttsError.style.display = 'none';
        ttsOutput.style.display = 'none';
        ttsBtn.disabled = true;

        try {
            const res = await fetch('/synthesize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, voice_type: ttsVoice.value })
            });

            if (res.ok) {
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                audioOut.src = url;
                downloadBtn.href = url;
                ttsOutput.style.display = 'block';
            } else {
                const data = await res.json();
                showError(ttsError, data.error || "Generation error.", ttsStatus, ttsOutput);
            }
        } catch (e) {
            showError(ttsError, "Network error.", ttsStatus, ttsOutput);
        } finally {
            ttsBtn.disabled = false;
            ttsStatus.style.display = 'none';
        }
    });

    ttsInput.addEventListener('input', () => { ttsOutput.style.display = 'none'; }, { once: true });

    // --- STT Logic ---
    const sttLang = document.getElementById('lang-select');
    const recordBtn = document.getElementById('record-btn');
    const fileUpload = document.getElementById('file-upload');
    const recordText = document.getElementById('record-text');
    const recordIcon = recordBtn.querySelector('i');
    
    const sttStatus = document.querySelector('.stt-status');
    const sttStatusText = document.getElementById('stt-status-text');
    const sttError = document.querySelector('.stt-error');
    const sttResult = document.querySelector('.stt-result');
    const transcriptBox = document.getElementById('transcript-box');

    let isRecording = false;
    let mediaRecorder;
    let audioChunks = [];

    recordBtn.addEventListener('click', async () => {
        if (!isRecording) startRecording();
        else stopRecording();
    });

    fileUpload.addEventListener('change', async (e) => {
        if (e.target.files.length > 0) {
            processAudioFile(e.target.files[0]);
        }
    });

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = () => processAudioFile(new Blob(audioChunks));
            mediaRecorder.start();
            isRecording = true;
            recordBtn.classList.add('recording');
            recordText.textContent = "Stop Recording";
            recordIcon.classList.replace('fa-microphone', 'fa-stop');
            sttStatus.style.display = 'none';
        } catch (err) {
            showError(sttError, "Microphone access denied.", sttStatus, sttResult);
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(t => t.stop());
        }
        isRecording = false;
        recordBtn.classList.remove('recording');
        recordText.textContent = "Start Recording";
        recordIcon.classList.replace('fa-stop', 'fa-microphone');
    }

    async function processAudioFile(fileOrBlob) {
        sttStatusText.textContent = "Converting audio & transcribing...";
        sttStatus.style.display = 'flex';
        sttError.style.display = 'none';
        sttResult.style.display = 'none';

        try {
            const wavBlob = await convertToWavBlob(fileOrBlob);
            const formData = new FormData();
            formData.append('audio_data', wavBlob, 'audio.wav');
            formData.append('language', sttLang.value);

            const res = await fetch('/transcribe', { method: 'POST', body: formData });
            const data = await res.json();
            
            if (res.ok) {
                transcriptBox.textContent = data.text;
                sttResult.style.display = 'block';
            } else {
                showError(sttError, data.error || "Transcription error.", sttStatus, sttResult);
            }
        } catch (err) {
            showError(sttError, "Error processing audio or network error.", sttStatus, sttResult);
        } finally {
            sttStatus.style.display = 'none';
            fileUpload.value = '';
        }
    }

    function showError(errEl, msg, statusEl, outEl) {
        errEl.textContent = msg;
        errEl.style.display = 'block';
        if(statusEl) statusEl.style.display = 'none';
        if(outEl) outEl.style.display = 'none';
    }

    // -- Audio Encoding Helper --
    async function convertToWavBlob(fileOrBlob) {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const arrayBuffer = await fileOrBlob.arrayBuffer();
        const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
        const pcmData = audioBuffer.getChannelData(0);
        return encodeWAV(pcmData, 16000);
    }

    function encodeWAV(samples, sampleRate) {
        let buffer = new ArrayBuffer(44 + samples.length * 2);
        let view = new DataView(buffer);
        writeString(view, 0, 'RIFF'); view.setUint32(4, 36 + samples.length * 2, true);
        writeString(view, 8, 'WAVE'); writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true); view.setUint16(34, 16, true);
        writeString(view, 36, 'data'); view.setUint32(40, samples.length * 2, true);
        
        let offset = 44;
        for (let i = 0; i < samples.length; i++, offset += 2) {
            let s = Math.max(-1, Math.min(1, samples[i]));
            view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }
        return new Blob([view], { type: 'audio/wav' });
    }
    const writeString = (v, o, s) => { for(let i=0; i<s.length; i++) v.setUint8(o+i, s.charCodeAt(i)); }
});

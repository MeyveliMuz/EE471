import os
import uuid
import io
from flask import Flask, render_template, request, jsonify, send_file
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SPEECH_KEY = os.environ.get('SPEECH_KEY')
SPEECH_REGION = 'westeurope'

@app.route('/')
def index():
    return render_template('index.html')

# ================================
# PART 1: Text to Speech (TTS)
# ================================
@app.route('/synthesize', methods=['POST'])
def synthesize():
    data = request.json
    text = data.get('text')
    voice_type = data.get('voice_type', 'female_neutral')
    
    if not text:
        return jsonify({'error': 'Lütfen geçerli bir metin girin.'}), 400
        
    if not SPEECH_KEY:
        return jsonify({'error': 'Azure SPEECH_KEY mevcut değil. Lütfen .env dosyanızı kontrol edin.'}), 500

    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)

    # For auto-detecting language, we use multilingual models which are incredibly smart.
    if voice_type == "female_auto":
        voice_name = "en-US-JennyMultilingualNeural" 
        style = "neutral"
    elif voice_type == "male_auto":
        voice_name = "en-US-RyanMultilingualNeural"
        style = "neutral"
    elif voice_type == "female_excited":
        voice_name = "en-US-AriaNeural"
        style = "excited"
    elif voice_type == "male_excited":
        voice_name = "en-US-DavisNeural"
        style = "excited"
    else:
        voice_name = "en-US-JennyMultilingualNeural"
        style = "neutral"
    
    import xml.sax.saxutils as saxutils
    escaped_text = saxutils.escape(text)
    
    if style and style != "neutral":
        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="{voice_name}">
                <mstts:express-as style="{style}">
                    {escaped_text}
                </mstts:express-as>
            </voice>
        </speak>"""
    else:
        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice_name}">
                {escaped_text}
            </voice>
        </speak>"""

    # Hoparlöre direkt çalmak yerine dosyayı byte stream olarak almak için None atıyoruz.
    auto_detect_config = None
    if "_auto" in voice_type:
        # For TTS, AutoDetectSourceLanguageConfig must use open range (no language list)
        auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig()
        
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, 
        audio_config=None,
        auto_detect_source_language_config=auto_detect_config
    )
    
    if "_auto" in voice_type:
        # Multilingual with explicit detect requires text API usually, not SSML overrides
        result = speech_synthesizer.speak_text_async(text).get()
    else:
        result = speech_synthesizer.speak_ssml_async(ssml).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data
        return send_file(
            io.BytesIO(audio_data),
            mimetype="audio/mpeg"
        )
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        reason_text = f"İşlem İptal Edildi: {cancellation_details.reason}"
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            reason_text += f" - Detay: {cancellation_details.error_details}"
        return jsonify({'error': reason_text}), 500

# ================================
# PART 2: Speech to Text (STT)
# ================================
@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio_data' not in request.files:
        return jsonify({'error': 'Lütfen bir ses dosyası yükleyin.'}), 400
        
    language = request.form.get('language', 'tr-TR')
    
    file = request.files['audio_data']
    if file.filename == '':
        return jsonify({'error': 'Seçili dosya eksik.'}), 400
        
    if not SPEECH_KEY:
        return jsonify({'error': 'Azure SPEECH_KEY eksik. Lütfen yapılandırın.'}), 500

    temp_filename = f"temp_{uuid.uuid4().hex}.wav"
    temp_path = os.path.join(app.root_path, temp_filename)
    file.save(temp_path)
    
    del file # Release early
    result_text = ""
    error_msg = ""
    status_code = 200

    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        
        # If language is set to 'auto', detect language automatically
        auto_detect_config = None
        if language == "auto":
            auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["tr-TR", "en-US"])
            speech_config.speech_recognition_language = "en-US" # fallback
        else:
            speech_config.speech_recognition_language = language
            
        audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
        
        if auto_detect_config:
            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, auto_detect_source_language_config=auto_detect_config, audio_config=audio_config)
        else:
            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        
        result = speech_recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            result_text = result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            error_msg = 'Ses anlaşılamadı. Hiçbir metin bulunamadı.'
            status_code = 400
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_msg = f"İptal Edildi: {cancellation_details.reason}"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_msg += f" - Detay: {cancellation_details.error_details}"
            status_code = 500
    finally:
        if 'speech_recognizer' in locals():
            del speech_recognizer
        if 'audio_config' in locals():
            del audio_config
            
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

    if error_msg:
        return jsonify({'error': error_msg}), status_code
    return jsonify({'text': result_text})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

import os
import io
from flask import Flask, render_template, request, jsonify, send_file
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# .env dosyasından gizli bilgileri yükle
load_dotenv()

app = Flask(__name__)

SPEECH_KEY = os.environ.get('SPEECH_KEY')
SPEECH_REGION = 'westeurope'

@app.route('/')
def index():
    return render_template('index.html')

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
    
    # Set output format to MP3
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    
    # Hoparlöre direkt çalmak yerine dosyayı byte stream olarak almak için None atıyoruz.
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    
    # Build SSML based on voice_type
    voice_name = "en-US-AriaNeural" # default
    style = ""
    
    if voice_type == "female_neutral":
        voice_name = "en-US-AriaNeural"
        style = "neutral"
    elif voice_type == "male_neutral":
        voice_name = "en-US-DavisNeural"
        style = "neutral"
    elif voice_type == "female_excited":
        voice_name = "en-US-AriaNeural"
        style = "excited"
    elif voice_type == "male_excited":
        voice_name = "en-US-DavisNeural"
        style = "excited"
    elif voice_type == "male_mature":
        voice_name = "en-GB-ArthurNeural"
    
    # Construct SSML
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

    result = speech_synthesizer.speak_ssml_async(ssml).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data
        
        # Binary datayı tarayıcıya file stream olarak aktar
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

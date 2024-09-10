import os
import re
import subprocess
from flask import Flask, render_template, request, send_file, url_for, send_from_directory
from werkzeug.utils import secure_filename
import ffmpeg as ffmpeg_lib
from openai import OpenAI
from dotenv import load_dotenv
from language_data import get_language_name, get_flag_emoji, get_all_languages
from langdetect import detect

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov'}


load_dotenv()

client = OpenAI()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def convert_video_to_audio(video_path):
    audio_path = video_path.rsplit('.', 1)[0] + '.mp3'

    if os.path.exists(audio_path):
        os.remove(audio_path)
    try:
        stream = ffmpeg_lib.input(video_path)
        stream = ffmpeg_lib.output(stream, audio_path)
        ffmpeg_lib.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return audio_path
    except ffmpeg_lib.Error as e:
        print(f'FFmpeg error: {e.stderr.decode()}')
        return None


def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="srt"
        )
    return transcript


def translate_text(transcription, target_language):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are a very helpful and talented translator who can translate all languages and srt files."},
            {"role": "user",
             "content": f"Could you please translate the .srt text below to {target_language}? Do not add any comments of yours only the translation. "
                        f"Please do not change the timestamps and structure of the file.\n<Transcription>{transcription}</Transcription>"}
        ]
    )

    translated_text = response.choices[0].message.content
    return translated_text


def srt_to_text(srt_content):
    lines = srt_content.strip().split('\n')
    text_lines = []
    for line in lines:
        if not re.match(r'^\d+$', line) and not re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line):
            if line.strip():
                text_lines.append(line.strip())
    return ' '.join(text_lines)


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/')
def landing_page():
    image_url = url_for('static', filename='images/back_to_the_future.jpg')
    return render_template('landing.html', image_url=image_url)


@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            video_url = url_for('uploaded_file', filename=filename)
            audio_path = convert_video_to_audio(file_path)
            transcript = transcribe_audio(audio_path)

            original_language = detect(transcript)

            languages = request.form.getlist('languages[]')
            translations = {}
            for lang in languages:
                translations[lang] = translate_text(transcript, get_language_name(lang))

            transcript_text = srt_to_text(transcript)
            translations_text = {lang: srt_to_text(trans) for lang, trans in translations.items()}

            # Generate subtitled videos

            subtitled_videos = {}
            for lang, srt_content in translations.items():
                srt_filename = f"{lang}_subtitle.srt"
                srt_path = os.path.join(app.config['UPLOAD_FOLDER'], srt_filename)
                with open(srt_path, 'w', encoding='utf-8') as srt_file:
                    srt_file.write(srt_content)

                output_filename = f"subtitled_{lang}_{filename}"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

                ffmpeg_command = [
                    'ffmpeg',
                    '-i', file_path,
                    '-vf', f"subtitles={srt_path}",
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ]

                subprocess.run(ffmpeg_command, check=True)
                subtitled_videos[lang] = url_for('download_file', filename=output_filename)

            srt_filename = f"{original_language}_subtitle.srt"
            srt_path = os.path.join(app.config['UPLOAD_FOLDER'], srt_filename)
            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                srt_file.write(transcript)

            output_filename = f"subtitled_{original_language}_{filename}"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

            ffmpeg_command = [
                'ffmpeg',
                '-i', file_path,
                '-vf', f"subtitles={srt_path}",
                '-c:a', 'copy',
                '-y',
                output_path
            ]

            subprocess.run(ffmpeg_command, check=True)
            subtitled_videos[original_language] = url_for('download_file', filename=output_filename)
            original_video_url = url_for('download_file', filename=output_filename)

            return render_template('results.html',
                                   transcript=transcript_text,
                                   transcript_srt=transcript,
                                   translations_text=translations_text,
                                   translations_srt=translations,
                                   get_language_name=get_language_name,
                                   get_flag_emoji=get_flag_emoji,
                                   original_lang=original_language,
                                   video_url=video_url,
                                   original_video_url=original_video_url,
                                   subtitled_videos=subtitled_videos)
    return render_template('index.html', languages=get_all_languages())


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)

# VideoLingo

VideoLingo is an AI-powered video translation and transcription tool. This project aims to overcome language barriers in global content consumption and provide an accessible solution for multilingual video content.

## Features

- Instant video translation to 99+ languages
- AI-driven transcription
- User-friendly web interface
- Multiple language selection
- SRT subtitle download
- Subtitled video download

## Technology Stack

- **Frontend:** HTML5, CSS3, JavaScript
- **Backend:** Python, Flask
- **AI:** OpenAI Whisper, GPT-4-mini
- **Video Processing:** FFmpeg


## Installation

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # For Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file and add the necessary API keys:
   ```
   OPENAI_API_KEY=your_openai_key
   ```

5. Run the application:
   ```
   python video_transcriber.py
   ```

6. Navigate to `http://127.0.0.1:5000` in your browser.

## Usage

1. Click the "Get Started" button on the home page.
2. On the video upload page, select a video file.
3. Choose the languages you want to translate to.
4. Click the "Upload and Process" button.
5. Once processing is complete, transcriptions and translations will be displayed.
6. You can download SRT files or subtitled videos.

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from typing import Dict, Optional
import uvicorn

from .engine import generate_response, get_project_context
from .devices import discover_devices

app = FastAPI(title="F.R.A.N.C.I.S API")


@app.get('/')
async def home():
    # Minimal web UI for quick testing
    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>F.R.A.N.C.I.S Chat</title>
    </head>
    <body>
      <h1>F.R.A.N.C.I.S</h1>
      <form id="chat-form">
        <input id="msg" type="text" placeholder="Say something" style="width:70%" />
        <button type="submit">Send</button>
      </form>
      <pre id="resp"></pre>
      <script>
        const form = document.getElementById('chat-form');
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const msg = document.getElementById('msg').value;
          const respEl = document.getElementById('resp');
          respEl.textContent = 'Thinking...';
          const r = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({message: msg})
          });
          const data = await r.json();
          respEl.textContent = data.response || JSON.stringify(data);
        });
      </script>
    </body>
    </html>
    """
    return Response(content=html, media_type='text/html')


@app.post('/chat')
@app.get('/chat')
async def chat(request: Request):
    """POST /chat expects JSON {message: str}. GET /chat?message=... is supported for quick browser tests."""
    if request.method == 'GET':
        message = request.query_params.get('message')
        if not message:
            raise HTTPException(status_code=400, detail="Missing 'message' query parameter")
    else:
        body = await request.json()
        message = body.get('message')
        if not message:
            raise HTTPException(status_code=400, detail="Missing 'message' field in JSON body")

    context = get_project_context(message)
    resp = generate_response(message, context)
    return {"response": resp}


@app.post('/voice')
async def voice(file: UploadFile = File(...)):
    # Basic voice endpoint: save file and attempt to transcribe if SpeechRecognition available
    content = await file.read()
    try:
        import speech_recognition as sr
        from io import BytesIO
        audio_data = BytesIO(content)
        r = sr.Recognizer()
        with sr.AudioFile(audio_data) as source:
            audio = r.record(source)
        text = r.recognize_google(audio)
        context = get_project_context(text)
        resp = generate_response(text, context)
        return {"transcript": text, "response": resp}
    except ImportError:
        # SpeechRecognition not installed
        return {"error": "Speech recognition not available. Install 'speechrecognition' to enable voice."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/devices')
async def devices():
    devs = discover_devices()
    return {"devices": devs}


@app.get('/favicon.ico')
async def favicon():
    # Return empty 204 to avoid browser 404 logs
    return Response(status_code=204)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)

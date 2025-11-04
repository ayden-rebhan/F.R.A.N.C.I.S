from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTextEdit, QLabel, QFileDialog, QListWidget, QTabWidget
)
from PySide6.QtCore import QThread, Signal
import sys

try:
    # Prefer local imports (when running as script)
    from engine import generate_response, get_project_context, check_model_availability
    from devices import discover_devices
except Exception:
    # Fallback when running as package
    from src.engine import generate_response, get_project_context, check_model_availability
    from src.devices import discover_devices


class Worker(QThread):
    finished = Signal(str)

    def __init__(self, fn, *args):
        super().__init__()
        self.fn = fn
        self.args = args

    def run(self):
        try:
            res = self.fn(*self.args)
            if isinstance(res, str):
                out = res
            else:
                out = str(res)
            self.finished.emit(out)
        except Exception as e:
            self.finished.emit(f"Error: {e}")


class FrancisGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('F.R.A.N.C.I.S')
        self.resize(800, 600)

        self.layout = QVBoxLayout(self)

        self.status_label = QLabel('Initializing model status...')
        self.layout.addWidget(self.status_label)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self._build_chat_tab()
        self._build_voice_tab()
        self._build_devices_tab()

        self.update_model_status()

    def update_model_status(self):
        ok = check_model_availability()
        if ok:
            self.status_label.setText(f'Model available')
        else:
            self.status_label.setText(f'Model not available — pull and run ollama serve')

    def _build_chat_tab(self):
        chat_tab = QWidget()
        v = QVBoxLayout(chat_tab)

        self.conversation = QTextEdit()
        self.conversation.setReadOnly(True)
        v.addWidget(self.conversation)

        h = QHBoxLayout()
        self.input_line = QLineEdit()
        self.send_btn = QPushButton('Send')
        self.send_btn.clicked.connect(self.on_send)
        h.addWidget(self.input_line)
        h.addWidget(self.send_btn)
        v.addLayout(h)

        self.tabs.addTab(chat_tab, 'Chat')

    def _build_voice_tab(self):
        voice_tab = QWidget()
        v = QVBoxLayout(voice_tab)

        self.voice_label = QLabel('No file selected')
        v.addWidget(self.voice_label)

        h = QHBoxLayout()
        self.select_btn = QPushButton('Select Audio File')
        self.select_btn.clicked.connect(self.select_audio)
        self.transcribe_btn = QPushButton('Transcribe & Send')
        self.transcribe_btn.clicked.connect(self.on_transcribe)
        h.addWidget(self.select_btn)
        h.addWidget(self.transcribe_btn)
        v.addLayout(h)

        self.voice_resp = QTextEdit()
        self.voice_resp.setReadOnly(True)
        v.addWidget(self.voice_resp)

        self.tabs.addTab(voice_tab, 'Voice')
        self.selected_audio = None

    def _build_devices_tab(self):
        dev_tab = QWidget()
        v = QVBoxLayout(dev_tab)

        self.discover_btn = QPushButton('Discover Devices')
        self.discover_btn.clicked.connect(self.on_discover)
        v.addWidget(self.discover_btn)

        self.devices_list = QListWidget()
        v.addWidget(self.devices_list)

        self.tabs.addTab(dev_tab, 'Devices')

    def append_conversation(self, text: str):
        self.conversation.append(text)

    def on_send(self):
        prompt = self.input_line.text().strip()
        if not prompt:
            return
        self.append_conversation(f'You: {prompt}')
        self.input_line.clear()

        context = get_project_context(prompt)
        self.append_conversation('Thinking...')

        worker = Worker(generate_response, prompt, context)
        worker.finished.connect(lambda out: self._on_response(out, worker))
        worker.start()

    def _on_response(self, out: str, worker: Worker):
        # Remove the 'Thinking...' line and append the actual response
        self.append_conversation(f'F.R.A.N.C.I.S: {out}')
        worker.deleteLater()

    def select_audio(self):
        fn, _ = QFileDialog.getOpenFileName(self, 'Select audio file', '', 'Audio Files (*.wav *.mp3 *.flac)')
        if fn:
            self.selected_audio = fn
            self.voice_label.setText(fn)

    def on_transcribe(self):
        if not self.selected_audio:
            self.voice_resp.setPlainText('No audio file selected')
            return
        try:
            import speech_recognition as sr
        except Exception:
            self.voice_resp.setPlainText("Speech recognition not available. Install 'speechrecognition' to enable voice.")
            return

        def transcribe_and_send(path):
            r = sr.Recognizer()
            with sr.AudioFile(path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio)
            return text

        self.voice_resp.setPlainText('Transcribing...')
        worker = Worker(transcribe_and_send, self.selected_audio)
        worker.finished.connect(lambda out: self._on_transcribed(out, worker))
        worker.start()

    def _on_transcribed(self, text: str, worker: Worker):
        self.voice_resp.append(f'Transcript: {text}')
        context = get_project_context(text)
        w2 = Worker(generate_response, text, context)
        w2.finished.connect(lambda out: self.voice_resp.append(f'F.R.A.N.C.I.S: {out}'))
        w2.start()
        worker.deleteLater()

    def on_discover(self):
        self.devices_list.clear()
        self.devices_list.addItem('Discovering...')
        worker = Worker(discover_devices)
        worker.finished.connect(lambda out: self._on_devices(out, worker))
        worker.start()

    def _on_devices(self, out: str, worker: Worker):
        self.devices_list.clear()
        try:
            import ast
            devices = ast.literal_eval(out) if out.startswith('[') or out.startswith('{') else None
        except Exception:
            devices = None
        if devices and isinstance(devices, list):
            for d in devices:
                addr = d.get('address', 'unknown')
                resp = d.get('response', '')
                self.devices_list.addItem(f"{addr} — {resp.splitlines()[0] if resp else ''}")
        else:
            # fallback: show raw
            self.devices_list.addItem(out)
        worker.deleteLater()


def main():
    app = QApplication(sys.argv)
    gui = FrancisGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

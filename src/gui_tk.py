import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont
import sys

# Theme override populated by splash (optional)
THEME = {}


class Tooltip:
    """Simple tooltip for widgets."""
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._id = None
        self.tipwindow = None
        widget.bind('<Enter>', self.schedule)
        widget.bind('<Leave>', self.hide)

    def schedule(self, _event=None):
        self._id = self.widget.after(self.delay, self.show)

    def show(self):
        if self.tipwindow:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, bg='#222', fg='white', font=('Segoe UI', 9), bd=0, padx=6, pady=2)
        label.pack()

    def hide(self, _event=None):
        if self._id:
            try:
                self.widget.after_cancel(self._id)
            except Exception:
                pass
            self._id = None
        if self.tipwindow:
            try:
                self.tipwindow.destroy()
            except Exception:
                pass
            self.tipwindow = None


def _make_icon(name: str, size: int = 20, fg: str = '#E0E0E0', bg: str = None):
    """Create a simple monochrome icon using Pillow and return an ImageTk.PhotoImage.
    Supported names: 'chat','mic','plug','trash','save','copy'.
    This keeps icons crisp and consistent across platforms.
    """
    try:
        from PIL import Image, ImageDraw
        from PIL import ImageTk
    except Exception:
        return None

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = max(1, size // 10)
    fg_rgb = tuple(int(fg.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

    if name == 'chat':
        # rounded rect bubble
        draw.rounded_rectangle([(2, 3), (size-3, size-6)], radius=4, outline=fg_rgb, width=stroke)
        # tail
        draw.polygon([(size//3, size-6), (size//3 + 4, size-2), (size//3 + 10, size-6)], fill=fg_rgb)
    elif name == 'mic':
        # mic head
        draw.ellipse([(size*0.28, size*0.12), (size*0.72, size*0.6)], outline=fg_rgb, width=stroke)
        # handle
        draw.rectangle([(size*0.45, size*0.58), (size*0.55, size*0.82)], fill=fg_rgb)
    elif name == 'plug':
        # body
        draw.rectangle([(size*0.42, size*0.18), (size*0.58, size*0.6)], fill=fg_rgb)
        # prongs
        draw.rectangle([(size*0.36, size*0.12), (size*0.42, size*0.22)], fill=fg_rgb)
        draw.rectangle([(size*0.58, size*0.12), (size*0.64, size*0.22)], fill=fg_rgb)
    elif name == 'trash':
        # lid
        draw.rectangle([(size*0.22, size*0.18), (size*0.78, size*0.3)], fill=fg_rgb)
        # body
        draw.rectangle([(size*0.28, size*0.3), (size*0.72, size*0.78)], outline=fg_rgb, width=stroke)
    elif name == 'save':
        # simple floppy
        draw.rectangle([(size*0.18, size*0.18), (size*0.78, size*0.78)], outline=fg_rgb, width=stroke)
        draw.rectangle([(size*0.32, size*0.28), (size*0.62, size*0.46)], fill=fg_rgb)
    elif name == 'copy':
        draw.rectangle([(size*0.28, size*0.22), (size*0.78, size*0.72)], outline=fg_rgb, width=stroke)
        draw.rectangle([(size*0.18, size*0.32), (size*0.68, size*0.82)], outline=fg_rgb, width=stroke)
    else:
        # fallback: circle
        draw.ellipse([(3, 3), (size-3, size-3)], outline=fg_rgb, width=stroke)

    return ImageTk.PhotoImage(img)

try:
    # local imports
    from engine import generate_response, get_project_context, check_model_availability
    from devices import discover_devices
except Exception:
    from src.engine import generate_response, get_project_context, check_model_availability
    from src.devices import discover_devices


class TkWorker(threading.Thread):
    def __init__(self, fn, args=(), callback=None):
        super().__init__(daemon=True)
        self.fn = fn
        self.args = args
        self.callback = callback

    def run(self):
        try:
            result = self.fn(*self.args)
        except Exception as e:
            result = f"Error: {e}"
        if self.callback:
            try:
                self.callback(result)
            except Exception:
                pass


class FrancisApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('F.R.A.N.C.I.S')
        self.geometry('800x600')

        # Modern dark theme with softer grays
        self._bg = THEME.get('bg', '#1E1E1E')  # Dark gray background
        self._fg = THEME.get('fg', '#E0E0E0')  # Light gray text
        self._accent = THEME.get('accent', '#1E90FF')  # Keep the blue accent
        self._bg_lighter = '#2D2D2D'  # Slightly lighter gray for contrast elements
        self._bg_darker = '#171717'   # Slightly darker gray for depth

        # compute a softer hover color by blending accent with the lighter bg
        def _blend_hex(a, b, t=0.18):
            # a, b are '#rrggbb'
            a = a.lstrip('#')
            b = b.lstrip('#')
            ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
            br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
            rr = int(ar * (1 - t) + br * t)
            rg = int(ag * (1 - t) + bg * t)
            rb = int(ab * (1 - t) + bb * t)
            return f"#{rr:02x}{rg:02x}{rb:02x}"

        self._hover_accent = _blend_hex(self._accent, self._bg_lighter, 0.25)

        # Configure root background
        self.configure(bg=self._bg)

        # Create main layout: sidebar + content with modern proportions
        self.sidebar = tk.Frame(self, bg=self._bg_darker, width=250)  # Wider sidebar
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)  # Keep width fixed

        # Content area (tabs) - use lighter background to avoid dark border
        self.content = tk.Frame(self, bg=self._bg_lighter)
        self.content.pack(side='right', fill='both', expand=True)

        # Configure notebook styling for a modern look
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure('Custom.TNotebook', 
                       background=self._bg,
                       borderwidth=0,
                       tabmargins=[0, 0, 0, 0],
                       tabposition='nw')
        
        style.configure('Custom.TNotebook.Tab', 
                       padding=[15, 8],
                       background=self._bg,
                       foreground=self._fg,
                       borderwidth=0,
                       lightcolor=self._bg,
                       darkcolor=self._bg)
        
        style.map('Custom.TNotebook.Tab',
                  background=[('selected', self._accent),
                            ('active', self._accent)],
                  foreground=[('selected', self._fg),
                            ('active', self._fg)],
                  borderwidth=[('selected', 0),
                             ('active', 0)],
                  expand=[('selected', [1, 1, 1, 0])])

        # Status at top of sidebar
        self.status_var = tk.StringVar(value='Initializing...')
        status = tk.Label(self.sidebar, textvariable=self.status_var,
                         anchor='w', bg=self._bg_darker, fg=self._fg,
                         wraplength=220, font=('Segoe UI', 9))
        status.pack(fill='x', padx=16, pady=(16, 24))

        # Navigation buttons with card-like style
        nav_frame = tk.Frame(self.sidebar, bg=self._bg_darker)
        nav_frame.pack(fill='x', padx=12, pady=4)

        def create_nav_button(text, command, symbol):
            # Card-like container with flexible height and internal padding
            container = tk.Frame(nav_frame, bg=self._bg_lighter, bd=0, relief='flat')
            container.pack(fill='x', padx=6, pady=8)
            container.pack_propagate(True)

            # Icon on the left (generated image)
            icon_img = _make_icon(symbol, size=28, fg=self._fg)
            if icon_img:
                icon = tk.Label(container, image=icon_img, bg=self._bg_lighter)
                icon.image = icon_img
            else:
                icon = tk.Label(container, text=' ', bg=self._bg_lighter)
            icon.pack(side='left', padx=(6, 8))

            # Text taking remaining space
            btn = tk.Label(container, text=text, bg=self._bg_lighter, fg=self._fg,
                           font=('Segoe UI', 11), anchor='w', padx=8)
            btn.pack(side='left', fill='x', expand=True)

            # Hover helpers to avoid late-binding pitfalls
            def on_enter(e, c=container, i=icon, b=btn):
                c.configure(bg=self._hover_accent)
                i.configure(bg=self._hover_accent, fg='white')
                b.configure(bg=self._hover_accent, fg='white')

            def on_leave(e, c=container, i=icon, b=btn):
                c.configure(bg=self._bg_lighter)
                i.configure(bg=self._bg_lighter, fg=self._fg)
                b.configure(bg=self._bg_lighter, fg=self._fg)

            for widget in (container, icon, btn):
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)
                widget.bind('<Button-1>', lambda e, cmd=command: cmd())

        # Navigation section (use icon keys instead of emoji)
        create_nav_button('Chat', lambda: self._show_frame('chat'), 'chat')
        create_nav_button('Voice', lambda: self._show_frame('voice'), 'mic')
        create_nav_button('Devices', lambda: self._show_frame('devices'), 'plug')

        # Prepare logo spot at bottom of sidebar
        self.sidebar_bottom = tk.Frame(self.sidebar, bg=self._bg_darker)
        self.sidebar_bottom.pack(side='bottom', fill='x', padx=8, pady=12)
        try:
            # Try to load and scale logo for sidebar
            logo_path = r"C:\Users\ayden\Downloads\62A51B93-2B4B-417F-95B7-F14B733F978C.PNG"
            from PIL import Image, ImageTk
            pil_img = Image.open(logo_path)
            max_w = 200
            w, h = pil_img.size
            ratio = max_w / w
            scaled_h = int(h * ratio)
            pil_img = pil_img.resize((max_w, scaled_h), Image.LANCZOS)
            img = ImageTk.PhotoImage(pil_img)
            self.logo_label = tk.Label(self.sidebar_bottom, image=img, bg=self._bg_darker)
            self.logo_label.image = img
            self.logo_label.pack()
        except Exception:
            pass  # Logo optional
        # Create frame container with padding so there's no visible gap
        self.content_container = tk.Frame(self.content, bg=self._bg_lighter)
        self.content_container.pack(expand=1, fill='both', padx=12, pady=12)

        # Create frames dictionary
        self.frames = {}

        # Build all frames
        chat_frame = tk.Frame(self.content_container, bg=self._bg_lighter)
        self._build_chat_frame(chat_frame)
        self.frames['chat'] = chat_frame

        voice_frame = tk.Frame(self.content_container, bg=self._bg)
        self._build_voice_frame(voice_frame)
        self.frames['voice'] = voice_frame

        devices_frame = tk.Frame(self.content_container, bg=self._bg)
        self._build_devices_frame(devices_frame)
        self.frames['devices'] = devices_frame

        # Show default frame
        self._show_frame('chat')

        # Update model status in background
        threading.Thread(target=self._update_model_status, daemon=True).start()

    def _update_model_status(self):
        ok = check_model_availability()
        self.status_var.set('Model available' if ok else 'Model not available — run ollama serve and pull qwen3:8b')

    def _show_frame(self, name):
        # Hide all frames
        for frame in self.frames.values():
            frame.pack_forget()
        # Show requested frame
        self.frames[name].pack(expand=True, fill='both')

    def _build_chat_frame(self, frame):
        """Build the chat interface in the given frame"""
        default_font = tkfont.nametofont('TkDefaultFont')
        default_font.configure(size=11)
        mono = tkfont.Font(family='Segoe UI', size=11)

        # Chat display area
        self.chat_text = tk.Text(
            frame, 
            wrap='word', 
            state='disabled', 
            font=('Segoe UI', 10),
            bg=self._bg_lighter,
            fg=self._fg,
            bd=0,
            relief='flat',
            padx=12,
            pady=12,
            insertbackground=self._fg,
            selectbackground=self._accent,
            selectforeground=self._fg
        )
        self.chat_text.pack(side='top', expand=1, fill='both', padx=16, pady=16)

        # Bottom controls with modern styling (use lighter bg so there's no dark strip)
        bottom = tk.Frame(frame, bg=self._bg_lighter)
        bottom.pack(side='bottom', fill='x', padx=16, pady=(0, 16))

        # Input border around typing field + buttons
        input_border = tk.Frame(bottom, bg=self._bg_lighter, highlightthickness=1, highlightbackground=self._bg)
        input_border.pack(side='left', expand=1, fill='x', padx=0, pady=6)

        # Input container holds the Entry
        input_container = tk.Frame(input_border, bg=self._bg_lighter, bd=0, relief='flat')
        input_container.pack(side='left', expand=1, fill='x', padx=(8, 4), pady=4)

        self.input_var = tk.StringVar()
        entry = tk.Entry(
            input_container,
            textvariable=self.input_var,
            font=('Segoe UI', 10),
            bg=self._bg_lighter,
            fg=self._fg,
            insertbackground=self._fg,
            relief='flat',
            bd=0
        )
        entry.pack(side='left', expand=1, fill='x', padx=4, pady=4)
        entry.bind('<Return>', lambda e: self.on_send())
        entry.focus_set()

        # Controls frame inside the input border holds icon buttons and Send button
        controls = tk.Frame(input_border, bg=self._bg_lighter)
        controls.pack(side='right', padx=(4, 8), pady=4)

        # Utility buttons with consistent styling
        btn_cfg = dict(
            bg=self._bg_lighter,  # blend buttons with panel so only the icon shows
            fg=self._fg,
            activebackground=self._hover_accent,
            activeforeground='white',
            bd=0,
            padx=8,
            pady=8,
            font=('Segoe UI', 9),
            takefocus=0
        )

        # Generated icons for the small buttons
        clear_img = _make_icon('trash', size=18, fg=self._fg)
        save_img = _make_icon('save', size=18, fg=self._fg)
        copy_img = _make_icon('copy', size=18, fg=self._fg)

        clear_btn = tk.Button(
            controls,
            image=clear_img,
            command=self.clear_conversation,
            bg=btn_cfg['bg'], fg=btn_cfg['fg'], bd=0, relief='flat', highlightthickness=0,
            activebackground=btn_cfg['activebackground'], padx=6, pady=4, takefocus=btn_cfg['takefocus']
        )
        clear_btn.image = clear_img
        clear_btn.pack(side='left', padx=6)

        save_btn = tk.Button(
            controls,
            image=save_img,
            command=self.save_conversation,
            bg=btn_cfg['bg'], fg=btn_cfg['fg'], bd=0, relief='flat', highlightthickness=0,
            activebackground=btn_cfg['activebackground'], padx=6, pady=4, takefocus=btn_cfg['takefocus']
        )
        save_btn.image = save_img
        save_btn.pack(side='left', padx=6)

        copy_btn = tk.Button(
            controls,
            image=copy_img,
            command=self.copy_last_response,
            bg=btn_cfg['bg'], fg=btn_cfg['fg'], bd=0, relief='flat', highlightthickness=0,
            activebackground=btn_cfg['activebackground'], padx=6, pady=4, takefocus=btn_cfg['takefocus']
        )
        copy_btn.image = copy_img
        copy_btn.pack(side='left', padx=6)
        Tooltip(clear_btn, 'Clear chat')
        Tooltip(save_btn, 'Save chat')
        Tooltip(copy_btn, 'Copy last response')

        send_btn = tk.Button(
            controls,
            text='Send',
            command=self.on_send,
            bg=self._accent,
            fg='white',
            activebackground=self._accent,
            activeforeground='white',
            bd=0,
            padx=12,
            pady=6,
            font=('Segoe UI', 10)
        )
        send_btn.pack(side='left', padx=(8, 0))
    def _build_voice_frame(self, frame):

        self.voice_label = ttk.Label(frame, text='No file selected')
        self.voice_label.pack(fill='x', padx=8, pady=8)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=8)
        sel = ttk.Button(btn_frame, text='Select Audio File', command=self.select_audio)
        sel.pack(side='left')
        trans = ttk.Button(btn_frame, text='Transcribe & Send', command=self.on_transcribe)
        trans.pack(side='left', padx=6)

        self.voice_resp = tk.Text(frame, wrap='word', state='disabled', height=10)
        self.voice_resp.pack(expand=1, fill='both', padx=8, pady=8)
        self.selected_audio = None

    def _build_devices_frame(self, frame):

        discover_btn = ttk.Button(frame, text='Discover Devices', command=self.on_discover)
        discover_btn.pack(padx=8, pady=6)

        self.devices_list = tk.Listbox(frame)
        self.devices_list.pack(expand=1, fill='both', padx=8, pady=6)

    def append_chat(self, text: str):
        self.chat_text.configure(state='normal')
        self.chat_text.insert('end', text + '\n')
        self.chat_text.configure(state='disabled')
        self.chat_text.see('end')

    def clear_conversation(self):
        self.chat_text.configure(state='normal')
        self.chat_text.delete('1.0', 'end')
        self.chat_text.configure(state='disabled')

    def save_conversation(self):
        content = self.chat_text.get('1.0', 'end').strip()
        if not content:
            messagebox.showinfo('Save', 'Nothing to save')
            return
        fn = filedialog.asksaveasfilename(defaultextension='.md', filetypes=[('Markdown','*.md'), ('Text','*.txt')])
        if fn:
            try:
                with open(fn, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo('Saved', f'Saved to {fn}')
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def copy_last_response(self):
        text = self.chat_text.get('1.0', 'end').strip().splitlines()
        for line in reversed(text):
            if line.startswith('F.R.A.N.C.I.S:'):
                resp = line[len('F.R.A.N.C.I.S:'):].strip()
                try:
                    self.clipboard_clear()
                    self.clipboard_append(resp)
                    messagebox.showinfo('Copied', 'Last response copied to clipboard')
                except Exception as e:
                    messagebox.showerror('Error', str(e))
                return
        messagebox.showinfo('Copy', 'No response found to copy')

    def on_send(self):
        prompt = self.input_var.get().strip()
        if not prompt:
            return
        self.append_chat(f'You: {prompt}')
        self.input_var.set('')
        self.append_chat('Thinking...')
        ctx = get_project_context(prompt)
        worker = TkWorker(generate_response, args=(prompt, ctx), callback=lambda out: self.after(0, self._on_response, out))
        worker.start()

    def _on_response(self, out):
        # Remove 'Thinking...' — simple approach: just append response
        self.append_chat(f'F.R.A.N.C.I.S: {out}')

    def select_audio(self):
        fn = filedialog.askopenfilename(title='Select audio file', filetypes=[('Audio', '*.wav *.mp3 *.flac')])
        if fn:
            self.selected_audio = fn
            self.voice_label.config(text=fn)

    def on_transcribe(self):
        if not self.selected_audio:
            messagebox.showinfo('No file', 'Please select an audio file first')
            return
        try:
            import speech_recognition as sr
        except Exception:
            messagebox.showwarning('Missing dependency', "Install 'speechrecognition' to enable audio transcription")
            return

        def transcribe(path):
            r = sr.Recognizer()
            with sr.AudioFile(path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio)
            return text

        self.voice_resp.configure(state='normal')
        self.voice_resp.delete('1.0', 'end')
        self.voice_resp.insert('end', 'Transcribing...')
        self.voice_resp.configure(state='disabled')

        worker = TkWorker(transcribe, args=(self.selected_audio,), callback=lambda out: self.after(0, self._on_transcribed, out))
        worker.start()

    def _on_transcribed(self, text):
        self.voice_resp.configure(state='normal')
        self.voice_resp.insert('end', f'\nTranscript: {text}\n')
        self.voice_resp.configure(state='disabled')
        ctx = get_project_context(text)
        worker = TkWorker(generate_response, args=(text, ctx), callback=lambda out: self.after(0, lambda: self.voice_resp.configure(state='normal') or self.voice_resp.insert('end', f'\nF.R.A.N.C.I.S: {out}\n') or self.voice_resp.configure(state='disabled')))
        worker.start()

    def on_discover(self):
        self.devices_list.delete(0, 'end')
        self.devices_list.insert('end', 'Discovering...')
        worker = TkWorker(discover_devices, callback=lambda out: self.after(0, self._on_devices, out))
        worker.start()

    def _on_devices(self, out):
        self.devices_list.delete(0, 'end')
        try:
            import ast
            devices = ast.literal_eval(out) if isinstance(out, str) and (out.strip().startswith('[') or out.strip().startswith('{')) else out
        except Exception:
            devices = out
        if isinstance(devices, list):
            for d in devices:
                addr = d.get('address', 'unknown')
                resp = d.get('response', '')
                self.devices_list.insert('end', f"{addr} — {resp.splitlines()[0] if resp else ''}")
        else:
            self.devices_list.insert('end', str(devices))


def main():
    # Modern splash screen
    splash_bg = '#1E1E1E'  # Match main window dark gray
    splash_fg = '#E0E0E0'  # Match main window text color
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg=splash_bg)
    w, h = 480, 280  # Slightly larger for better proportions
    ws = splash.winfo_screenwidth()
    hs = splash.winfo_screenheight()
    x = (ws - w) // 2
    y = (hs - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")
    
    # Add a subtle border
    splash_frame = tk.Frame(splash, bg='#2D2D2D', bd=1)
    splash_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    
    inner_frame = tk.Frame(splash_frame, bg=splash_bg)
    inner_frame.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)

    lbl = tk.Label(splash, text='Rebhan Industries', font=('Segoe UI', 20, 'bold'), bg=splash_bg, fg=splash_fg)
    lbl.pack(expand=True)
    # Try to load provided logo (PNG). Fall back to text placeholder on failure.
    logo_path = r"C:\Users\ayden\Downloads\62A51B93-2B4B-417F-95B7-F14B733F978C.PNG"
    # Prefer Pillow for robust PNG loading + resizing; fall back to PhotoImage if Pillow not available
    try:
        from PIL import Image, ImageTk
        try:
            pil_img = Image.open(logo_path)
            # Resize to fit within splash while preserving aspect ratio
            max_w, max_h = 360, 110
            pil_img.thumbnail((max_w, max_h), Image.LANCZOS)
            img = ImageTk.PhotoImage(pil_img)
            logo = tk.Label(splash, image=img, bg=splash_bg)
            logo.image = img
            logo.pack()

            # Derive a simple accent color from the image (average color)
            small = pil_img.convert('RGBA').resize((20, 20))
            pixels = list(small.getdata())
            r = sum(p[0] for p in pixels) / len(pixels)
            g = sum(p[1] for p in pixels) / len(pixels)
            b = sum(p[2] for p in pixels) / len(pixels)
            accent_hex = '#%02x%02x%02x' % (int(r), int(g), int(b))
            # store derived theme for the main app to consume
            THEME['accent'] = accent_hex
            # choose contrasting fg/bg
            luminance = (0.2126*r + 0.7152*g + 0.0722*b)
            if luminance < 128:
                # Avoid pure black; choose a very dark gray instead
                THEME['bg'] = '#0f0f0f'
                THEME['fg'] = '#FFFFFF'
            else:
                THEME['bg'] = '#FFFFFF'
                THEME['fg'] = '#111111'
        except Exception:
            raise
    except Exception:
        try:
            img = tk.PhotoImage(file=logo_path)
            logo = tk.Label(splash, image=img, bg=splash_bg)
            logo.image = img
            logo.pack()
        except Exception:
            logo = tk.Label(splash, text='[ Logo / Company ]', bg=splash_bg, fg=splash_fg)
            logo.pack()
    splash_status_var = tk.StringVar(value='Checking model...')
    splash_status = tk.Label(splash, textvariable=splash_status_var, bg=splash_bg, fg=splash_fg)
    splash_status.pack()
    pb = ttk.Progressbar(splash, mode='indeterminate', length=300)
    pb.pack(pady=10)
    pb.start(10)

    def _check():
        try:
            ok = check_model_availability()
        except Exception:
            ok = False
        # update status text on the main thread
        try:
            splash.after(0, lambda: splash_status_var.set('Model available' if ok else 'Model not available'))
        except Exception:
            pass
        # give user a short moment to read status
        time.sleep(0.8)
        try:
            # stop progressbar before destroying to avoid tk internals trying to access widgets after destroy
            splash.after(0, lambda: pb.stop())
            splash.after(0, splash.destroy)
        except Exception:
            pass

    threading.Thread(target=_check, daemon=True).start()
    splash.mainloop()

    # Start main app
    app = FrancisApp()
    app.mainloop()


if __name__ == '__main__':
    main()

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import sys
import os
import shutil
from facefusion import hardware_helper, metadata, installer
from facefusion.common_helper import is_linux, is_windows

class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{metadata.get('name')} - Setup Wizard")
        self.geometry("600x450")
        self.resizable(False, False)
        self.configure(bg="#1a1a1a")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.set_styles()

        self.current_step = 0
        self.install_settings = {
            'provider': hardware_helper.detect_hardware(),
            'force_reinstall': False
        }

        self.container = tk.Frame(self, bg="#1a1a1a")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self.pages = [
            WelcomePage(self.container, self),
            PrerequisitePage(self.container, self),
            HardwarePage(self.container, self),
            InstallPage(self.container, self),
            FinishPage(self.container, self)
        ]

        self.show_page(0)

    def set_styles(self):
        self.style.configure("TFrame", background="#1a1a1a")
        self.style.configure("TLabel", background="#1a1a1a", foreground="white", font=("Arial", 10))
        self.style.configure("Header.TLabel", background="#1a1a1a", foreground="#ff3b3b", font=("Arial", 18, "bold"))
        self.style.configure("TButton", padding=10, font=("Arial", 10, "bold"))
        self.style.configure("Primary.TButton", background="#ff3b3b", foreground="white")
        self.style.map("Primary.TButton", background=[('active', '#e60000')])
        self.style.configure("Horizontal.TProgressbar", thickness=20)

    def show_page(self, index):
        for i, page in enumerate(self.pages):
            if i == index:
                page.pack(fill="both", expand=True)
                page.on_show()
            else:
                page.pack_forget()
        self.current_step = index

    def next_step(self):
        if self.current_step < len(self.pages) - 1:
            self.show_page(self.current_step + 1)

    def prev_step(self):
        if self.current_step > 0:
            self.show_page(self.current_step - 1)

class Page(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1a1a1a")
        self.controller = controller

    def on_show(self):
        pass

class WelcomePage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = ttk.Label(self, text="Welcome to FaceFusion", style="Header.TLabel")
        label.pack(pady=(20, 10))

        desc = ttk.Label(self, text="This installer will guide you through the setup of FaceFusion,\nthe industry-leading face manipulation platform.\n\nWe will check your system for prerequisites and\nconfigure your hardware acceleration automatically.", justify="center")
        desc.pack(pady=20)

        btn = ttk.Button(self, text="Start Installation", command=controller.next_step)
        btn.pack(side="bottom", pady=20)

class PrerequisitePage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = ttk.Label(self, text="System Check", style="Header.TLabel")
        label.pack(pady=20)

        self.results_frame = tk.Frame(self, bg="#1a1a1a")
        self.results_frame.pack(fill="x", padx=40)

        self.check_btn = ttk.Button(self, text="Continue", state="disabled", command=controller.next_step)
        self.check_btn.pack(side="bottom", pady=20)

    def on_show(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        checks = [
            ("Python Version", sys.version.split()[0], sys.version_info >= (3, 10)),
            ("FFMPEG", "Found" if shutil.which("ffmpeg") else "Not Found", bool(shutil.which("ffmpeg"))),
            ("NPM", "Found" if shutil.which("npm") else "Optional", True)
        ]

        all_ok = True
        for name, value, ok in checks:
            color = "#00ff00" if ok else "#ff3b3b"
            row = tk.Frame(self.results_frame, bg="#1a1a1a")
            row.pack(fill="x", pady=5)
            tk.Label(row, text=name, bg="#1a1a1a", fg="white", font=("Arial", 10)).pack(side="left")
            tk.Label(row, text=value, bg="#1a1a1a", fg=color, font=("Arial", 10, "bold")).pack(side="right")
            if not ok and name != "NPM": all_ok = False

        if all_ok:
            self.check_btn.config(state="normal")
        else:
            tk.Label(self, text="Please install missing prerequisites to continue.", fg="#ff3b3b", bg="#1a1a1a").pack(pady=10)

class HardwarePage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = ttk.Label(self, text="Hardware Discovery", style="Header.TLabel")
        label.pack(pady=20)

        self.provider_var = tk.StringVar(value=controller.install_settings['provider'])

        desc = ttk.Label(self, text="We've detected the following optimal provider for your GPU:")
        desc.pack(pady=10)

        providers = [
            ('cuda', 'NVIDIA CUDA (TensorRT)'),
            ('rocm', 'AMD ROCm'),
            ('coreml', 'Apple CoreML'),
            ('directml', 'Windows DirectML'),
            ('cpu', 'CPU Only (Slow)')
        ]

        for code, name in providers:
            rb = tk.Radiobutton(self, text=name, variable=self.provider_var, value=code, 
                                bg="#1a1a1a", fg="white", selectcolor="#ff3b3b", 
                                font=("Arial", 10), activebackground="#1a1a1a", activeforeground="white")
            rb.pack(anchor="w", padx=60, pady=2)

        btn_frame = tk.Frame(self, bg="#1a1a1a")
        btn_frame.pack(side="bottom", fill="x", pady=20)
        ttk.Button(btn_frame, text="Back", command=controller.prev_step).pack(side="left", padx=20)
        ttk.Button(btn_frame, text="Next", command=self.save_and_next).pack(side="right", padx=20)

    def save_and_next(self):
        self.controller.install_settings['provider'] = self.provider_var.get()
        self.controller.next_step()

class InstallPage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.label = ttk.Label(self, text="Installing Dependencies...", style="Header.TLabel")
        self.label.pack(pady=20)

        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar")
        self.progress.pack(fill="x", padx=40, pady=20)

        self.log = tk.Text(self, height=10, bg="#0d0d0d", fg="#00ff00", font=("Consolas", 9), borderwidth=0)
        self.log.pack(fill="both", expand=True, padx=40)

        self.btn = ttk.Button(self, text="Finish", state="disabled", command=controller.next_step)
        self.btn.pack(side="bottom", pady=20)

    def on_show(self):
        threading.Thread(target=self.run_install, daemon=True).start()

    def update_log(self, text):
        self.log.insert("end", text)
        self.log.see("end")

    def run_install(self):
        provider = self.controller.install_settings['provider']
        self.update_log(f"Starting installation for {provider}...\n")
        
        # In a real scenario, we'd run the commands from installer.py
        # For this demo/task, I'll simulate or call the actual logic
        try:
            # 1. Pip Install
            self.update_log("Installing pip requirements...\n")
            self.progress['value'] = 20
            
            # Simulated call to actual installer logic (adapted for progress)
            self.execute_install_logic()
            
            self.progress['value'] = 100
            self.label.config(text="Installation Complete!")
            self.btn.config(state="normal")
        except Exception as e:
            self.update_log(f"\nERROR: {str(e)}")
            messagebox.showerror("Installation Failed", str(e))

    def execute_install_logic(self):
        # This mirrors the logic in installer.py but with GUI updates
        provider = self.controller.install_settings['provider']
        commands = [ sys.executable, '-m', 'pip', 'install', '--quiet' ]
        
        # Read requirements
        with open('requirements.txt') as f:
            for line in f:
                lib = line.strip()
                if lib and not lib.startswith('onnxruntime'):
                    commands.append(lib)
        
        # Add onnxruntime
        pkg = hardware_helper.get_onnx_package(provider)
        commands.append(pkg)

        # Run Command
        self.update_log(f"Running: {' '.join(commands)}\n")
        process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            self.update_log(line)
        process.wait()

        # Frontend
        web_path = os.path.join(os.getcwd(), 'web')
        if os.path.exists(web_path) and shutil.which('npm'):
            self.update_log("\nInstalling frontend (NPM)...\n")
            npm_process = subprocess.Popen([shutil.which('npm'), 'install'], cwd=web_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in npm_process.stdout:
                self.update_log(line)
            npm_process.wait()

class FinishPage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = ttk.Label(self, text="Setup Successful!", style="Header.TLabel")
        label.pack(pady=40)

        desc = ttk.Label(self, text="FaceFusion is now fully installed and configured.\n\nYou can launch the application using the \n'launch.py' script or the created shortcuts.", justify="center")
        desc.pack(pady=20)

        btn = ttk.Button(self, text="Exit", command=controller.quit)
        btn.pack(side="bottom", pady=40)

    def on_show(self):
        # Create shortcuts on finish
        install_path = os.getcwd()
        installer.create_user_config(install_path)
        if is_linux():
            installer.create_linux_desktop_file(install_path)
        elif is_windows():
            installer.create_windows_launcher(install_path)

def run():
    app = InstallerApp()
    app.mainloop()

if __name__ == "__main__":
    run()

"""
FaceFusion Qt6 Installer - Install Page
=======================================
Multi-stage installation progress with detailed logging.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPlainTextEdit, QFrame, QSpacerItem, 
    QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, QThread, Signal, Slot

from facefusion.qt_installer.utils.platform_utils import (
    get_requirements_path, get_web_path, get_npm_path, get_python_executable
)
from facefusion.qt_installer.utils.gpu_detector import (
    ExecutionProvider, get_onnxruntime_package
)


class InstallWorker(QThread):
    """Background worker for running installation steps."""
    
    # Signals
    log_message = Signal(str)
    stage_changed = Signal(str, int)  # stage_name, progress_percent
    error_occurred = Signal(str)
    finished_successfully = Signal()
    
    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        try:
            # Stage 1: Install Python requirements (0-40%)
            self._install_requirements()
            if self._cancelled:
                return
            
            # Stage 2: Install ONNX Runtime (40-60%)
            self._install_onnxruntime()
            if self._cancelled:
                return
            
            # Stage 3: Install TensorRT if selected (60-75%)
            if self.settings.get('install_tensorrt') and self.settings.get('provider') == 'cuda':
                self._install_tensorrt()
            if self._cancelled:
                return
            
            # Stage 4: Install frontend (75-95%)
            if self.settings.get('install_frontend'):
                self._install_frontend()
            if self._cancelled:
                return
            
            # Stage 5: Create shortcuts (95-100%)
            if self.settings.get('create_shortcuts'):
                self._create_shortcuts()
            
            self.finished_successfully.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> bool:
        """Run a command and stream output to log."""
        self.log_message.emit(f"$ {' '.join(cmd)}\n")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=cwd,
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                if self._cancelled:
                    process.terminate()
                    return False
                self.log_message.emit(line)
            
            process.wait()
            return process.returncode == 0
            
        except Exception as e:
            self.log_message.emit(f"ERROR: {e}\n")
            return False
    
    def _install_requirements(self):
        """Install Python requirements from requirements.txt."""
        self.stage_changed.emit("Installing Python dependencies...", 10)
        self.log_message.emit("\n=== Installing Python Dependencies ===\n")
        
        req_path = get_requirements_path()
        if not req_path.exists():
            self.log_message.emit(f"Warning: {req_path} not found\n")
            return
        
        # Build pip command
        python = get_python_executable()
        cmd = [python, '-m', 'pip', 'install', '--upgrade']
        
        # Read requirements (excluding onnxruntime which we handle separately)
        with open(req_path) as f:
            for line in f:
                pkg = line.strip()
                if pkg and not pkg.startswith('#') and 'onnxruntime' not in pkg.lower():
                    cmd.append(pkg)
        
        success = self._run_command(cmd)
        if not success:
            self.error_occurred.emit("Failed to install Python dependencies")
        
        self.stage_changed.emit("Python dependencies installed", 40)
    
    def _install_onnxruntime(self):
        """Install the appropriate ONNX Runtime package."""
        self.stage_changed.emit("Installing ONNX Runtime...", 45)
        self.log_message.emit("\n=== Installing ONNX Runtime ===\n")
        
        provider_str = self.settings.get('provider', 'cpu')
        
        # Map string to enum
        try:
            provider = ExecutionProvider(provider_str)
        except ValueError:
            provider = ExecutionProvider.CPU
        
        package = get_onnxruntime_package(provider)
        
        python = get_python_executable()
        cmd = [python, '-m', 'pip', 'install', '--upgrade', package]
        
        success = self._run_command(cmd)
        if not success:
            self.log_message.emit("Warning: ONNX Runtime installation may have issues\n")
        
        self.stage_changed.emit("ONNX Runtime installed", 60)
    
    def _install_tensorrt(self):
        """Install TensorRT for NVIDIA acceleration."""
        self.stage_changed.emit("Installing TensorRT...", 62)
        self.log_message.emit("\n=== Installing TensorRT ===\n")
        
        python = get_python_executable()
        cmd = [python, '-m', 'pip', 'install', 'tensorrt', 
               '--extra-index-url', 'https://pypi.nvidia.com']
        
        success = self._run_command(cmd)
        if not success:
            self.log_message.emit("Warning: TensorRT installation may have issues\n")
        
        self.stage_changed.emit("TensorRT installed", 75)
    
    def _install_frontend(self):
        """Install web frontend dependencies."""
        self.stage_changed.emit("Installing web frontend...", 78)
        self.log_message.emit("\n=== Installing Web Frontend ===\n")
        
        web_path = get_web_path()
        npm = get_npm_path()
        
        if not web_path.exists():
            self.log_message.emit(f"Skipping: {web_path} not found\n")
            return
        
        if not npm:
            self.log_message.emit("Skipping: npm not found\n")
            return
        
        success = self._run_command([npm, 'install'], cwd=web_path)
        if not success:
            self.log_message.emit("Warning: Frontend installation may have issues\n")
        
        self.stage_changed.emit("Frontend installed", 95)
    
    def _create_shortcuts(self):
        """Create desktop shortcuts."""
        self.stage_changed.emit("Creating shortcuts...", 97)
        self.log_message.emit("\n=== Creating Shortcuts ===\n")
        
        # This is platform-specific and handled by installer.py functions
        try:
            from facefusion.installer import (
                create_user_config, create_linux_desktop_file, 
                create_windows_launcher, get_platform
            )
            import os
            
            install_path = os.getcwd()
            create_user_config(install_path)
            
            platform = get_platform()
            if platform == 'linux':
                create_linux_desktop_file(install_path)
                self.log_message.emit("Created Linux desktop entry\n")
            elif platform == 'windows':
                create_windows_launcher(install_path)
                self.log_message.emit("Created Windows launcher\n")
            else:
                self.log_message.emit("Shortcuts not supported on this platform\n")
                
        except Exception as e:
            self.log_message.emit(f"Warning: Could not create shortcuts: {e}\n")
        
        self.stage_changed.emit("Installation complete!", 100)


class InstallPage(QWizardPage):
    """Installation progress page with multi-stage progress and log viewer."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("Installing FaceFusion")
        self.setSubTitle("Please wait while dependencies are installed...")
        self.setCommitPage(True)  # Disable back button
        
        self._installation_complete = False
        self._installation_failed = False
        self.worker: Optional[InstallWorker] = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(16)
        
        # Current stage label
        self.stage_label = QLabel("Preparing installation...")
        self.stage_label.setProperty("subheading", True)
        layout.addWidget(self.stage_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)
        
        # Log viewer
        log_label = QLabel("Installation Log:")
        layout.addWidget(log_label)
        
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)  # Limit memory usage
        layout.addWidget(self.log_view, 1)
        
        # Status/error area
        self.status_frame = QFrame()
        status_layout = QHBoxLayout(self.status_frame)
        
        self.status_icon = QLabel()
        self.status_icon.setFixedWidth(40)
        status_layout.addWidget(self.status_icon)
        
        self.status_text = QLabel()
        self.status_text.setWordWrap(True)
        status_layout.addWidget(self.status_text, 1)
        
        layout.addWidget(self.status_frame)
        self.status_frame.hide()
    
    def initializePage(self):
        """Start installation when page is shown."""
        wizard = self.wizard()
        settings = wizard.install_settings.copy()
        
        self._installation_complete = False
        self._installation_failed = False
        self.log_view.clear()
        self.progress_bar.setValue(0)
        self.status_frame.hide()
        
        # Start worker
        self.worker = InstallWorker(settings)
        self.worker.log_message.connect(self._on_log_message)
        self.worker.stage_changed.connect(self._on_stage_changed)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished_successfully.connect(self._on_success)
        self.worker.start()
    
    @Slot(str)
    def _on_log_message(self, message: str):
        """Append message to log viewer."""
        self.log_view.appendPlainText(message.rstrip())
        # Auto-scroll to bottom
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    @Slot(str, int)
    def _on_stage_changed(self, stage_name: str, progress: int):
        """Update stage label and progress bar."""
        self.stage_label.setText(stage_name)
        self.progress_bar.setValue(progress)
    
    @Slot(str)
    def _on_error(self, error_msg: str):
        """Handle installation error."""
        self._installation_failed = True
        self.status_frame.show()
        self.status_icon.setText("❌")
        self.status_text.setText(f"Installation failed: {error_msg}")
        self.status_text.setStyleSheet("color: #ff5252;")
        self.stage_label.setText("Installation failed")
        self.completeChanged.emit()
    
    @Slot()
    def _on_success(self):
        """Handle successful installation."""
        self._installation_complete = True
        self.status_frame.show()
        self.status_icon.setText("✅")
        self.status_text.setText("Installation completed successfully!")
        self.status_text.setStyleSheet("color: #4caf50;")
        self.stage_label.setText("Installation complete!")
        self.progress_bar.setValue(100)
        self.completeChanged.emit()
    
    def isComplete(self) -> bool:
        """Allow proceeding only after successful installation."""
        return self._installation_complete
    
    def cleanupPage(self):
        """Cancel worker if going back (shouldn't happen but safety first)."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)

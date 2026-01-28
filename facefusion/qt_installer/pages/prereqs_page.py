"""
FaceFusion Qt6 Installer - Prerequisites Page
==============================================
System requirements check with real-time validation.
"""

import sys
import shutil
import subprocess
from typing import Tuple, Optional

from PySide6.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSpacerItem, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from facefusion.qt_installer.utils.platform_utils import (
    get_python_version, get_ffmpeg_path, get_npm_path, get_node_path
)


class CheckWorker(QThread):
    """Background worker for running system checks."""
    check_complete = Signal(str, str, bool, str)  # name, value, ok, hint
    all_checks_done = Signal(bool)  # all_passed
    
    def run(self):
        all_passed = True
        
        # Python version check
        py_version = get_python_version()
        py_ok = sys.version_info >= (3, 10)
        self.check_complete.emit(
            "Python Version",
            py_version,
            py_ok,
            "Python 3.10 or higher required" if not py_ok else ""
        )
        if not py_ok:
            all_passed = False
        
        # FFmpeg check
        ffmpeg = get_ffmpeg_path()
        ffmpeg_ok = ffmpeg is not None
        self.check_complete.emit(
            "FFmpeg",
            "Found" if ffmpeg_ok else "Not Found",
            ffmpeg_ok,
            "Install FFmpeg: https://ffmpeg.org/download.html" if not ffmpeg_ok else ""
        )
        if not ffmpeg_ok:
            all_passed = False
        
        # Node.js check (optional but recommended)
        node = get_node_path()
        node_version = None
        node_ok = True
        node_hint = ""
        
        if node:
            try:
                result = subprocess.run([node, '--version'], capture_output=True, text=True, timeout=5)
                node_version = result.stdout.strip()
                # Check if >= v20
                major = int(node_version.lstrip('v').split('.')[0])
                if major < 20:
                    node_ok = False
                    node_hint = "Node.js 20+ recommended for frontend"
            except Exception:
                node_version = "Error checking version"
                node_ok = False
        else:
            node_version = "Not Found (Optional)"
            node_ok = True  # Optional, so still OK
            node_hint = "Install Node.js for web frontend"
        
        self.check_complete.emit("Node.js", node_version, node_ok, node_hint)
        
        # NPM check
        npm = get_npm_path()
        npm_ok = True  # Optional
        self.check_complete.emit(
            "NPM",
            "Found" if npm else "Not Found (Optional)",
            npm_ok,
            ""
        )
        
        # Virtual environment check
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        self.check_complete.emit(
            "Virtual Environment",
            "Active" if in_venv else "Not Detected",
            True,  # Not blocking
            "Recommended: Install in a virtual environment" if not in_venv else ""
        )
        
        self.all_checks_done.emit(all_passed)


class PrerequisitesPage(QWizardPage):
    """Prerequisites check page with animated status indicators."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("System Requirements")
        self.setSubTitle("Checking your system for prerequisites...")
        
        self._checks_passed = False
        self._check_rows = {}
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(16)
        
        # Status label
        self.status_label = QLabel("Running system checks...")
        self.status_label.setProperty("subheading", True)
        layout.addWidget(self.status_label)
        
        # Checks container
        self.checks_frame = QFrame()
        self.checks_frame.setProperty("card", True)
        self.checks_layout = QVBoxLayout(self.checks_frame)
        self.checks_layout.setSpacing(12)
        layout.addWidget(self.checks_frame)
        
        # Hint area
        self.hint_frame = QFrame()
        hint_layout = QVBoxLayout(self.hint_frame)
        self.hint_label = QLabel()
        self.hint_label.setWordWrap(True)
        self.hint_label.setProperty("warning", True)
        hint_layout.addWidget(self.hint_label)
        layout.addWidget(self.hint_frame)
        self.hint_frame.hide()
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Recheck button
        self.recheck_btn = QPushButton("🔄 Recheck")
        self.recheck_btn.clicked.connect(self._run_checks)
        layout.addWidget(self.recheck_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Worker thread
        self.worker: Optional[CheckWorker] = None
    
    def initializePage(self):
        """Run checks when page is shown."""
        self._run_checks()
    
    def _run_checks(self):
        """Start background system checks."""
        # Clear previous results
        for row in self._check_rows.values():
            row.deleteLater()
        self._check_rows.clear()
        self.hint_label.clear()
        self.hint_frame.hide()
        self._checks_passed = False
        self.status_label.setText("Running system checks...")
        self.recheck_btn.setEnabled(False)
        self.completeChanged.emit()
        
        # Start worker
        self.worker = CheckWorker()
        self.worker.check_complete.connect(self._on_check_complete)
        self.worker.all_checks_done.connect(self._on_all_checks_done)
        self.worker.start()
    
    def _create_check_row(self, name: str, value: str, ok: bool) -> QFrame:
        """Create a row for a single check result."""
        row = QFrame()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 8, 8, 8)
        
        # Status icon
        icon = "✅" if ok else "❌"
        icon_label = QLabel(icon)
        icon_label.setFixedWidth(30)
        row_layout.addWidget(icon_label)
        
        # Name
        name_label = QLabel(name)
        name_label.setFixedWidth(150)
        row_layout.addWidget(name_label)
        
        # Value
        value_label = QLabel(value)
        if ok:
            value_label.setProperty("success", True)
        else:
            value_label.setProperty("error", True)
        value_label.setStyleSheet(f"color: {'#4caf50' if ok else '#ff5252'};")
        row_layout.addWidget(value_label, 1)
        
        return row
    
    def _on_check_complete(self, name: str, value: str, ok: bool, hint: str):
        """Handle individual check completion."""
        row = self._create_check_row(name, value, ok)
        self.checks_layout.addWidget(row)
        self._check_rows[name] = row
        
        # Accumulate hints
        if hint:
            current = self.hint_label.text()
            if current:
                self.hint_label.setText(f"{current}\n• {hint}")
            else:
                self.hint_label.setText(f"• {hint}")
            self.hint_frame.show()
    
    def _on_all_checks_done(self, all_passed: bool):
        """Handle all checks completion."""
        self._checks_passed = all_passed
        self.recheck_btn.setEnabled(True)
        
        if all_passed:
            self.status_label.setText("✅ All system requirements met!")
            self.status_label.setStyleSheet("color: #4caf50;")
        else:
            self.status_label.setText("⚠️ Some requirements are missing (see above)")
            self.status_label.setStyleSheet("color: #ffc107;")
        
        self.completeChanged.emit()
    
    def isComplete(self) -> bool:
        """Page complete when all critical checks pass."""
        return self._checks_passed

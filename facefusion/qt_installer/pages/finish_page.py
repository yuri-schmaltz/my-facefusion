"""
FaceFusion Qt6 Installer - Finish Page
======================================
Success summary with launch options.
"""

import sys
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSpacerItem, QSizePolicy, QPushButton,
    QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from facefusion.qt_installer.utils.platform_utils import get_install_path


class FinishPage(QWizardPage):
    """Final page with success message and launch options."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("Installation Complete")
        self.setSubTitle("FaceFusion has been successfully installed!")
        self.setFinalPage(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(24)
        
        # Success message
        success_frame = QFrame()
        success_frame.setProperty("card", True)
        success_layout = QHBoxLayout(success_frame)
        
        success_icon = QLabel("🎉")
        success_icon.setStyleSheet("font-size: 48px;")
        success_layout.addWidget(success_icon)
        
        success_text = QLabel()
        success_text.setText(
            "<h2 style='color: #4caf50;'>Setup Successful!</h2>"
            "<p>FaceFusion is now fully installed and configured.</p>"
        )
        success_text.setWordWrap(True)
        success_layout.addWidget(success_text, 1)
        
        layout.addWidget(success_frame)
        
        # What's next section
        next_label = QLabel("<h3>What's Next?</h3>")
        layout.addWidget(next_label)
        
        instructions = QLabel()
        instructions.setText(
            "<ul>"
            "<li>Launch FaceFusion using the <b>launch.py</b> script</li>"
            "<li>Open your browser to <b>http://localhost:5173</b></li>"
            "<li>Upload a source face and target media to get started</li>"
            "</ul>"
        )
        instructions.setWordWrap(True)
        instructions.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(instructions)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Options
        self.launch_checkbox = QCheckBox("Launch FaceFusion now")
        self.launch_checkbox.setChecked(True)
        layout.addWidget(self.launch_checkbox)
        
        self.docs_checkbox = QCheckBox("Open documentation in browser")
        layout.addWidget(self.docs_checkbox)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Footer
        footer = QLabel()
        footer.setText(
            "<p style='color: #666666;'>Thank you for using FaceFusion!</p>"
            "<p style='color: #666666;'>⭐ Star us on GitHub: github.com/facefusion/facefusion</p>"
        )
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
    
    def initializePage(self):
        """Called when page is shown."""
        # Could add summary of installation here
        pass
    
    def validatePage(self) -> bool:
        """Handle finish actions."""
        # Open documentation if requested
        if self.docs_checkbox.isChecked():
            QDesktopServices.openUrl(QUrl("https://github.com/facefusion/facefusion"))
        
        # Launch FaceFusion if requested
        if self.launch_checkbox.isChecked():
            launch_path = get_install_path() / "launch.py"
            if launch_path.exists():
                subprocess.Popen(
                    [sys.executable, str(launch_path)],
                    start_new_session=True
                )
        
        return True

"""
FaceFusion Qt6 Installer - Welcome Page
=======================================
First wizard page with branding and introduction.
"""

from PySide6.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont


class WelcomePage(QWizardPage):
    """Welcome page with FaceFusion branding and getting started info."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("Welcome to FaceFusion")
        self.setSubTitle("The industry-leading face manipulation platform")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)
        
        # Logo area
        logo_frame = QFrame()
        logo_frame.setProperty("card", True)
        logo_layout = QHBoxLayout(logo_frame)
        
        logo_label = QLabel()
        logo_label.setText("🎭")  # Placeholder emoji as logo
        logo_label.setStyleSheet("font-size: 64px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        version_label = QLabel()
        version_label.setText("<h1 style='color: #ff3b3b;'>FaceFusion</h1>"
                             "<p style='color: #808080;'>Version 3.3.0</p>")
        version_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo_layout.addWidget(version_label, 1)
        
        layout.addWidget(logo_frame)
        
        # Description
        desc_label = QLabel()
        desc_label.setText(
            "<p>This setup wizard will guide you through the installation process.</p>"
            "<p>We will:</p>"
            "<ul>"
            "<li>Check your system for prerequisites (Python, FFmpeg)</li>"
            "<li>Detect your GPU and configure hardware acceleration</li>"
            "<li>Install all required Python dependencies</li>"
            "<li>Set up the web frontend (optional)</li>"
            "<li>Create desktop shortcuts</li>"
            "</ul>"
        )
        desc_label.setWordWrap(True)
        desc_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(desc_label)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Footer tip
        tip_label = QLabel()
        tip_label.setText("<p style='color: #666666;'>💡 Tip: For best performance, use an NVIDIA GPU with CUDA support.</p>")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tip_label)
    
    def initializePage(self):
        """Called when page is shown."""
        pass
    
    def isComplete(self) -> bool:
        """Page is always complete."""
        return True

#!/usr/bin/env python3
"""
FaceFusion Qt6 Installer - Main Entry Point
============================================
Handles QApplication setup, high DPI scaling, theming, and crash recovery.
"""

import sys
import signal
import traceback
from typing import Optional

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QIcon, QFont

from facefusion.qt_installer.wizard import InstallerWizard
from facefusion.qt_installer.styles.dark_theme import DARK_THEME_QSS


def setup_exception_handler(app: QApplication) -> None:
    """Install global exception handler for crash recovery."""
    def handle_exception(exc_type, exc_value, exc_tb):
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"[FATAL ERROR]\n{error_msg}", file=sys.stderr)
        
        # Show crash dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("FaceFusion Installer - Error")
        msg.setText("An unexpected error occurred.")
        msg.setDetailedText(error_msg)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        
        app.quit()
    
    sys.excepthook = handle_exception


def setup_signal_handlers() -> None:
    """Handle system signals for graceful shutdown."""
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        QCoreApplication.quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def run() -> int:
    """Main entry point for the Qt6 installer."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # Application metadata
    app.setApplicationName("FaceFusion Installer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FaceFusion")
    
    # Set application font
    font = QFont()
    font.setFamily("Segoe UI" if sys.platform == "win32" else "SF Pro Display" if sys.platform == "darwin" else "Ubuntu")
    font.setPointSize(10)
    app.setFont(font)
    
    # Apply dark theme
    app.setStyleSheet(DARK_THEME_QSS)
    
    # Setup handlers
    setup_signal_handlers()
    setup_exception_handler(app)
    
    # Create and show wizard
    wizard = InstallerWizard()
    wizard.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())

"""
FaceFusion Qt6 Installer - Main Wizard
======================================
QWizard-based installer with 6 wizard pages.
"""

from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QTextEdit, QRadioButton, QButtonGroup,
    QCheckBox, QFrame, QSpacerItem, QSizePolicy, QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QPixmap, QFont

from facefusion.qt_installer.pages.welcome_page import WelcomePage
from facefusion.qt_installer.pages.prereqs_page import PrerequisitesPage
from facefusion.qt_installer.pages.hardware_page import HardwarePage
from facefusion.qt_installer.pages.install_page import InstallPage
from facefusion.qt_installer.pages.finish_page import FinishPage


class InstallerWizard(QWizard):
    """Main installer wizard with modern UI and robust error handling."""
    
    # Page IDs
    PAGE_WELCOME = 0
    PAGE_PREREQS = 1
    PAGE_HARDWARE = 2
    PAGE_INSTALL = 3
    PAGE_FINISH = 4
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("FaceFusion — Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(700, 550)
        self.resize(750, 600)
        
        # Store installation settings
        self.install_settings = {
            'provider': 'cpu',
            'install_tensorrt': False,
            'install_frontend': True,
            'create_shortcuts': True
        }
        
        # Setup wizard options
        self.setOptions(
            QWizard.WizardOption.NoBackButtonOnStartPage |
            QWizard.WizardOption.NoBackButtonOnLastPage |
            QWizard.WizardOption.NoCancelButtonOnLastPage |
            QWizard.WizardOption.HaveHelpButton
        )
        
        # Custom button text
        self.setButtonText(QWizard.WizardButton.NextButton, "Next →")
        self.setButtonText(QWizard.WizardButton.BackButton, "← Back")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Finish")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Cancel")
        self.setButtonText(QWizard.WizardButton.HelpButton, "Help")
        
        # Add pages
        self.setPage(self.PAGE_WELCOME, WelcomePage(self))
        self.setPage(self.PAGE_PREREQS, PrerequisitesPage(self))
        self.setPage(self.PAGE_HARDWARE, HardwarePage(self))
        self.setPage(self.PAGE_INSTALL, InstallPage(self))
        self.setPage(self.PAGE_FINISH, FinishPage(self))
        
        # Connect signals
        self.helpRequested.connect(self._on_help_requested)
        self.currentIdChanged.connect(self._on_page_changed)
    
    def _on_help_requested(self):
        """Handle help button click."""
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Help")
        msg.setText("Need assistance with FaceFusion installation?")
        msg.setInformativeText(
            "Visit our documentation or GitHub repository for detailed guides and troubleshooting."
        )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        if msg.exec() == QMessageBox.StandardButton.Open:
            QDesktopServices.openUrl(QUrl("https://github.com/facefusion/facefusion"))
    
    def _on_page_changed(self, page_id: int):
        """Handle page transitions."""
        # Disable back button during installation
        if page_id == self.PAGE_INSTALL:
            self.button(QWizard.WizardButton.BackButton).setEnabled(False)
            self.button(QWizard.WizardButton.CancelButton).setEnabled(False)
    
    def get_setting(self, key: str):
        """Get an installation setting."""
        return self.install_settings.get(key)
    
    def set_setting(self, key: str, value):
        """Set an installation setting."""
        self.install_settings[key] = value

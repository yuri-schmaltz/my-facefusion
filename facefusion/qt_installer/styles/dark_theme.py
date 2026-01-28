"""
FaceFusion Dark Theme - QSS Stylesheet
=======================================
Modern dark theme matching FaceFusion branding.
"""

DARK_THEME_QSS = """
/* ==========================================================================
   Global Styles
   ========================================================================== */

QWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
    font-family: "Segoe UI", "SF Pro Display", "Ubuntu", sans-serif;
}

/* ==========================================================================
   QWizard
   ========================================================================== */

QWizard {
    background-color: #1a1a1a;
}

QWizard::title {
    color: #ffffff;
    font-size: 18px;
    font-weight: bold;
    padding: 10px 0;
}

QWizard::subTitle {
    color: #b0b0b0;
    font-size: 12px;
}

/* Wizard Buttons */
QWizard QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 6px;
    color: #e0e0e0;
    padding: 8px 20px;
    min-width: 100px;
    font-weight: 500;
}

QWizard QPushButton:hover {
    background-color: #3d3d3d;
    border-color: #505050;
}

QWizard QPushButton:pressed {
    background-color: #252525;
}

QWizard QPushButton:disabled {
    background-color: #1f1f1f;
    color: #666666;
    border-color: #333333;
}

/* Primary Button (Next/Finish) */
QWizard QPushButton#qt_wizard_commit,
QWizard QPushButton#qt_wizard_finish {
    background-color: #ff3b3b;
    border-color: #ff3b3b;
    color: #ffffff;
}

QWizard QPushButton#qt_wizard_commit:hover,
QWizard QPushButton#qt_wizard_finish:hover {
    background-color: #ff5555;
    border-color: #ff5555;
}

QWizard QPushButton#qt_wizard_commit:pressed,
QWizard QPushButton#qt_wizard_finish:pressed {
    background-color: #cc2f2f;
}

/* ==========================================================================
   Labels
   ========================================================================== */

QLabel {
    color: #e0e0e0;
    background-color: transparent;
}

QLabel[heading="true"] {
    font-size: 24px;
    font-weight: bold;
    color: #ffffff;
}

QLabel[subheading="true"] {
    font-size: 14px;
    color: #b0b0b0;
}

QLabel[success="true"] {
    color: #4caf50;
}

QLabel[error="true"] {
    color: #ff5252;
}

QLabel[warning="true"] {
    color: #ffc107;
}

/* ==========================================================================
   Progress Bar
   ========================================================================== */

QProgressBar {
    background-color: #2d2d2d;
    border: none;
    border-radius: 8px;
    height: 16px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff3b3b, stop:1 #ff6b6b);
    border-radius: 8px;
}

/* ==========================================================================
   Text Edit / Log Area
   ========================================================================== */

QTextEdit, QPlainTextEdit {
    background-color: #0d0d0d;
    border: 1px solid #333333;
    border-radius: 6px;
    color: #00ff00;
    font-family: "Consolas", "Monaco", "Ubuntu Mono", monospace;
    font-size: 11px;
    padding: 8px;
    selection-background-color: #ff3b3b;
}

/* ==========================================================================
   Radio Buttons & Checkboxes
   ========================================================================== */

QRadioButton, QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}

QRadioButton::indicator, QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #555555;
    border-radius: 4px;
    background-color: #2d2d2d;
}

QRadioButton::indicator {
    border-radius: 10px;
}

QRadioButton::indicator:checked, QCheckBox::indicator:checked {
    background-color: #ff3b3b;
    border-color: #ff3b3b;
}

QRadioButton::indicator:hover, QCheckBox::indicator:hover {
    border-color: #ff3b3b;
}

/* ==========================================================================
   Combo Box
   ========================================================================== */

QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 6px 12px;
    color: #e0e0e0;
    min-width: 150px;
}

QComboBox:hover {
    border-color: #ff3b3b;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    selection-background-color: #ff3b3b;
}

/* ==========================================================================
   Scroll Bars
   ========================================================================== */

QScrollBar:vertical {
    background-color: #1a1a1a;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #404040;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #505050;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1a1a1a;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #404040;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #505050;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ==========================================================================
   Group Box
   ========================================================================== */

QGroupBox {
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #ff3b3b;
}

/* ==========================================================================
   Frame
   ========================================================================== */

QFrame[card="true"] {
    background-color: #252525;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 16px;
}
"""

"""
FaceFusion Qt6 Installer - Hardware Page
========================================
GPU detection and execution provider selection.
"""

from PySide6.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSpacerItem, QSizePolicy, QRadioButton,
    QButtonGroup, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt

from facefusion.qt_installer.utils.gpu_detector import (
    detect_gpus, get_available_providers, get_recommended_provider,
    ExecutionProvider, GPUVendor
)


class HardwarePage(QWizardPage):
    """Hardware detection and provider selection page."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("Hardware Configuration")
        self.setSubTitle("Select your preferred execution provider for GPU acceleration")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)
        
        # Detected GPUs section
        gpu_group = QGroupBox("Detected GPUs")
        gpu_layout = QVBoxLayout(gpu_group)
        self.gpu_list_label = QLabel("Scanning for GPUs...")
        gpu_layout.addWidget(self.gpu_list_label)
        layout.addWidget(gpu_group)
        
        # Provider selection
        provider_group = QGroupBox("Execution Provider")
        provider_layout = QVBoxLayout(provider_group)
        
        self.provider_button_group = QButtonGroup(self)
        self.provider_buttons = {}
        
        # Will be populated in initializePage
        self.providers_container = QVBoxLayout()
        provider_layout.addLayout(self.providers_container)
        
        layout.addWidget(provider_group)
        
        # Additional options
        options_group = QGroupBox("Additional Options")
        options_layout = QVBoxLayout(options_group)
        
        self.tensorrt_checkbox = QCheckBox("Install TensorRT for maximum performance (NVIDIA only)")
        self.tensorrt_checkbox.setToolTip(
            "TensorRT provides 20-50% faster inference but requires additional setup time"
        )
        options_layout.addWidget(self.tensorrt_checkbox)
        
        self.frontend_checkbox = QCheckBox("Install web frontend (requires Node.js)")
        self.frontend_checkbox.setChecked(True)
        options_layout.addWidget(self.frontend_checkbox)
        
        self.shortcuts_checkbox = QCheckBox("Create desktop shortcuts")
        self.shortcuts_checkbox.setChecked(True)
        options_layout.addWidget(self.shortcuts_checkbox)
        
        layout.addWidget(options_group)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Performance hint
        self.perf_hint = QLabel()
        self.perf_hint.setWordWrap(True)
        self.perf_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.perf_hint)
    
    def initializePage(self):
        """Populate GPU and provider information."""
        # Detect GPUs
        gpus = detect_gpus()
        
        if gpus:
            gpu_text = "<ul>"
            for gpu in gpus:
                vendor_icon = {
                    GPUVendor.NVIDIA: "🟢",
                    GPUVendor.AMD: "🔴",
                    GPUVendor.INTEL: "🔵",
                    GPUVendor.APPLE: "⚪"
                }.get(gpu.vendor, "⚫")
                
                memory_str = f" ({gpu.memory_mb} MB)" if gpu.memory_mb else ""
                cuda_str = f" — CUDA {gpu.cuda_version}" if gpu.cuda_version else ""
                gpu_text += f"<li>{vendor_icon} {gpu.name}{memory_str}{cuda_str}</li>"
            gpu_text += "</ul>"
            self.gpu_list_label.setText(gpu_text)
        else:
            self.gpu_list_label.setText("<p style='color: #ffc107;'>⚠️ No dedicated GPUs detected. CPU mode will be used.</p>")
        
        # Clear existing provider buttons
        for btn in self.provider_buttons.values():
            btn.deleteLater()
        self.provider_buttons.clear()
        
        # Get available providers
        providers = get_available_providers()
        
        for provider, display_name, is_recommended in providers:
            label = display_name
            if is_recommended:
                label += " ⭐ Recommended"
            
            radio = QRadioButton(label)
            radio.setProperty("provider", provider.value)
            
            if is_recommended:
                radio.setChecked(True)
            
            self.provider_button_group.addButton(radio)
            self.providers_container.addWidget(radio)
            self.provider_buttons[provider] = radio
        
        # Update TensorRT checkbox visibility
        has_nvidia = any(g.vendor == GPUVendor.NVIDIA for g in gpus)
        self.tensorrt_checkbox.setVisible(has_nvidia)
        if has_nvidia:
            self.tensorrt_checkbox.setChecked(True)
        
        # Performance hint
        recommended = get_recommended_provider()
        hints = {
            ExecutionProvider.CUDA: "💡 NVIDIA CUDA with TensorRT offers the best performance for face processing.",
            ExecutionProvider.ROCM: "💡 AMD ROCm provides good GPU acceleration on Linux.",
            ExecutionProvider.DIRECTML: "💡 DirectML enables GPU acceleration on Windows for AMD/Intel GPUs.",
            ExecutionProvider.COREML: "💡 Apple CoreML leverages the Neural Engine for efficient processing.",
            ExecutionProvider.CPU: "⚠️ CPU mode is significantly slower. Consider installing GPU drivers."
        }
        self.perf_hint.setText(hints.get(recommended, ""))
    
    def validatePage(self) -> bool:
        """Save settings before moving to next page."""
        wizard = self.wizard()
        
        # Get selected provider
        selected_btn = self.provider_button_group.checkedButton()
        if selected_btn:
            wizard.set_setting('provider', selected_btn.property("provider"))
        
        wizard.set_setting('install_tensorrt', self.tensorrt_checkbox.isChecked())
        wizard.set_setting('install_frontend', self.frontend_checkbox.isChecked())
        wizard.set_setting('create_shortcuts', self.shortcuts_checkbox.isChecked())
        
        return True
    
    def isComplete(self) -> bool:
        """Complete when a provider is selected."""
        return self.provider_button_group.checkedButton() is not None

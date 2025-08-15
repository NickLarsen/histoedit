from PyQt6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QSlider, QSpinBox, QGroupBox, QGridLayout, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal
from histogram_widget import HistogramWidget

class ControlPanel(QWidget):
    """Right-side control panel for HistoEdit"""
    
    # Signals
    zoom_changed = pyqtSignal(float)  # Emits zoom level (1.0 = 100%)
    load_image_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the control panel UI"""
        self.setFixedWidth(400)
        
        # Create layout for control panel
        layout = QVBoxLayout(self)
        
        # Load image button
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image_requested.emit)
        layout.addWidget(self.load_button)
        
        # Zoom controls group
        zoom_group = QGroupBox("Zoom Controls")
        zoom_layout = QGridLayout(zoom_group)
        
        # Zoom slider
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(1)  # 1% = 0.01x
        self.zoom_slider.setMaximum(300)  # 300% = 3x
        self.zoom_slider.setValue(100)  # Start at 100% = 1x
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(50)  # Tick every 50%
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        
        # Zoom spin box
        self.zoom_spinbox = QSpinBox()
        self.zoom_spinbox.setMinimum(1)
        self.zoom_spinbox.setMaximum(300)
        self.zoom_spinbox.setValue(100)
        self.zoom_spinbox.setSuffix("%")
        self.zoom_spinbox.valueChanged.connect(self.on_zoom_spinbox_changed)
        
        # Connect slider and spinbox to keep them in sync
        self.zoom_slider.valueChanged.connect(self.zoom_spinbox.setValue)
        self.zoom_spinbox.valueChanged.connect(self.zoom_slider.setValue)
        
        # Add zoom controls to layout
        zoom_layout.addWidget(QLabel("Zoom:"), 0, 0)
        zoom_layout.addWidget(self.zoom_slider, 0, 1)
        zoom_layout.addWidget(self.zoom_spinbox, 0, 2)
        
        # Reset zoom button
        self.reset_zoom_button = QPushButton("Reset Zoom (100%)")
        self.reset_zoom_button.clicked.connect(self.reset_zoom)
        zoom_layout.addWidget(self.reset_zoom_button, 1, 0, 1, 3)
        
        layout.addWidget(zoom_group)
        
        # Add histogram widget
        self.histogram_widget = HistogramWidget()
        layout.addWidget(self.histogram_widget)
        
        # Add stretch to push controls to top
        layout.addStretch()
        
    def on_zoom_slider_changed(self, value):
        """Handle zoom slider changes"""
        zoom_level = value / 100.0
        self.zoom_changed.emit(zoom_level)
        
    def on_zoom_spinbox_changed(self, value):
        """Handle zoom spinbox changes"""
        zoom_level = value / 100.0
        self.zoom_changed.emit(zoom_level)
        
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.zoom_slider.setValue(100)
        self.zoom_changed.emit(1.0)
        
    def set_zoom(self, zoom_level):
        """Set the zoom level (1.0 = 100%)"""
        zoom_percent = int(zoom_level * 100)
        self.zoom_slider.setValue(zoom_percent)
        self.zoom_spinbox.setValue(zoom_percent)
        
    def set_image(self, pixmap):
        """Set the image for the histogram widget"""
        self.histogram_widget.set_image(pixmap) 
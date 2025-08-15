from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap
from PyQt6.QtCore import Qt, QRect
import numpy as np

class HistogramWidget(QWidget):
    """Widget for displaying RGB histograms with transparency"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Store histogram data
        self.red_histogram = None
        self.green_histogram = None
        self.blue_histogram = None
        
        # Set fixed height as requested
        self.setFixedHeight(350)
        
    def setup_ui(self):
        """Setup the histogram widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title label with black text on white background
        title_label = QLabel("Image Histogram")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px; color: black; background-color: white; padding: 5px; border-radius: 3px; border: 1px solid #ccc;")
        layout.addWidget(title_label)
        
        # Add stretch to push title to top
        layout.addStretch()
        
    def set_image(self, pixmap):
        """Calculate and display histogram for the given image"""
        if pixmap is None:
            self.clear_histogram()
            return
            
        # Convert QPixmap to numpy array for histogram calculation
        image = pixmap.toImage()
        width = image.width()
        height = image.height()
        
        # Get pixel data
        ptr = image.bits()
        ptr.setsize(height * width * 4)  # 4 bytes per pixel (RGBA)
        arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
        
        # Calculate histograms for each channel
        self.red_histogram = np.histogram(arr[:, :, 0], bins=256, range=(0, 256))[0]
        self.green_histogram = np.histogram(arr[:, :, 1], bins=256, range=(0, 256))[0]
        self.blue_histogram = np.histogram(arr[:, :, 2], bins=256, range=(0, 256))[0]
        
        # Update the display
        self.update()
        
    def clear_histogram(self):
        """Clear the histogram data"""
        self.red_histogram = None
        self.green_histogram = None
        self.blue_histogram = None
        self.update()
        
    def paintEvent(self, event):
        """Custom paint event to draw the histogram"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background with white for better contrast
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if (self.red_histogram is None or 
            self.green_histogram is None or 
            self.blue_histogram is None):
            return
            
        # Get widget dimensions
        width = self.width() - 20  # Account for margins
        height = self.height() - 60  # Account for title and margins
        
        # Find maximum value for normalization
        max_value = max(
            np.max(self.red_histogram),
            np.max(self.green_histogram),
            np.max(self.blue_histogram)
        )
        
        if max_value == 0:
            return
            
        # Draw histogram
        bar_width = width / 256
        
        # Draw red histogram (50% transparency fill, 90% transparency line)
        red_fill = QColor(255, 0, 0, 128)  # 50% transparency
        red_line = QColor(255, 0, 0, 26)   # 90% transparency
        
        painter.setBrush(QBrush(red_fill))
        painter.setPen(QPen(red_line, 1))
        
        for i in range(256):
            x = 10 + i * bar_width
            normalized_height = (self.red_histogram[i] / max_value) * height
            y = 50 + height - normalized_height
            painter.drawRect(QRect(int(x), int(y), int(bar_width), int(normalized_height)))
            
        # Draw green histogram
        green_fill = QColor(0, 255, 0, 128)  # 50% transparency
        green_line = QColor(0, 255, 0, 26)   # 90% transparency
        
        painter.setBrush(QBrush(green_fill))
        painter.setPen(QPen(green_line, 1))
        
        for i in range(256):
            x = 10 + i * bar_width
            normalized_height = (self.green_histogram[i] / max_value) * height
            y = 50 + height - normalized_height
            painter.drawRect(QRect(int(x), int(y), int(bar_width), int(normalized_height)))
            
        # Draw blue histogram
        blue_fill = QColor(0, 0, 255, 128)  # 50% transparency
        blue_line = QColor(0, 0, 255, 26)   # 90% transparency
        
        painter.setBrush(QBrush(blue_fill))
        painter.setPen(QPen(blue_line, 1))
        
        for i in range(256):
            x = 10 + i * bar_width
            normalized_height = (self.blue_histogram[i] / max_value) * height
            y = 50 + height - normalized_height
            painter.drawRect(QRect(int(x), int(y), int(bar_width), int(normalized_height)))
            
        # Draw axis labels with black text for better contrast
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(10, height + 70, "0")
        painter.drawText(width - 20, height + 70, "255")
        
        # Draw channel labels with black text for better contrast
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(10, 30, "R")
        painter.drawText(25, 30, "G")
        painter.drawText(40, 30, "B") 
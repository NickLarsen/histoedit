from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap
from PyQt6.QtCore import Qt, QRect
import numpy as np

class HistogramContainer(QWidget):
    """Container widget that handles histogram painting"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setMouseTracking(True)
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if not hasattr(self.parent_widget, 'highlight_enabled') or not self.parent_widget.highlight_enabled:
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.parent_widget.is_locked:
                # First click: start highlighting
                self.parent_widget.is_highlighting = True
                self.update_highlight_from_mouse(event.pos())
                self.update()
            else:
                # Click while locked: unlock
                self.parent_widget.is_locked = False
                self.parent_widget.lock_button.setChecked(False)
                self.parent_widget.lock_button.setText("🔓")
                
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if not hasattr(self.parent_widget, 'highlight_enabled') or not self.parent_widget.highlight_enabled:
            return
            
        if self.parent_widget.is_highlighting and not self.parent_widget.is_locked:
            # Update highlight while dragging
            self.update_highlight_from_mouse(event.pos())
            self.update()
        elif not self.parent_widget.is_locked:
            # Update highlight in real-time when not locked
            self.update_highlight_from_mouse(event.pos())
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if not hasattr(self.parent_widget, 'highlight_enabled') or not self.parent_widget.highlight_enabled:
            return
            
        if event.button() == Qt.MouseButton.LeftButton and self.parent_widget.is_highlighting:
            # Lock the position when mouse is released
            self.parent_widget.is_highlighting = False
            self.parent_widget.is_locked = True
            self.parent_widget.lock_button.setChecked(True)
            self.parent_widget.lock_button.setText("🔒")
            
    def update_highlight_from_mouse(self, pos):
        """Update highlight area based on mouse position"""
        # Calculate histogram area within the container
        hist_x = 10
        hist_y = 10
        hist_width = self.width() - 20
        hist_height = self.height() - 20
        
        # Calculate center position (0.0 to 1.0)
        if hist_width > 0:
            relative_x = (pos.x() - hist_x) / hist_width
            self.parent_widget.highlight_center = max(0.0, min(1.0, relative_x))
        
        # Calculate width based on vertical position (0.0 to 0.1)
        if hist_height > 0:
            relative_y = (pos.y() - hist_y) / hist_height
            # Linear progression: top (1.0) = 10% width, bottom (0.0) = 0% width
            self.parent_widget.highlight_width = (1.0 - relative_y) * 0.1
        
    def paintEvent(self, event):
        """Paint the histogram in this container"""
        super().paintEvent(event)
        
        if not hasattr(self.parent_widget, 'red_histogram') or self.parent_widget.red_histogram is None:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill the container background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # Get histogram dimensions
        hist_x = 10
        hist_y = 10
        hist_width = self.width() - 20
        hist_height = self.height() - 20
        
        # Find maximum value for normalization
        max_value = max(
            np.max(self.parent_widget.red_histogram),
            np.max(self.parent_widget.green_histogram),
            np.max(self.parent_widget.blue_histogram)
        )
        
        if max_value == 0:
            return
            
        # Draw histogram
        bar_width = hist_width / 256
        
        # Draw red histogram (50% transparency fill, 90% transparency line)
        red_fill = QColor(255, 0, 0, 128)  # 50% transparency
        red_line = QColor(255, 0, 0, 26)   # 90% transparency
        
        painter.setBrush(QBrush(red_fill))
        painter.setPen(QPen(red_line, 1))
        
        for i in range(256):
            x = hist_x + i * bar_width
            normalized_height = (self.parent_widget.red_histogram[i] / max_value) * hist_height
            y = hist_y + hist_height - normalized_height
            painter.drawRect(QRect(int(x), int(y), int(bar_width), int(normalized_height)))
            
        # Draw green histogram
        green_fill = QColor(0, 255, 0, 128)  # 50% transparency
        green_line = QColor(0, 255, 0, 26)   # 90% transparency
        
        painter.setBrush(QBrush(green_fill))
        painter.setPen(QPen(green_line, 1))
        
        for i in range(256):
            x = hist_x + i * bar_width
            normalized_height = (self.parent_widget.green_histogram[i] / max_value) * hist_height
            y = hist_y + hist_height - normalized_height
            painter.drawRect(QRect(int(x), int(y), int(bar_width), int(normalized_height)))
            
        # Draw blue histogram
        blue_fill = QColor(0, 0, 255, 128)  # 50% transparency
        blue_line = QColor(0, 0, 255, 26)   # 90% transparency
        
        painter.setBrush(QBrush(blue_fill))
        painter.setPen(QPen(blue_line, 1))
        
        for i in range(256):
            x = hist_x + i * bar_width
            normalized_height = (self.parent_widget.blue_histogram[i] / max_value) * hist_height
            y = hist_y + hist_height - normalized_height
            painter.drawRect(QRect(int(x), int(y), int(bar_width), int(normalized_height)))
            
        # Draw highlight overlay only if enabled
        if hasattr(self.parent_widget, 'highlight_enabled') and self.parent_widget.highlight_enabled:
            self.draw_highlight_overlay(painter, hist_width, hist_height, hist_x, hist_y)
            
        # Draw axis labels with black text for better contrast
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(hist_x, hist_y + hist_height + 20, "0")
        painter.drawText(hist_x + hist_width - 20, hist_y + hist_height + 20, "255")
        
    def draw_highlight_overlay(self, painter, hist_width, hist_height, hist_x, hist_y):
        """Draw the highlight overlay with vertical lines and transparency"""
        if not hasattr(self.parent_widget, 'highlight_width') or self.parent_widget.highlight_width <= 0:
            return
            
        # Calculate highlight area bounds
        center_x = hist_x + (self.parent_widget.highlight_center * hist_width)
        half_width = (self.parent_widget.highlight_width * hist_width) / 2
        
        left_line_x = int(center_x - half_width)
        right_line_x = int(center_x + half_width)
        
        # Draw left vertical line
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawLine(left_line_x, hist_y, left_line_x, hist_y + hist_height)
        
        # Draw right vertical line
        painter.drawLine(right_line_x, hist_y, right_line_x, hist_y + hist_height)
        
        # Create semi-transparent overlay to gray out non-highlighted areas
        overlay_brush = QBrush(QColor(128, 128, 128, 180))  # Gray with 70% opacity
        
        # Left gray area
        if left_line_x > hist_x:
            left_rect = QRect(hist_x, hist_y, left_line_x - hist_x, hist_height)
            painter.fillRect(left_rect, overlay_brush)
            
        # Right gray area
        if right_line_x < hist_x + hist_width:
            right_rect = QRect(right_line_x, hist_y, (hist_x + hist_width) - right_line_x, hist_height)
            painter.fillRect(right_rect, overlay_brush)

class HistogramWidget(QWidget):
    """Widget for displaying RGB histograms with transparency"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Store histogram data
        self.red_histogram = None
        self.green_histogram = None
        self.blue_histogram = None
        
        # Highlight state
        self.highlight_enabled = True
        self.is_highlighting = False
        self.is_locked = False
        self.highlight_center = 0.5  # Center position (0.0 to 1.0)
        self.highlight_width = 0.1   # Width as fraction (0.0 to 1.0)
        
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
        
        # Add control buttons above the histogram graph area
        button_layout = QHBoxLayout()
        
        # Toggle highlight button
        self.toggle_button = QPushButton("Disable Highlighting")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_highlighting)
        button_layout.addWidget(self.toggle_button)
        
        # Lock/unlock button with emoji
        self.lock_button = QPushButton("🔓")  # Unlocked emoji
        self.lock_button.setCheckable(True)
        self.lock_button.clicked.connect(self.toggle_lock)
        self.lock_button.setFixedSize(40, 30)  # Make it square-ish for the emoji
        button_layout.addWidget(self.lock_button)
        
        button_layout.addStretch()  # Push buttons to the left
        layout.addLayout(button_layout)
        
        # Add some spacing between buttons and histogram
        layout.addSpacing(10)
        
        # Create a container for the histogram area with fixed size
        self.histogram_container = HistogramContainer(self)
        self.histogram_container.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 3px;")
        self.histogram_container.setFixedHeight(250)  # Give it a proper height
        layout.addWidget(self.histogram_container)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
    def toggle_highlighting(self):
        """Toggle highlighting on/off"""
        self.highlight_enabled = not self.highlight_enabled
        if self.highlight_enabled:
            self.toggle_button.setText("Disable Highlighting")
        else:
            self.toggle_button.setText("Enable Highlighting")
        self.histogram_container.update()
        
    def toggle_lock(self):
        """Toggle lock state"""
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.lock_button.setText("🔒")  # Locked emoji
        else:
            self.lock_button.setText("🔓")  # Unlocked emoji
        
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
        self.histogram_container.update()
        
    def clear_histogram(self):
        """Clear the histogram data"""
        self.red_histogram = None
        self.green_histogram = None
        self.blue_histogram = None
        self.histogram_container.update() 
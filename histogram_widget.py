from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap
from PyQt6.QtCore import Qt, QRect, pyqtSignal
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
                self.parent_widget.update_pixel_counter()
                # Emit signal for highlight change
                self.parent_widget.highlight_changed.emit()
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
            self.parent_widget.update_pixel_counter()
            # Emit signal for highlight change
            self.parent_widget.highlight_changed.emit()
        elif not self.parent_widget.is_locked:
            # Update highlight in real-time when not locked
            self.update_highlight_from_mouse(event.pos())
            self.update()
            self.parent_widget.update_pixel_counter()
            # Emit signal for highlight change
            self.parent_widget.highlight_changed.emit()
            
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
            self.parent_widget.update_pixel_counter()
            # Emit signal for highlight change
            self.parent_widget.highlight_changed.emit()
            
    def update_highlight_from_mouse(self, pos):
        """Update highlight area based on mouse position"""
        # Calculate histogram area within the container
        hist_x = 10
        hist_y = 10
        hist_width = self.width() - 20
        hist_height = self.height() - 20
        
        # Calculate center position (0.0 to 1.0) - maps to histogram value range 0-255
        if hist_width > 0:
            relative_x = (pos.x() - hist_x) / hist_width
            self.parent_widget.highlight_center = max(0.0, min(1.0, relative_x))
        
        # Calculate width based on vertical position (0.0 to 0.1)
        if hist_height > 0:
            relative_y = (pos.y() - hist_y) / hist_height
            # Linear progression: top (1.0) = 10% width, bottom (0.0) = 0% width
            # This controls how wide the histogram value range is
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
        # Reserve space at bottom for axis labels - reduce histogram height
        hist_height = self.height() - 40  # 20px top margin + 20px bottom margin for labels
        
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
        
        # Apply logarithmic scaling to histogram values
        # Add 1 to avoid log(0) and ensure all values are positive
        log_red = np.log(self.parent_widget.red_histogram + 1)
        log_green = np.log(self.parent_widget.green_histogram + 1)
        log_blue = np.log(self.parent_widget.blue_histogram + 1)
        
        # Find maximum log value for normalization
        max_log_value = max(np.max(log_red), np.max(log_green), np.max(log_blue))
        
        # Draw red histogram (50% transparency fill, 90% transparency line)
        red_fill = QColor(255, 0, 0, 128)  # 50% transparency
        red_line = QColor(255, 0, 0, 26)   # 90% transparency
        
        painter.setBrush(QBrush(red_fill))
        painter.setPen(QPen(red_line, 1))
        
        for i in range(256):
            x = hist_x + i * bar_width
            # Use logarithmic normalization
            normalized_height = (log_red[i] / max_log_value) * hist_height
            y = hist_y + hist_height - normalized_height
            painter.drawRect(QRect(int(x), int(y), int(bar_width), int(normalized_height)))
            
        # Draw green histogram
        green_fill = QColor(0, 255, 0, 128)  # 50% transparency
        green_line = QColor(0, 255, 0, 26)   # 90% transparency
        
        painter.setBrush(QBrush(green_fill))
        painter.setPen(QPen(green_line, 1))
        
        for i in range(256):
            x = hist_x + i * bar_width
            # Use logarithmic normalization
            normalized_height = (log_green[i] / max_log_value) * hist_height
            y = hist_y + hist_height - normalized_height
            painter.drawRect(QRect(int(x), int(y), int(bar_width), int(normalized_height)))
            
        # Draw blue histogram
        blue_fill = QColor(0, 0, 255, 128)  # 50% transparency
        blue_line = QColor(0, 0, 255, 26)   # 90% transparency
        
        painter.setBrush(QBrush(blue_fill))
        painter.setPen(QPen(blue_line, 1))
        
        for i in range(256):
            x = hist_x + i * bar_width
            # Use logarithmic normalization
            normalized_height = (log_blue[i] / max_log_value) * hist_height
            y = hist_y + hist_height - normalized_height
            painter.drawRect(QRect(int(x), int(y), int(bar_width), int(normalized_height)))
            
        # Draw highlight overlay only if enabled
        if hasattr(self.parent_widget, 'highlight_enabled') and self.parent_widget.highlight_enabled:
            self.draw_highlight_overlay(painter, hist_width, hist_height, hist_x, hist_y)
            
        # Draw axis labels with black text for better contrast
        painter.setPen(QColor(0, 0, 0))
        # Position labels in the reserved bottom space
        label_y = hist_y + hist_height + 15  # 15px below histogram, 5px above bottom edge
        painter.drawText(hist_x, label_y, "0")
        painter.drawText(hist_x + hist_width - 20, label_y, "255")
        
    def draw_highlight_overlay(self, painter, hist_width, hist_height, hist_x, hist_y):
        """Draw the highlight overlay showing the selected histogram range"""
        if not hasattr(self.parent_widget, 'highlight_width') or self.parent_widget.highlight_width <= 0:
            return
            
        # Calculate highlight area bounds in histogram coordinates
        center_x = hist_x + (self.parent_widget.highlight_center * hist_width)
        half_width = (self.parent_widget.highlight_width * hist_width) / 2
        
        left_line_x = int(center_x - half_width)
        right_line_x = int(center_x + half_width)
        
        # Draw left vertical line
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawLine(left_line_x, hist_y, left_line_x, hist_y + hist_height)
        
        # Draw right vertical line
        painter.drawLine(right_line_x, hist_y, right_line_x, hist_y + hist_height)
        
        # Create semi-transparent overlay to highlight the selected range
        highlight_brush = QBrush(QColor(255, 255, 0, 80))  # Yellow with 30% opacity
        
        # Highlight the selected range
        if left_line_x < right_line_x:
            highlight_rect = QRect(left_line_x, hist_y, right_line_x - left_line_x, hist_height)
            painter.fillRect(highlight_rect, highlight_brush)
        
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
    
    # Signals
    highlight_changed = pyqtSignal()  # Emitted when highlight area changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Store histogram data
        self.red_histogram = None
        self.green_histogram = None
        self.blue_histogram = None
        
        # Store original image data for processing
        self.original_image_array = None
        
        # Highlight state
        self.highlight_enabled = True
        self.is_highlighting = False
        self.is_locked = False
        self.highlight_center = 0.5  # Center position (0.0 to 1.0)
        self.highlight_width = 0.1   # Width as fraction (0.0 to 1.0)
        
        # Set fixed height to accommodate histogram + labels
        self.setFixedHeight(420)
        
    def setup_ui(self):
        """Setup the histogram widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title label with black text on white background
        title_label = QLabel("Image Histogram (Log Scale)")
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
        self.histogram_container.setFixedHeight(270)  # Increased height to accommodate axis labels
        layout.addWidget(self.histogram_container)
        
        # Add spacing between histogram and labels
        spacer = QWidget()
        spacer.setFixedHeight(55)
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Allow mouse events to pass through
        layout.addWidget(spacer)
        
        # Add pixel counter below the histogram
        self.pixel_counter_label = QLabel("Pixels in selected range: 0")
        self.pixel_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pixel_counter_label.setStyleSheet("font-size: 12px; color: black; background-color: #f0f0f0; padding: 5px; border-radius: 3px; border: 1px solid #ccc;")
        layout.addWidget(self.pixel_counter_label)
        
        # Add spacing between the two labels
        label_spacer = QWidget()
        label_spacer.setFixedHeight(5)
        label_spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Allow mouse events to pass through
        layout.addWidget(label_spacer)
        
        # Add total pixel count and percentage
        self.total_pixel_label = QLabel("Total image pixels: 0")
        self.total_pixel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_pixel_label.setStyleSheet("font-size: 11px; color: #666; background-color: #f8f8f8; padding: 3px; border-radius: 2px; border: 1px solid #ddd;")
        layout.addWidget(self.total_pixel_label)
        
    def toggle_highlighting(self):
        """Toggle highlighting on/off"""
        self.highlight_enabled = not self.highlight_enabled
        if self.highlight_enabled:
            self.toggle_button.setText("Disable Highlighting")
        else:
            self.toggle_button.setText("Enable Highlighting")
        self.histogram_container.update()
        self.update_pixel_counter()
        # Emit signal for highlight change
        self.highlight_changed.emit()
        
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
        
        # Store original image data for processing
        # Make sure we have a completely independent copy
        self.original_image_array = arr.copy().astype(np.uint8)
        
        # Calculate histograms for each channel
        self.red_histogram = np.histogram(arr[:, :, 0], bins=256, range=(0, 256))[0]
        self.green_histogram = np.histogram(arr[:, :, 1], bins=256, range=(0, 256))[0]
        self.blue_histogram = np.histogram(arr[:, :, 2], bins=256, range=(0, 256))[0]
        
        # Update the display
        self.histogram_container.update()
        self.update_pixel_counter()
        
    def get_highlight_mask(self):
        """Get a boolean mask indicating which pixels have color channel values in the highlighted histogram range"""
        if self.original_image_array is None or not self.highlight_enabled:
            return None
            
        height, width = self.original_image_array.shape[:2]
        mask = np.zeros((height, width), dtype=bool)
        
        # Calculate the histogram value range based on highlight position and width
        # highlight_center (0.0 to 1.0) maps to histogram bin 0-255
        center_bin = int(self.highlight_center * 255)
        half_width_bins = int((self.highlight_width * 255) / 2)
        
        # Calculate the range of histogram bins to highlight
        left_bin = max(0, center_bin - half_width_bins)
        right_bin = min(255, center_bin + half_width_bins)
        
        # Create a mask for pixels that fall within this value range
        # Check if any of the RGB channels fall within the highlighted range
        for channel_idx in range(3):  # RGB channels only
            channel_data = self.original_image_array[:, :, channel_idx]
            # Pixels are highlighted if their value is within the highlighted range
            channel_mask = (channel_data >= left_bin) & (channel_data <= right_bin)
            mask = mask | channel_mask  # Combine with OR operation
        
        return mask
        
    def get_highlighted_image(self):
        """Get the image with white mask overlay"""
        if self.original_image_array is None or not self.highlight_enabled:
            return None
            
        # Get the highlight mask for pixels with values in the highlighted range
        mask = self.get_highlight_mask()
        if mask is None:
            return None
            
        # Create a deep copy of the original image for processing
        # Use numpy's copy with explicit order to ensure complete isolation
        result = np.array(self.original_image_array, copy=True, dtype=np.uint8, order='C')
        
        # Make highlighted pixels pure white
        if np.any(mask):
            # Create a copy of the mask to avoid any potential reference issues
            mask_copy = mask.copy()
            # Apply white color to highlighted pixels
            result[mask_copy, 0] = 255  # Red channel = 255
            result[mask_copy, 1] = 255  # Green channel = 255
            result[mask_copy, 2] = 255  # Blue channel = 255
        
        return result
        
    def update_pixel_counter(self):
        """Update the pixel counter display with the current number of highlighted pixels"""
        if not self.highlight_enabled or self.original_image_array is None:
            self.pixel_counter_label.setText("Pixels in selected range: 0")
            self.total_pixel_label.setText("Total image pixels: 0")
            return
            
        # Get the current highlight mask
        mask = self.get_highlight_mask()
        if mask is None:
            self.pixel_counter_label.setText("Pixels in selected range: 0")
            self.total_pixel_label.setText("Total image pixels: 0")
            return
            
        # Count the number of True pixels in the mask
        pixel_count = np.sum(mask)
        
        # Calculate total pixels in the image
        total_pixels = self.original_image_array.shape[0] * self.original_image_array.shape[1]
        
        # Calculate percentage
        percentage = (pixel_count / total_pixels) * 100 if total_pixels > 0 else 0
        
        # Update the labels
        self.pixel_counter_label.setText(f"Pixels in selected range: {pixel_count:,} ({percentage:.1f}%)")
        self.total_pixel_label.setText(f"Total image pixels: {total_pixels:,}")
        
    def clear_histogram(self):
        """Clear the histogram data"""
        self.red_histogram = None
        self.green_histogram = None
        self.blue_histogram = None
        self.original_image_array = None
        self.histogram_container.update()
        self.update_pixel_counter() 
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollBar, QComboBox
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
        
        # Get zoom and scroll information from parent
        zoom_level = getattr(self.parent_widget, 'zoom_level', 1)
        scroll_position = getattr(self.parent_widget, 'scroll_position', 0)
        
        # Calculate the visible range of histogram values
        total_visible_bins = 256 // zoom_level
        start_bin = int(scroll_position * (256 - total_visible_bins))
        
        # Calculate center position (0.0 to 1.0) - maps to visible histogram value range
        if hist_width > 0:
            relative_x = (pos.x() - hist_x) / hist_width
            # Map relative position to histogram value range, accounting for zoom and scroll
            visible_center = max(0.0, min(1.0, relative_x))
            self.parent_widget.highlight_center = (start_bin + visible_center * total_visible_bins) / 255.0
        
        # Calculate width based on vertical position (0.0 to 0.1)
        if hist_height > 0:
            relative_y = (pos.y() - hist_y) / hist_height
            # Linear progression: top (1.0) = 10% width, bottom (0.0) = 0% width
            # Scale the width by zoom level - more zoom = smaller range
            base_width = (1.0 - relative_y) * 0.1
            self.parent_widget.highlight_width = base_width / zoom_level
        
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
        
        # Get zoom and scroll information from parent
        zoom_level = getattr(self.parent_widget, 'zoom_level', 1)
        scroll_position = getattr(self.parent_widget, 'scroll_position', 0)
        
        # Calculate the visible range of histogram values
        total_visible_bins = 256 // zoom_level
        start_bin = int(scroll_position * (256 - total_visible_bins))
        end_bin = start_bin + total_visible_bins
        
        # Find maximum value for normalization in the visible range
        max_value = max(
            np.max(self.parent_widget.red_histogram[start_bin:end_bin]),
            np.max(self.parent_widget.green_histogram[start_bin:end_bin]),
            np.max(self.parent_widget.blue_histogram[start_bin:end_bin])
        )
        
        if max_value == 0:
            return
            
        # Draw histogram
        bar_width = hist_width / total_visible_bins
        
        # Apply logarithmic scaling to histogram values
        # Add 1 to avoid log(0) and ensure all values are positive
        log_red = np.log(self.parent_widget.red_histogram[start_bin:end_bin] + 1)
        log_green = np.log(self.parent_widget.green_histogram[start_bin:end_bin] + 1)
        log_blue = np.log(self.parent_widget.blue_histogram[start_bin:end_bin] + 1)
        
        # Find maximum log value for normalization
        max_log_value = max(np.max(log_red), np.max(log_green), np.max(log_blue))
        
        # Draw red histogram (50% transparency fill, 90% transparency line)
        red_fill = QColor(255, 0, 0, 128)  # 50% transparency
        red_line = QColor(255, 0, 0, 26)   # 90% transparency
        
        painter.setBrush(QBrush(red_fill))
        painter.setPen(QPen(red_line, 1))
        
        for i in range(total_visible_bins):
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
        
        for i in range(total_visible_bins):
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
        
        for i in range(total_visible_bins):
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
        painter.drawText(hist_x, label_y, str(start_bin))
        painter.drawText(hist_x + hist_width - 30, label_y, str(end_bin))
        
    def draw_highlight_overlay(self, painter, hist_width, hist_height, hist_x, hist_y):
        """Draw the highlight overlay showing the selected histogram range"""
        if not hasattr(self.parent_widget, 'highlight_width') or self.parent_widget.highlight_width <= 0:
            return
            
        # Get zoom and scroll information from parent
        zoom_level = getattr(self.parent_widget, 'zoom_level', 1)
        scroll_position = getattr(self.parent_widget, 'scroll_position', 0)
        
        # Calculate the visible range of histogram values
        total_visible_bins = 256 // zoom_level
        start_bin = int(scroll_position * (256 - total_visible_bins))
        
        # Calculate highlight area bounds in histogram coordinates
        # Map highlight center from global histogram space to visible space
        global_center_bin = self.parent_widget.highlight_center * 255
        visible_center = (global_center_bin - start_bin) / total_visible_bins
        
        if 0 <= visible_center <= 1:
            center_x = hist_x + (visible_center * hist_width)
            half_width = (self.parent_widget.highlight_width * hist_width) / 2
            
            left_line_x = int(center_x - half_width)
            right_line_x = int(center_x + half_width)
            
            # Clamp to histogram bounds
            left_line_x = max(hist_x, left_line_x)
            right_line_x = min(hist_x + hist_width, right_line_x)
            
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
    """Widget for displaying RGB histograms with transparency and zoom functionality"""
    
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
        
        # Zoom and scroll state
        self.zoom_level = 1  # 1x, 2x, or 3x zoom
        self.scroll_position = 0.0  # 0.0 to 1.0, represents position in scrollable area
        
        # Set fixed height to accommodate histogram + labels + controls
        # Title: 35 + Control Panel: 80 + Histogram: 240 + Scroll: 50 + Counter: 70 + Spacing: 50 = 525
        self.setFixedHeight(525)
        
    def setup_ui(self):
        """Setup the histogram widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)  # Increased spacing between major sections
        
        # Title label with black text on white background
        title_label = QLabel("Image Histogram (Log Scale)")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px; color: black; background-color: white; padding: 5px; border-radius: 3px; border: 1px solid #ccc;")
        title_label.setFixedHeight(35)
        layout.addWidget(title_label)
        
        # Control panel section
        control_panel = QWidget()
        control_panel.setFixedHeight(80)  # Fixed height for control panel
        control_panel.setStyleSheet("border: 1px solid #ddd; border-radius: 3px;")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(8, 8, 8, 8)
        control_layout.setSpacing(8)
        
        # Highlight controls row
        highlight_layout = QHBoxLayout()
        highlight_layout.setSpacing(8)
        
        # Toggle highlight button
        self.toggle_button = QPushButton("Disable Highlighting")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_highlighting)
        self.toggle_button.setFixedHeight(28)
        highlight_layout.addWidget(self.toggle_button)
        
        # Lock/unlock button with emoji
        self.lock_button = QPushButton("🔓")  # Unlocked emoji
        self.lock_button.setCheckable(True)
        self.lock_button.clicked.connect(self.toggle_lock)
        self.lock_button.setFixedSize(40, 28)  # Make it square-ish for the emoji
        highlight_layout.addWidget(self.lock_button)
        
        highlight_layout.addStretch()  # Push buttons to the left
        control_layout.addLayout(highlight_layout)
        
        # Zoom controls row
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(8)
        
        zoom_label = QLabel("Zoom Level:")
        zoom_label.setFixedWidth(80)
        zoom_layout.addWidget(zoom_label)
        
        # Zoom level selector
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["1x", "2x", "3x"])
        self.zoom_combo.setCurrentText("1x")
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        self.zoom_combo.setFixedHeight(28)
        zoom_layout.addWidget(self.zoom_combo)
        
        zoom_layout.addStretch()
        control_layout.addLayout(zoom_layout)
        
        layout.addWidget(control_panel)
        
        # Histogram container with proper sizing
        self.histogram_container = HistogramContainer(self)
        self.histogram_container.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 3px;")
        self.histogram_container.setFixedHeight(240)  # Fixed height for histogram
        layout.addWidget(self.histogram_container)
        
        # Scroll bar section with proper spacing
        scroll_section = QWidget()
        scroll_section.setFixedHeight(50)  # Fixed height for scroll section
        scroll_section.setStyleSheet("border: 1px solid #ddd; border-radius: 3px;")
        scroll_layout = QVBoxLayout(scroll_section)
        scroll_layout.setContentsMargins(8, 5, 8, 5)
        scroll_layout.setSpacing(3)
        
        # Scroll bar label
        scroll_label = QLabel("Navigate Histogram:")
        scroll_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_label.setStyleSheet("font-size: 10px; color: #666;")
        scroll_label.setFixedHeight(15)
        scroll_layout.addWidget(scroll_label)
        
        # Horizontal scroll bar
        self.scroll_bar = QScrollBar(Qt.Orientation.Horizontal)
        self.scroll_bar.setMinimum(0)
        self.scroll_bar.setMaximum(100)
        self.scroll_bar.setValue(0)
        self.scroll_bar.setPageStep(10)
        self.scroll_bar.setFixedHeight(20)
        self.scroll_bar.valueChanged.connect(self.on_scroll_changed)
        scroll_layout.addWidget(self.scroll_bar)
        
        layout.addWidget(scroll_section)
        
        # Pixel counter section
        counter_section = QWidget()
        counter_section.setFixedHeight(70)  # Fixed height for counter section
        counter_section.setStyleSheet("border: 1px solid #ddd; border-radius: 3px;")
        counter_layout = QVBoxLayout(counter_section)
        counter_layout.setContentsMargins(8, 8, 8, 8)
        counter_layout.setSpacing(5)
        
        # Add pixel counter below the histogram
        self.pixel_counter_label = QLabel("Pixels in selected range: 0")
        self.pixel_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pixel_counter_label.setStyleSheet("font-size: 12px; color: black; background-color: #f0f0f0; padding: 5px; border-radius: 3px; border: 1px solid #ccc;")
        self.pixel_counter_label.setFixedHeight(25)
        counter_layout.addWidget(self.pixel_counter_label)
        
        # Add total pixel count and percentage
        self.total_pixel_label = QLabel("Total image pixels: 0")
        self.total_pixel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_pixel_label.setStyleSheet("font-size: 11px; color: #666; background-color: #f8f8f8; padding: 3px; border-radius: 2px; border: 1px solid #ddd;")
        self.total_pixel_label.setFixedHeight(20)
        counter_layout.addWidget(self.total_pixel_label)
        
        layout.addWidget(counter_section)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
    def on_zoom_changed(self, zoom_text):
        """Handle zoom level changes"""
        zoom_map = {"1x": 1, "2x": 2, "3x": 3}
        self.zoom_level = zoom_map.get(zoom_text, 1)
        
        # Reset scroll position when zoom changes
        self.scroll_position = 0.0
        self.scroll_bar.setValue(0)
        
        # Update scroll bar range based on zoom level
        max_scroll = max(0, 100 - (100 // self.zoom_level))
        self.scroll_bar.setMaximum(max_scroll)
        
        # Update the display
        self.histogram_container.update()
        self.update_pixel_counter()
        
    def on_scroll_changed(self, value):
        """Handle scroll bar changes"""
        self.scroll_position = value / 100.0
        self.histogram_container.update()
        self.update_pixel_counter()
        
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
        # Note: QImage.bits() returns BGRA format, not RGBA
        self.blue_histogram = np.histogram(arr[:, :, 0], bins=256, range=(0, 256))[0]  # Channel 0 = Blue
        self.green_histogram = np.histogram(arr[:, :, 1], bins=256, range=(0, 256))[0]  # Channel 1 = Green
        self.red_histogram = np.histogram(arr[:, :, 2], bins=256, range=(0, 256))[0]   # Channel 2 = Red
        
        # Reset zoom and scroll when new image is loaded
        self.zoom_level = 1
        self.zoom_combo.setCurrentText("1x")
        self.scroll_position = 0.0
        self.scroll_bar.setValue(0)
        self.scroll_bar.setMaximum(0)  # No scrolling needed at 1x zoom
        
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
        # Note: QImage.bits() returns BGRA format, so channels are [Blue, Green, Red, Alpha]
        blue_channel = self.original_image_array[:, :, 0]   # Blue
        green_channel = self.original_image_array[:, :, 1]  # Green  
        red_channel = self.original_image_array[:, :, 2]    # Red
        
        # Pixels are highlighted if their value is within the highlighted range
        blue_mask = (blue_channel >= left_bin) & (blue_channel <= right_bin)
        green_mask = (green_channel >= left_bin) & (green_channel <= right_bin)
        red_mask = (red_channel >= left_bin) & (red_channel <= right_bin)
        
        mask = blue_mask | green_mask | red_mask  # Combine with OR operation
        
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
            # Note: QImage.bits() returns BGRA format, so channels are [Blue, Green, Red, Alpha]
            result[mask_copy, 0] = 255  # Blue channel = 255
            result[mask_copy, 1] = 255  # Green channel = 255
            result[mask_copy, 2] = 255  # Red channel = 255
        
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
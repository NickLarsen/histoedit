from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollBar, QComboBox, QSlider
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QThread, QTimer, QMutex, QWaitCondition
import numpy as np
import time

class ImageProcessorThread(QThread):
    """Background thread for processing image operations"""
    
    # Signal to emit processed results
    processing_complete = pyqtSignal(object, object, object)  # mask, highlighted_array, pixel_count
    
    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.running = True
        self.pending_work = False
        self.current_params = None
        
    def run(self):
        """Main thread loop"""
        while self.running:
            try:
                self.mutex.lock()
                if not self.pending_work:
                    self.wait_condition.wait(self.mutex)
                if not self.running:
                    self.mutex.unlock()
                    break
                    
                # Get current parameters
                params = self.current_params
                self.pending_work = False
                self.mutex.unlock()
                
                if params:
                    # Process the image
                    mask, highlighted_array, pixel_count = self.process_image(params)
                    # Emit results only if still running
                    if self.running:
                        self.processing_complete.emit(mask, highlighted_array, pixel_count)
            except Exception as e:
                # Handle any errors gracefully
                print(f"Warning: Error in image processing thread: {e}")
                if self.mutex.isLocked():
                    self.mutex.unlock()
                if not self.running:
                    break
                
    def process_image(self, params):
        """Process image with given parameters"""
        image_array = params['image_array']
        highlight_center = params['highlight_center']
        highlight_width = params['highlight_width']
        red_enabled = params['red_enabled']
        green_enabled = params['green_enabled']
        blue_enabled = params['blue_enabled']
        brightness_level = params['brightness_level']
        
        height, width = image_array.shape[:2]
        
        # Early exit if no channels are enabled
        if not (red_enabled or green_enabled or blue_enabled):
            empty_mask = np.zeros((height, width), dtype=bool)
            result = np.array(image_array, copy=True, dtype=np.uint8, order='C')
            return empty_mask, result, 0
        
        # Calculate the histogram value range
        center_bin = int(highlight_center * 255)
        half_width_bins = int((highlight_width * 255) / 2)
        
        left_bin = max(0, center_bin - half_width_bins)
        right_bin = min(255, center_bin + half_width_bins)
        
        # Use numpy's efficient boolean operations
        mask = np.zeros((height, width), dtype=bool)
        
        if blue_enabled:
            mask |= ((image_array[:, :, 0] >= left_bin) & (image_array[:, :, 0] <= right_bin))
        if green_enabled:
            mask |= ((image_array[:, :, 1] >= left_bin) & (image_array[:, :, 1] <= right_bin))
        if red_enabled:
            mask |= ((image_array[:, :, 2] >= left_bin) & (image_array[:, :, 2] <= right_bin))
        
        # Create highlighted image efficiently
        if np.any(mask):
            # Only create a copy if we need to modify it
            result = np.array(image_array, copy=True, dtype=np.uint8, order='C')
            
            # Apply brightness adjustment instead of white masking
            # brightness_level is 0.0 to 1.0, representing 0% to 100% of max brightness
            # Calculate how much to brighten each pixel
            # For each pixel, we want to brighten it by moving it towards 255
            # The amount of brightening is controlled by brightness_level
            
            # Get the masked pixels
            masked_pixels = result[mask, :3]  # RGB channels only
            
            # Calculate the distance from current value to maximum (255)
            distance_to_max = 255 - masked_pixels
            
            # Apply brightness adjustment: move towards max by brightness_level percentage
            brightness_adjustment = distance_to_max * brightness_level
            
            # Add the adjustment to current values, ensuring we don't exceed 255
            new_values = np.clip(masked_pixels + brightness_adjustment, 0, 255)
            
            # Update the result
            result[mask, :3] = new_values.astype(np.uint8)
        else:
            # No highlighting needed, return original
            result = image_array
        
        pixel_count = np.sum(mask)
        
        return mask, result, pixel_count
        
    def request_processing(self, params):
        """Request image processing with new parameters"""
        self.mutex.lock()
        # Cancel any pending work and start fresh
        self.pending_work = False
        self.current_params = params
        self.pending_work = True
        self.wait_condition.wakeAll()
        self.mutex.unlock()
        

        
    def stop(self):
        """Stop the thread"""
        try:
            self.mutex.lock()
            self.running = False
            self.wait_condition.wakeAll()
            self.mutex.unlock()
            
            # Wait for thread to finish, but with timeout
            if self.isRunning():
                self.wait(1000)  # Wait up to 1 second
                
                # Force quit if still running
                if self.isRunning():
                    self.terminate()
                    self.wait(500)  # Give it a bit more time
        except RuntimeError:
            # Handle case where Qt objects are already destroyed
            pass

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
                self.parent_widget.request_highlight_update()
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
            self.parent_widget.request_highlight_update()
        elif not self.parent_widget.is_locked:
            # Update highlight in real-time when not locked
            self.update_highlight_from_mouse(event.pos())
            self.update()
            self.parent_widget.request_highlight_update()
            
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
            self.parent_widget.request_highlight_update()
            
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
        max_value = 0
        if self.parent_widget.red_channel_enabled:
            max_value = max(max_value, np.max(self.parent_widget.red_histogram[start_bin:end_bin]))
        if self.parent_widget.green_channel_enabled:
            max_value = max(max_value, np.max(self.parent_widget.green_histogram[start_bin:end_bin]))
        if self.parent_widget.blue_channel_enabled:
            max_value = max(max_value, np.max(self.parent_widget.blue_histogram[start_bin:end_bin]))
        
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
        max_log_value = 0
        if self.parent_widget.red_channel_enabled:
            max_log_value = max(max_log_value, np.max(log_red))
        if self.parent_widget.green_channel_enabled:
            max_log_value = max(max_log_value, np.max(log_green))
        if self.parent_widget.blue_channel_enabled:
            max_log_value = max(max_log_value, np.max(log_blue))
        
        # Draw red histogram (50% transparency fill, 90% transparency line)
        red_fill = QColor(255, 0, 0, 128)  # 50% transparency
        red_line = QColor(255, 0, 0, 26)   # 90% transparency
        
        if self.parent_widget.red_channel_enabled:
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
        
        if self.parent_widget.green_channel_enabled:
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
        
        if self.parent_widget.blue_channel_enabled:
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
        
        # Channel toggle state
        self.red_channel_enabled = True
        self.green_channel_enabled = True
        self.blue_channel_enabled = True
        
        # Zoom and scroll state
        self.zoom_level = 1  # 1x, 2x, or 3x zoom
        self.scroll_position = 0.0  # 0.0 to 1.0, represents position in scrollable area
        
        # Brightness slider state
        self.brightness_level = 0.8  # 0.0 to 1.0, default to 80%
        
        # Set fixed height to accommodate histogram + labels + controls
        # Title: 35 + Control Panel: 110 + Histogram: 240 + Scroll: 50 + Counter: 70 + Spacing: 50 = 555
        self.setFixedHeight(555)
        
        # Initialize background thread
        self.image_processor = ImageProcessorThread()
        self.image_processor.processing_complete.connect(self.on_image_processing_complete)
        self.image_processor.start()
        
        # Add debouncing timer and caching
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.process_highlight_update)
        
        # Cache for processed results
        self.highlight_mask = None
        self.highlighted_image = None
        self.current_pixel_count = 0
        
        # Cache key for avoiding redundant processing
        self.last_cache_key = None
        
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
        control_panel.setFixedHeight(110)  # Increased height for brightness slider
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
        
        # Channel toggle buttons
        self.red_toggle = QPushButton("🔴")
        self.red_toggle.setCheckable(True)
        self.red_toggle.setChecked(True)
        self.red_toggle.clicked.connect(self.toggle_red_channel)
        self.red_toggle.setFixedSize(40, 28)
        self.red_toggle.setToolTip("Toggle Red Channel")
        highlight_layout.addWidget(self.red_toggle)
        
        self.green_toggle = QPushButton("🟢")
        self.green_toggle.setCheckable(True)
        self.green_toggle.setChecked(True)
        self.green_toggle.clicked.connect(self.toggle_green_channel)
        self.green_toggle.setFixedSize(40, 28)
        self.green_toggle.setToolTip("Toggle Green Channel")
        highlight_layout.addWidget(self.green_toggle)
        
        self.blue_toggle = QPushButton("🔵")
        self.blue_toggle.setCheckable(True)
        self.blue_toggle.setChecked(True)
        self.blue_toggle.clicked.connect(self.toggle_blue_channel)
        self.blue_toggle.setFixedSize(40, 28)
        self.blue_toggle.setToolTip("Toggle Blue Channel")
        highlight_layout.addWidget(self.blue_toggle)
        
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
        
        # Brightness slider row
        brightness_layout = QHBoxLayout()
        brightness_layout.setSpacing(8)
        
        brightness_label = QLabel("Brightness:")
        brightness_label.setFixedWidth(80)
        brightness_layout.addWidget(brightness_label)
        
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(80)  # Default to 80%
        self.brightness_slider.setPageStep(10)
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        self.brightness_slider.setFixedHeight(28)
        brightness_layout.addWidget(self.brightness_slider)
        
        # Add brightness percentage label
        self.brightness_value_label = QLabel("80%")
        self.brightness_value_label.setFixedWidth(40)
        self.brightness_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_value_label.setStyleSheet("font-size: 11px; color: #666; background-color: #f8f8f8; padding: 3px; border-radius: 2px; border: 1px solid #ddd;")
        brightness_layout.addWidget(self.brightness_value_label)
        
        control_layout.addLayout(brightness_layout)
        
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
        
        # Force immediate update when zoom changes
        self.force_highlight_update()
        
    def on_scroll_changed(self, value):
        """Handle scroll bar changes"""
        self.scroll_position = value / 100.0
        self.histogram_container.update()
        self.update_pixel_counter()
        
        # Force immediate update when scroll changes
        self.force_highlight_update()
        
    def toggle_highlighting(self):
        """Toggle highlighting on/off"""
        self.highlight_enabled = not self.highlight_enabled
        if self.highlight_enabled:
            self.toggle_button.setText("Disable Highlighting")
            # Force immediate update when enabling highlighting
            self.force_highlight_update()
        else:
            self.toggle_button.setText("Enable Highlighting")
            # Clear cache when disabling highlighting
            self.highlight_mask = None
            self.highlighted_image = None
            self.current_pixel_count = 0
            self.last_cache_key = None
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
        
    def toggle_red_channel(self):
        """Toggle the red channel on/off"""
        self.red_channel_enabled = not self.red_channel_enabled
        self.red_toggle.setChecked(self.red_channel_enabled)
        self.histogram_container.update()
        # Force immediate update when toggling channels
        self.force_highlight_update()
        
    def toggle_green_channel(self):
        """Toggle the green channel on/off"""
        self.green_channel_enabled = not self.green_channel_enabled
        self.green_toggle.setChecked(self.green_channel_enabled)
        self.histogram_container.update()
        # Force immediate update when toggling channels
        self.force_highlight_update()
        
    def toggle_blue_channel(self):
        """Toggle the blue channel on/off"""
        self.blue_channel_enabled = not self.blue_channel_enabled
        self.blue_toggle.setChecked(self.blue_channel_enabled)
        self.histogram_container.update()
        # Force immediate update when toggling channels
        self.force_highlight_update()
        
    def on_brightness_changed(self, value):
        """Handle brightness slider changes"""
        self.brightness_level = value / 100.0
        self.brightness_value_label.setText(f"{value}%")
        self.histogram_container.update()
        self.update_pixel_counter()
        self.force_highlight_update()
        
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
        
        # Reset channel toggles to enabled state
        self.red_channel_enabled = True
        self.green_channel_enabled = True
        self.blue_channel_enabled = True
        self.red_toggle.setChecked(True)
        self.green_toggle.setChecked(True)
        self.blue_toggle.setChecked(True)
        
        # Reset brightness to default 80%
        self.brightness_level = 0.8
        self.brightness_slider.setValue(80)
        self.brightness_value_label.setText("80%")
        
        # Clear cache for new image
        self.highlight_mask = None
        self.highlighted_image = None
        self.current_pixel_count = 0
        self.last_cache_key = None
        
        # Update the display
        self.histogram_container.update()
        self.update_pixel_counter()
        
    def get_highlight_mask(self):
        """Get a boolean mask indicating which pixels have color channel values in the highlighted histogram range"""
        if self.original_image_array is None or not self.highlight_enabled:
            return None
            
        # Return cached mask if available
        if self.highlight_mask is not None:
            return self.highlight_mask.copy()
            
        # Fallback to real-time calculation if no cache
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
        
        # Only include masks for enabled channels
        if self.blue_channel_enabled:
            mask |= blue_mask
        if self.green_channel_enabled:
            mask |= green_mask
        if self.red_channel_enabled:
            mask |= red_mask
        
        return mask
        
    def get_highlighted_image(self):
        """Get the image with brightness adjustment overlay"""
        if self.original_image_array is None or not self.highlight_enabled:
            return None
            
        # Return cached highlighted image if available
        if self.highlighted_image is not None:
            return self.highlighted_image.copy()
            
        # Fallback to real-time calculation if no cache
        # Get the highlight mask for pixels with values in the highlighted range
        mask = self.get_highlight_mask()
        if mask is None:
            return None
            
        # Create a deep copy of the original image for processing
        # Use numpy's copy with explicit order to ensure complete isolation
        result = np.array(self.original_image_array, copy=True, dtype=np.uint8, order='C')
        
        # Apply brightness adjustment instead of white masking
        if np.any(mask):
            # Create a copy of the mask to avoid any potential reference issues
            mask_copy = mask.copy()
            
            # Get the masked pixels
            masked_pixels = result[mask_copy, :3]  # RGB channels only
            
            # Calculate the distance from current value to maximum (255)
            distance_to_max = 255 - masked_pixels
            
            # Apply brightness adjustment: move towards max by brightness_level percentage
            brightness_adjustment = distance_to_max * self.brightness_level
            
            # Add the adjustment to current values, ensuring we don't exceed 255
            new_values = np.clip(masked_pixels + brightness_adjustment, 0, 255)
            
            # Update the result
            result[mask_copy, :3] = new_values.astype(np.uint8)
        
        return result
        
    def update_pixel_counter(self):
        """Update the pixel counter display with the current number of highlighted pixels"""
        if not self.highlight_enabled or self.original_image_array is None:
            self.pixel_counter_label.setText("Pixels in selected range: 0")
            self.total_pixel_label.setText("Total image pixels: 0")
            return
            
        # Use cached pixel count if available
        if self.highlight_mask is not None:
            pixel_count = self.current_pixel_count
        else:
            # Fallback to real-time calculation
            mask = self.get_highlight_mask()
            if mask is None:
                self.pixel_counter_label.setText("Pixels in selected range: 0")
                self.total_pixel_label.setText("Total image pixels: 0")
                return
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
        
        # Reset brightness to default 80%
        self.brightness_level = 0.8
        self.brightness_slider.setValue(80)
        self.brightness_value_label.setText("80%")
        
        self.histogram_container.update()
        self.update_pixel_counter()
        
    def closeEvent(self, event):
        """Clean up resources when widget is closed"""
        if hasattr(self, 'image_processor') and self.image_processor.isRunning():
            self.image_processor.stop()
        super().closeEvent(event)
        
    def hideEvent(self, event):
        """Clean up when widget is hidden"""
        if hasattr(self, 'image_processor') and self.image_processor.isRunning():
            self.image_processor.stop()
        super().hideEvent(event) 

    def on_image_processing_complete(self, mask, highlighted_array, pixel_count):
        """Handle results from the background image processor"""
        self.highlight_mask = mask
        self.highlighted_image = highlighted_array
        self.current_pixel_count = pixel_count
        self.update_pixel_counter()
        self.histogram_container.update()
        self.update()
        

        
        # Emit signal to update the image viewer
        self.highlight_changed.emit()
        
    def process_highlight_update(self):
        """Process highlight update after debouncing"""
        if not self.highlight_enabled or self.original_image_array is None:
            return
            
        # Create cache key to avoid redundant processing
        cache_key = (
            self.highlight_center,
            self.highlight_width,
            self.red_channel_enabled,
            self.green_channel_enabled,
            self.blue_channel_enabled,
            self.brightness_level
        )
        
        # Check if we can use cached results
        if cache_key == self.last_cache_key and self.highlighted_image is not None:
            # Use cached results
            self.update_pixel_counter()
            self.histogram_container.update()
            self.highlight_changed.emit()
            return
            
        # Request processing from background thread
        params = {
            'image_array': self.original_image_array,
            'highlight_center': self.highlight_center,
            'highlight_width': self.highlight_width,
            'red_enabled': self.red_channel_enabled,
            'green_enabled': self.green_channel_enabled,
            'blue_enabled': self.blue_channel_enabled,
            'brightness_level': self.brightness_level
        }
        
        self.image_processor.request_processing(params)
        self.last_cache_key = cache_key
        

        
    def request_highlight_update(self):
        """Request a highlight update with debouncing"""
        # Only start timer if not already running and thread is available
        if not self.debounce_timer.isActive() and self.image_processor.isRunning():
            self.debounce_timer.start(50)  # 50ms debounce delay
            
    def force_highlight_update(self):
        """Force an immediate highlight update, bypassing debouncing"""
        # Stop any pending debounced updates
        self.debounce_timer.stop()
        
        # Clear cache to force fresh processing
        self.highlight_mask = None
        self.highlighted_image = None
        self.current_pixel_count = 0
        self.last_cache_key = None
        
        # Process immediately
        self.process_highlight_update()
        
        # For immediate feedback, also emit signal now (will be updated again when background completes)
        self.highlight_changed.emit() 
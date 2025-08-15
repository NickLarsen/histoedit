from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget, QScrollArea
from PyQt6.QtGui import QPixmap, QPainter, QImage, QColor, QBrush
from PyQt6.QtCore import Qt, pyqtSignal, QRect
import numpy as np

class ImageViewer(QWidget):
    """Widget for displaying images with scroll area and zoom support"""
    
    # Signals
    image_modified = pyqtSignal(object)  # Emits the current pixmap when image is modified
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # Store current image data
        self.original_pixmap = None
        self.highlighted_image_array = None
        self.current_zoom = 1.0
        
        # Store highlight parameters
        self.highlight_center = 0.5
        self.highlight_width = 0.1
        self.highlight_enabled = False
        
    def setup_ui(self):
        """Setup the image viewer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for image
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create container widget for image
        self.image_container = QWidget()
        self.image_container.setMinimumSize(400, 300)
        
        # Create layout for image container
        container_layout = QVBoxLayout(self.image_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Image display label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("border: 2px dashed #ccc;")
        self.image_label.setText("No image loaded\nClick 'Load Image' to select a file")
        container_layout.addWidget(self.image_label)
        
        # Set the container as the scroll area widget
        self.scroll_area.setWidget(self.image_container)
        
        # Add scroll area to layout
        layout.addWidget(self.scroll_area)
        
    def set_image(self, pixmap):
        """Set the image to display"""
        self.original_pixmap = pixmap
        self.highlighted_image_array = None
        self.highlight_enabled = False
        
        # Store the original image array for processing
        if pixmap is not None:
            image = pixmap.toImage()
            width = image.width()
            height = image.height()
            
            # Get pixel data
            ptr = image.bits()
            ptr.setsize(height * width * 4)  # 4 bytes per pixel (RGBA)
            self.original_image_array = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
        else:
            self.original_image_array = None
        
        self.reset_zoom()
        # Emit signal that image has been modified
        self.image_modified.emit(pixmap)
        self.update_zoomed_image()
        
    def set_highlighted_image(self, highlighted_array, center=None, width=None, enabled=None):
        """Set the highlighted image array for overlay"""
        self.highlighted_image_array = highlighted_array
        
        # Update highlight parameters if provided
        if center is not None:
            self.highlight_center = center
        if width is not None:
            self.highlight_width = width
        if enabled is not None:
            self.highlight_enabled = enabled
            
        self.update_zoomed_image()
        
    def clear_highlight(self):
        """Clear the highlighted image overlay"""
        self.highlighted_image_array = None
        self.highlight_enabled = False
        self.update_zoomed_image()
        
    def set_zoom(self, zoom_level):
        """Set the zoom level (1.0 = 100%)"""
        self.current_zoom = zoom_level
        self.update_zoomed_image()
        
    def get_zoom(self):
        """Get current zoom level"""
        return self.current_zoom
        
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.current_zoom = 1.0
        self.update_zoomed_image()
        
    def calculate_fit_to_window_zoom(self):
        """Calculate zoom level to fit image within the viewing window"""
        if self.original_pixmap is None:
            return
            
        # Get the available viewing area size (scroll area viewport)
        viewport_size = self.scroll_area.viewport().size()
        
        # Get the original image size
        image_size = self.original_pixmap.size()
        
        # Calculate zoom factors for both width and height
        width_zoom = viewport_size.width() / image_size.width()
        height_zoom = viewport_size.height() / image_size.height()
        
        # Use the smaller zoom factor to ensure image fits completely
        fit_zoom = min(width_zoom, height_zoom)
        
        # Ensure zoom is within our allowed range (1% to 300%)
        fit_zoom = max(0.01, min(3.0, fit_zoom))
        
        # Set the zoom and update display
        self.current_zoom = fit_zoom
        self.update_zoomed_image()
        
        return fit_zoom
        
    def update_zoomed_image(self):
        """Update the displayed image with current zoom level"""
        if self.original_pixmap is None:
            return
            
        # Calculate new size based on zoom
        original_size = self.original_pixmap.size()
        new_width = int(original_size.width() * self.current_zoom)
        new_height = int(original_size.height() * self.current_zoom)
        
        # Ensure minimum size constraint (100px in smallest dimension)
        if new_width < 100 and new_height < 100:
            # Find which dimension is smaller and scale both proportionally
            if new_width < new_height:
                scale_factor = 100.0 / new_width
                new_width = 100
                new_height = int(new_height * scale_factor)
            else:
                scale_factor = 100.0 / new_height
                new_height = 100
                new_width = int(new_width * scale_factor)
            self.current_zoom = new_width / original_size.width()
        
        # Create the composite image with highlight overlay
        composite_pixmap = self.create_composite_image(new_width, new_height)
        
        # Update the image label
        self.image_label.setPixmap(composite_pixmap)
        
        # Update container size to accommodate zoomed image
        self.image_container.setMinimumSize(new_width, new_height)
        
    def create_composite_image(self, target_width, target_height):
        """Create a composite image with highlight overlay"""
        if self.original_pixmap is None:
            return QPixmap()
            
        # Scale the original pixmap
        scaled_original = self.original_pixmap.scaled(
            target_width, target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # If no highlight, just return the scaled original
        if not self.highlight_enabled or self.highlighted_image_array is None:
            return scaled_original
            
        # Create a QPixmap to draw on
        composite = QPixmap(target_width, target_height)
        composite.fill(Qt.GlobalColor.transparent)
        
        # Create a painter for the composite
        painter = QPainter(composite)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the scaled original image
        painter.drawPixmap(0, 0, scaled_original)
        
        # Draw the highlighted overlay
        self.draw_highlight_overlay(painter, target_width, target_height)
            
        painter.end()
        
        return composite
        
    def draw_highlight_overlay(self, painter, target_width, target_height):
        """Draw the highlight overlay on top of the image"""
        if not self.highlight_enabled or self.highlighted_image_array is None:
            return
            
        # Get original image dimensions
        orig_height, orig_width = self.highlighted_image_array.shape[:2]
        
        # Create a difference image that shows only the brightened pixels
        if hasattr(self, 'original_image_array') and self.original_image_array is not None:
            # Calculate the difference between original and highlighted
            # This will show only the pixels that were changed
            # Use only RGB channels from both arrays (exclude alpha)
            original_rgb = self.original_image_array[:, :, :3]
            highlighted_rgb = self.highlighted_image_array[:, :, :3]
            diff_array = highlighted_rgb.astype(np.int16) - original_rgb.astype(np.int16)
            
            # Only keep positive differences (brightened pixels)
            diff_array = np.maximum(diff_array, 0)
            
            # Normalize to 0-255 range
            if np.max(diff_array) > 0:
                diff_array = (diff_array * 255 / np.max(diff_array)).astype(np.uint8)
            
            # Convert the difference array to QImage
            height, width = diff_array.shape[:2]
            bytes_per_line = 3 * width
            
            q_image = QImage(
                diff_array.data, 
                width, 
                height, 
                bytes_per_line, 
                QImage.Format.Format_RGB888
            )
            
            # Scale the QImage to match target dimensions
            scaled_q_image = q_image.scaled(
                target_width, 
                target_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Convert to QPixmap
            diff_pixmap = QPixmap.fromImage(scaled_q_image)
            
            # Create a mask that shows only the brightened pixels
            # We'll use the difference image itself as a mask
            mask_pixmap = QPixmap(target_width, target_height)
            mask_pixmap.fill(Qt.GlobalColor.transparent)
            
            mask_painter = QPainter(mask_pixmap)
            mask_painter.setBrush(QBrush(Qt.GlobalColor.white))
            mask_painter.setPen(Qt.PenStyle.NoPen)
            
            # For now, we'll show the entire difference image
            # In a more sophisticated version, you could create a proper mask
            mask_painter.fillRect(0, 0, target_width, target_height, Qt.GlobalColor.white)
            mask_painter.end()
            
            # Set the mask
            diff_pixmap.setMask(mask_pixmap.createMaskFromColor(Qt.GlobalColor.transparent))
            
            # Draw the difference pixmap with transparency
            painter.setOpacity(0.7)  # 70% opacity
            painter.drawPixmap(0, 0, diff_pixmap)
            painter.setOpacity(1.0)  # Reset opacity
        
    def clear_image(self):
        """Clear the displayed image"""
        self.original_pixmap = None
        self.image_label.clear()
        self.image_label.setText("No image loaded\nClick 'Load Image' to select a file")
        self.image_container.setMinimumSize(400, 300)
        # Emit signal that image has been cleared
        self.image_modified.emit(None) 
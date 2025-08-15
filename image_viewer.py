from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget, QScrollArea
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class ImageViewer(QWidget):
    """Widget for displaying images with scroll area and zoom support"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # Store current image data
        self.original_pixmap = None
        self.current_zoom = 1.0
        
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
        self.reset_zoom()
        
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
        
        # Scale the pixmap
        scaled_pixmap = self.original_pixmap.scaled(
            new_width, new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Update the image label
        self.image_label.setPixmap(scaled_pixmap)
        
        # Update container size to accommodate zoomed image
        self.image_container.setMinimumSize(new_width, new_height)
        
    def clear_image(self):
        """Clear the displayed image"""
        self.original_pixmap = None
        self.image_label.clear()
        self.image_label.setText("No image loaded\nClick 'Load Image' to select a file")
        self.image_container.setMinimumSize(400, 300) 
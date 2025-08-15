import os
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
import numpy as np

class ImageLoader:
    """Handles loading and processing of various image formats"""
    
    @staticmethod
    def load_image(file_path):
        """Load an image file and return a QPixmap"""
        try:
            # Load image using PIL
            pil_image = Image.open(file_path)
            
            # Convert PIL image to QPixmap
            if pil_image.mode == "RGBA":
                # Convert RGBA to RGB if needed
                pil_image = pil_image.convert("RGB")
            
            # Convert PIL image to numpy array
            image_array = np.array(pil_image)
            
            # Convert numpy array to QImage
            height, width, channel = image_array.shape
            bytes_per_line = 3 * width
            q_image = QImage(image_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Convert QImage to QPixmap
            pixmap = QPixmap.fromImage(q_image)
            
            return pixmap, None
            
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def get_file_dialog_filter():
        """Get the file dialog filter string for supported formats"""
        return "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.fits);;All Files (*)"
    
    @staticmethod
    def open_file_dialog(parent):
        """Open file dialog for image selection"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Select Image",
            "",
            ImageLoader.get_file_dialog_filter()
        )
        return file_path 
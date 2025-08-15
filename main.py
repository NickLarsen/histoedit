import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

# Import our custom components
from image_viewer import ImageViewer
from control_panel import ControlPanel
from menu_bar import MenuBar
from image_loader import ImageLoader

class HistoEditMainWindow(QMainWindow):
    """Main window for HistoEdit application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HistoEdit - Image Viewer")
        self.setGeometry(100, 100, 1200, 700)
        
        # Setup UI components
        self.setup_ui()
        self.setup_connections()
        self.setup_application_icon()
        
        # Store current image data
        self.current_image_path = None
        
    def setup_ui(self):
        """Setup the main window UI"""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create image viewer (left side)
        self.image_viewer = ImageViewer()
        main_layout.addWidget(self.image_viewer, stretch=3)
        
        # Create control panel (right side)
        self.control_panel = ControlPanel()
        main_layout.addWidget(self.control_panel, stretch=1)
        
        # Create menu bar
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)
        
    def setup_connections(self):
        """Setup signal connections between components"""
        # Control panel signals
        self.control_panel.zoom_changed.connect(self.image_viewer.set_zoom)
        self.control_panel.load_image_requested.connect(self.load_image)
        
        # Menu bar signals
        self.menu_bar.set_signals(self.load_image, self.close)
        
    def setup_application_icon(self):
        """Setup the application icon"""
        try:
            # Try to load the icon file
            icon_path = "histoedit_icon.png"
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Could not load icon: {e}")
    
    def load_image(self):
        """Load and display an image file"""
        file_path = ImageLoader.open_file_dialog(self)
        
        if file_path:
            # Load the image
            pixmap, error = ImageLoader.load_image(file_path)
            
            if pixmap:
                # Set the image in the viewer
                self.image_viewer.set_image(pixmap)
                
                # Calculate fit-to-window zoom
                self.image_viewer.calculate_fit_to_window_zoom()
                
                # Update control panel zoom display
                current_zoom = self.image_viewer.get_zoom()
                self.control_panel.set_zoom(current_zoom)
                
                # Store current image path
                self.current_image_path = file_path
                
                # Update window title with filename
                filename = os.path.basename(file_path)
                self.setWindowTitle(f"HistoEdit - {filename}")
                
            else:
                # Handle error
                print(f"Error loading image: {error}")
                # You could add a status bar or dialog to show this error

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HistoEdit")
    
    # Set application icon
    try:
        icon_path = "histoedit_icon.png"
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except:
        pass
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = HistoEditMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
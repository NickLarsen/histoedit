from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtGui import QAction

class MenuBar(QMenuBar):
    """Application menu bar for HistoEdit"""
    
    # Signals
    open_image_requested = None  # Will be set by parent
    exit_requested = None        # Will be set by parent
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_menus()
        
    def setup_menus(self):
        """Setup the menu structure"""
        
        # File menu
        file_menu = self.addMenu("File")
        
        # Open action
        open_action = QAction("Open Image...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.on_open_image)
        file_menu.addAction(open_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.on_exit)
        file_menu.addAction(exit_action)
        
    def on_open_image(self):
        """Handle open image menu action"""
        if self.open_image_requested:
            self.open_image_requested.emit()
            
    def on_exit(self):
        """Handle exit menu action"""
        if self.exit_requested:
            self.exit_requested()
        else:
            # Fallback: close the parent window directly
            if self.parent():
                self.parent().close()
            
    def set_signals(self, open_image_signal, exit_signal):
        """Set the signal handlers"""
        self.open_image_requested = open_image_signal
        self.exit_requested = exit_signal 
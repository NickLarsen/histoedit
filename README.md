# HistoEdit

A cross-platform histogram editor for astrophotography images built with Python and PyQt6.

## Features

- Load and display images (PNG, JPG, JPEG, BMP, TIFF, FITS)
- Cross-platform compatibility (Windows, macOS, Linux)
- Zoom controls (1% to 300%) with scrollable view
- Auto-fit to window on image load
- Simple and intuitive interface
- Custom application icon

## Project Structure

The application is organized into modular components for better maintainability:

- **`main.py`** - Main application entry point and window management
- **`image_viewer.py`** - Image display widget with zoom and scroll functionality
- **`control_panel.py`** - Right-side control panel with zoom controls
- **`menu_bar.py`** - Application menu bar (File menu)
- **`image_loader.py`** - Image loading and format handling
- **`icon.py`** - Custom icon generator for the application

## Setup

1. **Install Python 3.8+** if you haven't already
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

```bash
python main.py
```

## Usage

1. Click "Load Image" or use File → Open Image... (Ctrl+O) to select an image file
2. The image will automatically scale to fit the viewing window
3. Use zoom controls to examine details (1% to 300% zoom)
4. Scroll around when zoomed in to navigate the image
5. Use File → Exit (Ctrl+Q) or close the window to exit

## Development

### Adding New Features

The modular structure makes it easy to add new functionality:

- **New controls**: Add to `control_panel.py`
- **Image processing**: Extend `image_loader.py`
- **New menus**: Modify `menu_bar.py`
- **UI enhancements**: Update `image_viewer.py`

### Icon Generation

To regenerate the application icon:
```bash
python icon.py
```

## Next Steps

This foundation provides a solid base for future enhancements:
- Histogram display and editing
- Image adjustment tools
- Real-time preview of changes
- Support for more image formats
- Advanced astrophotography-specific features 
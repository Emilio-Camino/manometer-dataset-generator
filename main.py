import sys
import os
from PySide6.QtWidgets import QApplication

from core.workspace_manager import WorkspaceManager
from gui.main_window import MainWindow

def main():
    # Set up workspace
    base_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_path = os.path.join(base_dir, "workspace")
    
    # Initialize Core Components
    wm = WorkspaceManager(workspace_path)
    
    # Initialize Application
    app = QApplication(sys.argv)
    
    # Run Window
    window = MainWindow(wm)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

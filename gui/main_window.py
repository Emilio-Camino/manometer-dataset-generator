from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QStackedWidget, QListWidget, QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt

from gui.gallery_view import GalleryView
from gui.views.annotation_view import AnnotationView
from gui.views.needle_annotation_view import NeedleAnnotationView
from gui.views.generation_view import GenerationView
from gui.views.visualization_view import VisualizationView

class MainWindow(QMainWindow):
    def __init__(self, wm):
        super().__init__()
        self.wm = wm
        
        self.setWindowTitle("Manometer Dataset Generator V2")
        self.resize(1024, 768)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Sidebar for navigation
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItem(QListWidgetItem("1. Galería Diales"))
        self.sidebar.addItem(QListWidgetItem("2. Geometría (Diales)"))
        self.sidebar.addItem(QListWidgetItem("3. Galería Agujas"))
        self.sidebar.addItem(QListWidgetItem("4. Pivote (Agujas)"))
        self.sidebar.addItem(QListWidgetItem("5. Generador de Dataset"))
        self.sidebar.addItem(QListWidgetItem("6. Visualización de Dataset"))
        self.sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        main_layout.addWidget(self.sidebar)
        
        # Stacked widget for views
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Initialize views
        self.dial_gallery = GalleryView(self.wm, "dial", "Módulo 1: Galería de Diales", "last_dial_dir")
        self.dial_gallery.image_selected.connect(self._on_image_selected)
        self.stacked_widget.addWidget(self.dial_gallery)
        
        self.annotation_view = AnnotationView(self.wm)
        self.annotation_view.annotation_done.connect(lambda: self.sidebar.setCurrentRow(2)) # ir a galeria de agujas
        self.stacked_widget.addWidget(self.annotation_view)
        
        self.needle_gallery = GalleryView(self.wm, "needle", "Módulo 3: Galería de Agujas", "last_needle_dir")
        self.needle_gallery.image_selected.connect(self._on_image_selected)
        self.stacked_widget.addWidget(self.needle_gallery)
        
        self.needle_annotation_view = NeedleAnnotationView(self.wm)
        self.needle_annotation_view.annotation_done.connect(lambda: self.sidebar.setCurrentRow(4)) # ir a generar
        self.stacked_widget.addWidget(self.needle_annotation_view)
        
        self.generation_view = GenerationView(self.wm)
        self.stacked_widget.addWidget(self.generation_view)
        
        self.visualization_view = VisualizationView(self.wm)
        self.stacked_widget.addWidget(self.visualization_view)
        
        # Start at dial gallery
        self.sidebar.setCurrentRow(0)
        
    def _on_sidebar_changed(self, index):
        self.stacked_widget.setCurrentIndex(index)
        
    def _on_image_selected(self, img_path, gallery_type):
        try:
            if gallery_type == "dial":
                self.annotation_view.load_image(img_path)
                self.sidebar.setCurrentRow(1)
            elif gallery_type == "needle":
                self.needle_annotation_view.load_image(img_path)
                self.sidebar.setCurrentRow(3)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la imagen:\n{str(e)}")

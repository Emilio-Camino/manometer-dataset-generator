import os
import json
import glob
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFileDialog, QMessageBox)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

class VisualizationView(QWidget):
    def __init__(self, wm, parent=None):
        super().__init__(parent)
        self.wm = wm
        self.current_images = []
        self.current_index = -1
        
        # Enable key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        layout = QVBoxLayout(self)
        
        # Header
        self.lbl_title = QLabel("Módulo 6: Visualización de Dataset")
        font = self.lbl_title.font()
        font.setBold(True)
        self.lbl_title.setFont(font)
        layout.addWidget(self.lbl_title)
        
        # Load Button
        self.btn_load = QPushButton("Seleccionar Dataset (Carpeta raíz)")
        self.btn_load.clicked.connect(self._on_load_dataset)
        layout.addWidget(self.btn_load)
        
        # Info Top
        top_info_layout = QHBoxLayout()
        self.lbl_counter = QLabel("Imagen 0 de 0")
        self.lbl_filename = QLabel("")
        top_info_layout.addWidget(self.lbl_counter)
        top_info_layout.addStretch()
        top_info_layout.addWidget(self.lbl_filename)
        layout.addLayout(top_info_layout)
        
        # Image Display
        self.lbl_image = QLabel("No hay imagen cargada")
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setMinimumSize(400, 400)
        self.lbl_image.setStyleSheet("border: 1px solid #ccc; background-color: #333;")
        layout.addWidget(self.lbl_image, stretch=1)
        
        # Info Bottom
        self.lbl_expected_value = QLabel("Valor Generado: --")
        font_large = self.lbl_expected_value.font()
        font_large.setPointSize(16)
        font_large.setBold(True)
        self.lbl_expected_value.setFont(font_large)
        self.lbl_expected_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_expected_value)
        
        # Navigation
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("< Anterior")
        self.btn_prev.clicked.connect(self._on_prev)
        self.btn_next = QPushButton("Siguiente >")
        self.btn_next.clicked.connect(self._on_next)
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        layout.addLayout(nav_layout)
        
        self._update_ui()
        
    def _on_load_dataset(self):
        last_out = self.wm.get_setting("last_output_dir", "")
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Dataset (Carpeta que contiene images/ y labels/)", last_out)
        
        if folder:
            images_dir = os.path.join(folder, "images")
            labels_dir = os.path.join(folder, "labels")
            
            if not os.path.exists(images_dir) or not os.path.exists(labels_dir):
                QMessageBox.warning(self, "Error", "La carpeta seleccionada no parece ser un dataset válido (faltan carpetas images/ o labels/).")
                return
                
            # Scan for images
            self.current_images = sorted(glob.glob(os.path.join(images_dir, "*.png")))
            if not self.current_images:
                # Intento con jpg si no hay png
                self.current_images = sorted(glob.glob(os.path.join(images_dir, "*.jpg")))
                
            if not self.current_images:
                QMessageBox.warning(self, "Error", "No se encontraron imágenes en la carpeta images/.")
                return
                
            self.current_labels_dir = labels_dir
            self.current_index = 0
            self._update_ui()
            self.setFocus() # Request focus for keyboard nav
            
    def _update_ui(self):
        if not self.current_images or self.current_index < 0:
            self.lbl_image.setText("No hay imagen cargada")
            self.lbl_counter.setText("Imagen 0 de 0")
            self.lbl_filename.setText("")
            self.lbl_expected_value.setText("Valor Generado: --")
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            return
            
        img_path = self.current_images[self.current_index]
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        json_path = os.path.join(self.current_labels_dir, f"{base_name}.json")
        
        # Update Image
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            # Escalar manteniendo proporción
            scaled_pixmap = pixmap.scaled(self.lbl_image.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_image.setPixmap(scaled_pixmap)
        
        # Update Info
        self.lbl_counter.setText(f"Imagen {self.current_index + 1} de {len(self.current_images)}")
        self.lbl_filename.setText(os.path.basename(img_path))
        
        # Update Expected Value
        val = "--"
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "value" in data:
                        val = str(data['value'])
            except Exception:
                pass
                
        self.lbl_expected_value.setText(f"Valor Generado: {val}")
        
        # Update Buttons
        self.btn_prev.setEnabled(self.current_index > 0)
        self.btn_next.setEnabled(self.current_index < len(self.current_images) - 1)
        
    def _on_prev(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._update_ui()
            
    def _on_next(self):
        if self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            self._update_ui()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-scale image when window size changes
        if self.current_images and self.current_index >= 0:
            img_path = self.current_images[self.current_index]
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.lbl_image.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl_image.setPixmap(scaled_pixmap)
                
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self._on_prev()
        elif event.key() == Qt.Key.Key_Right:
            self._on_next()
        else:
            super().keyPressEvent(event)

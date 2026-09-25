import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QFileDialog, 
                               QListWidget, QListWidgetItem, QLabel, QMessageBox)
from PySide6.QtCore import Signal, Qt

class GalleryView(QWidget):
    image_selected = Signal(str, str) # image_path, gallery_type (dial or needle)
    
    def __init__(self, wm, gallery_type, title, setting_key, parent=None):
        super().__init__(parent)
        self.wm = wm
        self.gallery_type = gallery_type
        self.setting_key = setting_key
        
        layout = QVBoxLayout(self)
        
        self.lbl_title = QLabel(title)
        font = self.lbl_title.font()
        font.setBold(True)
        self.lbl_title.setFont(font)
        layout.addWidget(self.lbl_title)
        
        self.btn_select_folder = QPushButton("Seleccionar carpeta de imágenes")
        self.btn_select_folder.clicked.connect(self._on_select_folder)
        layout.addWidget(self.btn_select_folder)
        
        self.lbl_info = QLabel("Seleccione una carpeta para buscar imágenes.")
        layout.addWidget(self.lbl_info)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        self.current_images = []
        
        # Load last used directory
        last_dir = self.wm.get_setting(self.setting_key)
        if last_dir and os.path.exists(last_dir):
            self.load_folder(last_dir)
            
    def _find_images(self, folder):
        valid_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}
        images = []
        for root, dirs, files in os.walk(folder):
            for f in files:
                if os.path.splitext(f)[1].lower() in valid_exts:
                    images.append(os.path.join(root, f))
        return images
        
    def _on_select_folder(self):
        last_dir = self.wm.get_setting(self.setting_key, "")
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio", last_dir)
        if folder:
            self.load_folder(folder)
            
    def load_folder(self, folder):
        self.list_widget.clear()
        self.current_images = self._find_images(folder)
        
        self.wm.set_setting(self.setting_key, folder)
        self.lbl_info.setText(f"Carpeta: {folder}\nImágenes encontradas: {len(self.current_images)}")
        
        for img_path in self.current_images:
            item = QListWidgetItem(os.path.basename(img_path))
            item.setData(Qt.ItemDataRole.UserRole, img_path)
            self.list_widget.addItem(item)
            
    def _on_item_double_clicked(self, item):
        img_path = item.data(Qt.ItemDataRole.UserRole)
        self.image_selected.emit(img_path, self.gallery_type)

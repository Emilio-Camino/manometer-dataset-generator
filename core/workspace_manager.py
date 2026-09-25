import os
import json
import glob

class WorkspaceManager:
    def __init__(self, workspace_path):
        self.workspace_path = workspace_path
        os.makedirs(self.workspace_path, exist_ok=True)
        
        self.dials_config_path = os.path.join(workspace_path, "dials_config.json")
        self.needles_config_path = os.path.join(workspace_path, "needles_config.json")
        self.settings_path = os.path.join(workspace_path, "settings.json")
        
        self._migrate_old_configs()
        
    def load_json(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
        
    def save_json(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
    def _migrate_old_configs(self):
        """Migrate global configs to individual files inside 'labels' folders."""
        for global_path in [self.dials_config_path, self.needles_config_path]:
            if os.path.exists(global_path):
                data = self.load_json(global_path)
                for key, info in data.items():
                    img_path = info.get("path")
                    if img_path and os.path.exists(img_path):
                        self.save_local_annotation(img_path, info)
                
                # Mark as migrated
                os.rename(global_path, global_path + ".migrated")
            
    # Settings
    def get_setting(self, key, default=None):
        settings = self.load_json(self.settings_path)
        return settings.get(key, default)
        
    def set_setting(self, key, value):
        settings = self.load_json(self.settings_path)
        settings[key] = value
        self.save_json(self.settings_path, settings)

    # Local Annotations
    def get_label_path(self, img_path):
        """Returns the path to the individual JSON file for a given image."""
        dir_name = os.path.dirname(img_path)
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        return os.path.join(dir_name, "labels", f"{base_name}.json")
        
    def load_local_annotation(self, img_path):
        label_path = self.get_label_path(img_path)
        return self.load_json(label_path)
        
    def save_local_annotation(self, img_path, data):
        label_path = self.get_label_path(img_path)
        self.save_json(label_path, data)
        
    def get_all_annotations_in_folder(self, folder_path):
        """Scans the labels/ directory inside the folder and returns all annotations."""
        annotations = {}
        if not folder_path or not os.path.exists(folder_path):
            return annotations
            
        labels_dir = os.path.join(folder_path, "labels")
        if not os.path.exists(labels_dir):
            return annotations
            
        json_files = glob.glob(os.path.join(labels_dir, "*.json"))
        for jf in json_files:
            data = self.load_json(jf)
            # Use filename as key just for internal dictionary reference
            base_name = os.path.basename(jf)
            annotations[base_name] = data
            
        return annotations

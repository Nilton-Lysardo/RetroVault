import os
import json
import re

class RomScanner:
    def __init__(self, config_path):
        self.config_path = config_path
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
    def scan_all(self):
        results = []
        for console in self.config.get('rom_directories', {}):
            results.extend(self.scan_console(console))
        return results
        
    def scan_console(self, console_name):
        dirs = self.config.get('rom_directories', {}).get(console_name, [])
        extensions = self.config.get('rom_extensions', {}).get(console_name, [])
        results = []
        
        for d in dirs:
            if not os.path.isdir(d):
                continue
                
            for root, _, files in os.walk(d):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in extensions:
                        file_path = os.path.join(root, file)
                        # Skip typical save files/states just in case they share extensions or for safety
                        if ext in ['.srm', '.zst', '.state']:
                            continue
                        
                        file_info = self._get_file_info(file_path, console_name)
                        if file_info:
                            results.append(file_info)
                            
        return results

    def _clean_name(self, filename):
        name = os.path.splitext(filename)[0]
        # Remove typical scene release tags like (U), (E), [!], (Rev 1), etc.
        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'\[.*?\]', '', name)
        # Clean up double spaces and trailing spaces
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def _get_file_info(self, filepath, console_name):
        try:
            stat = os.stat(filepath)
            filename = os.path.basename(filepath)
            return {
                'name': filename,
                'clean_name': self._clean_name(filename),
                'console': console_name,
                'file_path': filepath.replace('\\', '/'), # Ensure forward slashes
                'file_size': stat.st_size,
                'file_extension': os.path.splitext(filename)[1].lower()
            }
        except Exception:
            return None

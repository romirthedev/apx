import os
import shutil
import subprocess
import glob
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class FileManager:
    def __init__(self):
        self.home_dir = Path.home()
        self.current_dir = Path.cwd()
    
    def open_file(self, file_path: str) -> str:
        """Open a file with the default application."""
        try:
            # Resolve relative paths
            path = self._resolve_path(file_path)
            
            if not path.exists():
                return f"File not found: {path}"
            
            # Open file with default application
            if os.name == 'nt':  # Windows
                os.startfile(str(path))
            elif os.name == 'posix':  # macOS and Linux
                if os.uname().sysname == 'Darwin':  # macOS
                    subprocess.run(['open', str(path)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(path)])
            
            return f"Opened {path.name}"
            
        except Exception as e:
            logger.error(f"Error opening file: {str(e)}")
            return f"Failed to open file: {str(e)}"
    
    def create_file(self, file_path: str, content: str = "") -> str:
        """Create a new file."""
        try:
            path = self._resolve_path(file_path)
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if path.exists():
                return f"File already exists: {path}"
            
            # Create the file
            path.write_text(content)
            
            return f"Created file: {path}"
            
        except Exception as e:
            logger.error(f"Error creating file: {str(e)}")
            return f"Failed to create file: {str(e)}"
    
    def create_folder(self, folder_path: str) -> str:
        """Create a new folder."""
        try:
            path = self._resolve_path(folder_path)
            
            if path.exists():
                return f"Folder already exists: {path}"
            
            path.mkdir(parents=True, exist_ok=True)
            
            return f"Created folder: {path}"
            
        except Exception as e:
            logger.error(f"Error creating folder: {str(e)}")
            return f"Failed to create folder: {str(e)}"
    
    def delete(self, path_str: str) -> str:
        """Delete a file or folder."""
        try:
            path = self._resolve_path(path_str)
            
            if not path.exists():
                return f"Path not found: {path}"
            
            if path.is_file():
                path.unlink()
                return f"Deleted file: {path}"
            elif path.is_dir():
                shutil.rmtree(path)
                return f"Deleted folder: {path}"
            
        except Exception as e:
            logger.error(f"Error deleting: {str(e)}")
            return f"Failed to delete: {str(e)}"
    
    def copy(self, source: str, destination: str) -> str:
        """Copy a file or folder."""
        try:
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(destination)
            
            if not src_path.exists():
                return f"Source not found: {src_path}"
            
            if src_path.is_file():
                # If destination is a directory, copy file into it
                if dst_path.is_dir():
                    dst_path = dst_path / src_path.name
                
                # Create parent directories if needed
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(src_path, dst_path)
                return f"Copied file from {src_path} to {dst_path}"
            
            elif src_path.is_dir():
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                return f"Copied folder from {src_path} to {dst_path}"
            
        except Exception as e:
            logger.error(f"Error copying: {str(e)}")
            return f"Failed to copy: {str(e)}"
    
    def move(self, source: str, destination: str) -> str:
        """Move a file or folder."""
        try:
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(destination)
            
            if not src_path.exists():
                return f"Source not found: {src_path}"
            
            # If destination is a directory, move source into it
            if dst_path.is_dir():
                dst_path = dst_path / src_path.name
            
            # Create parent directories if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            
            return f"Moved {src_path} to {dst_path}"
            
        except Exception as e:
            logger.error(f"Error moving: {str(e)}")
            return f"Failed to move: {str(e)}"
    
    def search_files(self, query: str, search_path: Optional[str] = None) -> str:
        """Search for files by name or content."""
        try:
            if search_path:
                base_path = self._resolve_path(search_path)
            else:
                base_path = self.home_dir
            
            if not base_path.exists() or not base_path.is_dir():
                return f"Invalid search path: {base_path}"

            logger.info(f"search_files: Searching for query '{query}' in path '{base_path}'")

            # Search by filename
            filename_matches = []
            for pattern in [f"*{query}*", f"*{query.lower()}*", f"*{query.upper()}*"]:
                matches = list(base_path.rglob(pattern))
                filename_matches.extend(matches)
            
            # Remove duplicates
            filename_matches = list(set(filename_matches))
            
            if not filename_matches:
                return f"No files found matching '{query}'"
            
            # Format results
            results = []
            for match in filename_matches[:20]:  # Limit to 20 results
                relative_path = match.relative_to(base_path)
                file_type = "Folder" if match.is_dir() else "File"
                results.append(f"{file_type}: {relative_path}")
            
            result_text = f"Found {len(filename_matches)} matches for '{query}':\n\n"
            result_text += "\n".join(results)
            
            if len(filename_matches) > 20:
                result_text += f"\n\n... and {len(filename_matches) - 20} more"
            
            return result_text
            
        except Exception as e:
            logger.error(f"Error searching files: {str(e)}")
            return f"Failed to search files: {str(e)}"
    
    def edit_file(self, file_path: str) -> str:
        """Open a file for editing."""
        try:
            path = self._resolve_path(file_path)
            
            if not path.exists():
                return f"File not found: {path}"
            
            if not path.is_file():
                return f"Not a file: {path}"
            
            # Open with default text editor
            if os.name == 'nt':  # Windows
                subprocess.run(['notepad', str(path)])
            elif os.name == 'posix':
                if os.uname().sysname == 'Darwin':  # macOS
                    subprocess.run(['open', '-t', str(path)])
                else:  # Linux
                    # Try common editors
                    editors = ['code', 'gedit', 'nano', 'vim']
                    for editor in editors:
                        try:
                            subprocess.run([editor, str(path)], check=True)
                            break
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue
            
            return f"Opened {path.name} for editing"
            
        except Exception as e:
            logger.error(f"Error editing file: {str(e)}")
            return f"Failed to edit file: {str(e)}"
    
    def get_file_info(self, file_path: str) -> str:
        """Get information about a file or folder."""
        try:
            path = self._resolve_path(file_path)
            
            if not path.exists():
                return f"Path not found: {path}"
            
            info = []
            info.append(f"Path: {path}")
            info.append(f"Type: {'Directory' if path.is_dir() else 'File'}")
            
            stat = path.stat()
            info.append(f"Size: {self._format_size(stat.st_size)}")
            info.append(f"Modified: {self._format_time(stat.st_mtime)}")
            info.append(f"Created: {self._format_time(stat.st_ctime)}")
            
            if path.is_file():
                info.append(f"Extension: {path.suffix}")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return f"Failed to get file info: {str(e)}"
    
    def _resolve_path(self, path_str: str) -> Path:
        """Resolve a path string to an absolute Path object."""
        path = Path(path_str).expanduser()
        
        if not path.is_absolute():
            path = self.current_dir / path
        
        return path.resolve()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _format_time(self, timestamp: float) -> str:
        """Format timestamp in human-readable format."""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

import os
import shutil
import subprocess
import glob
import logging
import psutil
import platform
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class FileManager:
    def __init__(self):
        self.home_dir = Path.home()
        self.current_dir = Path.cwd()
        self.platform = platform.system().lower()
    
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
    
    def delete(self, path_str: str, confirm: bool = False) -> str:
        """Delete a file or folder with optional confirmation."""
        try:
            path = self._resolve_path(path_str)
            
            if not path.exists():
                return f"Path not found: {path}"
            
            # Check if this is a destructive operation that needs confirmation
            if not confirm and self._is_destructive_operation(path):
                return f"⚠️ CONFIRMATION REQUIRED: This will permanently delete '{path}'. This action cannot be undone. Please confirm if you want to proceed with this deletion."
            
            if path.is_file():
                path.unlink()
                return f"✅ Deleted file: {path}"
            elif path.is_dir():
                shutil.rmtree(path)
                return f"✅ Deleted folder: {path}"
            
        except Exception as e:
            logger.error(f"Error deleting: {str(e)}")
            return f"❌ Failed to delete: {str(e)}"
    
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

    def find_largest_files(self, search_path: Optional[str] = None, limit: int = 10) -> str:
        """Find the largest files on the system."""
        try:
            if search_path:
                base_path = self._resolve_path(search_path)
            else:
                base_path = self.home_dir
            
            if not base_path.exists() or not base_path.is_dir():
                return f"❌ Invalid search path: {base_path}"
            
            logger.info(f"Finding largest files in: {base_path}")
            
            files_info = []
            
            # Walk through all files
            for root, dirs, files in os.walk(base_path):
                # Skip system directories that might cause permission issues
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['System', 'Library']]
                
                for file in files:
                    try:
                        file_path = Path(root) / file
                        if file_path.is_file() and not file_path.is_symlink():
                            size = file_path.stat().st_size
                            if size > 0:  # Only include non-empty files
                                files_info.append({
                                    'name': file,
                                    'path': str(file_path),
                                    'size': size,
                                    'size_mb': size / (1024**2),
                                    'size_gb': size / (1024**3)
                                })
                    except (PermissionError, OSError, FileNotFoundError):
                        continue
            
            if not files_info:
                return "📂 No files found or accessible in the specified location."
            
            # Sort by size (largest first)
            files_info.sort(key=lambda x: x['size'], reverse=True)
            
            # Format the output with enhanced styling
            result_lines = []
            result_lines.append(f"## 📁 Top {limit} Largest Files")
            result_lines.append(f"**Search Location:** `{base_path}`\n")
            
            for i, file_info in enumerate(files_info[:limit]):
                if file_info['size_gb'] >= 1:
                    size_str = f"{file_info['size_gb']:.2f} GB"
                    size_emoji = "🔴"  # Red for very large files
                elif file_info['size_mb'] >= 100:
                    size_str = f"{file_info['size_mb']:.1f} MB"
                    size_emoji = "🟡"  # Yellow for large files
                else:
                    size_str = f"{file_info['size_mb']:.1f} MB"
                    size_emoji = "🟢"  # Green for smaller files
                
                # Truncate long file names for better display
                display_name = file_info['name'][:50] + "..." if len(file_info['name']) > 50 else file_info['name']
                
                result_lines.append(f"**{i+1}.** {size_emoji} **{display_name}**")
                result_lines.append(f"   📏 Size: `{size_str}`")
                result_lines.append(f"   📂 Path: `{file_info['path']}`\n")
            
            # Add summary
            total_size = sum(f['size'] for f in files_info[:limit])
            total_gb = total_size / (1024**3)
            result_lines.append("---")
            result_lines.append(f"**📊 Summary:** Top {limit} files total **{total_gb:.2f} GB**")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"Error finding largest files: {str(e)}")
            return f"❌ **Error finding largest files:** {str(e)}"

    def find_smallest_files(self, search_path: Optional[str] = None, limit: int = 10) -> str:
        """Find the smallest files on the system."""
        try:
            if search_path:
                base_path = self._resolve_path(search_path)
            else:
                base_path = self.home_dir
            
            if not base_path.exists() or not base_path.is_dir():
                return f"Invalid search path: {base_path}"
            
            logger.info(f"Finding smallest files in: {base_path}")
            
            files_info = []
            
            # Walk through all files
            for root, dirs, files in os.walk(base_path):
                # Skip system directories that might cause permission issues
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['System', 'Library']]
                
                for file in files:
                    try:
                        file_path = Path(root) / file
                        if file_path.is_file() and not file_path.is_symlink():
                            size = file_path.stat().st_size
                            files_info.append({
                                'name': file,
                                'path': str(file_path),
                                'size': size,
                                'size_kb': size / 1024,
                                'size_mb': size / (1024**2)
                            })
                    except (PermissionError, OSError, FileNotFoundError):
                        continue
            
            if not files_info:
                return "No files found or accessible."
            
            # Sort by size (smallest first)
            files_info.sort(key=lambda x: x['size'])
            
            # Format the output
            info = [f"📁 Top {limit} smallest files:\n"]
            info.append(f"{'Rank':<4} {'File Name':<40} {'Size':<12} {'Path'}")
            info.append("-" * 100)
            
            for i, file_info in enumerate(files_info[:limit]):
                if file_info['size'] == 0:
                    size_str = "0 B"
                elif file_info['size_kb'] < 1:
                    size_str = f"{file_info['size']} B"
                elif file_info['size_mb'] < 1:
                    size_str = f"{file_info['size_kb']:.1f} KB"
                else:
                    size_str = f"{file_info['size_mb']:.2f} MB"
                
                name = file_info['name'][:39] if len(file_info['name']) > 39 else file_info['name']
                info.append(f"{i+1:<4} {name:<40} {size_str:<12} {file_info['path']}")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error finding smallest files: {str(e)}")
            return f"❌ Error finding smallest files: {str(e)}"

    def get_directory_analysis(self, directory_path: Optional[str] = None) -> str:
        """Get comprehensive analysis of a directory."""
        try:
            if directory_path:
                path = self._resolve_path(directory_path)
            else:
                path = self.home_dir
            
            if not path.exists() or not path.is_dir():
                return f"Invalid directory path: {path}"
            
            logger.info(f"Analyzing directory: {path}")
            
            total_size = 0
            file_count = 0
            dir_count = 0
            file_types = {}
            largest_files = []
            
            # Walk through directory
            for root, dirs, files in os.walk(path):
                dir_count += len(dirs)
                
                for file in files:
                    try:
                        file_path = Path(root) / file
                        if file_path.is_file() and not file_path.is_symlink():
                            size = file_path.stat().st_size
                            total_size += size
                            file_count += 1
                            
                            # Track file types
                            ext = file_path.suffix.lower()
                            if ext:
                                file_types[ext] = file_types.get(ext, 0) + 1
                            else:
                                file_types['(no extension)'] = file_types.get('(no extension)', 0) + 1
                            
                            # Track largest files
                            largest_files.append({
                                'name': file,
                                'path': str(file_path),
                                'size': size
                            })
                            
                    except (PermissionError, OSError, FileNotFoundError):
                        continue
            
            # Sort largest files
            largest_files.sort(key=lambda x: x['size'], reverse=True)
            
            # Format output
            info = []
            info.append(f"📊 Directory Analysis: {path}")
            info.append("=" * 60)
            info.append(f"Total Size: {self._format_size(total_size)}")
            info.append(f"Files: {file_count:,}")
            info.append(f"Directories: {dir_count:,}")
            info.append("")
            
            # Top file types
            if file_types:
                info.append("📄 Top File Types:")
                sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
                for ext, count in sorted_types[:10]:
                    info.append(f"  {ext}: {count:,} files")
                info.append("")
            
            # Largest files in directory
            if largest_files:
                info.append("📁 Largest Files:")
                for i, file_info in enumerate(largest_files[:5]):
                    size_str = self._format_size(file_info['size'])
                    info.append(f"  {i+1}. {file_info['name']} - {size_str}")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error analyzing directory: {str(e)}")
            return f"❌ Error analyzing directory: {str(e)}"

    def get_downloads_analysis(self) -> str:
        """Analyze the Downloads folder with enhanced robustness."""
        downloads_path = self.home_dir / "Downloads"
        if not downloads_path.exists():
            return "Downloads folder not found."
        
        try:
            result = self.get_directory_analysis(str(downloads_path))
            
            # Add specific downloads insights
            additional_info = self._get_downloads_insights(downloads_path)
            if additional_info:
                result += "\n\n" + additional_info
                
            return result
        except Exception as e:
            logger.error(f"Error analyzing downloads: {str(e)}")
            # Fallback to basic listing
            return self._get_basic_directory_listing(downloads_path, "Downloads")

    def get_desktop_analysis(self) -> str:
        """Analyze the Desktop folder with enhanced robustness."""
        desktop_path = self.home_dir / "Desktop"
        if not desktop_path.exists():
            return "Desktop folder not found."
        
        try:
            result = self.get_directory_analysis(str(desktop_path))
            
            # Add specific desktop insights
            additional_info = self._get_desktop_insights(desktop_path)
            if additional_info:
                result += "\n\n" + additional_info
                
            return result
        except Exception as e:
            logger.error(f"Error analyzing desktop: {str(e)}")
            # Fallback to basic listing
            return self._get_basic_directory_listing(desktop_path, "Desktop")

    def get_documents_analysis(self) -> str:
        """Analyze the Documents folder with enhanced robustness."""
        documents_path = self.home_dir / "Documents"
        if not documents_path.exists():
            return "Documents folder not found."
        
        try:
            result = self.get_directory_analysis(str(documents_path))
            
            # Add specific documents insights
            additional_info = self._get_documents_insights(documents_path)
            if additional_info:
                result += "\n\n" + additional_info
                
            return result
        except Exception as e:
            logger.error(f"Error analyzing documents: {str(e)}")
            # Fallback to basic listing
            return self._get_basic_directory_listing(documents_path, "Documents")
    
    def _get_downloads_insights(self, downloads_path: Path) -> str:
        """Get specific insights about downloads folder."""
        try:
            insights = []
            
            # Count file types
            file_types = {}
            recent_files = []
            large_files = []
            
            for item in downloads_path.iterdir():
                if item.is_file():
                    # File type analysis
                    ext = item.suffix.lower()
                    if not ext:
                        ext = "no extension"
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
                    # Recent files (last 7 days)
                    if item.stat().st_mtime > (datetime.datetime.now().timestamp() - 7 * 24 * 3600):
                        recent_files.append(item.name)
                    
                    # Large files (>100MB)
                    if item.stat().st_size > 100 * 1024 * 1024:
                        large_files.append((item.name, self._format_size(item.stat().st_size)))
            
            if file_types:
                insights.append("📊 File Types:")
                for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                    insights.append(f"  • {ext}: {count} files")
            
            if recent_files:
                insights.append(f"\n🕒 Recent Downloads ({len(recent_files)} files in last 7 days):")
                for file in recent_files[:5]:
                    insights.append(f"  • {file}")
                if len(recent_files) > 5:
                    insights.append(f"  • ... and {len(recent_files) - 5} more")
            
            if large_files:
                insights.append(f"\n📦 Large Files (>100MB):")
                for name, size in large_files[:3]:
                    insights.append(f"  • {name} ({size})")
            
            return "\n".join(insights) if insights else ""
            
        except Exception as e:
            logger.error(f"Error getting downloads insights: {str(e)}")
            return ""
    
    def _get_desktop_insights(self, desktop_path: Path) -> str:
        """Get specific insights about desktop folder."""
        try:
            insights = []
            
            # Count different item types
            folders = 0
            files = 0
            shortcuts = 0
            
            for item in desktop_path.iterdir():
                if item.is_dir():
                    folders += 1
                elif item.is_file():
                    files += 1
                    if item.suffix.lower() in ['.lnk', '.alias', '.desktop']:
                        shortcuts += 1
            
            insights.append("🖥️ Desktop Organization:")
            insights.append(f"  • Folders: {folders}")
            insights.append(f"  • Files: {files}")
            if shortcuts > 0:
                insights.append(f"  • Shortcuts: {shortcuts}")
            
            if files > 10:
                insights.append("\n💡 Tip: Consider organizing files into folders for better desktop management")
            
            return "\n".join(insights)
            
        except Exception as e:
            logger.error(f"Error getting desktop insights: {str(e)}")
            return ""
    
    def _get_documents_insights(self, documents_path: Path) -> str:
        """Get specific insights about documents folder."""
        try:
            insights = []
            
            # Count document types
            doc_types = {
                'text': ['.txt', '.md', '.rtf'],
                'office': ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
                'pdf': ['.pdf'],
                'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
                'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c']
            }
            
            type_counts = {doc_type: 0 for doc_type in doc_types}
            
            for item in documents_path.rglob('*'):
                if item.is_file():
                    ext = item.suffix.lower()
                    for doc_type, extensions in doc_types.items():
                        if ext in extensions:
                            type_counts[doc_type] += 1
                            break
            
            insights.append("📄 Document Types:")
            for doc_type, count in type_counts.items():
                if count > 0:
                    insights.append(f"  • {doc_type.title()}: {count} files")
            
            return "\n".join(insights) if any(type_counts.values()) else ""
            
        except Exception as e:
            logger.error(f"Error getting documents insights: {str(e)}")
            return ""
    
    def _get_basic_directory_listing(self, directory_path: Path, folder_name: str) -> str:
        """Fallback method for basic directory listing when analysis fails."""
        try:
            items = list(directory_path.iterdir())
            
            if not items:
                return f"{folder_name} folder is empty."
            
            result = [f"📁 {folder_name.upper()} FOLDER CONTENTS", "=" * 40]
            
            # Sort items: directories first, then files
            dirs = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]
            
            if dirs:
                result.append(f"\n📂 Folders ({len(dirs)}):")
                for item in sorted(dirs)[:10]:
                    result.append(f"  • {item.name}/")
                if len(dirs) > 10:
                    result.append(f"  • ... and {len(dirs) - 10} more folders")
            
            if files:
                result.append(f"\n📄 Files ({len(files)}):")
                for item in sorted(files)[:10]:
                    try:
                        size = self._format_size(item.stat().st_size)
                        result.append(f"  • {item.name} ({size})")
                    except:
                        result.append(f"  • {item.name}")
                if len(files) > 10:
                    result.append(f"  • ... and {len(files) - 10} more files")
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error in basic directory listing: {str(e)}")
            return f"❌ Unable to access {folder_name} folder: {str(e)}"

    def clean_temp_files(self, confirm: bool = False) -> str:
        """Clean temporary files (with confirmation)."""
        try:
            if not confirm:
                return "⚠️ CONFIRMATION REQUIRED: This will delete temporary files from your system. This action cannot be undone. Please confirm if you want to proceed with cleaning temporary files."
            
            temp_dirs = []
            files_deleted = 0
            space_freed = 0
            
            # Common temp directories
            if self.platform == "darwin":  # macOS
                temp_dirs = [
                    "/tmp",
                    str(self.home_dir / "Library/Caches"),
                    "/var/folders"
                ]
            elif self.platform == "windows":
                temp_dirs = [
                    os.environ.get("TEMP", ""),
                    os.environ.get("TMP", ""),
                    "C:\\Windows\\Temp"
                ]
            else:  # Linux
                temp_dirs = [
                    "/tmp",
                    "/var/tmp"
                ]
            
            for temp_dir in temp_dirs:
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                try:
                                    file_path = Path(root) / file
                                    if file_path.is_file():
                                        size = file_path.stat().st_size
                                        file_path.unlink()
                                        files_deleted += 1
                                        space_freed += size
                                except (PermissionError, OSError):
                                    continue
                    except (PermissionError, OSError):
                        continue
            
            return f"✅ Cleaned {files_deleted} temporary files, freed {self._format_size(space_freed)} of space."
            
        except Exception as e:
            logger.error(f"Error cleaning temp files: {str(e)}")
            return f"❌ Error cleaning temp files: {str(e)}"
    
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

    def find_recent_files_by_type(self, file_type: str, days: int = 7) -> str:
        """Find recent files of a specific type within the last N days."""
        try:
            # Common directories to search
            search_dirs = [
                self.home_dir / "Downloads",
                self.home_dir / "Desktop", 
                self.home_dir / "Documents",
                self.home_dir / "Pictures"
            ]
            
            # File extension mapping
            type_extensions = {
                'png': ['.png'],
                'jpg': ['.jpg', '.jpeg'],
                'pdf': ['.pdf'],
                'doc': ['.doc', '.docx'],
                'txt': ['.txt'],
                'zip': ['.zip', '.rar', '.7z'],
                'video': ['.mp4', '.mov', '.avi', '.mkv'],
                'audio': ['.mp3', '.wav', '.m4a', '.flac'],
                'image': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'],
                'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf']
            }
            
            extensions = type_extensions.get(file_type.lower(), [f'.{file_type.lower()}'])
            
            # Calculate cutoff time
            cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            recent_files = []
            
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                    
                try:
                    for file_path in search_dir.rglob('*'):
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            # Check if file matches the type
                            if any(file_path.suffix.lower() == ext for ext in extensions):
                                try:
                                    stat = file_path.stat()
                                    # Check modification time
                                    if stat.st_mtime >= cutoff_timestamp:
                                        recent_files.append({
                                            'name': file_path.name,
                                            'path': str(file_path),
                                            'size': stat.st_size,
                                            'modified': stat.st_mtime,
                                            'directory': search_dir.name
                                        })
                                except (PermissionError, OSError):
                                    continue
                except (PermissionError, OSError):
                    continue
            
            if not recent_files:
                return f"📂 No **{file_type}** files found in the last **{days} days**.\n\n*Searched in: Downloads, Desktop, Documents, Pictures*"
            
            # Sort by modification time (newest first)
            recent_files.sort(key=lambda x: x['modified'], reverse=True)
            
            # Format the output with enhanced styling
            result_lines = []
            result_lines.append(f"## 📁 Recent {file_type.upper()} Files")
            result_lines.append(f"**Time Period:** Last {days} days")
            result_lines.append(f"**Files Found:** {len(recent_files)}\n")
            
            for i, file_info in enumerate(recent_files[:15]):  # Limit to 15 files
                # Format file size
                size_mb = file_info['size'] / (1024**2)
                if size_mb >= 1:
                    size_str = f"{size_mb:.1f} MB"
                else:
                    size_kb = file_info['size'] / 1024
                    size_str = f"{size_kb:.1f} KB"
                
                # Format modification time
                mod_time = datetime.datetime.fromtimestamp(file_info['modified'])
                time_str = mod_time.strftime("%b %d, %Y at %I:%M %p")
                
                # Get appropriate emoji based on file type
                type_emoji = {
                    'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'image': '🖼️',
                    'pdf': '📄', 'doc': '📝', 'docx': '📝', 'txt': '📝', 'document': '📝',
                    'zip': '📦', 'rar': '📦', '7z': '📦',
                    'video': '🎥', 'mp4': '🎥', 'mov': '🎥',
                    'audio': '🎵', 'mp3': '🎵', 'wav': '🎵'
                }.get(file_type.lower(), '📄')
                
                result_lines.append(f"**{i+1}.** {type_emoji} **{file_info['name']}**")
                result_lines.append(f"   📏 Size: `{size_str}`")
                result_lines.append(f"   📅 Modified: `{time_str}`")
                result_lines.append(f"   📂 Location: `{file_info['directory']}`")
                result_lines.append(f"   📍 Path: `{file_info['path']}`\n")
            
            if len(recent_files) > 15:
                result_lines.append(f"*... and {len(recent_files) - 15} more files*")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"Error finding recent {file_type} files: {str(e)}")
            return f"❌ **Error finding recent {file_type} files:** {str(e)}"
    
    def find_recent_files(self, days: int = 7) -> str:
        """Find all recent files within the last N days."""
        try:
            # Common directories to search
            search_dirs = [
                self.home_dir / "Downloads",
                self.home_dir / "Desktop", 
                self.home_dir / "Documents",
                self.home_dir / "Pictures"
            ]
            
            # Calculate cutoff time
            cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            recent_files = []
            
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                    
                try:
                    for file_path in search_dir.rglob('*'):
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            try:
                                stat = file_path.stat()
                                # Check modification time
                                if stat.st_mtime >= cutoff_timestamp:
                                    recent_files.append({
                                        'name': file_path.name,
                                        'path': str(file_path),
                                        'size': stat.st_size,
                                        'modified': stat.st_mtime,
                                        'extension': file_path.suffix.lower(),
                                        'directory': search_dir.name
                                    })
                            except (PermissionError, OSError):
                                continue
                except (PermissionError, OSError):
                    continue
            
            if not recent_files:
                return f"📂 No files found in the last **{days} days**.\n\n*Searched in: Downloads, Desktop, Documents, Pictures*"
            
            # Sort by modification time (newest first)
            recent_files.sort(key=lambda x: x['modified'], reverse=True)
            
            # Group files by type for better organization
            file_types = {}
            for file_info in recent_files:
                ext = file_info['extension']
                if ext not in file_types:
                    file_types[ext] = []
                file_types[ext].append(file_info)
            
            # Format the output with enhanced styling
            result_lines = []
            result_lines.append(f"## 📁 Recent Files")
            result_lines.append(f"**Time Period:** Last {days} days")
            result_lines.append(f"**Total Files Found:** {len(recent_files)}")
            result_lines.append(f"**File Types:** {len(file_types)} different types\n")
            
            # Show top 20 most recent files
            result_lines.append("### 🕒 Most Recent Files")
            for i, file_info in enumerate(recent_files[:20]):
                # Format file size
                size_mb = file_info['size'] / (1024**2)
                if size_mb >= 1:
                    size_str = f"{size_mb:.1f} MB"
                else:
                    size_kb = file_info['size'] / 1024
                    size_str = f"{size_kb:.1f} KB"
                
                # Format modification time
                mod_time = datetime.datetime.fromtimestamp(file_info['modified'])
                time_str = mod_time.strftime("%b %d, %Y at %I:%M %p")
                
                # Get appropriate emoji based on file extension
                ext_emoji = {
                    '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️', '.bmp': '🖼️',
                    '.pdf': '📄', '.doc': '📝', '.docx': '📝', '.txt': '📝', '.rtf': '📝',
                    '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦',
                    '.mp4': '🎥', '.mov': '🎥', '.avi': '🎥', '.mkv': '🎥',
                    '.mp3': '🎵', '.wav': '🎵', '.m4a': '🎵', '.flac': '🎵',
                    '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
                    '.xlsx': '📊', '.csv': '📊', '.pptx': '📊'
                }.get(file_info['extension'], '📄')
                
                result_lines.append(f"**{i+1}.** {ext_emoji} **{file_info['name']}**")
                result_lines.append(f"   📏 Size: `{size_str}`")
                result_lines.append(f"   📅 Modified: `{time_str}`")
                result_lines.append(f"   📂 Location: `{file_info['directory']}`\n")
            
            if len(recent_files) > 20:
                result_lines.append(f"*... and {len(recent_files) - 20} more files*\n")
            
            # Show file type summary
            result_lines.append("### 📊 File Type Summary")
            sorted_types = sorted(file_types.items(), key=lambda x: len(x[1]), reverse=True)
            for ext, files in sorted_types[:10]:  # Show top 10 file types
                ext_display = ext if ext else "No extension"
                result_lines.append(f"• **{ext_display}**: {len(files)} files")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"Error finding recent files: {str(e)}")
            return f"❌ **Error finding recent files:** {str(e)}"

    def _is_destructive_operation(self, path: Path) -> bool:
        """Check if an operation is destructive and needs confirmation."""
        # Consider operations destructive if they affect:
        # - System directories
        # - Large directories (>100 files)
        # - Important user directories
        
        important_dirs = {
            'Documents', 'Desktop', 'Downloads', 'Pictures', 'Music', 'Videos',
            'Applications', 'Library', 'System', 'usr', 'bin', 'etc'
        }
        
        # Check if it's an important directory
        if path.name in important_dirs:
            return True
        
        # Check if it's a large directory
        if path.is_dir():
            try:
                file_count = sum(1 for _ in path.rglob('*'))
                if file_count > 100:
                    return True
            except (PermissionError, OSError):
                pass
        
        # Check if it's a large file (>100MB)
        if path.is_file():
            try:
                size = path.stat().st_size
                if size > 100 * 1024 * 1024:  # 100MB
                    return True
            except (PermissionError, OSError):
                pass
        
        return False
    
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
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

import platform
import psutil
import socket
import datetime
import logging
import subprocess
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SystemInfo:
    def __init__(self):
        self.platform = platform.system().lower()
    
    def get_system_info(self) -> str:
        """Get comprehensive system information."""
        try:
            info = []
            
            # Basic system info
            info.append("=== SYSTEM INFORMATION ===")
            info.append(f"Operating System: {platform.system()} {platform.release()}")
            info.append(f"Platform: {platform.platform()}")
            info.append(f"Architecture: {platform.architecture()[0]}")
            info.append(f"Machine: {platform.machine()}")
            info.append(f"Processor: {platform.processor()}")
            info.append(f"Hostname: {socket.gethostname()}")
            
            # CPU info
            info.append("\n=== CPU INFORMATION ===")
            info.append(f"Physical cores: {psutil.cpu_count(logical=False)}")
            info.append(f"Logical cores: {psutil.cpu_count(logical=True)}")
            info.append(f"Current frequency: {psutil.cpu_freq().current:.2f} MHz")
            info.append(f"CPU usage: {psutil.cpu_percent(interval=1)}%")
            
            # Memory info
            memory = psutil.virtual_memory()
            info.append("\n=== MEMORY INFORMATION ===")
            info.append(f"Total: {self._bytes_to_gb(memory.total):.2f} GB")
            info.append(f"Available: {self._bytes_to_gb(memory.available):.2f} GB")
            info.append(f"Used: {self._bytes_to_gb(memory.used):.2f} GB")
            info.append(f"Usage: {memory.percent}%")
            
            # Disk info
            info.append("\n=== DISK INFORMATION ===")
            disk_usage = psutil.disk_usage('/')
            info.append(f"Total: {self._bytes_to_gb(disk_usage.total):.2f} GB")
            info.append(f"Used: {self._bytes_to_gb(disk_usage.used):.2f} GB")
            info.append(f"Free: {self._bytes_to_gb(disk_usage.free):.2f} GB")
            info.append(f"Usage: {(disk_usage.used / disk_usage.total) * 100:.1f}%")
            
            # Network info
            info.append("\n=== NETWORK INFORMATION ===")
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                info.append(f"Local IP: {local_ip}")
            except:
                info.append("Local IP: Unable to determine")
            
            # Boot time
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            info.append(f"\nBoot time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return f"Error getting system information: {str(e)}"
    
    def get_current_time(self) -> str:
        """Get current date and time."""
        try:
            now = datetime.datetime.now()
            
            info = []
            info.append(f"Current time: {now.strftime('%H:%M:%S')}")
            info.append(f"Current date: {now.strftime('%Y-%m-%d')}")
            info.append(f"Day of week: {now.strftime('%A')}")
            info.append(f"Time zone: {now.astimezone().tzname()}")
            
            # Uptime
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = now - boot_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            info.append(f"System uptime: {days} days, {hours} hours, {minutes} minutes")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error getting time: {str(e)}")
            return f"Error getting time: {str(e)}"
    
    def get_weather(self) -> str:
        """Get weather information (placeholder - would need weather API)."""
        try:
            # This is a placeholder. In a real implementation, you would:
            # 1. Get user's location (with permission)
            # 2. Call a weather API (OpenWeatherMap, etc.)
            # 3. Format and return the weather data
            
            return """Weather information requires API setup.
            
To get weather data, you would need to:
1. Sign up for a weather API (like OpenWeatherMap)
2. Get an API key
3. Configure location settings
4. Enable location access

For now, try asking me to open a weather website:
"browse weather.com" or "google weather [your city]" """
            
        except Exception as e:
            logger.error(f"Error getting weather: {str(e)}")
            return f"Error getting weather: {str(e)}"
    
    def get_battery_info(self) -> str:
        """Get battery information if available."""
        try:
            battery = psutil.sensors_battery()
            
            if battery is None:
                return "No battery information available (desktop computer or unsupported)"
            
            info = []
            info.append(f"Battery percentage: {battery.percent}%")
            
            if battery.power_plugged:
                info.append("Power source: AC adapter (plugged in)")
            else:
                info.append("Power source: Battery")
                
                if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                    hours = battery.secsleft // 3600
                    minutes = (battery.secsleft % 3600) // 60
                    info.append(f"Time remaining: {hours}h {minutes}m")
                else:
                    info.append("Time remaining: Unknown")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error getting battery info: {str(e)}")
            return f"Error getting battery info: {str(e)}"
    
    def get_running_processes(self, limit: int = 10) -> str:
        """Get list of running processes."""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            info = [f"Top {limit} processes by CPU usage:\n"]
            
            for i, proc in enumerate(processes[:limit]):
                cpu = proc['cpu_percent'] or 0
                memory = proc['memory_percent'] or 0
                info.append(f"{i+1:2}. {proc['name']:<20} PID:{proc['pid']:<8} CPU:{cpu:5.1f}% MEM:{memory:5.1f}%")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error getting processes: {str(e)}")
            return f"Error getting running processes: {str(e)}"
    
    def get_network_interfaces(self) -> str:
        """Get network interface information."""
        try:
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            info = ["Network Interfaces:\n"]
            
            for interface_name, addresses in interfaces.items():
                info.append(f"Interface: {interface_name}")
                
                # Get stats if available
                if interface_name in stats:
                    stat = stats[interface_name]
                    info.append(f"  Status: {'Up' if stat.isup else 'Down'}")
                    info.append(f"  Speed: {stat.speed} Mbps")
                
                # Get addresses
                for addr in addresses:
                    if addr.family == socket.AF_INET:  # IPv4
                        info.append(f"  IPv4: {addr.address}")
                        if addr.netmask:
                            info.append(f"  Netmask: {addr.netmask}")
                    elif addr.family == socket.AF_INET6:  # IPv6
                        info.append(f"  IPv6: {addr.address}")
                
                info.append("")  # Empty line between interfaces
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error getting network interfaces: {str(e)}")
            return f"Error getting network interfaces: {str(e)}"
    
    def _bytes_to_gb(self, bytes_value: int) -> float:
        """Convert bytes to gigabytes."""
        return bytes_value / (1024 ** 3)
    
    def _get_cpu_temperature(self) -> str:
        """Get CPU temperature if available."""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current:
                                return f"CPU Temperature: {entry.current}°C"
            
            return "CPU temperature not available"
            
        except Exception as e:
            return f"Error getting temperature: {str(e)}"
    
    def get_largest_applications(self, limit: int = 10) -> str:
        """Find the largest applications by disk usage."""
        try:
            apps_info = []
            
            # Common application directories on macOS
            app_dirs = [
                "/Applications",
                "~/Applications",
                "/System/Applications",
                "/System/Library/CoreServices"
            ]
            
            # If Windows, check Program Files
            if self.platform == "windows":
                app_dirs = [
                    "C:\\Program Files",
                    "C:\\Program Files (x86)"
                ]
            # If Linux, check common app directories
            elif self.platform == "linux":
                app_dirs = [
                    "/usr/bin",
                    "/usr/local/bin",
                    "/opt",
                    "~/.local/share/applications"
                ]
            
            for app_dir in app_dirs:
                expanded_dir = os.path.expanduser(app_dir)
                if os.path.exists(expanded_dir):
                    try:
                        for item in os.listdir(expanded_dir):
                            item_path = os.path.join(expanded_dir, item)
                            if os.path.isdir(item_path):
                                size = self._get_directory_size(item_path)
                                if size > 0:  # Only include non-empty directories
                                    apps_info.append({
                                        'name': item,
                                        'path': item_path,
                                        'size': size,
                                        'size_gb': size / (1024**3)
                                    })
                    except (PermissionError, OSError) as e:
                        logger.warning(f"Could not access {expanded_dir}: {str(e)}")
                        continue
            
            # Sort by size (largest first)
            apps_info.sort(key=lambda x: x['size'], reverse=True)
            
            if not apps_info:
                return "No application directories found or accessible."
            
            # Format the output
            info = [f"🔍 Top {limit} largest applications by disk usage:\n"]
            info.append(f"{'Rank':<4} {'Application':<30} {'Size':<10} {'Path'}")
            info.append("-" * 80)
            
            for i, app in enumerate(apps_info[:limit]):
                size_str = f"{app['size_gb']:.2f} GB" if app['size_gb'] >= 1 else f"{app['size']/(1024**2):.1f} MB"
                info.append(f"{i+1:<4} {app['name'][:29]:<30} {size_str:<10} {app['path']}")
            
            # Add total size summary
            total_size = sum(app['size'] for app in apps_info[:limit])
            total_gb = total_size / (1024**3)
            info.append("-" * 80)
            info.append(f"Total size of top {limit} apps: {total_gb:.2f} GB")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error analyzing application sizes: {str(e)}")
            return f"❌ Error analyzing application sizes: {str(e)}"
    
    def _get_directory_size(self, directory_path: str) -> int:
        """Calculate the total size of a directory and its contents."""
        total_size = 0
        try:
            # Use os.walk to recursively get all files
            for dirpath, dirnames, filenames in os.walk(directory_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        if os.path.isfile(filepath) and not os.path.islink(filepath):
                            total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        # Skip files that can't be accessed
                        continue
        except (PermissionError, OSError):
            # If we can't access the directory, return 0
            return 0
        
        return total_size
    
    def get_disk_usage_analysis(self) -> str:
        """Get detailed disk usage analysis."""
        try:
            info = []
            info.append("💾 DISK USAGE ANALYSIS")
            info.append("=" * 50)
            
            # Get overall disk usage
            disk_usage = psutil.disk_usage('/')
            info.append(f"Total disk space: {self._bytes_to_gb(disk_usage.total):.2f} GB")
            info.append(f"Used disk space: {self._bytes_to_gb(disk_usage.used):.2f} GB ({(disk_usage.used/disk_usage.total)*100:.1f}%)")
            info.append(f"Free disk space: {self._bytes_to_gb(disk_usage.free):.2f} GB")
            info.append("")
            
            # Analyze common directories
            directories_to_check = []
            
            if self.platform == "darwin":  # macOS
                directories_to_check = [
                    ("Applications", "/Applications"),
                    ("User Home", os.path.expanduser("~")),
                    ("Downloads", os.path.expanduser("~/Downloads")),
                    ("Documents", os.path.expanduser("~/Documents")),
                    ("Desktop", os.path.expanduser("~/Desktop")),
                    ("Movies", os.path.expanduser("~/Movies")),
                    ("Pictures", os.path.expanduser("~/Pictures")),
                    ("Music", os.path.expanduser("~/Music"))
                ]
            elif self.platform == "windows":
                directories_to_check = [
                    ("Program Files", "C:\\Program Files"),
                    ("Program Files (x86)", "C:\\Program Files (x86)"),
                    ("Users", "C:\\Users"),
                    ("Windows", "C:\\Windows")
                ]
            else:  # Linux
                directories_to_check = [
                    ("Home", os.path.expanduser("~")),
                    ("Applications", "/usr"),
                    ("Optional Software", "/opt"),
                    ("Variable Data", "/var")
                ]
            
            dir_sizes = []
            for name, path in directories_to_check:
                if os.path.exists(path):
                    try:
                        size = self._get_directory_size(path)
                        if size > 0:
                            dir_sizes.append((name, path, size))
                    except Exception as e:
                        logger.warning(f"Could not analyze {path}: {str(e)}")
            
            # Sort by size
            dir_sizes.sort(key=lambda x: x[2], reverse=True)
            
            info.append("📁 Largest directories:")
            info.append(f"{'Directory':<20} {'Size':<12} {'Path'}")
            info.append("-" * 60)
            
            for name, path, size in dir_sizes[:8]:
                size_gb = size / (1024**3)
                if size_gb >= 1:
                    size_str = f"{size_gb:.2f} GB"
                else:
                    size_str = f"{size/(1024**2):.1f} MB"
                info.append(f"{name[:19]:<20} {size_str:<12} {path}")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error performing disk analysis: {str(e)}")
            return f"❌ Error performing disk analysis: {str(e)}"
    
    def get_largest_apps(self) -> str:
        """Get the largest applications on the system."""
        try:
            info = []
            info.append("🔍 ANALYZING APPLICATION SIZES")
            info.append("=" * 50)
            
            if self.platform == "darwin":  # macOS
                apps = self._get_macos_apps()
            elif self.platform == "windows":
                apps = self._get_windows_apps()
            else:  # Linux
                apps = self._get_linux_apps()
            
            if not apps:
                return "❌ No applications found or unable to analyze"
            
            # Sort by size
            apps.sort(key=lambda x: x[1], reverse=True)
            
            info.append(f"\n📱 Top {min(15, len(apps))} largest applications:")
            info.append(f"{'Application':<30} {'Size':<12} {'Location'}")
            info.append("-" * 80)
            
            total_size = 0
            for name, size, path in apps[:15]:
                size_gb = size / (1024**3)
                total_size += size
                
                if size_gb >= 1:
                    size_str = f"{size_gb:.2f} GB"
                elif size >= 1024**2:
                    size_str = f"{size/(1024**2):.1f} MB"
                else:
                    size_str = f"{size/1024:.1f} KB"
                
                # Truncate path if too long
                display_path = path if len(path) <= 30 else "..." + path[-27:]
                info.append(f"{name[:29]:<30} {size_str:<12} {display_path}")
            
            total_gb = total_size / (1024**3)
            info.append(f"\n📊 Total analyzed: {total_gb:.2f} GB")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error analyzing app sizes: {str(e)}")
            return f"❌ Error analyzing app sizes: {str(e)}"
    
    def _get_macos_apps(self):
        """Get macOS applications and their sizes."""
        apps = []
        
        # Standard app directories
        app_dirs = [
            "/Applications",
            "/System/Applications",
            os.path.expanduser("~/Applications")
        ]
        
        for app_dir in app_dirs:
            if os.path.exists(app_dir):
                try:
                    for item in os.listdir(app_dir):
                        if item.endswith('.app'):
                            app_path = os.path.join(app_dir, item)
                            try:
                                size = self._get_directory_size(app_path)
                                app_name = item.replace('.app', '')
                                apps.append((app_name, size, app_path))
                            except Exception as e:
                                logger.debug(f"Could not get size for {app_path}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Could not access {app_dir}: {str(e)}")
        
        return apps
    
    def _get_windows_apps(self):
        """Get Windows applications and their sizes."""
        apps = []
        
        # Common program directories
        prog_dirs = [
            "C:\\Program Files",
            "C:\\Program Files (x86)"
        ]
        
        for prog_dir in prog_dirs:
            if os.path.exists(prog_dir):
                try:
                    for item in os.listdir(prog_dir):
                        item_path = os.path.join(prog_dir, item)
                        if os.path.isdir(item_path):
                            try:
                                size = self._get_directory_size(item_path)
                                apps.append((item, size, item_path))
                            except Exception as e:
                                logger.debug(f"Could not get size for {item_path}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Could not access {prog_dir}: {str(e)}")
        
        return apps
    
    def _get_linux_apps(self):
        """Get Linux applications and their sizes."""
        apps = []
        
        # Common app directories
        app_dirs = [
            "/usr/bin",
            "/usr/local/bin",
            "/opt",
            "/snap"
        ]
        
        for app_dir in app_dirs:
            if os.path.exists(app_dir):
                try:
                    for item in os.listdir(app_dir):
                        item_path = os.path.join(app_dir, item)
                        if os.path.isdir(item_path):
                            try:
                                size = self._get_directory_size(item_path)
                                apps.append((item, size, item_path))
                            except Exception as e:
                                logger.debug(f"Could not get size for {item_path}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Could not access {app_dir}: {str(e)}")
        
        return apps

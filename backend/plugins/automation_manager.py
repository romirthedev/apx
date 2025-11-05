"""
Automation Plugin - Handle complex task automation and workflows
"""

import os
import subprocess
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class AutomationManager:
    def __init__(self):
        self.workflows_dir = os.path.expanduser("~/Documents/Apex_Workflows")
        os.makedirs(self.workflows_dir, exist_ok=True)
        self.running_workflows = {}
    
    def create_workflow(self, name: str, steps: List[Dict], description: str = "") -> str:
        """Create a new automation workflow."""
        try:
            workflow = {
                'name': name,
                'description': description,
                'steps': steps,
                'created': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            workflow_file = os.path.join(self.workflows_dir, f"{name}.json")
            with open(workflow_file, 'w') as f:
                json.dump(workflow, f, indent=2)
            
            return f"✅ Workflow '{name}' created with {len(steps)} steps"
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {str(e)}")
            return f"❌ Failed to create workflow: {str(e)}"
    
    def run_workflow(self, name: str, parameters: Dict = None) -> str:
        """Execute a saved workflow."""
        try:
            workflow_file = os.path.join(self.workflows_dir, f"{name}.json")
            if not os.path.exists(workflow_file):
                return f"❌ Workflow '{name}' not found"
            
            with open(workflow_file, 'r') as f:
                workflow = json.load(f)
            
            results = []
            parameters = parameters or {}
            
            for i, step in enumerate(workflow['steps'], 1):
                step_type = step.get('type', '')
                step_data = step.get('data', {})
                
                # Replace parameters in step data
                for key, value in step_data.items():
                    if isinstance(value, str):
                        for param_key, param_value in parameters.items():
                            value = value.replace(f"{{{param_key}}}", str(param_value))
                        step_data[key] = value
                
                result = self._execute_workflow_step(step_type, step_data)
                results.append(f"Step {i}: {result}")
                
                # Add delay if specified
                if 'delay' in step:
                    time.sleep(step['delay'])
            
            execution_summary = f"✅ Workflow '{name}' completed\\n" + "\\n".join(results)
            
            # Log execution
            self._log_workflow_execution(name, parameters, results)
            
            return execution_summary
            
        except Exception as e:
            logger.error(f"Failed to run workflow: {str(e)}")
            return f"❌ Failed to run workflow: {str(e)}"
    
    def _execute_workflow_step(self, step_type: str, step_data: Dict) -> str:
        """Execute a single workflow step."""
        try:
            if step_type == 'open_app':
                app_name = step_data.get('app', '')
                subprocess.run(['open', '-a', app_name], check=True)
                return f"Opened {app_name}"
            
            elif step_type == 'open_url':
                url = step_data.get('url', '')
                subprocess.run(['open', url], check=True)
                return f"Opened {url}"
            
            elif step_type == 'create_file':
                filepath = step_data.get('path', '')
                content = step_data.get('content', '')
                full_path = os.path.expanduser(filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
                return f"Created file {filepath}"
            
            elif step_type == 'run_command':
                command = step_data.get('command', '')
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return f"Executed: {command}"
            
            elif step_type == 'send_email':
                # This would integrate with email manager
                to = step_data.get('to', '')
                subject = step_data.get('subject', '')
                body = step_data.get('body', '')
                return f"Email composed to {to}"
            
            elif step_type == 'wait':
                duration = step_data.get('seconds', 1)
                time.sleep(duration)
                return f"Waited {duration} seconds"
            
            elif step_type == 'notification':
                title = step_data.get('title', 'Apex')
                message = step_data.get('message', '')
                self._send_notification(title, message)
                return f"Sent notification: {message}"
            
            else:
                return f"Unknown step type: {step_type}"
            
        except Exception as e:
            logger.error(f"Step execution failed: {str(e)}")
            return f"Failed: {str(e)}"
    
    def _send_notification(self, title: str, message: str):
        """Send system notification."""
        applescript = f'''
        display notification "{message}" with title "{title}"
        '''
        subprocess.run(['osascript', '-e', applescript])
    
    def _log_workflow_execution(self, name: str, parameters: Dict, results: List[str]):
        """Log workflow execution for debugging."""
        log_entry = {
            'workflow': name,
            'timestamp': datetime.now().isoformat(),
            'parameters': parameters,
            'results': results
        }
        
        log_file = os.path.join(self.workflows_dir, 'execution_log.json')
        
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 100 executions
            if len(logs) > 100:
                logs = logs[-100:]
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log workflow execution: {str(e)}")
    
    def organize_downloads(self) -> str:
        """Organize files in the Downloads folder."""
        try:
            downloads_dir = os.path.expanduser("~/Downloads")
            if not os.path.exists(downloads_dir):
                return "❌ Downloads folder not found"
            
            # Create organization folders
            folders = {
                'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'],
                'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.pages'],
                'Spreadsheets': ['.xls', '.xlsx', '.csv', '.numbers'],
                'Presentations': ['.ppt', '.pptx', '.key'],
                'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
                'Audio': ['.mp3', '.wav', '.aac', '.flac', '.m4a'],
                'Video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'],
                'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c'],
                'Installers': ['.dmg', '.pkg', '.app', '.exe', '.msi']
            }
            
            moved_files = 0
            results = []
            
            # Create folders if they don't exist
            for folder_name in folders.keys():
                folder_path = os.path.join(downloads_dir, folder_name)
                os.makedirs(folder_path, exist_ok=True)
            
            # Move files
            for filename in os.listdir(downloads_dir):
                filepath = os.path.join(downloads_dir, filename)
                
                # Skip if it's a directory
                if os.path.isdir(filepath):
                    continue
                
                # Get file extension
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                
                # Find appropriate folder
                target_folder = None
                for folder_name, extensions in folders.items():
                    if ext in extensions:
                        target_folder = folder_name
                        break
                
                if target_folder:
                    target_path = os.path.join(downloads_dir, target_folder, filename)
                    
                    # Handle filename conflicts
                    counter = 1
                    original_target = target_path
                    while os.path.exists(target_path):
                        name, ext = os.path.splitext(original_target)
                        target_path = f"{name}_{counter}{ext}"
                        counter += 1
                    
                    os.rename(filepath, target_path)
                    moved_files += 1
                    results.append(f"Moved {filename} to {target_folder}/")
            
            if moved_files > 0:
                summary = f"✅ Organized {moved_files} files in Downloads folder:\\n" + "\\n".join(results[:10])
                if len(results) > 10:
                    summary += f"\\n... and {len(results) - 10} more files"
                return summary
            else:
                return "✅ Downloads folder is already organized!"
            
        except Exception as e:
            logger.error(f"Failed to organize downloads: {str(e)}")
            return f"❌ Failed to organize downloads: {str(e)}"
    
    def backup_important_folders(self, destination: str = "~/Desktop/Backup") -> str:
        """Create backup of important folders."""
        try:
            import shutil
            
            backup_dir = os.path.expanduser(destination)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
            
            os.makedirs(backup_path, exist_ok=True)
            
            # Important folders to backup
            important_folders = [
                ("~/Documents", "Documents"),
                ("~/Desktop", "Desktop"),
                ("~/Pictures", "Pictures")
            ]
            
            backed_up = []
            
            for source, name in important_folders:
                source_path = os.path.expanduser(source)
                if os.path.exists(source_path):
                    dest_path = os.path.join(backup_path, name)
                    
                    # Copy folder
                    shutil.copytree(source_path, dest_path, ignore=shutil.ignore_patterns('.*'))
                    
                    # Get folder size
                    total_size = 0
                    for dirpath, dirnames, filenames in os.walk(dest_path):
                        for f in filenames:
                            fp = os.path.join(dirpath, f)
                            total_size += os.path.getsize(fp)
                    
                    size_mb = total_size / (1024 * 1024)
                    backed_up.append(f"{name}: {size_mb:.1f} MB")
            
            if backed_up:
                return f"✅ Backup completed to {backup_path}:\\n" + "\\n".join(backed_up)
            else:
                return "❌ No folders found to backup"
            
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return f"❌ Failed to create backup: {str(e)}"
    
    def clean_temp_files(self) -> str:
        """Clean temporary files and caches."""
        try:
            cleaned_items = []
            total_freed = 0
            
            # Temp directories to clean
            temp_dirs = [
                "~/Library/Caches",
                "~/Library/Logs",
                "/tmp"
            ]
            
            for temp_dir in temp_dirs:
                dir_path = os.path.expanduser(temp_dir)
                if os.path.exists(dir_path):
                    try:
                        # Count files before cleaning
                        file_count = 0
                        size_before = 0
                        
                        for root, dirs, files in os.walk(dir_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    size_before += os.path.getsize(file_path)
                                    file_count += 1
                                except:
                                    pass
                        
                        # Clean using system command (safer)
                        if temp_dir == "/tmp":
                            subprocess.run(['sudo', 'rm', '-rf', '/tmp/*'], shell=True)
                        else:
                            subprocess.run(['find', dir_path, '-type', 'f', '-mtime', '+7', '-delete'])
                        
                        cleaned_items.append(f"{temp_dir}: ~{file_count} files")
                        
                    except Exception as e:
                        logger.error(f"Failed to clean {temp_dir}: {str(e)}")
            
            # Empty trash
            try:
                subprocess.run(['osascript', '-e', 'tell application "Finder" to empty trash'])
                cleaned_items.append("Emptied Trash")
            except:
                pass
            
            if cleaned_items:
                return f"✅ Cleaned temporary files:\\n" + "\\n".join(cleaned_items)
            else:
                return "✅ No temporary files found to clean"
            
        except Exception as e:
            logger.error(f"Failed to clean temp files: {str(e)}")
            return f"❌ Failed to clean temp files: {str(e)}"
    
    def create_daily_report(self) -> str:
        """Create a daily productivity report."""
        try:
            report_content = f"""DAILY PRODUCTIVITY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SYSTEM STATUS:
{self._get_system_summary()}

RECENT ACTIVITIES:
{self._get_recent_activities()}

STORAGE STATUS:
{self._get_storage_status()}

RECOMMENDATIONS:
{self._get_recommendations()}
"""
            
            # Save report
            reports_dir = os.path.expanduser("~/Documents/Daily_Reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(report_content)
            
            # Open the report
            subprocess.run(['open', filepath])
            
            return f"✅ Daily report created: {filename}"
            
        except Exception as e:
            logger.error(f"Failed to create daily report: {str(e)}")
            return f"❌ Failed to create daily report: {str(e)}"
    
    def _get_system_summary(self) -> str:
        """Get system status summary."""
        try:
            # Get basic system info
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True)
            system_info = result.stdout.strip()
            
            # Get uptime
            uptime_result = subprocess.run(['uptime'], capture_output=True, text=True)
            uptime = uptime_result.stdout.strip()
            
            return f"System: {system_info}\\nUptime: {uptime}"
        except:
            return "System information not available"
    
    def _get_recent_activities(self) -> str:
        """Get recent file activities."""
        try:
            # Get recently modified files
            result = subprocess.run([
                'find', os.path.expanduser('~/Documents'), '-type', 'f', 
                '-mtime', '-1', '-exec', 'ls', '-la', '{}', '+'
            ], capture_output=True, text=True)
            
            if result.stdout:
                return "Recent file modifications found"
            else:
                return "No recent file activity"
        except:
            return "Activity information not available"
    
    def _get_storage_status(self) -> str:
        """Get storage status."""
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "Storage information not available"
    
    def _get_recommendations(self) -> str:
        """Get productivity recommendations."""
        recommendations = [
            "Consider organizing your Downloads folder",
            "Review and clean temporary files weekly",
            "Backup important documents regularly",
            "Update your applications for security"
        ]
        return "\\n".join(f"• {rec}" for rec in recommendations)
    
    def list_workflows(self) -> str:
        """List all available workflows."""
        try:
            workflows = []
            for file in os.listdir(self.workflows_dir):
                if file.endswith('.json') and file != 'execution_log.json':
                    workflow_name = file.replace('.json', '')
                    
                    # Get workflow info
                    workflow_file = os.path.join(self.workflows_dir, file)
                    with open(workflow_file, 'r') as f:
                        workflow_data = json.load(f)
                    
                    step_count = len(workflow_data.get('steps', []))
                    description = workflow_data.get('description', 'No description')
                    
                    workflows.append(f"• {workflow_name} ({step_count} steps) - {description}")
            
            if workflows:
                return f"🤖 Available workflows:\\n" + "\\n".join(workflows)
            else:
                return "🤖 No workflows found. Create some with 'create workflow'!"
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {str(e)}")
            return f"❌ Failed to list workflows: {str(e)}"

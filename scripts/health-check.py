#!/usr/bin/env python3
"""
Cluely System Health Monitor
Monitors the health and status of the Cluely AI assistant
"""

import os
import sys
import json
import requests
import subprocess
import psutil
from datetime import datetime

class CluelyHealthMonitor:
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "checks": {}
        }
    
    def check_backend_status(self):
        """Check if the backend server is running"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                self.health_report["checks"]["backend"] = {
                    "status": "healthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "details": "Backend responding normally"
                }
                return True
        except requests.exceptions.ConnectionError:
            self.health_report["checks"]["backend"] = {
                "status": "down",
                "details": "Cannot connect to backend server"
            }
        except requests.exceptions.Timeout:
            self.health_report["checks"]["backend"] = {
                "status": "slow",
                "details": "Backend responding slowly (>5s)"
            }
        except Exception as e:
            self.health_report["checks"]["backend"] = {
                "status": "error",
                "details": f"Backend check failed: {str(e)}"
            }
        return False
    
    def check_permissions(self):
        """Check macOS permissions status"""
        try:
            # Add the backend directory to Python path
            backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
            sys.path.insert(0, backend_dir)
            
            from core.macos_permissions import MacOSPermissionsManager
            
            manager = MacOSPermissionsManager()
            results = manager.check_all_permissions()
            
            self.health_report["checks"]["permissions"] = {
                "status": "healthy" if results["all_granted"] else "warning",
                "details": f"Permissions: {results['permissions']}",
                "missing": results.get("missing", [])
            }
            
            return results["all_granted"]
            
        except Exception as e:
            self.health_report["checks"]["permissions"] = {
                "status": "error",
                "details": f"Permission check failed: {str(e)}"
            }
            return False
    
    def check_python_environment(self):
        """Check Python virtual environment and dependencies"""
        try:
            venv_path = os.path.join(os.path.dirname(__file__), '..', '.venv')
            
            if not os.path.exists(venv_path):
                self.health_report["checks"]["python_env"] = {
                    "status": "error",
                    "details": "Virtual environment not found"
                }
                return False
            
            # Check if required packages are installed
            python_exe = os.path.join(venv_path, 'bin', 'python')
            result = subprocess.run([python_exe, '-c', 
                'import flask, requests, psutil; print("OK")'], 
                capture_output=True, text=True)
            
            if result.returncode == 0:
                self.health_report["checks"]["python_env"] = {
                    "status": "healthy",
                    "details": "Virtual environment and dependencies OK"
                }
                return True
            else:
                self.health_report["checks"]["python_env"] = {
                    "status": "error",
                    "details": f"Missing dependencies: {result.stderr}"
                }
                return False
                
        except Exception as e:
            self.health_report["checks"]["python_env"] = {
                "status": "error",
                "details": f"Environment check failed: {str(e)}"
            }
            return False
    
    def check_system_resources(self):
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check for resource issues
            status = "healthy"
            warnings = []
            
            if cpu_percent > 80:
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 85:
                status = "warning"
                warnings.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                status = "warning"
                warnings.append(f"Low disk space: {disk.percent}% used")
            
            self.health_report["checks"]["system_resources"] = {
                "status": status,
                "details": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "warnings": warnings
                }
            }
            
            return status == "healthy"
            
        except Exception as e:
            self.health_report["checks"]["system_resources"] = {
                "status": "error",
                "details": f"Resource check failed: {str(e)}"
            }
            return False
    
    def check_log_files(self):
        """Check log files for errors"""
        try:
            backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
            log_file = os.path.join(backend_dir, 'cluely.log')
            
            if not os.path.exists(log_file):
                self.health_report["checks"]["logs"] = {
                    "status": "warning",
                    "details": "Log file not found (may not have run yet)"
                }
                return True
            
            # Check for recent errors in logs
            with open(log_file, 'r') as f:
                recent_lines = f.readlines()[-100:]  # Last 100 lines
            
            error_count = sum(1 for line in recent_lines if 'ERROR' in line)
            warning_count = sum(1 for line in recent_lines if 'WARNING' in line)
            
            if error_count > 10:
                status = "error"
                details = f"Many recent errors: {error_count} errors, {warning_count} warnings"
            elif error_count > 5 or warning_count > 20:
                status = "warning"
                details = f"Some issues found: {error_count} errors, {warning_count} warnings"
            else:
                status = "healthy"
                details = f"Logs look good: {error_count} errors, {warning_count} warnings"
            
            self.health_report["checks"]["logs"] = {
                "status": status,
                "details": details
            }
            
            return status != "error"
            
        except Exception as e:
            self.health_report["checks"]["logs"] = {
                "status": "error",
                "details": f"Log check failed: {str(e)}"
            }
            return False
    
    def generate_overall_status(self):
        """Generate overall health status"""
        statuses = [check["status"] for check in self.health_report["checks"].values()]
        
        if "error" in statuses:
            self.health_report["overall_status"] = "error"
        elif "warning" in statuses:
            self.health_report["overall_status"] = "warning"
        else:
            self.health_report["overall_status"] = "healthy"
    
    def run_health_check(self):
        """Run all health checks"""
        print("🏥 Cluely Health Check")
        print("=" * 22)
        
        checks = [
            ("Backend Server", self.check_backend_status),
            ("Permissions", self.check_permissions),
            ("Python Environment", self.check_python_environment),
            ("System Resources", self.check_system_resources),
            ("Log Files", self.check_log_files)
        ]
        
        for check_name, check_func in checks:
            print(f"\n🔍 Checking {check_name}...")
            try:
                check_func()
                status = self.health_report["checks"].get(check_name.lower().replace(" ", "_"), {}).get("status", "unknown")
                emoji = {"healthy": "✅", "warning": "⚠️", "error": "❌", "unknown": "❓"}.get(status, "❓")
                print(f"{emoji} {check_name}: {status}")
            except Exception as e:
                print(f"❌ {check_name}: error ({str(e)})")
        
        self.generate_overall_status()
        
        print(f"\n📊 Overall Status: {self.health_report['overall_status'].upper()}")
        
        # Print detailed results
        print("\n📋 Detailed Results:")
        print("-" * 20)
        for check_name, check_data in self.health_report["checks"].items():
            print(f"\n{check_name.replace('_', ' ').title()}:")
            print(f"  Status: {check_data['status']}")
            print(f"  Details: {check_data['details']}")
            if 'missing' in check_data and check_data['missing']:
                print(f"  Missing: {', '.join(check_data['missing'])}")
        
        return self.health_report

def main():
    monitor = CluelyHealthMonitor()
    health_report = monitor.run_health_check()
    
    # Save report
    report_file = os.path.join(os.path.dirname(__file__), '..', 'backend', 'health_report.json')
    with open(report_file, 'w') as f:
        json.dump(health_report, f, indent=2)
    
    print(f"\n💾 Health report saved to: {report_file}")
    
    # Exit with appropriate code
    if health_report["overall_status"] == "error":
        sys.exit(1)
    elif health_report["overall_status"] == "warning":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()

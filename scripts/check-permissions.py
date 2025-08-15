#!/usr/bin/env python3
"""
Cluely Permissions Checker
Run this script to check and guide setup of required macOS permissions
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from core.macos_permissions import MacOSPermissionsManager

def main():
    print("🔐 Cluely Permissions Checker")
    print("=" * 30)
    
    manager = MacOSPermissionsManager()
    results = manager.check_all_permissions()
    
    print(f"\n📊 Permission Status:")
    print("-" * 20)
    
    for permission, status in results['permissions'].items():
        status_emoji = "✅" if status else "❌"
        permission_name = permission.replace('_', ' ').title()
        print(f"{status_emoji} {permission_name}: {'Granted' if status else 'Not Granted'}")
    
    if not results['all_granted']:
        print(f"\n⚠️  Missing Permissions: {', '.join(results['missing'])}")
        print("\n📋 Setup Instructions:")
        print("-" * 20)
        
        for i, instruction in enumerate(results['instructions'], 1):
            print(f"{i}. {instruction}")
        
        print("\n💡 Tips:")
        print("- You may need to restart Cluely after granting permissions")
        print("- Some permissions require the app to be running when you grant them")
        print("- If you see 'Operation not permitted', permissions are likely missing")
        
        return False
    else:
        print("\n🎉 All permissions granted! Cluely is ready for full functionality.")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

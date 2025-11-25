"""Dependency validation utility"""

import subprocess
import sys


def validate_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'selenium',
        'webdriver-manager',
        'beautifulsoup4',
        'lxml',
        'pandas',
        'openpyxl',
        'fuzzywuzzy',
        'python-Levenshtein',
        'colorama'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        
        print("\n📦 Installing missing packages...")
        for pkg in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
                print(f"   ✅ Installed {pkg}")
            except:
                print(f"   ❌ Failed to install {pkg}")
                return False
    
    print("✅ All dependencies validated")
    return True
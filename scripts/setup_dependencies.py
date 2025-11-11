#!/usr/bin/env python3
"""
Setup script to install required dependencies for the cluster system.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required Python packages."""
    requirements_file = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        print("❌ requirements.txt not found")
        return False
    
    try:
        print("Installing required dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
        print("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def verify_installation():
    """Verify that all required modules can be imported."""
    required_modules = ['docker', 'requests', 'schedule']
    
    print("Verifying installation...")
    for module in required_modules:
        try:
            __import__(module)
            print(f"{module} - OK")
        except ImportError:
            print(f"{module} - MISSING")
            return False
    
    return True

if __name__ == "__main__":
    print("Cluster System Dependency Setup")
    print("=" * 40)
    
    if install_requirements() and verify_installation():
        print("\nSetup completed successfully!")
        print("You can now run the advanced auto-scaler with:")
        print("python scripts/start_advanced_autoscaler.py")
    else:
        print("\nSetup failed. Please check the error messages above.")
        sys.exit(1)
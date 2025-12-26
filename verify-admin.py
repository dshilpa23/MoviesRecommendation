#!/usr/bin/env python3
"""
Admin Dashboard Verification Script
Checks that all components are properly set up and ready to run.
"""

import os
import sys
import json
from pathlib import Path

# Color output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
CHECK = '✓'
CROSS = '✗'
WARN = '⚠'

def print_check(text):
    print(f"{GREEN}{CHECK}{RESET} {text}")

def print_error(text):
    print(f"{RED}{CROSS}{RESET} {text}")

def print_warn(text):
    print(f"{YELLOW}{WARN}{RESET} {text}")

def verify_admin_dashboard():
    """Verify all admin dashboard components."""
    
    print("\n🔍 Admin Dashboard Verification")
    print("=" * 50)
    
    base_dir = Path(__file__).parent.resolve()
    admin_dir = base_dir / "admin"
    
    all_good = True
    
    # Check directory structure
    print("\n📁 Directory Structure:")
    required_dirs = [
        admin_dir,
        admin_dir / "utils",
        admin_dir / "templates",
        admin_dir / "static",
    ]
    
    for dir_path in required_dirs:
        if dir_path.exists():
            print_check(f"{dir_path.relative_to(base_dir)}/")
        else:
            print_error(f"{dir_path.relative_to(base_dir)}/ (MISSING)")
            all_good = False
    
    # Check Python files
    print("\n🐍 Python Files:")
    required_python_files = [
        admin_dir / "app.py",
        admin_dir / "requirements.txt",
        admin_dir / "utils" / "__init__.py",
        admin_dir / "utils" / "excel_handler.py",
        admin_dir / "utils" / "validation.py",
        admin_dir / "utils" / "pipeline_runner.py",
    ]
    
    for file_path in required_python_files:
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print_check(f"{file_path.relative_to(base_dir)} ({size_kb:.1f} KB)")
        else:
            print_error(f"{file_path.relative_to(base_dir)} (MISSING)")
            all_good = False
    
    # Check frontend files
    print("\n🎨 Frontend Files:")
    required_frontend_files = [
        admin_dir / "templates" / "admin.html",
        admin_dir / "static" / "admin.css",
        admin_dir / "static" / "admin.js",
    ]
    
    for file_path in required_frontend_files:
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print_check(f"{file_path.relative_to(base_dir)} ({size_kb:.1f} KB)")
        else:
            print_error(f"{file_path.relative_to(base_dir)} (MISSING)")
            all_good = False
    
    # Check launcher scripts
    print("\n🚀 Launcher Scripts:")
    launcher_scripts = [
        base_dir / "start-admin.sh",
        base_dir / "start-admin.bat",
    ]
    
    for file_path in launcher_scripts:
        if file_path.exists():
            is_executable = os.access(file_path, os.X_OK)
            status = "executable" if is_executable else "not executable"
            if is_executable:
                print_check(f"{file_path.relative_to(base_dir)} ({status})")
            else:
                print_warn(f"{file_path.relative_to(base_dir)} ({status})")
        else:
            print_error(f"{file_path.relative_to(base_dir)} (MISSING)")
            all_good = False
    
    # Check documentation
    print("\n📖 Documentation:")
    required_docs = [
        base_dir / "ADMIN_GUIDE.md",
        base_dir / "ADMIN_QUICK_START.md",
        base_dir / "ADMIN_IMPLEMENTATION.md",
    ]
    
    for file_path in required_docs:
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print_check(f"{file_path.relative_to(base_dir)} ({size_kb:.1f} KB)")
        else:
            print_error(f"{file_path.relative_to(base_dir)} (MISSING)")
            all_good = False
    
    # Check data files
    print("\n📊 Data Files:")
    data_dir = base_dir / "data"
    excel_file = base_dir / "movies_master.xlsx"
    
    if excel_file.exists():
        size_mb = excel_file.stat().st_size / (1024 * 1024)
        print_check(f"{excel_file.relative_to(base_dir)} ({size_mb:.2f} MB)")
    else:
        print_warn(f"{excel_file.relative_to(base_dir)} (Not required for setup, but needed for runtime)")
    
    if data_dir.exists():
        json_files = list(data_dir.glob("*.json"))
        if json_files:
            print_check(f"data/ directory with {len(json_files)} JSON files")
        else:
            print_warn(f"data/ directory exists but is empty (will be populated by pipeline)")
    else:
        print_warn(f"data/ directory (Will be created when generating JSON)")
    
    # Check Python syntax
    print("\n✅ Python Syntax Check:")
    import py_compile
    
    # Exclude requirements.txt (not a Python file)
    python_files_to_check = [f for f in required_python_files if f.suffix == '.py']
    syntax_ok = True
    
    for file_path in python_files_to_check:
        try:
            py_compile.compile(str(file_path), doraise=True)
            print_check(f"{file_path.name} - Valid syntax")
        except py_compile.PyCompileError as e:
            print_error(f"{file_path.name} - Syntax error: {e}")
            syntax_ok = False
            all_good = False
    
    if syntax_ok:
        print_check("All Python files have valid syntax")
    
    # Check Flask import
    print("\n📦 Dependencies Check:")
    try:
        import flask
        print_check(f"Flask {flask.__version__} available")
    except ImportError:
        print_warn("Flask not installed (will be installed by launcher script)")
    
    try:
        import pandas
        print_check(f"pandas {pandas.__version__} available")
    except ImportError:
        print_warn("pandas not installed (will be installed by launcher script)")
    
    # Summary
    print("\n" + "=" * 50)
    if all_good and syntax_ok:
        print(f"{GREEN}✓ All checks passed!{RESET}")
        print("\n🚀 Ready to run admin dashboard:")
        if os.name == 'nt':
            print("   > start-admin.bat")
        else:
            print("   > ./start-admin.sh")
        print("\n📍 Dashboard will be accessible at: http://127.0.0.1:5000")
        return 0
    else:
        print(f"{RED}✗ Some checks failed. Please review above.{RESET}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(verify_admin_dashboard())
    except Exception as e:
        print(f"{RED}Verification error: {e}{RESET}")
        sys.exit(1)

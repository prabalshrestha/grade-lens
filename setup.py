#!/usr/bin/env python3
"""
Setup script for the CS361 HW5 Grading System
"""

import os
import subprocess
import sys


def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing requirements: {e}")
        return False


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = ".env"
    if not os.path.exists(env_file):
        print("Creating .env file...")
        with open(env_file, "w") as f:
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            f.write("OPENAI_MODEL=gpt-4o-mini\n")
        print("✓ .env file created")
        print("⚠ Please edit .env file and add your OpenAI API key")
        return False
    else:
        print("✓ .env file already exists")
        return True


def check_api_key():
    """Check if API key is set"""
    try:
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠ OpenAI API key not set")
            return False
        return True
    except ImportError:
        print("⚠ python-dotenv not installed yet")
        return False


def main():
    """Main setup function"""
    print("=" * 50)
    print("CS361 HW5 GRADING SYSTEM SETUP")
    print("=" * 50)

    # Install requirements
    if not install_requirements():
        print("Setup failed at requirements installation")
        return 1

    # Create .env file
    env_created = create_env_file()

    # Check API key
    api_key_set = check_api_key()

    print("\n" + "=" * 50)
    print("SETUP SUMMARY")
    print("=" * 50)

    if env_created and api_key_set:
        print("✓ Setup complete! You can now run:")
        print("  python test_setup.py  # Test the setup")
        print("  python main.py         # Run the grading workflow")
    else:
        print("⚠ Setup partially complete. Please:")
        if not env_created:
            print("  1. Edit .env file and add your OpenAI API key")
        if not api_key_set:
            print("  2. Set your OpenAI API key in the .env file")
        print("  3. Run: python test_setup.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())

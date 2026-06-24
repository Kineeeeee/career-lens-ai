"""Setup script for Career Lens AI with RAG and Streamlit.

This script helps set up the project and installs all dependencies.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description=""):
    """Run a shell command."""
    if description:
        print(f"\n📦 {description}")
    print(f"  Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  ✅ Done")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"  ❌ Command not found: {cmd[0]}")
        return False


def main():
    """Main setup function."""
    print("🎯 Career Lens AI - Setup Script")
    print("=" * 50)

    # Check Python version
    print(f"\n📌 Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)

    # Create necessary directories
    print("\n📁 Creating directories...")
    dirs = [
        "data/analyses",
        "data/chroma_db",
        "data/results",
        "prompts",
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path}")

    # Install dependencies
    print("\n📥 Installing dependencies...")
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                        "Upgrading pip"):
        print("⚠️  Failed to upgrade pip, continuing anyway")

    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                        "Installing required packages"):
        print("❌ Failed to install requirements")
        sys.exit(1)

    # Check environment file
    print("\n🔑 Checking environment configuration...")
    if Path(".env").exists():
        print("  ✅ .env file exists")
    else:
        if Path(".env.example").exists():
            print("  ⚠️  .env not found, copying from .env.example")
            import shutil
            shutil.copy(".env.example", ".env")
            print("  📝 Please edit .env and add your API keys:")
            print("     - TAVILY_API_KEY")
            print("     - GROQ_API_KEY")
        else:
            print("  ⚠️  .env.example not found")

    # Print summary
    print("\n" + "=" * 50)
    print("✅ Setup Complete!")
    print("\n📚 Next Steps:")
    print("  1. Edit .env with your API keys")
    print("  2. Run the CLI: python main.py")
    print("  3. Or run the Streamlit UI: streamlit run app_streamlit.py")
    print("\n📖 Documentation:")
    print("  - Basic usage: python main.py --help")
    print("  - Web UI: streamlit run app_streamlit.py")
    print("  - See docs/ folder for detailed guides")
    print("=" * 50)


if __name__ == "__main__":
    main()

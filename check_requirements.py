import pkg_resources
import subprocess
import sys

def check_and_install_packages():
    # Define required packages
    required = {'python-dotenv', 'pyTelegramBotAPI'}
    
    # Get installed packages
    installed = {pkg.key for pkg in pkg_resources.working_set}
    
    # Find missing packages
    missing = required - installed
    
    if missing:
        print(f"Missing packages: {missing}")
        print("Installing missing packages...")
        
        try:
            # Install missing packages
            for package in missing:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print("All packages installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
            return False
    else:
        print("All required packages are installed!")
    
    return True

if __name__ == "__main__":
    check_and_install_packages() 
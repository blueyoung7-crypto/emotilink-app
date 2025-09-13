#!/usr/bin/env python3
"""
EmotiBit CardioGuard Setup Script
Automatically installs dependencies and configures the system
"""

import os
import sys
import subprocess
import platform

def install_requirements():
    """Install required Python packages"""
    print("📦 Installing required packages...")
    
    packages = [
        'numpy',
        'scipy', 
        'websockets',
        'asyncio'
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def create_batch_files():
    """Create convenient batch files for Windows"""
    if platform.system() == 'Windows':
        # Create start_bridge.bat
        with open('start_bridge.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('echo Starting EmotiBit UDP Bridge...\n')
            f.write('python emotibit_bridge.py\n')
            f.write('pause\n')
        
        # Create start_cardioguard.bat  
        with open('start_cardioguard.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('echo Opening CardioGuard AI...\n')
            f.write('start cardioguard_realtime.html\n')
        
        print("✅ Created Windows batch files")
    
    # Create shell scripts for Linux/Mac
    else:
        # Create start_bridge.sh
        with open('start_bridge.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('echo "Starting EmotiBit UDP Bridge..."\n')
            f.write('python3 emotibit_bridge.py\n')
        
        os.chmod('start_bridge.sh', 0o755)
        
        # Create start_cardioguard.sh
        with open('start_cardioguard.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('echo "Opening CardioGuard AI..."\n')
            f.write('open cardioguard_realtime.html || xdg-open cardioguard_realtime.html\n')
        
        os.chmod('start_cardioguard.sh', 0o755)
        
        print("✅ Created shell scripts")

def create_emotibit_config():
    """Create EmotiBit configuration instructions"""
    config_text = """
# EmotiBit Configuration for CardioGuard AI

## Step 1: Configure EmotiBit UDP Output
1. Connect to your EmotiBit via serial terminal (115200 baud)
2. Press 'C' during startup to enter configuration mode
3. Set the following parameters:

UDP_ENABLE=1
UDP_HOST=127.0.0.1
UDP_PORT=12345
UDP_DATA_TYPES=PPG_INFRARED,PPG_RED,EDA,TEMPERATURE_0,ACCELEROMETER_X,ACCELEROMETER_Y,ACCELEROMETER_Z

## Step 2: Save Configuration
1. Type 'S' to save settings
2. Type 'R' to restart EmotiBit
3. Your EmotiBit should now send data to localhost:12345

## Step 3: Verify Data Stream
1. Run: python emotibit_bridge.py
2. You should see data being received in the console
3. Open cardioguard_realtime.html to see live data

## Troubleshooting
- Make sure EmotiBit and computer are on same network
- Check firewall settings allow UDP port 12345
- Verify EmotiBit is properly paired and connected
- Check console output for error messages
"""
    
    with open('EmotiBit_Config.txt', 'w') as f:
        f.write(config_text)
    
    print("✅ Created EmotiBit configuration guide")

def create_readme():
    """Create comprehensive README file"""
    readme_text = """# CardioGuard AI - EmotiBit Integration

## 🚀 Quick Start

### 1. Install Dependencies
```bash
python setup.py
```

### 2. Configure EmotiBit
- Follow instructions in `EmotiBit_Config.txt`
- Make sure EmotiBit sends UDP data to localhost:12345

### 3. Start the System
```bash
# Terminal 1: Start the bridge server
python emotibit_bridge.py

# Terminal 2: Open the web app
# Windows: start_cardioguard.bat
# Mac/Linux: ./start_cardioguard.sh
```

## 📁 File Structure
- `emotibit_bridge.py` - UDP to WebSocket bridge server
- `cardioguard_realtime.html` - Web interface with live data
- `setup.py` - This setup script
- `EmotiBit_Config.txt` - EmotiBit configuration guide

## 🔧 Technical Details

### Data Flow
```
EmotiBit → UDP (port 12345) → Python Bridge → WebSocket → Web App
```

### Processed Metrics
- Heart Rate (from PPG)
- HRV RMSSD (from PPG)  
- EDA Tonic Level
- Activity Level (from accelerometer)
- Temperature

### Real-time Features
- Live vital signs display
- AI-powered health insights
- Data export to CSV
- Connection status monitoring
- Automatic reconnection

## 🐛 Troubleshooting

### EmotiBit Not Connecting
1. Check EmotiBit configuration (see EmotiBit_Config.txt)
2. Verify UDP port 12345 is not blocked
3. Ensure EmotiBit and computer are on same network

### Bridge Server Issues
1. Check Python dependencies are installed
2. Verify port 8765 is available for WebSocket
3. Look at console output for error messages

### Web App Not Updating
1. Make sure bridge server is running
2. Check browser console (F12) for errors
3. Try refreshing the page
4. Verify WebSocket connection status

## 📊 Data Export
Click "Export Live Data" to download CSV file with:
- Timestamps
- Heart rate values
- HRV measurements  
- EDA readings
- Activity levels
- Temperature data

## 🔒 Privacy & Security
- All data processing happens locally
- No data sent to external servers
- UDP and WebSocket connections are local only
- Export files saved to your local machine

## 💡 Tips
- Ensure good EmotiBit skin contact for best signal quality
- Let the system collect data for 2-3 minutes before analysis
- Use chest placement for optimal ECG/PPG signal
- Check AI insights for real-time health recommendations

## 🆘 Support
For issues:
1. Check console output for error messages
2. Verify EmotiBit configuration
3. Test with demo mode (auto-starts after 10 seconds)
4. Review setup steps in EmotiBit_Config.txt
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_text)
    
    print("✅ Created comprehensive README")

def main():
    """Main setup function"""
    print("🔧 CardioGuard AI - EmotiBit Setup")
    print("=" * 50)
    
    # Install dependencies
    if not install_requirements():
        print("❌ Failed to install dependencies. Please install manually:")
        print("pip install numpy scipy websockets")
        return
    
    # Create helper files
    create_batch_files()
    create_emotibit_config()
    create_readme()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Configure your EmotiBit (see EmotiBit_Config.txt)")
    print("2. Run: python emotibit_bridge.py")
    print("3. Open: cardioguard_realtime.html")
    print("\n🎯 Your EmotiBit should send UDP data to localhost:12345")
    print("🌐 The web app will connect via WebSocket on port 8765")
    print("\n📖 See README.md for detailed instructions")

if __name__ == "__main__":
    main()
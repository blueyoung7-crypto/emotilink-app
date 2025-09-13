#!/usr/bin/env python3
"""
EmotiBit UDP Bridge Server - Improved Data Parser
Enhanced parsing to extract actual sensor values from EmotiBit packets
"""

import socket
import json
import threading
import time
import numpy as np
from collections import deque
import http.server
import socketserver
import re

class EmotiBitBridge:
    def __init__(self, udp_port=3000, http_port=8080):
        self.udp_port = udp_port
        self.http_port = http_port
        self.running = True
        
        # Data storage for real sensor data
        self.sensor_data = {
            'PPG_INFRARED': deque(maxlen=200),
            'PPG_RED': deque(maxlen=200),
            'PPG_GREEN': deque(maxlen=200),
            'EDA': deque(maxlen=200),
            'TEMPERATURE_0': deque(maxlen=200),
            'ACCELEROMETER_X': deque(maxlen=200),
            'ACCELEROMETER_Y': deque(maxlen=200),
            'ACCELEROMETER_Z': deque(maxlen=200),
            'GYROSCOPE_X': deque(maxlen=200),
            'GYROSCOPE_Y': deque(maxlen=200),
            'GYROSCOPE_Z': deque(maxlen=200),
        }
        
        # Current processed values - only from real data
        self.current_data = {
            'heart_rate': None,
            'hrv_rmssd': None,
            'eda_tonic': None,
            'temperature': None,
            'activity_level': None,
            'timestamp': time.time(),
            'packets_received': 0,
            'last_update': 'No sensor data received',
            'connection_status': 'disconnected',
            'raw_data_samples': 0
        }
        
        # Stats
        self.packets_received = 0
        self.last_packet_time = 0
        self.successful_parses = 0

    def start(self):
        """Start the bridge server"""
        print("=" * 50)
        print("EmotiBit Bridge Server - IMPROVED PARSER")
        print("=" * 50)
        print(f"UDP Port: {self.udp_port}")
        print(f"HTTP Port: {self.http_port}")
        print("Enhanced parsing for EmotiBit data format")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        # Start UDP listener
        udp_thread = threading.Thread(target=self.udp_listener, daemon=True)
        udp_thread.start()
        
        # Start data processor
        process_thread = threading.Thread(target=self.process_loop, daemon=True)
        process_thread.start()
        
        # Start HTTP server
        try:
            handler = self.make_handler()
            with socketserver.TCPServer(("", self.http_port), handler) as httpd:
                print(f"HTTP server running on http://localhost:{self.http_port}")
                print("Check status at: http://localhost:8080/status")
                print("=" * 50)
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.running = False
        except Exception as e:
            print(f"Server error: {e}")

    def udp_listener(self):
        """Listen for UDP data from EmotiBit"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', self.udp_port))
            sock.settimeout(2.0)
            
            print(f"UDP listener active on port {self.udp_port}")
            print("Enhanced parser ready for EmotiBit data...")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(8192)  # Increased buffer size
                    self.packets_received += 1
                    self.last_packet_time = time.time()
                    
                    # Process the data with improved parsing
                    data_string = data.decode('utf-8', errors='ignore')
                    self.parse_emotibit_data_improved(data_string)
                    
                    # Update connection status
                    self.current_data['connection_status'] = 'connected'
                    self.current_data['packets_received'] = self.packets_received
                    
                    if self.packets_received % 1000 == 1:  # Log every 1000th packet
                        print(f"Processed {self.packets_received} packets, {self.successful_parses} successful parses")
                        
                except socket.timeout:
                    # Check if we've lost connection
                    if self.last_packet_time > 0 and (time.time() - self.last_packet_time) > 10:
                        self.current_data['connection_status'] = 'disconnected'
                        self.current_data['last_update'] = f'Lost connection {int(time.time() - self.last_packet_time)}s ago'
                    continue
                    
                except Exception as e:
                    print(f"UDP error: {e}")
                    
        except Exception as e:
            print(f"Failed to start UDP listener: {e}")

    def parse_emotibit_data_improved(self, data_string):
        """Improved EmotiBit data parser - handles multiple data formats"""
        try:
            timestamp = time.time()
            
            # Debug: Print first few characters to understand format
            if self.packets_received % 5000 == 1:
                print(f"Sample data format: {data_string[:200]}...")
            
            # Method 1: Try to parse XML-style EmotiBit format
            if self.parse_xml_format(data_string, timestamp):
                return
            
            # Method 2: Try to parse CSV-style format
            if self.parse_csv_format(data_string, timestamp):
                return
            
            # Method 3: Try to extract numbers and map to sensor types
            if self.parse_numeric_format(data_string, timestamp):
                return
            
            # Method 4: Parse structured text format
            if self.parse_structured_format(data_string, timestamp):
                return
                
        except Exception as e:
            if self.packets_received % 1000 == 1:
                print(f"Parse error: {e}")

    def parse_xml_format(self, data_string, timestamp):
        """Parse XML-style EmotiBit data"""
        try:
            if '<type>' in data_string and '</type>' in data_string:
                # Extract data type
                type_match = re.search(r'<type>(.*?)</type>', data_string)
                if type_match:
                    data_type = type_match.group(1).strip()
                    
                    # Extract numeric values from anywhere in the string
                    numbers = re.findall(r'-?\d+\.?\d*', data_string)
                    values = []
                    
                    for num_str in numbers:
                        try:
                            value = float(num_str)
                            # Filter out obviously non-sensor values (like timestamps, ports, etc.)
                            if abs(value) < 100000 and value != 3000:  # Reasonable sensor value range
                                values.append(value)
                        except ValueError:
                            continue
                    
                    if data_type in self.sensor_data and values:
                        # Store multiple values if available
                        for value in values[:5]:  # Take up to 5 values
                            self.sensor_data[data_type].append({
                                'timestamp': timestamp,
                                'value': value
                            })
                        
                        self.successful_parses += 1
                        self.current_data['last_update'] = f"XML: {data_type} = {values[0]:.3f} ({len(values)} values)"
                        self.current_data['raw_data_samples'] = len(self.sensor_data[data_type])
                        
                        if self.successful_parses % 100 == 1:
                            print(f"XML parsed {data_type}: {values[:3]}")
                        return True
        except Exception:
            pass
        return False

    def parse_csv_format(self, data_string, timestamp):
        """Parse CSV-style EmotiBit data"""
        try:
            lines = data_string.strip().split('\n')
            for line in lines:
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        try:
                            # Try different CSV formats
                            if parts[1].strip() in self.sensor_data:
                                data_type = parts[1].strip()
                                values = []
                                
                                for part in parts[2:]:
                                    try:
                                        value = float(part.strip())
                                        if abs(value) < 100000:  # Reasonable range
                                            values.append(value)
                                    except ValueError:
                                        continue
                                
                                if values:
                                    for value in values:
                                        self.sensor_data[data_type].append({
                                            'timestamp': timestamp,
                                            'value': value
                                        })
                                    
                                    self.successful_parses += 1
                                    self.current_data['last_update'] = f"CSV: {data_type} = {values[0]:.3f}"
                                    return True
                                    
                        except (ValueError, IndexError):
                            continue
        except Exception:
            pass
        return False

    def parse_numeric_format(self, data_string, timestamp):
        """Extract numbers and intelligently assign to sensor types"""
        try:
            # Extract all numeric values
            numbers = re.findall(r'-?\d+\.?\d+', data_string)
            if len(numbers) < 2:
                return False
            
            values = []
            for num_str in numbers:
                try:
                    value = float(num_str)
                    # Filter reasonable sensor ranges
                    if -1000 <= value <= 10000 and value != 3000:  # Exclude port numbers
                        values.append(value)
                except ValueError:
                    continue
            
            if len(values) >= 2:
                # Intelligently assign values to sensor types based on typical ranges
                for i, value in enumerate(values[:6]):  # Take first 6 values
                    
                    # PPG values are typically large positive numbers
                    if 500 <= value <= 5000:
                        self.sensor_data['PPG_INFRARED'].append({
                            'timestamp': timestamp,
                            'value': value
                        })
                        sensor_type = 'PPG_INFRARED'
                        
                    # EDA values are typically small positive numbers
                    elif 0 <= value <= 10:
                        self.sensor_data['EDA'].append({
                            'timestamp': timestamp,
                            'value': value
                        })
                        sensor_type = 'EDA'
                        
                    # Temperature values are around body temperature
                    elif 20 <= value <= 50:
                        self.sensor_data['TEMPERATURE_0'].append({
                            'timestamp': timestamp,
                            'value': value
                        })
                        sensor_type = 'TEMPERATURE_0'
                        
                    # Accelerometer values are typically small
                    elif -50 <= value <= 50:
                        accel_types = ['ACCELEROMETER_X', 'ACCELEROMETER_Y', 'ACCELEROMETER_Z']
                        sensor_type = accel_types[i % 3]
                        self.sensor_data[sensor_type].append({
                            'timestamp': timestamp,
                            'value': value
                        })
                    else:
                        continue
                
                self.successful_parses += 1
                self.current_data['last_update'] = f"Numeric: {len(values)} values parsed"
                
                if self.successful_parses % 50 == 1:
                    print(f"Numeric parsing: {values[:4]}")
                return True
                
        except Exception:
            pass
        return False

    def parse_structured_format(self, data_string, timestamp):
        """Parse any structured text format with sensor names"""
        try:
            # Look for sensor names followed by values
            for sensor_name in self.sensor_data.keys():
                pattern = rf'{sensor_name}[:\s=]+(-?\d+\.?\d*)'
                match = re.search(pattern, data_string, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    self.sensor_data[sensor_name].append({
                        'timestamp': timestamp,
                        'value': value
                    })
                    
                    self.successful_parses += 1
                    self.current_data['last_update'] = f"Structured: {sensor_name} = {value:.3f}"
                    return True
                    
        except Exception:
            pass
        return False

    def process_loop(self):
        """Process REAL data only - enhanced calculations"""
        while self.running:
            try:
                if self.packets_received > 0 and self.successful_parses > 0:
                    self.calculate_enhanced_metrics()
                else:
                    self.current_data.update({
                        'heart_rate': None,
                        'hrv_rmssd': None,
                        'eda_tonic': None,
                        'temperature': None,
                        'activity_level': None,
                        'last_update': f'Received {self.packets_received} packets, {self.successful_parses} parsed'
                    })
                
                self.current_data['timestamp'] = time.time()
                time.sleep(2)
                
            except Exception as e:
                print(f"Process error: {e}")
                time.sleep(2)

    def calculate_enhanced_metrics(self):
        """Enhanced metric calculation from real sensor data"""
        
        # Heart rate from PPG data
        ppg_data = self.sensor_data['PPG_INFRARED']
        if len(ppg_data) > 30:
            try:
                # Get recent data
                recent_data = list(ppg_data)[-50:]
                values = [d['value'] for d in recent_data]
                timestamps = [d['timestamp'] for d in recent_data]
                
                if len(values) > 20:
                    # Enhanced peak detection
                    values_array = np.array(values)
                    
                    # Remove trend
                    detrended = values_array - np.linspace(values_array[0], values_array[-1], len(values_array))
                    
                    # Find peaks
                    mean_val = np.mean(detrended)
                    std_val = np.std(detrended)
                    threshold = mean_val + std_val * 0.7
                    
                    peaks = []
                    for i in range(2, len(detrended)-2):
                        if (detrended[i] > detrended[i-1] and detrended[i] > detrended[i+1] and 
                            detrended[i] > detrended[i-2] and detrended[i] > detrended[i+2] and
                            detrended[i] > threshold):
                            peaks.append(i)
                    
                    if len(peaks) >= 3:
                        # Calculate heart rate
                        peak_times = [timestamps[p] for p in peaks]
                        intervals = np.diff(peak_times)
                        
                        if len(intervals) > 0:
                            avg_interval = np.median(intervals)  # Use median for robustness
                            if avg_interval > 0:
                                heart_rate = 60 / avg_interval
                                
                                # Reasonable heart rate range
                                if 30 <= heart_rate <= 200:
                                    self.current_data['heart_rate'] = int(heart_rate)
                                    
                                    # Calculate HRV from intervals
                                    if len(intervals) > 2:
                                        # RMSSD calculation
                                        diff_intervals = np.diff(intervals)
                                        rmssd = np.sqrt(np.mean(diff_intervals**2)) * 1000
                                        
                                        if 5 <= rmssd <= 300:
                                            self.current_data['hrv_rmssd'] = int(rmssd)
                                            
            except Exception as e:
                print(f"HR calculation error: {e}")
        
        # EDA processing
        eda_data = self.sensor_data['EDA']
        if len(eda_data) > 10:
            try:
                recent_values = [d['value'] for d in list(eda_data)[-20:]]
                if recent_values:
                    # Use median for tonic level (more robust than mean)
                    tonic_level = np.median(recent_values)
                    if 0 <= tonic_level <= 100:  # Reasonable EDA range
                        self.current_data['eda_tonic'] = float(tonic_level)
            except Exception as e:
                print(f"EDA calculation error: {e}")
        
        # Activity level from accelerometer
        accel_data = self.sensor_data['ACCELEROMETER_X']
        if len(accel_data) > 15:
            try:
                recent_values = [d['value'] for d in list(accel_data)[-30:]]
                if recent_values:
                    activity = np.std(recent_values)
                    self.current_data['activity_level'] = float(activity)
            except Exception as e:
                print(f"Activity calculation error: {e}")
        
        # Temperature
        temp_data = self.sensor_data['TEMPERATURE_0']
        if len(temp_data) > 5:
            try:
                recent_values = [d['value'] for d in list(temp_data)[-10:]]
                if recent_values:
                    avg_temp = np.mean(recent_values)
                    if 15 <= avg_temp <= 60:  # Reasonable temperature range
                        self.current_data['temperature'] = float(avg_temp)
            except Exception as e:
                print(f"Temperature calculation error: {e}")

    def make_handler(self):
        """Create HTTP request handler with enhanced status"""
        bridge = self
        
        class BridgeHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/data':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response_data = {
                        'type': 'sensor_data',
                        'data': bridge.current_data.copy(),
                        'timestamp': time.time(),
                        'real_data_only': True,
                        'parsing_stats': {
                            'packets_received': bridge.packets_received,
                            'successful_parses': bridge.successful_parses,
                            'parse_rate': bridge.successful_parses / max(bridge.packets_received, 1) * 100
                        }
                    }
                    
                    self.wfile.write(json.dumps(response_data).encode())
                    
                elif self.path == '/status':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    conn_status = bridge.current_data['connection_status']
                    status_color = 'green' if conn_status == 'connected' else 'red'
                    parse_rate = bridge.successful_parses / max(bridge.packets_received, 1) * 100
                    
                    status_html = f"""
                    <html>
                    <head>
                        <title>EmotiBit Bridge - Enhanced Parser</title>
                        <style>body{{font-family: Arial; margin: 40px;}}</style>
                    </head>
                    <body>
                    <h1>EmotiBit Bridge - Enhanced Parser</h1>
                    <p><strong>Connection:</strong> <span style="color: {status_color};">{conn_status.upper()}</span></p>
                    <p><strong>Packets Received:</strong> {bridge.packets_received}</p>
                    <p><strong>Successfully Parsed:</strong> {bridge.successful_parses}</p>
                    <p><strong>Parse Success Rate:</strong> {parse_rate:.1f}%</p>
                    <p><strong>Last Update:</strong> {bridge.current_data['last_update']}</p>
                    
                    <h2>Real Sensor Data:</h2>
                    <ul>
                    <li>Heart Rate: {bridge.current_data['heart_rate'] or 'No data'} BPM</li>
                    <li>HRV: {bridge.current_data['hrv_rmssd'] or 'No data'} ms</li>
                    <li>EDA: {bridge.current_data['eda_tonic'] or 'No data'}</li>
                    <li>Activity: {bridge.current_data['activity_level'] or 'No data'}</li>
                    <li>Temperature: {bridge.current_data['temperature'] or 'No data'}°C</li>
                    </ul>
                    
                    <h2>Data Buffer Status:</h2>
                    <ul>
                    <li>PPG Samples: {len(bridge.sensor_data['PPG_INFRARED'])}</li>
                    <li>EDA Samples: {len(bridge.sensor_data['EDA'])}</li>
                    <li>Accelerometer Samples: {len(bridge.sensor_data['ACCELEROMETER_X'])}</li>
                    <li>Temperature Samples: {len(bridge.sensor_data['TEMPERATURE_0'])}</li>
                    </ul>
                    
                    <p><a href="/data">Raw JSON Data</a></p>
                    <script>setTimeout(function(){{location.reload()}}, 3000);</script>
                    </body>
                    </html>
                    """
                    
                    self.wfile.write(status_html.encode())
                else:
                    super().do_GET()
                    
            def log_message(self, format, *args):
                return  # Suppress logs
        
        return BridgeHandler

if __name__ == "__main__":
    print("Starting EmotiBit Bridge - ENHANCED PARSER")
    print("Multiple parsing methods to extract real sensor values")
    
    bridge = EmotiBitBridge(udp_port=3000, http_port=8080)
    bridge.start()
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .const import MainService
from .exceptions import DecodeError
from .packets import PacketNotify
from .services import NotifyCharacteristic

app = FastAPI()

# Global state
ble_client = None
current_data = None
connected_websockets = []
scanning = False
discovered_devices = []


class ConnectRequest(BaseModel):
    address: str


async def notify_data(char_specifier: BleakGATTCharacteristic, data: bytearray):
    """Callback function for BLE notifications"""
    global current_data
    try:
        packet_data = NotifyCharacteristic.decode(data)
        packet = PacketNotify.decode(packet_data)
        current_data = {
            "battery": packet.battery,
            "ambient_a": packet.ambient_a,
            "ambient_b": packet.ambient_b,
            "probe_p1": packet.probe_p1,
            "probe_p2": packet.probe_p2,
            "probe_p1_connected": packet.probe_p1_connected,
            "probe_p2_connected": packet.probe_p2_connected,
            "eco_mode": packet.eco_mode,
            "temperature_unit": packet.temperature_unit.value,
        }
        
        # Send to all connected websockets
        for ws in connected_websockets[:]:
            try:
                await ws.send_json(current_data)
            except:
                connected_websockets.remove(ws)
                
    except DecodeError as exc:
        print(f"Failed to decode: {data.hex()} with error {exc}")


async def connect_ble(address: str):
    """Connect to BLE device"""
    global ble_client
    
    # Disconnect existing client if any
    if ble_client and ble_client.is_connected:
        await ble_client.stop_notify(MainService.notify.uuid)
        await ble_client.disconnect()
    
    # Create new client and connect
    ble_client = BleakClient(address, timeout=20)
    await ble_client.connect()
    await ble_client.start_notify(MainService.notify.uuid, notify_data)
    
    return True


@app.get("/")
async def get_home():
    """Serve the main HTML page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ooni Connect Thermometer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 695px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .connect-section {
                margin-bottom: 30px;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
            .scan-section {
                margin-bottom: 20px;
            }
            .button-group {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }
            .manual-connect {
                margin-top: 15px;
                display: none;
            }
            .manual-connect.show {
                display: block;
            }
            .advanced-toggle {
                background-color: #666;
            }
            .advanced-toggle:hover {
                background-color: #555;
            }
            .devices-list {
                margin-top: 15px;
                max-height: 200px;
                overflow-y: auto;
            }
            .device-item {
                padding: 12px;
                margin: 5px 0;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.2s;
            }
            .device-item:hover {
                background-color: #e8f5e9;
                border-color: #4CAF50;
            }
            .device-info {
                flex: 1;
            }
            .device-name {
                font-weight: bold;
                color: #333;
            }
            .device-address {
                font-size: 12px;
                color: #666;
            }
            .device-rssi {
                font-size: 12px;
                color: #999;
            }
            .input-group {
                display: flex;
                gap: 10px;
                margin-bottom: 10px;
            }
            input[type="text"] {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            button {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
            }
            button:hover {
                background-color: #45a049;
            }
            button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .status {
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            .status.connected {
                background-color: #d4edda;
                color: #155724;
            }
            .status.disconnected {
                background-color: #f8d7da;
                color: #721c24;
            }
            .status.connecting {
                background-color: #fff3cd;
                color: #856404;
            }
            .data-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .data-card {
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                border: 2px solid #e0e0e0;
            }
            .data-card.active {
                border-color: #4CAF50;
            }
            .data-label {
                font-size: 14px;
                color: #666;
                margin-bottom: 10px;
            }
            .data-value {
                font-size: 32px;
                font-weight: bold;
                color: #333;
            }
            .data-unit {
                font-size: 16px;
                color: #999;
            }
            .info-row {
                display: flex;
                justify-content: space-around;
                margin-top: 20px;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
            .info-item {
                text-align: center;
            }
            .info-label {
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }
            .info-value {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
            .badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }
            .badge.on {
                background-color: #d4edda;
                color: #155724;
            }
            .badge.off {
                background-color: #f8d7da;
                color: #721c24;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔥 Ooni Connect Thermometer</h1>
            
            <div class="connect-section">
                <div class="scan-section">
                    <div class="button-group">
                        <button id="scanBtn" onclick="scanDevices()">🔍 Scan for Devices</button>
                        <button class="advanced-toggle" onclick="toggleAdvanced()">⚙️ Advanced Options</button>
                    </div>
                    <div id="devicesList" class="devices-list"></div>
                </div>
                
                <div id="manualConnect" class="manual-connect">
                    <div class="input-group">
                        <input type="text" id="address" placeholder="Enter BLE device address (e.g., AA:BB:CC:DD:EE:FF)" value="">
                        <button id="connectBtn" onclick="connect()">Connect</button>
                    </div>
                </div>
                <div id="status" class="status disconnected">Disconnected</div>
            </div>
            
            <div class="data-grid">
                <div class="data-card" id="probe1-card">
                    <div class="data-label">Probe P1</div>
                    <div class="data-value" id="probe_p1">--</div>
                    <div class="data-unit" id="temp_unit">°F</div>
                </div>
                
                <div class="data-card" id="probe2-card">
                    <div class="data-label">Probe P2</div>
                    <div class="data-value" id="probe_p2">--</div>
                    <div class="data-unit" id="temp_unit2">°F</div>
                </div>
                
                <div class="data-card">
                    <div class="data-label">Ambient A</div>
                    <div class="data-value" id="ambient_a">--</div>
                    <div class="data-unit" id="temp_unit3">°F</div>
                </div>
                
                <div class="data-card">
                    <div class="data-label">Ambient B</div>
                    <div class="data-value" id="ambient_b">--</div>
                    <div class="data-unit" id="temp_unit4">°F</div>
                </div>
            </div>
            
            <div class="info-row">
                <div class="info-item">
                    <div class="info-label">Battery</div>
                    <div class="info-value" id="battery">--</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Eco Mode</div>
                    <div class="info-value" id="eco_mode">--</div>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            
            function toggleAdvanced() {
                const manualConnect = document.getElementById('manualConnect');
                manualConnect.classList.toggle('show');
            }
            
            function updateStatus(message, type) {
                const status = document.getElementById('status');
                status.textContent = message;
                status.className = 'status ' + type;
            }
            
            async function scanDevices() {
                const scanBtn = document.getElementById('scanBtn');
                const devicesList = document.getElementById('devicesList');
                
                scanBtn.disabled = true;
                scanBtn.textContent = '🔍 Scanning...';
                devicesList.innerHTML = '<div style="padding: 10px; text-align: center; color: #666;">Scanning for devices...</div>';
                
                try {
                    const response = await fetch('/scan');
                    const result = await response.json();
                    
                    if (result.success) {
                        if (result.devices.length === 0) {
                            devicesList.innerHTML = '<div style="padding: 10px; text-align: center; color: #666;">No devices found</div>';
                        } else {
                            devicesList.innerHTML = result.devices.map(device => `
                                <div class="device-item" onclick="selectDevice('${device.address}')">
                                    <div class="device-info">
                                        <div class="device-name">${device.name}</div>
                                        <div class="device-address">${device.address}</div>
                                    </div>
                                    <div class="device-rssi">RSSI: ${device.rssi}</div>
                                </div>
                            `).join('');
                        }
                    } else {
                        devicesList.innerHTML = `<div style="padding: 10px; color: #721c24;">Error: ${result.error}</div>`;
                    }
                } catch (error) {
                    devicesList.innerHTML = `<div style="padding: 10px; color: #721c24;">Error: ${error.message}</div>`;
                } finally {
                    scanBtn.disabled = false;
                    scanBtn.textContent = '🔍 Scan for Devices';
                }
            }
            
            function selectDevice(address) {
                document.getElementById('address').value = address;
                connect();
            }
            
            function updateData(data) {
                document.getElementById('probe_p1').textContent = data.probe_p1;
                document.getElementById('probe_p2').textContent = data.probe_p2;
                document.getElementById('ambient_a').textContent = data.ambient_a;
                document.getElementById('ambient_b').textContent = data.ambient_b;
                document.getElementById('battery').textContent = data.battery + '%';
                
                const unit = '°' + data.temperature_unit;
                document.getElementById('temp_unit').textContent = unit;
                document.getElementById('temp_unit2').textContent = unit;
                document.getElementById('temp_unit3').textContent = unit;
                document.getElementById('temp_unit4').textContent = unit;
                
                const ecoMode = document.getElementById('eco_mode');
                ecoMode.innerHTML = data.eco_mode ? '<span class="badge on">ON</span>' : '<span class="badge off">OFF</span>';
                
                // Highlight connected probes
                const probe1Card = document.getElementById('probe1-card');
                const probe2Card = document.getElementById('probe2-card');
                if (data.probe_p1_connected) {
                    probe1Card.classList.add('active');
                } else {
                    probe1Card.classList.remove('active');
                }
                if (data.probe_p2_connected) {
                    probe2Card.classList.add('active');
                } else {
                    probe2Card.classList.remove('active');
                }
            }
            
            async function connect() {
                const address = document.getElementById('address').value.trim();
                if (!address) {
                    alert('Please enter a BLE device address');
                    return;
                }
                
                const connectBtn = document.getElementById('connectBtn');
                connectBtn.disabled = true;
                updateStatus('Connecting...', 'connecting');
                
                try {
                    const response = await fetch('/connect', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ address: address })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        updateStatus('Connected to ' + address, 'connected');
                        
                        // Connect WebSocket
                        if (ws) {
                            ws.close();
                        }
                        
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        ws = new WebSocket(protocol + '//' + window.location.host + '/ws');
                        
                        ws.onmessage = function(event) {
                            const data = JSON.parse(event.data);
                            updateData(data);
                        };
                        
                        ws.onclose = function() {
                            console.log('WebSocket closed');
                            updateStatus('Disconnected', 'disconnected');
                            document.getElementById('connectBtn').disabled = false;
                        };
                        
                        ws.onerror = function(error) {
                            console.error('WebSocket error:', error);
                        };
                    } else {
                        updateStatus('Connection failed: ' + result.error, 'disconnected');
                        connectBtn.disabled = false;
                    }
                } catch (error) {
                    updateStatus('Connection failed: ' + error.message, 'disconnected');
                    connectBtn.disabled = false;
                }
            }
            
            // Allow Enter key to connect
            document.getElementById('address').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    connect();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/scan")
async def scan_devices():
    """Scan for nearby Ooni devices"""
    global scanning, discovered_devices
    
    if scanning:
        return {"success": False, "error": "Scan already in progress"}
    
    scanning = True
    discovered_devices = []
    found_addresses = set()
    
    def detection_callback(device: BLEDevice, advertisement: AdvertisementData):
        if device.address not in found_addresses and device.name == "Ooni_DT_Hub":
            found_addresses.add(device.address)
            discovered_devices.append({
                "address": device.address,
                "name": device.name or "Unknown",
                "rssi": advertisement.rssi
            })
    
    try:
        scanner = BleakScanner(detection_callback)
        await scanner.start()
        await asyncio.sleep(5)  # Scan for 5 seconds
        await scanner.stop()
        
        scanning = False
        return {"success": True, "devices": discovered_devices}
    except Exception as e:
        scanning = False
        return {"success": False, "error": str(e)}


@app.post("/connect")
async def connect_endpoint(request: ConnectRequest):
    """Connect to BLE device endpoint"""
    try:
        await connect_ble(request.address)
        return {"success": True, "address": request.address}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data updates"""
    await websocket.accept()
    connected_websockets.append(websocket)
    
    # Send current data if available
    if current_data:
        await websocket.send_json(current_data)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global ble_client
    if ble_client and ble_client.is_connected:
        await ble_client.stop_notify(MainService.notify.uuid)
        await ble_client.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

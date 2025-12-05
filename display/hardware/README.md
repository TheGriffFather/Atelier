# Hardware Planning - Digital Art Frame

This document outlines the hardware components for building a physical digital art frame to display the Dan Brown artwork collection.

---

## Current Test Setup Status (December 3, 2025)

### Hardware Configuration
| Component | Status | Details |
|-----------|--------|---------|
| Raspberry Pi 4B | ✅ **ONLINE** | IP: 192.168.87.67 (jarvis-satellite) |
| OS | ✅ Running | Debian 13 (trixie) |
| Display | Test Setup | DVI monitor via adapter chain |
| Connection | microHDMI → HDMI → DVI | Not the planned DSI touchscreen |
| Kiosk Service | ✅ Running | Chromium in kiosk mode |
| Server Connection | ✅ Working | http://192.168.87.63:8000/frame |

### Current Adapter Chain
```
Pi 4B microHDMI port → HDMI adapter → HDMI cable → HDMI-to-DVI adapter → DVI Monitor
```

### Software Stack (Verified Working)
- ✅ Debian 13 (trixie) installed
- ✅ Xorg display server
- ✅ Chromium 142.0.7444.175
- ✅ Unclutter (cursor hiding)
- ✅ Kiosk service (`/etc/systemd/system/kiosk.service`)
- ✅ Auto-start on boot enabled
- ✅ Points to `http://192.168.87.63:8000/frame`

### Test Commands
```bash
# From Windows PC - Test Pi connectivity
python scripts/pi_ssh.py

# From Windows PC - Check kiosk status
python scripts/pi_ssh.py "systemctl status kiosk.service --no-pager"

# From Windows PC - Test server reachability from Pi
python scripts/pi_ssh.py "curl -s http://192.168.87.63:8000/health"
```

### Kiosk Service Commands (run on Pi via SSH)
```bash
sudo systemctl start kiosk.service    # Start display
sudo systemctl stop kiosk.service     # Stop display
sudo systemctl status kiosk.service   # Check status
sudo journalctl -u kiosk.service -f   # View logs
```

### If Pi Goes Offline
1. Connect Pi to power and network
2. Check router for new IP assignment (DHCP may have changed)
3. Update `scripts/pi_ssh.py` line 5 with new IP if changed
4. Test with: `python scripts/pi_ssh.py`

---

## Display Selection

### Waveshare 10.1" DSI Touch Display (10.1-DSI-TOUCH-B)

**Product Link:** https://www.waveshare.com/10.1-dsi-touch-b.htm

#### Specifications

| Feature | Value |
|---------|-------|
| Screen Size | 10.1 inches (diagonal) |
| Resolution | 720 x 1280 pixels |
| Panel Type | IPS |
| Interface | DSI (MIPI Display Serial Interface) |
| Viewing Angle | 170 degrees |
| Brightness | 500 cd/m² |
| Touch Type | 10-point capacitive |
| Touch Interface | I2C |
| Power | 5V via GPIO |
| Weight | 0.623 kg |

#### Key Features
- High contrast IPS panel with excellent viewing angles
- Capacitive touch supports gestures (swipe, pinch, etc.)
- DSI interface provides better performance than HDMI
- No additional power supply needed (powers from Pi GPIO)
- Suitable aspect ratio for portrait-oriented artwork

## Board Selection

### Primary: Raspberry Pi 4B (Using Existing Hardware)

For initial prototyping and deployment, we'll use an existing Raspberry Pi 4B. This board is fully compatible with the display and adequate for our use case:

- Displaying the web interface at 720x1280
- Touch interaction with swipe gestures
- Image slideshow functionality
- Running the FastAPI server locally

**Note:** The Pi 4B uses a 15-pin DSI connector. The Waveshare display includes the appropriate cable for Pi 4B.

### Future Upgrade: Raspberry Pi 5 (4GB or 8GB)

If performance upgrades are needed later:

| Feature | Pi 5 | Pi 4B |
|---------|------|-------|
| CPU | Quad-core Cortex-A76 @ 2.4GHz | Quad-core Cortex-A72 @ 1.8GHz |
| GPU | VideoCore VII | VideoCore VI |
| DSI Port | 22-pin (needs adapter cable) | 15-pin (direct) |
| Browser Performance | Excellent | Good |

**Note:** Pi 5 uses a different DSI connector - would need the [Pi5 Display Cable](https://www.waveshare.com/pi5-display-cable.htm) ($0.89-$2.89).

## Parts List

### What's Included with Display

The [Waveshare 10.1-DSI-TOUCH-B](https://www.waveshare.com/10.1-dsi-touch-b.htm) ($79.99) includes:
- 10.1-DSI-TOUCH-B display unit
- MIPI-DSI-Cable-12cm (for Pi 4B connection)
- MX 1.25 2PIN to 2.54 3PIN cable (power/touch)
- FFC 22PIN cable ~200mm x2 (opposite sides)
- MX1.25 2PIN to MX1.25 4PIN cable ~150mm
- Screws pack

### What You Already Have (Existing Hardware)

| Component | Status |
|-----------|--------|
| Raspberry Pi 4B | Have |
| Pi 4B Power Supply | Have |
| microSD Card | Have (or need 32GB+) |

### Shopping List - Waveshare Items to Purchase

| Item | Waveshare SKU | Price | Link |
|------|---------------|-------|------|
| **10.1" DSI Touch Display** | 10.1-DSI-TOUCH-B | $79.99 | [Product Page](https://www.waveshare.com/10.1-dsi-touch-b.htm) |

**Total to Purchase: ~$80** (display only - cables included!)

### Optional Waveshare Accessories

| Item | SKU | Price | Link | Notes |
|------|-----|-------|------|-------|
| 32GB microSD Card | Raspberry Pi SD Card | $3.99 | [Product Page](https://www.waveshare.com/raspberry-pi-sd-card.htm) | Class A2, pre-formatted |
| Pi4 Aluminum Case | PI4-CASE-A | ~$8 | [Cases](https://www.waveshare.com/product/accessories/misc/raspberry-pi-cases.htm) | With heatsinks |
| Longer DSI Cable (300mm) | pi5_display_cable | $1.89 | [Product Page](https://www.waveshare.com/pi5-display-cable.htm) | If more cable length needed |

### Future Upgrade Parts (Pi 5)

If upgrading to Pi 5 later:

| Item | SKU | Price | Link |
|------|-----|-------|------|
| Raspberry Pi 5 (4GB) | Raspberry Pi 5 | $54.99 | [Pi 5 Page](https://www.waveshare.com/product/raspberry-pi/boards-kits/raspberry-pi-5.htm) |
| 27W USB-C Power Supply | PSU-27W-USB-C | $7.99 | [Product Page](https://www.waveshare.com/psu-27w-usb-c.htm) |
| Pi5 DSI Display Cable | pi5_display_cable | $0.89-$2.89 | [Product Page](https://www.waveshare.com/pi5-display-cable.htm) |
| Pi5 Case with Cooling | PI5-CASE-C | $7.99 | [Product Page](https://www.waveshare.com/pi5-case-c.htm) |

## Software Requirements

### Operating System
- Raspberry Pi OS (64-bit) - Bookworm or later
- Desktop environment required for browser

### Display Driver
The Waveshare DSI display requires driver configuration:

```bash
# Add to /boot/firmware/config.txt (Pi 5) or /boot/config.txt (Pi 4)
dtoverlay=vc4-kms-dsi-waveshare-panel,10_1_inchB
```

### Touch Calibration
Touch should work automatically via I2C. If calibration is needed:
```bash
sudo apt install xinput-calibrator
xinput_calibrator
```

### Auto-start Browser (Kiosk Mode)

Create autostart file for fullscreen browser:

```bash
# ~/.config/autostart/kiosk.desktop
[Desktop Entry]
Type=Application
Name=Art Frame Kiosk
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8000/frame
```

### Art Tracker Service

The FastAPI server should run as a systemd service:

```bash
# /etc/systemd/system/art-tracker.service
[Unit]
Description=Dan Brown Art Tracker
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/dan-brown-art
ExecStart=/home/pi/dan-brown-art/.venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Frame Design Considerations

### Orientation
- Display is naturally portrait (720x1280)
- Most Dan Brown artwork is portrait-oriented
- Frame interface designed for vertical viewing

### Mounting Options
1. **Tabletop stand** - Display includes mounting holes
2. **Picture frame** - Build custom frame surround
3. **Wall mount** - Use VESA adapter or custom bracket

### Heat Management
- Ensure adequate ventilation behind display
- Pi 5 may need active cooling for continuous operation
- Consider standby mode during extended non-use periods

## Assembly Notes

### Connection Order
1. Connect DSI ribbon cable to display (silver contacts facing board)
2. Connect other end to Pi DSI port
3. Connect I2C touch cable to Pi GPIO (included with display)
4. Insert microSD with pre-configured OS
5. Connect power last

### Testing
1. Boot Pi and verify display shows desktop
2. Test touch by tapping/swiping
3. Open browser and navigate to `http://localhost:8000/frame`
4. Verify swipe navigation works
5. Test long-press for settings menu

## Cost Estimate

### Initial Build (Using Existing Pi 4B)

| Component | Cost (USD) | Source |
|-----------|------------|--------|
| Waveshare 10.1" Display | $79.99 | Waveshare |
| Raspberry Pi 4B | Already have | - |
| Power Supply | Already have | - |
| microSD Card | Already have | - |
| **Total** | **~$80** | |

### Full Build (If Starting Fresh with Pi 5)

| Component | Cost (USD) | Source |
|-----------|------------|--------|
| Waveshare 10.1" Display | $79.99 | Waveshare |
| Raspberry Pi 5 (4GB) | $54.99 | Waveshare |
| 27W USB-C Power Supply | $7.99 | Waveshare |
| Pi5 DSI Cable | $1.89 | Waveshare |
| 32GB microSD Card | $3.99 | Waveshare |
| Pi5 Case with Cooling | $7.99 | Waveshare |
| **Total** | **~$157** | |

*Prices as of November 2024, may vary by region*

## Future Enhancements

- [ ] Design 3D-printable frame enclosure
- [ ] Add ambient light sensor for brightness adjustment
- [ ] Add physical button for power/wake
- [ ] Integrate with home automation (Home Assistant)
- [ ] Add proximity sensor to wake on approach

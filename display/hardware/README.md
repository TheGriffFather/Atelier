# A browser display for your collection

Atelier's `/frame` page can run on a normal computer display or a Raspberry Pi in Chromium kiosk mode. Begin with a local browser before buying dedicated hardware.

## Parts

| Component | Purpose |
| --- | --- |
| Raspberry Pi 4B or newer, or a small computer | Runs the browser; it can also host Atelier. |
| Compatible display | HDMI is a simple first setup. Touch is optional. |
| Appropriate power supply and microSD/storage | Follow the board manufacturer's requirements. |
| Stand or frame with ventilation | Keeps the assembly stable and serviceable. |

A Waveshare **10.1-DSI-TOUCH-B** was considered for the original design. Confirm the exact display revision, DSI cable, driver instructions, and power requirements with the [manufacturer](https://www.waveshare.com/10.1-dsi-touch-b.htm). Pi 4 and Pi 5 use different display connectors. The repository does not include a tested printable enclosure for this display.

## Local setup

1. Install an operating system with a desktop and Chromium.
2. Install Atelier using the [README](../../README.md#run-atelier-locally).
3. Start the server on localhost and open `http://127.0.0.1:8000/display` to choose slideshow settings.
4. Open `http://127.0.0.1:8000/frame` and check navigation, image fit, and touch behavior on your actual screen.

For a kiosk, launch the browser installed on your system with a dedicated profile:

```bash
chromium --kiosk --user-data-dir="$HOME/.config/atelier-kiosk" http://127.0.0.1:8000/frame
```

Some distributions name the executable `chromium-browser`. Use your desktop environment's supported autostart mechanism after testing the command manually. Keep a way to exit kiosk mode and service the computer.

## A separate host

Atelier currently has no application login. Its default listener and Docker host mapping are localhost-only. A display on another computer needs a protected connection, such as an authenticated tunnel; do not expose the complete API merely to show the frame. Review [Security](../../SECURITY.md) before changing network access.

Keep host addresses, device names, SSH settings, and deployment status in your own local notes, not this public guide.

## Physical checks

Power down before connecting display cables. Follow the board and display manuals for ribbon orientation and power connections. Test touch and image orientation, cable strain relief, stability, ventilation, and recovery after reboot on the actual assembly. A working browser preview does not establish physical compatibility or continuous-operation reliability.

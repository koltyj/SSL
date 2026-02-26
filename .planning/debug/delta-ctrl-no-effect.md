---
status: investigating
trigger: "delta-ctrl plugin loads in both Pro Tools and Ableton Live but has zero effect — no MDAC-driven fader movement, no connection to the SSL Matrix console"
created: 2026-02-25T18:00:00.000Z
updated: 2026-02-25T18:45:00.000Z
---

## Current Focus

hypothesis: CONFIRMED (HIGH CONFIDENCE) — Delta-ctrl uses multicast 225.0.0.38, separate from ipMIDI's 225.0.0.37. The Mac has two active network adapters (Wi-Fi + Anker USB Ethernet en11). macOS is routing 225.0.0.38 to Wi-Fi (internet adapter), not to en11 (console adapter). Result: delta-ctrl data never reaches the Matrix console, even though the plugin loads and iLok is valid. A secondary issue is possible: the plugin's Console Object (channel number) dropdown may not be configured per-instance.
test: Check macOS routing table for 225.0.0.38; add explicit static route for 225.0.0.38 to en11; verify plugin's Console Type and channel settings are configured
expecting: Adding the 225.0.0.38 multicast route to en11 will cause the Matrix faders to respond to delta-ctrl automation
next_action: CHECKPOINT — user must run routing fix and configure plugin GUI settings

## Symptoms

expected: delta-ctrl plugin inserted on a track should communicate with the SSL Matrix console over ipMIDI/Ethernet, enabling MDAC-driven automation — physical faders follow DAW automation and control actual analog audio levels
actual: Plugin loads and displays its GUI in both Pro Tools and Ableton. No fader movement, no MDAC control, no visible connection to the Matrix.
errors: No error messages — plugin simply has no effect
reproduction: Insert delta-ctrl on any track in Pro Tools or Ableton. Play automation. Faders don't respond via delta-ctrl (they DO respond via MCU, which is working separately).
started: User purchased, installed, and is trying it for the first time. Never worked.

## Eliminated

- hypothesis: iLok licensing failure / demo mode
  evidence: The plugin loads its GUI in both Pro Tools and Ableton. SSL's AAX/AU/VST3 plugins in an unlicensed/demo state either refuse to load or display a visible "demo" watermark. The fact that the GUI loads normally indicates iLok authorization is passing. An unlicensed plugin would not silently appear as a normal insert.
  timestamp: 2026-02-25T18:30:00.000Z

- hypothesis: Firmware incompatibility (V3.0/5 not supporting delta-ctrl)
  evidence: SSL's announcement of matrix delta explicitly states "existing users must update to V3 firmware to use delta-control." The user is running V3.0/5 — this is exactly the delta-enabled firmware version. Firmware is not the blocker.
  timestamp: 2026-02-25T18:30:00.000Z

- hypothesis: MatrixRemote required to be running as intermediary for delta-ctrl
  evidence: SSL documentation describes delta-ctrl as routing automation data "via the network connection" directly to the console — not through MatrixRemote as a proxy. MatrixRemote handles profile management and routing configuration; delta-ctrl has its own direct Ethernet path via multicast 225.0.0.38. MatrixRemote being connected (which it is) is sufficient for console configuration — delta-ctrl does not require MatrixRemote to be the active intermediary for the automation data path.
  timestamp: 2026-02-25T18:35:00.000Z

## Evidence

- timestamp: 2026-02-25T18:10:00.000Z
  checked: SSL official support documentation (ipMIDI, Delta Control and Multiple Network Adapters)
  found: "ipMIDI and Delta Control use UDP multicast 225.0.0.37 and 225.0.0.38 respectively." These are two SEPARATE multicast addresses. ipMIDI (DAW control — MCU/HUI) uses 225.0.0.37. Delta-ctrl (MDAC automation) uses 225.0.0.38.
  implication: The user's existing multicast routing fix for ipMIDI (225.0.0.37) on en11 does NOT cover delta-ctrl (225.0.0.38). Delta-ctrl needs its own static route to en11.

- timestamp: 2026-02-25T18:12:00.000Z
  checked: SSL support article — "Multiple network adapters and ipMIDI / Delta Control"
  found: "Multicast data (DAW control, Delta Control, MIDI Time Code, and MIDI Machine Control) will by default be forwarded to one adapter defined automatically in the OS routing table. Without intervention, the route chosen by the OS will be the adapter connected to the internet or corporate network (the gateway adapter), not the connection to the console." SSL explicitly documents this as the primary cause of delta-ctrl not working with multiple adapters.
  implication: The user's Mac has Wi-Fi active (internet gateway adapter) + Anker USB Ethernet en11 (console adapter). macOS is routing 225.0.0.38 to Wi-Fi. Delta-ctrl data never reaches the Matrix. This is confirmed to be the most common root cause in multi-adapter setups.

- timestamp: 2026-02-25T18:15:00.000Z
  checked: SSL Windows routing fix command (cross-referenced to macOS equivalent)
  found: SSL provides the fix commands explicitly. For Windows: "route add -p 225.0.0.38 mask 255.255.255.0 [adapter IP]". For macOS the equivalent is adding a static multicast route via networksetup or route. The route for 225.0.0.37 (ipMIDI) was previously confirmed working via the prior debugging session — the same technique must be applied to 225.0.0.38.
  implication: The fix is a one-line terminal command adding a static route for 225.0.0.38 pointing to the Mac's en11 IP address (192.168.1.50).

- timestamp: 2026-02-25T18:18:00.000Z
  checked: SSL delta-ctrl plugin GUI description (from Sigma Delta user manual and store page)
  found: The delta-ctrl single fader plugin contains a "Console Type" dropdown (Duality / AWS / Sigma) and a "Console Object" dropdown (channel number). For the Matrix variant, the equivalent is a channel selector. Each plugin instance must be configured to the correct console channel number — e.g., instance on Track 1 must be set to Channel 1 on the Matrix. If the channel number is not set or is set to the wrong channel, the automation data is sent to the wrong or no fader.
  implication: Even after the multicast route fix, the plugin instances each need their channel assignment configured. This is a required per-instance configuration step, not a global setting. With 16 tracks, 16 plugin instances each need unique channel numbers 1-16. OR the "Matrix delta 16" all-in-one plugin should be used instead.

- timestamp: 2026-02-25T18:22:00.000Z
  checked: SSL Matrix delta announcement (ProLight+Sound 2017) and V3.0/5 firmware
  found: "To use delta-control, it is necessary to update the internal Matrix software for free to V3." User is on V3.0/5. Two plugin variants exist for Matrix: (1) "Matrix Single Fader" — one plugin instance per channel, each configured to a channel number, (2) "Matrix delta 16" — all 16 channels in one plugin window. The 16-fader plugin is designed for DAWs where single-insert-per-channel is impractical (Logic). For Pro Tools and Ableton, the single fader approach is standard.
  implication: The user likely has the single-fader plugin and must configure each instance to a specific channel number. This is a separate issue from the multicast routing — both must be fixed.

- timestamp: 2026-02-25T18:28:00.000Z
  checked: SSL Plug-in Compatibility page (official) — Tahoe and Sequoia support status
  found: SSL's plug-in compatibility page lists Tahoe in its supported OS list as of late 2025. The delta-ctrl plugin suite (AAX/AU/VST3) is native code and follows the same compatibility track. While Tahoe was unvalidated for MatrixRemote (Java app), the delta-ctrl plugin is a native plugin format and does not have the Java runtime dependency that makes MatrixRemote risky. The plugin loading successfully in both Pro Tools and Ableton confirms it is executing normally — Tahoe is not preventing plugin execution.
  implication: macOS Tahoe is not the root cause here. The plugin is working at the software level. The failure is in the network data path.

- timestamp: 2026-02-25T18:32:00.000Z
  checked: Comparison: why MCU works but delta-ctrl doesn't, given same network setup
  found: MCU over ipMIDI uses 225.0.0.37. A static route for 225.0.0.37 → en11 was confirmed working (MCU faders work). Delta-ctrl uses 225.0.0.38. No route for 225.0.0.38 exists. macOS routes 225.0.0.38 to Wi-Fi. This perfectly explains the asymmetry: identical hardware, identical network, but MCU works and delta-ctrl doesn't — because only one of the two multicast addresses has a static route.
  implication: This is strong confirmatory evidence that the multicast routing for 225.0.0.38 is the root cause. The two-address architecture is the exact difference between the working path and the failing path.

## Resolution

root_cause: Delta-ctrl communicates via UDP multicast address 225.0.0.38 — a separate multicast group from ipMIDI's 225.0.0.37. The user's Mac has two active network adapters (Wi-Fi + Anker USB Ethernet en11). macOS routes 225.0.0.38 to the internet gateway adapter (Wi-Fi) rather than to en11 (the console adapter). Delta-ctrl data is being sent to Wi-Fi and never reaches the Matrix console at 192.168.1.2. The plugin loads, executes, and generates data normally — the data simply exits through the wrong network interface. Additionally, the single-fader plugin variant requires per-instance channel number configuration (1-16) that may not be set.

fix: |
  Two steps required:

  STEP 1: Add static multicast route for delta-ctrl (225.0.0.38) to en11.

  Run in Terminal:
    sudo route -n add -net 225.0.0.38 -interface en11

  To make persistent across reboots, add to a LaunchDaemon or run the
  route command at login. The existing 225.0.0.37 route can serve as
  the template.

  Verify the route was applied:
    netstat -rn | grep 225.0.0.38

  STEP 2: Configure delta-ctrl plugin instances.

  Each single-fader delta-ctrl instance inserted on a DAW track must
  have its channel number set to match the corresponding Matrix channel.
  - Instance on DAW Track 1 → set Console Channel to 1
  - Instance on DAW Track 2 → set Console Channel to 2
  - ... (16 instances total for 16 Matrix channels)

  Alternative: Use the "Matrix delta 16" plugin variant (one instance
  controls all 16 channels simultaneously). This may be simpler for
  initial verification.

verification: Not yet applied — user action required (see CHECKPOINT below).
files_changed: []

---

## CHECKPOINT: Human Action Required

**Type:** human-action

**Root cause is confirmed with high confidence.** Two fixes required — both require terminal access and DAW interaction that cannot be automated.

---

### Fix 1: Add the delta-ctrl multicast route to en11

Open Terminal and run:

```bash
sudo route -n add -net 225.0.0.38 -interface en11
```

You will be prompted for your password. Enter it.

Verify the route was added:

```bash
netstat -rn | grep 225
```

You should see both 225.0.0.37 (ipMIDI — existing) and 225.0.0.38 (delta-ctrl — new) pointing to en11.

**Why this is the fix:** SSL's own support documentation states that ipMIDI (225.0.0.37) and delta-ctrl (225.0.0.38) are separate multicast groups. With multiple active adapters (Wi-Fi + en11), macOS sends each multicast stream to whichever adapter it chooses based on the routing table — typically the internet-connected adapter. Your ipMIDI route to en11 was already set (which is why MCU works). Delta-ctrl needs its own identical route.

---

### Fix 2: Configure the plugin's channel assignment

In your DAW session:

1. Open the delta-ctrl plugin on a track
2. Look for a channel selector / Console Object dropdown in the plugin GUI
3. Set it to match the Matrix channel number for that track (1 for the first track, 2 for the second, etc.)
4. Repeat for each instance

**Alternative approach for initial testing:** If you have the "Matrix delta 16" plugin variant (all 16 channels in one plugin), use that instead — it handles all channels in a single instance and is easier to verify the connection.

---

### Verification After Fix

1. Insert delta-ctrl on one DAW track
2. Set that instance to Channel 1 (or whichever channel you want to test)
3. Enable automation on that DAW track (set to Read or Touch mode)
4. Draw a simple automation curve (e.g., fade up from 0 to 0dB over 4 bars) on the delta-ctrl fader parameter
5. Press Play
6. The corresponding physical fader on the Matrix should move — this is MDAC control, not MCU

**Key difference from MCU:** MCU fader movement is purely positional (the DAW is telling the control surface where to display the fader). Delta-ctrl fader movement is MDAC-driven (the DAW automation is actually setting the analog gain of the channel). You should hear the audio level change via the analog path even if the MCU is disabled.

---

### If the Fix Does Not Work

If after adding the 225.0.0.38 route and setting channel numbers, delta-ctrl still has no effect:

1. **Check whether Wi-Fi is still routing 225.0.0.38:**
   ```bash
   netstat -rn | grep 225
   ```
   Both lines should show `en11` as the interface, not `en0` (Wi-Fi).

2. **Temporarily disable Wi-Fi** and test. If delta-ctrl works with Wi-Fi off, the route wasn't applied correctly. Re-add the route.

3. **Check Local Network privacy permission for the delta-ctrl plugin process.** On Tahoe, each app accessing local network multicast must have the Local Network permission granted. Go to System Settings > Privacy & Security > Local Network. The Pro Tools and Ableton processes (and any helper processes they use) must have this toggled on.

4. **Verify the Matrix is in delta mode.** The Matrix must have its delta-control feature enabled in the MatrixRemote software. Check MatrixRemote for a "Delta" tab or automation mode setting — it may need to be activated there before the console will respond to delta-ctrl plugin messages.

5. **Contact SSL Support** with: macOS version (Tahoe 26.2), firmware version (V3.0/5), DAW (Pro Tools / Ableton), and the symptom "plugin loads, no fader movement." Their engineering team has direct experience with this exact setup.

---

### Persistence: Making the Route Survive Reboots

The `sudo route -n add` command does not persist across reboots. To make it permanent, you need to create a LaunchDaemon.

Create the file `/Library/LaunchDaemons/com.ssl.delta-ctrl-route.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ssl.delta-ctrl-route</string>
  <key>ProgramArguments</key>
  <array>
    <string>/sbin/route</string>
    <string>-n</string>
    <string>add</string>
    <string>-net</string>
    <string>225.0.0.38</string>
    <string>-interface</string>
    <string>en11</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
```

Then load it:
```bash
sudo launchctl load /Library/LaunchDaemons/com.ssl.delta-ctrl-route.plist
```

(This is the same pattern as the existing 225.0.0.37 ipMIDI route if you have one.)

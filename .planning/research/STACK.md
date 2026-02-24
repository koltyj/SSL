# Stack Research

**Domain:** macOS hardware control bridge — SSL Matrix console to Pro Tools and Ableton Live via HUI/MIDI
**Researched:** 2026-02-24
**Confidence:** MEDIUM (protocol chain verified via official SSL docs; custom bridge library choices verified via GitHub/Swift Package Index; macOS Tahoe audio state MEDIUM due to known instability reports)

---

## Critical Protocol Facts (Read Before Stack)

The SSL Matrix's DAW control chain works like this:

```
SSL Matrix Console
       |
   Ethernet (RJ45)
       |
  ipMIDI driver (nerds.de) — multicast UDP to 225.0.0.37
       |
  CoreMIDI virtual ports (appear as MIDI I/O in macOS)
       |
  HUI protocol over these MIDI ports (2x 8-channel banks = 16 faders)
       |
  Pro Tools / Ableton Live
```

**Key finding:** The Matrix does NOT use raw USB-MIDI for DAW control. USB carries only keyboard/HID commands (soft key macros). DAW control (flying faders, HUI) travels over **Ethernet via ipMIDI**, which the console's Matrix Remote software configures. You must install ipMIDI on the Mac and configure multicast routing.

**HUI protocol facts (MEDIUM confidence — Wikipedia + multiple forum cross-references):**
- HUI is MIDI-based: SysEx, Control Change, Channel Pressure, and Note On/Off messages
- Bidirectional: DAW sends fader positions to console (motor control); console sends touch/move events back
- Fader resolution: 14-bit (MSB+LSB via two CC messages per channel)
- Meters: Channel Pressure, 4-bit nibble encoding channel + VU state
- 8 channels per HUI device; SSL Matrix uses 2 HUI devices for 16 channels (ipMIDI ports 1+2)
- Pro Tools is the canonical HUI host — designed for it
- Ableton Live supports HUI (confirmed via SSL's official Ableton profile guide)
- HUI ≠ Mackie Control Universal (MCU) — they are incompatible protocols despite surface similarity

---

## Recommended Stack

### Tier 1: Prerequisites (Configure Before Writing Any Code)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| ipMIDI (nerds.de) | Current (macOS arm64/intel64 native) | Exposes SSL Matrix Ethernet HUI ports to CoreMIDI | The Matrix uses multicast UDP MIDI over Ethernet; ipMIDI is the only macOS driver that implements this protocol. Without it, no CoreMIDI port appears for the console. |
| macOS network route config | N/A (shell command) | Directs multicast traffic to correct NIC | macOS will not auto-route 225.0.0.37 multicast to the Matrix's NIC; requires `sudo route -n add -net 225.0.0.37 -interface <NIC>` or `networksetup -setadditionalroutes` for persistence |
| MatrixRemote | SSL-current | Console network config and profile management | Configures which ipMIDI ports map to which HUI banks on the console; required to unlock DAW control mode |

### Tier 2: Core Framework for Custom Bridge Software

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Swift | 6.x (Xcode 16+) | Bridge application language | Native macOS, direct CoreMIDI access, zero GIL/GC pauses, Swift 6 concurrency model maps directly to real-time event handling. HUI fader latency must be under 10ms — Node.js GC jitter is a real risk, Python is worse. Swift compiles to native code. |
| MIDIKit (orchetect/MIDIKit) | 0.11.0 (Feb 2026) | Swift CoreMIDI wrapper + HUI protocol implementation | The only actively maintained Swift library with HUI protocol implementation in `MIDIKitControlSurfaces`. Version 0.11.0 released Feb 2, 2026. Swift 6 strict concurrency compliant. Supports macOS 10.13+. The HUI module implements both the host-side (DAW-facing) and surface-side (console-facing) roles — exactly what a bridge needs. |
| SwiftUI + AppKit | macOS SDK current | Status bar app UI for bridge configuration | Menu bar daemon pattern: no Dock icon, status bar item with popover for config. SwiftUI for the popover content, AppKit for `NSStatusItem`. Native, zero overhead, appropriate for a background utility. |

### Tier 3: Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| MIDIKitControlSurfaces | Included in MIDIKit 0.11.0 | HUI protocol parsing and generation | Always — this is the core HUI implementation. Use `HUISurface` for console-side behavior and `HUIHostBank` for DAW-side behavior. |
| Combine (Apple framework) | macOS SDK | Reactive event routing between HUI surface and host | Use for routing HUI events from surface to host and back. Fits naturally with MIDIKit's event model. Avoid third-party reactive frameworks here. |
| UserDefaults / PropertyList | macOS SDK | Persisting port assignments and configuration | Simple enough for the config surface — no database needed. |

### Tier 4: Development and Debugging Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Audio MIDI Setup (built-in macOS) | Verify CoreMIDI sees ipMIDI ports and SSL Matrix | Essential for debugging: confirms ipMIDI driver is working before writing any code |
| theMartzSound/HUI-MCU-Logger | Log raw HUI messages from DAW for reverse-engineering | Swift command-line tool; use this to verify what the DAW is actually sending when you press buttons or move faders |
| MIDIKit OSC Demos (in MIDIKit repo) | Reference architecture for CoreMIDI app structure | Study the included demo apps in MIDIKit repo for correct Swift concurrency + CoreMIDI patterns |
| Console.app | CoreMIDI error logging | CoreMIDI driver errors appear in system logs; essential for Tahoe compatibility debugging |
| Wireshark (with Ethernet capture) | Debug ipMIDI multicast traffic | Use if ipMIDI ports appear but HUI is not working — verify UDP packets are reaching the Mac on 225.0.0.37 |

---

## Installation

```bash
# 1. ipMIDI: Download from https://nerds.de/en/ipmidi_osx.html
#    Install, set port count to 9, disable loopback, reboot

# 2. Add multicast route (add to a login item or launchd plist for persistence)
sudo route -n add -net 225.0.0.37 -interface en0  # replace en0 with your NIC

# 3. For persistent multicast routing on macOS Tahoe (recommended over the above)
sudo networksetup -setadditionalroutes "USB 10/100/1000 LAN" 225.0.0.37 255.255.255.255 0.0.0.0

# 4. Swift bridge app — Swift Package Manager
# Package.swift dependency:
# .package(url: "https://github.com/orchetect/MIDIKit", from: "0.11.0")
# Products to import:
# MIDIKit, MIDIKitControlSurfaces

# 5. In Xcode, create macOS App target, set:
#    - Application is agent (LSUIElement = YES in Info.plist)
#    - Signing: requires "com.apple.security.temporary-exception.mach-lookup.global-name" for CoreMIDI
```

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| Swift + MIDIKit | Node.js + @julusian/midi | Node.js GC pauses (10-100ms) are incompatible with flying fader requirements. node-midi v3.6.1 is active and uses CoreMIDI, but no HUI implementation exists in the Node.js ecosystem — you'd write the entire HUI protocol layer from scratch. Electron adds Chromium overhead. Only viable if the team has no Swift experience and zero tolerance for learning it. |
| Swift + MIDIKit | Python + python-rtmidi + mido | Python GIL + interpreter overhead makes <5ms latency unreliable. python-rtmidi 1.5.8 uses CoreMIDI but no HUI library exists. hui_control_lib on GitHub has 1 commit, 1 star — not a real library. Python is good for prototyping protocol behavior, not for production flying fader latency. |
| Swift + MIDIKit | C++ + RtMidi | RtMidi (C++) is the underlying engine for all the above libraries. Maximum performance but no HUI implementation, no macOS app framework, enormous development overhead. Only justified if MIDIKit's HUI layer proves incomplete for your needs. |
| Swift + MIDIKit | Rust + midir | Rust has excellent MIDI I/O (midir crate), real-time performance, no GC. But zero HUI implementation exists in the Rust ecosystem, and macOS GUI for a status bar app requires bridging to AppKit anyway. High effort, no HUI shortcut. |
| SwiftUI menu bar app | Electron/web app | Web MIDI API requires browser context + user gesture for each connection — completely incompatible with a background daemon pattern. Electron wrapping a web app adds 150MB+ overhead for a bridge utility. |
| ipMIDI (paid, ~$50) | IDAM / RTP-MIDI (Apple's network MIDI) | Apple's built-in Network MIDI (RTP-MIDI) uses a different protocol than ipMIDI's multicast UDP. The SSL Matrix firmware sends ipMIDI-format packets specifically. Apple's network MIDI will not receive them. Cannot substitute. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Electron / web-based bridge | Chromium process overhead, Node.js GC, no background daemon without tricks, Web MIDI API not designed for always-on bridge use | Swift native menu bar app |
| Python for production bridge | GIL, interpreter jitter, no HUI library exists in Python ecosystem | Swift + MIDIKit |
| hui_control_lib (davisonaudio/GitHub) | 1 commit, 1 star, GPL-3.0, no releases, unclear what it even implements | MIDIKit's MIDIKitControlSurfaces |
| Raw CoreMIDI C API directly | Extremely verbose, error-prone, requires manual C interop boilerplate. MIDIKit wraps this cleanly with Swift 6 concurrency. | MIDIKit |
| USB as the DAW control path | SSL Matrix uses USB only for HID keyboard commands (soft key macros), NOT for HUI fader data. DAW control is Ethernet-only via ipMIDI. | Ethernet + ipMIDI |
| EUCON (Avid's protocol) | Pro Tools will conflict with EUCON when HUI devices are present — disables metering on HUI devices. SSL Matrix does not implement EUCON. | HUI over ipMIDI |
| macOS IAC Bus for internal routing | IAC adds an extra hop and latency vs. direct CoreMIDI virtual port connections. ipMIDI ports appear directly in CoreMIDI — connect directly. | Direct CoreMIDI port assignment |

---

## Stack Patterns by Variant

**If custom bridge software is needed (gaps in MatrixRemote coverage):**
- Use Swift 6 + MIDIKit 0.11.0 + MIDIKitControlSurfaces
- Pattern: `HUISurface` receives events from the console's ipMIDI ports; bridge translates and re-emits as `HUIHostBank` events on virtual CoreMIDI ports connected to Pro Tools/Ableton
- Run as a macOS menu bar agent (LSUIElement=YES, no Dock icon)
- Because: this is the minimum-latency, maximum-compatibility approach for a background daemon on macOS

**If only Pro Tools is needed (not Ableton):**
- MatrixRemote may cover all needs without custom software
- Pro Tools HUI is the canonical use case; SSL has official profiles for it
- Investigate this path first before building anything

**If Ableton Live HUI support proves incomplete via MatrixRemote:**
- Ableton's HUI implementation is less complete than Pro Tools'
- The bridge may need to translate HUI → MIDI CC or OSC for certain Ableton functions (automation arm, session view)
- OSC bridge pattern: use MIDIKit for HUI decode, emit OSC via Network.framework to Ableton's OSC port

**If ipMIDI fails on macOS Tahoe:**
- Fallback: Connect a MIDI interface (e.g., iConnectivity mio4) and patch the console's MIDI I/O directly
- This bypasses ipMIDI entirely; HUI travels over standard 5-pin DIN MIDI instead
- Performance is equivalent; latency may be slightly higher but reliable

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| MIDIKit 0.11.0 | macOS 10.13+, Xcode 16.0+, Swift 6.x | Released Feb 2, 2026. Swift 6 strict concurrency compliant. Current as of research date. |
| ipMIDI (nerds.de) | macOS arm64 + intel64 (native binary) | No stated Tahoe 26 compatibility — requires empirical testing. Trial: 60 days full functionality. |
| macOS Tahoe 26.2 | CoreMIDI framework (Apple) | Audio bugs present in 26.0 were fixed in 26.1. Tahoe 26.2 is the current version as of research date. MIDI routing reconfiguration reportedly needed after Tahoe upgrade. |
| Pro Tools | HUI controller: Setup > Peripherals > MIDI Controllers | EUCON must be disabled when using HUI devices — enabling EUCON disables HUI metering |
| Ableton Live | HUI via Control Surfaces preferences | Ableton HUI support is functional but less feature-complete than Pro Tools HUI |

---

## SSL Matrix — Protocol Architecture Summary

Based on SSL official documentation and setup guides (MEDIUM confidence):

```
Physical connections:
  Ethernet RJ45 → ipMIDI → CoreMIDI (HUI for faders, transport, mute, solo)
  USB-A to USB-B → HID keyboard events only (soft key macros, NOT faders)

DAW communication path:
  Console → ipMIDI multicast UDP → Mac NIC → ipMIDI driver → CoreMIDI port
  Pro Tools/Ableton ← CoreMIDI port ← HUI protocol ← ipMIDI port

ipMIDI configuration on Mac:
  - Port count: 9 (to support 4 DAW banks of 8 channels each + spare)
  - Loopback: disabled
  - Route: multicast 225.0.0.37 must be routed to Matrix NIC (not internet NIC)

Pro Tools HUI setup:
  - Setup > Peripherals > MIDI Controllers
  - HUI type, ipMIDI Port 1 (channels 1-8), ipMIDI Port 2 (channels 9-16)
  - EUCON disabled

Ableton Live HUI setup:
  - Preferences > Link/Tempo/MIDI > Control Surfaces
  - HUI type, Input/Output assigned to ipMIDI Port 1 and Port 2
  - SSL provides an "Ableton Standard" profile in MatrixRemote
```

---

## Open Questions / Validation Required

1. **ipMIDI on macOS Tahoe 26.2** — No confirmed reports of working or broken. Must test empirically. Highest risk item.
2. **MatrixRemote on macOS Tahoe 26.2** — No confirmed compatibility statement found. SSL's compatibility pages didn't mention Tahoe for Matrix (original, not Matrix 2). Must test.
3. **SSL Matrix firmware version** — User's firmware version is unknown. Some Matrix features and profile support vary by firmware. Check MatrixRemote connection to determine installed version.
4. **HUI completeness in MIDIKit** — Issue #136 was open and partially complete as of 2022. Version 0.11.0 (2026) claims HUI support but the exact feature completeness needs hands-on testing. The `HUIHostBank` API for hosting two 8-channel banks must be validated against actual Pro Tools fader moves.
5. **Ableton Live HUI automation write** — Ableton's HUI implementation may not support full automation write from motorized faders. This is a known limitation in the HUI/Ableton ecosystem that may require MIDI CC fallback.

---

## Sources

- SSL ipMIDI setup guide: https://livehelp.solidstatelogic.com/Help/ipMIDI.html — ipMIDI protocol details, multicast UDP 225.0.0.37, macOS route command (HIGH confidence — official SSL docs)
- SSL Pro Tools Matrix Profile guide: https://www.solidstatelogic.com/assets/uploads/downloads/matrix/ProTools-Standard-Matrix-Profile-Setup-Quick-Start-Guide.pdf — HUI port configuration, 2x 8-channel banks (MEDIUM confidence — official but couldn't fully parse PDF)
- SSL Live DAW Control docs: https://livehelp.solidstatelogic.com/Help/DAWControl.html — HUI/MCU protocol confirmation, ipMIDI port count (HIGH confidence — official SSL docs)
- MIDIKit GitHub: https://github.com/orchetect/MIDIKit — v0.11.0, Feb 2026, Swift 6 compliant, MIDIKitControlSurfaces module confirmed (HIGH confidence — official source)
- MIDIKit HUI issue: https://github.com/orchetect/MIDIKit/issues/136 — HUI implementation status, open issue with partial completion (MEDIUM confidence — GitHub issue thread)
- nerds.de ipMIDI for macOS: https://www.nerds.de/en/ipmidi_osx.html — arm64 native, 20 ports, 60-day trial (MEDIUM confidence — vendor page, no Tahoe version confirmation)
- Rogue Amoeba Tahoe audio bugs: https://weblog.rogueamoeba.com/2025/11/04/macos-26-tahoe-includes-important-audio-related-bug-fixes/ — audio bug fixes in Tahoe 26.1 (MEDIUM confidence — third-party but authoritative audio developer)
- HUI Wikipedia: https://en.wikipedia.org/wiki/Human_User_Interface_Protocol — protocol history, MIDI encoding, comparison with MCU (MEDIUM confidence — Wikipedia, cross-referenced with forum posts)
- @julusian/midi GitHub: https://github.com/Julusian/node-midi — v3.6.1 Aug 2024, active Node.js MIDI fork (HIGH confidence — GitHub, official source)
- Apple CoreMIDI docs: https://developer.apple.com/documentation/coremidi/ — framework existence confirmed, MIDI 2.0 support confirmed (HIGH confidence — official Apple docs)
- MixOnline SSL Matrix review: https://www.mixonline.com/technology/review-solid-state-logic-matrix-369393 — original Matrix Ethernet-only DAW path confirmation (MEDIUM confidence)

---

*Stack research for: SSL Matrix Console Control Bridge (macOS, HUI, Pro Tools, Ableton Live)*
*Researched: 2026-02-24*

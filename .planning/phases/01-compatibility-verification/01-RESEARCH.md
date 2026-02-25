# Phase 1: Compatibility Verification - Research

**Researched:** 2026-02-24
**Domain:** ipMIDI / macOS Tahoe 26.2 / MatrixRemote / SSL Matrix v1 hardware verification
**Confidence:** MEDIUM-HIGH (ipMIDI Tahoe compatibility now HIGH; MatrixRemote Tahoe status MEDIUM-LOW; Local Network permission bug MEDIUM)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Fallback Strategy**
- Primary path: Ethernet + ipMIDI (designed protocol path for the SSL Matrix)
- Fallback path: iConnectivity mioXL DIN MIDI interface (already connected to Mac and working, DIN MIDI cables on hand)
- Research must verify whether the Matrix's DIN MIDI ports carry HUI/MCU control data or only auxiliary MIDI — this determines whether the mioXL is a viable fallback for DAW control
- If ipMIDI fails on Tahoe 26.2, switch to mioXL testing the next day
- No OS downgrade considered — one of the two paths WILL work
- The mioXL also has Ethernet/RTP-MIDI capabilities (unused so far) — could be a third path if needed

**Verification Criteria**
- Full DAW test required — "ports visible in Audio MIDI Setup" is NOT sufficient
- Pro Tools 2025.x is the first DAW to verify with (canonical HUI target)
- Four behaviors must all pass to mark phase complete:
  1. Playing automation in Pro Tools moves physical faders on the Matrix
  2. Pressing transport buttons on Matrix controls Pro Tools playback
  3. Touching and moving a fader on Matrix writes automation into Pro Tools
  4. Pro Tools track names appear on Matrix scribble strips
- User will create a test session with simple fader automation for verification
- MIDI monitoring tools need to be installed as part of this phase (user doesn't have one)

**Console Inventory**
- Console is an original SSL Matrix v1 (not Matrix²)
- Firmware version is unknown — plan must include steps to check firmware via the console display
- No SD card in rear slot (stores MatrixRemote configs/profiles)
- Ethernet cable is connected from Matrix to a USB hub/dock that has a built-in Ethernet port
- Mac connects to Ethernet via a Thunderbolt adapter
- Network topology is unclear — must verify Matrix and Mac Ethernet are on the same network segment during setup
- ipMIDI multicast routing is a known pain point with multiple network adapters — Mac has Wi-Fi + Thunderbolt Ethernet + USB hub Ethernet, all of which could interfere

### Claude's Discretion
- Choice of MIDI monitoring tool (MIDI Monitor by Snoize is the standard macOS choice)
- Exact order of verification steps within the phase
- How to handle partial success (e.g., MIDI ports visible but faders don't move)
- Network troubleshooting approach if ipMIDI multicast doesn't route correctly

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FOUN-01 | ipMIDI driver installed and verified working on macOS Tahoe 26.2 | ipMIDI 2.0 explicitly lists macOS 26 Tahoe as supported on download page. Install, configure 9 ports, verify ipMIDI ports appear in Audio MIDI Setup > MIDI Studio. |
| FOUN-02 | Ethernet network configured with correct multicast routing for ipMIDI (225.0.0.37) | SSL official docs + prior research confirm this is the most common failure mode with multiple NICs. Static route must be added to Mac for 225.0.0.37 via Thunderbolt Ethernet adapter. |
| FOUN-03 | MatrixRemote communicating with SSL Matrix console over Ethernet | Requires: Matrix v1 correct software version (not Matrix 2 software), static IP or DHCP reservation for console, Local Network permission granted to MatrixRemote on Tahoe. |
| FOUN-04 | macOS Local Network permissions and Audio MIDI Setup verified for MIDI port visibility | Tahoe 26 has a documented Local Network permission bug for multicast UDP apps. Permissions must be explicitly granted and may need to be toggled after first boot. |
</phase_requirements>

---

## Summary

Phase 1 is a pure hardware and OS compatibility verification phase — no code is written. The goal is to confirm that the entire Ethernet/ipMIDI/MatrixRemote protocol stack operates correctly on macOS Tahoe 26.2 before any bridge software development begins.

**Updated status since initial project research:** ipMIDI 2.0's download page now explicitly lists macOS 26 Tahoe as a supported operating system, which upgrades the primary path from HIGH RISK to MEDIUM risk. The remaining risk is macOS Tahoe's documented Local Network permission bug for UDP multicast applications, which affects ipMIDI's multicast (225.0.0.37) and may require manual permission toggling after installation or reboot. This bug is present in Tahoe 26.x broadly but some users report it resolves in 26.1+.

MatrixRemote remains the key uncertainty. SSL has not published a Tahoe 26 compatibility statement for the original Matrix v1. The application is Java-based, which means Java runtime compatibility on Tahoe is a separate verification point from ipMIDI itself. Community reports confirm MatrixRemote worked on Ventura, and the general pattern suggests it continues to work on Sonoma and Sequoia, but Tahoe is unconfirmed by any community report found. The plan must account for this gap.

The network topology in this setup — Matrix → USB hub/dock Ethernet → (unknown) → Thunderbolt Ethernet to Mac, with Wi-Fi also active — is exactly the multi-NIC scenario SSL documents as the most common cause of "MatrixRemote connects but DAW control does not work." Mapping and controlling this is a required step before any DAW verification.

**Primary recommendation:** Execute verification in this order: (1) identify firmware version and download correct MatrixRemote, (2) install ipMIDI and handle Local Network permissions, (3) map and fix the network topology, (4) verify MIDI ports in Audio MIDI Setup, (5) connect MatrixRemote, (6) run DAW test with Pro Tools. Each step must pass before the next begins.

---

## Standard Stack

### Core (Phase 1 only — these are tools to install/configure, not develop)

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| ipMIDI (nerds.de) | 2.0 (current, explicit Tahoe 26 support) | Ethernet-to-CoreMIDI bridge exposing Matrix MIDI ports | The only macOS driver implementing the Matrix's multicast UDP MIDI protocol. Cannot be substituted with Apple's Network MIDI (RTP-MIDI) — different protocol. |
| MatrixRemote (SSL) | v1-series (must confirm for Matrix v1 hardware) | Console Ethernet configuration, DAW profile selection | Required to configure which ipMIDI ports map to which HUI banks. Without it, the console cannot be put into DAW control mode. |
| MIDI Monitor (Snoize) | Current (Tahoe confirmed compatible) | Observe raw MIDI traffic during verification | Free, authoritative, explicitly Tahoe-compatible. Allows confirming HUI heartbeat, fader messages, and transport commands are flowing correctly. |
| Pro Tools 2025.x | 2025.10+ (Tahoe 26.0-26.1 compatible per Avid) | First DAW target for HUI verification | Canonical HUI implementation. Phase requires four specific behaviors verified in Pro Tools. |

### Supporting (troubleshooting if needed)

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| Wireshark | Current | Capture raw UDP multicast to confirm 225.0.0.37 is routing to the correct NIC | If ipMIDI ports appear in Audio MIDI Setup but DAW receives no MIDI — use to trace whether packets are going to Wi-Fi instead of Matrix Ethernet |
| Terminal (route/networksetup) | macOS built-in | Add persistent multicast route to Thunderbolt Ethernet adapter | Required if Wireshark confirms multicast routing to wrong NIC |
| System Settings > Privacy & Security > Local Network | macOS built-in | Grant/revoke/re-grant Local Network permission to ipMIDI, MatrixRemote, Pro Tools | Required due to Tahoe 26 Local Network permission bug |
| Audio MIDI Setup (macOS built-in) | macOS built-in | Confirm ipMIDI ports appear as CoreMIDI ports in MIDI Studio | Definitive verification of FOUN-01 |

### Installation

```bash
# 1. ipMIDI: Download from https://nerds.de/en/download.html (macOS, version 2.0)
#    Mount DMG, install, reboot
#    Configure: System Settings > Sound (or the ipMIDI preference pane)
#    Set port count to 9, disable loopback

# 2. MIDI Monitor: Download from https://www.snoize.com/MIDIMonitor/
#    Free, no install required beyond dragging to Applications

# 3. MatrixRemote: Download from SSL support for original Matrix (NOT Matrix 2 page)
#    URL: https://support.solidstatelogic.com/hc/en-gb/articles/4407299066385-Matrix-Documents
#    Requires: Java runtime — install current JRE from Adoptium if not present

# 4. Pro Tools: Already installed (user's primary DAW)

# 5. Wireshark (optional, if multicast routing fails):
#    Download from https://www.wireshark.org/download.html
```

---

## Architecture Patterns

### Phase Structure

This phase has no code architecture — it is a sequential verification protocol with defined pass/fail criteria at each step. The planner should structure tasks as: gate steps (must pass before continuing) followed by verification steps (the four behaviors).

```
Phase 1 Flow:
├── Gate 1: Firmware identification (determines correct MatrixRemote version)
├── Gate 2: Software install (ipMIDI + MatrixRemote + MIDI Monitor)
├── Gate 3: Local Network permissions granted and stable on Tahoe
├── Gate 4: Network topology mapped and multicast route confirmed
├── Gate 5: ipMIDI ports visible in Audio MIDI Setup
├── Gate 6: MatrixRemote connects to console
└── Verification: Four DAW behaviors pass in Pro Tools
    ├── Automation playback → physical faders move
    ├── Transport buttons → Pro Tools playback control
    ├── Fader touch + move → automation written into Pro Tools
    └── Track names → appear on Matrix scribble strips
```

### Fallback Decision Tree

```
ipMIDI install attempt
    └── Tahoe Local Network permission bug → Toggle off/on in System Settings, restart apps
    └── Ports appear but multicast fails → Add static route (see pitfall below)
    └── Ports still absent → Check Console.app for kernel extension errors
    └── Cannot resolve → Activate mioXL DIN MIDI fallback path

MatrixRemote connect attempt
    └── Java runtime error → Install Adoptium JRE, relaunch
    └── Console not detected → Verify IP addressing (Matrix and Mac on same subnet)
    └── Connects but wrong layout → Wrong MatrixRemote version (Matrix 2 instead of v1)
    └── Cannot resolve → Ethernet path confirmed broken; use mioXL DIN fallback
```

### DIN MIDI Fallback Path (mioXL)

The context doc requires research on whether the Matrix's DIN MIDI ports carry HUI/MCU control data. Based on SSL documentation and the Matrix architecture:

**Finding:** The SSL Matrix original (v1) has standard 5-pin DIN MIDI In/Out ports on the rear panel. These ports ARE connected to the console's MIDI processing, but their function depends on the Matrix's internal routing and firmware configuration. SSL's documentation primarily describes the Ethernet/ipMIDI path for DAW control. DIN MIDI is documented as the physical layer but whether the Matrix routes full HUI protocol (faders, transport, scribble strips) or only auxiliary MIDI through the DIN ports is not definitively confirmed in available public documentation. **Confidence: LOW** — this must be empirically tested with the mioXL if the Ethernet path fails.

The mioXL DIN approach: connect Matrix DIN MIDI Out → mioXL MIDI In, Matrix DIN MIDI In ← mioXL MIDI Out. The mioXL then appears as a standard USB MIDI interface on macOS Tahoe. No ipMIDI required. If the Matrix sends full HUI over DIN, this path works identically to Ethernet from Pro Tools' perspective.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MIDI traffic inspection | Custom MIDI sniffer | MIDI Monitor (Snoize) | Free, CoreMIDI native, Tahoe compatible, industry standard |
| Network packet capture | Custom UDP listener | Wireshark | Wireshark captures kernel-level packets before any app filtering |
| Multicast routing | Custom routing daemon | `networksetup` CLI command (macOS built-in) | One terminal command adds a persistent static route; no daemon needed |
| IP address assignment for console | Network configuration script | Router DHCP reservation or static IP on Matrix | Simplest stable solution; Matrix has built-in IP config in its display menu |

**Key insight:** Phase 1 has zero custom software. Every tool needed is either free (MIDI Monitor, Wireshark, Terminal) or commercially available (ipMIDI, MatrixRemote). The only decision is configuration and verification order.

---

## Common Pitfalls

### Pitfall 1: macOS Tahoe Local Network Permission Bug for Multicast UDP

**What goes wrong:** After installing ipMIDI on Tahoe 26 and granting Local Network permission, the permission entry disappears from System Settings > Privacy & Security > Local Network after a reboot. The app no longer receives multicast UDP, and MIDI ports that previously appeared in Audio MIDI Setup are absent or non-functional. The app may or may not re-prompt for permission. This is a documented bug affecting multiple applications on Tahoe 26.x.

**Why it happens:** Apple's TCC (Transparency, Consent, and Control) system has a regression in Tahoe 26.x where Local Network permission records for UDP multicast-using apps are not reliably persisted. This was reported extensively in Apple Developer Forums and community threads as of late 2025.

**How to avoid:**
1. After granting permission, verify it persists after one reboot before concluding the phase is complete.
2. If permission disappears: open System Settings > Privacy & Security > Local Network, toggle the ipMIDI entry off then on, quit and relaunch ipMIDI and the DAW.
3. If permission entry is absent entirely: quit all affected apps, delete TCC database entries for ipMIDI via Terminal (`tccutil reset LocalNetwork`), relaunch ipMIDI and grant permission fresh.
4. Some users report the issue resolves after Tahoe 26.1 — ensure system is on 26.2 (current) before spending time debugging this.

**Warning signs:** MIDI ports were visible yesterday, absent today. MatrixRemote connects but MIDI is silent. Toggling Local Network permission temporarily fixes it.

**Recovery:** Toggle permission in System Settings. If that fails, `tccutil reset LocalNetwork <bundle-id>` for the affected apps.

---

### Pitfall 2: ipMIDI Multicast Routed to Wrong NIC (Multiple Adapters)

**What goes wrong:** This setup has at minimum three network interfaces — Wi-Fi, Thunderbolt Ethernet (to switch/Mac network), and the USB hub/dock's built-in Ethernet (connected to Matrix). macOS routes multicast 225.0.0.37 to the adapter with the best gateway route, which is almost certainly the internet-facing adapter (Wi-Fi or Thunderbolt Ethernet), not the Matrix's adapter. MatrixRemote may report the console connected while DAW control is completely silent — because MatrixRemote uses TCP to the console's IP, but ipMIDI uses UDP multicast which goes to the wrong adapter.

**SSL's own documentation** (https://support.solidstatelogic.com/hc/en-gb/articles/4408131999121) calls this "the most common cause of Remote app connects but DAW control does not work."

**How to avoid:**
1. First: map the network topology. Identify which macOS interface name (en0, en1, en2, en3) corresponds to the USB hub/dock Ethernet connected to the Matrix.
2. Add a static multicast route via the correct interface:
   ```bash
   # Find the interface connected to the Matrix's network segment:
   networksetup -listallhardwareports
   # Then add the route (use the correct interface name):
   sudo networksetup -setadditionalroutes "USB 10/100/1000 LAN" 225.0.0.37 255.255.255.255 0.0.0.0
   # Or with route command (not persistent across reboots):
   sudo route -n add -net 225.0.0.37 -interface en3
   ```
3. The `networksetup -setadditionalroutes` approach is more persistent but requires knowing the exact service name. The `route` command approach works immediately but needs to be re-run after reboot.

**Warning signs:** MatrixRemote shows "Matrix Connected - Matrix SN XXXX" but Pro Tools receives no HUI data. ipMIDI ports are visible in Audio MIDI Setup but MIDI Monitor shows no incoming traffic.

**Topology-specific risk:** The USB hub/dock Ethernet is an additional complication — USB hub network adapters sometimes have different multicast IGMP behavior than native Ethernet adapters. If routing to the hub's adapter still fails, try connecting the Matrix directly to the Thunderbolt Ethernet adapter with the Mac's normal network via Wi-Fi.

---

### Pitfall 3: Wrong MatrixRemote Software Version (Matrix v1 vs. Matrix 2)

**What goes wrong:** The SSL website's primary Matrix page (solidstatelogic.com/studio/matrix/downloads) now shows Matrix 2 software. If you download from there, you install MatrixRemote for Matrix 2, which will not recognize a Matrix v1 console. It either fails to connect or connects but shows incorrect configuration options.

**How to avoid:**
1. Go to the SSL Support portal: https://support.solidstatelogic.com/hc/en-gb/articles/4407299066385-Matrix-Documents — this is the original Matrix documents page, not Matrix 2.
2. Before downloading anything, physically identify the console as Matrix v1 (no "2" or "delta" marking on the chassis; original design circa 2010-2015).
3. The correct software for original Matrix is V2.0/6 (the version numbers reference the console firmware/software generation, not the Matrix 2 product). If SSL support redirects to the Matrix 2 page, contact SSL directly for the legacy download link.

**Warning signs:** MatrixRemote installs but shows wrong channel count, or cannot detect the console at all despite network connectivity.

---

### Pitfall 4: Network Topology Unknown — USB Hub/Dock Ethernet Segment

**What goes wrong:** The Matrix is connected to a USB hub/dock's built-in Ethernet port. The Mac connects to Ethernet via a Thunderbolt adapter. Whether these two Ethernet connections are on the same network segment (directly connected or via a switch between them) is unknown. If they are on different subnets, MatrixRemote cannot reach the Matrix and ipMIDI multicast will not route between them regardless of route configuration.

**How to avoid:**
1. Map the physical connections before any software configuration. Draw out: Matrix → [cable] → [device] → [cable] → Mac. Identify every device in the chain.
2. If the USB hub has a built-in switch and both ports are on the same switch, they are on the same segment — good.
3. If the USB hub connects to a different network than the Thunderbolt Ethernet, a simple unmanaged 5-port switch between Matrix and Mac will resolve this.
4. Check whether the Mac can ping the Matrix's IP (default is 192.168.1.x or similar — check Matrix display for its IP setting) using the Thunderbolt Ethernet interface.
5. Most studio USB hub/dock setups are directly connected, not routed — this is probably fine, but must be confirmed.

**Warning signs:** MatrixRemote shows "Searching for Matrix..." indefinitely. `ping <matrix-ip>` returns "no route to host."

---

### Pitfall 5: Java Runtime Not Installed or Wrong Version for MatrixRemote

**What goes wrong:** MatrixRemote is a Java application. macOS no longer ships with Java. If no Java runtime is installed, MatrixRemote will show an error on launch. If an old or incompatible Java version is installed, MatrixRemote may crash or show UI rendering issues.

**How to avoid:**
1. Before launching MatrixRemote, verify Java is installed: `java -version` in Terminal.
2. If absent or below version 11: install Adoptium Temurin JRE (free, current, macOS native): https://adoptium.net/
3. For Tahoe 26 specifically: use a modern JDK (17 or 21 LTS). Old Java 8 runtime has known issues on Apple Silicon and newer macOS.
4. MatrixRemote uses Java Swing for its UI — this may have rendering quirks on Retina displays but is functional.

**Warning signs:** Double-clicking MatrixRemote shows a dialog about needing Java, or the app bounces in the Dock then disappears without opening.

---

### Pitfall 6: EUCON Must Be Disabled Before HUI Testing in Pro Tools

**What goes wrong:** If EUCON (Avid's proprietary surface protocol) is enabled in Pro Tools peripherals, all HUI-connected surfaces lose their channel metering. The Matrix's meter bridge will show no signal even though transport, faders, and other controls work. This is a documented unresolved bug in Pro Tools.

**How to avoid:** Before any Pro Tools HUI testing in Phase 1, verify EUCON is disabled: Pro Tools > Setup > Peripherals > Ethernet Controllers — confirm EuControl is not active. Note: Avid's own Tahoe Known Issues page documents that EuControl/WSControl may not connect to the control surface on first boot — log out and back in as the stated workaround.

---

### Pitfall 7: Firmware Version Unknown — Must Be Identified Before Software Download

**What goes wrong:** The Matrix v1 has multiple firmware generations (V1.x, V2.x, V3.x on the Matrix 2 line). Different firmware versions may require different MatrixRemote versions. Installing a mismatched MatrixRemote can appear to connect but show wrong configuration options or fail to enable DAW control mode.

**How to identify firmware:**
- The Matrix displays its software version on the console's built-in alphanumeric display during bootup — watch for the version string during power-on.
- Once MatrixRemote connects to the console, the status bar shows "Matrix Connected - Matrix SN XXXX" — the firmware version may be reported in the connection log or About screen.
- The rear panel of the console has a label with the serial number; the firmware is separate and shown on the display.
- If firmware is unreadable during boot, hold the console's dedicated "version/info" button (varies by generation) during startup, or check the MatrixRemote application's About section after connection.

---

## Code Examples

This phase has no code. The only "commands" are shell commands for network routing:

### Check current multicast routing on macOS

```bash
# List all network interfaces and their service names
networksetup -listallhardwareports

# Show current routing table — look for 225.x.x.x entries
netstat -rn | grep 225

# Ping the Matrix from a specific interface (replace en3 with actual Matrix-facing interface)
# First find Matrix IP from its display menu, default is often 192.168.1.100
ping -I en3 <matrix-ip>
```

### Add persistent multicast route via networksetup

```bash
# Replace "USB 10/100/1000 LAN" with exact service name from listallhardwareports
# Replace "en3" with the interface name shown in the hardware ports list
sudo networksetup -setadditionalroutes "USB 10/100/1000 LAN" 225.0.0.37 255.255.255.255 0.0.0.0

# Verify it was applied
networksetup -getadditionalroutes "USB 10/100/1000 LAN"
```

### Add ephemeral multicast route via route command (survives until reboot)

```bash
sudo route -n add -net 225.0.0.37 -interface en3
```

### Reset Local Network permissions if permission entry disappears on Tahoe

```bash
# Reset all Local Network permissions — all apps will need to re-grant on next launch
tccutil reset LocalNetwork

# Or reset only for a specific app bundle identifier (preferred — more targeted)
# For ipMIDI — find bundle ID: codesign -d -r- /path/to/ipMIDI.app
tccutil reset LocalNetwork <ipMIDI-bundle-identifier>
```

### Verify ipMIDI ports appear as CoreMIDI sources

```bash
# List MIDI sources via command line (requires CoreMIDI tools)
# Use MIDI Monitor GUI instead — this is for quick terminal check
system_profiler SPMIDIDataType
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ipMIDI without Tahoe support | ipMIDI 2.0 with explicit Tahoe 26 support | Late 2025 (post-Tahoe release) | Removes the highest-risk unknown from the project; primary path is now probably viable |
| No Local Network permission requirement | macOS Sequoia+ requires explicit Local Network permission for UDP multicast apps | macOS 15 Sequoia (2024), continued in Tahoe | Adds a configuration step; has a known bug in Tahoe 26.x that requires manual intervention |
| Pro Tools with EUCON + HUI coexisting | EUCON disabled required for HUI metering | Long-standing known bug, unresolved | Must disable EUCON before Phase 1 DAW verification |
| macOS routing multicast automatically | Static multicast route required with multiple NICs | Always true but more common with multi-adapter setups | Required configuration step, documented by SSL officially |

---

## Open Questions

1. **MatrixRemote compatibility with macOS Tahoe 26.2**
   - What we know: MatrixRemote worked on Ventura (community reports); SSL has not published Tahoe 26 compatibility for original Matrix v1; the app is Java-based
   - What's unclear: Whether any Tahoe-specific Java or macOS behavior breaks MatrixRemote; whether the USB hub/dock Ethernet topology affects Java's network binding
   - Recommendation: Attempt install and connection as Gate 6 in the plan; if it fails, check SSL support page for any new Tahoe statement, then contact SSL support; MatrixRemote is not strictly required for HUI to work (it configures the profile, but if a profile is already loaded in the console it persists)

2. **Do the Matrix v1's DIN MIDI ports carry full HUI protocol?**
   - What we know: Matrix has 5-pin DIN MIDI In/Out on the rear panel; these are connected to the console's MIDI processing
   - What's unclear: Whether the console routes full HUI (faders, scribble strips, transport) through the DIN ports or uses them only for auxiliary MIDI or configuration
   - Recommendation: If Ethernet path fails, connect the mioXL and attempt to configure Pro Tools HUI on the mioXL's USB MIDI ports; if faders don't move, DIN is auxiliary-only and mioXL becomes the bridge layer requiring custom code (Phase 2 problem)
   - **This question only needs to be answered if Ethernet/ipMIDI fails**

3. **Matrix v1 firmware version**
   - What we know: Unknown; must be identified before downloading MatrixRemote
   - What's unclear: Whether the console's current firmware is compatible with current MatrixRemote for v1, and whether an SD card is required for profile storage
   - Recommendation: Power-on observation is the first step in the plan; if firmware cannot be read from display, connect and check MatrixRemote's connection log

4. **Local Network permission stability on Tahoe 26.2**
   - What we know: There is a documented bug in Tahoe 26.x where Local Network permissions for multicast UDP apps can disappear or become non-functional after reboot; some users report it improves on 26.1+; user is on 26.2
   - What's unclear: Whether 26.2 (current) has addressed this bug vs. 26.1 reports
   - Recommendation: Grant permissions, reboot once, verify they persist before concluding Gate 3 is passed; if they disappear, use `tccutil reset LocalNetwork` and re-grant

---

## Sources

### Primary (HIGH confidence)

- nerds.de ipMIDI download page (https://www.nerds.de/en/download.html) — ipMIDI 2.0 explicitly lists "macOS 26 Tahoe" and "macOS 10.12 Sierra" as supported operating systems; ARM64 and intel64 native
- Avid KB: macOS Tahoe support for Avid software (https://kb.avid.com/pkb/articles/compatibility/macOS-Tahoe) — Pro Tools 2025.10+ compatible with macOS Tahoe 26.0-26.1
- Avid KB: Pro Tools Known Issues on Tahoe (https://kb.avid.com/pkb/articles/compatibility/Pro-Tools-support-with-macOS-Known-Issues) — EuControl first-boot connectivity issue documented; HUI not specifically mentioned
- snoize.com/MIDIMonitor — MIDI Monitor explicitly lists Tahoe as a supported macOS version
- SSL Support: Remote app connects but DAW control does not work (https://support.solidstatelogic.com/hc/en-gb/articles/4408131999121) — ipMIDI multicast routing to wrong NIC is the documented primary failure mode
- SSL Support: ipMIDI and Multiple Network Adapters (https://support.solidstatelogic.com/hc/en-gb/articles/4408132028305) — official multicast routing guidance
- Prior project research: .planning/research/PITFALLS.md, STACK.md, SUMMARY.md — all prior research incorporated

### Secondary (MEDIUM confidence)

- Apple Developer Forums thread 809211 — Local Network permission bug on Tahoe 26.x affecting UDP multicast apps; toggling permission as workaround documented
- Apple Community thread 256051137 — Intermittent multicast socket failures "errno 65 - no route to host" on macOS 15 Sequoia and Tahoe; toggling Local Network permission as temporary fix
- GitHub: home-assistant/iOS issue 4192 — macOS Tahoe 26.x app doesn't request Local Network permission; permission entry disappearing after reboot documented
- Community reports (WebSearch synthesis) — MatrixRemote working on Ventura (2023); Sequoia/Sonoma status unclear; Tahoe unconfirmed

### Tertiary (LOW confidence, mark for validation)

- Research finding re: DIN MIDI ports on Matrix v1 carrying HUI — not definitively confirmed by official SSL documentation; requires empirical testing if Ethernet path fails
- matrixRemote for Matrix v1 download URL — SSL support page may require login or may redirect; must be validated during plan execution

---

## Metadata

**Confidence breakdown:**
- ipMIDI Tahoe 26 support: HIGH — explicitly listed on nerds.de download page as of research date
- Local Network permission bug: MEDIUM — widely reported, multiple sources, but 26.2-specific fix status unclear
- MatrixRemote Tahoe compatibility: LOW-MEDIUM — no community confirmation; Java-based with unknown Tahoe status
- Pro Tools 2025.x on Tahoe: HIGH — Avid official KB confirms 2025.10+
- Multicast routing with multiple NICs: HIGH — SSL's own documentation names this the primary failure mode
- DIN MIDI port capability for HUI: LOW — not definitively documented; requires empirical testing
- Network topology (USB hub/dock): LOW — unknown until physically mapped during execution

**Research date:** 2026-02-24
**Valid until:** 2026-04-24 (60 days — ipMIDI and macOS release stable; LocalNetwork bug may evolve with point releases)

# Pitfalls Research

**Domain:** Hardware console control bridge (SSL Matrix + HUI + macOS + Pro Tools + Ableton Live)
**Researched:** 2026-02-24
**Confidence:** HIGH (most findings from official SSL documentation, Avid KB, and verified community forums)

---

## Critical Pitfalls

### Pitfall 1: Flying Fader Feedback Loop (Motor Fight)

**What goes wrong:**
The fader sends a position message to the DAW. The DAW receives it and immediately echoes the position back to the console to confirm. The console receives the echo and treats it as a new fader move, sending it back again. The motor and the incoming position message fight each other, causing the fader to jitter, buzz, or lock up.

**Why it happens:**
Implementors mirror all incoming MIDI back to the output without understanding the HUI touch-sense architecture. HUI uses a touch-sense bit to signal whether the user's hand is on the fader. The correct behavior is: only echo fader position back to the surface *after* a touch-release event, not while the fader is actively being touched. Without this gate, the feedback loop is immediate.

Additionally, if the SSL Matrix's MIDI output port is accidentally enabled as a MIDI input *and* a MIDI thru is active anywhere in the chain, any fader move gets looped continuously.

**How to avoid:**
- Gate all outbound fader-position messages behind touch-sense state. When touch is active (user holding fader), suppress incoming DAW position updates to that fader channel.
- Never enable the Matrix's MIDI port as a Track input in Pro Tools or Ableton. Explicitly exclude it from all MIDI thru paths.
- In any MIDI bridge code, maintain a per-fader `isTouched` boolean. Only send DAW-to-surface fader updates when `isTouched == false`.
- Test with a MIDI monitor (MIDI Monitor.app) to verify no runaway message stream exists before connecting motors.

**Warning signs:**
- Fader buzzes, vibrates, or moves in an oscillating pattern
- Fader refuses to stay at a position when set from the DAW
- MIDI monitor shows rapidly alternating duplicate messages on the same CC/pitch address
- CPU usage spikes from MIDI processing

**Phase to address:** HUI communication phase (initial bridge implementation), specifically the fader echo architecture design.

---

### Pitfall 2: HUI Heartbeat Failure Causes Silent Disconnection

**What goes wrong:**
The HUI protocol requires a continuous heartbeat exchange. The DAW sends a ping (`0x90 0x00 0x00`) approximately every second. The surface must respond with a pong (`0x90 0x00 0x7F`). If the DAW stops receiving pongs for approximately 2 seconds, it marks the surface offline and stops sending automation data. Faders freeze. The user gets no obvious error — things just stop working.

**Why it happens:**
Developers implement the HUI data path but forget the heartbeat entirely, or implement it but handle it on a thread that gets blocked by other processing. Because HUI was reverse-engineered (not officially documented by Mackie/Digidesign), many implementations miss this requirement. Pro Tools will show an "Unable to communicate with HUI" dialog, but this only appears after the timeout, and sometimes gets suppressed by the user clicking "Don't show again."

**How to avoid:**
- Implement heartbeat on a dedicated timer with ~1 second interval, isolated from the main MIDI processing thread.
- Log every missed pong with a timestamp. If 2 consecutive pongs are missed, surface reconnection logic should trigger.
- Never block the heartbeat thread with heavy processing.
- In a custom bridge, ensure the bridge itself relays heartbeat messages bidirectionally — if you're sitting between the console and Pro Tools, you must pass through or regenerate the heartbeat.

**Warning signs:**
- Faders work initially then stop responding after ~2-5 seconds
- Pro Tools shows "Pro Tools is unable to communicate with HUI" dialog
- Console appears connected (lights on) but DAW ignores input
- Heartbeat exchange visible in MIDI monitor initially, then disappears

**Phase to address:** HUI protocol implementation phase. Must be the first thing verified after establishing any MIDI connection.

---

### Pitfall 3: EUCON Conflict Disables HUI Metering in Pro Tools

**What goes wrong:**
If EUCON (Avid's proprietary control surface protocol) is enabled in Pro Tools peripherals, all HUI-connected surfaces lose metering. The channel meters on the SSL Matrix stop working entirely. This is an undocumented bug in Pro Tools that has existed since at least Pro Tools 11. It affects all HUI devices (Matrix, Nucleus, AWS, Duality, Mackie products, Icon, Behringer X-Touch, etc.).

**Why it happens:**
Pro Tools has a conflict in how it initializes metering for HUI when EUCON is also initialized. The exact root cause is internal to Pro Tools and has never been officially addressed by Avid. It is documented as a known issue in SSL's own HUI setup guides.

**How to avoid:**
- If using the SSL Matrix exclusively via HUI, disable EUCON completely in Pro Tools: Setup > Peripherals > Ethernet Controllers — disable EuControl.
- Verify EUCON is disabled *before* troubleshooting any metering issues.
- If EUCON is needed for other surfaces simultaneously, accept that HUI metering will not work and use in-DAW metering only.

**Warning signs:**
- All other HUI functions (faders, transport, mute, solo) work normally but channel meters are frozen or absent
- Problem appears only after installing EuControl software or enabling it in Peripherals

**Phase to address:** Pro Tools integration setup phase, before any HUI testing begins.

---

### Pitfall 4: macOS Tahoe USB Class-Compliant Audio Regression

**What goes wrong:**
macOS Tahoe 26.0 introduced a confirmed regression in the generic USB Audio Class driver, causing some class-compliant USB devices to be detected in System Information but ignored by CoreAudio. Devices show in USB tree but do not appear in Audio MIDI Setup. This affects class-compliant interfaces broadly and may affect the SSL Matrix's USB connection if it relies on the generic class-compliant stack rather than a proprietary driver.

The Tahoe 26.0 regression was partially addressed in 26.1, but specific device compatibility depends on whether the device firmware speaks USB Audio Class 1.1 or 2.0.

**Why it happens:**
Apple changed the USB audio stack in Tahoe 26. Devices relying on older USB Audio Class 1.1 are most affected. The Matrix is a legacy device (original design ~2010) and likely uses an older USB audio/MIDI implementation.

**How to avoid:**
- Do not test on Tahoe 26.0. Ensure the system is on 26.1 or higher before any MIDI/USB testing.
- Verify the Matrix appears in Audio MIDI Setup > MIDI Studio before any other configuration.
- If the Matrix is absent from MIDI Studio, test with a known-working class-compliant MIDI device to isolate whether the issue is macOS-wide or Matrix-specific.
- Have the physical MIDI I/O ports (DIN MIDI) configured as a fallback route for HUI if USB proves unreliable on Tahoe.

**Warning signs:**
- SSL Matrix USB device appears in System Information > USB but not in Audio MIDI Setup
- No MIDI ports visible for the Matrix in DAW preferences
- Issue appears after an OS update but not before

**Phase to address:** Initial connectivity and OS compatibility phase. This must be resolved before any protocol work begins.

---

### Pitfall 5: ipMIDI Multicast Routing to Wrong Network Adapter

**What goes wrong:**
The SSL Matrix sends ipMIDI (MIDI over Ethernet) as multicast UDP. On a Mac with multiple active network adapters (Wi-Fi, Ethernet to console, Ethernet to router, Thunderbolt bridge, etc.), macOS routes multicast to whichever adapter is listed first in the routing table — typically the internet-connected adapter, not the console-connected adapter. DAW control appears connected but all MIDI data goes nowhere. MatrixRemote may appear to connect while DAW control is completely silent.

**Why it happens:**
macOS determines multicast routing automatically based on the default gateway. If Wi-Fi or a second Ethernet port has a gateway configured, multicast traffic defaults to that path. The SSL console's dedicated Ethernet port has no gateway and therefore loses the routing election.

SSL explicitly documents this as the most common cause of "Remote app connects but DAW control does not work."

**How to avoid:**
- The cleanest solution: connect everything (console, Mac, router) to a single unmanaged switch and disable all other network adapters except the one connected to that switch.
- If multiple adapters must remain active, add a persistent static multicast route via terminal: `sudo networksetup -setadditionalroutes <adapter-name> 225.0.0.0 255.255.0.0 127.0.0.1`. Note: this route is not persistent across reboots on macOS without a startup script.
- Avoid 10G network adapters for the console connection — they have known IGMP multicast handling issues. Use a 1G adapter.
- Do not use TP-Link TL-SG105 or TL-SG108E switches — they have documented IGMP multicast problems with ipMIDI.

**Warning signs:**
- MatrixRemote shows console connected, but DAW receives no fader or transport control
- Swapping to a single active network adapter fixes the issue immediately
- ipMIDI Monitor shows traffic but DAW sees nothing

**Phase to address:** MatrixRemote/Ethernet configuration phase. This is the first thing to verify when setting up the Ethernet path.

---

### Pitfall 6: HUI 14-Bit Fader Position: Acting on Incomplete Messages

**What goes wrong:**
HUI fader positions are 14-bit values transmitted as two separate 7-bit MIDI bytes (MSB then LSB). If the bridge code processes and acts on the MSB byte before the LSB arrives, it produces wildly wrong intermediate positions — a fader targeted at position 8000 will briefly jump to 16256 (MSB only, LSB=0), causing a visible fader snap before settling. At high update rates (automation playback), this manifests as fader jitter or erratic movement.

**Why it happens:**
Implementors process MIDI messages as they arrive on a per-byte or per-message basis without tracking message pairs. Standard MIDI note-on style handling doesn't account for the paired nature of HUI's 14-bit fader data. The HUI spec sends LSB *first* to minimize perceived latency, which runs counter to most developers' intuition about MSB-first encoding.

**How to avoid:**
- Buffer fader messages in pairs. Only compute and act on the final position after both MSB and LSB have been received for the same fader channel.
- Note: the HUI protocol transmits LSB before MSB — implement the pair-collection logic in that order.
- Internal fader resolution in the HUI hardware is 9-bit; the lower 5 bits of the LSB are set by the hardware itself. Account for this in any position validation.

**Warning signs:**
- Faders briefly jump to wrong position before settling
- At fast automation playback speeds, faders appear to stutter or vibrate
- Logging shows position values wildly outside expected range on first byte receipt

**Phase to address:** HUI protocol implementation phase, during fader position decoding development.

---

### Pitfall 7: SSL Matrix Firmware vs. MatrixRemote Version Mismatch

**What goes wrong:**
The Matrix original (v1) console firmware is incompatible with the newer Matrix Remote application designed for Matrix 2. Installing the wrong version of MatrixRemote results in a silent failure where the app either cannot connect or connects but all configuration options are wrong for the console. Since the project states the firmware version is unknown, this is an active risk.

**Why it happens:**
SSL released the original Matrix and the Matrix 2 as distinct products with different firmware branches. The remote applications are not cross-compatible. Without knowing the console's firmware version, installing the most recent MatrixRemote from SSL's website will install the Matrix 2 version, which will not work with a Matrix v1 console.

**How to avoid:**
- Before any software installation, physically identify the console model and check the firmware version from the console's internal menu system.
- Download MatrixRemote from the specific product page for the original Matrix, not the Matrix 2 page.
- The original Matrix remote software is at a different download location than the Matrix 2 software. Confirm with SSL support which version is current for the v1 hardware.

**Warning signs:**
- MatrixRemote installs but cannot detect console
- Console detected but configuration pages show wrong channel counts or unavailable features
- SSL support confirms incompatible software version

**Phase to address:** MatrixRemote configuration phase, as the very first step.

---

### Pitfall 8: Ableton Live Has No Native HUI Support

**What goes wrong:**
Ableton Live does not natively implement the HUI protocol as a built-in control surface type. Pro Tools is HUI's native environment. Attempting to configure the SSL Matrix as a HUI device directly in Ableton Live preferences will fail — there is no HUI option. Without a workaround, the Matrix cannot send automation to Ableton or receive fader feedback from it via HUI.

**Why it happens:**
Ableton Live was designed around its own control surface script architecture (Python scripts) and MCU protocol. HUI was created by Mackie/Digidesign for Pro Tools compatibility and Ableton never implemented it natively. The SSL Matrix's profile system supports HUI for Pro Tools and MCU for other DAWs, but Ableton's MCU implementation and the Matrix's MCU mode have distinct behavioral differences from HUI.

**How to avoid:**
- Use the Matrix's MCU (Mackie Control Universal) profile for Ableton Live, not HUI. The Matrix supports both and MCU is what Ableton natively understands.
- Verify what the Matrix's MCU profile exposes vs. the HUI profile — fader behavior and display mapping differ.
- A custom MIDI bridge that translates HUI to Ableton-compatible MIDI CC or MCU messages is the alternative if MCU doesn't provide the needed control.
- Do not expect identical behavior between Pro Tools (HUI) and Ableton Live (MCU) paths — they will have different fader scaling, display behavior, and automation mode capabilities.

**Warning signs:**
- No "HUI" or "SSL Matrix" appears in Ableton's control surface dropdown
- Ableton receives MIDI from the Matrix but ignores it as a control surface
- Faders in Ableton don't respond to physical moves on the Matrix

**Phase to address:** Ableton Live integration phase. Requires separate design from the Pro Tools HUI path.

---

### Pitfall 9: macOS Local Network Privacy Permission Blocks ipMIDI

**What goes wrong:**
Starting with macOS Sequoia (15) and continuing in Tahoe (26), macOS prompts applications to request Local Network access for any network-based communication. Applications like ipMIDI, MatrixRemote, and Pro Tools's network control features require this permission explicitly granted. If the permission prompt was missed, dismissed, or corrupted during a system upgrade, DAW control via Ethernet will silently fail even though the physical connection is intact.

**Why it happens:**
Apple added Local Network privacy as a TCC (Transparency, Consent, and Control) system requirement. Unlike USB MIDI which doesn't need this permission, Ethernet-based MIDI (ipMIDI multicast) counts as local network access. The permission can appear to be granted but fail to propagate correctly after major OS upgrades.

**How to avoid:**
- After any macOS upgrade, verify: System Settings > Privacy & Security > Local Network — confirm that MatrixRemote, Pro Tools, and any MIDI bridge application have the toggle enabled.
- If connection issues appear after an OS upgrade, toggle the Local Network permission off and back on for each affected app, then restart the app.
- Be aware that some background daemons or helper processes may need separate permission grants.

**Warning signs:**
- ipMIDI-based DAW control stops working after a macOS upgrade
- MatrixRemote connects to the console but no MIDI data flows
- Toggling the network interface off/on fixes it temporarily

**Phase to address:** macOS Tahoe compatibility phase, during initial Ethernet/MatrixRemote setup.

---

### Pitfall 10: CoreMIDI Callback Thread Safety Violations

**What goes wrong:**
CoreMIDI delivers incoming MIDI messages on a dedicated high-priority real-time thread. If custom bridge code modifies shared state (arrays, queues, counters) from both the CoreMIDI callback thread and the main thread without synchronization, the result is undefined behavior — crashes, corrupted messages, or silent data loss. This is particularly dangerous because it's non-deterministic: the code appears to work in testing but fails randomly in production, often under automation playback load when message rates are high.

**Why it happens:**
Developers used to single-threaded JavaScript or Python environments don't instinctively guard shared data with locks or lock-free structures. CoreMIDI's documentation warns about this but the warning is easy to overlook. Using standard Swift `Dictionary` or `Array` from both threads without synchronization is a common mistake.

**How to avoid:**
- All shared state accessed from both CoreMIDI callback and main/application threads must use a lock-free mechanism (ring buffer, `os_unfair_lock`, or DispatchQueue with serial execution).
- Do not perform UI updates, file I/O, or memory allocation inside the CoreMIDI MIDIReadProc callback. Queue events for processing off the real-time thread.
- Do not use `DispatchQueue.main.sync` from the CoreMIDI thread — this will deadlock.
- Use Instruments' Thread Sanitizer (TSan) during development to catch races early.

**Warning signs:**
- Crashes with `EXC_BAD_ACCESS` in CoreMIDI-related code under load
- Intermittent dropped MIDI messages that only occur during heavy automation playback
- Behavior changes based on message rate (works at low rate, fails under load)

**Phase to address:** Custom bridge software development phase. Design the threading model before writing any message handling code.

---

### Pitfall 11: ipMIDI Port Enumeration Bug After Adding/Removing MIDI Devices

**What goes wrong:**
There is a documented bug in SSL's ipMIDI implementation where the port list in the control software shifts (moves up or down by one position) whenever a USB MIDI device is added or removed from the system — even a device unrelated to the console. This causes all ipMIDI-to-DAW port assignments to silently de-sync. DAW control stops working, and the fix requires either reconfiguring the port mapping in the SSL control application or rebooting the Matrix console.

**Why it happens:**
The SSL control software enumerates MIDI ports in order and stores port assignments by index, not by stable identifier. When any MIDI device change occurs (USB device plugged in, Bluetooth MIDI device connects, system MIDI service restarts), the port indices shift and the stored index no longer points to the correct port.

**How to avoid:**
- Minimize the number of MIDI devices connected to the system. Plug all MIDI hardware in before booting and avoid hot-plugging.
- If DAW control stops working without any apparent cause, check port assignment in ipMIDI Monitor before spending time on deeper debugging.
- Create a documented startup sequence: console on first, then Mac, then launch MatrixRemote and DAW in that order — consistency reduces enumeration-order variation.

**Warning signs:**
- DAW control working one session, inexplicably broken the next
- Works after a reboot but fails again after adding/removing an unrelated MIDI device
- ipMIDI Monitor shows ports but DAW assignment points to the wrong one

**Phase to address:** MatrixRemote/Ethernet configuration phase. Document the port enumeration issue in the startup procedure.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode HUI port names instead of discovering them dynamically | Simpler initial code | Breaks when any MIDI device is added/removed (ipMIDI port shift bug) | Never |
| Process fader MSB immediately without waiting for LSB | Simpler per-message code | Causes fader snap/jitter on every automation playback | Never |
| Skip heartbeat implementation initially | Faster to first fader movement | HUI goes offline after 2 seconds silently | Never |
| Disable touch-sense gating "temporarily" for testing | Easier to reason about | Creates feedback loops that are hard to disable once habit sets in | Testing only, never in production path |
| Use a single serial queue for all MIDI processing | Avoids threading complexity | Creates backpressure that causes heartbeat timeouts under automation load | MVP only if load stays minimal |
| Ignore MCU path and force HUI for Ableton | Consistent protocol | Ableton Live will not work as a HUI control surface — dead end | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Pro Tools HUI | Leaving EUCON enabled alongside HUI | Disable EUCON in Setup > Peripherals > Ethernet Controllers before any HUI testing |
| ipMIDI / MatrixRemote | Assuming one Ethernet adapter is enough | Explicitly disable all non-console network adapters or add static multicast routes |
| Ableton Live | Configuring SSL Matrix as HUI device | Use MCU profile on the Matrix for Ableton; HUI is not natively supported in Live |
| macOS MIDI permissions | Assuming permissions from previous OS version persist | After any OS upgrade, verify Local Network permissions for all relevant apps |
| HUI on two DAWs simultaneously | Routing same MIDI port to both Pro Tools and Ableton | Use separate virtual MIDI ports or physical ports per DAW; they cannot share a single HUI port |
| SSL Matrix USB | Assuming it will appear in MIDI Studio automatically on Tahoe | Verify device appears in Audio MIDI Setup > MIDI Studio before any other configuration |
| MatrixRemote version | Installing latest MatrixRemote from SSL site | Confirm Matrix hardware version (v1 vs. v2) before downloading software |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Processing MIDI on main thread | Heartbeat timeouts under heavy automation, fader lag | Use dedicated MIDI processing thread/queue | When automation has >16 simultaneous moving faders |
| Re-allocating memory inside CoreMIDI callback | Sporadic audio glitches coinciding with fader moves | Pre-allocate all buffers before starting MIDI session | From the start — memory allocation is not real-time safe |
| Using Wi-Fi for ipMIDI | Inconsistent fader response latency (10-100ms variance) | Dedicated wired Ethernet only for console connection | Immediately — Wi-Fi multicast behavior is unreliable |
| Using managed switch with ipMIDI | MIDI data not forwarded or delayed | Use unmanaged switch; managed switches may block or throttle multicast | Configuration-dependent, can work but unpredictable |

---

## "Looks Done But Isn't" Checklist

- [ ] **HUI heartbeat:** Pong response verified in MIDI monitor — not just "faders work for 10 seconds" but sustained communication over 60+ seconds.
- [ ] **Fader feedback loop:** Verified with MIDI monitor that fader moves do not echo back to console while touch is active. Test by watching MIDI output while automation plays.
- [ ] **EUCON disabled:** Pro Tools Peripherals > Ethernet Controllers confirms EuControl is not active when using HUI.
- [ ] **ipMIDI multicast routing:** After any OS boot with multiple network adapters active, confirm DAW control works — not just MatrixRemote connection.
- [ ] **Ableton MCU vs HUI:** Confirmed which profile the Matrix is using for Ableton, and that it's MCU, not HUI.
- [ ] **Port enumeration stability:** Added and removed an unrelated USB MIDI device and confirmed DAW control still works afterward.
- [ ] **macOS permissions:** After Tahoe installation or upgrade, Local Network permission verified for each relevant application.
- [ ] **Firmware/software version match:** Confirmed SSL Matrix hardware version and corresponding correct MatrixRemote version.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Feedback loop activated | LOW | Disconnect console USB, restart both DAWs, reconnect — then fix the touch-sense gate in code |
| HUI heartbeat lost | LOW | Pro Tools > Setup > Peripherals — remove and re-add HUI device |
| EUCON conflict | LOW | Pro Tools > Setup > Peripherals > Ethernet Controllers — disable EuControl, restart Pro Tools |
| ipMIDI multicast routing failure | MEDIUM | Disable and re-enable the correct network adapter, or run routing table command; restart MatrixRemote and DAW |
| Tahoe USB regression | HIGH | If Matrix absent from MIDI Studio on Tahoe 26.0, upgrade to 26.1+; if persists, switch to DIN MIDI fallback path |
| Port enumeration shift | LOW | Open ipMIDI Monitor, reassign to correct port, restart Matrix if needed |
| Firmware/software mismatch | MEDIUM | Identify hardware revision, download correct software version from SSL, reinstall |
| Local Network permission | LOW | System Settings > Privacy & Security > Local Network — toggle off/on for affected apps, restart apps |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Flying fader feedback loop | HUI bridge implementation | MIDI monitor shows no runaway messages during automation playback |
| HUI heartbeat failure | HUI protocol implementation | 60-second sustained connection test without "unable to communicate" dialog |
| EUCON conflict | Pro Tools setup | Metering works on Matrix while Pro Tools is running HUI |
| Tahoe USB regression | OS/hardware compatibility | Matrix appears in Audio MIDI Setup > MIDI Studio on Tahoe |
| ipMIDI multicast routing | Ethernet/MatrixRemote setup | DAW control works on fresh boot with Wi-Fi also active |
| HUI 14-bit fader encoding | HUI protocol implementation | Fader moves smoothly without snap at every automation step |
| Firmware/software mismatch | MatrixRemote configuration (first step) | MatrixRemote detects console and shows correct 16-channel layout |
| Ableton HUI not supported | Ableton integration design | Matrix controls Ableton faders via MCU profile |
| Local Network permission | macOS compatibility | DAW control survives a full system reboot on Tahoe |
| CoreMIDI thread safety | Custom bridge development | TSan reports zero races; bridge survives 30min automation stress test |
| ipMIDI port enumeration bug | MatrixRemote configuration | DAW control works after plugging in an unrelated USB MIDI device |

---

## Sources

- [SSL Matrix General FAQ (SSL Support)](https://support.solidstatelogic.com/hc/en-gb/articles/4415895478417-Matrix-General-FAQ)
- [SSL — AWS, Duality, Matrix and Nucleus Windows and macOS Compatibility](https://support.solidstatelogic.com/hc/en-gb/articles/9050560656413-AWS-Duality-Matrix-and-Nucleus-Windows-and-macOS-Compatibility)
- [SSL — Nucleus/Sigma/Matrix IP address configuration](https://support.solidstatelogic.com/hc/en-gb/articles/4408131882641-Nucleus-Sigma-Matrix-AWS-and-Duality-IP-address-configuration)
- [SSL — ipMIDI and Multiple Network Adapters](https://support.solidstatelogic.com/hc/en-gb/articles/4408132028305-Multiple-network-adapters-ipMIDI-and-Delta-Control)
- [SSL — Remote app connects but DAW control does not work](https://support.solidstatelogic.com/hc/en-gb/articles/4408131999121-The-Remote-app-connects-but-DAW-control-does-not-work)
- [SSL — Integrating ipMIDI with existing networks](https://support.solidstatelogic.com/hc/en-gb/articles/4408132183185-Integrating-ipMIDI-Delta-Control-or-multiple-consoles-with-existing-networks)
- [SSL DAW Control Help — ipMIDI](https://livehelp.solidstatelogic.com/Help/ipMIDI.html)
- [Mackie HUI MIDI Protocol reverse-engineering document (htlab.net)](https://htlab.net/computer/protocol/mackie-control/HUI.pdf)
- [Production Expert — Using a HUI Based Control Surface With Pro Tools](https://www.production-expert.com/home-page/2019/3/3/using-a-hui-based-control-surface-with-pro-tools-you-must-read-this)
- [Avid — Pro Tools support with macOS Known Issues (Tahoe/Sequoia)](https://kb.avid.com/pkb/articles/compatibility/Pro-Tools-support-with-macOS-Known-Issues)
- [Avid Pro Audio Community — HUI control surface bug](https://duc.avid.com/showthread.php?t=420225)
- [Icon Pro Audio — Pro Tools Unable to Communicate With HUI](https://support.iconproaudio.com/hc/en-us/articles/212136747-PRO-TOOLS-In-Pro-Tools-A-Message-Appears-Saying-Pro-Tools-Is-Unable-To-Communicate-With-HUI)
- [Gearspace — SSL Matrix Ethernet connection](https://gearspace.com/board/high-end/1237723-ssl-matrix-ethernet-connection.html)
- [Gearspace — SSL Matrix with Mac OS Ventura](https://gearspace.com/board/music-computers/1407268-ssl-matrix-mac-os-ventura-anyone.html)
- [MOTUnation — HUI stuck fader MIDI loop](https://www.motunation.com/forum/viewtopic.php?f=1&t=16680)
- [Music Tribe Community — HUI Mode faders resetting](https://community.musictribe.com/t5/Mixing/HUI-Mode-faders-resetting/m-p/244541)
- [Apple Community — USB Microphone / class-compliant regression macOS Tahoe](https://discussions.apple.com/thread/256152219)
- [Rogue Amoeba — macOS 26 Tahoe audio-related bug fixes](https://weblog.rogueamoeba.com/2025/11/04/macos-26-tahoe-includes-important-audio-related-bug-fixes/)
- [MacReports — Audio crackling on macOS Tahoe](https://macreports.com/audio-crackling-pops-or-drop-outs-on-mac-after-updating-to-macos-tahoe-26/)
- [MOTU — MOTU and macOS Tahoe compatibility](https://motu.com/en-us/news/motu-and-macos-tahoe/)
- [timur.audio — Using locks in real-time audio processing safely](https://timur.audio/using-locks-in-real-time-audio-processing-safely)
- [Apple Developer — CoreMIDI documentation](https://developer.apple.com/documentation/coremidi/)
- [GitHub MIDIKit — HUI Protocol Support issue](https://github.com/orchetect/MIDIKit/issues/136)
- [Ableton — Using Control Surfaces](https://help.ableton.com/hc/en-us/articles/209774285-Using-Control-Surfaces)
- [Ableton Forum — How HUI?](https://forum.ableton.com/viewtopic.php?t=236264)
- [Eclectic Light — How local network privacy could affect you](https://eclecticlight.co/2026/01/14/how-local-network-privacy-could-affect-you/)
- [SSL Matrix Software Update Install Notes (V2.0)](https://s3.amazonaws.com/sonicc/uploads/SSL-Matrix-2-Analog-Recording-Console-Software-Update-Install-Notes.pdf)

---
*Pitfalls research for: SSL Matrix HUI/MIDI bridge on macOS Tahoe*
*Researched: 2026-02-24*

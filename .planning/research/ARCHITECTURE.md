# Architecture Research

**Domain:** Hardware console control bridge — SSL Matrix + macOS + Pro Tools + Ableton Live
**Researched:** 2026-02-24
**Confidence:** MEDIUM-HIGH (protocol mechanics HIGH, Ableton/HUI distinction HIGH, macOS threading MEDIUM, MatrixRemote internals LOW due to inaccessible official docs)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SSL Matrix Console                           │
│   16x Motorized Faders  │  Transport  │  Mute/Solo  │  VPots       │
└────────────┬────────────────────────────────────────────────────────┘
             │ Two physical connections
             ├─── USB (keyboard emulation + HUI carrier for some setups)
             └─── Ethernet (ipMIDI — primary DAW control path)
                       │ Multicast UDP 225.0.0.37:21928
                       │ Emulates multi-port MIDI interface via ipMIDI driver
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    macOS CoreMIDI Layer                              │
│  ipMIDI driver registers virtual MIDI ports in Audio MIDI Setup     │
│  Matrix appears as: ipMIDI Port 1-N (up to 20 ports)               │
│  USB appears as: SSL Matrix USB MIDI device (class compliant)       │
└───────────┬──────────────────────────────────────────────────────┬──┘
            │ CoreMIDI API                                         │
            ▼                                                      ▼
┌───────────────────────┐                            ┌────────────────────────┐
│   Bridge Application  │                            │  MatrixRemote (Java)   │
│   (Custom Software)   │                            │  Ethernet only         │
│                       │                            │  Console configuration │
│  ┌─────────────────┐  │                            │  routing / recall      │
│  │ HUI Engine      │  │                            │  NOT DAW control       │
│  │ (Pro Tools)     │  │                            └────────────────────────┘
│  ├─────────────────┤  │
│  │ MCU Engine      │  │
│  │ (Ableton Live)  │  │
│  ├─────────────────┤  │
│  │ Console State   │  │
│  │ Manager         │  │
│  ├─────────────────┤  │
│  │ Message Router  │  │
│  └────────┬────────┘  │
└───────────┼───────────┘
            │ Forks MIDI messages
            ├──────────────────────────────────────────┐
            ▼                                          ▼
┌───────────────────────┐                  ┌───────────────────────┐
│   Pro Tools           │                  │   Ableton Live        │
│   HUI Peripheral 1    │                  │   Mackie Control      │
│   HUI Peripheral 2    │                  │   (MCU protocol)      │
│   (8 ch per HUI)      │                  │                       │
└───────────────────────┘                  └───────────────────────┘
```

### Critical Protocol Split

**Pro Tools uses HUI.** Pro Tools was designed with HUI; it is the native protocol.

**Ableton Live does NOT support HUI.** Ableton Live only supports Mackie Control Universal (MCU). This is a hard constraint confirmed by community testing — the Mackie Baby HUI protocol is incompatible with Ableton Live.

The SSL Matrix supports both HUI and MCU modes per layer, which means it can present as HUI to Pro Tools and MCU to Ableton Live simultaneously via separate ipMIDI ports.

---

## Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| ipMIDI Driver | Transport SSL Matrix MIDI over Ethernet via multicast UDP | nerds.de ipMIDI kernel extension; native ARM64 |
| HUI Engine | Encode/decode HUI protocol for Pro Tools; manage keepalive ping (90 00 00 every ~1s); handle zone/port addressing | MIDIKit `MIDIKitControlSurfaces` module |
| MCU Engine | Encode/decode Mackie Control Universal for Ableton; pitchbend fader messages; LCD updates | MIDIKit or raw CoreMIDI |
| Console State Manager | Single source of truth for all 16 fader positions, mute states, solo states, automation modes | In-memory state model; updated from both directions |
| Message Router | Receives MIDI from Matrix, dispatches to correct DAW engine; receives DAW automation data and forwards to Matrix | Event-driven dispatch |
| Bridge Application Shell | Menu bar app (stays resident), manages engine lifecycle, provides status UI | SwiftUI + MenuBarExtra |

---

## Recommended Project Structure

```
ssl-bridge/
├── Sources/
│   ├── SSLBridgeApp/              # SwiftUI app entry point, menu bar
│   │   ├── App.swift              # NSApplicationDelegateAdaptor, MenuBarExtra
│   │   └── MenuBarView.swift      # Status indicators, connect/disconnect
│   ├── BridgeCore/                # Protocol-agnostic orchestration
│   │   ├── BridgeEngine.swift     # Top-level coordinator; owns all sub-engines
│   │   ├── ConsoleStateManager.swift  # Canonical state store for 16ch
│   │   └── MessageRouter.swift    # Routes MIDI between hardware and DAWs
│   ├── HUIEngine/                 # Pro Tools HUI implementation
│   │   ├── HUIHostSession.swift   # Manages HUI host-to-surface comms
│   │   ├── HUISurfaceSession.swift # Manages surface-to-host (fader moves)
│   │   └── HUIKeepalive.swift     # 1s ping timer; offline detection
│   ├── MCUEngine/                 # Ableton Live MCU implementation
│   │   ├── MCUSession.swift       # Manages MCU host and surface comms
│   │   └── MCUFaderEncoder.swift  # Pitchbend ↔ fader position encoding
│   ├── ConsoleLayer/              # SSL Matrix hardware interface
│   │   ├── MatrixMIDIInterface.swift  # CoreMIDI port management
│   │   └── ipMIDIPortConfig.swift     # ipMIDI port assignment constants
│   └── Shared/
│       ├── ChannelState.swift     # Value type: fader pos, mute, solo, auto mode
│       └── MIDIMessageQueue.swift # Lock-free SPSC queue for RT safety
├── Tests/
│   ├── HUIEngineTests/
│   ├── MCUEngineTests/
│   └── ConsoleStateTests/
├── Package.swift
└── .planning/
```

### Structure Rationale

- **BridgeCore/:** Protocol-agnostic layer keeps HUI and MCU engines replaceable without changing routing logic
- **HUIEngine/ vs MCUEngine/:** Separate modules because HUI and MCU are fundamentally different protocols — different keepalive mechanisms, different fader encoding, different button addressing
- **ConsoleStateManager:** A single canonical model prevents the two DAW engines from fighting over console state; all updates flow through it
- **MIDIMessageQueue:** Lock-free queue isolates the CoreMIDI real-time thread from the application logic thread

---

## Architectural Patterns

### Pattern 1: Dual-Engine Fan-Out

**What:** The bridge maintains two active protocol sessions simultaneously — one HUI session targeting Pro Tools and one MCU session targeting Ableton Live. When the console sends a fader move, the router fans the update out to both DAW engines. Each engine translates and forwards only what its DAW understands.

**When to use:** Required because Pro Tools and Ableton Live use incompatible protocols. There is no single protocol that addresses both.

**Trade-offs:** State divergence is possible if one DAW updates track state while the other doesn't. The ConsoleStateManager must be the authoritative source and reconcile conflicts.

**Example:**
```swift
// MessageRouter.swift
func handleConsoleFaderMove(channel: Int, position: UInt16) {
    // Update canonical state
    stateManager.update(channel: channel, faderPosition: position)

    // Fan out to both DAW engines
    huiEngine.sendFaderPosition(channel: channel, position: position)
    mcuEngine.sendFaderPosition(channel: channel, position: position)
}
```

### Pattern 2: Lock-Free MIDI Thread Isolation

**What:** CoreMIDI delivers callbacks on a real-time thread. Application logic (state updates, SwiftUI) lives on the main thread or Swift actors. A lock-free single-producer/single-consumer queue (SPSC) bridges the two without blocking.

**When to use:** Any time CoreMIDI callback data must reach application-level code. Blocking the MIDI callback thread causes glitches, dropped messages, and latency.

**Trade-offs:** SPSC queues require that exactly one thread writes and one thread reads. For multiple readers, use separate queues or a different dispatch strategy.

**Example:**
```swift
// Real-time thread (CoreMIDI callback)
func midiReceived(_ message: MIDIMessage) {
    inboundQueue.enqueue(message)  // lock-free, non-blocking
}

// Application thread (polled via DispatchSourceTimer or async loop)
func processPendingMessages() {
    while let msg = inboundQueue.dequeue() {
        messageRouter.handle(msg)
    }
}
```

### Pattern 3: Keepalive State Machine (HUI-specific)

**What:** HUI requires a ping message (90 00 00) sent every ~1 second. If the HUI device doesn't receive a ping within 2 seconds, it goes offline and stops responding. The HUI session must maintain a timer and track round-trip ping responses to detect disconnections.

**When to use:** Always when implementing HUI host mode. This is not optional.

**Trade-offs:** Adds a timer thread. If the timer fires late (thread scheduling) the console can briefly disconnect. Use high-priority timer dispatch.

**Example:**
```swift
// HUIKeepalive.swift
class HUIKeepalive {
    private var timer: DispatchSourceTimer?

    func start() {
        timer = DispatchSource.makeTimerSource(queue: .global(qos: .userInteractive))
        timer?.schedule(deadline: .now(), repeating: .milliseconds(1000))
        timer?.setEventHandler { [weak self] in
            self?.sendPing()  // 90 00 00
        }
        timer?.resume()
    }

    private func sendPing() {
        midiOutput.send([0x90, 0x00, 0x00])
    }
}
```

### Pattern 4: Automation Mode State per Channel

**What:** Each of the 16 console channels maintains its own automation mode (Off, Read, Touch, Latch, Write, Trim). These states determine how fader moves are handled. On Touch: fader moves update DAW until released, then reverts. On Latch: fader moves persist after release. The bridge must track per-channel automation mode and signal the correct behavior to the DAW.

**When to use:** Required for real automation writing — without this, fader moves are just CC data with no write context.

**Trade-offs:** Automation modes differ slightly between Pro Tools and Ableton; the ConsoleStateManager must abstract over these differences.

---

## Data Flow

### Console Fader Move → DAW (Surface to Host)

```
Console Hardware
    │ Physical fader moved (touch detected)
    ▼
ipMIDI multicast UDP (LAN)
    │ MIDI packets arrive at nerds.de ipMIDI kernel driver
    ▼
CoreMIDI (macOS)
    │ Delivers to registered input port callback (real-time thread)
    ▼
Lock-Free Inbound Queue (MIDIMessageQueue)
    │ Enqueue — non-blocking
    ▼
Application Thread (polled)
    │ Dequeue and route
    ▼
MessageRouter.handleConsoleFaderMove()
    │ Parse: HUI zone/port pair OR MCU pitchbend → channel + position
    ├──→ ConsoleStateManager.update(channel, faderPosition)
    ├──→ HUIEngine.sendFaderPosition() → Pro Tools MIDI out
    └──→ MCUEngine.sendFaderPosition() → Ableton Live MIDI out
```

### DAW Automation Playback → Console (Host to Surface)

```
DAW (Pro Tools or Ableton Live)
    │ Automation playback sends fader position on MIDI out
    ▼
CoreMIDI (macOS)
    │ Arrives on bridge's registered input from DAW port
    ▼
Lock-Free Inbound Queue
    ▼
MessageRouter.handleDAWFaderUpdate(source: .proTools or .abletonLive)
    │ Decode position
    ├──→ ConsoleStateManager.update() — resolve conflicts if both DAWs send
    └──→ MatrixMIDIInterface.sendFaderPosition()
            │ Re-encode as HUI host command (for Matrix in HUI mode)
            ▼
        ipMIDI UDP → Console motors move to position
```

### Conflict Resolution (Both DAWs Sending Simultaneously)

When both Pro Tools and Ableton Live are playing automation that sends fader position commands, the bridge must have a policy. Recommended: last-write wins with a per-channel timestamp, plus a configurable "focus DAW" preference for the active mixing session.

### HUI vs MCU Message Encoding

| Event | HUI Encoding | MCU Encoding |
|-------|-------------|-------------|
| Fader position (host → surface) | SysEx `F0 00 00 66 05 00 ... F7` with zone addressing | Pitch Bend message (0xE0 + channel), 14-bit |
| Fader position (surface → host) | Zone select + port on/off pair sequence | Pitch Bend message identical to host→surface |
| Fader touch | Note On zone 0 port 0 | Note 68 + ch (touch) / Note On velocity 0 (release) |
| Mute | Zone/port button press pair | Note On 0x10 + channel |
| Transport Play | Zone 0x0F specific port | Note On 0x5E |
| Keepalive ping | Note On 0x90 0x00 0x00 | Not required |

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| SSL Matrix (hardware) | CoreMIDI via ipMIDI driver | Matrix presents as virtual MIDI ports; no proprietary API needed |
| ipMIDI driver (nerds.de) | Kernel extension; auto-registers MIDI ports | Must be installed; macOS Tahoe compatibility needs verification |
| Pro Tools | MIDI Peripheral: HUI, receive/send port pair in Peripherals dialog | Max 4 HUI peripherals = 32 channels; SSL Matrix uses channels 1-8 and 9-16 on separate HUI ports |
| Ableton Live | Control Surface: Mackie Control in Preferences → MIDI | Requires MCU mode on Matrix layer; separate ipMIDI port from HUI |
| MatrixRemote | Separate Java app; independent Ethernet connection; NOT bridged | Handles console routing and recall only; no bridge needed |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CoreMIDI RT thread ↔ BridgeCore | Lock-free SPSC queue | NEVER hold locks or allocate on RT thread |
| HUIEngine ↔ ConsoleStateManager | Direct method calls, Swift actor | ConsoleStateManager is the actor; engines call update methods |
| MCUEngine ↔ ConsoleStateManager | Direct method calls, Swift actor | Same actor, serializes concurrent updates |
| BridgeEngine ↔ SwiftUI | @Published / Combine or @Observable | Status, connection state, channel meters |
| BridgeEngine ↔ MatrixMIDIInterface | Direct; owns the CoreMIDI client | MatrixMIDIInterface is not concurrent — single client |

---

## Anti-Patterns

### Anti-Pattern 1: Treating HUI and MCU as Interchangeable

**What people do:** Configure the SSL Matrix in HUI mode for all DAWs, then wonder why Ableton doesn't respond.

**Why it's wrong:** Ableton Live does not implement HUI. It implements MCU. These are different protocols with different message formats, keepalive requirements, and addressing schemes. HUI messages are entirely invisible to Ableton's control surface layer.

**Do this instead:** Configure two separate SSL Matrix layers — one in HUI mode targeting Pro Tools (ipMIDI ports 1-2), one in MCU mode targeting Ableton Live (ipMIDI port 3). The bridge application handles the translation difference internally.

### Anti-Pattern 2: Blocking on the CoreMIDI Callback Thread

**What people do:** Perform state lookups, dictionary updates, or async dispatch from inside the CoreMIDI message callback.

**Why it's wrong:** CoreMIDI callbacks fire on a real-time thread. Any blocking, locking, or memory allocation causes jitter. At 128 MIDI messages/sec during automation playback, even 1ms of blocking is audible as fader stutter.

**Do this instead:** Use a lock-free queue (SPSC ring buffer) to shuttle messages from the RT thread to the application thread. Process the queue on a high-priority DispatchQueue with a timer or continuation loop.

### Anti-Pattern 3: Letting Both DAW Engines Write Console State Independently

**What people do:** HUIEngine and MCUEngine each maintain their own model of fader positions and update the console hardware directly.

**Why it's wrong:** When both Pro Tools and Ableton send automation data simultaneously, the console faders oscillate between two conflicting positions. There is no authoritative state and no conflict resolution.

**Do this instead:** All state writes go through ConsoleStateManager (single actor). ConsoleStateManager decides which update wins (focus DAW, last-write, or user preference), then issues one command to the console hardware.

### Anti-Pattern 4: Polling the Console Instead of Event-Driven

**What people do:** Periodically query the console hardware for current fader positions via polling loop.

**Why it's wrong:** Console hardware does not support polling — it is a MIDI device that pushes events. Polling causes latency proportional to poll interval and wastes CPU. HUI/MCU are purely event-driven protocols.

**Do this instead:** Register CoreMIDI input callbacks. The console pushes all state changes (fader moves, button presses) as MIDI events. The bridge is purely reactive.

### Anti-Pattern 5: Using USB Instead of Ethernet for DAW Control

**What people do:** Connect SSL Matrix via USB and route HUI over the USB MIDI connection.

**Why it's wrong:** The SSL Matrix USB connection is primarily a USB keyboard emulator (soft keys send keyboard shortcuts to the computer). While there is a USB MIDI aspect, SSL's primary and recommended architecture for HUI/MCU DAW control is ipMIDI over Ethernet. USB is supplementary.

**Do this instead:** Configure Ethernet first. Use ipMIDI driver for all HUI and MCU communication. Use USB only for keyboard-emulated shortcuts (macros, transport shortcuts that map to keyboard commands).

---

## Suggested Build Order

Build in this sequence because each layer depends on the previous one being stable:

```
Phase 1: Transport and Protocol Verification
    ├── Install and validate ipMIDI driver on macOS Tahoe 26.2
    ├── Configure SSL Matrix Ethernet (static IP or DHCP reservation)
    ├── Verify Matrix appears as ipMIDI ports in Audio MIDI Setup
    └── Confirm USB MIDI class compliance recognized by macOS

Phase 2: HUI Engine (Pro Tools first — HUI is the core protocol)
    ├── Implement CoreMIDI input/output port setup
    ├── Implement HUI keepalive (ping every 1s, detect offline)
    ├── Implement fader move surface→host (zone/port decode)
    ├── Implement fader position host→surface (automation playback)
    ├── Implement mute/solo/transport buttons
    └── Validate end-to-end with Pro Tools in a test session

Phase 3: Console State Manager
    ├── Define ChannelState value type (16 channels)
    ├── Implement Swift actor with update/read methods
    ├── Wire HUI engine events through state manager
    └── Write unit tests for state update logic

Phase 4: MCU Engine (Ableton Live)
    ├── Implement MCU session on separate ipMIDI port
    ├── Implement pitchbend fader encoding (14-bit)
    ├── Wire through ConsoleStateManager (no direct console access)
    ├── Implement transport and button mapping
    └── Validate end-to-end with Ableton Live

Phase 5: Bridge App Shell
    ├── SwiftUI MenuBarExtra (stays resident)
    ├── Connection status per DAW (connected/disconnected indicator)
    ├── Focus DAW selector (conflict resolution preference)
    └── Launch-at-login LaunchAgent configuration

Phase 6: Hardening
    ├── Reconnection logic (DAW restart, console power cycle)
    ├── Error logging and diagnostics
    └── Real-world session testing (automation read/write)
```

**Why this order:**
- Phase 1 before all else because if ipMIDI doesn't work on Tahoe 26.2, the entire architecture changes
- Phase 2 before Phase 4 because HUI is the harder protocol (keepalive, zone/port addressing) — solve the hard problem first
- Phase 3 between Phase 2 and 4 because the state manager needs to exist before MCU can write through it
- Phase 5 last because the shell is cosmetic; core functionality must work first

---

## Real-Time Constraints

| Constraint | Target | Why |
|------------|--------|-----|
| Fader latency (console → DAW) | < 5ms | At 5ms, fader stutter is imperceptible to human touch |
| DAW automation → console motor | < 10ms | Motors are slow mechanical devices; DAW automation jitter is the bottleneck, not MIDI |
| HUI keepalive period | 1000ms nominal, < 2000ms max | HUI goes offline at 2s; use 1s interval with 100ms jitter tolerance |
| MIDI callback processing | < 0.1ms | Must not block the RT callback; lock-free queue enqueue is ~10ns |
| State manager update | < 1ms | Swift actor serialization; acceptable for control surface (not audio) data |

MIDI control data (HUI/MCU) is not audio — it is not subject to audio buffer deadlines. However, fader position data at 100 updates/second with 5ms latency is the practical target for a console to feel "live" rather than laggy.

---

## Scaling Considerations

This is a single-machine, single-user application. Scaling in the traditional sense does not apply. Relevant operational constraints:

| Concern | Approach |
|---------|----------|
| 16 channels (full Matrix) | Two HUI peripherals in Pro Tools (8ch each); one MCU session in Ableton (up to 8 banks of 8) |
| Console power cycle | Detect MIDI port disappearance via CoreMIDI notification; auto-reconnect with exponential backoff |
| DAW restart | Same: CoreMIDI port disappears, bridge detects, re-establishes when port reappears |
| macOS update breaks ipMIDI | Critical risk — monitor nerds.de for Tahoe-compatible ipMIDI updates; document fallback (IAC bus + USB) |
| Adding a third DAW (Logic, etc.) | Architecture supports it — add a third engine, wire through ConsoleStateManager |

---

## Sources

- [HUI Protocol — Wikipedia](https://en.wikipedia.org/wiki/Human_User_Interface_Protocol) — MEDIUM confidence (secondary source but widely cited)
- [Mackie HUI MIDI Protocol Reverse Engineering (Cockos Forums)](https://forum.cockos.com/showthread.php?t=101328) — MEDIUM confidence (community reverse engineering, well-validated)
- [HUI Protocol Reverse Engineering PDF](https://htlab.net/computer/protocol/mackie-control/HUI.pdf) — MEDIUM confidence (reverse-engineered; matches MIDIKit implementation)
- [MCU Protocol Specification — TouchMCU](https://github.com/NicoG60/TouchMCU/blob/main/doc/mackie_control_protocol.md) — HIGH confidence (detailed community documentation, matches multiple independent implementations)
- [MIDIKit — orchetect/MIDIKit](https://github.com/orchetect/MIDIKit) — HIGH confidence (actively maintained Swift library; supports HUI, MIDI 2.0, Swift 6)
- [MIDIKit HUI Protocol Support Issue](https://github.com/orchetect/MIDIKit/issues/136) — HIGH confidence (implementation details from library author)
- [ipMIDI for macOS — nerds.de](https://nerds.de/en/ipmidi.html) — HIGH confidence (official product page; ARM64 native confirmed)
- [SSL Live DAW Control Architecture](https://livehelp.solidstatelogic.com/Help/DAWControl.html) — HIGH confidence (official SSL documentation)
- [SSL Matrix General FAQ](https://support.solidstatelogic.com/hc/en-gb/articles/4415895478417-Matrix-General-FAQ) — HIGH confidence (official SSL support)
- [Ableton Live: Mackie Baby HUI Not Supported](https://forum.ableton.com/viewtopic.php?t=241657) — HIGH confidence (community validation; consistent with Ableton's control surface script architecture)
- [Pro Tools HUI Setup — Sweetwater](https://www.sweetwater.com/sweetcare/articles/instructions-setting-up-hui-protools/) — MEDIUM confidence (third-party, matches Avid documentation pattern)
- [SSL Matrix Pro Tools Quick Start Guide](https://www.solidstatelogic.com/assets/uploads/downloads/matrix/ProTools-Standard-Matrix-Profile-Setup-Quick-Start-Guide.pdf) — HIGH confidence (official SSL document; PDF unreadable but URL references confirmed by search)
- [CoreMIDI Modern Swift Event Handling](https://furnacecreek.org/blog/2024-04-06-modern-coremidi-event-handling-with-swift) — MEDIUM confidence (community blog, 2024)
- [Lock-Free Real-Time Audio — timur.audio](https://timur.audio/using-locks-in-real-time-audio-processing-safely) — HIGH confidence (established real-time audio reference)

---

*Architecture research for: SSL Matrix console control bridge*
*Researched: 2026-02-24*

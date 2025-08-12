ByteBeast — Product Feature Description & Software Architecture (Hand-off)
1) Product summary
ByteBeast is a device-centric virtual pet that reacts to the real world via onboard sensors, shows its mood/evolution with OpenMoji emojis on a triple-screen LCD HAT, and can interact with nearby pets. Core loop: sense → infer mood/needs → visualize → evolve → suggest tasks → (optional) socialize.

Primary goals
Delightful ambient companion that’s glanceable and expressive.

Environment-aware: light, color temp, temp/humidity, pressure trends, motion/orientation, battery state.

Low-friction engagement: daily micro-goals, emoji UI, minimal menus.

Battery-aware UX: adapts frame rate/brightness and safely shuts down.

Target hardware assumptions
Raspberry Pi Zero 2W, Ubuntu (ARM64)

Waveshare Sense HAT (C) (I²C):

IMU: QMI8658C (accel/gyro) + AK09918 (mag)

SHTC3 (temp/humidity), LPS22HB (pressure), TCS34725 (RGB/clear light)

Waveshare UPS HAT (C) (I²C): INA219 telemetry (V/I/P, charge state)

Waveshare Zero LCD HAT (A) (SPI):

Main 1.3" ST7789 240×240 + two 0.96" ST7735S 160×80, 2x keys

2) User-facing feature set
A. Emoji-first visualization
Central mood emoji (main screen) + badges (env/status) on the two secondary screens.

Tiny bars: Energy, Evolution XP.

Idle animations: eye blink, pulse on state change (LCD only; fall back to static frames if low power).

B. Adaptive mood & needs
Moods: happy, calm, sleepy, anxious, sick, playful, bored, curious, hot, cold.

Needs: hunger, rest, social, hygiene (0–100). Needs drift over time; player actions + environment satisfy them.

C. Multi-path evolution (functional + visual)
Paths selected by sustained exposure (rolling window, 24–72h):

sun (bright/warm & active), shadow (dark/quiet), ember (hot), frost (cold),

social (many encounters), lone_wolf (solitary).

Each path has 4 stages; stage-ups unlock a small ability (e.g., better stamina, faster “duel” resolve).

D. Daily tasks & events
Auto-generated micro-goals from deficits/traits: “walk 600m”, “quiet 15 min”, “bright spot 10 min”, “meet 1 peer”.

Weekly themes/seasonal flags tweak thresholds & emoji skins.

E. Social encounters (MVP)
Nearby discovery via Wi-Fi SSID fingerprinting (no connection) or BLE if enabled.

Encounters: quick greet (XP + mood bump) or duel (turn-based, deterministic with traits/stage).

F. Battery-aware behavior
Uses INA219: battery %, current draw.

<20%: dim/slow UI; <10%: static frames; <5%: safe shutdown.

3) Non-functional requirements
Uptime: 24/7 daemonized services with graceful recovery.

Data integrity: ring buffers to limit flash wear; periodic compaction.

Latency: UI frame ≤ 50 ms on state change; baseline 10–30 FPS (active) / 1–5 FPS (idle).

Attribution: Display OpenMoji CC BY-SA 4.0 in About screen.

4) Software architecture
Process layout (systemd services)
bytebeast-sense.service — sensor polling/fusion → features bus

bytebeast-state.service — mood/needs/traits/evolution engine

bytebeast-viz.service — emoji rendering to ST7789/ST7735S

bytebeast-power.service — battery monitoring, power policy, safe shutdown

bytebeast-social.service — peer discovery + encounter logic (optional/start disabled)

Inter-process comms: local MQTT (mosquitto) or ZeroMQ pub/sub. Topic examples:

sense/features (EnvFeatures JSON @ 2–5 Hz active, 0.2–1 Hz idle)

state/snapshot, state/mood, state/evolution

power/telemetry, social/encounter

High-level data flow (ASCII)

[Sensors (I2C)] -> [bytebeast-sense] -> features --->+
                                                     |
                                      +--------------v--------------+
                                      |       bytebeast-state       |
                                      | mood/needs/traits/evolution |
                                      +--------------+--------------+
                                                     |
                                  +------------------v------------------+
                                  |           bytebeast-viz              |
                                  | emoji map + badges -> 3 LCD panels   |
                                  +------------------+-------------------+
                                                     |
                         +---------------------------v---------------------------+
                         | bytebeast-power (INA219) dim/idle/sleep, safe shutdown|
                         +---------------------------+---------------------------+
                                                     |
                                      +--------------v--------------+
                                      |       bytebeast-social      |
                                      | (optional) greet/duel/co-op |
                                      +-----------------------------+
5) Sensor → feature extraction (Sense HAT C + UPS HAT C)
Sampling

IMU (accel/gyro): 25–50 Hz → downsample to 5–10 Hz; RMS motion, shakes

Magnetometer: 5 Hz

TCS34725 (RGB/clear): 1–2 Hz → lux proxy + CCT (color temperature)

SHTC3 (temp/rh), LPS22HB (pressure): 1 Hz (active), 0.2 Hz (idle)

INA219: 1–2 Hz

Derived features (names stable for downstream)


lux: float             # from clear channel
cct_k: float           # color temperature
temp_c: float
rh: float
pressure_hpa: float
pressure_trend: float  # dP/dt smoothed
motion_rms_g: float
shake_events: int/min
heading_deg: float
roll: float; pitch: float; yaw: float
vbat: float; ibat: float; pwr_w: float
charging: bool
ssid_fingerprint: str  # hashed list for place/peer inference
timestamp: iso8601
6) Mood engine & emoji mapping
Thresholds (tuneable defaults)


LUX_BRIGHT = 8000.0
LUX_DARK   = 50.0
TEMP_HOT   = 30.0
TEMP_COLD  = 10.0
NOISE_QUIET = 35.0    # optional mic later
MOTION_ACTIVE = 0.20  # g RMS
Rule order (first match wins; else fallback by needs)

hot if temp ≥ HOT → 😵‍💫/🥵 badge 🔥

cold if temp ≤ COLD → 🥶 badge ❄️

sick if (battery < 10% OR humidity/extremes sustained) → 🤒

sleepy if dark & low motion for ≥ N minutes → 😴 🌙

playful if shake bursts or active → 🤩

happy if bright & comfortable → 😃 ☀️

bored if no novelty & low motion for long → 😐

curious if place/heading/CCT novelty → 🧐

else calm → 😌

Badges

Env: ☀️/🌙, 🔥/❄️, 🧪 (air/voc if added), 🔋 (low)

Progress: small dot trail while evolving

7) Evolution engine (multi-path)
Rolling window exposure (minutes in last 48h)

sun_score: bright + warm + active minutes

shadow_score: dark + quiet + low motion minutes

ember_score: hot minutes

frost_score: cold minutes

social_score: encounters/minutes with peers

lone_score: low peers + roaming novelty

Path selection

Path = argmax(weighted_scores) with hysteresis (min dwell before switching).

progression += f(score_delta) per tick; stage++ when ≥ 1.0; grant ability.

Path tables (example)


sun:    [🐣, 🐥, 🦅, 🦄]
shadow: [🦇, 🦉, 🐺, 🐉]
ember:  [🦁, 🔥, 🐯, 🐉]
frost:  [🐧, ❄️, 🐻‍❄️, 🐉]
social: [🐒, 🦁, 🦄, 👑]
lone:   [🐭, 🦊, 🐺, 🐉]
8) Traits & adaptive learning (lightweight)
Maintain EMA-based traits in [0..1]: playful, needy, rebellious, social, explorer.

Increment on actions/events:

mini-games/active → playful↑

missed care windows → needy↑; repeated neglect → rebellious↑

peer encounters → social↑

place novelty (SSID/heading/CCT delta) → explorer↑

Use traits to bias mood selection, task generation, and duel resolution.

9) Storage model (SQLite + JSON blobs)
Tables:

state_snapshot(id INTEGER PK, json TEXT, ts INTEGER)

history_sense(id, json TEXT, ts) (ring buffer capped by row count)

history_events(id, type, payload_json, ts)

config(key TEXT PK, value TEXT)

telemetry_daily(ts_day, stats_json)

Periodic compaction & pruning policies to limit writes.

10) Display system (Zero LCD HAT A)
Main ST7789 (240×240):

Center emoji 128–192 px.

Top-right badges (max 3).

Bottom 3–6 px bars (energy / EVO XP).

Left ST7735S (160×80):

Ambient strip: gradient from TCS34725 (RGB), text: 22.4°C 48%

Right ST7735S (160×80):

Battery % bar from INA219, charge icon, uptime; KEY1/KEY2 hints.

Rendering: pre-rasterized OpenMoji PNGs (64/96/128) cached in RAM; Pillow for compositing; SPI blits per panel.

Frame policy: 10–30 FPS active, 1–5 FPS idle; static below 10% battery.

11) Public Python APIs (what the coder must implement)
Data classes

from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class EnvFeatures:
    lux: float; cct_k: float
    temp_c: float; rh: float
    pressure_hpa: float; pressure_trend: float
    motion_rms_g: float; shake_events: int
    heading_deg: float; roll: float; pitch: float; yaw: float
    vbat: float; ibat: float; pwr_w: float; charging: bool
    ssid_fingerprint: str
    timestamp: float

@dataclass
class Beast:
    mood: str
    needs: Dict[str, float]
    traits: Dict[str, float]
    evolution_path: str
    evolution_stage: int         # 1..4
    evolution_prog: float        # 0..1
    energy: float                # 0..100
Sensing HAL

def sense_read() -> EnvFeatures: ...
def wifi_fingerprint() -> str: ...  # hash of nearby SSIDs/BSSIDs
State & evolution

def infer_mood(env: EnvFeatures, beast: Beast) -> Beast: ...
def tick_traits(env: EnvFeatures, beast: Beast, actions: Dict) -> Beast: ...
def update_evolution(env: EnvFeatures, beast: Beast) -> Beast: ...
def generate_tasks(beast: Beast, env: EnvFeatures) -> list[dict]: ...
Visualization

@dataclass
class EmojiFrame:
    emoji: str           # main glyph
    badges: list[str]    # up to 3
    bars: Dict[str, float]  # {'energy':0.7, 'evo':0.3}

def map_emoji(beast: Beast, env: EnvFeatures) -> EmojiFrame: ...
def draw_main(frame: EmojiFrame) -> None: ...
def draw_aux_left(env: EnvFeatures) -> None: ...
def draw_aux_right(env: EnvFeatures) -> None: ...
Power & safety

def power_policy(env: EnvFeatures) -> dict:
    """
    returns {'fps': int, 'dim': bool, 'static_mode': bool, 'shutdown': bool}
    """
Social (MVP)
python
Copy
Edit
def social_scan() -> Dict: ...      # returns {'peers': int, 'peer_hashes': [...]}
def social_encounter(beast: Beast, other: Dict) -> Dict: ...  # duel/greet result
12) Config & constants (YAML)

display:
  fps_active: 20
  fps_idle: 3
  battery_dim_pct: 20
  battery_static_pct: 10
  battery_shutdown_pct: 5

evolution:
  window_hours: 48
  stage_goal: 1.0
  hysteresis_hours: 6

thresholds:
  lux_bright: 8000
  lux_dark: 50
  temp_hot: 30
  temp_cold: 10
  motion_active_g: 0.2
13) Testing strategy
Sensor sims: feed recorded CSVs into bytebeast-state to validate mood/evo transitions.

Golden traces: unit tests for rule ordering (hot vs happy, etc.).

Power tests: scripted discharge with INA219 logs → verify dim/static/shutdown thresholds.

UI snap tests: offscreen renders compared as hashes to detect regressions.

14) Deliverables for the coder


Configurable thresholds via /config/defaults.yaml.

OpenMoji assets (PNG sizes) + attribution page.

15) Acceptance criteria
Emoji UI updates within ≤100 ms of mood change; evolution stage-up visible with transition.

Power policies trigger at the defined thresholds.

After 48h of simulated data, path selection and stage progression match spec.

Safe shutdown occurs <5% battery with a visible warning frame.
# ByteBeast Virtual Pet User Guide

Welcome to ByteBeast - your digital companion that lives and grows based on its environment! This guide will help you understand what your ByteBeast is showing you and how to care for it.

## Hardware Overview

ByteBeast uses a triple-display system on your Raspberry Pi:

- **Main Display (1.3" LCD)**: Center screen showing mood
- **Left Display (0.96" LCD)**: Evolution stage indicator  
- **Right Display (0.96" LCD)**: Care needs warnings

## Understanding the Displays

### 🎭 Main Display - Mood Indicator

The center screen shows your ByteBeast's current mood through colorful emoji artwork:

| Emoji | Mood | What It Means |
|-------|------|---------------|
| 😃 | **Happy** | Content and satisfied with current conditions |
| 😌 | **Calm** | Relaxed and at peace |
| 😴 | **Sleepy** | Low light and minimal motion detected |
| 😰 | **Anxious** | Stressed by environmental conditions |
| 🤒 | **Sick** | Low battery, extreme conditions, or poor health |
| 🤩 | **Playful** | Excited by movement and activity |
| 😐 | **Bored** | Needs stimulation or change |
| 🧐 | **Curious** | Exploring and investigating environment |
| 🥵 | **Hot** | Temperature is too warm |
| 🥶 | **Cold** | Temperature is too cool |

### 🌱 Left Display - Evolution Stage

Shows your ByteBeast's current evolutionary form across 6 possible paths:

#### Solar Path ☀️ (Bright, active environments)
🐣 **Stage 1**: Hatchling → 🐥 **Stage 2**: Chick → 🦅 **Stage 3**: Eagle → 🦄 **Stage 4**: Unicorn

#### Shadow Path 🌙 (Dark, quiet environments)  
🦇 **Stage 1**: Bat → 🦉 **Stage 2**: Owl → 🐺 **Stage 3**: Wolf → 🐉 **Stage 4**: Dragon

#### Ember Path 🔥 (Hot temperature environments)
🦁 **Stage 1**: Lion Cub → 🔥 **Stage 2**: Fire Spirit → 🐯 **Stage 3**: Tiger → 🐉 **Stage 4**: Fire Dragon

#### Frost Path ❄️ (Cold temperature environments)
🐧 **Stage 1**: Penguin → ❄️ **Stage 2**: Ice Crystal → 🐻‍❄️ **Stage 3**: Polar Bear → 🐉 **Stage 4**: Ice Dragon

#### Social Path 👥 (High interaction environments)
🐒 **Stage 1**: Monkey → 🦁 **Stage 2**: Lion → 🦄 **Stage 3**: Unicorn → 👑 **Stage 4**: Crowned King

#### Lone Wolf Path 🐺 (Solitary environments)
🐭 **Stage 1**: Mouse → 🦊 **Stage 2**: Fox → 🐺 **Stage 3**: Wolf → 🐉 **Stage 4**: Lone Dragon

### 🚨 Right Display - Care Warnings

Shows urgent care needs when levels drop below 40%:

| Icon | Need | Action Required |
|------|------|-----------------|
| 🍴 | **Hunger** | Provide food or stimulating environment |
| 😴 | **Rest** | Ensure quiet, dim environment for recovery |
| 👥 | **Social** | Increase interaction and WiFi connectivity |
| 🚿 | **Hygiene** | Reset or clean the environment |

## Caring for Your ByteBeast

### 🌡️ Environmental Care

**Temperature**: 
- Keep between 18-25°C (64-77°F) for optimal happiness
- Too hot (>28°C) or cold (<15°C) will make your pet sick
- Gradual temperature changes are better than sudden shifts

**Light**:
- Bright light (>100 lux) encourages solar evolution path
- Dim light (<10 lux) promotes shadow evolution path  
- Natural daylight cycles help maintain healthy rhythms

**Movement & Activity**:
- Gentle movement keeps your ByteBeast playful
- Too much shaking causes anxiety
- Stillness for extended periods leads to boredom

### 💖 Meeting Basic Needs

**Hunger (🍴)**:
- Automatically satisfied by environmental richness
- Bright light, moderate temperature, and gentle activity help
- Low hunger leads to sick mood and stunted growth

**Rest (😴)**:
- Provided by quiet, dim environments
- Your ByteBeast needs downtime to recover energy
- Constant stimulation prevents proper rest

**Social (👥)**:
- Increases with WiFi network diversity (detects nearby devices)
- Take your ByteBeast to different locations
- Social interaction affects evolution path selection

**Hygiene (🚿)**:
- Automatically maintained through environmental stability
- Extreme conditions or power issues reduce hygiene
- Clean, stable environments promote health

### 🔋 Power & Health

**Battery Management**:
- Keep ByteBeast charged above 30% battery
- Low power triggers sick mood and stops evolution
- Critical battery (<10%) shows red warning screen

**Environmental Extremes**:
- Avoid temperatures outside 10-35°C range
- Protect from excessive vibration or shock
- Stable conditions promote healthy growth

### 📈 Evolution & Growth

**Evolution Triggers**:
- **Solar Path**: Bright environments (>50 lux average)
- **Shadow Path**: Dark environments (<20 lux average)  
- **Ember Path**: Hot conditions (>25°C average)
- **Frost Path**: Cold conditions (<20°C average)
- **Social Path**: High WiFi activity and interaction
- **Lone Path**: Isolated, low-activity environments

**Growth Requirements**:
- All needs above 40% for healthy development
- Consistent environmental conditions for 24+ hours
- Energy level above 60% for evolution progress

**Evolution Timeline**:
- **Stage 1→2**: 2-3 days of optimal conditions
- **Stage 2→3**: 4-5 days of consistent care
- **Stage 3→4**: 7+ days of perfect environment match

## 🎯 Daily Care Routine

### Morning (7-9 AM)
- Check mood and needs on displays
- Ensure battery is charged
- Place in bright, active environment for solar types

### Midday (12-2 PM)  
- Monitor temperature and light levels
- Look for need warnings on right display
- Adjust environment based on evolution path

### Evening (6-8 PM)
- Review day's mood changes in console log
- Prepare quieter environment for rest
- Check evolution progress

### Night (10 PM+)
- Dim lighting for shadow evolution or rest
- Minimize vibration and movement
- Allow 6-8 hours of low-activity time

## 📊 Understanding Console Output

Your ByteBeast logs its status every 3 seconds:

```
--- Cycle 67 ---
🌡️ Environment: 18.9°C, 66 lux, 59%RH
🎭 Status: playful mood, 69% avg needs, 100% energy  
🔋 Power: 67% battery, 0.48W
😊 Mood changed: playful → sick
```

- **Environment**: Current sensor readings
- **Status**: Mood, average need satisfaction, energy level
- **Power**: Battery percentage and power consumption
- **Mood Changes**: Notifications when mood shifts

## 🔧 Troubleshooting

### My ByteBeast seems sick 🤒
- Check battery level (charge if <30%)
- Verify temperature is in 18-25°C range
- Ensure stable power supply
- Avoid extreme environmental conditions

### Displays show colored rectangles instead of emojis
- This indicates test pattern mode
- Restart the ByteBeast application
- Verify OpenMoji image files are present

### Evolution isn't progressing 🐣
- Ensure all needs stay above 40%
- Maintain consistent environmental conditions
- Check that energy level stays above 60%
- Be patient - evolution takes days, not hours

### Right display always shows same warning 🚨
- Address the specific need shown (hunger, rest, social, hygiene)
- Monitor changes in console output for confirmation
- Some needs require sustained environmental changes

## 🎊 Advanced Care Tips

### Optimization for Specific Paths

**Solar Path Mastery**:
- Morning sunlight exposure
- Active, bright environments
- Warm (but not hot) temperatures

**Shadow Path Mastery**:
- Evening/night environments
- Consistent dim lighting
- Quiet, still conditions

**Social Path Mastery**:
- Take to cafes, offices, public spaces
- High WiFi network diversity
- Regular location changes

### Understanding Personality Traits

Your ByteBeast develops personality traits over time:

- **Playful**: Responds well to movement and activity
- **Needy**: Requires more attention to needs
- **Rebellious**: May resist environmental changes  
- **Social**: Thrives in interactive environments
- **Explorer**: Benefits from location variety

### Long-term Care

- Evolution is permanent - choose your path thoughtfully
- Stage 4 ByteBeasts are more resilient but still need care
- Consider seasonal environmental changes
- Plan care routine around your lifestyle

## 🤝 Community & Support

- Monitor console output for detailed status information
- Each ByteBeast is unique based on its experiences
- Environmental history shapes personality development
- Share your ByteBeast's evolution journey with others!

---

*Remember: ByteBeast is a living digital companion that responds to real environmental conditions. Consistent, thoughtful care leads to a happy, healthy, and uniquely evolved pet!*
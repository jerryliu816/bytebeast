"""
Mood inference engine for ByteBeast virtual pet.

Implements rule-based mood detection based on environmental sensors
and beast internal state.
"""

import time
import logging
from typing import Dict, List, Optional
from core.models import EnvFeatures, Beast, MOOD_EMOJIS, EVOLUTION_PATHS
from core.config import get_config

logger = logging.getLogger(__name__)


class MoodEngine:
    """Rule-based mood inference engine."""
    
    def __init__(self):
        """Initialize mood engine."""
        self.config = get_config()
        self.thresholds = self.config.thresholds
        
    def infer_mood(self, env: EnvFeatures, beast: Beast) -> str:
        """Infer mood from environment and beast state using rule priority."""
        
        # Rule order: first match wins, else fallback by needs
        
        # 1. Hot rule - immediate environmental response
        if env.temp_c >= self.thresholds['temp_hot']:
            return 'hot'
        
        # 2. Cold rule - immediate environmental response  
        if env.temp_c <= self.thresholds['temp_cold']:
            return 'cold'
        
        # 3. Sick rule - battery or health issues
        if (env.vbat < self.config.power['low_voltage'] or 
            beast.energy < 20 or
            self._is_environmental_extreme(env)):
            return 'sick'
        
        # 4. Sleepy rule - dark and low motion for extended time
        if (env.lux < self.thresholds['lux_dark'] and 
            env.motion_rms_g < (self.thresholds['motion_active_g'] / 4) and
            self._is_sustained_condition(env, beast, 'sleepy')):
            return 'sleepy'
        
        # 5. Playful rule - shake bursts or high activity
        if (env.shake_events > 0 or 
            env.motion_rms_g > self.thresholds['motion_active_g']):
            return 'playful'
        
        # 6. Happy rule - bright and comfortable conditions
        if (env.lux > self.thresholds['lux_bright'] and
            self._is_comfortable_temperature(env.temp_c) and
            beast.energy > 60):
            return 'happy'
        
        # 7. Curious rule - environmental novelty
        if self._detect_novelty(env, beast):
            return 'curious'
        
        # 8. Bored rule - no novelty and low motion for extended time
        if (env.motion_rms_g < (self.thresholds['motion_active_g'] / 2) and
            self._is_sustained_condition(env, beast, 'bored')):
            return 'bored'
        
        # 9. Anxious rule - rapid environmental changes or low needs
        if (self._is_environment_unstable(env) or 
            any(need < 30 for need in beast.needs.values())):
            return 'anxious'
        
        # 10. Default fallback - calm
        return 'calm'
    
    def _is_environmental_extreme(self, env: EnvFeatures) -> bool:
        """Check for extreme environmental conditions."""
        return (abs(env.pressure_trend) > self.thresholds.get('pressure_stable', 2.0) * 2 or
                env.rh > 90 or env.rh < 10)
    
    def _is_sustained_condition(self, env: EnvFeatures, beast: Beast, condition: str) -> bool:
        """Check if condition has been sustained (simplified - would need history)."""
        # This is a placeholder - in full implementation would check recent history
        # For now, use a simple heuristic based on current state
        if condition == 'sleepy':
            return beast.energy < 40
        elif condition == 'bored':
            return beast.needs.get('social', 50) < 40
        return False
    
    def _is_comfortable_temperature(self, temp_c: float) -> bool:
        """Check if temperature is in comfortable range."""
        return (self.thresholds['temp_cold'] + 5) <= temp_c <= (self.thresholds['temp_hot'] - 5)
    
    def _detect_novelty(self, env: EnvFeatures, beast: Beast) -> bool:
        """Detect environmental novelty (simplified)."""
        # In full implementation, would compare with recent history
        # For now, use simple heuristics
        
        # Location novelty (WiFi fingerprint change)
        if env.ssid_fingerprint != getattr(beast, '_last_fingerprint', ''):
            return True
        
        # Large changes in heading or orientation
        if env.shake_events > 2:
            return True
            
        # Significant light changes
        if hasattr(beast, '_last_lux'):
            lux_change = abs(env.lux - beast._last_lux) / max(beast._last_lux, 1)
            if lux_change > 0.5:  # 50% change
                return True
        
        return False
    
    def _is_environment_unstable(self, env: EnvFeatures) -> bool:
        """Check for rapidly changing environmental conditions."""
        return (abs(env.pressure_trend) > self.thresholds.get('pressure_stable', 2.0) or
                env.shake_events > 3)
    
    def update_needs(self, beast: Beast, env: EnvFeatures, actions: Dict = None) -> Beast:
        """Update beast needs based on time passage and actions."""
        if actions is None:
            actions = {}
        
        current_time = time.time()
        time_delta = current_time - beast.last_updated
        hours_passed = time_delta / 3600.0
        
        # Get base drift rates from config
        needs_config = self.config.needs
        base_rates = {
            'hunger': needs_config['hunger_base'],
            'rest': needs_config['rest_base'], 
            'social': needs_config['social_base'],
            'hygiene': needs_config['hygiene_base']
        }
        
        # Apply need drift over time
        for need, base_rate in base_rates.items():
            # Adjust drift based on environmental factors
            drift_rate = self._calculate_drift_rate(need, base_rate, env, beast)
            
            # Apply drift
            beast.needs[need] -= drift_rate * hours_passed * needs_config['drift_rate']
            
            # Apply actions that satisfy needs
            if need in actions:
                beast.needs[need] += actions[need]
        
        # Environmental need satisfaction
        beast.needs = self._apply_environmental_satisfaction(beast.needs, env)
        
        # Clamp needs to valid range
        for need in beast.needs:
            beast.needs[need] = max(0.0, min(100.0, beast.needs[need]))
        
        beast.last_updated = current_time
        return beast
    
    def _calculate_drift_rate(self, need: str, base_rate: float, env: EnvFeatures, beast: Beast) -> float:
        """Calculate adjusted drift rate based on conditions."""
        rate = base_rate
        
        if need == 'hunger':
            # Higher activity increases hunger
            if env.motion_rms_g > self.thresholds['motion_active_g']:
                rate *= 1.5
                
        elif need == 'rest':
            # Bright light reduces rest need satisfaction
            if env.lux > self.thresholds['lux_bright']:
                rate *= 1.2
            # Activity increases rest need
            if env.motion_rms_g > self.thresholds['motion_active_g']:
                rate *= 1.3
                
        elif need == 'social':
            # Location changes suggest social opportunities
            if self._detect_novelty(env, beast):
                rate *= 0.8  # Slower drift when exploring
                
        elif need == 'hygiene':
            # Environmental extremes increase hygiene need
            if not self._is_comfortable_temperature(env.temp_c):
                rate *= 1.2
        
        return rate
    
    def _apply_environmental_satisfaction(self, needs: Dict[str, float], env: EnvFeatures) -> Dict[str, float]:
        """Apply environmental satisfaction to needs."""
        
        # Rest satisfaction from dark, quiet environment
        if (env.lux < self.thresholds['lux_dark'] and 
            env.motion_rms_g < self.thresholds['motion_active_g'] / 4):
            needs['rest'] = min(100.0, needs['rest'] + 0.5)
        
        # Social satisfaction from location novelty (proxy for meeting others)
        # This is simplified - full implementation would detect actual peers
        
        # Hygiene satisfaction from moderate conditions
        if self._is_comfortable_temperature(env.temp_c) and 40 < env.rh < 70:
            needs['hygiene'] = min(100.0, needs['hygiene'] + 0.2)
        
        return needs
    
    def tick_traits(self, env: EnvFeatures, beast: Beast, actions: Dict = None) -> Beast:
        """Update beast traits based on experiences and actions."""
        if actions is None:
            actions = {}
        
        # Trait learning rates (small increments)
        learning_rate = 0.01
        
        # Playful trait - increases with activity and play actions
        if (env.motion_rms_g > self.thresholds['motion_active_g'] or 
            env.shake_events > 0 or 
            'play' in actions):
            beast.traits['playful'] += learning_rate
        
        # Needy trait - increases when needs are low
        avg_need = sum(beast.needs.values()) / len(beast.needs)
        if avg_need < 40:
            beast.traits['needy'] += learning_rate
        elif avg_need > 70:
            beast.traits['needy'] -= learning_rate / 2
        
        # Rebellious trait - increases with neglect or when needs ignored
        if any(need < 20 for need in beast.needs.values()):
            beast.traits['rebellious'] += learning_rate
        
        # Social trait - would increase with peer interactions
        # Simplified for now since we don't have social system fully implemented
        if 'social_interaction' in actions:
            beast.traits['social'] += learning_rate
        
        # Explorer trait - increases with location/environmental novelty
        if self._detect_novelty(env, beast):
            beast.traits['explorer'] += learning_rate
        
        # Clamp traits to valid range
        for trait in beast.traits:
            beast.traits[trait] = max(0.0, min(1.0, beast.traits[trait]))
        
        return beast
    
    def update_evolution(self, env: EnvFeatures, beast: Beast, hours: int = 48) -> Beast:
        """Update evolution path and progression."""
        # This is simplified - full implementation would use database history
        
        # Calculate exposure scores (simplified heuristics)
        exposure_scores = {
            'sun': 0.0,
            'shadow': 0.0,
            'ember': 0.0, 
            'frost': 0.0,
            'social': 0.0,
            'lone': 0.0
        }
        
        # Sun path: bright + warm + active
        if (env.lux > 1000 and 
            env.temp_c > 20 and 
            env.motion_rms_g > self.thresholds['motion_active_g'] / 2):
            exposure_scores['sun'] += 1.0
        
        # Shadow path: dark + quiet + low motion  
        if (env.lux < self.thresholds['lux_dark'] and
            env.motion_rms_g < self.thresholds['motion_active_g'] / 4):
            exposure_scores['shadow'] += 1.0
        
        # Ember path: hot temperatures
        if env.temp_c > self.thresholds['temp_hot']:
            exposure_scores['ember'] += 1.0
        
        # Frost path: cold temperatures
        if env.temp_c < self.thresholds['temp_cold']:
            exposure_scores['frost'] += 1.0
        
        # Social/lone paths (simplified - would need peer detection)
        if env.motion_rms_g > self.thresholds['motion_active_g']:
            exposure_scores['social'] += 0.5
        else:
            exposure_scores['lone'] += 0.5
        
        # Select path with highest score (with hysteresis)
        current_score = exposure_scores.get(beast.evolution_path, 0.0)
        max_path = max(exposure_scores.items(), key=lambda x: x[1])
        
        # Path switching with hysteresis
        if max_path[1] > current_score + 0.2:  # Require significant difference
            beast.evolution_path = max_path[0]
        
        # Update progression
        progression_rate = self.config.evolution.get('progression_rate', 0.01)
        beast.evolution_prog += progression_rate * max(max(exposure_scores.values()), 0.1)
        
        # Stage progression
        stage_goal = self.config.evolution.get('stage_goal', 1.0)
        if beast.evolution_prog >= stage_goal and beast.evolution_stage < 4:
            beast.evolution_stage += 1
            beast.evolution_prog = 0.0
            logger.info(f"Evolution stage up: {beast.evolution_path} stage {beast.evolution_stage}")
        
        return beast
    
    def generate_tasks(self, beast: Beast, env: EnvFeatures) -> List[Dict]:
        """Generate daily tasks based on deficits and traits."""
        tasks = []
        
        # Need-based tasks
        for need, value in beast.needs.items():
            if value < 40:  # Need is low
                if need == 'hunger':
                    tasks.append({
                        'type': 'care',
                        'action': 'feed',
                        'description': 'Feed your ByteBeast',
                        'reward': {'hunger': 20}
                    })
                elif need == 'rest':
                    tasks.append({
                        'type': 'environment',
                        'action': 'quiet_time',
                        'description': 'Find a quiet spot for 15 minutes',
                        'reward': {'rest': 15}
                    })
                elif need == 'social':
                    tasks.append({
                        'type': 'social',
                        'action': 'meet_peer',
                        'description': 'Take your ByteBeast to meet others',
                        'reward': {'social': 25}
                    })
                elif need == 'hygiene':
                    tasks.append({
                        'type': 'care',
                        'action': 'clean',
                        'description': 'Keep your ByteBeast in comfortable conditions',
                        'reward': {'hygiene': 20}
                    })
        
        # Trait-based tasks
        if beast.traits['explorer'] > 0.7:
            tasks.append({
                'type': 'exploration',
                'action': 'new_location',
                'description': 'Take your ByteBeast somewhere new',
                'reward': {'explorer_xp': 10}
            })
        
        if beast.traits['playful'] > 0.7:
            tasks.append({
                'type': 'activity',
                'action': 'play_session',
                'description': 'Have an active play session (shake/move around)',
                'reward': {'playful_xp': 10}
            })
        
        # Environmental tasks
        if env.lux < 100:  # Very dark
            tasks.append({
                'type': 'environment',
                'action': 'bright_spot',
                'description': 'Find a bright spot for 10 minutes',
                'reward': {'energy': 10}
            })
        
        # Limit to reasonable number of tasks
        return tasks[:3]


def create_default_beast() -> Beast:
    """Create a new ByteBeast with default values."""
    return Beast(
        mood='calm',
        needs={
            'hunger': 75.0,
            'rest': 60.0,
            'social': 50.0, 
            'hygiene': 80.0
        },
        traits={
            'playful': 0.5,
            'needy': 0.3,
            'rebellious': 0.2,
            'social': 0.4,
            'explorer': 0.6
        },
        evolution_path='sun',
        evolution_stage=1,
        evolution_prog=0.0,
        energy=100.0,
        last_updated=time.time()
    )
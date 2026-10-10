"""
Procedural sound effects generator and manager for Metro Tycoon.
Generates all sound effects dynamically in memory using standard math and pygame.mixer,
requiring zero external audio files.
"""

import math
import struct
import pygame

class SoundManager:
    def __init__(self):
        self.enabled = True
        self.volume = 0.7
        self.sounds = {}
        self._init_mixer()
        if pygame.mixer.get_init():
            self._generate_all_sounds()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception as e:
            print(f"[SoundManager] Mixer init warning: {e}")

    def _make_pcm_sound(self, generator_func, duration=0.2, volume=0.8):
        """Helper to create a pygame.mixer.Sound from a math sample generator."""
        if not pygame.mixer.get_init():
            return None
        
        sample_rate = 44100
        num_samples = int(sample_rate * duration)
        buf = bytearray()
        
        for i in range(num_samples):
            t = i / sample_rate
            # Generator yields value between -1.0 and 1.0
            sample_val = generator_func(t, i, num_samples)
            # Clamp and convert to 16-bit integer
            sample_val = max(-1.0, min(1.0, sample_val)) * volume
            int_val = int(sample_val * 32767)
            # Stereo 16-bit little-endian (left and right channels)
            packed = struct.pack('<hh', int_val, int_val)
            buf += packed

        try:
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception as e:
            print(f"[SoundManager] Sound build error: {e}")
            return None

    def _generate_all_sounds(self):
        """Pre-synthesizes all game sound effects."""
        # 1. Button click: Short crisp click
        def gen_click(t, i, n):
            decay = math.exp(-i / (n * 0.15))
            return math.sin(2 * math.pi * 1200 * t) * decay

        # 2. Dice roll rattle: multiple rapid clicks/tumbles
        def gen_dice(t, i, n):
            envelope = math.exp(-t * 8.0) * math.sin(math.pi * t / 0.25)
            # Blend multiple discordant high frequencies for a tumbling click
            noise = (math.sin(2 * math.pi * 320 * t) + 
                     0.5 * math.sin(2 * math.pi * 640 * t + 0.5) +
                     0.3 * math.sin(2 * math.pi * 980 * t + 1.2))
            # Amplitude modulation for dice bounces
            bounces = abs(math.sin(2 * math.pi * 18 * t))
            return noise * envelope * bounces

        # 3. Buy property: Pleasant 3-note cash register chime (C5 -> E5 -> G5)
        def gen_buy(t, i, n):
            decay = math.exp(-t * 5.0)
            if t < 0.08:
                f = 523.25 # C5
            elif t < 0.16:
                f = 659.25 # E5
            else:
                f = 783.99 # G5
            tone = math.sin(2 * math.pi * f * t) + 0.3 * math.sin(2 * math.pi * f * 2 * t)
            return tone * decay

        # 4. Pay rent: Double descending drop tone
        def gen_pay(t, i, n):
            decay = math.exp(-t * 9.0)
            f = 440 - (t * 800)
            return math.sin(2 * math.pi * max(150, f) * t) * decay

        # 5. Pass Go: Ascending fanfare chime
        def gen_pass_go(t, i, n):
            envelope = math.exp(-t * 3.5)
            # Arpeggio C5 -> G5 -> C6
            if t < 0.09:
                f = 523.25
            elif t < 0.18:
                f = 659.25
            elif t < 0.27:
                f = 783.99
            else:
                f = 1046.50
            return (math.sin(2 * math.pi * f * t) + 0.2 * math.sin(2 * math.pi * f * 2 * t)) * envelope

        # 6. Jail clang: Heavy metallic resonant strike
        def gen_jail(t, i, n):
            envelope = math.exp(-t * 6.0)
            low = math.sin(2 * math.pi * 110 * t)
            metal1 = 0.5 * math.sin(2 * math.pi * 337 * t)
            metal2 = 0.25 * math.sin(2 * math.pi * 684 * t)
            return (low + metal1 + metal2) * envelope

        # 7. Card draw swoosh
        def gen_card(t, i, n):
            envelope = math.sin(math.pi * t / 0.18)
            f = 300 + 600 * (t / 0.18)
            return math.sin(2 * math.pi * f * t) * envelope * 0.6

        # 8. Build upgrade chime: Crisp hammer / build sparkle
        def gen_build(t, i, n):
            envelope = math.exp(-t * 7.0)
            f = 880 + 200 * math.sin(2 * math.pi * 15 * t)
            return (math.sin(2 * math.pi * f * t) + 0.4 * math.sin(2 * math.pi * f * 2 * t)) * envelope

        # 9. Trade accept fanfare
        def gen_trade(t, i, n):
            envelope = math.exp(-t * 4.0)
            f = 440 + 220 * (1 if t > 0.1 else 0)
            return math.sin(2 * math.pi * f * t) * envelope

        # 10. Bankruptcy gong
        def gen_bankrupt(t, i, n):
            envelope = math.exp(-t * 3.0)
            f = max(80, 220 - t * 150)
            return (math.sin(2 * math.pi * f * t) + 0.3 * math.sin(2 * math.pi * (f * 1.5) * t)) * envelope

        # 11. Auction gavel strike: crisp double wooden tap
        def gen_gavel(t, i, n):
            t_rel = t if t < 0.08 else (t - 0.08)
            envelope = math.exp(-t_rel * 45.0)
            f = 420
            tone = (math.sin(2 * math.pi * f * t_rel) + 
                    0.6 * math.sin(2 * math.pi * 840 * t_rel) + 
                    0.3 * math.sin(2 * math.pi * 1260 * t_rel))
            return tone * envelope

        self.sounds["click"] = self._make_pcm_sound(gen_click, duration=0.08, volume=0.5)
        self.sounds["dice"] = self._make_pcm_sound(gen_dice, duration=0.25, volume=0.7)
        self.sounds["buy"] = self._make_pcm_sound(gen_buy, duration=0.28, volume=0.6)
        self.sounds["pay"] = self._make_pcm_sound(gen_pay, duration=0.18, volume=0.6)
        self.sounds["pass_go"] = self._make_pcm_sound(gen_pass_go, duration=0.45, volume=0.65)
        self.sounds["jail"] = self._make_pcm_sound(gen_jail, duration=0.4, volume=0.8)
        self.sounds["card"] = self._make_pcm_sound(gen_card, duration=0.18, volume=0.5)
        self.sounds["build"] = self._make_pcm_sound(gen_build, duration=0.25, volume=0.65)
        self.sounds["trade"] = self._make_pcm_sound(gen_trade, duration=0.3, volume=0.6)
        self.sounds["bankrupt"] = self._make_pcm_sound(gen_bankrupt, duration=0.6, volume=0.7)
        self.sounds["gavel"] = self._make_pcm_sound(gen_gavel, duration=0.2, volume=0.75)

    def play(self, name):
        """Plays a pre-generated sound if sound is enabled."""
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            try:
                sound.set_volume(self.volume)
                sound.play()
            except Exception as e:
                pass

    def toggle(self):
        """Toggle mute / unmute."""
        self.enabled = not self.enabled
        return self.enabled


# Global sound manager singleton instance
sound_fx = SoundManager()

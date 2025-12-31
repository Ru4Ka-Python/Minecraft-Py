import pygame as pg
import random
import os

class SoundManager:
    def __init__(self, sound_dir):
        pg.mixer.init()
        self.sounds = {}
        self.sound_dir = sound_dir
        # Load some sounds if they exist
        # for f in os.listdir(sound_dir):
        #     if f.endswith('.ogg') or f.endswith('.wav'):
        #         self.sounds[f[:-4]] = pg.mixer.Sound(os.path.join(sound_dir, f))

    def play(self, name, volume=1.0, pitch_variation=0.1):
        if name in self.sounds:
            sound = self.sounds[name]
            # Pygame doesn't natively support pitch variation easily 
            # without external libraries like numpy/scipy for processing.
            # But we can simulate it if we have multiple versions or use a library.
            # For now, just play the sound.
            sound.set_volume(volume)
            sound.play()

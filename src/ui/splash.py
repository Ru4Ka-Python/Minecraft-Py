import random
import math

class SplashText:
    def __init__(self, splash_file):
        with open(splash_file, 'r') as f:
            self.splashes = [line.strip() for line in f.readlines()]
        self.current_splash = random.choice(self.splashes)
        self.angle = -20
        self.base_scale = 1.0

    def get_scale(self, time):
        return self.base_scale + 0.1 * math.sin(time * 5)

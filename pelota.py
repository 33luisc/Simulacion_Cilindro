import numpy as np
import random
from config import GRAVEDAD

class Pelota:
    def __init__(self, x, y, z):
        self.pos = np.array([x, y, z], dtype=float)
        self.vel = np.array([0.0, -40.0, 0.0], dtype=float)
        self.color = [random.uniform(0.4, 1.0), random.uniform(0.4, 1.0), random.uniform(0.4, 1.0)]

    def integrar_movimiento(self, dt):
        self.vel[1] += GRAVEDAD * dt
        self.pos += self.vel * dt
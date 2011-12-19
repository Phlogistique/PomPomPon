import cv
import pygame
from itertools import cycle

class PomPomPon:
    COLORS = cycle([
        pygame.Color(255,0,0), pygame.Color(0,255,0), pygame.Color(0,0,255),
        pygame.Color(255,255,0), pygame.Color(255,0,255), pygame.Color(0,255,255)])

    def __init__(self, hue_target=127, hue_tolerance=30, sat_target=127,
            sat_tolerance=30, val_target=127, val_tolerance=30):


        self.color = PomPomPon.COLORS.next()

        self.hue_target = hue_target
        self.hue_tolerance = hue_tolerance
        self.sat_target = sat_target
        self.sat_tolerance = sat_tolerance
        self.val_target = val_target
        self.val_tolerance = val_tolerance

        self.calibration_done = False

        self.pos = None

        self.set_bounds()

    def set_target(self, hue_target=127, sat_target=127, val_target=127):

        self.hue_target = hue_target
        self.sat_target = sat_target
        self.val_target = val_target
        
        pg_hue = int(self.hue_target * 2)
        self.color.hsva = (pg_hue, 100, 100, 100)
        self.set_bounds()
        self.calibration_done = True

    def set_bounds(self):

        def clamp(x, m, M):
            if x < m: return m
            if x > M: return M
            return x

        def clamp256(v): return clamp(v, 0, 0xFF)

        self.lower = cv.Scalar(
                clamp256(self.hue_target - self.hue_tolerance),
                clamp256(self.sat_target - self.sat_tolerance),
                clamp256(self.val_target - self.val_tolerance))
        self.upper = cv.Scalar(
                clamp256(self.hue_target + self.hue_tolerance),
                clamp256(self.sat_target + self.sat_tolerance),
                clamp256(self.val_target + self.val_tolerance))


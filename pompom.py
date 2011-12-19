import cv
import time
import pygame
import sys
from pygame.locals import *
from itertools import cycle
from math import sqrt

from pompompon import PomPomPon
from song import Note, Touch

class PomPom:
    def __init__(self, song, steps, show_binary=None):
        self.show_binary = show_binary
        with open(steps, 'r') as f:
            self.steps = eval(f.read()) # c'est tellement secure j'y crois meme pas
        self.song = song

        self.init_params()
        self.init_cv()
        self.init_pygame()
        self.game()

    def init_params(self):
        self.dilatation = 3

        self.process_size = (320, 240)
        self.display_size = (640, 480)

        self.pompon = [PomPomPon(), PomPomPon()]
        self.pomponi = cycle(self.pompon)

        self.calibration_done = False

        self.nsteps = len(self.steps)
        self.score_miss = 0
        self.score_hit = 0
        self.score = 50

    def init_cv(self):
        # init image capture
        self.camera = cv.CaptureFromCAM(-1) # any camera

        # create image buffers

        def img(chans=3, size=self.process_size):
            return cv.CreateImage(size, cv.IPL_DEPTH_8U, chans)

        self.frame_rgb      = img(size=self.display_size)
        self.resized_frame  = img()
        self.hsv_frame      = img()
        self.smooth_frame   = img()
        self.bin_frame      = img(1)
        self.mask           = img(1)
        if self.show_binary:
            self.mask2          = img(1)
            self.miniature      = img()

    def init_pygame(self):
        pygame.init()
        self.fps_clock = pygame.time.Clock()
        self.window_surface = pygame.display.set_mode(self.display_size)
        self.canvas = pygame.Surface(self.display_size, flags=SRCALPHA)
        pygame.display.set_caption("PomPom")
        self.font = pygame.font.Font('DejaVuSans-Bold.ttf', 32)

        pygame.mixer.music.load(self.song)
        pygame.mixer.music.play()
        self.start = pygame.time.get_ticks()

    def in_range(self, pompon, src, dst):
        cv.InRangeS(src, pompon.lower, pompon.upper, dst);

    def alpha(self, color, a):
        trans = pygame.Color(color.r, color.g, color.b, color.a)
        trans.a = int(a)
        return trans

    def target(self, center, color, inside=None, radius=40, filled=True):
        if filled:
            pygame.draw.circle(
                    self.canvas,
                    inside or self.alpha(color, 0.3 * color.a),
                    self.sym2disp(center),
                    radius,
                    0)
        pygame.draw.circle(
                self.canvas,
                color,
                self.sym2disp(center),
                radius,
                6)

    sym2disp = lambda self, x, y=None: self.convert_coord(
            (1,1), self.display_size, x, y)
    sym2proc = lambda self, x, y=None: self.convert_coord(
            (1,1), self.process_size, x, y)

    disp2proc = lambda self, x, y=None: self.convert_coord(
            self.display_size, self.process_size, x, y)
    proc2disp = lambda self, x, y=None: self.convert_coord(
            self.process_size, self.display_size, x, y)

    disp2sym = lambda self, x, y=None: self.coord_2sym(
            self.display_size, x, y)
    proc2sym = lambda self, x, y=None: self.coord_2sym(
            self.process_size, x, y)

    def convert_coord(self, from_size, to_size, frac, y=None):
        if y is not None: frac = (frac, y)
        x,y = frac
        fx,fy = from_size
        tx,ty = to_size

        return (int(x*tx/fx), int(y*ty/fy))

    def coord_2sym(self, from_size, frac, y=None):
        if y is not None: frac = (frac, y)
        x,y = frac
        fx,fy = from_size

        return (x/float(fx), y/float(fy))

    POSITIONS = [
    #  (-1,1)             (1,1)
    #   +------------------+
    #   |                  |
    #   |                  |
    #   |                  |
    #   |                  |
    #   |                  |
    #   +------------------+
    #  (-1,-1)            (1,1)
            (0.33, 0.75),
            (0.17, 0.50),
            (0.33, 0.25),
            (0.50, 0.12),
            (0.67, 0.25),
            (0.83, 0.50),
            (0.67, 0.75)]

    RED = pygame.Color(255,0,0)
    BLUE = pygame.Color(0,0,255)

    def wait(self, seconds):
        start = time.time()
        while time.time() - start < seconds:
            self.loop.next()

    def do_for(self, seconds, f):
        start = time.time()
        while time.time() - start < seconds:
            f()
            self.loop.next()

    def wait_until(self, cond):
        self.do_until(cond, lambda: None)

    def do_until(self, cond, f):
        while not cond():
            f()
            self.loop.next()

    def do_forever(self, f):
        while True:
            f()
            self.loop.next()

    def now(self):
        return pygame.time.get_ticks() - self.start 

    def game(self):

        self.loop = self.run()

        self.left = (0.2, 0.3)
        self.right = (0.8, 0.3)
        self.left_color = self.pompon[0].color
        self.right_color = self.pompon[1].color

        next(self.loop) # retrieve first frame

        self.draw_calibration_targets()

        bg = None
        for i in range(5, -1, -1): # from 10 to 0
            msg = self.font.render("%d" % i, True, pygame.Color("black"))
            rect = msg.get_rect()
            rect.center = self.sym2disp(0.5, 0.2)
            if bg is None:
                bg = rect.inflate(4,4)

            self.canvas.fill((255,255,255,100), bg)
            self.canvas.blit(msg, rect)
            self.wait(1)

        self.calibrate(self.pompon[0], self.left)
        self.calibrate(self.pompon[1], self.right)

        bg.topleft = (0,0)
        w,_ = self.display_size
        bg.w = w
        self.score_bg = bg

        self.pre = []
        self.preavis = (1100, 200)
        self.cur = []
        self.ko = []
        self.ok = []
        self.calibration_done = True
        while True:
            self.redraw = False

            def transfer(fro, to, delay, cb=None):
                while len(fro) and fro[0].time < self.now() - delay:
                    pop = fro.pop(0)
                    if to is not None: to.append(pop)
                    if cb is not None: cb()

            transfer(self.steps, self.pre, -self.preavis[0])
            transfer(self.pre, self.cur, -self.preavis[1])
            transfer(self.cur, self.ko, 200, cb=lambda: self.miss())
            transfer(self.ko, None, 1000)
            transfer(self.ok, None, 1000)

            for p in self.pompon:
                if p.pos is None:
                    print "Pompon not on screen"
                    continue

                self.target(p.pos, pygame.Color("black"),
                        inside=pygame.Color("white"), radius=20)
                for note in cur:
                    px, py = p.pos
                    nx, ny = note.pos

                    distance = sqrt(4/3.0*(px-nx)**2 + (py-ny)**2)
                    if distance < 0.1:
                        cur.remove(note)
                        ok.append(note)
                        self.hit()
                        for i, kon in enumerate(ko):
                            if kon.pos == note.pos:
                                ko.pop(i)

            if len(self.steps) is None:
                break

            next(self.loop)

        self.wait(5)

    def calibrate(self, pompon, coord, recalibrate=None):
        x, y = self.sym2proc(coord)
        hue, sat, val = self.smooth_frame[y,x] # (y,x), not (x,y).
        pompon.set_target(hue, sat, val, recalibrate=recalibrate)

    def draw_calibration_targets(self):
        self.target(self.left, self.left_color)
        self.target(self.right, self.right_color)

    def calibration_step(self):
        pass


    def process(self):

        def seq_to_iter(seq):
            while seq:
                yield seq
                seq = seq.h_next()

        #back to a simple scoring method because I'm not sure this works
        def score_rect(r,p):
            x,y,w,h = r
            #if p.pos is None:
            #    distance = 0
            #else:
            #    px, py = self.sym2proc(p.pos)
            #    distance = sqrt(((x+w/2)-px)**2 + ((y+h/2)-py)**2) # XXX arbitraire

            return w * h #- distance

        cv.Resize(self.frame, self.resized_frame)
        cv.CvtColor(self.resized_frame, self.hsv_frame, cv.CV_RGB2HSV)
        cv.Smooth(self.hsv_frame, self.smooth_frame, cv.CV_GAUSSIAN,
                31)

        for p in self.pompon:
            if p.calibration_done:

                self.in_range(p, self.smooth_frame, self.bin_frame)
                cv.Erode(self.bin_frame, self.mask, None, self.dilatation);

                if self.show_binary:
                    self.mask2 = cv.CloneImage(self.mask) # for miniature

                contour = seq_to_iter(cv.FindContours(self.mask,
                        cv.CreateMemStorage(), cv.CV_RETR_EXTERNAL,
                        cv.CV_CHAIN_APPROX_SIMPLE));

                rects = map((lambda c: cv.BoundingRect(c, 0)), contour)
                if rects:
                    x,y,w,h = max(rects, key=lambda r: score_rect(r,p))

                    p.pos = self.proc2sym(x+w/2,y+h/2)
                    #self.calibrate(p, p.pos, recalibrate=0.05)
                    
                    # TODO here draw something for debugging
                    #cv.Rectangle(self.resized_frame, (x, y), (x+w, y+h),
                    #        p.color, 3)

    def hit(self):
        self.score_hit += 1
        self.score += 1
        if self.score > 100: self.score = 100
    def miss(self):
        self.score_miss += 1
        self.score -= 1
        if self.score < 0: self.score = 0

    def display(self):

        if self.calibration_done:
            self.canvas.fill((0,0,0,0))

            self.canvas.fill((255,255,255,100), self.score_bg)
            progressbar = self.score_bg.inflate(-2,-2)
            progressbar.w = progressbar.w * 100 / self.score

            green = 255 * (self.score) / 100
            red = 255 - green
            self.canvas.fill((255,255,255,100), self.score_bg)
            self.canvas.fill((red,green,0,100), self.progressbar)
            msg = self.font.render("Miss: %d" % self.score_hit, True, pygame.Color("black"))
            rect = msg.get_rect()
            rect.topleft = (2,2)
            self.canvas.blit(msg, rect)

            msg = self.font.render("Hit: %d" %self.score_miss, True, pygame.Color("black"))
            rect = msg.get_rect()
            w,_ = self.display_size()
            rect.topleft = (w-2,2)
            self.canvas.blit(msg, rect)

            for note in self.cur:
                self.target(note.pos, pygame.Color("blue"))
            for note in self.ok:
                self.target(note.pos, pygame.Color("green"), filled=False)
            for note in self.ko:
                self.target(note.pos, pygame.Color("red"), filled=False)

            color = pygame.Color("blue")
            h,s,v,a = color.hsva
            for note in self.pre:
                f = (note.time - self.now()) / float(self.preavis[1] - self.preavis[0])
                color.hsva = (h, int(s*f), v, int(a*f))
                self.target(note.pos, color, filled=False)

        cv.CvtColor(self.frame, self.frame_rgb, cv.CV_BGR2RGB)
        pg_img = pygame.image.frombuffer(
                self.frame_rgb.tostring(), cv.GetSize(self.frame), "RGB")
        self.window_surface.blit(pg_img, (0,0))

        if self.show_binary:
            cv.Merge(self.mask2, self.mask2, self.mask2, None, self.miniature)
            pg_img = pygame.image.frombuffer(
                    self.miniature.tostring(), cv.GetSize(self.miniature), "RGB")
            self.window_surface.blit(pg_img, (0,0))

        self.window_surface.blit(self.canvas, (0,0))
        pygame.display.update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type is QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type is KEYDOWN:
                if event.key is K_ESCAPE:
                    pygame.event.post(pygame.event.Event(QUIT))

    def run(self):

        def next_frame():
            self.frame = cv.QueryFrame(self.camera)
            cv.Flip(self.frame, None, 1)
            return self.frame

        while next_frame():
            self.handle_events()
            self.process()
            yield
            self.display()

        # No webcam frame?
        print "No webcam frame! Exiting..."
        sys.exit(1)


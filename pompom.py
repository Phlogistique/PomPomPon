import cv
import time
from itertools import cycle

class PomPomPon:
    COLORS = cycle([
        cv.CV_RGB(255,0,0), cv.CV_RGB(0,255,0), cv.CV_RGB(0,0,255),
        cv.CV_RGB(255,255,0), cv.CV_RGB(255,0,255), cv.CV_RGB(0,255,255)])

    def __init__(self, hue_target=127, hue_tolerance=40, sat_target=127,
            sat_tolerance=40, val_target=127, val_tolerance=50):

        self.hue_target = hue_target
        self.hue_tolerance = hue_tolerance
        self.sat_target = sat_target
        self.sat_tolerance = sat_tolerance
        self.val_target = val_target
        self.val_tolerance = val_tolerance

        self.color = PomPomPon.COLORS.next()

        self.calibration_done = False

        self.set_bounds()

    def set_target(self, hue_target=127, sat_target=127, val_target=127):
        self.hue_target = hue_target
        self.sat_target = sat_target
        self.val_target = val_target
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

class PomPom:
    def _window_name(name):
        return "PomPom - %s" % name

    INPUT_WINDOW = _window_name("Main window")
    PROCESSING_WINDOW = _window_name("Traitement")
    INTERSECT_WINDOW = _window_name("Intersect")

    SMOOTH_PARAM = "Aperture du flou"

    def cb_set(self, attr):
        def _():
            for i in self.pompom:
                setattr(i, attr, val)
                i.set_bounds()
        return _

    def set_aperture(self, aperture):
        self.aperture = aperture * 2 + 1

    def on_mouse(self, event, x, y, flags, param):

        if event != cv.CV_EVENT_LBUTTONUP:
            return

        pompon = self.pomponi.next()
        hue, sat, val = self.smooth_frame[y,x] # (y,x), not (x,y). No idea why
        pompon.set_target(hue, sat, val)

        print "color at (%d,%d) = (%d,%d,%d)" % (x, y, hue, sat, val)

    def __init__(self):

        # init parameters

        self.dilatation = 3

        initial_aperture = 10
        self.set_aperture(initial_aperture)

        self.size = (320, 240) #FIXME

        self.pompon = [PomPomPon(), PomPomPon()]
        self.pomponi = cycle(self.pompon)

        # init UI
        cv.NamedWindow(self.INPUT_WINDOW, cv.CV_WINDOW_AUTOSIZE)
        cv.NamedWindow(self.PROCESSING_WINDOW, cv.CV_WINDOW_AUTOSIZE)

        cv.SetMouseCallback(self.INPUT_WINDOW, self.on_mouse)

        cv.CreateTrackbar("Hue tolerance", self.PROCESSING_WINDOW,
                self.pompon[0].hue_tolerance, 127, self.cb_set("hue_tolerance"))
        cv.CreateTrackbar("Sat tolerance", self.PROCESSING_WINDOW,
                self.pompon[0].sat_tolerance, 127, self.cb_set("sat_tolerance"))
        cv.CreateTrackbar("Val tolerance", self.PROCESSING_WINDOW,
                self.pompon[0].val_tolerance, 127, self.cb_set("val_tolerance"))
        cv.CreateTrackbar("Flou", self.PROCESSING_WINDOW,
                initial_aperture, 20, self.set_aperture)
        cv.CreateTrackbar("Dilatation", self.PROCESSING_WINDOW,
                3, 20, self.cb_set("dilatation"))

        # init image capture
        self.camera = cv.CaptureFromCAM(-1) # any camera

        # create image buffers

        def img(chans=3):
            return cv.CreateImage(self.size, cv.IPL_DEPTH_8U, chans)

        self.resized_frame  = img()
        self.hsv_frame      = img()
        self.smooth_frame   = img()
        self.bin_frame      = img(1)
        self.mask           = img(1)

    def in_range(self, pompon, src, dst):
        cv.InRangeS(src, pompon.lower, pompon.upper, dst);

    def target(center, color, radius = 30):
        for i in [3,2,1]:
            cv.Circle(self.frame, (x, y), radius * i / 3.0, color, thickness=3)

    def coord(frac):
        return frac

    POSITIONS = map(coord, [
    #  (-1,1)             (1,1)
    #   +------------------+
    #   |                  |
    #   |                  |
    #   |                  |
    #   |                  |
    #   |                  |
    #   +------------------+
    #  (-1,-1)            (1,1)
            (-1.0/3, -1.0/2),
            (-2.0/3,      0),
            (-1.0/3,  1.0/2),
            (     0,  3.0/4),
            ( 1.0/3,  1.0/2),
            ( 2.0/3,      0),
            ( 1.0/3, -1.0/2)])

    RED = cv.CV_RGB(255,0,0)
    BLUE = cv.CV_RGB(0,0,255)

    def wait(self, seconds):
        start = time.time()
        while time.time() - start < seconds:
            self.step.next()
        
    def game(self):
        loop = game.loop()

        self.left = self.coord((-0.7,0.7))
        self.right = self.coord((0.7,0.7))
        self.left_color = cv.CV_RGB(255,100,0))
        self.right_color = cv.CV_RGB(0,100,255))

        self.step = self.calibration_step
        self.wait(1)

        while not self.calibration_done:
            self.step.next()

        self.step = self.play_step
        while True:
            self.step.next()

    def calibration_step(self):
        self.target(self.left, self.left_color)
        self.target(self.right, self.right_color)

    def play_step(self):
        pass

    def loop(self):

        def next_frame():
            self.frame = cv.QueryFrame(self.camera)
            return self.frame
        
        def seq_to_iter(seq):
            while seq:
                yield seq
                seq = seq.h_next()

        def rect_size(r):
            _,_,w,h = r
            return w * h


        while next_frame():

            cv.Resize(self.frame, self.resized_frame)
            cv.Flip(self.resized_frame, None, 1)
            cv.CvtColor(self.resized_frame, self.hsv_frame, cv.CV_RGB2HSV)
            cv.Smooth(self.hsv_frame, self.smooth_frame, cv.CV_GAUSSIAN,
                    self.aperture)

            for p in self.pompon:
                if p.calibration_done:

                    self.in_range(p, self.smooth_frame, self.bin_frame)
                    cv.Dilate(self.bin_frame, self.mask, None, self.dilatation);

                    contour = seq_to_iter(cv.FindContours(self.mask,
                            cv.CreateMemStorage(), cv.CV_RETR_EXTERNAL,
                            cv.CV_CHAIN_APPROX_SIMPLE));

                    rects = map((lambda c: cv.BoundingRect(c, 0)), contour)
                    if rects:
                        x,y,w,h = max(rects, key=rect_size)
                        
                        cv.Rectangle(self.resized_frame, (x, y), (x+w, y+h),
                                p.color, 3)

            cv.ShowImage(self.INPUT_WINDOW, self.resized_frame)

            yield
            cv.WaitKey(20)

        # No webcam frame?
        print "No webcam frame! Exiting..."
        sys.exit 1

a = PomPom().run()


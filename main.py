from pompom import PomPom
import argparse

parser = argparse.ArgumentParser(description='Pom-pom pom-pon!')
parser.add_argument('-b', '--show-binary', action='store_true',
        help='Show a binary image that shows what is detected by OpenCV')
parser.add_argument('-f', '--fullscreen', action='store_true',
        help='Show a binary image that shows what is detected by OpenCV')
parser.add_argument('-t', '--calibration-time', type=int, default=10,
        help='Number of seconds allowed for calibration')
parser.add_argument('-d', '--delay', type=int, default=0,
        help='Add a compensation to the display lag (milliseconds)')
parser.add_argument('song', type=str)
parser.add_argument('steps', type=str)
args = parser.parse_args()
PomPom(args.song, args.steps, show_binary=args.show_binary,
        calibration_time=args.calibration_time, delay=args.delay,
        fullscreen=args.fullscreen)

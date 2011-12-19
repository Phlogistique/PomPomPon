from pompom import PomPom
import argparse

parser = argparse.ArgumentParser(description='Pom-pom pom-pon!')
parser.add_argument('-b', '--show-binary', action='store_true',
        help='Show a binary image that shows what is detected by OpenCV')
parser.add_argument('song', type=str)
parser.add_argument('steps', type=str)
args = parser.parse_args()
PomPom(args.song, args.steps, show_binary=args.show_binary)

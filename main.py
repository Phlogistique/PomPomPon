from pompom import PomPom
import argparse

parser = argparse.ArgumentParser(description='Pom-pom pom-pon!')
parser.add_argument('-b', '--show-binary', action='store_true',
        help='Show a binary image that shows what is detected by OpenCV')
args = parser.parse_args()
print args
PomPom(show_binary=args.show_binary)

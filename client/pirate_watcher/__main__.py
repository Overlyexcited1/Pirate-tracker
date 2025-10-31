from pirate_watcher.watcher import run_watcher
import argparse
parser = argparse.ArgumentParser(description="Pirate watcher")
parser.add_argument("--log", help="Path to Game.log", required=False)
args = parser.parse_args()
run_watcher(args.log)

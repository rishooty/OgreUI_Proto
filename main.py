from controllers.overlay import ControllerOverlayApp
import sys

def main():
    # Get profile name and forced layout from command line arguments
    profile_name = sys.argv[1] if len(sys.argv) > 1 else None
    forced_layout = sys.argv[2] if len(sys.argv) > 2 else None

    app = ControllerOverlayApp(profile_name, forced_layout)
    app.run()

if __name__ == "__main__":
    main()

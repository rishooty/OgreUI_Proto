from controllers.overlay import ControllerOverlayApp
import sys

def main():
    # Get profile name from command line argument
    profile_name = sys.argv[1] if len(sys.argv) > 1 else None

    app = ControllerOverlayApp(profile_name)
    app.run()

if __name__ == "__main__":
    main()

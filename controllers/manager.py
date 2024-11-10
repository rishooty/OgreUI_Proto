import sdl2
import sdl2.ext
import yaml
from pathlib import Path
import sys

class ControllerManager:
    def __init__(self, profile_name=None):
        if sdl2.SDL_WasInit(sdl2.SDL_INIT_GAMECONTROLLER) == 0:
            sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER)
        self.controllers = {}
        self.profiles = {}
        self.active_profile = None
        self.load_profiles(profile_name)

    def detect_controllers(self):
        num_joysticks = sdl2.SDL_NumJoysticks()
        for i in range(num_joysticks):
            if sdl2.SDL_IsGameController(i):
                controller = sdl2.SDL_GameControllerOpen(i)
                if controller:
                    joy_id = sdl2.SDL_JoystickInstanceID(
                        sdl2.SDL_GameControllerGetJoystick(controller)
                    )
                    if joy_id not in self.controllers:  # Only add if not already present
                        self.controllers[joy_id] = {
                            "controller": controller,
                            "type": None,  # Will be set during detection
                            "overlay": None  # Will be set when overlay is created
                        }
                        print(f"Controller {joy_id} connected")  # Debug output

    def __del__(self):
        # Clean up controllers
        for controller_data in self.controllers.values():
            if controller_data["controller"]:
                sdl2.SDL_GameControllerClose(controller_data["controller"])

    def load_profiles(self, profile_name=None):
        # Get all YAML files in the profiles directory
        profile_dir = Path("profiles")
        if not profile_dir.exists():
            print(f"Error: profiles directory not found at {profile_dir.absolute()}")
            sys.exit(1)

        yaml_files = list(profile_dir.glob("*.yaml"))
        if not yaml_files:
            print(f"Error: No YAML profiles found in {profile_dir.absolute()}")
            sys.exit(1)

        # Load all profiles
        for profile_path in yaml_files:
            profile_key = profile_path.stem  # Get filename without extension
            try:
                with open(profile_path) as f:
                    self.profiles[profile_key] = yaml.safe_load(f)
                print(f"Loaded profile: {profile_key}")
            except yaml.YAMLError as e:
                print(f"Error loading {profile_path}: {e}")
                continue

        # Set active profile
        if profile_name:
            if profile_name in self.profiles:
                self.active_profile = profile_name
                print(f"Active profile set to: {profile_name}")
            else:
                print(f"Error: Profile '{profile_name}' not found")
                print(f"Available profiles: {list(self.profiles.keys())}")
                sys.exit(1)
        else:
            # If no profile specified, use the first one found
            self.active_profile = list(self.profiles.keys())[0]
            print(f"No profile specified. Using default: {self.active_profile}")

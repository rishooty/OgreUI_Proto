# controllers/hotkey_manager.py
import os
import yaml
from pathlib import Path
import sdl2

class HotkeyManager:
    def __init__(self):
        self.active_buttons = set()
        self.hotkeys = {}
        self.load_hotkeys()

    def load_hotkeys(self):
        hotkey_path = Path("profiles/hotkeys.yaml")
        if hotkey_path.exists():
            with open(hotkey_path) as f:
                self.hotkeys = yaml.safe_load(f)
                print(f"Loaded hotkeys: {self.hotkeys}")

    def get_button_name(self, button):
        button_names = {
            sdl2.SDL_CONTROLLER_BUTTON_GUIDE: "Guide",
            sdl2.SDL_CONTROLLER_BUTTON_START: "Start",
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: "Up",
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: "Down",
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: "Left",
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: "Right",
            sdl2.SDL_CONTROLLER_BUTTON_Y: "North",
            sdl2.SDL_CONTROLLER_BUTTON_A: "South",
            sdl2.SDL_CONTROLLER_BUTTON_X: "West",
            sdl2.SDL_CONTROLLER_BUTTON_B: "East",
            sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: "RB",
            sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: "LB"
        }
        return button_names.get(button)

    def handle_button_event(self, button, pressed):
        button_name = self.get_button_name(button)
        if not button_name:
            return None

        if pressed:
            self.active_buttons.add(button_name)
        else:
            self.active_buttons.discard(button_name)

        return self.get_display_info()

    def get_display_info(self):
        if not self.active_buttons:
            return None

        # Navigate the hotkey tree
        current_level = self.hotkeys.get("mappings", {})
        for button in sorted(self.active_buttons):
            if button in current_level:
                current_level = current_level[button]
            else:
                return None

        # Format the display based on the type
        if "Dpad" in current_level:
            return {
                "type": "dpad",
                "up": current_level["Dpad"].get("Up", ""),
                "down": current_level["Dpad"].get("Down", ""),
                "left": current_level["Dpad"].get("Left", ""),
                "right": current_level["Dpad"].get("Right", "")
            }
        elif "Face" in current_level:
            return {
                "type": "face",
                "north": current_level["Face"].get("North", ""),
                "south": current_level["Face"].get("South", ""),
                "west": current_level["Face"].get("West", ""),
                "east": current_level["Face"].get("East", "")
            }
        elif "Shoulders" in current_level:
            return {
                "type": "shoulders",
                "rb": current_level["Shoulders"].get("RB", ""),
                "rt": current_level["Shoulders"].get("RT", ""),
                "lb": current_level["Shoulders"].get("LB", ""),
                "lt": current_level["Shoulders"].get("LT", "")
            }
        elif "Single" in current_level:
            return {
                "type": "single",
                "text": current_level["Single"]
            }
        return None

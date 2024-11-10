from ui.gtk_overlay import ControllerOverlay
from controllers.manager import ControllerManager
from controllers.hotkey_manager import HotkeyManager
import sdl2
import sdl2.ext
from gi.repository import Gtk, GLib
import threading
import time

class ControllerOverlayApp:
    def __init__(self, profile_name=None):
        self.controller_manager = ControllerManager(profile_name)
        self.hotkey_manager = HotkeyManager()  # Add this line
        self.overlays = {}
        self.running = True

        # Initialize GTK
        Gtk.init(None)

        # Setup controller detection callback
        GLib.timeout_add(100, self.check_controllers)

        # Start SDL event thread
        self.sdl_thread = threading.Thread(target=self.sdl_event_loop)
        self.sdl_thread.daemon = True
        self.sdl_thread.start()

    def sdl_event_loop(self):
        while self.running:
            for event in sdl2.ext.get_events():
                if event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                    button = event.cbutton.button
                    joy_id = event.cbutton.which

                    # Check for hotkey combinations first
                    hotkey_info = self.hotkey_manager.handle_button_event(button, True)
                    if hotkey_info:
                        # Update overlay with hotkey information
                        if joy_id in self.controller_manager.controllers:
                            controller_data = self.controller_manager.controllers[joy_id]
                            if controller_data["overlay"]:
                                controller_data["overlay"].update_hotkey_display(hotkey_info)
                    elif button == sdl2.SDL_CONTROLLER_BUTTON_GUIDE:
                        print("Guide button pressed!")
                        self.handle_guide_press(joy_id)
                    else:
                        # Handle regular button press
                        self.handle_button_press(joy_id, button)

                elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                    button = event.cbutton.button
                    joy_id = event.cbutton.which

                    # Update hotkey state
                    hotkey_info = self.hotkey_manager.handle_button_event(button, False)
                    if hotkey_info:
                        # Update overlay with new hotkey information
                        if joy_id in self.controller_manager.controllers:
                            controller_data = self.controller_manager.controllers[joy_id]
                            if controller_data["overlay"]:
                                controller_data["overlay"].update_hotkey_display(hotkey_info)
                    elif button == sdl2.SDL_CONTROLLER_BUTTON_GUIDE:
                        print("Guide button released!")
                        self.handle_guide_release(joy_id)
                    else:
                        # Handle regular button release
                        self.handle_button_release(joy_id, button)

                # Add back axis motion handling
                elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                    try:
                        joy_id = event.caxis.which
                        axis = event.caxis.axis
                        value = event.caxis.value

                        # Validate the controller exists before processing
                        if joy_id in self.controller_manager.controllers:
                            self.handle_axis_motion(joy_id, axis, value)
                    except Exception as e:
                        print(f"Error handling axis motion: {e}")


    def handle_guide_press(self, joy_id):
        # Handle guide button specifically
        if joy_id in self.controller_manager.controllers:
            controller_data = self.controller_manager.controllers[joy_id]
            if controller_data["overlay"]:
                button_info = {
                    'color': '#FF00FF',  # Special color for guide
                    'label': 'Guide'
                }
                controller_data["overlay"].update_button_display(button_info)

    def handle_guide_release(self, joy_id):
        # Clear guide button display
        if joy_id in self.controller_manager.controllers:
            controller_data = self.controller_manager.controllers[joy_id]
            if controller_data["overlay"]:
                button_info = {
                    'color': '#808080',
                    'label': ''
                }
                controller_data["overlay"].update_button_display(button_info)

    def handle_axis_motion(self, joy_id, axis, value):
        # Add threshold and rate limiting
        AXIS_THRESHOLD = 16384  # About half of max value (32768)

        try:
            if abs(value) < AXIS_THRESHOLD:
                return

            # Add rate limiting using a class variable
            current_time = time.time()
            if hasattr(self, '_last_axis_update'):
                if (current_time - self._last_axis_update) < 0.016:  # ~60fps
                    return
            self._last_axis_update = current_time

            print(f"Axis motion detected: joy_id={joy_id}, axis={axis}, value={value}")

            if joy_id in self.controller_manager.controllers:
                controller_data = self.controller_manager.controllers[joy_id]
                if controller_data["overlay"] and controller_data["type"]:
                    axis_info = self.get_axis_info(
                        controller_data["type"],
                        axis,
                        value > 0
                    )
                    if axis_info:
                        # Use GLib.idle_add for thread-safe GUI updates
                        GLib.idle_add(
                            self._update_axis_display,
                            controller_data["overlay"],
                            axis_info
                        )
        except Exception as e:
            print(f"Error in handle_axis_motion: {e}")

    def _update_axis_display(self, overlay, axis_info):
        """Thread-safe method to update the overlay"""
        try:
            overlay.update_button_display(axis_info)
        except Exception as e:
            print(f"Error updating axis display: {e}")
        return False  # Important: return False to prevent repeated calls



    def get_axis_info(self, controller_type, axis, is_positive):
        profile = self.controller_manager.profiles.get(
            self.controller_manager.active_profile, {}
        )
        mapping = profile.get("mappings", {}).get(controller_type, {})
        axes = mapping.get("axes", {})

        axis_name = self.get_sdl_axis_name(axis)
        print(f"Looking for axis: {axis_name}")  # Debug

        # Find the matching axis by sdl_axis value
        for axis_key, axis_data in axes.items():
            if axis_data["sdl_axis"] == axis_name:
                result = axis_data["positive" if is_positive else "negative"]
                print(f"Found axis mapping: {result}")  # Debug
                return result

        return {"color": "#808080", "label": ""}

    def get_sdl_axis_name(self, axis):
        axis_names = {
            sdl2.SDL_CONTROLLER_AXIS_LEFTX: "LEFTX",
            sdl2.SDL_CONTROLLER_AXIS_LEFTY: "LEFTY",
            sdl2.SDL_CONTROLLER_AXIS_RIGHTX: "RIGHTX",
            sdl2.SDL_CONTROLLER_AXIS_RIGHTY: "RIGHTY",
            sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT: "TRIGGERLEFT",
            sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT: "TRIGGERRIGHT"
        }
        return axis_names.get(axis, "UNKNOWN")

    def remove_controller(self, joy_id):
        if joy_id in self.overlays:
            self.overlays[joy_id].hide()
            del self.overlays[joy_id]
        if joy_id in self.controller_manager.controllers:
            del self.controller_manager.controllers[joy_id]

    def check_controllers(self):
        self.controller_manager.detect_controllers()
        for joy_id, controller_data in self.controller_manager.controllers.items():
            if controller_data["overlay"] is None:
                # Create new overlay for this controller
                player_num = len(self.overlays)
                if player_num < 4:  # Maximum 4 players
                    corner = ["TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT"][player_num]
                    overlay = ControllerOverlay(corner)
                    overlay.show()
                    controller_data["overlay"] = overlay
                    self.overlays[joy_id] = overlay

        return True  # Keep the timeout active

    def handle_button_press(self, joy_id, button):
        print(f"Button press detected: joy_id={joy_id}, button={button}")  # Debug
        if joy_id in self.controller_manager.controllers:
            controller_data = self.controller_manager.controllers[joy_id]
            if controller_data["type"] is None:
                # First button press - detect controller type
                controller_data["type"] = self.detect_controller_type(button)
                print(f"Controller type detected: {controller_data['type']}")  # Debug

            # Update overlay display based on button press
            if controller_data["overlay"]:
                button_info = self.get_button_info(controller_data["type"], button)
                print(f"Updating overlay with: {button_info}")  # Debug
                controller_data["overlay"].update_button_display(button_info)

    def handle_button_release(self, joy_id, button):
        print(f"Button release detected: joy_id={joy_id}, button={button}")  # Debug
        if joy_id in self.controller_manager.controllers:
            controller_data = self.controller_manager.controllers[joy_id]

            # Only handle release if we have a valid controller type
            if controller_data["type"] and controller_data["overlay"]:
                # Clear the button display or show default state
                button_info = {
                    'color': '#808080',  # Grey out or use your default color
                    'label': '',         # Clear the label
                    'sdl_button': self.get_sdl_button_name(button)  # Optional: for debugging
                }
                print(f"Clearing overlay for button: {button_info}")  # Debug
                controller_data["overlay"].update_button_display(button_info)

    # User is prompted to press X, or C if there is no X
    def detect_controller_type(self, button):
        if button == sdl2.SDL_CONTROLLER_BUTTON_X:
            return "XBOX"
        elif button == sdl2.SDL_CONTROLLER_BUTTON_A:
            return "PS"
        elif button == sdl2.SDL_CONTROLLER_BUTTON_Y:
            return "NINTENDO"
        elif button == sdl2.SDL_CONTROLLER_BUTTON_B:
            return "GC"
        elif button == sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT:
            return "Sega"
        return "UNKNOWN" # I'll need to come up with something for neo geo

    def get_button_info(self, controller_type, button):
        if not self.controller_manager.active_profile:
            return {"color": "#808080", "label": ""}

        profile = self.controller_manager.profiles.get(
            self.controller_manager.active_profile, {}
        )
        mapping = profile.get("mappings", {}).get(controller_type, {})
        buttons = mapping.get("buttons", {})  # Get the buttons section

        # Find the corresponding button mapping
        for btn_name, btn_info in buttons.items():  # Iterate through buttons
            if btn_info["sdl_button"] == self.get_sdl_button_name(button):
                return btn_info

        return {"color": "#808080", "label": ""}

    def get_sdl_button_name(self, button):
        button_names = {
            sdl2.SDL_CONTROLLER_BUTTON_A: "A",
            sdl2.SDL_CONTROLLER_BUTTON_B: "B",
            sdl2.SDL_CONTROLLER_BUTTON_X: "X",
            sdl2.SDL_CONTROLLER_BUTTON_Y: "Y",
            sdl2.SDL_CONTROLLER_BUTTON_GUIDE: "Guide",  # Add this
            sdl2.SDL_CONTROLLER_BUTTON_START: "Start",  # Add this
            sdl2.SDL_CONTROLLER_BUTTON_BACK: "Back"     # Add this
        }
        return button_names.get(button)

    def run(self):
        try:
            Gtk.main()
        finally:
            self.running = False
            sdl2.SDL_Quit()

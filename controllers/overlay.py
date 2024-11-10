from ui.gtk_overlay import ControllerOverlay
from controllers.manager import ControllerManager
import sdl2
from gi.repository import Gtk, GLib
import threading

class ControllerOverlayApp:
    def __init__(self, profile_name=None,forced_layout=None):
        self.controller_manager = ControllerManager(profile_name, forced_layout)
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
        event = sdl2.SDL_Event()
        while self.running:
            while sdl2.SDL_PollEvent(event):
                if event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                    GLib.idle_add(
                        self.handle_button_press,
                        event.cbutton.which,
                        event.cbutton.button
                    )
                elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                    # Only process significant axis movement
                    if abs(event.caxis.value) > 16384:  # Half of max value
                        GLib.idle_add(
                            self.handle_axis_motion,
                            event.caxis.which,
                            event.caxis.axis,
                            event.caxis.value
                        )
                elif event.type == sdl2.SDL_CONTROLLERDEVICEADDED:
                    GLib.idle_add(self.check_controllers)
                elif event.type == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                    GLib.idle_add(self.remove_controller, event.cdevice.which)
            sdl2.SDL_Delay(16)

    def handle_axis_motion(self, joy_id, axis, value):
        print(f"Axis motion detected: joy_id={joy_id}, axis={axis}, value={value}")
        if joy_id in self.controller_manager.controllers:
            controller_data = self.controller_manager.controllers[joy_id]
            if controller_data["overlay"]:
                axis_info = self.get_axis_info(
                    controller_data["type"],
                    axis,
                    value > 0
                )
                print(f"Axis info: {axis_info}")  # Debug
                if axis_info:
                    print(f"Updating overlay with axis info: {axis_info}")  # Debug
                    controller_data["overlay"].update_button_display(axis_info)

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
            sdl2.SDL_CONTROLLER_BUTTON_Y: "Y"
        }
        return button_names.get(button, "UNKNOWN")

    def run(self):
        try:
            Gtk.main()
        finally:
            self.running = False
            sdl2.SDL_Quit()

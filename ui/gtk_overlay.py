import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, GtkLayerShell, Gdk, GLib
from gi.repository import Pango

class ControllerOverlay:
    def __init__(self, corner, controller_type=None):
        # Create the window
        self.window = Gtk.Window()

        # Initialize layer shell
        GtkLayerShell.init_for_window(self.window)

        # Set layer (OVERLAY puts it above normal windows)
        GtkLayerShell.set_layer(self.window, GtkLayerShell.Layer.OVERLAY)

        self.window.set_size_request(200, 200)  # Increased size

        # Create a container for our content
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.set_homogeneous(True)  # Equal spacing
        self.window.add(self.box)

        # Create a label for button display
        self.label = Gtk.Label()
        self.label.set_justify(Gtk.Justification.CENTER)
        self.label.set_line_wrap(True)
        self.label.set_line_wrap_mode(2)  # PANGO_WRAP_WORD
        self.box.pack_start(self.label, True, True, 0)

        # Set the corner anchors based on position
        if corner == "TOP_LEFT":
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.TOP, True)
        elif corner == "TOP_RIGHT":
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.TOP, True)
        elif corner == "BOTTOM_LEFT":
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.BOTTOM, True)
        elif corner == "BOTTOM_RIGHT":
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.BOTTOM, True)

        # Set margins (distance from edges)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.TOP, 20)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.LEFT, 20)

        # Add controller type and styling
        self.controller_type = controller_type
        self.style_provider = Gtk.CssProvider()
        self.style_context = self.window.get_style_context()
        self.style_context.add_provider(
            self.style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def get_contrast_color(self, background_color):
        """
        Calculate whether to use black or white text based on background color
        Using W3C algorithm for brightness
        """
        # Remove the '#' if present
        bg_color = background_color.lstrip('#')

        # Convert hex to RGB
        try:
            r = int(bg_color[0:2], 16)
            g = int(bg_color[2:4], 16)
            b = int(bg_color[4:6], 16)
        except ValueError:
            return "white"  # Default to white on error

        # Calculate brightness using W3C formula
        brightness = (r * 299 + g * 587 + b * 114) / 1000

        # Return black for bright backgrounds, white for dark ones
        return "black" if brightness > 125 else "white"

    def update_button_display(self, button_info):
        def _update():
            try:
                # Get the appropriate text color based on background
                text_color = self.get_contrast_color(button_info['color'])

                # Create CSS for background color
                css = f"""
                window {{
                    background-color: {button_info['color']};
                    border-radius: 10px;
                    padding: 10px;
                }}
                """
                self.style_provider.load_from_data(css.encode())

                # Get and modify the Pango context for font scaling
                context = self.label.get_pango_context()
                font = context.get_font_description()
                font.set_size(48 * Pango.SCALE)  # Scale factor
                font.set_weight(Pango.Weight.ULTRABOLD)
                context.set_font_description(font)

                # Update label with contrast-appropriate color, size, and bold text
                self.label.set_markup(
                    f'<span color="{text_color}" font_desc="48" weight="bold">{button_info["label"]}</span>'
                )
            except Exception as e:
                print(f"Error in update_button_display: {e}")
            return False

        # Ensure we're on the main GTK thread
        if not Gtk.main_level():
            GLib.idle_add(_update)
        else:
            _update()


    def update_hotkey_display(self, hotkey_info):
        if hotkey_info["type"] == "single":
            self.update_button_display({
                'color': '#FF00FF',  # Magenta for hotkeys
                'label': hotkey_info["text"]
            })
        elif hotkey_info["type"] in ["dpad", "face", "shoulders"]:
            # Handle multi-button displays
            labels = []
            if "up" in hotkey_info: labels.append(f"↑: {hotkey_info['up']}")
            if "down" in hotkey_info: labels.append(f"↓: {hotkey_info['down']}")
            if "left" in hotkey_info: labels.append(f"←: {hotkey_info['left']}")
            if "right" in hotkey_info: labels.append(f"→: {hotkey_info['right']}")

            self.update_button_display({
                'color': '#FF00FF',  # Magenta for hotkeys
                'label': '\n'.join(labels)
            })

    def show(self):
        self.window.show_all()

    def hide(self):
        self.window.hide()

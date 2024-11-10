# Ogre UI - Python Prototype
*UI development is like an ogre, it has LAYERS*

Wayland (mainly sway) GTK overlay that translates input prompts of one controller
face button type to another.

WIP added bonus: I hope to add the ability to append mappings. Namely for the purposes
of hotkeys.
  - i.e. you hold down your HOME button and it lets you know which face button
    fast fowards, save-states, quits, etc.

Automatically detects what type of face buttons you have by asking you to press C
or X. If you press C it detects a 6-button sega controller, otherwise it assumes
nintendo, playstation, xbox, etc.

Seeing as this is likely going to be a heavy process on weaker systems,
I plan on translating this to a faster language like Go or C.

This version is simply a rapid prototype.

## Development

### Dependencies
* Fedora: sudo dnf install \
    gtk3-devel \
    gtk-layer-shell \
    gtk-layer-shell-devel \
    python3-gobject \
    gobject-introspection-devel
* Debian: sudo apt install python3-gi gir1.2-gtk-3.0 libgtk-layer-shell0 gir1.2-gtklayershell-0.1
* Arch: sudo pacman -S python-gobject gtk3 gtk-layer-shell

### Testing
source .venv/bin/activate
pip install
python main.py N64 2>&1 | tee debug.log

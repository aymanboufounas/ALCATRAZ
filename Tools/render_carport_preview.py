"""Render the imported carport offline; this is not a Unity capture."""
from pathlib import Path
from render_revision12_previews import native, mark
from render_current_previews import placed, cube
import render_supplied_previews as renderer


def main():
    scene = placed(native('Carport'), 3.2, (0, 0, 0))
    scene += [cube('Floor', (0, -.02, 0), (12, .04, 14), (.43, .46, .45, 1))]
    image = renderer.render(scene, size=(1280, 720), eye=(9, 6, 10), center=(0, 1.4, 0))
    mark(image, 'SUPPLIED WOODEN CARPORT / FULL SOURCE MESH').save(
        renderer.ROOT / 'Documentation/CarportPreview.png')


if __name__ == '__main__':
    main()

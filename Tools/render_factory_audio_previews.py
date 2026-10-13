"""Render the three native imports offline; these are not Unity gameplay captures."""
from pathlib import Path
from render_revision12_previews import native, mark
from render_current_previews import placed, cube
import render_supplied_previews as renderer


def main():
    output = renderer.ROOT / 'Documentation/FactoryAudioPreviews'
    output.mkdir(parents=True, exist_ok=True)
    views = [
        ('Factory', 10, (27, 18, 39), (0, 4, 0)),
        ('SpeakerArray', 2.5, (3, 2, 4), (0, 1.25, 0)),
        ('Radio', .35, (.5, .3, .6), (0, .175, 0)),
    ]
    for name, height, eye, center in views:
        scene = placed(native(name), height, (0, 0, 0))
        scene += [cube('Preview floor', (0, -.02, 0),
                       (height * 5, .04, height * 5), (.38, .4, .4, 1))]
        image = renderer.render(scene, size=(1280, 720), eye=eye, center=center)
        mark(image, 'SUPPLIED ' + name.upper() + ' / FULL SOURCE MESH').save(output / (name + '.png'))
        print('Rendered ' + name, flush=True)


if __name__ == '__main__':
    main()

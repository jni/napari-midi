# napari-midi

[![License](https://img.shields.io/pypi/l/napari-midi.svg?color=green)](https://github.com/jni/napari-midi/raw/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-midi.svg?color=green)](https://pypi.org/project/napari-midi)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-midi.svg?color=green)](https://python.org)
[![tests](https://github.com/jni/napari-midi/workflows/tests/badge.svg)](https://github.com/jni/napari-midi/actions)
[![codecov](https://codecov.io/gh/jni/napari-midi/branch/master/graph/badge.svg)](https://codecov.io/gh/jni/napari-midi)

Control napari with a USB MIDI controller

----------------------------------

## What works

- bidirectional updates of the button and rotary dial LEDs
- Fast and slow scrolling dials
- Opacity of the topmost layer with the slider
- All out-of-tree code: no hacking napari internals needed 🎉
- Pretty decent API I think...! See all the `.bind_` calls at the end of the file.

## What doesn't work

- Any kind of documentation or comments 😂
- Thread safety — see #2326 for how to do it properly, I mistakenly thought that our events would handle that for us 😬, thanks @tlambert03 for clarifying that the most certainly do not! 😂
- (same vein) race conditions. Some of our events don't seem to carry the event data (?), and checking the source for the value sometimes returns the old value — hence the `time.sleep` currently there.
- super clunky implementation

## Installation

You can install `napari-midi` via [pip]:

    pip install git+https://github.com/jni/napari-midi

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-midi" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/jni/napari-midi/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/

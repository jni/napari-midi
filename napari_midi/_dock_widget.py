"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
import napari
import numpy as np
from magicgui import magic_factory
from napari_plugin_engine import napari_hook_implementation

from .xtouchmini import XTouchMini


def new_label(layer):
    """Set the currently selected label to the largest used label plus one."""
    layer.selected_label = np.max(layer.data) + 1


@magic_factory
def activate_default_bindings(viewer: napari.Viewer, labels_layer: "napari.layers.Labels"):
    xt = XTouchMini(viewer)
    xt.bind_current_step('b', 0, 0, 1)
    xt.bind_current_step('b', 1, 2, 3)
    xt.bind_slider('b')
    xt.bind_button('b', (0, 0), viewer.dims, 'ndisplay', attr_value=3)
    xt.bind_button('b', (0, 1), viewer.dims, 'ndisplay', attr_value=2)
    xt.bind_button('b', (1, 2), labels_layer, 'visible')
    xt.bind_button('b', (1, 0), labels_layer, 'mode', attr_value='erase')
    xt.bind_button('b', (2, 0), labels_layer, 'mode', attr_value='paint')
    xt.bind_button('b', (1, 1), labels_layer, 'mode', attr_value='fill')
    xt.bind_button('b', (2, 1), labels_layer, 'mode', attr_value='pick')
    xt.bind_button('b', (2, 2), labels_layer, 'mode', attr_value='pan_zoom')
    xt.bind_action('b', (2, 3), new_label, (labels_layer,))


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return activate_default_bindings

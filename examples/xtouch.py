import napari
from napari_midi.xtouchmini import XTouchMini
import numpy as np

from napari.layers.labels._labels_key_bindings import new_label
from skimage import data, filters, morphology
from scipy import ndimage as ndi

cells3d = data.cells3d()

viewer = napari.view_image(
    cells3d[::2],
    channel_axis=1,
    name=['membranes', 'nuclei'],
    scale=[0.58, 0.26, 0.26],
)
membrane, nuclei = cells3d.transpose((1, 0, 2, 3)) / np.max(cells3d)
edges = filters.scharr(nuclei)
denoised = ndi.median_filter(nuclei, size=3)
thresholded = denoised > filters.threshold_li(denoised)
cleaned = morphology.remove_small_objects(
    morphology.remove_small_holes(thresholded, 20**3),
    20**3,
)

segmented = ndi.label(cleaned)[0]

# # better segmentation
#
# from skimage import segmentation
# maxima = ndi.label(morphology.local_maxima(filters.gaussian(nuclei, sigma=10)))[0]
# markers_big = morphology.dilation(maxima, morphology.ball(5))
#
# segmented = segmentation.watershed(
#     edges,
#     markers_big,
#     mask=cleaned,
# )

labels_layer = viewer.add_labels(segmented[::2], scale=[0.58, 0.26, 0.26])

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

napari.run()

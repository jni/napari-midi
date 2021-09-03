import napari
import numpy as np
import pandas as pd
import rtmidi.midiutil
import time


class XTouchMini:
    def __init__(self, viewer, hold_thresh=0.5):
        self.viewer = viewer
        self.midi_in, _ = rtmidi.midiutil.open_midiinput(0)
        self.midi_in.set_callback(self.receive_set)
        self.midi_out, _ = rtmidi.midiutil.open_midioutput(0)
        table = []
        press_dict = {}
        control_ids = {
            'a-button': np.arange(24).reshape((3, 8)),
            'b-button': np.arange(24, 48).reshape((3, 8)),
            'a-rotary': np.arange(1, 9),
            'b-rotary': np.arange(11, 19),
            'a-slider': np.array([9]),
            'b-slider': np.array([10]),
        }
        for name, array in control_ids.items():
            layer, control_type = name.split('-')
            for idx in np.ndindex(*array.shape):
                control_id = array[idx]
                press_dict[control_id] = (array, idx)
                virtual2raw = 127 if control_type == 'button' else 1
                virtual2data = 1
                value = 0
                table.append((
                    layer,
                    control_type,
                    control_id,
                    idx,
                    value,
                    virtual2raw,
                    virtual2data,
                    None,
                    None,
                ))
        self.table = pd.DataFrame(
            table,
            columns=[
                'layer',  # midi control layer, 'a' or 'b'
                'type',  # 'rotary', 'button', or 'slider'
                'id',  # midi control ID
                'index',  # position of the control in logical space
                'value',  # value of the control in 0-127
                'virtual2raw',  # conv. factor when number of levels not 128
                'raw2data',  # conv factor to actual slider numbers
                'fw',  # function to apply slider values to viewer
                'inv',  # function to apply viewer values to slider
            ],
        )
        self.table.set_index('id', drop=False)

    def receive_set(self, message_time_tup, data):
        message, time = message_time_tup
        msg_type, control_id, value = message
        if msg_type == 186:  # rotary or slider
            self.receive_continuous(control_id, value)
        elif msg_type == 154:  # button press down
            self.receive_button(control_id, value)
        elif msg_type == 138:  # button press up
            self.receive_button(control_id, value)

    def receive_continuous(self, control_id, value):
        control = self.table.loc[control_id]
        if control['fw'] is not None:
            control['fw'](value)

    def receive_button(self, control_id, value):
        control = self.table.loc[control_id]
        if control['fw'] is not None:
            control['fw'](value)

    def send_continuous(self, control_id, value):
        self.midi_out.send_message((186, control_id, value))

    def send_button(self, button_id, value):
        sent_value = int(bool(value)) * 127
        message_id = 154 if sent_value else 138
        self.midi_out.send_message((message_id, button_id, sent_value))

    def bind_current_step(self, layer, axis, rotary0, rotary1):
        cond0 = (
            (self.table['index'] == (rotary0,))
            & (self.table['type'] == 'rotary')
            & (self.table['layer'] == layer)
        )
        rotary0_id = int(self.table.loc[cond0]['id'])
        cond1 = (
            (self.table['index'] == (rotary1,))
            & (self.table['type'] == 'rotary')
            & (self.table['layer'] == layer)
        )
        rotary1_id = int(self.table.loc[cond1]['id'])

        nsteps = self.viewer.dims.nsteps[axis]
        rot0_nsteps = min(nsteps, 13)
        self.table.loc[rotary0_id, 'virtual2raw'] = (v2r := 127 / rot0_nsteps)
        self.table.loc[rotary0_id, 'raw2data'] = (r2d := nsteps / 127)
        self.table.loc[rotary1_id, 'virtual2raw'] = (v2r1 := 127 / v2r)

        def process_current_step_event(ev):
            current_step = ev.value[axis]
            r0_value = int(current_step / r2d)
            self.table.loc[rotary0_id, 'value'] = r0_value
            self.send_continuous(rotary0_id, r0_value)
            r1_value = (current_step % v2r) * v2r1
            self.table.loc[rotary1_id, 'value'] = r1_value
            self.send_continuous(rotary1_id, r1_value)

        self.viewer.dims.events.current_step.connect(process_current_step_event)

        def fw0(value):
            prev_value = self.table.loc[rotary0_id, 'value']
            down = (prev_value > value) or (prev_value == value and value == 0)
            increment = int(np.round(v2r))
            if down:
                increment = -increment
            next_step = list(self.viewer.dims.current_step)
            next_step[axis] = np.clip(next_step[axis] + increment, 0, nsteps - 1)
            self.viewer.dims.current_step = tuple(next_step)

        self.table.loc[rotary0_id, 'fw'] = fw0

        def fw1(value):
            prev_value = self.table.loc[rotary1_id, 'value']
            up = (prev_value < value) or (prev_value == value and value == 127)
            next_step = list(self.viewer.dims.current_step)
            increment = 1 if up else -1
            next_step[axis] = np.clip(next_step[axis] + increment, 0, nsteps - 1)
            self.viewer.dims.current_step = tuple(next_step)

        self.table.loc[rotary1_id, 'fw'] = fw1

    def bind_slider(self, layer):
        table = self.table
        cond = (table['layer'] == layer) & (table['type'] == 'slider')
        slider_id = table.loc[cond, 'id']

        def change_opacity(value):
            vlayer = self.viewer.layers[-1]
            vlayer.opacity = value / 127

        table.loc[slider_id, 'fw'] = change_opacity

    def bind_button(
        self, control_layer, index, obj, attr, attr_value=True
    ):
        table = self.table
        cond = (table['layer'] == control_layer) & (table['index'] == index)
        button_id = table.loc[cond, 'id']

        def fw(val):
            if val == 127:
                if type(attr_value) is bool:
                    toggled_value = not getattr(obj, attr)
                    setattr(obj, attr, toggled_value)
                else:
                    setattr(obj, attr, attr_value)
            elif type(attr_value) is bool:
                self.send_button(button_id, getattr(obj, attr))

        table.loc[button_id, 'fw'] = fw

        def set_button(ev):
            # this function can get called on a separate thread before the
            # attribute has been updated, so we sleep to wait for the update
            time.sleep(0.3)
            if hasattr(ev, 'value'):
                value = ev.value
            else:
                value = getattr(ev.source, ev.type)
            if value == attr_value:
                self.send_button(button_id, 127)
            else:
                self.send_button(button_id, 0)

        event = getattr(obj.events, attr)
        event.connect(set_button)
        event(value=getattr(obj, attr), **{attr: getattr(obj, attr)})

    def bind_action(self, control_layer, index, function, args=(), kwargs={}):
        table = self.table
        cond = (table['layer'] == control_layer) & (table['index'] == index)
        button_id = table.loc[cond, 'id']

        def func(val):
            if val > 0:
                function(*args, **kwargs)

        table.loc[button_id, 'fw'] = func


def default_bindings(
    viewer: napari.Viewer,
    labels_layer: napari.layers.Labels,
):

    from napari.layers.labels._labels_key_bindings import new_label

    xt = XTouchMini(viewer)
    xt.bind_current_step('b', 0, 0, 1)
    xt.bind_current_step('b', 1, 2, 3)
    xt.bind_slider('b')
    xt.bind_button('b', (0, 0), viewer.dims, attr='ndisplay', attr_value=3)
    xt.bind_button('b', (0, 1), viewer.dims, attr='ndisplay', attr_value=2)
    xt.bind_button('b', (1, 2), labels_layer, attr='visible')
    xt.bind_button('b', (1, 0), labels_layer, 'mode', attr_value='erase')
    xt.bind_button('b', (2, 0), labels_layer, 'mode', attr_value='paint')
    xt.bind_button('b', (1, 1), labels_layer, 'mode', attr_value='fill')
    xt.bind_button('b', (2, 1), labels_layer, 'mode', attr_value='pick')
    xt.bind_button('b', (2, 2), labels_layer, 'mode', attr_value='pan_zoom')
    xt.bind_action('b', (2, 3), new_label, (labels_layer,))

    return xt

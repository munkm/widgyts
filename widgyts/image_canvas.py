import ipywidgets as ipywidgets
import traitlets
from ipydatawidgets import DataUnion, shape_constraints, \
        data_union_serialization
import numpy as np
from ipywidgets import widget_serialization

from .colormaps.colormaps import ColorMaps

from yt.data_objects.selection_data_containers import \
        YTSlice
from yt.data_objects.construction_data_containers import \
        YTQuadTreeProj
from yt.visualization.fixed_resolution import \
        FixedResolutionBuffer as frb
from yt.funcs import \
        ensure_list
from ._version import EXTENSION_VERSION

rgba_image_shape = shape_constraints(None, None, 4)
vmesh_shape = shape_constraints(None)

@ipywidgets.register
class ImageCanvas(ipywidgets.DOMWidget):
    """An example widget."""
    _view_name = traitlets.Unicode('ImageCanvasView').tag(sync=True)
    _model_name = traitlets.Unicode('ImageCanvasModel').tag(sync=True)
    _view_module = traitlets.Unicode('@data-exp-lab/yt-widgets').tag(sync=True)
    _model_module = traitlets.Unicode('@data-exp-lab/yt-widgets').tag(sync=True)
    _view_module_version = traitlets.Unicode(EXTENSION_VERSION).tag(sync=True)
    _model_module_version = traitlets.Unicode(EXTENSION_VERSION).tag(sync=True)
    image_array = DataUnion(dtype=np.uint8,
            shape_constraint=rgba_image_shape).tag(sync=True,
                    **data_union_serialization)
    width = traitlets.Int(256).tag(sync=True)
    height = traitlets.Int(256).tag(sync=True)

@ipywidgets.register
class FRBViewer(ipywidgets.DOMWidget):
    """View of a fixed resolution buffer.

    FRBViewer(width, height, px, py, pdx, pdy, val)

    This widget creates a view of a fixed resolution buffer of
    size (`width`, `height`) given data variables `px`, `py`, `pdx`, `pdy`,
    and val. Updates on the view of the fixed reolution buffer can be made
    by modifying traitlets `view_center`, `view_width`, or `Colormaps`

    Parameters
    ----------

    width : integer
        The width of the fixed resolution buffer output, in pixels
    height : integer
        The height of the fixed resolution buffer, in pixels
    px : array of floats
        x coordinates for the center of each grid box
    py : array of floats
        y coordinates for the center of each grid box
    pdx : array of floats
        Values of the half-widths for each grid box
    pdy : array of floats
        Values of the half-heights for each grid box
    val : array of floats
        Data values for each grid box
        The data values to be visualized in the fixed resolution buffer.
    colormaps : :class: `widgyts.Colormaps`
        This is the widgyt that controls traitlets associated with the
        colormap.
    view_center : tuple
        This is a length two tuple that represents the normalized center of
        the resulting FRBView.
    view_width : tuple
        This is a length two tuple that represents the height and with of the
        view, normalized to the original size of the image. (0.5, 0.5)
        represents a view of half the total data with and half the total
        data height.

    Examples
    --------
    To create a fixed resolution buffer view of a density field with this
    widget, and then to display it:

    >>> ds = yt.load("IsolatedGalaxy")
    >>> proj = ds.proj("density", "z")
    >>> frb1 = widgyts.FRBViewer(height=512, width=512, px=proj["px"],
    ...                          py=proj["py"], pdx=proj["pdx"],
    ...                          pdy=proj["pdy"], val = proj["density"])
    >>> display(frb1)

    """
    _view_name = traitlets.Unicode('FRBView').tag(sync=True)
    _model_name = traitlets.Unicode('FRBModel').tag(sync=True)
    _view_module = traitlets.Unicode('@data-exp-lab/yt-widgets').tag(sync=True)
    _model_module = traitlets.Unicode('@data-exp-lab/yt-widgets').tag(sync=True)
    _view_module_version = traitlets.Unicode(EXTENSION_VERSION).tag(sync=True)
    _model_module_version = traitlets.Unicode(EXTENSION_VERSION).tag(sync=True)
    width = traitlets.Int(512).tag(sync=True)
    height = traitlets.Int(512).tag(sync=True)
    px = DataUnion(dtype=np.float64,
            shape_constraint=vmesh_shape).tag(sync = True,
                    **data_union_serialization)
    py = DataUnion(dtype=np.float64,
            shape_constraint=vmesh_shape).tag(sync = True,
                    **data_union_serialization)
    pdx = DataUnion(dtype=np.float64,
            shape_constraint=vmesh_shape).tag(sync = True,
                    **data_union_serialization)
    pdy = DataUnion(dtype=np.float64,
            shape_constraint=vmesh_shape).tag(sync = True,
                    **data_union_serialization)
    val = DataUnion(dtype=np.float64,
            shape_constraint=vmesh_shape).tag(sync = True,
                    **data_union_serialization)
    colormaps = traitlets.Instance(ColorMaps).tag(sync = True,
            **widget_serialization)
    view_center = traitlets.Tuple((0.5, 0.5)).tag(sync=True, config=True)
    view_width = traitlets.Tuple((0.2, 0.2)).tag(sync=True, config=True)

    @traitlets.default('layout')
    def _layout_default(self):
        return ipywidgets.Layout(width = '{}px'.format(self.width),
                                 height ='{}px'.format(self.height))

    @traitlets.default('colormaps')
    def _colormap_load(self):
        return ColorMaps()

    def setup_controls(self):
        down = ipywidgets.Button(icon="arrow-down",
                layout=ipywidgets.Layout(width='auto', grid_area="down"))
        up = ipywidgets.Button(icon="arrow-up",
                layout=ipywidgets.Layout(width='auto', grid_area="up"))
        right = ipywidgets.Button(icon="arrow-right",
                layout=ipywidgets.Layout(width='auto', grid_area="right"))
        left = ipywidgets.Button(icon="arrow-left",
                layout=ipywidgets.Layout(width='auto', grid_area="left"))
        zoom_start = 1./(self.view_width[0])
        # By setting the dynamic range to be the ratio between coarsest and
        # finest, we ensure that at the fullest zoom, our smallest point will
        # be the size of our biggest point at the outermost zoom.
        dynamic_range = (max(self.pdx.max(), self.pdy.max()) /
                         min(self.pdx.min(), self.pdy.min()))

        zoom = ipywidgets.FloatSlider(min=0.5, max=dynamic_range, step=0.1,
                value=zoom_start, description="Zoom",
                layout=ipywidgets.Layout(width="auto", grid_area="zoom"))
        is_log = ipywidgets.Checkbox(value=False, description="Log colorscale")
        colormaps = ipywidgets.Dropdown(
                options=list(self.colormaps.cmaps.keys()),
                description="colormap",
                value = "viridis")
        min_val = ipywidgets.BoundedFloatText(description="lower colorbar bound:",
                value=self.val.min(), min=self.val.min(), max=self.val.max())
        max_val = ipywidgets.BoundedFloatText(description="upper colorbar bound:",
                value=self.val.max(), min=self.val.min(), max=self.val.max())
        minmax = ipywidgets.FloatRangeSlider(min=self.val.min(), max=self.val.max())


        down.on_click(self.on_ydownclick)
        up.on_click(self.on_yupclick)
        right.on_click(self.on_xrightclick)
        left.on_click(self.on_xleftclick)
        zoom.observe(self.on_zoom, names='value')
        # These can be jslinked, so we will do so.
        ipywidgets.jslink((is_log, 'value'), (self.colormaps, 'is_log'))
        ipywidgets.jslink((min_val, 'value'), (self.colormaps, 'min_val'))
        ipywidgets.link((min_val, 'value'), (self.colormaps, 'min_val'))
        ipywidgets.jslink((max_val, 'value'), (self.colormaps, 'max_val'))
        ipywidgets.link((max_val, 'value'), (self.colormaps, 'max_val'))
        # This one seemingly cannot be.
        ipywidgets.link((colormaps, 'value'), (self.colormaps, 'map_name'))

        nav_buttons = ipywidgets.GridBox(children = [up, left, right, down],
                         layout=ipywidgets.Layout(width='100%',
                                    grid_template_columns = '33% 34% 33%',
                                    grid_template_rows = 'auto auto auto',
                                    grid_template_areas = '''
                                    " . up . "
                                    " left . right "
                                    " . down . "
                                    ''',
                                    grid_area='nav_buttons'))

        all_navigation = ipywidgets.GridBox(children = [nav_buttons, zoom],
                layout=ipywidgets.Layout(width="300px",
                    grid_template_columns="25% 50% 25%",
                    grid_template_rows="auto auto",
                    grid_template_areas='''
                    ". nav_buttons ."
                    "zoom zoom zoom"
                    '''
                    ))

        all_normalizers = ipywidgets.GridBox(children = [is_log,
                colormaps, min_val, max_val],
                layout=ipywidgets.Layout(width="auto")
                )

        accordion = ipywidgets.Accordion(children=[all_navigation,
            all_normalizers])

        accordion.set_title(0, 'navigation')
        accordion.set_title(1, 'colormap controls')

        return accordion

    def on_xrightclick(self, b):
        vc = self.view_center
        self.view_center = ((vc[0]+0.01),vc[1])

    def on_xleftclick(self, b):
        vc = self.view_center
        self.view_center = ((vc[0]-0.01),vc[1])

    def on_yupclick(self, b):
        vc = self.view_center
        self.view_center = (vc[0],(vc[1]+0.01))

    def on_ydownclick(self, b):
        vc = self.view_center
        self.view_center = (vc[0],(vc[1]-0.01))

    def on_zoom(self, change):
        vw = self.view_width
        width_x = 1.0/change["new"]
        ratio = width_x/vw[0]
        width_y = vw[1]*ratio
        self.view_width = (width_x, width_y)
        # print("canvas center is at: {}".format(center))
        # print("zoom value is: {}".format(change["new"]))
        # print("width of frame is: {}".format(width))
        # print("old edges: {} \n new edges:{}".format(ce, new_bounds))


def display_yt(data_object, field):
    # Note what we are doing here: we are taking *views* of these,
    # as the logic in the ndarray traittype doesn't check for subclasses.
    frb = FRBViewer(px = data_object["px"].d,
                    py = data_object["py"].d,
                    pdx = data_object["pdx"].d,
                    pdy = data_object["pdy"].d,
                    val = data_object[field].d)
    controls = frb.setup_controls()
    return ipywidgets.HBox([controls, frb])

def _2d_display(self, fields = None):
    axis = self.axis
    skip = self._key_fields
    skip += list(set(frb._exclude_fields).difference(set(self._key_fields)))
    self.fields = [k for k in self.field_data if k not in skip]
    if fields is not None:
        self.fields = ensure_list(fields) + self.fields
    if len(self.fields) == 0:
        raise ValueError("No fields found to plot in display()")
    return display_yt(self, self.fields[0])


YTSlice.display = _2d_display
YTQuadTreeProj.display = _2d_display

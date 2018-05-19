from typing import List, Tuple
from pathlib import Path

from PyQt5.QtCore import Qt, QSettings, QRectF, QMarginsF
from PyQt5.QtGui import QColor, QPainterPath, QBrush, QPen, QResizeEvent
from PyQt5.QtWidgets import QGraphicsScene, QFileDialog

from plover import system
from plover.config import CONFIG_DIR
from plover.engine import StenoEngine
from plover.steno import Stroke
from plover.gui_qt.i18n import get_gettext
from plover.gui_qt.tool import Tool

from layout_display.layout_display_ui import Ui_LayoutDisplay
from layout_display.steno_layout import StenoLayout


_ = get_gettext()

class LayoutDisplay(Tool, Ui_LayoutDisplay):
    ''' Steno layout display of strokes '''

    TITLE = _('Layout Display')
    ROLE = 'layout_display'
    ICON = ':/layout_display/steno_key.svg'

    def __init__(self, engine: StenoEngine):
        super(LayoutDisplay, self).__init__(engine)
        self.setupUi(self)

        self.graphics_scene = QGraphicsScene()

        self._stroke = []
        self._numbers = set()
        self._numbers_to_keys = {}
        self._number_key = ''
        self._system_name = ''
        self._system_file_map = {}

        self._layout = StenoLayout()
        self._layout_file_path = ''

        self.restore_state()

        self.button_reset.clicked.connect(self.on_reset)
        self.button_load.clicked.connect(self.on_load)
        engine.signal_connect('config_changed', self.on_config_changed)
        self.on_config_changed(engine.config)
        engine.signal_connect('stroked', self.on_stroke)

        self.update_layout_view(self._layout)

    def _save_state(self, settings: QSettings):
        ''' 
        Save state to settings.
        Called via save_state through plover.qui_qt.utils.WindowState
        '''

        settings.setValue('system_file_map', self._system_file_map)

    def _restore_state(self, settings: QSettings):
        '''
        Restore state from settings.
        Called via restore_state through plover.qui_qt.utils.WindowState
        '''

        self._system_file_map = settings.value('system_file_map', {}, dict)

    def on_config_changed(self, config):
        ''' Updates state based off of the new Plover configuration '''

        # TODO: when does this actually happen...?
        if 'system_name' not in config:
            return

        self._stroke = []
        self._numbers = set(system.NUMBERS.values())
        self._numbers_to_keys = {v: k for k, v in system.NUMBERS.items()}
        self._number_key = system.NUMBER_KEY
        self._system_name = config['system_name']

        # Respect layout padding by manipulating the scene's rect during update
        # TODO: this doesn't work, just removes some and adds it back.
        #       need to make it only add once per config change and not remove
        #       if no margins existed before. And, need to move it so that it
        #       happens before show but after the paths get added or scaling
        #       won't work I'm pretty sure
        padding_old = self._layout.padding
        # scene_rect = self.graphics_scene.sceneRect()
        # scene_rect = scene_rect.marginsRemoved(QMarginsF(padding_old, padding_old,
        #                                                  padding_old, padding_old))

        # If the user has no valid preference then fall back to the default
        preferred_layout_file = self.get_preferred_layout(self._system_name)
        if not preferred_layout_file:
            self.on_reset()
        else:
            self._layout_file_path = preferred_layout_file
            self._system_file_map[self._system_name] = self._layout_file_path
            self.save_state()

            self._layout.load_from_file(preferred_layout_file)
            self.label_layout_name.setText(self._layout.name)
            self.update_layout_view(self._layout)

        # padding_new = self._layout.padding
        # scene_rect = scene_rect.marginsAdded(QMarginsF(padding_new, padding_new,
        #                                                padding_new, padding_new))
        # self.graphics_scene.setSceneRect(scene_rect)

    def on_stroke(self, stroke: Stroke):
        ''' Updates state based off of the latest stroke by the user '''

        keys = stroke.steno_keys[:]

        # Handle converting numbers in the stroke to the actual key values
        if any(key in self._numbers for key in keys):
            keys.append(self._number_key)
        keys = [self._numbers_to_keys[x] if x in self._numbers_to_keys else x for x in keys]

        self._stroke = keys
        self.update_layout_view(self._layout, keys)

    def on_reset(self):
        ''' Resets the layout to the built-in default layout '''

        self._layout_file_path = ''
        if self._system_name in self._system_file_map:
            self._system_file_map.pop(self._system_name)
            self.save_state()

        self._layout.load_from_resource(':/layout_display/english_stenotype.json')
        self.label_layout_name.setText(self._layout.name)
        self.update_layout_view(self._layout)

    def on_load(self):
        ''' Gets a layout file from the user to load '''

        # The API says this should return a string, but it returns a tuple
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open Layout File', CONFIG_DIR, '(*.json)')

        # If the user cancelled out of the dialog then we will have a null string
        if not file_path:
            return

        self._layout_file_path = file_path
        self._system_file_map[self._system_name] = self._layout_file_path
        self.save_state()

        self._layout.load_from_file(file_path)
        self.label_layout_name.setText(self._layout.name)
        self.update_layout_view(self._layout)

    def get_preferred_layout(self, system_name: str) -> str:
        ''' Gets the user's preferred layout file for the given system '''

        # Restore state to make sure our system to file mapping is up to date
        self.restore_state()

        file_path = ''
        if system_name in self._system_file_map:
            file_path = self._system_file_map[system_name]

        # At least validate the file exists
        if file_path and not Path(file_path).is_file():
            file_path = ''
            if self._system_name in self._system_file_map:
                self._system_file_map.pop(self._system_name)
                self.save_state()

        return file_path

    def update_layout_view(self, steno_layout: StenoLayout, stroke: List[str] = []):
        ''' Updates the current layout display for the provided stroke '''

        # Clear all items from the scene. Could probably be made more efficient...
        graphics_scene = self.graphics_scene
        graphics_scene.clear()

        scene_pen = QPen(QColor('#000000'), 1, Qt.SolidLine, Qt.SquareCap, Qt.BevelJoin)

        for key_path, path_brush in LayoutDisplay._get_key_paths(steno_layout, stroke):
            if not key_path or not path_brush:
                break

            graphics_scene.addPath(key_path, scene_pen, path_brush)

        # Scene rects don't shrink when items are removed, so need to manually
        # set it to the current size needed by the contained items
        graphics_scene.setSceneRect(graphics_scene.itemsBoundingRect())

        self.layout_display_view.setScene(graphics_scene)
        self.layout_display_view.show()
        # TODO: this actually needs to happen in the showEvent of the view
        self.layout_display_view.fitInView(graphics_scene.sceneRect(), Qt.KeepAspectRatio)

    @staticmethod
    def _get_key_paths(steno_layout: StenoLayout, stroke: List[str]) -> List[Tuple[QPainterPath, QBrush]]:
        ''' Constructs paths for the layout '''

        key_paths = []

        key_width = steno_layout.key_width
        key_height = steno_layout.key_height

        for key in steno_layout.keys:
            x = key.position_x * key_width
            y = key.position_y * key_height
            w = key_width * key.width
            h = key_height * key.height

            path = LayoutDisplay._steno_key_path(x, y, w, h,
                                                 key.is_round_top, key.is_round_bottom)

            # Determine what color the path should be filled with
            is_in_stroke = (key.name in stroke)
            if is_in_stroke and key.color_pressed:
                path_brush = QBrush(QColor(key.color_pressed))
            elif not is_in_stroke and key.color:
                path_brush = QBrush(QColor(key.color))
            else:
                path_brush = QBrush()

            key_paths.append((path, path_brush))

        return key_paths

    @staticmethod
    def _steno_key_path(x, y, w, h, round_top, round_bottom, corner_radius=0) -> QPainterPath:
        ''' Creates the generic path for a key '''

        # These allow us to make the main key and rounded portions separately
        h_ellipse = min((w, h / 2))

        y = y + h_ellipse / 2 if round_top else y
        if round_top and round_bottom:
            h = h - h_ellipse
        elif round_top or round_bottom:
            h = h - h_ellipse / 2

        # Construct the main key shape
        key_path = QPainterPath()
        if corner_radius:
            key_path.addRect(x, y, w, h)
            # TODO: Actually figure out this case
            # box_height = h - height_offset + (corner_radius if round_bottom else 0)
            # box.addRoundedRect(x, y, w, box_height, corner_radius, corner_radius)
        else:
            key_path.addRect(x, y, w, h)

        # Add on the rounded top and bottom parts
        if round_top:
            key_top = QPainterPath()

            key_top.addEllipse(x, y - h_ellipse / 2, w, h_ellipse)
            key_path = key_path.united(key_top)
        if round_bottom:
            key_bottom = QPainterPath()

            key_bottom.addEllipse(x, y + h - h_ellipse / 2, w, h_ellipse)
            key_path = key_path.united(key_bottom)

        return key_path

    def resizeEvent(self, event: QResizeEvent):
        ''' Qt resize event '''

        # Make sure that the layout display scene scales to the view
        if self.graphics_scene:
            self.layout_display_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)

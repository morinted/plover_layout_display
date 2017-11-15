import time
from collections import namedtuple
from math import ceil

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QFont, QColor, QPainterPath, QBrush

from plover import system
from plover.gui_qt.i18n import get_gettext
from plover.gui_qt.tool import Tool

from layout_display.layout_display_ui import Ui_LayoutDisplay

_ = get_gettext()


class LayoutDisplay(Tool, Ui_LayoutDisplay):

    ''' Paper tape display of strokes. '''

    TITLE = _('Layout Display')
    ROLE = 'layout_display'
    ICON = ':/layout_display/steno_key.svg'

    def __init__(self, engine):
        super(LayoutDisplay, self).__init__(engine)
        self.setupUi(self)
        self._stroke = []
        engine.signal_connect('config_changed', self.on_config_changed)
        self.on_config_changed(engine.config)
        engine.signal_connect('stroked', self.on_stroke)

    @staticmethod
    def _set_label_color(label, color, opacity=255):
        label.setStyleSheet(
            'color: rgba(%s, %s, %s, %s)' % (
                color.red(), color.green(), color.blue(), opacity
            )
        )

    def on_config_changed(self, config):
        if 'system_name' in config:
            self._stroke = []
            self._numbers = set(system.NUMBERS.values())
            self._numbers_to_keys = {v: k for k, v in system.NUMBERS.items()}

    def paintEvent(self, event):
        padding = 4
        key_width = 30
        key_height = 35
        StenoKey = namedtuple('StenoKey', 'x y w h rounded key_name')
        keys = (
            [ StenoKey(0, 0, 10, 0.5, False, '#'),
              StenoKey(0, 0.5, 1, 2, True, 'S-'),
              StenoKey(4, 0.5, 1, 2, True, '*'),
            ] + [StenoKey(x + 1, 0.5, 1, 1, False, letter)
                 for x, letter in enumerate('T-,P-,H-,,-F,-P,-L,-T,-D'.split(',')) if letter]
              + [StenoKey(x + 1, 1.5, 1, 1, True, letter)
                 for x, letter in enumerate('K-,W-,R-,,-R,-B,-G,-S,-Z'.split(',')) if letter]
              + [StenoKey(x + 2.2, 2.5, 1, 1, True, letter) for x, letter in enumerate(['A-', 'O-'])]
              + [StenoKey(x + 4.8, 2.5, 1, 1, True, letter) for x, letter in enumerate(['-E', '-U'])]
        )
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)
        painting_width = 10 * (key_width + padding) + padding
        painting_height = 3.5 * (key_height + padding) + padding * 1.5
        qp.setWindow(0, 0, painting_width, painting_height)
        min_scale = min(self.width() / painting_width, self.height() / painting_height)
        qp.translate(
            (abs(self.width() / min_scale - painting_width)) / 2,
            (abs(self.height() / min_scale - painting_height)) / 2
        )
        qp.setViewport(0, 0, painting_width * min_scale, painting_height * min_scale)
        filled_key_brush = QBrush(QColor.fromRgb(0, 0, 0))

        key_paths = {}

        for x, y, w, h, rounded, key_name in keys:
            w = key_width * w + ceil(w - 1) * padding
            h = key_height * h + ceil(h - 1) * padding
            path = key_paths.get((w, h, rounded))
            if path is None:
                path = self._steno_key_path(1, 1, w, h, rounded)
                key_paths[(w, h, rounded)] = path
            x = (x + 1) * padding + x * key_width
            y = ceil(y + 1) * padding + y * key_height
            qp.save()
            qp.translate(x, y)
            (qp.fillPath(path, filled_key_brush)
             if key_name in self._stroke
             else qp.drawPath(path)
            )
            qp.restore()
        qp.end()

    def _steno_key_path(self, x, y, w, h, rounded=False, corner_radius=0):
        ellipse_y = min((w, h / 2)) if rounded else 0
        height_offset = ellipse_y / 2 if rounded else 0
        box = QPainterPath()
        if corner_radius:
            box_height = h - height_offset + (corner_radius if rounded else 0)
            box.addRoundedRect(x, y, w, box_height, corner_radius, corner_radius)
        else:
            box.addRect(x, y, w, h - height_offset)
        if rounded:
            round_bottom = QPainterPath()

            round_bottom.addEllipse(x, y + h - height_offset - ellipse_y / 2, w, ellipse_y)
            box = box.united(round_bottom)
        return box

    def drawText(self, event, qp):
        qp.setPen(QColor(168, 34, 3))
        qp.setFont(QFont('Decorative', 10))
        qp.drawRect(10, 10, 100, 100)
        qp.drawText(event.rect(), Qt.AlignCenter, 'booop')

    def on_stroke(self, stroke):
        keys = stroke.steno_keys[:]
        if any(key in self._numbers for key in keys):
            keys.append('#')
        keys = [self._numbers_to_keys[x] if x in self._numbers_to_keys else x for x in keys]
        self._stroke = keys
        self.update()

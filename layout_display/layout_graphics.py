from typing import List

from PyQt5.QtCore import Qt, QMarginsF
from PyQt5.QtWidgets import (QWidget, QGraphicsView, QGraphicsScene,
                             QGraphicsTextItem)
from PyQt5.QtGui import (QPainterPath, QPen, QBrush, QColor,
                         QFont, QResizeEvent, QShowEvent)

from layout_display.steno_layout import StenoLayout, StenoKey


class LayoutDisplayView(QGraphicsView):
    ''' View to manage Layout Display scenes '''

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.graphics_scene = LayoutDisplayScene(self)
        self._scene_pen = QPen(QColor('#000000'), 1, Qt.SolidLine,
                               Qt.SquareCap, Qt.BevelJoin)

    def resizeEvent(self, event: QResizeEvent):
        ''' Qt resize event '''

        # Make sure the layout display scene scales to the view
        self.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)

    def showEvent(self, event: QShowEvent):
        ''' Qt show event '''

        # Make sure the layout display scene is scaled on initial "show"
        self.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)

    def initialize_view(self, steno_layout: StenoLayout):
        ''' Initializes the view for the provided layout '''

        # TODO: For now, just call update without a stroke, but these two
        #       should be optimized to not re-create the scene each time
        self.update_view(steno_layout, [])

    def update_view(self, steno_layout: StenoLayout, stroke: List[str]):
        ''' Updates the layout display for the provided layout and stroke '''

        scene = self.graphics_scene
        pen = self._scene_pen
        font = QFont(steno_layout.font) if steno_layout.font else QFont()
        # Clear all items from the scene. Could be more efficient...
        scene.clear()
        scene.setBackgroundBrush(QBrush(QColor(steno_layout.background_color)))

        for key in steno_layout.keys:
            path = LayoutDisplayView._create_key_path(steno_layout, key)
            brush = LayoutDisplayView._get_key_path_brush(key, (key.name in stroke))
            pen.setColor(QColor(key.stroke_color))

            # Add the key path before its label, then center the label
            scene.addPath(path, pen, brush)

            if key.label:
                label = QGraphicsTextItem(key.label)
                label.setFont(font)
                label.setDefaultTextColor(QColor(key.font_color))

                label_rect = label.boundingRect()
                label_rect.moveCenter(path.boundingRect().center())
                label.setPos(label_rect.x(), label_rect.y())
                scene.addItem(label)

        # Scene rects don't shrink when items are removed, so need to manually
        # set it to the current size needed by the contained items + margin
        margin = steno_layout.margin
        scene_rect = scene.itemsBoundingRect()
        scene_rect = scene_rect.marginsAdded(QMarginsF(margin, margin,
                                                       margin, margin))
        scene.setSceneRect(scene_rect)
        self.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)

        self.setScene(scene)
        self.show()

    @staticmethod
    def _get_key_path_brush(key: StenoKey, is_pressed: bool) -> QBrush:
        ''' Gets what brush the key should use '''

        if is_pressed and key.color_pressed:
            path_brush = QBrush(QColor(key.color_pressed))
        elif not is_pressed and key.color:
            path_brush = QBrush(QColor(key.color))
        else:
            path_brush = QBrush()

        return path_brush

    @staticmethod
    def _create_key_path(steno_layout: StenoLayout, key: StenoKey) -> QPainterPath:
        ''' Creates the path for a key '''

        key_width = steno_layout.key_width
        key_height = steno_layout.key_height

        pos_x = key.x * key_width
        pos_y = key.y * key_height
        width = key_width * key.width
        height = key_height * key.height
        is_round_top = key.is_round_top
        is_round_bottom = key.is_round_bottom

        # Figure out adjustments needed to add rounded parts
        ellipse_height = min((width, height / 2))

        pos_y = pos_y + ellipse_height / 2 if is_round_top else pos_y
        if is_round_top and is_round_bottom:
            height = height - ellipse_height
        elif is_round_top or is_round_bottom:
            height = height - ellipse_height / 2

        # Construct the main key shape
        key_path = QPainterPath()
        key_path.addRect(pos_x, pos_y, width, height)

        # Add on the rounded parts
        if is_round_top:
            key_top = QPainterPath()

            key_top.addEllipse(pos_x, pos_y - ellipse_height / 2,
                               width, ellipse_height)
            key_path = key_path.united(key_top)
        if is_round_bottom:
            key_bottom = QPainterPath()

            key_bottom.addEllipse(pos_x, pos_y + height - ellipse_height / 2,
                                  width, ellipse_height)
            key_path = key_path.united(key_bottom)

        return key_path

class LayoutDisplayScene(QGraphicsScene):
    ''' Scene containing all layout display objects '''

    def __init__(self, parent: QWidget):
        super().__init__(parent)

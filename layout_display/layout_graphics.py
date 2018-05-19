from typing import List, Tuple

from PyQt5.QtCore import Qt, QMarginsF
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import (QPainterPath, QPen, QBrush, QColor,
                         QResizeEvent, QShowEvent)

from layout_display.steno_layout import StenoLayout


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

    def update_view(self, steno_layout: StenoLayout, stroke: List[str] = []):
        ''' Updates the layout display for the provided layout and stroke '''

        scene = self.graphics_scene
        pen = self._scene_pen
        # Clear all items from the scene. Could be more efficient...
        scene.clear()

        for path, brush in LayoutDisplayView._get_key_paths(steno_layout, stroke):
            if not path or not brush:
                break

            scene.addPath(path, pen, brush)

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
    def _get_key_paths(steno_layout: StenoLayout,
                       stroke: List[str]) -> List[Tuple[QPainterPath, QBrush]]:
        ''' Constructs paths for the layout '''

        key_paths = []
        key_width = steno_layout.key_width
        key_height = steno_layout.key_height

        for key in steno_layout.keys:
            pos_x = key.position_x * key_width
            pos_y = key.position_y * key_height
            width = key_width * key.width
            height = key_height * key.height
            is_round_top = key.is_round_top
            is_round_bottom = key.is_round_bottom

            path = LayoutDisplayView._create_key_path(pos_x, pos_y,
                                                      width, height,
                                                      is_round_top,
                                                      is_round_bottom)

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
    def _create_key_path(pos_x: float, pos_y: float,
                         width: float, height: float,
                         is_round_top: bool, is_round_bottom: bool) -> QPainterPath:
        ''' Creates the path for a key '''

        # Figure out adjustments needed to add rounded parts
        h_ellipse = min((width, height / 2))

        pos_y = pos_y + h_ellipse / 2 if is_round_top else pos_y
        if is_round_top and is_round_bottom:
            height = height - h_ellipse
        elif is_round_top or is_round_bottom:
            height = height - h_ellipse / 2

        # Construct the main key shape
        key_path = QPainterPath()
        key_path.addRect(pos_x, pos_y, width, height)

        # Add on the rounded parts
        if is_round_top:
            key_top = QPainterPath()

            key_top.addEllipse(pos_x, pos_y - h_ellipse / 2, width, h_ellipse)
            key_path = key_path.united(key_top)
        if is_round_bottom:
            key_bottom = QPainterPath()

            key_bottom.addEllipse(pos_x, pos_y + height - h_ellipse / 2, width, h_ellipse)
            key_path = key_path.united(key_bottom)

        return key_path

class LayoutDisplayScene(QGraphicsScene):
    ''' Scene containing all layout display objects '''

    def __init__(self, parent: QWidget):
        super().__init__(parent)

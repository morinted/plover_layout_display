from collections import namedtuple
import json
from typing import List

from PyQt5 import QtCore


DEF_LAYOUT_NAME = 'Default Layout Name'
DEF_FONT = ''
DEF_FONT_COLOR = '#000000'
DEF_BACKGROUND_COLOR = '#FFFFFF'
DEF_MARGIN = 5.0
DEF_KEY_WIDTH = 30.0
DEF_KEY_HEIGHT = 35.0

DEF_KEY_LABEL = ''
DEF_KEY_WIDTH_UNIT = 1.0
DEF_KEY_HEIGHT_UNIT = 1.0
DEF_KEY_POS_X = 0.0
DEF_KEY_POS_Y = 0.0
DEF_KEY_COLOR = ''
DEF_KEY_COLOR_PRESSED = '#000000'

StenoKey = namedtuple('StenoKey',
                      'name label ' +
                      'position_x position_y ' +
                      'width height ' +
                      'is_round_top is_round_bottom ' +
                      'color color_pressed font_color')

class StenoLayout():
    ''' Represents the structure of a stenography layout '''

    def __init__(self):
        self.name = DEF_LAYOUT_NAME
        self.font = DEF_FONT
        self.background_color = DEF_BACKGROUND_COLOR
        self.margin = DEF_MARGIN
        self.key_width = DEF_KEY_WIDTH
        self.key_height = DEF_KEY_HEIGHT

        self.keys: List[StenoKey] = []

    def load_from_file(self, file_path: str):
        ''' Populates layout information from the provided file path '''

        try:
            with open(file_path, encoding='utf-8') as file:
                data = json.load(file)

            self.load_from_json(data)
        except:
            pass

    def load_from_resource(self, resource_path: str):
        ''' Populates layout information from the provided Qt resource path '''

        try:
            file = QtCore.QFile(resource_path)

            if file.open(QtCore.QIODevice.ReadOnly | QtCore.QFile.Text):
                text_stream = QtCore.QTextStream(file)
                text_stream.setCodec('utf-8')
                text_stream.setAutoDetectUnicode(True)

                file_text = text_stream.readAll()
                file.close()

            data = json.loads(str(file_text))

            self.load_from_json(data)
        except:
            pass

    def load_from_json(self, data: dict):
        ''' Populates layout information from the provided JSON data '''

        self.name = data['name'] if 'name' in data else DEF_LAYOUT_NAME
        self.font = data['font'] if 'font' in data else DEF_FONT
        font_color = data['font_color'] if 'font_color' in data else DEF_FONT_COLOR
        self.background_color = data['background_color'] if 'background_color' in data else DEF_BACKGROUND_COLOR
        self.margin = data['margin'] if 'margin' in data else DEF_MARGIN
        self.key_width = data['key_width'] if 'key_width' in data else DEF_KEY_WIDTH
        self.key_height = data['key_height'] if 'key_height' in data else DEF_KEY_HEIGHT

        self.keys = []
        for key in data['keys']:
            self.keys.append(StenoKey(
                # Make sure that name always exists; we'll default to unique
                key['name'] if 'name' in key else str(len(self.keys)),
                key['label'] if 'label' in key else DEF_KEY_LABEL,
                key['position_x'] if 'position_x' in key else DEF_KEY_POS_X,
                key['position_y'] if 'position_y' in key else DEF_KEY_POS_Y,
                key['width'] if 'width' in key else DEF_KEY_WIDTH_UNIT,
                key['height'] if 'height' in key else DEF_KEY_HEIGHT_UNIT,
                key['is_round_top'] if 'is_round_top' in key else False,
                key['is_round_bottom'] if 'is_round_bottom' in key else False,
                key['color'] if 'color' in key else DEF_KEY_COLOR,
                key['color_pressed'] if 'color_pressed' in key else DEF_KEY_COLOR_PRESSED,
                key['font_color'] if 'font_color' in key else font_color
            ))

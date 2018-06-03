from collections import namedtuple
import json
from typing import List

from PyQt5 import QtCore
import jsonschema


DEF_LAYOUT_NAME = 'Default Layout Name'
DEF_MARGIN = 5.0
DEF_KEY_WIDTH = 30.0
DEF_KEY_HEIGHT = 35.0
DEF_FONT = ''
DEF_FONT_COLOR = '#000000'
DEF_BACKGROUND_COLOR = '#FFFFFF'
DEF_STROKE_COLOR = '#000000'
DEF_KEY_COLOR = ''
DEF_KEY_COLOR_PRESSED = '#000000'

DEF_KEY_LABEL = ''
DEF_KEY_WIDTH_UNIT = 1.0
DEF_KEY_HEIGHT_UNIT = 1.0
DEF_KEY_POS_X = 0.0
DEF_KEY_POS_Y = 0.0

StenoKey = namedtuple('StenoKey',
                      'name label ' +
                      'x y ' +
                      'width height ' +
                      'is_round_top is_round_bottom ' +
                      'font_color stroke_color color color_pressed')

class StenoLayout():
    ''' Represents the structure of a stenography layout '''

    def __init__(self):
        self.name = DEF_LAYOUT_NAME
        self.margin = DEF_MARGIN
        self.key_width = DEF_KEY_WIDTH
        self.key_height = DEF_KEY_HEIGHT
        self.font = DEF_FONT
        self.background_color = DEF_BACKGROUND_COLOR

        self.keys: List[StenoKey] = []

        self._validation_schema = StenoLayout._load_validation_schema()

    def load_from_file(self, file_path: str) -> bool:
        ''' Populates layout information from the provided file path '''

        try:
            with open(file_path, encoding='utf-8') as file:
                data = json.load(file)
        except:
            return False

        return self.load_from_json(data)

    def load_from_resource(self, resource_path: str) -> bool:
        ''' Populates layout information from the provided Qt resource path '''

        try:
            file_text = StenoLayout._load_qt_resource_text(resource_path)
            data = json.loads(file_text)
        except:
            return False

        return self.load_from_json(data)

    def load_from_json(self, data: dict) -> bool:
        ''' Populates layout information from the provided JSON data '''

        # Validate the JSON file first before trying to load it
        try:
            jsonschema.validate(data, self._validation_schema)
        except (jsonschema.ValidationError, jsonschema.SchemaError) as error:
            return False

        self.name = data.get('name', DEF_LAYOUT_NAME)
        self.margin = data.get('margin', DEF_MARGIN)
        self.key_width = data.get('key_width', DEF_KEY_WIDTH)
        self.key_height = data.get('key_height', DEF_KEY_HEIGHT)
        self.font = data.get('font', DEF_FONT)
        font_color = data.get('font_color', DEF_FONT_COLOR)
        self.background_color = data.get('background_color', DEF_BACKGROUND_COLOR)
        key_stroke_color = data.get('key_stroke_color', DEF_STROKE_COLOR)
        key_color = data.get('key_color', DEF_KEY_COLOR)
        key_color_pressed = data.get('key_color', DEF_KEY_COLOR_PRESSED)

        self.keys = []
        for key in data['keys']:
            self.keys.append(StenoKey(
                # Make sure that name always exists; we'll default to unique
                key.get('name', str(len(self.keys))),
                key.get('label', DEF_KEY_LABEL),
                key.get('x', DEF_KEY_POS_X),
                key.get('y', DEF_KEY_POS_Y),
                key.get('width', DEF_KEY_WIDTH_UNIT),
                key.get('height', DEF_KEY_HEIGHT_UNIT),
                key.get('is_round_top', False),
                key.get('is_round_bottom', False),
                key.get('font_color', font_color),
                key.get('stroke_color', key_stroke_color),
                key.get('color', key_color),
                key.get('color_pressed', key_color_pressed)
            ))

        return True

    @staticmethod
    def _load_validation_schema() -> dict:
        ''' Loads a JSON Schema validation schema '''

        data = {}

        try:
            file_text = StenoLayout._load_qt_resource_text(':/layout_display/steno_layout.schema.json')
            data = json.loads(file_text)
        except:
            return {}

        return data

    @staticmethod
    def _load_qt_resource_text(resource_path: str) -> str:
        ''' Wrapper for loading a Qt resource file's text contents '''

        file_text = ''

        try:
            file = QtCore.QFile(resource_path)

            if file.open(QtCore.QIODevice.ReadOnly | QtCore.QFile.Text):
                text_stream = QtCore.QTextStream(file)
                text_stream.setCodec('utf-8')
                text_stream.setAutoDetectUnicode(True)

                file_text = str(text_stream.readAll())
                file.close()
        except:
            return ''

        return file_text

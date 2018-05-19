from collections import namedtuple
import json
from typing import List

from PyQt5 import QtCore


StenoKey = namedtuple('StenoKey',
                      'name label ' +
                      'position_x position_y ' +
                      'width height ' +
                      'is_round_top is_round_bottom ' +
                      'color color_pressed')

class StenoLayout():
    ''' Represents the structure of a stenography layout '''

    name: str = 'Default Layout Name'
    padding: float = 4.0
    key_width: int = 30
    key_height: int = 35
    keys: List[StenoKey] = []

    def __init__(self):
        pass

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

    def load_from_json(self, data):
        ''' Populates layout information from the provided JSON data '''

        if 'name' in data:
            self.name = data['name']
        if 'padding' in data:
            self.padding = data['padding']
        if 'key_width' in data:
            self.key_width = data['key_width']
        if 'key_height' in data:
            self.key_height = data['key_height']

        self.keys = []
        for key in data['keys']:
            self.keys.append(StenoKey(
                key['name'] if 'name' in key else str(len(self.keys)),
                key['label'] if 'label' in key else '',
                key['position_x'] if 'position_x' in key else 0.0,
                key['position_y'] if 'position_y' in key else 0.0,
                key['width'] if 'width' in key else 1.0,
                key['height'] if 'height' in key else 1.0,
                key['is_round_top'] if 'is_round_top' in key else False,
                key['is_round_bottom'] if 'is_round_bottom' in key else False,
                key['color'] if 'color' in key else '',
                key['color_pressed'] if 'color_pressed' in key else '#000000'
            ))

    def get_width(self) -> int:
        ''' Calculates the width the layout requires '''

        return max(self.padding + key.position_x + key.width * self.key_width for key in self.keys)

    def get_height(self) -> int:
        ''' Calculates the height the layout requires '''

        return max(self.padding + key.position_y + key.height * self.key_height for key in self.keys)

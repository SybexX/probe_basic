import os

import linuxcnc

# Workarround for nvidia propietary drivers

import ctypes
import ctypes.util

ctypes.CDLL(ctypes.util.find_library("GL"), mode=ctypes.RTLD_GLOBAL)

# end of Workarround

from qtpy.QtCore import Property, Slot
from qtpy.QtGui import QColor

from qtpy.QtCore import Signal, Slot, QUrl, QTimer
from qtpy.QtQuickWidgets import QQuickWidget

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)
STATUS = getPlugin('status')
TOOLTABLE = getPlugin('tooltable')
IN_DESIGNER = os.getenv('DESIGNER', False)
WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))
INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))

class DynATC(QQuickWidget):
    atcInitSig = Signal(int, int, arguments=['pockets', 'step_duration'])
    
    resizeSig = Signal(int, int, arguments=["width", "height"])
    
    rotateSig = Signal(int, int, arguments=['steps', 'direction'])

    showToolSig = Signal(float, float, arguments=['pocket', 'tool_num'])
    hideToolSig = Signal(float, arguments=['pocket'])

    bgColorSig = Signal(QColor, arguments=["color"])
    homeMsgSig = Signal(str, arguments=["message"])

    def __init__(self, parent=None):
        super(DynATC, self).__init__(parent)

        # properties
        self._background_color = QColor(0, 0, 0)
        
        self.atc_position = 0
        self.pocket = 1
        self.home = 0
        self.homing = 0
        self.pocket_slots = int(INIFILE.find("ATC", "POCKETS") or 12)
        self.rotaion_duration = int(INIFILE.find("ATC", "STEP_TIME") or 1000)
        
        self.engine().rootContext().setContextProperty("atc_spiner", self)
        qml_path = os.path.join(WIDGET_PATH, "atc.qml")
        url = QUrl.fromLocalFile(qml_path)

        self.setSource(url)  # Fixme fails on qtdesigner

        self.tool_table = None
        self.status_tool_table = None
        self.pockets = dict()
        self.tools = None

        self.atcInitSig.emit(self.pocket_slots, self.rotaion_duration)
        
        if not IN_DESIGNER:
            for pocket in range(1, self.pocket_slots+1):
                self.hideToolSig.emit(pocket)
     
    def resizeEvent(self, event):
        self.resizeSig.emit(self.maximumWidth(), self.maximumHeight())
        super().resizeEvent(event)

    @Property(QColor)
    def backgroundColor(self):
        return self._background_color

    @backgroundColor.setter
    def backgroundColor(self, color):
        self.bgColorSig.emit(color)
        self._background_color = color

    def load_tools(self):
        # print("load_tools")
        for i in range(1, self.pocket_slots+1):
            self.hideToolSig.emit(i)

        for pocket, tool in list(self.pockets.items()):
            if tool != 0:
                self.showToolSig.emit(pocket, tool)
            else:
                self.hideToolSig.emit(pocket)

    def store_tool(self, pocket, tool_num):
        self.pockets[pocket] = tool_num
        #
        # print(type(pocket), pocket)
        # print(type(tool_num), tool_num)
        if tool_num != 0:
            # print("show tool {} at pocket {}".format(tool_num, pocket))
            self.showToolSig.emit(pocket, tool_num)
        else:
            # print("Hide tool at pocket {}".format(pocket))
            self.hideToolSig.emit(pocket)

    def atc_message(self, msg=""):
        self.homeMsgSig.emit(msg)

    def rotate(self, steps, direction):
        if direction == "cw":
            self.rotateSig.emit(int(steps), 1)
        elif direction == "ccw":
            self.rotateSig.emit(int(steps), -1)

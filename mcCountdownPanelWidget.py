import time
import datetime
import threading
import random
from functools import partial

import nuke
import nukescripts
from PySide2 import QtCore, QtWidgets, QtGui


class EditFieldBase(QtWidgets.QWidget):
    list = set()
    (LINEEDIT, TEXTEDIT) = range(2)

    def __init__(self, parent, efbDictList):
        QtWidgets.QWidget.__init__(self, parent)
        self.type = None

        self.parent = parent
        self.efbDictList = efbDictList

        self.frameLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.frameLayout)

        for efb in self.efbDictList:
            self.label_name = str(efb['label_name'])
            self.object_name = str(efb['object_name'])
            self.default_value = efb['default_value']
            self.validator = efb['validator']
            self.tooltip = efb['tooltip']
            self.type = efb['type']

            # Simple label
            self.label_field = QtWidgets.QLabel(self.label_name)
            self.layout().addWidget(self.label_field)

            # Simple line edit field
            if self.type == self.LINEEDIT:
                self.text_field = QtWidgets.QLineEdit()
            elif self.type == self.TEXTEDIT:
                self.text_field = QtWidgets.QTextEdit()
            self.text_field.setObjectName(self.object_name)
            self.text_field.setAlignment(QtCore.Qt.AlignTop)
            if self.default_value is not None:
                if self.type == self.LINEEDIT:
                    self.text_field.setText(str(self.default_value))
                elif self.type == self.TEXTEDIT:
                    self.text_field.setPlainText(str(self.default_value))
            if self.tooltip is not None:
                self.text_field.setToolTip(str(self.tooltip))
            self.layout().addWidget(self.text_field)
            self.addToList(self.text_field)

            if self.validator is not None and isinstance(self.validator, QtGui.QValidator):
                self.text_field.setValidator(self.validator)

    @classmethod
    def addToList(cls, textField):
        cls.list.add(textField)

    @classmethod
    def GetAllTextData(cls):
        txtList = set()
        for textObj in cls.list:
            if isinstance(textObj, QtWidgets.QLineEdit):
                txtList.add((textObj.objectName(), textObj.text()))
            elif isinstance(textObj, QtWidgets.QTextEdit):
                txtList.add((textObj.objectName(), textObj.toPlainText()))
        return txtList


class AddItemDialogBase(QtWidgets.QDialog):
    (HOURS, MINS, SECONDS, NOTES, BLINK_NUM, REMIND_IN, REMIND_AT) = range(7)

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        self.INT_VAL = QtGui.QIntValidator(1, 99, self)
        self.HOURS_VAL = QtGui.QIntValidator(0, 24, self)
        self.MINS_VAL = QtGui.QIntValidator(0, 60, self)

        self.editFieldBaseList = set()
        self.parent = parent
        self.type = None
        self.what = {}

        self.frameLayout = QtWidgets.QVBoxLayout()
        self.frameLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.setLayout(self.frameLayout)

        self.buttonWidget = QtWidgets.QWidget()
        self.buttonLayout = QtWidgets.QHBoxLayout()

        self.addButton = QtWidgets.QPushButton('Add')
        self.addButton.clicked.connect(self.addAction)
        self.buttonLayout.addWidget(self.addButton)

        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.cancelAction)
        self.buttonLayout.addWidget(self.cancelButton)

        self.buttonWidget.setLayout(self.buttonLayout)
        self.layout().addWidget(self.buttonWidget)

    def addWidget(self, widget_to_add, base_widget_name, index=None, add_to_list=True):
        self.base_widget = self.findChild(QtWidgets.QGroupBox, base_widget_name)
        if self.base_widget:
            if index is not None:
                self.base_widget.layout().insertWidget(index, widget_to_add)
            else:
                self.base_widget.layout().addWidget(widget_to_add)
        else:
            self.base_layout = QtWidgets.QVBoxLayout()
            self.base_widget = QtWidgets.QGroupBox()

            self.base_widget.setObjectName(base_widget_name)
            self.base_widget.setTitle(base_widget_name)

            self.base_layout.addWidget(widget_to_add)
            self.base_widget.setLayout(self.base_layout)
            self.frameLayout.insertWidget(0, self.base_widget)

        if add_to_list:
            self.editFieldBaseList.add(widget_to_add)
        return widget_to_add, self.base_widget

    def addBaseWidgets(self):
        self.intValidator = QtGui.QIntValidator(1, 99, self)

        self.blinkEFB = [self.CreateNewEFBDict('How Many Times To Blink', self.BLINK_NUM, EditFieldBase.LINEEDIT, self.INT_VAL, 5, 'How many times it should blink. Default to 5')]
        self.remindCounter = EditFieldBase(self, self.blinkEFB)
        self.addWidget(self.remindCounter, 'Options')

        self.notesEFB = [self.CreateNewEFBDict('Notes', self.NOTES, EditFieldBase.TEXTEDIT, tooltip='The notes associated with this reminder.')]
        self.notesField = EditFieldBase(self, self.notesEFB)
        self.addWidget(self.notesField, 'Options')

        return (self.remindCounter, self.notesField)

    def CreateNewEFBDict(self, label_name=None, object_name=None, text_type=None, validator=None, default_value=None, tooltip=None):
        if None in [label_name, object_name, text_type]:
            return
        return {
            'label_name': label_name,
            'object_name': object_name,
            'type': text_type,
            'default_value': default_value,
            'validator': validator,
            'tooltip': tooltip
        }

    def GetAllEditFieldBase(self):
        return self.editFieldBaseList

    def GetTextDict(self):
        for efb in self.GetAllEditFieldBase():
            for lineEditName, lineEditText in efb.GetAllTextData():
                # print lineEditName, lineEditText
                if lineEditText:
                    self.what.update({int(lineEditName): lineEditText})
        return self.what

    def GetTimeCardData(self, what):
        self.now = datetime.datetime.now()
        self.hours = int(what.get(self.HOURS, 0))
        self.minutes = int(what.get(self.MINS, 0))
        self.seconds = int(what.get(self.SECONDS, 0))
        self.notes = what.get(self.NOTES, None)
        self.blink_num = int(what.get(self.BLINK_NUM, 5))

        return self.now, self.hours, self.minutes, self.seconds, self.notes, self.blink_num

    def addAction(self):
        NotImplementedError()

    def addTimeCard(self, parent, now, remind_time, notes, card_type, blink_num, hours, minutes, seconds):
        self.timecard = TimecardWidget(parent, now=now, remind_time=remind_time, notes=notes, submit_type=card_type, reminder_blinks=blink_num, hours=hours, minutes=minutes, seconds=seconds)
        parent.TimecardSpaceLayout.insertWidget(0, self.timecard)
        self.timecard.startCountdownThread()
        self.close()

    def cancelAction(self):
        return self.reject()


class RemindInDialog(AddItemDialogBase):
    def __init__(self, parent=None):
        AddItemDialogBase.__init__(self, parent)

        self.type = self.REMIND_IN

        self.countdownEFB = []
        self.countdownEFB.append(
            self.CreateNewEFBDict('Hours', self.HOURS, EditFieldBase.LINEEDIT, self.INT_VAL))
        self.countdownEFB.append(
            self.CreateNewEFBDict('Minutes', self.MINS, EditFieldBase.LINEEDIT, self.INT_VAL))
        self.countdownEFB.append(
            self.CreateNewEFBDict('Seconds', self.SECONDS, EditFieldBase.LINEEDIT, self.INT_VAL))
        self.remindInWidget = EditFieldBase(self, self.countdownEFB)

        # Add base option widgets
        self.baseWidgetList = self.addBaseWidgets()

        # Add additional widget
        self.addWidget(self.remindInWidget, 'Remind Me In')

    def addAction(self):
        self.what = self.GetTextDict()
        self.now, self.hours, self.minutes, self.seconds, self.notes, self.blink_num = self.GetTimeCardData(self.what)
        self.hasError = False

        try:
            self.remind_time = self.now + datetime.timedelta(hours=self.hours, minutes=self.minutes, seconds=self.seconds)
            if self.remind_time <= self.now:
                if nuke.GUI:
                    nuke.message('Reminder time must be later than current time')
                self.hasError = True
        except Exception as e:
            print str(e)
            self.hasError = True

        if not self.hasError:
            self.addTimeCard(self.parent, self.now, self.remind_time, self.notes, self.type, self.blink_num, self.hours, self.minutes, self.seconds)


class RemindAtDialog(AddItemDialogBase):
    def __init__(self, parent=None):
        AddItemDialogBase.__init__(self, parent)

        self.type = self.REMIND_AT

        self.timeWidget = QtCore.QTime().currentTime()
        self.currentTime = QtCore.QTime(self.timeWidget.hour(), self.timeWidget.minute() + 1)
        self.remindAtWidget = QtWidgets.QTimeEdit()
        self.remindAtWidget.setMinimumTime(self.currentTime)
        self.remindAtWidget.setMinimumHeight(22)

        # Add base option widgets
        self.baseWidgetList = self.addBaseWidgets()

        # Add additional widget
        self.addWidget(self.remindAtWidget, 'Remind Me At', add_to_list=False)

    def addAction(self):
        self.what = self.GetTextDict()
        self.what.update(
            {
                self.HOURS: self.remindAtWidget.time().hour(),
                self.MINS: self.remindAtWidget.time().minute(),
            }
        )
        self.now, self.hours, self.minutes, self.seconds, self.notes, self.blink_num = self.GetTimeCardData(self.what)
        self.hasError = False

        try:
            self.remind_time = datetime.datetime(year=self.now.year, month=self.now.month, day=self.now.day, hour=self.hours, minute=self.minutes)
            if self.remind_time <= self.now:
                if nuke.GUI:
                    nuke.message('Reminder time must be later than current time')
                self.hasError = True
        except Exception as e:
            print str(e)
            self.hasError = True

        if not self.hasError:
            self.addTimeCard(self.parent, self.now, self.remind_time, self.notes, self.type, self.blink_num, self.hours, self.minutes, self.seconds)


class TimecardWidget(QtWidgets.QGroupBox):
    dagFlashing = False
    runThread = True

    def __init__(self, parent=None, **kwargs):
        QtWidgets.QGroupBox.__init__(self, parent)

        self.frameLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.frameLayout)
        self.setObjectName('time_base')
        self.styleSheet = self.getStylesheet()
        self.setStyleSheet(self.styleSheet)
        self. parent = parent
        self.now = kwargs.get('now')
        self.remind_time = kwargs.get('remind_time', None)
        self.notes = kwargs.get('notes', None)
        self.submit_type = kwargs.get('submit_type', None)
        self.reminder_blinks = kwargs.get('reminder_blinks', None)
        self.hours = kwargs.get('hours', None)
        self.minutes = kwargs.get('minutes', None)
        self.seconds = kwargs.get('seconds', None)

        self.now_text = str('Submitted on: %s' % self.now.strftime("%b %d %Y %H:%M:%S"))
        self.remind_time_text = str(self.remind_time.strftime("%b %d %Y %H:%M:%S"))
        self.countdown = int((self.remind_time - self.now).total_seconds())
        self.countdown_text = str(self.countdown)

        if self.submit_type == AddItemDialogBase.REMIND_IN:
            self.now_text += ' to be reminded in'
            if self.hours:
                self.now_text += ' %s hour(s)' % self.hours
            if self.minutes:
                self.now_text += ' %s min(s)' % self.minutes
            if self.seconds:
                self.now_text += ' %s sec(s)' % self.seconds
        elif self.submit_type == AddItemDialogBase.REMIND_AT:
            self.now_text += ' to be reminded at:'

        # self.setTitle(self.now_text)
        self.setMinimumHeight(100)

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonWidget = QtWidgets.QWidget()
        self.buttonLayout.setAlignment(QtCore.Qt.AlignRight)

        self.submitLabel = QtWidgets.QLabel(self.now_text)
        self.buttonLayout.addWidget(self.submitLabel)
        self.horizontalSpacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.buttonLayout.addItem(self.horizontalSpacer)
        self.deleteButton = QtWidgets.QLabel('X')
        self.deleteButton.setStyleSheet("QLabel {color: black}")
        self.deleteButton.mousePressEvent = self.deleteAction
        # self.deleteButton = QtWidgets.QPushButton('X')
        # self.deleteButton.setFixedSize(25, 25)
        # self.deleteButton.clicked.connect(self.deleteAction)
        self.buttonLayout.addWidget(self.deleteButton)
        self.buttonWidget.setLayout(self.buttonLayout)
        self.layout().addWidget(self.buttonWidget)

        self.remindWidget = QtWidgets.QGroupBox()
        self.remindLayout = QtWidgets.QVBoxLayout()
        self.remindWidget.setLayout(self.remindLayout)
        self.remindField = QtWidgets.QLabel(self.remind_time_text)
        self.remindLayout.addWidget(self.remindField)
        self.remindWidget.setTitle('Time To Remind')
        self.layout().addWidget(self.remindWidget)

        self.countdownField = QtWidgets.QLabel(self.countdown_text)
        # self.layout().addWidget(self.countdownField)

        self.notesWidget = QtWidgets.QGroupBox()
        self.notesLayout = QtWidgets.QVBoxLayout()
        self.notesWidget.setLayout(self.notesLayout)
        if self.notes is None:
            self.notes = 'No notes submitted'
        self.notesField = QtWidgets.QLabel(self.notes)
        self.notesField.setWordWrap(True)
        self.notesLayout.addWidget(self.notesField)
        self.notesWidget.setTitle('Notes')
        self.layout().addWidget(self.notesWidget)
        self.width = self.sizeHint().width()
        self.height = self.sizeHint().height()
        self.setMinimumWidth(self.width)
        self.setMinimumHeight(self.height)


    def startCountdownThread(self):
        timeValue = int(self.countdownField.text())
        if timeValue > 0:
            self.newCountdown = threading.Thread(target=self.countdownThread, args=(timeValue,))
            self.newCountdown.start()
        else:
            if nuke.GUI:
                nuke.message('Need countdown number to be 1 or above.')

    def stopCountdownThread(self, deleteCard=False):
        self.runThread = False
        if deleteCard:
            self.setParent(None)
        else:
            self.old_colour = mcCountdownMainPanel.OLD_COLOUR
            self.old_hex = self.old_colour[2:-2]
            self.old_rgb = tuple(int(self.old_hex[i:i+2], 16) for i in (0, 2, 4))
            r = self.old_rgb[0] + int(0.1 * self.rgb[0])
            g = self.old_rgb[1] + int(0.1 * self.rgb[1])
            b = self.old_rgb[2] + int(0.1 * self.rgb[2])
            self.new_colour = '0x%02x%02x%02xff' % (r, g, b)
            self.flashingThread = threading.Thread(target=self.colourFlashingThread, args=(self.old_colour, self.new_colour))
            self.flashingThread.start()

    def colourFlashingThread(self, old_colour, new_colour):
        for t in range(self.reminder_blinks):
            nuke.toNode('preferences').knob('DAGBackColor').fromScript(new_colour)
            time.sleep(0.5)
            nuke.toNode('preferences').knob('DAGBackColor').fromScript(old_colour)
            time.sleep(0.5)

    def countdownThread(self, timeValue):
        for t in range(1, timeValue + 1):
            if not self.runThread:
                break
            time.sleep(1)
            self.countdownField.setText(str(timeValue - t))
            if t == timeValue:
                self.setDagStatus(True)
                self.stopCountdownThread(False)
                # print 'DONE!'
            # print t, timeValue, self.getDagStatus()
        # print 'Stopped'

    def getStylesheet(self):
        self.rgb = []
        for i in range(3):
            self.rgb.append(random.randint(0, 255))
        ss = '#time_base {border: 1px solid rgb(%s, %s, %s);} ' % (self.rgb[0], self.rgb[1], self.rgb[2])
        ss += '#time_base::title {subcontrol-position: top left; padding:2 13px;}'
        return ss

    def deleteAction(self, event):
        self.stopCountdownThread(True)

    @classmethod
    def getDagStatus(cls):
        return cls.dagFlashing

    @classmethod
    def setDagStatus(cls, status):
        cls.dagFlashing = status


class mcCountdownMainPanel(QtWidgets.QWidget):
    OLD_COLOUR = nuke.toNode('preferences').knob('DAGBackColor').toScript()

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setContentsMargins(0, 0, 0, 0)

        self.MenuSpaceWidget = QtWidgets.QWidget()
        self.MenuSpaceLayout = QtWidgets.QHBoxLayout()
        self.MenuSpaceLayout.setContentsMargins(0, 0, 0, 0)
        self.MenuSpaceWidget.setLayout(self.MenuSpaceLayout)
        # self.MenuSpaceLayout.setAlignment(QtCore.Qt.AlignTop)
        self.layout().addWidget(self.MenuSpaceWidget)

        self.RemindInButton = QtWidgets.QPushButton('Remind Me In')
        self.MenuSpaceLayout.addWidget(self.RemindInButton)

        self.RemindAtButton = QtWidgets.QPushButton('Remind Me At')
        self.MenuSpaceLayout.addWidget(self.RemindAtButton)

        self.TimecardSpaceLayout = QtWidgets.QVBoxLayout()
        self.TimecardSpaceLayout.setContentsMargins(0, 0, 10, 0)
        self.TimecardSpaceScroll = QtWidgets.QScrollArea()
        self.TimecardSpaceScroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.TimecardSpaceScroll.setLayout(self.TimecardSpaceLayout)
        self.TimecardSpaceScroll.setWidgetResizable(True)
        self.TimecardSpaceWidget = QtWidgets.QWidget()
        # self.TimecardSpaceLayout2 = QtWidgets.QVBoxLayout()
        self.TimecardSpaceLayout.setAlignment(QtCore.Qt.AlignTop)
        self.TimecardSpaceWidget.setLayout(self.TimecardSpaceLayout)
        self.TimecardSpaceScroll.setWidget(self.TimecardSpaceWidget)
        self.layout().addWidget(self.TimecardSpaceScroll)

        self.layout().setAlignment(QtCore.Qt.AlignTop)

        self.setupConnections()

    def setupConnections(self):
        self.RemindInButton.clicked.connect(self.addRemindIn)
        self.RemindAtButton.clicked.connect(self.addRemindAt)

    def addRemindIn(self):
        self.addPanel = RemindInDialog(self)
        self.addPanel.show()

    def addRemindAt(self):
        self.addPanel = RemindAtDialog(self)
        self.addPanel.show()


def Install():
    pane = nuke.getPaneFor('Properties.1')
    panel = nukescripts.panels.registerWidgetAsPanel('mcCountdownPanelWidget.mcCountdownMainPanel', 'Reminder Panel', 'id.countdownPanel', True).addToPane(pane)

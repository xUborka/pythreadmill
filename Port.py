from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QLabel,\
    QSpinBox, QGroupBox


class Port(QWidget):
    positionTriggerChangedSignal = pyqtSignal(object)

    def __init__(self, name, appendPortList, getTreadmillData, treadmill):
        super(Port, self).__init__()
        self.name = name
        self.treadmill = treadmill
        self.getTreadmillData = getTreadmillData
        self.positionTriggerData = PositionTriggerData(self)

        # create worker thread
        self.worker = PositionTriggerWorker(self.positionTriggerData)
        self.initThread()
        self.positionTriggerChangedSignal.connect(self.worker.updateTriggerInterval)

        # initialize UI elements
        self.label = QLabel(self.name)
        self.editLabel = QLineEdit()
        self.switchButton = QPushButton("OFF")
        self.editTriggerDuration = QSpinBox()
        self.pulseButton = QPushButton("Impulse")
        self.pulseRepetitionButton = QPushButton("Single Shot")
        self.editTriggerPosition = QSpinBox()
        self.editTriggerWindow = QSpinBox()
        self.editTriggerRetention = QSpinBox()
        self.setButton = QPushButton("Set")
        self.restoreButton = QPushButton("Restore")
        self.groupboxPositionTrigger = QGroupBox()
        self.pulseTimer = QTimer()

        # set parameters of UI elements
        self.setUIElements()

        # update and send data about port instance to main thread
        self.getPositionTriggerData()
        appendPortList(self.positionTriggerData)

        self.portDictionary = {
            "switchButton":        self.switchButton,
            "pulseButton":         self.pulseButton,
            "triggerDuration":     self.editTriggerDuration,
            "triggerPosition":     self.editTriggerPosition,
            "triggerWindow":       self.editTriggerWindow,
            "triggerRetention":    self.editTriggerRetention,
            "timer":               self.pulseTimer,
            "onString":            self.name,
            "offString":           self.name.lower()
        }

    def setUIElements(self):
        self.editLabel.setPlaceholderText("port " + self.name)

        self.switchButton.setStyleSheet("color: white;" "background-color: red")
        self.switchButton.setCheckable(True)
        self.switchButton.toggled.connect(self.portSwitchAction)
        self.pulseTimer.timeout.connect(lambda: self.switchButton.setChecked(False))

        self.editTriggerDuration.setAlignment(Qt.AlignRight)
        self.editTriggerDuration.setSuffix(" ms")
        self.editTriggerDuration.valueChanged.connect(self.getPulseDuration)

        self.pulseButton.clicked.connect(self.pulseSignalAction)

        self.pulseRepetitionButton.setCheckable(True)
        self.pulseRepetitionButton.setFocusPolicy(Qt.NoFocus)
        self.pulseRepetitionButton.toggled.connect(self.pulseRepetitionButtonAction)

        self.editTriggerPosition.setAlignment(Qt.AlignRight)
        self.editTriggerPosition.setSuffix(" ‰")
        self.editTriggerPosition.valueChanged.connect(
            lambda: self.valueChanged(self.editTriggerPosition, self.positionTriggerData.start))

        self.editTriggerWindow.setAlignment(Qt.AlignRight)
        self.editTriggerWindow.setSuffix(" ‰")
        self.editTriggerWindow.valueChanged.connect(
            lambda: self.valueChanged(self.editTriggerWindow, self.positionTriggerData.window))

        self.editTriggerRetention.setAlignment(Qt.AlignRight)
        self.editTriggerRetention.setSuffix(" ms")
        self.editTriggerRetention.valueChanged.connect(
            lambda: self.valueChanged(self.editTriggerRetention, self.positionTriggerData.retention))

        self.setButton.clicked.connect(self.setButtonAction)

        self.restoreButton.clicked.connect(self.restoreButtonAction)

        self.groupboxPositionTrigger.setCheckable(True)
        self.groupboxPositionTrigger.toggled.connect(self.groupboxToggleAction)
        self.groupboxPositionTrigger.setChecked(False)
        # self.enableChildrenWidgets(self.groupboxPositionTrigger)

    def initThread(self):
        self.positionTriggerData.thread = QThread(self)
        self.worker.moveToThread(self.positionTriggerData.thread)
        self.positionTriggerData.thread.started.connect(self.worker.process)
        self.worker.finished.connect(self.positionTriggerData.thread.quit)
        self.worker.triggerSignal.connect(self.pulseSignalAction)
        # self.worker.finished.connect(self.worker.deleteLater)
        # self.positionTriggerData.thread.finished.connect(self.positionTriggerData.thread.deleteLater)

    def setSpinBox(self, name, minimum, maximum, value, step):
        spinBox = self.portDictionary[name]
        spinBox.setMinimum(minimum)
        spinBox.setMaximum(maximum)
        spinBox.setValue(value)
        spinBox.setSingleStep(step)

        self.setButtonAction()

    def portSwitchAction(self, checked):
        if checked:
            self.switchButton.setText("ON")
            self.switchButton.setStyleSheet("color: white;"
                                            "background-color: green;")
            self.pulseButton.setDisabled(True)
            self.treadmill.writeData(self.portDictionary["onString"])
        else:
            self.switchButton.setText("OFF")
            self.switchButton.setStyleSheet("color: white;"
                                            "background-color: red;")
            self.pulseButton.setDisabled(False)
            self.pulseTimer.stop()
            self.treadmill.writeData(self.portDictionary["offString"])

    def pulseSignalAction(self):
        pulseInterval = self.editTriggerDuration.value()
        self.pulseTimer.start(pulseInterval)
        self.switchButton.setChecked(True)

    def pulseRepetitionButtonAction(self, checked):
        if checked:
            self.pulseRepetitionButton.setText("Continuous Shot")
            self.worker.setTimerSingleShot(False)
        else:
            self.pulseRepetitionButton.setText("Single Shot")
            self.worker.setTimerSingleShot(True)

    def valueChanged(self, spinBox, reference):
        if spinBox.value() != reference:
            spinBox.setStyleSheet("background-color: yellow;")
        else:
            spinBox.setStyleSheet("background-color: white;")
    
    def getPulseDuration(self):
        self.positionTriggerData.duration = self.editTriggerDuration.value()

    def getPositionTriggerData(self):
        self.positionTriggerData.start = self.editTriggerPosition.value()
        self.positionTriggerData.window = self.editTriggerWindow.value()
        self.positionTriggerData.retention = self.editTriggerRetention.value()
        self.getPulseDuration()

    def setButtonAction(self):
        self.getPositionTriggerData()
        self.valueChanged(self.editTriggerPosition, self.positionTriggerData.start)
        self.valueChanged(self.editTriggerWindow, self.positionTriggerData.window)
        self.valueChanged(self.editTriggerRetention, self.positionTriggerData.retention)

        self.positionTriggerChangedSignal.emit(self.positionTriggerData)

    def restoreButtonAction(self):
        self.editTriggerPosition.setValue(self.positionTriggerData.start)
        self.editTriggerWindow.setValue(self.positionTriggerData.window)
        self.editTriggerRetention.setValue(self.positionTriggerData.retention)

    def groupboxToggleAction(self, isToggled):
        self.positionTriggerData.isActive = isToggled
        if not isToggled:
            self.enableChildrenWidgets(self.groupboxPositionTrigger)
            self.worker.terminate()

    def enableChildrenWidgets(self, object):
        for child in object.findChildren(QWidget):
            child.setEnabled(True)


class PositionTriggerData:
    def __init__(self, port):
        self.port = port
        self.thread: QThread
        self.isActive = False

        self.start: int
        self.window: int
        self.retention: int
        self.duration: int


class PositionTriggerWorker(QObject):
    triggerSignal = pyqtSignal()
    finished = pyqtSignal()
    checkerInterval = 50

    def __init__(self, positionTriggerData, parent=None):
        super(PositionTriggerWorker, self).__init__(parent)

        self.positionTriggerData = positionTriggerData
        self.getTreadmillData = positionTriggerData.port.getTreadmillData

        self.isRunning = True
        self.isSingleShot = True
        self.hasFired = False

        self.triggerTimer = QTimer(self)
        self.triggerTimer.setSingleShot(False)
        self.triggerTimer.timeout.connect(self.trigger)

        self.checkerTimer = QTimer(self)
        self.checkerTimer.setSingleShot(False)
        self.checkerTimer.timeout.connect(self.checkPosition)

    def process(self):
        self.hasFired = False
        self.checkerTimer.start(self.checkerInterval)
        self.triggerTimer.start(self.positionTriggerData.retention)

    def trigger(self):
        if self.isSingleShot:
            if not self.hasFired:
                self.triggerSignal.emit()
                # print("triggerTimer fired")
        else:
            self.triggerSignal.emit()
            # print("triggerTimer fired")
        self.hasFired = True

    def setTimerSingleShot(self, isSingleShot):
        # self.triggerTimer.setInterval(self.positionTriggerData.retention)
        self.isSingleShot = isSingleShot

    def updateTriggerInterval(self):
        self.triggerTimer.setInterval(self.positionTriggerData.retention)

    def checkPosition(self):
        treadmillData = self.getTreadmillData()
        if treadmillData.relPosition < self.positionTriggerData.start \
                or treadmillData.relPosition > (self.positionTriggerData.start + self.positionTriggerData.window):
            self.terminate()

    def terminate(self):
        self.isRunning = False
        self.hasFired = False
        self.checkerTimer.stop()
        self.triggerTimer.stop()
        self.finished.emit()

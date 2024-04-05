import os
import sys
import json
import random

from PySide2.QtGui import QPainter, QColor, QPen
from PySide2.QtCore import Qt, QUrl, QTimer, QPoint, QRectF, QSize, QPointF, Slot
from PySide2.QtWidgets import QApplication, QWidget, QPushButton
from PySide2.QtWebSockets import QWebSocket

from math import sin, cos

import logging

home_dir = os.path.expanduser("~")
logging.basicConfig(
    filename = os.path.join(home_dir, "output.log"), 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# CONTROL PANEL
# ----------------------------#
test_mode  = False
# ----------------------------#

def linspace(start, stop, num):
    step = (stop - start) / (num - 1)
    
    return [start + step * i for i in range(num)]
    
class FaceWidget(QWidget):

    def __init__(self, v1, v2, v3, v4, v5, stepsIn10s = 10, delay_time = 8000):
        logging.info("Init...")
        super().__init__()

        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.v4 = v4
        self.v5 = v5

        self.stepsIn10s = stepsIn10s
        self.delay_time = delay_time

        self.setupFaceParametersStatic()
        self.setupFaceParametersDynamic()

        self.setWindowTitle('Expression Changer')
        self.resize(self.sceen_width, self.sceen_height)

        self.left_pupil_offset  = QPoint(0, 0)  # Initial offset for left eye
        self.right_pupil_offset = QPoint(0, 0)  # Initial offset for right eye

        self.button1 = QPushButton('Eyelid' , self)
        self.button2 = QPushButton('Mouth ' , self)
        self.button3 = QPushButton('Eyebrow', self)
        self.button4 = QPushButton('Eye', self)
        self.button5 = QPushButton('Maluco', self)

        self.button1.setGeometry(0, 0, 80, 20)
        self.button2.setGeometry(0, 40, 80, 20)
        self.button3.setGeometry(0, 80, 80, 20)
        self.button4.setGeometry(0, 120, 80, 20)
        self.button5.setGeometry(0, 160, 80, 20)

        # self.button1.clicked.connect(self.changeEyelid)
        # self.button2.clicked.connect(self.changeExpression)
        # self.button3.clicked.connect(self.changeEyebrow)
        # self.button4.clicked.connect(self.changeEyePosition)
        # self.button5.clicked.connect(self.goMaluco)

        self.button1.clicked.connect(lambda: self.getExpression(self.happy))
        self.button2.clicked.connect(lambda: self.getExpression(self.sad))
        self.button3.clicked.connect(lambda: self.getExpression(self.angry))
        self.button4.clicked.connect(lambda: self.getExpression(self.sapecao))
        self.button5.clicked.connect(self.goMaluco)

        self.button1.setStyleSheet("background-color: transparent; border: 0px solid black; font-size: 1px;")
        self.button2.setStyleSheet("background-color: transparent; border: 0px solid black; font-size: 1px;")
        self.button3.setStyleSheet("background-color: transparent; border: 0px solid black; font-size: 1px;")
        self.button4.setStyleSheet("background-color: transparent; border: 0px solid black; font-size: 1px;")
        self.button5.setStyleSheet("background-color: transparent; border: 0px solid black; font-size: 1px;")
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateScreen)
        self.timer.start(100)

        self.timer_animation = QTimer(self)
        self.timer_animation.timeout.connect(self.updatePositions)
        self.timer_animation.start(50)

        self.delay = QTimer(self)
        self.delay.timeout.connect(self.resetDelay)
        self.delay.start(self.delay_time)

        self.is_conected = False
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.on_connected)
        self.websocket.disconnected.connect(self.on_disconnected)
        self.websocket.textMessageReceived.connect(self.on_message_received)

        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.try_reconnect)
        logging.info("Init done")

    def setupFaceParametersStatic(self):
        # Set screen Resolution
        self.sceen_width       = 1024
        self.sceen_height      = 600

        # Set colors
        self.eye_color_sclera  = QColor(255, 255, 255)  # White color for sclera
        self.iris_color        = QColor(40, 84, 144)    # Toradex Blue color for iris
        self.pupil_color       = QColor(255, 255, 255)  # White color for pupil
        self.eyelid_color      = QColor(240, 240, 240)  # Light gray (background) color for eyelid
        self.nose_color        = QColor(148, 204, 52)   # Red color for nose
        self.mouth_color       = QColor(40, 84, 144)    # Toradex Blue color for mouth
        self.eyebrow_color     = QColor(148, 204, 52)   # Toradex Green for eyebrow

        # eye parameters
        self.eye_radius        = round(self.sceen_height * 0.20)
        self.max_offset        = round(self.sceen_height * 10 / 100)  # Maximum offset for eye movement

        self.left_eye_center   = QPoint(self.sceen_width // 2 - self.sceen_width // 7, round(self.sceen_height * 0.3))
        self.right_eye_center  = QPoint(self.sceen_width // 2 + self.sceen_width // 7, round(self.sceen_height * 0.3))

        self.brow_length       = round(self.sceen_width * 20 / 100)
        self.brow_thickness    = round(self.sceen_width * 2 / 100)

        # nose parameters
        self.nose_size         = QSize(round(self.sceen_height * 9 / 100), round(self.sceen_height * 9 / 100))
        self.nose_center       = QPoint(round(self.sceen_width * 0.50), round(self.sceen_height * 0.6))
        self.nose_t            = self.sceen_width * (4 / 1000)

        # mouth parameters
        self.mouth_xpos        = round(self.sceen_width * 0.45)
        self.mouth_w           = round(self.sceen_width / 9)
        self.mouth_h           = round(self.sceen_height * 8 / 60)
        self.mouth_t           = self.sceen_width * (5 / 1000)

    def setupFaceParametersDynamic(self):
        o1                     = self.max_offset * 0.33
        o2                     = self.max_offset * 0.64

        # movement parameters
        self.blink_state       = 0
        self.blink_state_old   = 0
        self.blink_positions   = [
            # I have no idea how this works https://doc.qt.io/qt-6/qpainter.html#drawChord
            (-self.eye_radius, self.eye_radius * -1, True),
            (self.eye_radius - self.eye_radius, self.eye_radius - self.eye_radius // 3, True),
            (self.eye_radius + self.eye_radius * 0.70, self.eye_radius * 0.35, True),
            (self.eye_radius + self.eye_radius * 0.7, self.eye_radius * -0.4, True),
            (-self.eye_radius, self.eye_radius * -1, True),
            # (self.eye_radius + self.eye_radius * 2, self.eye_radius * 0.25, False),
        ]

        self.eye_state         = 0
        self.eye_state_old     = 0
        self.eye_positions     = [
            # (x1, y1, x2, y2), defined as offset from the center
            (0, 0, 0, 0),
            (o1, o1, o1, o1),
            
            (o1, o1, o1, -o1),
            (o1, o1, -o1, o1),
            (o1, -o1, o1, o1),
            (-o1, o1, o1, o1),
            
            (o1, o1, -o1, -o1),
            (o1, -o1, o1, -o1),
            (-o1, o1, o1, -o1),
            (o1, -o1, -o1, o1),
            (-o1, o1,-o1, o1),
            (-o1, -o1, o1, o1),

            (o1, -o1, -o1, -o1),
            (-o1, o1, -o1, -o1),
            (-o1, -o1, o1, -o1),
            (-o1, -o1, -o1, o1),

            (-o1, -o1, -o1, -o1),

            (o2, o2, o2, o2),
            
            (o2, o2, o2, -o2),
            (o2, o2, -o2, o2),
            (o2, -o2, o2, o2),
            (-o2, o2, o2, o2),
            
            (o2, o2, -o2, -o2),
            (o2, -o2, o2, -o2),
            (-o2, o2, o2, -o2),
            (o2, -o2, -o2, o2),
            (-o2, o2,-o2, o2),
            (-o2, -o2, o2, o2),

            (o2, -o2, -o2, -o2),
            (-o2, o2, -o2, -o2),
            (-o2, -o2, o2, -o2),
            (-o2, -o2, -o2, o2),

            (-o2, -o2, -o2, -o2),
            ]

        self.pupil_state       = 0
        self.pupil_state_old   = 0
        self.pupil_sizes       = [
            (round(self.eye_radius * 0.15), round(self.eye_radius * 0.15)), 
            (round(self.eye_radius * 0.25), round(self.eye_radius * 0.25)),
            (round(self.eye_radius * 0.15), round(self.eye_radius * 0.25)),
            (round(self.eye_radius * 0.25), round(self.eye_radius * 0.15)),
             ]

        self.mouth_state       = 0
        self.mouth_state_old   = 0
        self.mouth_positions   = [
            # (start_angle1, span_angle1, start_angle2, span_angle2, height1, height2), 
            # the mouth is 2 ellipsis arcs with the first ending at the point the second starts (to make the ~ mouth)
            ( 30,  50,  80,   50, round(self.sceen_height * 47 / 60), round(self.sceen_height * 47 / 60)),
            ( 30,  60,  90,   60, round(self.sceen_height * 47 / 60), round(self.sceen_height * 47 / 60)),
            (  0,  60,  60,   60, round(self.sceen_height * 47 / 60), round(self.sceen_height * 47 / 60)),

            (  0, 180,  180, 180, round(self.sceen_height * 47 / 60), round(self.sceen_height * 47 / 60)),

            (-30, -50,  -80, -50, round(self.sceen_height * 47 / 60), round(self.sceen_height * 47 / 60)),
            (-30, -60,  -90, -60, round(self.sceen_height * 47 / 60), round(self.sceen_height * 47 / 60)),
            (  0, -60,  -60, -60, round(self.sceen_height * 47 / 60), round(self.sceen_height * 47 / 60)),

            (-30, -60, -210, -60, round(self.sceen_height * 52 / 60), round(self.sceen_height * 44 / 60)),
            ( 30,  60,  210,  60, round(self.sceen_height * 44 / 60), round(self.sceen_height * 52 / 60)),
        ]

        self.brown_state       = 0
        self.brown_state_old   = 0
        self.brown_positions   = [
            (-15,  15),
            ( 15,  15),
            (-15, -15),
            {-15,  15},
            { 15, -15},
        ]

        # init states
        self.frame_n = 0
        self.transition  = False
        self.maluco      = False
        self.reset_delay = False
        self.brown_angle_l, self.brown_angle_r               = self.brown_positions[self.brown_state]
        self.blink_up, self.blink_down, self.blink1          = self.blink_positions[self.blink_state]
        self.left_pupil_size, self.right_pupil_size          = self.pupil_sizes    [self.pupil_state]
        self.a1, self.a2, self.a3, self.a4, self.h1, self.h2 = self.mouth_positions[self.mouth_state]
        self.x_left, self.y_left, self.x_right, self.y_right = self.eye_positions  [self.eye_state]
        self.interpolatePositions()

        self.happy   = {
            "0" : {
                "eyelid" : [0, 1, 4],
                "eye"    : [7, 12, 16, 23, 28, 32],
            },
            "1" : {
                "eyelid" : [0, 1, 2, 4],
                "eye"    : [3, 10],
            },
            "2" : {
                "eyelid" : [0, 1, 2, 3, 4],
                "eye"    : [17, 19, 26],
            },
            "eyebrow": [0, 1, 2],
            "mouth"  : [0, 1, 2],
            "pupil"  : [0, 1],
        }

        self.sad     = {
            "0" : {
                "eyelid" : [0, 1, 4],
                "eye"    : [7, 12, 16, 23, 28, 32],
            },
            "1" : {
                "eyelid" : [0, 1, 2, 4],
                "eye"    : [3, 10],
            },
            "2" : {
                "eyelid" : [0, 1, 2, 3, 4],
                "eye"    : [17, 19, 26],
            },
            "eyebrow": [0, 1 ,2],
            "mouth"  : [3, 4, 5, 6],
            "pupil"  : [0, 1],
        }

        self.angry   = {
            "0" : {
                "eyelid" : [0, 1, 4],
                "eye"    : [7, 12, 16, 23, 28, 32],
            },
            "1" : {
                "eyelid" : [0, 1, 2, 4],
                "eye"    : [3, 10],
            },
            "2" : {
                "eyelid" : [0, 1, 2, 3, 4],
                "eye"    : [17, 19, 26],
            },
            "eyebrow": [3],
            "mouth"  : [3, 4, 5, 6],
            "pupil"  : [0, 1],
        }

        self.sapecao = {
            "0" : {
                "eyelid" : [0, 1, 4],
                "eye"    : [7, 12, 16, 23, 28, 32],
            },
            "1" : {
                "eyelid" : [0, 1, 2, 4],
                "eye"    : [3, 10],
            },
            "2" : {
                "eyelid" : [0, 1, 2, 3, 4],
                "eye"    : [17, 19, 26],
            },
            "eyebrow": [3],
            "mouth"  : [0, 1, 2],
            "pupil"  : [0, 1],
        }

# <websocket handlers>
    def startConnection(self, url):
        random_expression = random.choice([self.happy, self.sad, self.angry, self.sapecao])

        self.getExpression(random_expression)

        self.url = url
        logging.info(f"Connecting to WebSocket server: {url}")
        self.websocket.open(QUrl(url))

    def try_reconnect(self):
        random_expression = random.choice([self.happy, self.sad, self.angry, self.sapecao])

        self.getExpression(random_expression)

        url = self.url
        logging.warning(f"reConnecting to WebSocket server: {url}")
        self.websocket.open(QUrl(url))

    @Slot(str)
    def send_message(self, message):
        self.websocket.sendTextMessage(message)

    @Slot()
    def on_connected(self):
        logging.warning("WebSocket connected")
        self.is_conected = True
        self.reconnect_timer.stop()
        
    @Slot()
    def on_disconnected(self):
        logging.warning("WebSocket disconnected")
        self.is_conected = False
        self.reconnect_timer.start(5000)

    @Slot(str)
    def on_message_received(self, message):
        try:
            telemetry_dict = json.loads(message)

            if "velocity" in telemetry_dict.keys():
                velocity = telemetry_dict.get("velocity")
                # print(f"Received velocity: {velocity}")

                if (velocity < self.v1) or (self.v5 < velocity):
                    self.maluco = True

                else:
                    self.maluco = False

                    if (self.v1 < velocity) and (velocity < self.v2) and (not self.reset_delay):
                        self.getExpression(self.sad)

                    elif (self.v2 < velocity) and (velocity < self.v3) and (not self.reset_delay):
                        self.getExpression(self.happy)

                    elif (self.v3 < velocity) and (velocity < self.v4) and (not self.reset_delay):
                        self.getExpression(self.sapecao)
                        
                    elif (self.v4 < velocity) and (velocity < self.v5) and (not self.reset_delay):
                        self.getExpression(self.angry)

            elif "message" in telemetry_dict.keys():
                logging.info(telemetry_dict["message"])

        except json.JSONDecodeError as e:
            logging.info(f"Error decoding JSON: {e}")

# <\websocket handlers>

    def drawFace(self, painter):
        self.left_pupil_offset.setX(self.x_left)
        self.left_pupil_offset.setY(self.y_left)
        self.right_pupil_offset.setX(self.x_right)
        self.right_pupil_offset.setY(self.y_right)

        self.drawEye(painter, self.left_eye_center , self.left_pupil_offset , self.left_pupil_size)
        self.drawEye(painter, self.right_eye_center, self.right_pupil_offset, self.right_pupil_size)

        self.drawEyelid(painter, self.left_eye_center , self.blink_up, self.blink_down)
        self.drawEyelid(painter, self.right_eye_center, self.blink_up, self.blink_down)

        self.drawEyebrow(painter, self.left_eye_center , self.brown_angle_l)
        self.drawEyebrow(painter, self.right_eye_center, self.brown_angle_r)

        self.drawNose(painter)
        self.drawMouth(painter)

    def drawEye(self, painter, eye_center, pupil_offset, pupil_size):
        # Draw eye whites (sclera)
        painter.setBrush(self.eye_color_sclera)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(eye_center, self.eye_radius, self.eye_radius)

        # Draw eye iris
        painter.setBrush(self.iris_color)
        painter.drawEllipse(eye_center, self.eye_radius * 0.75, self.eye_radius * 0.75)

        # Calculate pupil position
        pupil_center = eye_center + pupil_offset

        # Draw pupil
        painter.setBrush(self.pupil_color)
        pupil_rect = QRectF(pupil_center - QPoint(pupil_size, pupil_size),
                            pupil_center + QPoint(pupil_size, pupil_size))
        painter.drawEllipse(pupil_rect)

    def drawNose(self, painter):
        painter.setBrush(self.nose_color)
        painter.setPen(QPen(QPen(self.mouth_color, self.nose_t, Qt.SolidLine)))
        painter.drawEllipse(self.nose_center, self.nose_size.width(), self.nose_size.height())

    def drawMouth(self, painter):
        half_rect1 = QRectF(self.mouth_xpos, self.h1 , self.mouth_w, self.mouth_h)
        half_rect2 = QRectF(self.mouth_xpos, self.h2 , self.mouth_w, self.mouth_h)
        
        orientation = -16

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(self.mouth_color, self.mouth_t, Qt.SolidLine))
        painter.drawArc(half_rect1, self.a1 * orientation, self.a2 * orientation)
        painter.drawArc(half_rect2, self.a3 * orientation, self.a4 * orientation)

    def drawEyebrow(self, painter, eye_center, brow_angle):
        brow_start = QPoint(eye_center.x() - self.brow_length // 2, eye_center.y() - self.eye_radius)
        brow_end   = QPoint(eye_center.x() + self.brow_length // 2, eye_center.y() - self.eye_radius)

        # Calculate rotated points for eyebrow
        angle_rad = brow_angle * 3.14 / 180.0
        rot_start = QPoint(
            int((brow_start.x() - eye_center.x()) * round(cos(angle_rad), 2)) - (brow_start.y() - eye_center.y()) * round(sin(angle_rad), 2) + eye_center.x(),
            int((brow_start.x() - eye_center.x()) * round(sin(angle_rad), 2)) + (brow_start.y() - eye_center.y()) * round(cos(angle_rad), 2) + eye_center.y()
        )
        rot_end = QPoint(
            int((brow_end.x() - eye_center.x()) * round(cos(angle_rad), 2)) - (brow_end.y() - eye_center.y()) * round(sin(angle_rad), 2) + eye_center.x(),
            int((brow_end.x() - eye_center.x()) * round(sin(angle_rad), 2)) + (brow_end.y() - eye_center.y()) * round(cos(angle_rad), 2) + eye_center.y()
        )

        # Draw rotated eyebrows
        painter.setPen(QPen(self.eyebrow_color, self.brow_thickness))
        painter.drawLine(rot_start, rot_end)

    def drawEyelid(self, painter, eye_center, blink_up, blink_down):
        eyelid_rect_top = QRectF(eye_center.x() - self.eye_radius - self.eye_radius * 0.25, 
                                 eye_center.y() - self.eye_radius - self.eye_radius * 0.25,
                                 (self.eye_radius * 1.2) * 2, 
                                 self.eye_radius + blink_up)
        
        eyelid_rect_bot = QRectF(eye_center.x() - self.eye_radius - self.eye_radius * 0.25, 
                                 eye_center.y() - self.eye_radius + self.eye_radius * 0.75,
                                 (self.eye_radius * 1.2) * 2, 
                                 self.eye_radius + blink_down)

        start_angle = 0   * 16
        span_angle  = 180 * 16

        painter.setBrush(self.eyelid_color)
        if test_mode:
            painter.setBrush(Qt.red)
        painter.setPen(Qt.NoPen)
        painter.drawChord(eyelid_rect_top, start_angle, span_angle)
        painter.drawChord(eyelid_rect_bot, -start_angle, -span_angle)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.drawFace(painter)

# <drawing event>
    @Slot()
    def updateScreen(self):
        self.update()  # Update widget to trigger paintEvent

    @Slot()
    def updatePositions(self):
        if self.frame_n == self.stepsIn10s:
            self.transition  = False
            self.reset_delay = True
            self.blink_up, self.blink_down, self.blink1          = self.blink_positions[self.blink_state]
            self.a1, self.a2, self.a3, self.a4, self.h1, self.h2 = self.mouth_positions[self.mouth_state]

        if self.maluco:
            self.brown_state   = random.choice([0, 1, 2, 3])
            self.blink_state   = 0
            self.pupil_state   = random.choice([0, 1, 2, 3])
            self.mouth_state   = random.choice([len(self.mouth_positions) - 1, len(self.mouth_positions) - 2])
            
            self.x_left  = random.randint(-self.max_offset, self.max_offset)
            self.y_left  = random.randint(-self.max_offset, self.max_offset)
            self.y_right = random.randint(-self.max_offset, self.max_offset)
            self.x_right = random.randint(-self.max_offset, self.max_offset)

            self.brown_angle_l, self.brown_angle_r               = self.brown_positions[self.brown_state]
            self.blink_up, self.blink_down, self.blink1          = self.blink_positions[self.blink_state]
            self.left_pupil_size, self.right_pupil_size          = self.pupil_sizes    [self.pupil_state]
            self.a1, self.a2, self.a3, self.a4, self.h1, self.h2 = self.mouth_positions[self.mouth_state]

        elif self.transition:
            # self.x_left, self.y_left, self.x_right, self.y_right = self.eye_positions  [self.eye_state]
            # self.brown_angle_l, self.brown_angle_r               = self.brown_positions[self.brown_state]
            # self.left_pupil_size, self.right_pupil_size          = self.pupil_sizes    [self.pupil_state]

            self.x_left  = self.x_left_inter [self.frame_n]
            self.y_left  = self.y_left_inter [self.frame_n]
            self.x_right = self.x_right_inter[self.frame_n]
            self.y_right = self.y_right_inter[self.frame_n]

            self.brown_angle_l = self.brown_angle_l_inter[self.frame_n]
            self.brown_angle_r = self.brown_angle_r_inter[self.frame_n]

            # self.blink_up   = self.blink_up_inter[self.frame_n]
            # self.blink_down = self.blink_down_inter[self.frame_n]

            self.left_pupil_size  = self.left_pupil_size_inter[self.frame_n]
            self.right_pupil_size = self.right_pupil_size_inter[self.frame_n]

            # self.a1 = self.a1_inter[self.frame_n]
            # self.a2 = self.a2_inter[self.frame_n]
            # self.a3 = self.a3_inter[self.frame_n]
            # self.a4 = self.a4_inter[self.frame_n]
            # self.h1 = self.h1_inter[self.frame_n]
            # self.h2 = self.h2_inter[self.frame_n]

        self.frame_n += 1

    @Slot()
    def interpolatePositions(self):
        x_left_old, y_left_old, x_right_old, y_right_old = self.eye_positions  [self.eye_state_old]
        brown_angle_l_old, brown_angle_r_old             = self.brown_positions[self.brown_state_old]
        # blink_up_old, blink_down_old, blink1_old         = self.blink_positions[self.blink_state_old]
        left_pupil_size_old, right_pupil_size_old        = self.pupil_sizes    [self.pupil_state_old]
        # a1_old, a2_old, a3_old, a4_old, h1_old, h2_old   = self.mouth_positions[self.mouth_state_old]

        x_left_new, y_left_new, x_right_new, y_right_new = self.eye_positions  [self.eye_state]
        brown_angle_l_new, brown_angle_r_new             = self.brown_positions[self.brown_state]
        # blink_up_new, blink_down_new, blink1_new         = self.blink_positions[self.blink_state]
        left_pupil_size_new, right_pupil_size_new        = self.pupil_sizes    [self.pupil_state]
        # a1_new, a2_new, a3_new, a4_new, h1_new, h2_new   = self.mouth_positions[self.mouth_state]

        # Interpolators using linspace
        self.x_left_inter = linspace(x_left_old, x_left_new, self.stepsIn10s)
        self.y_left_inter = linspace(y_left_old, y_left_new, self.stepsIn10s)
        self.x_right_inter = linspace(x_right_old, x_right_new, self.stepsIn10s)
        self.y_right_inter = linspace(y_right_old, y_right_new, self.stepsIn10s)

        self.brown_angle_l_inter = linspace(brown_angle_l_old, brown_angle_l_new, self.stepsIn10s)
        self.brown_angle_r_inter = linspace(brown_angle_r_old, brown_angle_r_new, self.stepsIn10s)

        # self.blink_up_inter = linspace(blink_up_old, blink_up_new)
        # self.blink_down_inter = linspace(blink_down_old, blink_down_new)

        self.left_pupil_size_inter  = linspace(left_pupil_size_old, left_pupil_size_new, self.stepsIn10s)
        self.right_pupil_size_inter = linspace(right_pupil_size_old, right_pupil_size_new, self.stepsIn10s)

        # self.a1_inter = linspace(a1_old, a1_new)
        # self.a2_inter = linspace(a2_old, a2_new)
        # self.a3_inter = linspace(a3_old, a3_new)
        # self.a4_inter = linspace(a4_old, a4_new)
        # self.h1_inter = linspace(h1_old, h1_new)
        # self.h2_inter = linspace(h2_old, h2_new)

        self.frame_n    = 0

# <\drawing event>

    @Slot()
    def goMaluco(self):
        self.maluco = not self.maluco
        logging.info("Maluco = ", self.maluco)

    @Slot()
    def resetDelay(self):
        self.reset_delay = False

# <unused>
    @Slot()
    def changeExpression(self):
        self.mouth_state += 1

        if self.mouth_state == len(self.mouth_positions):
            self.mouth_state = 0

    @Slot()
    def changeEyebrow(self):
        self.frown = not self.frown

    @Slot()
    def changeEyelid(self):
        self.blink_state += 1
        if self.blink_state == len(self.blink_positions):
            self.blink_state = 0

    @Slot()
    def changeEyePosition(self):
        self.eye_state += 1
        if self.eye_state == len(self.eye_positions):
            self.eye_state = 0

# <\unused>

    @Slot(dict)
    def getExpression(self, expression_options):
        self.transition = True
        preface      = random.choice(["0", "1", "2"])

        self.brown_state_old = self.brown_state
        self.blink_state_old = self.blink_state
        self.eye_state_old   = self.eye_state
        self.mouth_state_old = self.mouth_state
        self.pupil_state_old = self.pupil_state

        self.brown_state = random.choice(expression_options["eyebrow"])
        self.blink_state = random.choice(expression_options[preface]["eyelid"])
        self.eye_state   = random.choice(expression_options[preface]["eye"])
        self.mouth_state = random.choice(expression_options["mouth"])
        self.pupil_state = random.choice(expression_options["pupil"])

        self.interpolatePositions()

        logging.info(f"Set expression to ({self.brown_state}, {self.blink_state}, {self.eye_state }, {self.mouth_state}, {self.pupil_state})")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    face_widget = FaceWidget()
    if test_mode:
        face_widget.show()
    else:
        face_widget.showFullScreen()
    sys.exit(app.exec_())
import sys
import time
import math
import cv2
import numpy as np
import threading
from serial import Serial
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QBrush, QColor, QFont
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QPointF, Qt


class GaussianBlur():
    # 初始化
    def __init__(self, radius=1, sigema=1.5):
        self.radius=radius
        self.sigema=sigema    
    # 高斯的计算公式
    def calc(self,x,y):
        res1=1/(2*math.pi*self.sigema*self.sigema)
        res2=math.exp(-(x*x+y*y)/(2*self.sigema*self.sigema))
        return res1*res2
    # 得到滤波模版
    def template(self):
        sideLength=self.radius*2+1
        result = np.zeros((sideLength, sideLength))
        for i in range(sideLength):
            for j in range(sideLength):
                result[i,j]=self.calc(i-self.radius, j-self.radius)
        all=result.sum()
        return result/all    
    # 滤波函数
    def filter(self, image, template): 
        arr=np.array(image)
        height=arr.shape[0]
        width=arr.shape[1]
        newData=np.zeros((height, width))
        for i in range(self.radius, height-self.radius):
            for j in range(self.radius, width-self.radius):
                t=arr[i-self.radius:i+self.radius+1, j-self.radius:j+self.radius+1]
                a= np.multiply(t, template)
                newData[i, j] = a.sum()
        # newImage = Image.fromarray(newData)
        return newData


def mapValue(value, curMin, curMax, desMin, desMax):
    curDistance = value - curMax
    if curDistance == 0:
        return desMax
    curRange = curMax - curMin
    direction = 1 if curDistance > 0 else -1
    ratio = curRange / curDistance
    desRange = desMax - desMin
    value = desMax + (desRange / ratio)
    return value


def constrain(value, down, up):
    value = up if value > up else value
    value = down if value < down else value
    return value        


def isDigital(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


hetaData = []
maxHet = 0
minHet = 0
lock = threading.Lock()


class SerialDataReader(QThread):
    def __init__(self, port, camera):
        super(SerialDataReader, self).__init__()
        self.port = port
        self.irc = camera
        self.com = Serial(self.port, 2000000, timeout=5)
        self.frameCount = 0

    def run(self):
        global maxHet
        global minHet
        # throw first frame
        self.com.read_until(terminator=b'\r\n')
        while True:
            hetData = self.com.read_until(terminator=b'\r\n')
            hetData = str(hetData, encoding="utf8").split(",")
            hetData = hetData[:-1]
            maxHet = 0
            minHet = 500
            tempData = []
            for i in range(0, 768):
                curCol = i % 32
                if curCol == 31:
                    tempData.append(0)
                    continue
                if i < len(hetData) and isDigital(hetData[i]):
                    tempData.append(float(hetData[i]))
                    maxHet = tempData[i] if tempData[i] > maxHet else maxHet
                    minHet = tempData[i] if tempData[i] < minHet else minHet
                else:
                    tempData.append(0)
            if maxHet == 0:
                continue
            # map value to 180-360
            for i in range(len(tempData)):
                tempData[i] = constrain(mapValue(tempData[i], minHet, maxHet, 180, 360), 180, 360)
            lock.acquire()
            hetaData.append(tempData)
            lock.release()
            self.irc.update()
            self.frameCount = self.frameCount + 1
            print("+++++" + str(self.frameCount))
        self.com.close()


class IRCamera(QWidget):
    pixelSize = 15
    width = 480
    height = 360
    col = width / pixelSize
    line = height / pixelSize
    centerIndex = round(((line / 2 - 1) * col) + col / 2)
    r=3 #模版半径，自己自由调整
    s=10 #sigema数值，自己自由调整
    GBlur = GaussianBlur(radius=r, sigema=s)#声明高斯模糊类
    temp = GBlur.template()#得到滤波模版
    frameCount = 0

    def __init__(self):
        super(IRCamera, self).__init__()
        self.resize(self.width, self.height + 40)

    def expand(self, frame):
        # frameData = [[0 for col in range(self.width)] for row in range(self.height)]
        # for y in range(self.height):
        #     for x in range(self.width):
        #         curIndex = (int(y/self.pixelSize) * int(self.col)) + int(x/self.pixelSize)
        #         frameData[y][x] = frame[curIndex]
        # return frameData
        col = int(self.col)
        row = int(self.line)
        frameData = [[0 for c in range(col)] for r in range(row)]
        index = 0
        for y in range(row):
            for x in range(col):
                frameData[y][x] = frame[index]
                index = index+1
        return frameData

    def paintEvent(self, event):
        if len(hetaData) == 0:
            return
        p = QPainter(self)
        # p.setRenderHint(QPainter.Antialiasing, True);
        font = QFont()
        color = QColor()
        font.setPointSize(27)
        font.setFamily("Microsoft YaHei")
        font.setLetterSpacing(QFont.AbsoluteSpacing,0)
        index = 0
        lock.acquire()
        frame = hetaData.pop(0)
        lock.release()
        p.fillRect(0, 0, self.width, self.height + 40, QBrush(QColor(Qt.black)))
        # frame = self.expand(frame)
        # frame = self.GBlur.filter(self.expand(frame), self.temp)
        # print(np.array(self.expand(frame)))
        frame = cv2.GaussianBlur(np.array(self.expand(frame)), (3, 3), 2)
        # print(frame.shape)
        # draw camera
        for yIndex in range(frame.shape[0]):
            for xIndex in range(frame.shape[1]):
                color.setHsvF(frame[yIndex][xIndex] / 360, 1.0, 1.0)
                p.fillRect(xIndex*15, yIndex*15, 15, 15, QBrush(color))
        # for yIndex in range(self.height):
        #     for xIndex in range(self.width):
        #         color = QColor()
        #         color.setHsvF(frame[yIndex][xIndex] / 360, 1.0, 1.0)
        #         p.setPen(color)
        #         p.drawPoint(xIndex, yIndex)
        # draw text
        hetDiff = maxHet - minHet
        bastNum = round(minHet)
        interval = round(hetDiff / 5)
        for i in range(5):
            # color = QColor()
            hue = constrain(mapValue((bastNum + (i * interval)), minHet, maxHet, 180, 360), 180, 360)
            color.setHsvF(hue / 360, 1.0, 1.0)
            p.setPen(color)
            p.setFont(font)
            p.drawText(i * 90, 390, str(bastNum + (i * interval)) + "°")
        # draw center
        centerX = self.width / 2
        centerY = self.height / 2
        # draw achor line
        p.setPen(QColor(Qt.white))
        p.drawLine(centerX - 50, centerY, centerX + 50, centerY)
        p.drawEllipse(centerX - 8, centerY - 8, 16, 16)
        p.drawLine(centerX, centerY - 50, centerX, centerY + 50)
        cneter = round(mapValue(frame[int(self.line/2)][int(self.col/2)], 180, 360, minHet, maxHet), 1)
        p.setPen(QColor(Qt.white))
        p.setFont(font)
        p.drawText(480 / 2 - 35, 30, str(cneter) + "°")
        self.frameCount = self.frameCount + 1
        print("-----"+str(self.frameCount))

def run():
    app = QApplication(sys.argv)
    m = IRCamera()
    dataThread = SerialDataReader(sys.argv[1], m)
    dataThread.start()
    m.show()
    app.exec_()


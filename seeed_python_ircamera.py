import sys
import threading
from serial import Serial
from PyQt5.QtWidgets import (
        QApplication,
        QGraphicsView,
        QGraphicsScene,
        QGraphicsPixmapItem,
        QGraphicsTextItem,
        QGraphicsEllipseItem,
        QGraphicsLineItem,
        QGraphicsBlurEffect
    )
from PyQt5.QtGui import QPainter, QBrush, QColor, QFont, QPixmap
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QPointF, Qt


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
        if value == "nan":
            return False
        else:
            float(value)
        return True
    except ValueError:
        return False


hetaData = []
maxHet = 0
minHet = 0
lock = threading.Lock()
minHue = 90
maxHue = 360


class SerialDataReader(QThread):
    drawRequire = pyqtSignal()
    def __init__(self, port):
        super(SerialDataReader, self).__init__()
        self.port = port
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
            nanCount = 0

            if  len(hetData) < 768 :
                continue

            for i in range(0, 768):
                curCol = i % 32
                newValueForNanPoint = 0
            

                if i < len(hetData) and isDigital(hetData[i]):
                    tempData.append(float(hetData[i]))
                    maxHet = tempData[i] if tempData[i] > maxHet else maxHet
                    minHet = tempData[i] if tempData[i] < minHet else minHet
                else:
                    interpolationPointCount = 0
                    sumValue = 0
                    # print("curCol",curCol,"i",i)

                    abovePointIndex = i-32
                    if (abovePointIndex>0):
                        if hetData[abovePointIndex] is not "nan" :
                            interpolationPointCount += 1
                            sumValue += float(hetData[abovePointIndex])

                    belowPointIndex = i+32
                    if (belowPointIndex<768):
                        print(" ")
                        if hetData[belowPointIndex] is not "nan" :
                            interpolationPointCount += 1
                            sumValue += float(hetData[belowPointIndex])
                            
                    leftPointIndex = i -1
                    if (curCol != 31):
                        if hetData[leftPointIndex]  is not "nan" :
                            interpolationPointCount += 1
                            sumValue += float(hetData[leftPointIndex])

                    rightPointIndex = i + 1
                    if (belowPointIndex<768):
                        if (curCol != 0):
                            if hetData[rightPointIndex] is not "nan" :
                                interpolationPointCount += 1
                                sumValue += float(hetData[rightPointIndex])

                    newValueForNanPoint =  sumValue /interpolationPointCount
                   
                    # For debug :
                    # print(abovePointIndex,belowPointIndex,leftPointIndex,rightPointIndex)
                    # print("newValueForNanPoint",newValueForNanPoint," interpolationPointCount" , interpolationPointCount ,"sumValue",sumValue)
                    
                    tempData.append(newValueForNanPoint)
                    nanCount +=1
            if maxHet == 0:
                continue
            # For debug :
            # if nanCount > 0 :
            #     print("____@@@@@@@ nanCount " ,nanCount , " @@@@@@@____")
           
            # map value to 180-360
            for i in range(len(tempData)):
                tempData[i] = constrain(mapValue(tempData[i], minHet, maxHet, minHue, maxHue), minHue, maxHue)
            lock.acquire()
            hetaData.append(tempData)
            lock.release()
            self.drawRequire.emit()
            self.frameCount = self.frameCount + 1
            print("data->" + str(self.frameCount))
        self.com.close()


class painter(QGraphicsView):
    narrowRatio = int(sys.argv[4]) if len(sys.argv) >= 5 else 1
    useBlur = sys.argv[5] != "False" if len(sys.argv) >= 6 else True
    pixelSize = int(15 / narrowRatio)
    width = int (480 / narrowRatio)
    height = int(360 / narrowRatio)
    fontSize = int(30 / narrowRatio)
    anchorLineSize = int(100 / narrowRatio)
    ellipseRadius = int(8 / narrowRatio)
    textInterval = int(90 / narrowRatio)
    col = width / pixelSize
    line = height / pixelSize
    centerIndex = int(round(((line / 2 - 1) * col) + col / 2))
    frameCount = 0
    baseZValue = 0
    textLineHeight = fontSize + 10
    blurRaduis = 50  # Smoother improvement
    def __init__(self):
        super(painter, self).__init__()
        self.setFixedSize(self.width, self.height + self.textLineHeight)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        # center het text item
        self.centerTextItem = QGraphicsTextItem()
        self.centerTextItem.setPos(self.width / 2 - self.fontSize, 0)
        self.centerTextItem.setZValue(self.baseZValue + 1)
        self.scene.addItem(self.centerTextItem)
        # center anchor item
        centerX = self.width / 2
        centerY = self.height / 2
        self.ellipseItem = QGraphicsEllipseItem(
                0, 0, 
                self.ellipseRadius * 2, 
                self.ellipseRadius * 2
            )
        self.horLineItem = QGraphicsLineItem(0, 0, self.anchorLineSize, 0)
        self.verLineItem = QGraphicsLineItem(0, 0, 0, self.anchorLineSize)
        self.ellipseItem.setPos(
                centerX - self.ellipseRadius, 
                centerY - self.ellipseRadius
            )
        self.horLineItem.setPos(centerX - self.anchorLineSize / 2, centerY)
        self.verLineItem.setPos(centerX, centerY - self.anchorLineSize / 2)
        self.ellipseItem.setPen(QColor(Qt.white))
        self.horLineItem.setPen(QColor(Qt.white))
        self.verLineItem.setPen(QColor(Qt.white))
        self.ellipseItem.setZValue(self.baseZValue + 1)
        self.horLineItem.setZValue(self.baseZValue + 1)
        self.verLineItem.setZValue(self.baseZValue + 1)
        self.scene.addItem(self.ellipseItem)
        self.scene.addItem(self.horLineItem)
        self.scene.addItem(self.verLineItem)
        # camera item
        self.cameraBuffer = QPixmap(self.width, self.height + self.textLineHeight)
        self.cameraItem = QGraphicsPixmapItem()
        if self.useBlur:
            self.gusBlurEffect = QGraphicsBlurEffect()
            self.gusBlurEffect.setBlurRadius(self.blurRaduis)
            self.cameraItem.setGraphicsEffect(self.gusBlurEffect)
        self.cameraItem.setPos(0, 0)
        self.cameraItem.setZValue(self.baseZValue)
        self.scene.addItem(self.cameraItem)
        # het text item
        self.hetTextBuffer = QPixmap(self.width, self.textLineHeight)
        self.hetTextItem = QGraphicsPixmapItem()
        self.hetTextItem.setPos(0, self.height)
        self.hetTextItem.setZValue(self.baseZValue)
        self.scene.addItem(self.hetTextItem)

    def draw(self):
        if len(hetaData) == 0:
            return
        font = QFont()
        color = QColor()
        font.setPointSize(self.fontSize)
        font.setFamily("Microsoft YaHei")
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0)
        index = 0
        lock.acquire()
        frame = hetaData.pop(0)
        lock.release()
        p = QPainter(self.cameraBuffer)
        p.fillRect(
                0, 0, self.width, 
                self.height + self.textLineHeight, 
                QBrush(QColor(Qt.black))
            )
        # draw camera
        color = QColor()
        for yIndex in range(int(self.height / self.pixelSize)):
            for xIndex in range(int(self.width / self.pixelSize)):
                color.setHsvF(frame[index] / 360, 1.0, 1.0)
                p.fillRect(
                    xIndex * self.pixelSize,
                    yIndex * self.pixelSize,
                    self.pixelSize, self.pixelSize,
                    QBrush(color)
                )
                index = index + 1
        self.cameraItem.setPixmap(self.cameraBuffer)
        # draw text
        p = QPainter(self.hetTextBuffer)
        p.fillRect(
                0, 0, self.width, 
                self.height + self.textLineHeight, 
                QBrush(QColor(Qt.black))
            )
        hetDiff = maxHet - minHet
        bastNum = round(minHet)
        interval = round(hetDiff / 5)
        for i in range(5):
            hue = constrain(mapValue((bastNum + (i * interval)), minHet, maxHet, minHue, maxHue), minHue, maxHue)
            color.setHsvF(hue / 360, 1.0, 1.0)
            p.setPen(color)
            p.setFont(font)
            p.drawText(i * self.textInterval, self.fontSize + 3, str(bastNum + (i * interval)) + "°")
        self.hetTextItem.setPixmap(self.hetTextBuffer)
        # draw center het text
        cneter = round(mapValue(frame[self.centerIndex], minHue, maxHue, minHet, maxHet), 1)
        centerText = "<font color=white>%s</font>"
        self.centerTextItem.setFont(font)
        self.centerTextItem.setHtml(centerText % (str(cneter) + "°"))
        self.frameCount = self.frameCount + 1
        print("picture->"+str(self.frameCount))


def run():
    global minHue
    global maxHue
    if len(sys.argv) < 2:
        print("Usage: %s PortName [minHue] [maxHue] [NarrowRatio] [UseBlur]" % sys.argv[0])
        exit(0)
    if len(sys.argv) >= 4:
        minHue = int(sys.argv[2])
        maxHue = int(sys.argv[3])
    app = QApplication(sys.argv)
    window = painter()
    dataThread = SerialDataReader(sys.argv[1])
    dataThread.drawRequire.connect(window.draw)
    dataThread.start()
    window.show()
    app.exec_()


import sys
from qtpy import QtWidgets as QW, QtGui as QG, QtCore as QC

# This is a simple GUI that allows you to paste coordinate arrays or QPainterPath commands such as the ones in ClientGUIPainterShapes.py and view the results live
# It's pretty simple and you need to remove the name e.g. REMOVE_THIS.moveTo(blah) for path commands

#e.g. heart shape
# QPainterPath()
# moveTo(6, 12)
# lineTo(1.5,6)
# cubicTo(0,4, 3.5,0, 6, 4)
# cubicTo(8.5,0, 12,4, 10.5,6)
# lineTo(6, 12)

class ShapePreviewWidget(QW.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.path = QG.QPainterPath()
        self.scale = 20

    def setPath(self, path: QG.QPainterPath):
        self.path = path
        self.update()

    def setPoints(self, points: list):
        self.path = QG.QPainterPath()
        if points:
            self.path.moveTo(points[0])
            for pt in points[1:]:
                self.path.lineTo(pt)
            self.path.closeSubpath()
        self.update()

    def paintEvent(self, event):
        painter = QG.QPainter(self)
        painter.setRenderHint(QG.QPainter.Antialiasing)

        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.translate(rect.center())
        painter.scale(self.scale, self.scale)
        painter.translate(-6, -6)

        pen = QG.QPen(QC.Qt.black, 0.1)
        painter.setPen(pen)
        painter.drawPath(self.path)

class MainWindow(QW.QWidget):
    def __init__(self):
        super().__init__()

        self.preview = ShapePreviewWidget()
        self.textEdit = QW.QPlainTextEdit()
        self.textEdit.setPlaceholderText("Paste coordinates or path here...")
        self.textEdit.textChanged.connect(self.parseAndDraw)

        layout = QW.QVBoxLayout()
        layout.addWidget(self.textEdit)
        layout.addWidget(self.preview)
        self.setLayout(layout)

        self.setWindowTitle("Shape Preview")
        self.resize(500, 600)

    def parseAndDraw(self):
        text = self.textEdit.toPlainText()

        if "QPainterPath" in text or "moveTo" in text:
            path = QG.QPainterPath()
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("moveTo"):
                    x, y = map(float, line[7:-1].split(","))
                    path.moveTo(x, y)
                elif line.startswith("lineTo"):
                    x, y = map(float, line[7:-1].split(","))
                    path.lineTo(x, y)
                elif line.startswith("cubicTo"):
                    points = list(map(float, line[8:-1].split(",")))
                    path.cubicTo(*points)
                elif line.startswith("closeSubpath"):
                    path.closeSubpath()
            self.preview.setPath(path)
        else:
            points = []
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("QC.QPointF"):
                    coords = line[line.find("(")+1:line.find(")")].split(",")
                    points.append(QC.QPointF(float(coords[0]), float(coords[1])))
            self.preview.setPoints(points)

if __name__ == '__main__':
    app = QW.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

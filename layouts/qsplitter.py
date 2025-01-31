"""1. Using QSplitter (Most Common):"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QTextEdit, QWidget
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create your panels/widgets
        left_panel = QTextEdit()
        right_panel = QTextEdit()

        # Add widgets to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Set the splitter as the central widget
        self.setCentralWidget(splitter)


app = QApplication([])
window = MainWindow()
window.show()
app.exec()

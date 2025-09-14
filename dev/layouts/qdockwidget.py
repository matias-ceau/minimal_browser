from PyQt6.QtWidgets import QApplication, QMainWindow, QDockWidget, QTextEdit, QWidget
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create central widget
        central_widget = QTextEdit()
        self.setCentralWidget(central_widget)

        # Create dock widget
        dock = QDockWidget("Side Panel", self)
        dock.setWidget(QTextEdit())
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Add dock widget to main window
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)


app = QApplication([])
window = MainWindow()
window.show()
app.exec()

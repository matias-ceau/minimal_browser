from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTextEdit


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create main widget and layout
        main_widget = QWidget()
        layout = QHBoxLayout()

        # Create panels
        left_panel = QTextEdit()
        right_panel = QTextEdit()

        # Add widgets to layout
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)

        # Set layout to main widget
        main_widget.setLayout(layout)

        # Set main widget as central widget
        self.setCentralWidget(main_widget)


app = QApplication([])
window = MainWindow()
window.show()
app.exec()

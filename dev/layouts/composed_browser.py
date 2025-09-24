"""4. More Complex Example with Multiple Panes:"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QTextEdit
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create main splitter (horizontal)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create left panel
        left_panel = QTextEdit()

        # Create vertical splitter for right side
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_top = QTextEdit()
        right_bottom = QTextEdit()
        right_splitter.addWidget(right_top)
        right_splitter.addWidget(right_bottom)

        # Add widgets to main splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_splitter)

        # Set the splitter as the central widget
        self.setCentralWidget(main_splitter)

        # Set initial sizes (optional)
        main_splitter.setSizes([200, 400])  # Left panel 200px, right panel 400px


app = QApplication([])
window = MainWindow()
window.show()
app.exec()

"""
Key points:

1. QSplitter is good for resizable panes with a draggable separator
2. QDockWidget is perfect for panels that need to be detachable or hideable
3. QHBoxLayout/QVBoxLayout are good for fixed-size or proportion-based layouts
4. You can combine these approaches for more complex layouts

Choose the approach that best fits your needs:
- Use QSplitter for vim-like panes
- Use QDockWidget for IDE-like panels that can be hidden/shown
- Use layouts for simpler, fixed arrangements

Remember to import the necessary modules and adjust the widgets inside the panels according to your needs (QTextEdit is just used as an example here).
"""

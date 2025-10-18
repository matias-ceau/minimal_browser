"""Command palette widget for vim-like commands"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit

from ..config.default_config import DEFAULT_CONFIG


COMMAND_PROMPT_STYLES = DEFAULT_CONFIG.ui.command_prompt_styles


class CommandPalette(QWidget):
    """Lightweight command palette widget with icon + input"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("CommandPalette")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        self.icon_label = QLabel("⌨️")
        self.icon_label.setObjectName("CommandIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedWidth(28)

        self.mode_label = QLabel("Command Mode")
        self.mode_label.setObjectName("CommandLabel")

        header.addWidget(self.icon_label)
        header.addWidget(self.mode_label)
        header.addStretch()

        self.input = QLineEdit()
        self.input.setObjectName("CommandInput")
        self.input.setClearButtonEnabled(True)
        self.input.setPlaceholderText("Run a Vim command (e.g. :help)")

        layout.addLayout(header)
        layout.addWidget(self.input)

        self.setStyleSheet(
            """
            #CommandPalette {
                background-color: rgba(20, 20, 20, 220);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            #CommandLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 1.1px;
                text-transform: uppercase;
            }
            #CommandIcon {
                font-size: 18px;
            }
            #CommandInput {
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                color: #ffffff;
                font-size: 14px;
                padding: 10px 14px;
                selection-background-color: rgba(118, 75, 162, 0.6);
            }
            #CommandInput:focus {
                border: 1px solid rgba(134, 84, 204, 0.8);
                background-color: rgba(255, 255, 255, 0.12);
            }
            """
        )

        self.setFocusProxy(self.input)

    def configure(self, prefix: str) -> None:
        style = COMMAND_PROMPT_STYLES.get(prefix)
        if style is None:
            style = {
                "icon": "⌨️",
                "label": "Command Mode",
                "placeholder": "Type a command",
                "bg_color": "rgba(20, 20, 20, 220)",
                "border_color": "rgba(255, 255, 255, 0.12)",
            }
        self.icon_label.setText(style["icon"])
        self.mode_label.setText(style["label"])
        self.input.setPlaceholderText(style["placeholder"])
        self.input.clear()
        
        # Update dynamic colors
        bg_color = style.get("bg_color", "rgba(20, 20, 20, 220)")
        border_color = style.get("border_color", "rgba(255, 255, 255, 0.12)")
        
        self.setStyleSheet(
            f"""
            #CommandPalette {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {border_color};
            }}
            #CommandLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 1.1px;
                text-transform: uppercase;
            }}
            #CommandIcon {{
                font-size: 18px;
            }}
            #CommandInput {{
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                color: #ffffff;
                font-size: 14px;
                padding: 10px 14px;
                selection-background-color: rgba(118, 75, 162, 0.6);
            }}
            #CommandInput:focus {{
                border: 1px solid rgba(134, 84, 204, 0.8);
                background-color: rgba(255, 255, 255, 0.12);
            }}
            """
        )

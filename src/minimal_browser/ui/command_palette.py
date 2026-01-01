"""Command palette widget for vim-like commands"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
)

from ..config.default_config import DEFAULT_CONFIG


COMMAND_PROMPT_STYLES = DEFAULT_CONFIG.ui.command_prompt_styles


class CommandPalette(QWidget):
    """Lightweight command palette widget with icon + input + autocomplete"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("CommandPalette")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.current_prefix: Optional[str] = None
        self.selected_index = -1
        self.command_registry: dict[str, str] = {}

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

        # Autocomplete suggestion list
        self.suggestion_list = QListWidget()
        self.suggestion_list.setObjectName("SuggestionList")
        self.suggestion_list.setMaximumHeight(200)
        self.suggestion_list.hide()
        self.suggestion_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addLayout(header)
        layout.addWidget(self.input)
        layout.addWidget(self.suggestion_list)

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
            #SuggestionList {
                background-color: rgba(30, 30, 30, 240);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 4px;
                outline: none;
            }
            #SuggestionList::item {
                padding: 6px 10px;
                border-radius: 4px;
                background-color: transparent;
            }
            #SuggestionList::item:selected {
                background-color: rgba(134, 84, 204, 0.4);
                color: #ffffff;
            }
            #SuggestionList::item:hover {
                background-color: rgba(134, 84, 204, 0.2);
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
        self.current_prefix = prefix
        self.selected_index = -1
        self.suggestion_list.clear()
        self.suggestion_list.hide()
        
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
            #SuggestionList {{
                background-color: rgba(20, 20, 20, 240);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 4px;
                max-height: 200px;
            }}
            #SuggestionList::item {{
                padding: 6px 10px;
                border-radius: 4px;
            }}
            #SuggestionList::item:selected {{
                background-color: rgba(134, 84, 204, 0.6);
                color: #ffffff;
            }}
            #SuggestionList::item:hover {{
                background-color: rgba(134, 84, 204, 0.4);
            }}
            """
        )

    def set_command_registry(self, commands: dict[str, str]) -> None:
        """Set the command registry for autocomplete"""
        self.command_registry = commands

    def update_suggestions(self, text: str, commands: dict[str, str]) -> None:
        """Update suggestion list based on input text"""
        if self.current_prefix != ":":
            self.suggestion_list.hide()
            return

        text = text.strip().lower()
        self.suggestion_list.clear()
        self.selected_index = -1

        if not text:
            # Show all commands when input is empty
            matches = list(commands.items())
        else:
            # Filter commands that start with the typed text
            matches = [
                (cmd, desc) for cmd, desc in commands.items() if cmd.lower().startswith(text)
            ]

        if not matches:
            self.suggestion_list.hide()
            return

        # Sort matches by command name
        matches.sort(key=lambda x: x[0])

        # Add matches to suggestion list
        for cmd, desc in matches:
            item = QListWidgetItem(f"{cmd:<12} {desc}")
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.suggestion_list.addItem(item)

        # Show and adjust size
        self.suggestion_list.show()
        item_count = min(len(matches), 5)  # Show max 5 items
        self.suggestion_list.setMaximumHeight(item_count * 32 + 8)
        
        # Select first item
        if self.suggestion_list.count() > 0:
            self.selected_index = 0
            self.suggestion_list.setCurrentRow(0)

    def get_selected_command(self) -> Optional[str]:
        """Get the currently selected command from suggestions"""
        current_item = self.suggestion_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def navigate_suggestions(self, direction: int) -> None:
        """Navigate up (-1) or down (1) in suggestions"""
        if not self.suggestion_list.isVisible():
            return

        count = self.suggestion_list.count()
        if count == 0:
            return

        if self.selected_index < 0:
            self.selected_index = 0 if direction > 0 else count - 1
        else:
            self.selected_index = (self.selected_index + direction) % count

        self.suggestion_list.setCurrentRow(self.selected_index)
        self.suggestion_list.scrollToItem(self.suggestion_list.currentItem())

    def select_suggestion(self) -> Optional[str]:
        """Select the current suggestion and return the command"""
        if not self.suggestion_list.isVisible():
            return None

        current_item = self.suggestion_list.currentItem()
        if current_item:
            cmd = current_item.data(Qt.ItemDataRole.UserRole)
            self.input.setText(cmd)
            self.suggestion_list.hide()
            return cmd
        return None


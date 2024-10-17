# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import json
import sys
import typing

import markdown  # type: ignore
from PyQt6.QtCore import (
    pyqtSignal,
    QObject,
    Qt,
    QThread,
)
from PyQt6.QtGui import (
    QClipboard,
    QCloseEvent,
    QColor,
    QPalette,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import _api

MAX_USER_MESSAGE_WIDTH = 400

CHAT_WINDOW_STYLE = """
QWidget {
    background-color: #212121;
}
QScrollArea {
    background-color: transparent; 
    border: none;
}
QScrollBar:vertical {
    background-color: #2F2F2F;
    width: 12px;
    margin: 0px 0px 0px 0px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #808080;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background-color: #2F2F2F;
    height: 12px;
    margin: 0px 0px 0px 0px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background-color: #808080;
    min-width: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
QTextEdit {
    background-color: #2F2F2F; 
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
}
QTextEdit:focus {
    border: 1px solid #FFFFFF;
}
QPushButton {
    background-color: #808080;
    color: #FFFFFF;
    border: none;
    padding: 5px;
    border-radius: 8px;
}
QPushButton:hover {
    background-color: #696969;
}
"""

USER_MESSAGE_STYLE = """

/* same as QLabel */
QTextBrowser {
    color: #FFFFFF;  /* White font color */
    background-color: #808080;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
    border-top-right-radius: 0px;  
    padding: 5px;
    text-align: left;
}
QTextBrowser:hover {
    background-color: #696969; 
}
AutoResizingTextBrowser {
    color: #FFFFFF;  /* White font color */
    background-color: #808080;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
    border-top-right-radius: 0px;
    padding: 5px;
    text-align: left;
}
AutoResizingTextBrowser:hover {
    background-color: #696969;
}
"""

ASSISTANT_MESSAGE_STYLE = """
QTextBrowser {
    color: #FFFFFF;  /* White font color */
    background-color: transparent; 
    border: none;
}
AutoResizingTextBrowser {
    color: #FFFFFF;  /* White font color */
    background-color: transparent; 
    border: none;
}
"""

COPY_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    border-radius: 10px;  
}
QPushButton:hover {
    background-color: #696969;
}
"""


# noinspection PyUnresolvedReferences
class ChatWorker(QObject):
    """
    Worker class for handling chat messages in a separate thread.
    """
    finished = pyqtSignal()
    responseReady = pyqtSignal(str)

    def __init__(
        self,
        message: str,
        cli: _api.GraphRAGCli,
        params: typing.Optional[typing.Dict[str, typing.Any]] = None
    ) -> None:
        super().__init__()
        self.message: str = message
        self.cli = cli
        self._stop = False
        self._stream_response: typing.Optional[typing.Generator[str, None, None]] = None
        self.params = params

    def run(self) -> None:
        """
        Processes the chat message and emits responses.
        """
        response = self.cli.chat(self.message, **(self.params or {}))
        self._stream_response = typing.cast(typing.Generator[str, None, None], response)
        for chunk in self._stream_response:
            if self._stop:
                break
            self.responseReady.emit(chunk)
        self.finished.emit()

    def stop(self) -> None:
        """
        Stops the worker process.
        """
        self._stop = True
        self.finished.emit()
        if self._stream_response:
            try:
                self._stream_response.close()
            except ValueError:
                pass


# noinspection PyUnresolvedReferences
class AutoResizingTextBrowser(QTextBrowser):
    """
    QTextBrowser that automatically adjusts its height based on its content.
    """

    def __init__(self, parent: typing.Optional[QWidget] = None, adjust: bool = False) -> None:
        super().__init__(parent)
        self.adjust_width = adjust
        document = self.document()
        if document:
            document.contentsChanged.connect(self.adjust_height)

    def adjust_height(self) -> None:
        """
        Adjusts the height of the text browser to fit its content.
        """
        document = self.document()
        if not document:
            return
        if self.adjust_width:
            font_metrics = self.fontMetrics()
            text_width = font_metrics.boundingRect(self.toPlainText()).width()
            self.setFixedWidth(min(text_width, MAX_USER_MESSAGE_WIDTH) + 20)

        docLayout = document.documentLayout()
        docHeight = docLayout.documentSize().height() if docLayout else document.size().height()
        totalHeight = docHeight + self.frameWidth() * 2

        self.setFixedHeight(int(totalHeight))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_height()


# noinspection PyUnresolvedReferences
class AutoResizingTextEdit(QTextEdit):
    """
    QTextEdit that automatically adjusts its height based on its content.
    """

    def __init__(self, parent: typing.Optional[QWidget] = None) -> None:
        super().__init__(parent)
        document = self.document()
        if document:
            document.contentsChanged.connect(self.adjust_height)

    def adjust_height(self) -> None:
        """
        Adjusts the height of the text edit to fit its content.
        """
        document = self.document()
        if not document:
            return
        docHeight = document.size().height()
        margins = self.contentsMargins()
        totalHeight = docHeight + margins.top() + margins.bottom() + self.frameWidth() * 2
        self.setFixedHeight(min(100, int(totalHeight)))

    def keyPressEvent(self, event):
        """
        Handles key press events, sending the message on Ctrl+Enter.
        """
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.parent().send_message()
        else:
            super().keyPressEvent(event)


# noinspection PyUnresolvedReferences
class ChatWindow(QWidget):
    """
    The main window for the chat application.
    """

    def __init__(self, cli: _api.GraphRAGCli, **kwargs: typing.Any) -> None:
        super().__init__()
        self.cli = cli
        self.params = kwargs

        self.assistant_label: typing.Optional[QWidget] = None
        self.assistant_response_text: str = ''
        self.setWindowTitle('Chat with GraphRAG')
        self.resize(600, 500)
        self.layout_ = QVBoxLayout()

        # Toolbar
        self.toolbar = QWidget()
        self.toolbarLayout = QHBoxLayout()
        self.toolbarLayout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.copyButton = QPushButton('Copy')
        self.copyButton.setStyleSheet(COPY_BUTTON_STYLE)
        self.copyButton.clicked.connect(self.copy_conversation)
        self.toolbarLayout.addWidget(self.copyButton)
        self.toolbar.setLayout(self.toolbarLayout)
        self.layout_.addWidget(self.toolbar)

        # Chat area
        self.chatScrollArea = QScrollArea()
        self.chatScrollArea.setWidgetResizable(True)
        self.chatWidget = QWidget()
        self.chatLayout = QVBoxLayout()
        self.chatLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chatWidget.setLayout(self.chatLayout)
        self.chatScrollArea.setWidget(self.chatWidget)

        # Input area
        self.inputText = AutoResizingTextEdit()
        self.inputText.setPlaceholderText('Type your message here...')
        self.inputText.adjust_height()

        # Send button
        self.sendButton = QPushButton('Send')
        self.sendButton.clicked.connect(self.send_message)

        # Clear button
        self.clearButton = QPushButton('Clear')
        self.clearButton.clicked.connect(self.clear_history)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.clearButton)
        buttonLayout.addWidget(self.sendButton)

        inputLayout = QHBoxLayout()
        inputLayout.addWidget(self.inputText)
        inputLayout.addLayout(buttonLayout)

        self.layout_.addWidget(self.chatScrollArea)
        self.layout_.addLayout(inputLayout)
        self.setLayout(self.layout_)
        self.thread_: typing.Optional[QThread] = None
        self.worker: typing.Optional[ChatWorker] = None

        self.setStyleSheet(CHAT_WINDOW_STYLE)

    def copy_conversation(self) -> None:
        """
        Copies the conversation history to the clipboard.
        """
        conversation = self.cli.conversation_history()
        conversation_text = json.dumps(conversation, ensure_ascii=False, indent=4)
        typing.cast(QClipboard, QApplication.clipboard()).setText(conversation_text)

    def send_message(self) -> None:
        """
        Sends the user's message to the assistant.
        """
        message = self.inputText.toPlainText().strip()
        if not message:
            return

        # Display user's message
        user_message_widget = self.create_message_widget(message, sender='User')
        self.chatLayout.addWidget(user_message_widget)
        self.inputText.clear()

        # Add an empty assistant message container
        self.assistant_label = self.create_message_widget("", sender='Assistant')
        self.chatLayout.addWidget(self.assistant_label)
        self.assistant_response_text = ''

        # Start worker thread to process simulated response
        self.thread_ = QThread()
        self.worker = ChatWorker(message, cli=self.cli, params=self.params)
        self.worker.moveToThread(self.thread_)

        # Connect signals and slots
        self.thread_.started.connect(self.worker.run)
        self.worker.responseReady.connect(self.update_response)
        self.worker.finished.connect(self.thread_.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread_.finished.connect(self.thread_.deleteLater)

        # Disable send button until response is finished
        self.sendButton.setEnabled(False)
        self.thread_.finished.connect(lambda: self.sendButton.setEnabled(True))
        self.thread_.start()

    def clear_history(self) -> None:
        """
        Clears the chat history and resets the interface.
        """
        try:
            if self.worker:
                self.worker.stop()
                self.worker.responseReady.disconnect(self.update_response)
        except (RuntimeError, TypeError):
            pass

        self.cli.clear_history()
        while self.chatLayout.count():
            child = self.chatLayout.takeAt(0)
            if child and child.widget():
                typing.cast(QWidget, child.widget()).deleteLater()

        self.chatWidget.update()
        self.chatScrollArea.update()
        self.sendButton.setEnabled(True)

    @staticmethod
    def create_message_widget(text: str, sender: str = 'User') -> QWidget:
        """
        Creates a message widget for the chat interface.

        Args:
            text: The message text.
            sender: 'User' or 'Assistant' indicating the sender.

        Returns:
            The message widget.
        """
        # Create a container to set alignment
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 5, 10, 5)

        # Create message container
        if sender == 'Assistant':
            message_widget = AutoResizingTextBrowser()
            message_widget.setReadOnly(True)
            message_widget.setStyleSheet(ASSISTANT_MESSAGE_STYLE)
            message_widget.setOpenExternalLinks(True)
            message_widget.setOpenLinks(True)
            message_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            message_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            message_widget.setHtml(markdown.markdown(text))

            container_layout.addWidget(message_widget, 0, Qt.AlignmentFlag.AlignTop)
        else:
            message_widget = AutoResizingTextBrowser(adjust=True)
            message_widget.setReadOnly(True)
            message_widget.setStyleSheet(USER_MESSAGE_STYLE)
            message_widget.setOpenExternalLinks(False)
            message_widget.setOpenLinks(False)
            message_widget.setPlainText(text)
            message_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            container_layout.addWidget(message_widget, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        container.setLayout(container_layout)
        return container

    def update_response(self, chunk: str) -> None:
        """
        Updates the assistant's response in the chat interface.

        Args:
            chunk: A chunk of the assistant's response text.
        """
        if self.assistant_label:
            self.assistant_response_text += chunk
            # Update the content of the message widget
            message_widget = self.assistant_label.findChild(AutoResizingTextBrowser)
            if isinstance(message_widget, AutoResizingTextBrowser):
                html_content = markdown.markdown(self.assistant_response_text)
                message_widget.setHtml(html_content)
            # Auto-scroll to the bottom
            scroll_bar = self.chatScrollArea.verticalScrollBar()
            if scroll_bar:
                scroll_bar.setValue(scroll_bar.maximum())

    def closeEvent(self, event: typing.Optional[QCloseEvent]) -> None:
        if event:
            event.accept()


def main(cli: _api.GraphRAGCli, **kwargs: typing.Any) -> None:
    """
    Runs the chat GUI application.

    Args:
        cli: An instance of GraphRAGCli.
        **kwargs: Additional parameters.
    """
    app = QApplication(sys.argv)

    # Set application palette to dark theme
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(23, 23, 23))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    app.setPalette(palette)

    window = ChatWindow(cli, **kwargs)
    window.show()
    sys.exit(app.exec())

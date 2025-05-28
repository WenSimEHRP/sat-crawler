#!/usr/bin/env python3
import sys
import os
import traceback
from typing import Optional, Tuple, Dict, Any, Callable, Union, Literal

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTabWidget,
    QGroupBox,
    QCheckBox,
    QRadioButton,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QLabel,
    QMessageBox,
    QScrollBar,
)
from PySide6.QtCore import QThread, Signal

# Type definitions
ProgressCallback = Optional[Callable[[int, str], None]]
ParametersDict = Dict[str, Union[str, bool]]
PaperSizeType = Literal["us-letter", "a4", "legal", "a3"]

# Import the main functions directly
try:
    from crawl import main as crawl_main
    from make_pdf import main as pdf_main
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class WorkerThread(QThread):
    """Thread for running functions directly"""

    output_received: Signal = Signal(str)
    progress_updated: Signal = Signal(int, str)
    finished_signal: Signal = Signal(int, str)

    def __init__(self, func: Callable[..., None], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.func: Callable[..., None] = func
        self.args: Tuple[Any, ...] = args
        self.kwargs: Dict[str, Any] = kwargs
        self.should_stop: bool = False

    def run(self) -> None:
        """Run the function and emit signals"""
        try:
            self.output_received.emit(f"Starting {self.func.__name__}...")

            # Create progress callback that emits signals
            def progress_callback(value: int, message: str) -> None:
                self.progress_updated.emit(value, message)
                self.output_received.emit(f"Progress {value}%: {message}")

            # Add progress_callback to kwargs if not present
            if "progress_callback" not in self.kwargs:
                self.kwargs["progress_callback"] = progress_callback

            # Capture print statements as well
            import io
            from contextlib import redirect_stdout, redirect_stderr

            output_buffer: io.StringIO = io.StringIO()
            error_buffer: io.StringIO = io.StringIO()

            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                # Run the function
                self.func(*self.args, **self.kwargs)

            # Get output
            stdout_content: str = output_buffer.getvalue()
            stderr_content: str = error_buffer.getvalue()

            # Emit output line by line
            if stdout_content:
                for line in stdout_content.strip().split("\n"):
                    if line.strip():
                        self.output_received.emit(line)

            if stderr_content:
                for line in stderr_content.strip().split("\n"):
                    if line.strip():
                        self.output_received.emit(f"ERROR: {line}")

            self.finished_signal.emit(0, "Process completed successfully!")

        except Exception as e:
            error_msg: str = f"Error: {str(e)}\n{traceback.format_exc()}"
            self.output_received.emit(error_msg)
            self.finished_signal.emit(-1, f"Error: {str(e)}")

    def stop(self) -> None:
        """Stop the running process"""
        self.should_stop = True


class CrawlerTab(QWidget):
    """Tab for SAT Question Crawler"""

    def __init__(self) -> None:
        super().__init__()
        self.debug_checkbox: QCheckBox
        self.setup_ui()

    def setup_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout()
        self.setLayout(layout)

        # Settings group
        settings_group: QGroupBox = QGroupBox("Crawler Settings")
        settings_layout: QVBoxLayout = QVBoxLayout()

        # Debug mode checkbox
        self.debug_checkbox = QCheckBox("Debug mode (100 questions per section)")
        settings_layout.addWidget(self.debug_checkbox)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Description
        desc_text: str = "Fetches SAT questions and saves to reading.csv, math.csv, and questions.json"
        desc_label: QLabel = QLabel(desc_text)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

    def get_parameters(self) -> ParametersDict:
        """Get the parameters for the crawler function"""
        return {"debug": self.debug_checkbox.isChecked()}


class PDFTab(QWidget):
    """Tab for PDF Generator"""

    def __init__(self) -> None:
        super().__init__()
        self.paper_buttons: Dict[str, QRadioButton] = {}
        self.output_edit: QLineEdit
        self.answer_buttons: Dict[str, QRadioButton] = {}
        self.setup_ui()

    def setup_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout()
        self.setLayout(layout)

        # Main two-column layout
        main_layout: QHBoxLayout = QHBoxLayout()

        # Left column
        left_column: QVBoxLayout = QVBoxLayout()

        # Paper size group - compact
        paper_group: QGroupBox = QGroupBox("Paper Size")
        paper_layout: QVBoxLayout = QVBoxLayout()

        self.paper_buttons = {}
        paper_sizes: list[Tuple[str, str]] = [
            ("Letter", "us-letter"),
            ("A4", "a4"),
            ("Legal", "legal"),
            ("A3", "a3"),
        ]

        for text, value in paper_sizes:
            radio: QRadioButton = QRadioButton(text)
            if value == "us-letter":
                radio.setChecked(True)
            self.paper_buttons[value] = radio
            paper_layout.addWidget(radio)

        paper_group.setLayout(paper_layout)
        left_column.addWidget(paper_group)
        left_column.addStretch()

        # Right column
        right_column: QVBoxLayout = QVBoxLayout()

        # Output prefix - compact
        output_group: QGroupBox = QGroupBox("Output")
        output_layout: QVBoxLayout = QVBoxLayout()

        prefix_layout: QHBoxLayout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Prefix:"))
        self.output_edit = QLineEdit("questions")
        prefix_layout.addWidget(self.output_edit)
        output_layout.addLayout(prefix_layout)

        output_group.setLayout(output_layout)
        right_column.addWidget(output_group)

        # Answer options - radio buttons
        answer_group: QGroupBox = QGroupBox("Answer Options")
        answer_layout: QVBoxLayout = QVBoxLayout()

        self.answer_buttons = {}
        answer_options: list[Tuple[str, str]] = [
            ("Both questions and answers", "both"),
            ("Only answers", "answers_only"),
            ("No answers", "no_answers"),
        ]

        for text, value in answer_options:
            radio: QRadioButton = QRadioButton(text)
            if value == "both":
                radio.setChecked(True)
            self.answer_buttons[value] = radio
            answer_layout.addWidget(radio)

        answer_group.setLayout(answer_layout)
        right_column.addWidget(answer_group)
        right_column.addStretch()

        # Add columns to main layout
        main_layout.addLayout(left_column)
        main_layout.addLayout(right_column)
        layout.addLayout(main_layout)

        # Description
        desc_text: str = "Generates PDFs from questions.json. Run crawler first."
        desc_label: QLabel = QLabel(desc_text)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

    def get_paper_size(self) -> str:
        """Get selected paper size"""
        for value, radio in self.paper_buttons.items():
            if radio.isChecked():
                return value
        return "us-letter"

    def get_answer_option(self) -> str:
        """Get selected answer option"""
        for value, radio in self.answer_buttons.items():
            if radio.isChecked():
                return value
        return "both"

    def get_parameters(self) -> ParametersDict:
        """Get the parameters for the PDF generator function"""
        answer_option: str = self.get_answer_option()

        return {
            "paper_size": self.get_paper_size(),
            "output": self.output_edit.text(),
            "answers_only": answer_option == "answers_only",
            "no_answers": answer_option == "no_answers",
        }


class SATCrawlerGUI(QMainWindow):
    """Main GUI application"""

    def __init__(self) -> None:
        super().__init__()
        self.worker_thread: Optional[WorkerThread] = None
        self.tab_widget: QTabWidget
        self.crawler_tab: CrawlerTab
        self.pdf_tab: PDFTab
        self.run_button: QPushButton
        self.stop_button: QPushButton
        self.status_label: QLabel
        self.progress_bar: QProgressBar
        self.log_text: QTextEdit
        self.log_group: QGroupBox
        self.hide_output_checkbox: QCheckBox
        self.setup_ui()
        self.check_dependencies()

    def setup_ui(self) -> None:
        """Setup the user interface"""
        self.setWindowTitle("SAT Crawler GUI")
        self.setGeometry(100, 100, 400, 370)
        self.setMinimumSize(400, 370)

        # Central widget
        central_widget: QWidget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout: QVBoxLayout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.crawler_tab = CrawlerTab()
        self.pdf_tab = PDFTab()

        self.tab_widget.addTab(self.crawler_tab, "Crawler")
        self.tab_widget.addTab(self.pdf_tab, "PDF Generator")

        layout.addWidget(self.tab_widget)

        # Control buttons
        button_layout: QHBoxLayout = QHBoxLayout()

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_current_tab)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setEnabled(False)

        # Hide output checkbox
        self.hide_output_checkbox = QCheckBox("Hide output")
        self.hide_output_checkbox.setChecked(True)
        self.hide_output_checkbox.toggled.connect(self.toggle_output_visibility)

        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.hide_output_checkbox)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Progress section
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Log section
        self.log_group = QGroupBox("Output")
        log_layout: QVBoxLayout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        clear_button: QPushButton = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_button)

        self.log_group.setLayout(log_layout)
        layout.addWidget(self.log_group)

        self.log_group.setVisible(False)

    def toggle_output_visibility(self, checked: bool) -> None:
        """Toggle the visibility of the output section"""
        self.log_group.setVisible(not checked)

        # Adjust window size when hiding/showing output
        if checked:
            # Hide output - make window smaller
            self.resize(400, 370)
        else:
            # Show output - make window larger
            self.resize(400, 600)

    def check_dependencies(self) -> None:
        """Check if required files exist"""
        missing_files: list[str] = []

        if not os.path.exists("crawl.py"):
            missing_files.append("crawl.py")

        if not os.path.exists("make_pdf.py"):
            missing_files.append("make_pdf.py")

        if missing_files:
            QMessageBox.critical(
                self,
                "Missing Files",
                f"Required files not found: {', '.join(missing_files)}\n\n"
                "Please ensure you're running this GUI from the correct directory.",
            )

    def run_current_tab(self) -> None:
        """Run the function for the currently selected tab"""
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Warning", "A process is already running!")
            return

        # Get function and parameters based on current tab
        current_index: int = self.tab_widget.currentIndex()

        if current_index == 0:  # Crawler tab
            params: ParametersDict = self.crawler_tab.get_parameters()
            func: Callable[..., None] = crawl_main
            process_name: str = "Crawler"

            # Call with debug parameter
            self.start_function(func, process_name, debug=params["debug"])

        elif current_index == 1:  # PDF tab
            # Check if questions.json exists
            if not os.path.exists("questions.json"):
                QMessageBox.critical(
                    self,
                    "Missing Data",
                    "questions.json not found!\n\n"
                    "Please run the Question Crawler first.",
                )
                return

            params = self.pdf_tab.get_parameters()
            func = pdf_main
            process_name = "PDF Generator"

            # Call with all PDF parameters
            self.start_function(
                func,
                process_name,
                paper_size=params["paper_size"],
                output=params["output"],
                answers_only=params["answers_only"],
                no_answers=params["no_answers"],
            )

    def start_function(
        self, func: Callable[..., None], process_name: str, **kwargs: Any
    ) -> None:
        """Start a new function in a worker thread"""
        self.log_message(f"Starting {process_name}...")
        self.log_message(f"Parameters: {kwargs}")

        # Update UI state
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Starting {process_name}...")

        # Create and start thread
        self.worker_thread = WorkerThread(func, **kwargs)
        self.worker_thread.output_received.connect(self.log_message)
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.finished_signal.connect(self.process_finished)
        self.worker_thread.start()

    def stop_process(self) -> None:
        """Stop the current process"""
        if self.worker_thread:
            self.worker_thread.stop()
            self.log_message("Process stopped by user")
            self.status_label.setText("Stopped")
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def update_progress(self, value: int, description: str) -> None:
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(description)

    def process_finished(self, return_code: int, message: str) -> None:
        """Handle process completion"""
        self.log_message(message)

        if return_code == 0:
            self.status_label.setText("Completed successfully")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText("Process failed")

        # Update UI state
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def log_message(self, message: str) -> None:
        """Add message to log"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar: QScrollBar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self) -> None:
        """Clear the log"""
        self.log_text.clear()


def main() -> int:
    """Main function"""
    app: QApplication = QApplication(sys.argv)

    # Create and show main window
    window: SATCrawlerGUI = SATCrawlerGUI()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

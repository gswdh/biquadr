"""
Target management dialog for creating and editing targets.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
)
from PyQt6.QtCore import pyqtSignal

from models import Target, DataType


class TargetDialog(QDialog):
    """Dialog for creating or editing targets."""

    target_created = pyqtSignal(Target)
    target_updated = pyqtSignal(Target)

    def __init__(self, parent=None, target: Target = None):
        super().__init__(parent)
        self.target = target
        self.setWindowTitle("Edit Target" if target else "Create Target")
        self.setModal(True)
        self.resize(400, 200)

        self.setup_ui()
        self.load_target_data()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Form layout for target properties
        form_layout = QFormLayout()

        # Target name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter target name...")
        form_layout.addRow("Name:", self.name_edit)

        # Data type
        self.data_type_combo = QComboBox()
        for data_type in DataType:
            self.data_type_combo.addItem(data_type.value, data_type)
        form_layout.addRow("Data Type:", self.data_type_combo)

        # Maximum filter order
        self.max_order_spin = QSpinBox()
        self.max_order_spin.setRange(2, 32)
        self.max_order_spin.setValue(8)
        form_layout.addRow("Max Filter Order:", self.max_order_spin)

        layout.addLayout(form_layout)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_dialog)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def load_target_data(self):
        """Load existing target data if editing."""
        if self.target:
            self.name_edit.setText(self.target.name)

            # Find and select the data type
            for i in range(self.data_type_combo.count()):
                if self.data_type_combo.itemData(i) == self.target.data_type:
                    self.data_type_combo.setCurrentIndex(i)
                    break

            self.max_order_spin.setValue(self.target.max_filter_order)

    def accept_dialog(self):
        """Handle OK button click."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a target name.")
            return

        try:
            data_type = self.data_type_combo.currentData()
            max_order = self.max_order_spin.value()

            target = Target(name=name, data_type=data_type, max_filter_order=max_order)

            if self.target:
                # Update existing target
                print(f"DEBUG: TargetDialog emitting target_updated for: {target.name}")
                self.target_updated.emit(target)
            else:
                # Create new target
                print(f"DEBUG: TargetDialog emitting target_created for: {target.name}")
                self.target_created.emit(target)

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))


class TargetListWidget(QWidget):
    """Widget for displaying and managing targets."""

    target_created = pyqtSignal(Target)
    target_selected = pyqtSignal(Target)
    target_deleted = pyqtSignal(Target)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.targets = []
        self.setup_ui()

    def setup_ui(self):
        """Setup the target list UI."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Targets")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.add_button = QPushButton("Add Target")
        self.add_button.clicked.connect(self.add_target)

        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_button)

        layout.addLayout(header_layout)

        # Target list (simplified - in a real app you'd use QListWidget)
        self.target_label = QLabel("No targets created")
        self.target_label.setStyleSheet("color: palette(mid-text); font-style: italic;")
        layout.addWidget(self.target_label)

        layout.addStretch()

    def add_target(self):
        """Open dialog to add a new target."""
        dialog = TargetDialog(self)
        dialog.target_created.connect(self.on_target_created)
        dialog.exec()

    def on_target_created(self, target: Target):
        """Handle new target creation."""
        print(f"DEBUG: TargetListWidget received target: {target.name}")
        self.targets.append(target)
        print(f"DEBUG: TargetListWidget targets now: {[t.name for t in self.targets]}")
        self.update_display()
        print(f"DEBUG: Emitting target_created signal for: {target.name}")
        self.target_created.emit(target)
        self.target_selected.emit(target)

    def update_display(self):
        """Update the target display."""
        if self.targets:
            target_names = [t.name for t in self.targets]
            self.target_label.setText(f"Targets: {', '.join(target_names)}")
        else:
            self.target_label.setText("No targets created")

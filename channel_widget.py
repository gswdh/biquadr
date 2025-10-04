"""
Channel management widget for creating and managing channels within projects.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore import pyqtSignal, Qt

from models import Channel, Project


class ChannelDialog(QDialog):
    """Dialog for creating or editing channels."""

    channel_created = pyqtSignal(Channel)
    channel_updated = pyqtSignal(Channel)

    def __init__(self, parent=None, channel: Channel = None):
        super().__init__(parent)
        self.channel = channel
        self.setWindowTitle("Edit Channel" if channel else "Create Channel")
        self.setModal(True)
        self.resize(400, 200)

        self.setup_ui()
        self.load_channel_data()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Form layout for channel properties
        form_layout = QFormLayout()

        # Channel name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter channel name...")
        form_layout.addRow("Name:", self.name_edit)

        # Enabled checkbox
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(True)
        form_layout.addRow("Enabled:", self.enabled_check)

        layout.addLayout(form_layout)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_dialog)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def load_channel_data(self):
        """Load existing channel data if editing."""
        if self.channel:
            self.name_edit.setText(self.channel.name)
            self.enabled_check.setChecked(self.channel.enabled)

    def accept_dialog(self):
        """Handle OK button click."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a channel name.")
            return

        try:
            enabled = self.enabled_check.isChecked()

            channel = Channel(name=name, filters=[], enabled=enabled)

            if self.channel:
                # Update existing channel
                self.channel_updated.emit(channel)
            else:
                # Create new channel
                self.channel_created.emit(channel)

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))


class ChannelListWidget(QWidget):
    """Widget for displaying and managing channels in a project."""

    channel_created = pyqtSignal(Channel)
    channel_updated = pyqtSignal(Channel)
    channel_deleted = pyqtSignal(Channel)
    channel_selected = pyqtSignal(Channel)
    project_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.current_channel = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the channel list UI."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Channels")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.add_button = QPushButton("Add Channel")
        self.add_button.clicked.connect(self.add_channel)
        self.add_button.setEnabled(False)

        self.edit_button = QPushButton("Edit Channel")
        self.edit_button.clicked.connect(self.edit_selected_channel)
        self.edit_button.setEnabled(False)

        self.remove_button = QPushButton("Remove Channel")
        self.remove_button.clicked.connect(self.remove_selected_channel)
        self.remove_button.setEnabled(False)

        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_button)
        header_layout.addWidget(self.edit_button)
        header_layout.addWidget(self.remove_button)

        layout.addLayout(header_layout)

        # Channel list
        self.channel_list = QListWidget()
        self.channel_list.setMinimumHeight(100)
        self.channel_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.channel_list.itemDoubleClicked.connect(self.edit_selected_channel)
        layout.addWidget(self.channel_list)

        # Project info
        self.project_info = QLabel("No project selected")
        self.project_info.setStyleSheet("color: palette(mid-text); font-style: italic;")
        layout.addWidget(self.project_info)

    def set_project(self, project: Project):
        """Set the current project."""
        self.project = project
        self.update_display()
        self.add_button.setEnabled(project is not None)

    def update_display(self):
        """Update the channel list display."""
        self.channel_list.clear()

        if self.project:
            self.project_info.setText(
                f"Project: {self.project.name} | Sample Rate: {self.project.sample_rate} Hz"
            )

            for channel in self.project.channels:
                item = QListWidgetItem()
                status = "✓" if channel.enabled else "✗"
                filter_count = len(channel.filters)
                item.setText(f"{status} {channel.name} ({filter_count} filters)")
                item.setData(Qt.ItemDataRole.UserRole, channel)
                self.channel_list.addItem(item)
        else:
            self.project_info.setText("No project selected")

    def add_channel(self):
        """Open dialog to add a new channel."""
        if not self.project:
            return

        dialog = ChannelDialog(self)
        dialog.channel_created.connect(self.on_channel_created)
        dialog.exec()

    def edit_selected_channel(self):
        """Edit the selected channel."""
        current_item = self.channel_list.currentItem()
        if not current_item:
            return

        channel = current_item.data(Qt.ItemDataRole.UserRole)
        if not channel:
            return

        dialog = ChannelDialog(self, channel)
        dialog.channel_updated.connect(self.on_channel_updated)
        dialog.exec()

    def remove_selected_channel(self):
        """Remove the selected channel."""
        current_item = self.channel_list.currentItem()
        if not current_item:
            return

        channel = current_item.data(Qt.ItemDataRole.UserRole)
        if not channel:
            return

        reply = QMessageBox.question(
            self,
            "Remove Channel",
            f"Are you sure you want to remove the channel '{channel.name}' and all its filters?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.project.remove_channel(channel.name)
            self.update_display()
            self.channel_deleted.emit(channel)
            self.project_changed.emit()

    def on_channel_created(self, channel: Channel):
        """Handle new channel creation."""
        if self.project:
            self.project.add_channel(channel)
            self.update_display()
            self.channel_created.emit(channel)
            self.project_changed.emit()

    def on_channel_updated(self, channel: Channel):
        """Handle channel update."""
        # Find and update the existing channel
        for i, existing_channel in enumerate(self.project.channels):
            if existing_channel.name == channel.name:
                # Update the channel properties
                existing_channel.enabled = channel.enabled
                break

        self.update_display()
        self.channel_updated.emit(channel)
        self.project_changed.emit()

    def on_selection_changed(self):
        """Handle channel list selection change."""
        current_item = self.channel_list.currentItem()
        self.edit_button.setEnabled(current_item is not None)
        self.remove_button.setEnabled(current_item is not None)

        if current_item:
            channel = current_item.data(Qt.ItemDataRole.UserRole)
            if channel:
                self.current_channel = channel
                self.channel_selected.emit(channel)
            else:
                self.current_channel = None
        else:
            self.current_channel = None

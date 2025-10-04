"""
Filter management widget for configuring filters in projects.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QCheckBox,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore import pyqtSignal, Qt

from models import Filter, FilterType, Project, Channel


class FilterDialog(QDialog):
    """Dialog for creating or editing filters."""

    filter_created = pyqtSignal(Filter)
    filter_updated = pyqtSignal(Filter)

    def __init__(self, parent=None, filter_obj: Filter = None, max_order: int = 32):
        super().__init__(parent)
        self.filter_obj = filter_obj
        self.max_order = max_order
        self.setWindowTitle("Edit Filter" if filter_obj else "Add Filter")
        self.setModal(True)
        self.resize(400, 250)

        self.setup_ui()
        self.load_filter_data()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Form layout for filter properties
        form_layout = QFormLayout()

        # Filter name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter filter name...")
        form_layout.addRow("Name:", self.name_edit)

        # Filter type
        self.type_combo = QComboBox()
        for filter_type in FilterType:
            self.type_combo.addItem(filter_type.value.title(), filter_type)
        form_layout.addRow("Type:", self.type_combo)

        # Order
        self.order_spin = QSpinBox()
        self.order_spin.setRange(2, self.max_order)
        self.order_spin.setValue(4)
        form_layout.addRow("Order:", self.order_spin)

        # Frequency
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(1.0, 24000.0)
        self.freq_spin.setValue(1000.0)
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.setDecimals(1)
        form_layout.addRow("Frequency:", self.freq_spin)

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

    def load_filter_data(self):
        """Load existing filter data if editing."""
        if self.filter_obj:
            self.name_edit.setText(self.filter_obj.name)

            # Find and select the filter type
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == self.filter_obj.filter_type:
                    self.type_combo.setCurrentIndex(i)
                    break

            self.order_spin.setValue(self.filter_obj.order)
            self.freq_spin.setValue(self.filter_obj.frequency)
            self.enabled_check.setChecked(self.filter_obj.enabled)

    def accept_dialog(self):
        """Handle OK button click."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a filter name.")
            return

        try:
            filter_type = self.type_combo.currentData()
            order = self.order_spin.value()
            frequency = self.freq_spin.value()
            enabled = self.enabled_check.isChecked()

            filter_obj = Filter(
                name=name,
                filter_type=filter_type,
                order=order,
                frequency=frequency,
                enabled=enabled,
            )

            if self.filter_obj:
                # Update existing filter
                self.filter_updated.emit(filter_obj)
            else:
                # Create new filter
                self.filter_created.emit(filter_obj)

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))


class FilterListWidget(QWidget):
    """Widget for displaying and managing filters in a project."""

    filter_created = pyqtSignal(Filter)
    filter_updated = pyqtSignal(Filter)
    filter_selected = pyqtSignal(Filter)
    filter_deleted = pyqtSignal(Filter)
    project_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the filter list UI."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Filters")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.add_button = QPushButton("Add Filter")
        self.add_button.clicked.connect(self.add_filter)
        self.add_button.setEnabled(False)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_selected_filter)
        self.remove_button.setEnabled(False)

        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_button)
        header_layout.addWidget(self.remove_button)

        layout.addLayout(header_layout)

        # Filter list
        self.filter_list = QListWidget()
        self.filter_list.setMinimumHeight(100)
        self.filter_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.filter_list.itemDoubleClicked.connect(self.edit_selected_filter)
        layout.addWidget(self.filter_list)

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
        """Update the filter list display."""
        self.filter_list.clear()

        if self.project:
            self.project_info.setText(
                f"Project: {self.project.name} | Sample Rate: {self.project.sample_rate} Hz"
            )

            # Get all filters from all channels
            all_filters = self.project.get_all_filters()
            for filter_obj in all_filters:
                item = QListWidgetItem()
                status = "✓" if filter_obj.enabled else "✗"
                # Find which channel this filter belongs to
                channel_name = "Unknown"
                for channel in self.project.channels:
                    if filter_obj in channel.filters:
                        channel_name = channel.name
                        break
                item.setText(
                    f"{status} {filter_obj.name} ({filter_obj.filter_type.value}, order {filter_obj.order}, {filter_obj.frequency:.1f} Hz) [{channel_name}]"
                )
                item.setData(Qt.ItemDataRole.UserRole, filter_obj)
                self.filter_list.addItem(item)
        else:
            self.project_info.setText("No project selected")

    def add_filter(self):
        """Open dialog to add a new filter."""
        if not self.project:
            return

        # If project has multiple channels, we need to ask which channel to add to
        if len(self.project.channels) == 0:
            QMessageBox.warning(
                self,
                "No Channels",
                "Please create a channel first before adding filters.",
            )
            return
        elif len(self.project.channels) == 1:
            # Only one channel, add to it directly
            target_channel = self.project.channels[0]
        else:
            # Multiple channels, ask user to select
            from PyQt6.QtWidgets import QInputDialog

            channel_names = [ch.name for ch in self.project.channels]
            channel_name, ok = QInputDialog.getItem(
                self,
                "Select Channel",
                "Add filter to which channel?",
                channel_names,
                0,
                False,
            )
            if not ok:
                return
            target_channel = self.project.get_channel(channel_name)
            if not target_channel:
                return

        dialog = FilterDialog(self, max_order=32)  # Default max order
        dialog.filter_created.connect(
            lambda filter_obj: self.on_filter_created_for_channel(
                filter_obj, target_channel
            )
        )
        dialog.exec()

    def edit_selected_filter(self):
        """Edit the selected filter."""
        current_item = self.filter_list.currentItem()
        if not current_item:
            return

        filter_obj = current_item.data(Qt.ItemDataRole.UserRole)
        if not filter_obj:
            return

        dialog = FilterDialog(self, filter_obj, 32)  # Default max order
        dialog.filter_updated.connect(self.on_filter_updated)
        dialog.exec()

    def remove_selected_filter(self):
        """Remove the selected filter."""
        current_item = self.filter_list.currentItem()
        if not current_item:
            return

        filter_obj = current_item.data(Qt.ItemDataRole.UserRole)
        if not filter_obj:
            return

        reply = QMessageBox.question(
            self,
            "Remove Filter",
            f"Are you sure you want to remove the filter '{filter_obj.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove filter from all channels
            for channel in self.project.channels:
                channel.remove_filter(filter_obj.name)
            self.update_display()
            self.filter_deleted.emit(filter_obj)
            self.project_changed.emit()

    def on_filter_created(self, filter_obj: Filter):
        """Handle new filter creation."""
        if self.project:
            # This method is kept for backward compatibility
            # In the new system, filters should be added to specific channels
            if len(self.project.channels) > 0:
                # Add to first channel as fallback
                self.project.channels[0].add_filter(filter_obj)
            self.update_display()
            self.filter_created.emit(filter_obj)
            self.project_changed.emit()

    def on_filter_created_for_channel(self, filter_obj: Filter, channel: Channel):
        """Handle new filter creation for a specific channel."""
        if self.project and channel:
            channel.add_filter(filter_obj)
            self.update_display()
            self.filter_created.emit(filter_obj)
            self.project_changed.emit()

    def on_filter_updated(self, filter_obj: Filter):
        """Handle filter update."""
        # Find and update the existing filter in all channels
        for channel in self.project.channels:
            for i, existing_filter in enumerate(channel.filters):
                if existing_filter.name == filter_obj.name:
                    # Update the filter properties
                    existing_filter.filter_type = filter_obj.filter_type
                    existing_filter.frequency = filter_obj.frequency
                    existing_filter.order = filter_obj.order
                    existing_filter.enabled = filter_obj.enabled
                    break

        self.update_display()
        self.filter_updated.emit(filter_obj)
        self.project_changed.emit()

    def on_selection_changed(self):
        """Handle filter list selection change."""
        current_item = self.filter_list.currentItem()
        self.remove_button.setEnabled(current_item is not None)

        if current_item:
            filter_obj = current_item.data(Qt.ItemDataRole.UserRole)
            if filter_obj:
                self.filter_selected.emit(filter_obj)

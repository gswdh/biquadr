#!/usr/bin/env python3
"""
Biquadr - A PyQt6 Frequency Response Design Application
A modern desktop application for designing frequency responses and exporting biquad coefficients.
"""

import sys
import json
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTabWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QMenuBar,
    QStatusBar,
    QFrame,
    QGroupBox,
    QFormLayout,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction

from models import Target, Project, DataType, Channel
from frequency_plot import FrequencyResponsePlot
from target_dialog import TargetDialog, TargetListWidget
from filter_widget import FilterListWidget
from channel_widget import ChannelListWidget


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.targets = []
        self.projects = []
        self.current_project = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Biquadr - Frequency Response Designer")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)

        # Set application icon
        self.set_application_icon()

        # Set application style - adaptive to system theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: palette(window);
            }
            QLabel {
                color: palette(window-text);
                font-size: 14px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QPushButton:disabled {
                background-color: palette(mid);
                color: palette(mid-text);
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid palette(mid);
                border-radius: 4px;
                font-size: 14px;
                background-color: palette(base);
                color: palette(text);
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid palette(mid);
                border-radius: 4px;
                font-size: 14px;
                background-color: palette(base);
                color: palette(text);
            }
            QComboBox:focus {
                border-color: #007acc;
            }
            QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 2px solid palette(mid);
                border-radius: 4px;
                font-size: 14px;
                background-color: palette(base);
                color: palette(text);
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #007acc;
            }
            QCheckBox {
                color: palette(window-text);
                font-size: 14px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid palette(mid);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: palette(window-text);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: palette(window-text);
            }
            QTextEdit {
                border: 2px solid palette(mid);
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                background-color: palette(base);
                color: palette(text);
            }
            QListWidget {
                border: 2px solid palette(mid);
                border-radius: 4px;
                background-color: palette(base);
                color: palette(text);
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
        """)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Frequency response plot
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions (25% left, 75% right) - more space for frequency plot
        splitter.setSizes([350, 1050])

        # Create status bar
        self.create_status_bar()

        # Create menu bar
        self.create_menu_bar()

    def create_left_panel(self):
        """Create the left control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Header
        header_label = QLabel("Biquadr Designer")
        header_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #007acc; margin-bottom: 10px;"
        )
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

        # Project management (first - no targets needed)
        project_group = QGroupBox("Project Management")
        project_layout = QVBoxLayout(project_group)

        # Project selection
        project_select_layout = QHBoxLayout()
        self.project_combo = QComboBox()
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        project_select_layout.addWidget(QLabel("Project:"))
        project_select_layout.addWidget(self.project_combo)

        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.clicked.connect(self.create_new_project)
        project_select_layout.addWidget(self.new_project_btn)

        self.edit_project_btn = QPushButton("Edit Project")
        self.edit_project_btn.clicked.connect(self.edit_current_project)
        self.edit_project_btn.setEnabled(False)
        project_select_layout.addWidget(self.edit_project_btn)

        project_layout.addLayout(project_select_layout)

        # Project info
        self.project_info = QLabel("No project selected")
        self.project_info.setStyleSheet("color: palette(mid-text); font-style: italic;")
        project_layout.addWidget(self.project_info)

        layout.addWidget(project_group)

        # Channel management
        channel_group = QGroupBox("Channel Management")
        channel_layout = QVBoxLayout(channel_group)

        self.channel_widget = ChannelListWidget()
        self.channel_widget.project_changed.connect(self.on_project_channels_changed)
        self.channel_widget.channel_created.connect(self.on_channel_created)
        self.channel_widget.channel_updated.connect(self.on_channel_updated)
        self.channel_widget.channel_deleted.connect(self.on_channel_deleted)
        self.channel_widget.channel_selected.connect(self.on_channel_selected)
        channel_layout.addWidget(self.channel_widget)

        layout.addWidget(channel_group)

        # Filter management
        filter_group = QGroupBox("Filter Management")
        filter_layout = QVBoxLayout(filter_group)

        self.filter_widget = FilterListWidget()
        self.filter_widget.project_changed.connect(self.on_project_filters_changed)
        self.filter_widget.filter_created.connect(self.on_filter_changed)
        self.filter_widget.filter_updated.connect(self.on_filter_changed)
        self.filter_widget.filter_deleted.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_widget)

        layout.addWidget(filter_group)

        # Export functionality moved to File menu

        layout.addStretch()
        return panel

    def create_right_panel(self):
        """Create the right panel with frequency response plot."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Plot controls
        plot_controls = QHBoxLayout()

        plot_controls.addWidget(QLabel("Frequency Response"))
        plot_controls.addStretch()

        # Frequency range controls
        plot_controls.addWidget(QLabel("Range:"))
        self.freq_min_spin = QSpinBox()
        self.freq_min_spin.setRange(1, 20000)
        self.freq_min_spin.setValue(20)
        self.freq_min_spin.setSuffix(" Hz")
        plot_controls.addWidget(self.freq_min_spin)

        plot_controls.addWidget(QLabel("to"))
        self.freq_max_spin = QSpinBox()
        self.freq_max_spin.setRange(1, 20000)
        self.freq_max_spin.setValue(20000)
        self.freq_max_spin.setSuffix(" Hz")
        plot_controls.addWidget(self.freq_max_spin)

        self.update_plot_btn = QPushButton("Update Plot")
        self.update_plot_btn.clicked.connect(self.update_frequency_plot)
        plot_controls.addWidget(self.update_plot_btn)

        layout.addLayout(plot_controls)

        # Frequency response plot
        self.frequency_plot = FrequencyResponsePlot()
        self.frequency_plot.setMinimumHeight(500)
        layout.addWidget(self.frequency_plot)

        return panel

    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        self.setStatusBar(self.status_bar)

    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self.create_new_project)
        file_menu.addAction(new_project_action)

        file_menu.addSeparator()

        open_project_action = QAction("Open Project", self)
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)

        save_project_action = QAction("Save Project", self)
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)

        save_as_project_action = QAction("Save Project As...", self)
        save_as_project_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_project_action)

        file_menu.addSeparator()

        # Export submenu
        export_menu = file_menu.addMenu("Export")

        export_all_action = QAction("Export All Channels", self)
        export_all_action.triggered.connect(self.export_all_channels)
        export_menu.addAction(export_all_action)

        export_single_action = QAction("Export Single Channel", self)
        export_single_action.triggered.connect(self.export_single_channel)
        export_menu.addAction(export_single_action)

        copy_action = QAction("Copy to Clipboard", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        export_menu.addAction(copy_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_new_project(self):
        """Create a new project."""
        # Create project dialog
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QFormLayout,
            QLineEdit,
            QSpinBox,
            QDialogButtonBox,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Project")
        dialog.setModal(True)
        dialog.resize(400, 200)

        layout = QVBoxLayout(dialog)

        # Form layout
        form_layout = QFormLayout()

        # Project name
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Enter project name...")
        form_layout.addRow("Project Name:", name_edit)

        # Sample rate
        sample_rate_spin = QSpinBox()
        sample_rate_spin.setRange(1000, 192000)
        sample_rate_spin.setValue(48000)
        sample_rate_spin.setSuffix(" Hz")
        form_layout.addRow("Sample Rate:", sample_rate_spin)

        layout.addLayout(form_layout)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(
                    self, "Invalid Input", "Please enter a project name."
                )
                return

            sample_rate = sample_rate_spin.value()
            project = Project(name=name, channels=[], sample_rate=sample_rate)

            self.projects.append(project)
            self.project_combo.addItem(project.name)
            self.project_combo.setCurrentText(project.name)
            self.current_project = project

            self.update_project_info()
            self.filter_widget.set_project(project)
            # Export functionality moved to File menu
            self.frequency_plot.add_project(project)

            self.status_bar.showMessage(f"Created project: {project.name}")

    def edit_current_project(self):
        """Edit the current project's settings."""
        if not self.current_project:
            return

        # Create project edit dialog
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QFormLayout,
            QLineEdit,
            QSpinBox,
            QDialogButtonBox,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Project")
        dialog.setModal(True)
        dialog.resize(400, 200)

        layout = QVBoxLayout(dialog)

        # Form layout
        form_layout = QFormLayout()

        # Project name
        name_edit = QLineEdit()
        name_edit.setText(self.current_project.name)
        form_layout.addRow("Project Name:", name_edit)

        # Sample rate
        sample_rate_spin = QSpinBox()
        sample_rate_spin.setRange(1000, 192000)
        sample_rate_spin.setValue(int(self.current_project.sample_rate))
        sample_rate_spin.setSuffix(" Hz")
        form_layout.addRow("Sample Rate:", sample_rate_spin)

        layout.addLayout(form_layout)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(
                    self, "Invalid Input", "Please enter a project name."
                )
                return

            sample_rate = sample_rate_spin.value()

            # Update project
            old_name = self.current_project.name
            self.current_project.name = name
            self.current_project.sample_rate = sample_rate

            # Update combo box if name changed
            if old_name != name:
                index = self.project_combo.findText(old_name)
                if index >= 0:
                    self.project_combo.setItemText(index, name)
                    self.project_combo.setCurrentText(name)

            self.update_project_info()
            self.status_bar.showMessage(f"Updated project: {name}")

    def on_project_changed(self, project_name):
        """Handle project selection change."""
        if not project_name:
            self.current_project = None
            self.filter_widget.set_project(None)
            self.frequency_plot.clear_projects()
            self.edit_project_btn.setEnabled(False)
            return

        project = next((p for p in self.projects if p.name == project_name), None)
        if project:
            self.current_project = project
            self.update_project_info()
            self.channel_widget.set_project(project)
            self.filter_widget.set_project(project)
            self.frequency_plot.add_project(project)
            self.edit_project_btn.setEnabled(True)

    def on_target_created(self, target):
        """Handle target creation."""
        print(f"DEBUG: Target created: {target.name}")
        self.targets.append(target)
        print(f"DEBUG: Targets list now: {[t.name for t in self.targets]}")
        self.status_bar.showMessage(f"Created target: {target.name}")

    def on_target_selected(self, target):
        """Handle target selection."""
        self.status_bar.showMessage(f"Selected target: {target.name}")

    def on_project_filters_changed(self):
        """Handle project filter changes."""
        if self.current_project:
            self.frequency_plot.update_plot()
            # Export functionality moved to File menu

    def on_project_channels_changed(self):
        """Handle project channel changes."""
        if self.current_project:
            self.frequency_plot.update_plot()
            # Export functionality moved to File menu
            self.update_project_info()

    def on_channel_created(self, channel: Channel):
        """Handle channel creation."""
        if self.current_project:
            self.frequency_plot.update_plot()
            # Export functionality moved to File menu
            self.update_project_info()

    def on_channel_updated(self, channel: Channel):
        """Handle channel update."""
        if self.current_project:
            self.frequency_plot.update_plot()
            # Export functionality moved to File menu
            self.update_project_info()

    def on_channel_deleted(self, channel: Channel):
        """Handle channel deletion."""
        if self.current_project:
            self.frequency_plot.update_plot()
            # Export functionality moved to File menu
            self.update_project_info()

    def on_channel_selected(self, channel: Channel):
        """Handle channel selection."""
        # Update filter widget to show filters for selected channel
        if self.current_project and channel:
            # Create a temporary project with just this channel for filter management
            temp_project = Project(
                name=f"{self.current_project.name}_{channel.name}",
                channels=[channel],
                sample_rate=self.current_project.sample_rate,
            )
            self.filter_widget.set_project(temp_project)
        else:
            self.filter_widget.set_project(None)

    def on_filter_changed(self, filter_obj):
        """Handle individual filter changes."""
        if self.current_project:
            self.frequency_plot.update_plot()
            # Export functionality moved to File menu

    def update_project_info(self):
        """Update the project information display."""
        if self.current_project:
            total_filters = sum(
                len(channel.filters) for channel in self.current_project.channels
            )
            info = f"Channels: {len(self.current_project.channels)} | "
            info += f"Filters: {total_filters} | "
            info += f"Sample Rate: {self.current_project.sample_rate} Hz"
            self.project_info.setText(info)
        else:
            self.project_info.setText("No project selected")

    def update_frequency_plot(self):
        """Update the frequency response plot."""
        min_freq = self.freq_min_spin.value()
        max_freq = self.freq_max_spin.value()
        self.frequency_plot.set_frequency_range(min_freq, max_freq)

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Biquadr",
            "Biquadr v1.0\n\n"
            "A modern PyQt6 application for designing frequency responses\n"
            "and exporting biquad coefficients.\n\n"
            "Features:\n"
            "• Multiple target systems\n"
            "• Butterworth filter design\n"
            "• Real-time frequency response plotting\n"
            "• Multiple export formats\n\n"
            "Built with Python and PyQt6.",
        )

    def export_all_channels(self):
        """Export all channels to separate files."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please create a project first.")
            return

        from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
        import os

        # Get export format
        format_name, ok = QInputDialog.getItem(
            self,
            "Export Format",
            "Choose export format:",
            ["C Header", "JSON", "CSV", "Python"],
            0,
            False,
        )
        if not ok:
            return

        # Get data type for C/JSON/Python
        data_type = "float32"
        if format_name in ["C Header", "JSON", "Python"]:
            data_type, ok = QInputDialog.getItem(
                self,
                "Data Type",
                "Choose data type:",
                ["float32", "float64", "int16", "int32"],
                0,
                False,
            )
            if not ok:
                return

        # Get directory to save files
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory for Channel Files"
        )
        if not directory:
            return

        # Export each channel
        exported_count = 0
        for channel in self.current_project.channels:
            if channel.enabled:
                # Create temporary project with just this channel
                temp_project = Project(
                    name=f"{self.current_project.name}_{channel.name}",
                    channels=[channel],
                    sample_rate=self.current_project.sample_rate,
                )

                # Get coefficients for this channel
                coefficients = self.get_coefficients_for_project(
                    temp_project, data_type
                )

                # Generate filename
                format_ext = {
                    "C Header": ".h",
                    "JSON": ".json",
                    "CSV": ".csv",
                    "Python": ".py",
                }
                ext = format_ext.get(format_name, ".txt")
                filename = f"{channel.name}{ext}"
                filepath = os.path.join(directory, filename)

                # Generate content
                content = self.generate_export_content(
                    coefficients, format_name, data_type, temp_project
                )

                # Write file
                try:
                    with open(filepath, "w") as f:
                        f.write(content)
                    exported_count += 1
                except Exception as e:
                    QMessageBox.warning(
                        self, "Export Error", f"Failed to export {channel.name}: {e}"
                    )

        QMessageBox.information(
            self,
            "Export Complete",
            f"Exported {exported_count} channels to {directory}",
        )

    def export_single_channel(self):
        """Export a single selected channel."""
        if not self.current_project or not self.current_project.channels:
            QMessageBox.warning(self, "No Channels", "No channels to export.")
            return

        from PyQt6.QtWidgets import QInputDialog, QFileDialog, QMessageBox
        import os

        # Let user select channel
        channel_names = [ch.name for ch in self.current_project.channels if ch.enabled]
        if not channel_names:
            QMessageBox.warning(self, "No Channels", "No enabled channels to export.")
            return

        channel_name, ok = QInputDialog.getItem(
            self, "Select Channel", "Export which channel?", channel_names, 0, False
        )
        if not ok:
            return

        # Find the selected channel
        selected_channel = None
        for channel in self.current_project.channels:
            if channel.name == channel_name:
                selected_channel = channel
                break

        if not selected_channel:
            return

        # Get export format
        format_name, ok = QInputDialog.getItem(
            self,
            "Export Format",
            "Choose export format:",
            ["C Header", "JSON", "CSV", "Python"],
            0,
            False,
        )
        if not ok:
            return

        # Get data type for C/JSON/Python
        data_type = "float32"
        if format_name in ["C Header", "JSON", "Python"]:
            data_type, ok = QInputDialog.getItem(
                self,
                "Data Type",
                "Choose data type:",
                ["float32", "float64", "int16", "int32"],
                0,
                False,
            )
            if not ok:
                return

        # Create temporary project with just this channel
        temp_project = Project(
            name=f"{self.current_project.name}_{channel_name}",
            channels=[selected_channel],
            sample_rate=self.current_project.sample_rate,
        )

        # Get coefficients
        coefficients = self.get_coefficients_for_project(temp_project, data_type)

        # Generate filename
        format_ext = {"C Header": ".h", "JSON": ".json", "CSV": ".csv", "Python": ".py"}
        ext = format_ext.get(format_name, ".txt")
        default_filename = f"{channel_name}{ext}"

        # Get save location
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {channel_name}",
            default_filename,
            f"{format_name} files (*{ext});;All files (*.*)",
        )

        if not filepath:
            return

        # Generate content
        content = self.generate_export_content(
            coefficients, format_name, data_type, temp_project
        )

        # Write file
        try:
            with open(filepath, "w") as f:
                f.write(content)
            QMessageBox.information(
                self, "Export Complete", f"Exported {channel_name} to {filepath}"
            )
        except Exception as e:
            QMessageBox.warning(
                self, "Export Error", f"Failed to export {channel_name}: {e}"
            )

    def copy_to_clipboard(self):
        """Copy coefficients to clipboard."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please create a project first.")
            return

        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        from PyQt6.QtWidgets import QApplication

        # Get export format
        format_name, ok = QInputDialog.getItem(
            self,
            "Copy Format",
            "Choose format to copy:",
            ["C Header", "JSON", "CSV", "Python"],
            0,
            False,
        )
        if not ok:
            return

        # Get data type for C/JSON/Python
        data_type = "float32"
        if format_name in ["C Header", "JSON", "Python"]:
            data_type, ok = QInputDialog.getItem(
                self,
                "Data Type",
                "Choose data type:",
                ["float32", "float64", "int16", "int32"],
                0,
                False,
            )
            if not ok:
                return

        try:
            # Get coefficients for all channels
            coefficients = self.get_coefficients_for_project(
                self.current_project, data_type
            )
            content = self.generate_export_content(
                coefficients, format_name, data_type, self.current_project
            )

            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            QMessageBox.information(
                self, "Copy Successful", "Coefficients copied to clipboard"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Copy Error", f"Failed to copy to clipboard: {str(e)}"
            )

    def get_coefficients_for_project(
        self, project: Project, data_type: str = "float32"
    ):
        """Get coefficients for a specific project."""
        if not project:
            return []

        # Calculate required biquad sections
        filters = project.get_enabled_filters()
        total_order = sum(f.order for f in filters)
        max_sections = (total_order + 1) // 2  # Each biquad is 2nd order

        # Get coefficients
        coefficients = project.calculate_full_biquad_coefficients(
            max_sections, data_type
        )
        return coefficients

    def generate_export_content(
        self, coefficients, format_name: str, data_type: str, project: Project
    ):
        """Generate export content based on format."""
        if format_name == "C Header":
            return self.generate_c_header(coefficients, data_type, project)
        elif format_name == "JSON":
            return self.generate_json(coefficients, data_type, project)
        elif format_name == "CSV":
            return self.generate_csv(coefficients)
        elif format_name == "Python":
            return self.generate_python(coefficients, data_type, project)
        else:
            return str(coefficients)

    def generate_c_header(self, coefficients, data_type: str, project: Project):
        """Generate C header file content."""
        if not coefficients:
            return "// No coefficients to export"

        biquad_count = len(coefficients)

        content = f"// Biquad coefficients for project: {project.name}\n"
        content += f"// Sample rate: {project.sample_rate} Hz\n"
        content += f"// Data type: {data_type}\n"
        content += f"// Number of biquad sections: {biquad_count}\n\n"
        content += f"#define BIQUAD_COUNT {biquad_count}\n\n"

        precision = 15  # Maximum precision

        for i, coeff in enumerate(coefficients):
            content += f"// {coeff.get('filter_name', 'unknown')} ({coeff.get('filter_type', 'unknown')})\n"
            content += f"static const {data_type} biquad_{i}_b0 = {coeff['b0']:.{precision}f};\n"
            content += f"static const {data_type} biquad_{i}_b1 = {coeff['b1']:.{precision}f};\n"
            content += f"static const {data_type} biquad_{i}_b2 = {coeff['b2']:.{precision}f};\n"
            content += f"static const {data_type} biquad_{i}_a1 = {coeff['a1']:.{precision}f};\n"
            content += f"static const {data_type} biquad_{i}_a2 = {coeff['a2']:.{precision}f};\n\n"

        return content

    def generate_json(self, coefficients, data_type: str, project: Project):
        """Generate JSON content."""
        if not coefficients:
            return "{}"

        import json

        data = {
            "project": project.name,
            "sample_rate": project.sample_rate,
            "data_type": data_type,
            "biquad_count": len(coefficients),
            "coefficients": coefficients,
        }

        return json.dumps(data, indent=2)

    def generate_csv(self, coefficients):
        """Generate CSV content."""
        if not coefficients:
            return ""

        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            ["Index", "Filter Name", "Filter Type", "B0", "B1", "B2", "A1", "A2"]
        )

        # Data
        for i, coeff in enumerate(coefficients):
            writer.writerow(
                [
                    i,
                    coeff.get("filter_name", ""),
                    coeff.get("filter_type", ""),
                    f"{coeff['b0']:.15f}",
                    f"{coeff['b1']:.15f}",
                    f"{coeff['b2']:.15f}",
                    f"{coeff['a1']:.15f}",
                    f"{coeff['a2']:.15f}",
                ]
            )

        return output.getvalue()

    def generate_python(self, coefficients, data_type: str, project: Project):
        """Generate Python content."""
        if not coefficients:
            return "# No coefficients to export"

        content = f"# Biquad coefficients for project: {project.name}\n"
        content += f"# Sample rate: {project.sample_rate} Hz\n"
        content += f"# Data type: {data_type}\n"
        content += f"# Biquad count: {len(coefficients)}\n\n"

        content += "import numpy as np\n\n"
        content += "biquad_coefficients = [\n"

        for coeff in coefficients:
            content += f"    {{  # {coeff.get('filter_name', 'unknown')} ({coeff.get('filter_type', 'unknown')})\n"
            content += (
                f"        'filter_name': '{coeff.get('filter_name', 'unknown')}',\n"
            )
            content += (
                f"        'filter_type': '{coeff.get('filter_type', 'unknown')}',\n"
            )
            content += f"        'b0': {coeff['b0']:.15f},\n"
            content += f"        'b1': {coeff['b1']:.15f},\n"
            content += f"        'b2': {coeff['b2']:.15f},\n"
            content += f"        'a1': {coeff['a1']:.15f},\n"
            content += f"        'a2': {coeff['a2']:.15f},\n"
            content += "    },\n"

        content += "]\n"
        return content

    def open_project(self):
        """Open an existing project."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import json
        import os

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "Biquadr Project Files (*.biquadr);;All Files (*.*)",
        )

        if not filepath:
            return

        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            # Create project from loaded data
            project = self.create_project_from_data(data)

            # Add to projects list
            self.projects.append(project)
            self.project_combo.addItem(project.name)
            self.project_combo.setCurrentText(project.name)
            self.current_project = project

            # Update UI
            self.update_project_info()
            self.channel_widget.set_project(project)
            self.filter_widget.set_project(project)
            self.frequency_plot.add_project(project)
            self.edit_project_btn.setEnabled(True)

            # Set current file path for future saves
            self.current_file_path = filepath

            self.status_bar.showMessage(f"Opened project: {project.name}")

        except Exception as e:
            QMessageBox.critical(
                self, "Open Error", f"Failed to open project: {str(e)}"
            )

    def save_project(self):
        """Save the current project."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "No project to save.")
            return

        if hasattr(self, "current_file_path") and self.current_file_path:
            # Save to existing file
            self.save_project_to_file(self.current_file_path)
        else:
            # No existing file, use Save As
            self.save_project_as()

    def save_project_as(self):
        """Save the current project with a new name."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "No project to save.")
            return

        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import os

        # Suggest filename based on project name
        suggested_name = f"{self.current_project.name}.biquadr"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            suggested_name,
            "Biquadr Project Files (*.biquadr);;All Files (*.*)",
        )

        if not filepath:
            return

        # Ensure .biquadr extension
        if not filepath.endswith(".biquadr"):
            filepath += ".biquadr"

        self.save_project_to_file(filepath)
        self.current_file_path = filepath

    def save_project_to_file(self, filepath):
        """Save project to a specific file."""
        try:
            # Convert project to dictionary
            project_data = self.project_to_dict(self.current_project)

            # Save to file
            with open(filepath, "w") as f:
                json.dump(project_data, f, indent=2)

            self.status_bar.showMessage(f"Saved project: {self.current_project.name}")

        except Exception as e:
            QMessageBox.critical(
                self, "Save Error", f"Failed to save project: {str(e)}"
            )

    def project_to_dict(self, project):
        """Convert a project to a dictionary for saving."""
        return {
            "name": project.name,
            "sample_rate": project.sample_rate,
            "channels": [
                {
                    "name": channel.name,
                    "enabled": channel.enabled,
                    "filters": [
                        {
                            "name": filter_obj.name,
                            "filter_type": filter_obj.filter_type.value,
                            "frequency": filter_obj.frequency,
                            "order": filter_obj.order,
                            "enabled": filter_obj.enabled,
                        }
                        for filter_obj in channel.filters
                    ],
                }
                for channel in project.channels
            ],
        }

    def create_project_from_data(self, data):
        """Create a project from loaded data."""
        from models import Filter, FilterType, Channel, Project

        # Create project
        project = Project(
            name=data["name"], channels=[], sample_rate=data.get("sample_rate", 48000.0)
        )

        # Create channels
        for channel_data in data.get("channels", []):
            channel = Channel(
                name=channel_data["name"],
                filters=[],
                enabled=channel_data.get("enabled", True),
            )

            # Create filters for this channel
            for filter_data in channel_data.get("filters", []):
                filter_obj = Filter(
                    name=filter_data["name"],
                    filter_type=FilterType(filter_data["filter_type"]),
                    frequency=filter_data["frequency"],
                    order=filter_data["order"],
                    enabled=filter_data.get("enabled", True),
                )
                channel.filters.append(filter_obj)

            project.channels.append(channel)

        return project

    def set_application_icon(self):
        """Set the application icon."""
        try:
            from PyQt6.QtGui import QIcon
            import os

            # Try to load the icon from the current directory
            icon_paths = ["biquadr_icon.ico", "biquadr_icon.png"]
            icon_set = False

            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
                    print(f"✅ Application icon set: {icon_path}")
                    icon_set = True
                    break

            if not icon_set:
                print("⚠️  Icon file not found, using default icon")
        except Exception as e:
            print(f"⚠️  Could not set application icon: {e}")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Biquadr")
    app.setApplicationVersion("1.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

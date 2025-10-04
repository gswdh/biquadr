"""
Biquad coefficient export functionality.
"""

import json
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QCheckBox,
)
# from PyQt6.QtCore import pyqtSignal

from models import Project


class ExportWidget(QWidget):
    """Widget for exporting biquad coefficients."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_project = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the export widget UI."""
        layout = QVBoxLayout(self)

        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QFormLayout(options_group)

        # Format selection
        self.format_combo = QComboBox()
        self.format_combo.addItems(["C Header", "JSON", "CSV", "Python"])
        options_layout.addRow("Format:", self.format_combo)

        # Include disabled filters
        self.include_disabled = QCheckBox()
        self.include_disabled.setChecked(False)
        options_layout.addRow("Include Disabled:", self.include_disabled)

        # Data type selection
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["float32", "float64", "int16", "int32"])
        self.data_type_combo.setCurrentText("float32")
        options_layout.addRow("Data Type:", self.data_type_combo)

        # Number of biquads (auto-calculated)
        self.biquad_count_label = QLabel("Auto-calculated")
        self.biquad_count_label.setStyleSheet(
            "color: palette(mid-text); font-style: italic;"
        )
        options_layout.addRow("Biquad Count:", self.biquad_count_label)

        # Full biquad export (pad to specified count)
        self.full_biquad_export = QCheckBox()
        self.full_biquad_export.setChecked(True)
        self.full_biquad_export.setToolTip(
            "Export all biquad coefficients up to specified count, padding with identity coefficients"
        )
        options_layout.addRow("Full Biquad Export:", self.full_biquad_export)

        # Precision (always maximum)
        self.precision_label = QLabel("Maximum (15 digits)")
        self.precision_label.setStyleSheet(
            "color: palette(mid-text); font-style: italic;"
        )
        options_layout.addRow("Precision:", self.precision_label)

        layout.addWidget(options_group)

        # Export buttons
        button_layout = QHBoxLayout()

        self.export_button = QPushButton("Export All Channels")
        self.export_button.clicked.connect(self.export_all_channels)
        self.export_button.setEnabled(False)

        self.export_single_button = QPushButton("Export Single Channel")
        self.export_single_button.clicked.connect(self.export_single_channel)
        self.export_single_button.setEnabled(False)

        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.copy_button.setEnabled(False)

        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.export_single_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Preview area
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)

        # Update preview when options change
        self.format_combo.currentTextChanged.connect(self.update_preview)
        self.include_disabled.toggled.connect(self.update_preview)
        self.data_type_combo.currentTextChanged.connect(self.update_preview)
        self.full_biquad_export.toggled.connect(self.update_preview)

    def set_project(self, project: Project):
        """Set the current project for export."""
        self.current_project = project
        self.export_button.setEnabled(project is not None)
        self.export_single_button.setEnabled(
            project is not None and len(project.channels) > 0
        )
        self.copy_button.setEnabled(project is not None)
        self.update_biquad_count()
        self.update_preview()

    def update_biquad_count(self):
        """Update the biquad count display based on current project."""
        if not self.current_project:
            self.biquad_count_label.setText("No project")
            return

        # Calculate required biquad sections
        if self.include_disabled.isChecked():
            filters = self.current_project.filters
        else:
            filters = self.current_project.get_enabled_filters()

        total_order = sum(f.order for f in filters)
        required_sections = (total_order + 1) // 2  # Each biquad is 2nd order

        if required_sections == 0:
            self.biquad_count_label.setText("No filters")
        else:
            self.biquad_count_label.setText(f"{required_sections} sections")

    def update_preview(self):
        """Update the export preview."""
        if not self.current_project:
            self.preview_text.clear()
            return

        try:
            coefficients = self.get_coefficients()
            format_type = self.format_combo.currentText()

            if format_type == "C Header":
                content = self.generate_c_header(coefficients)
            elif format_type == "JSON":
                content = self.generate_json(coefficients)
            elif format_type == "CSV":
                content = self.generate_csv(coefficients)
            elif format_type == "Python":
                content = self.generate_python(coefficients)
            else:
                content = "Unknown format"

            self.preview_text.setPlainText(content)

        except Exception as e:
            self.preview_text.setPlainText(f"Error generating preview: {str(e)}")

    def get_coefficients(self):
        """Get coefficients for the current project."""
        if not self.current_project:
            return []

        if self.full_biquad_export.isChecked():
            # Use full biquad export (padded to calculated count)
            # Calculate required biquad sections
            if self.include_disabled.isChecked():
                filters = self.current_project.filters
            else:
                filters = self.current_project.get_enabled_filters()

            total_order = sum(f.order for f in filters)
            max_sections = (total_order + 1) // 2  # Each biquad is 2nd order
            data_type = self.data_type_combo.currentText()

            if self.include_disabled.isChecked():
                # Include all filters
                original_filters = self.current_project.filters
                try:
                    coefficients = (
                        self.current_project.calculate_full_biquad_coefficients(
                            max_sections, data_type
                        )
                    )
                finally:
                    self.current_project.filters = original_filters
            else:
                # Only enabled filters - temporarily modify project
                original_filters = self.current_project.filters
                self.current_project.filters = (
                    self.current_project.get_enabled_filters()
                )
                try:
                    coefficients = (
                        self.current_project.calculate_full_biquad_coefficients(
                            max_sections, data_type
                        )
                    )
                finally:
                    self.current_project.filters = original_filters
        else:
            # Use regular export (only actual filter coefficients)
            if self.include_disabled.isChecked():
                # Include all filters
                filters = self.current_project.filters
            else:
                # Only enabled filters
                filters = self.current_project.get_enabled_filters()

            # Temporarily modify project to include all filters if needed
            original_filters = self.current_project.filters
            if self.include_disabled.isChecked():
                self.current_project.filters = filters

            try:
                coefficients = self.current_project.calculate_biquad_coefficients()
            finally:
                # Restore original filters
                self.current_project.filters = original_filters

        return coefficients

    def generate_c_header(self, coefficients):
        """Generate C header file content."""
        if not coefficients:
            return "// No coefficients to export"

        data_type = self.data_type_combo.currentText()
        biquad_count = len(coefficients)

        content = f"// Biquad coefficients for project: {self.current_project.name}\n"
        content += f"// Sample rate: {self.current_project.sample_rate} Hz\n"
        content += f"// Data type: {data_type}\n"
        content += f"// Number of biquad sections: {biquad_count}\n\n"
        content += f"#define BIQUAD_COUNT {biquad_count}\n\n"

        precision = 15  # Maximum precision

        for i, coeff in enumerate(coefficients):
            content += f"// {coeff['filter_name']} ({coeff['filter_type']})\n"
            content += f"static const {data_type} biquad_{i}_b0 = {coeff['b0']:.{precision}f};\n"
            content += f"static const {data_type} biquad_{i}_b1 = {coeff['b1']:.{precision}f};\n"
            content += f"static const {data_type} biquad_{i}_b2 = {coeff['b2']:.{precision}f};\n"
            content += f"static const {data_type} biquad_{i}_a1 = {coeff['a1']:.{precision}f};\n"
            content += f"static const {data_type} biquad_{i}_a2 = {coeff['a2']:.{precision}f};\n\n"

        return content

    def generate_json(self, coefficients):
        """Generate JSON content."""
        if not coefficients:
            return "{}"

        data = {
            "project": self.current_project.name,
            "sample_rate": self.current_project.sample_rate,
            "data_type": self.data_type_combo.currentText(),
            "biquad_count": len(coefficients),
            "coefficients": coefficients,
        }

        return json.dumps(data, indent=2)

    def generate_csv(self, coefficients):
        """Generate CSV content."""
        if not coefficients:
            return "No coefficients to export"

        output = []
        output.append("Filter Name,Filter Type,b0,b1,b2,a1,a2")

        for coeff in coefficients:
            output.append(
                f"{coeff['filter_name']},{coeff['filter_type']},"
                f"{coeff['b0']},{coeff['b1']},{coeff['b2']},"
                f"{coeff['a1']},{coeff['a2']}"
            )

        return "\n".join(output)

    def generate_python(self, coefficients):
        """Generate Python content."""
        if not coefficients:
            return "# No coefficients to export"

        content = f"# Biquad coefficients for project: {self.current_project.name}\n"
        content += f"# Sample rate: {self.current_project.sample_rate} Hz\n"
        content += f"# Data type: {self.data_type_combo.currentText()}\n"
        content += f"# Biquad count: {len(coefficients)}\n\n"

        content += "import numpy as np\n\n"
        content += "biquad_coefficients = [\n"

        for coeff in coefficients:
            content += f"    {{  # {coeff['filter_name']} ({coeff['filter_type']})\n"
            content += f"        'filter_name': '{coeff['filter_name']}',\n"
            content += f"        'filter_type': '{coeff['filter_type']}',\n"
            content += f"        'b0': {coeff['b0']:.15f},\n"
            content += f"        'b1': {coeff['b1']:.15f},\n"
            content += f"        'b2': {coeff['b2']:.15f},\n"
            content += f"        'a1': {coeff['a1']:.15f},\n"
            content += f"        'a2': {coeff['a2']:.15f},\n"
            content += "    },\n"

        content += "]\n"

        return content

    def export_to_file(self):
        """Export coefficients to a file."""
        if not self.current_project:
            return

        format_type = self.format_combo.currentText()

        # Determine file extension
        extensions = {
            "C Header": "*.h",
            "JSON": "*.json",
            "CSV": "*.csv",
            "Python": "*.py",
        }

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Biquad Coefficients",
            f"{self.current_project.name}_coefficients",
            f"{format_type} Files ({extensions[format_type]})",
        )

        if filename:
            try:
                coefficients = self.get_coefficients()
                format_type = self.format_combo.currentText()

                if format_type == "C Header":
                    content = self.generate_c_header(coefficients)
                elif format_type == "JSON":
                    content = self.generate_json(coefficients)
                elif format_type == "CSV":
                    content = self.generate_csv(coefficients)
                elif format_type == "Python":
                    content = self.generate_python(coefficients)

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)

                QMessageBox.information(
                    self, "Export Successful", f"Coefficients exported to {filename}"
                )

            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export coefficients: {str(e)}"
                )

    def copy_to_clipboard(self):
        """Copy coefficients to clipboard."""
        if not self.current_project:
            return

        try:
            from PyQt6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            clipboard.setText(self.preview_text.toPlainText())
            QMessageBox.information(
                self, "Copy Successful", "Coefficients copied to clipboard"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Copy Error", f"Failed to copy to clipboard: {str(e)}"
            )

    def export_all_channels(self):
        """Export all channels to separate files."""
        if not self.current_project:
            return

        from PyQt6.QtWidgets import QFileDialog
        import os

        # Get directory to save files
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory for Channel Files"
        )
        if not directory:
            return

        # Export each channel
        for channel in self.current_project.channels:
            if channel.enabled:
                # Create temporary project with just this channel
                temp_project = Project(
                    name=f"{self.current_project.name}_{channel.name}",
                    channels=[channel],
                    sample_rate=self.current_project.sample_rate,
                )

                # Get coefficients for this channel
                coefficients = self.get_coefficients_for_project(temp_project)

                # Generate filename
                format_ext = {
                    "C Header": ".h",
                    "JSON": ".json",
                    "CSV": ".csv",
                    "Python": ".py",
                }
                format_name = self.format_combo.currentText()
                ext = format_ext.get(format_name, ".txt")
                filename = f"{channel.name}{ext}"
                filepath = os.path.join(directory, filename)

                # Generate content
                if format_name == "C Header":
                    content = self.generate_c_header(coefficients)
                elif format_name == "JSON":
                    content = self.generate_json(coefficients)
                elif format_name == "CSV":
                    content = self.generate_csv(coefficients)
                elif format_name == "Python":
                    content = self.generate_python(coefficients)
                else:
                    content = str(coefficients)

                # Write file
                try:
                    with open(filepath, "w") as f:
                        f.write(content)
                    print(f"Exported {channel.name} to {filepath}")
                except Exception as e:
                    print(f"Error exporting {channel.name}: {e}")

    def export_single_channel(self):
        """Export a single selected channel."""
        if not self.current_project or not self.current_project.channels:
            return

        from PyQt6.QtWidgets import QInputDialog

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

        # Create temporary project with just this channel
        temp_project = Project(
            name=f"{self.current_project.name}_{channel_name}",
            channels=[selected_channel],
            sample_rate=self.current_project.sample_rate,
        )

        # Get coefficients
        coefficients = self.get_coefficients_for_project(temp_project)

        # Generate filename
        format_ext = {"C Header": ".h", "JSON": ".json", "CSV": ".csv", "Python": ".py"}
        format_name = self.format_combo.currentText()
        ext = format_ext.get(format_name, ".txt")
        default_filename = f"{channel_name}{ext}"

        # Get save location
        from PyQt6.QtWidgets import QFileDialog

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {channel_name}",
            default_filename,
            f"{format_name} files (*{ext});;All files (*.*)",
        )

        if not filepath:
            return

        # Generate content
        if format_name == "C Header":
            content = self.generate_c_header(coefficients)
        elif format_name == "JSON":
            content = self.generate_json(coefficients)
        elif format_name == "CSV":
            content = self.generate_csv(coefficients)
        elif format_name == "Python":
            content = self.generate_python(coefficients)
        else:
            content = str(coefficients)

        # Write file
        try:
            with open(filepath, "w") as f:
                f.write(content)
            print(f"Exported {channel_name} to {filepath}")
        except Exception as e:
            print(f"Error exporting {channel_name}: {e}")

    def get_coefficients_for_project(self, project: Project):
        """Get coefficients for a specific project (used for channel export)."""
        if not project:
            return []

        if self.full_biquad_export.isChecked():
            # Use full biquad export (padded to calculated count)
            # Calculate required biquad sections
            if self.include_disabled.isChecked():
                filters = project.get_all_filters()
            else:
                filters = project.get_enabled_filters()

            total_order = sum(f.order for f in filters)
            max_sections = (total_order + 1) // 2  # Each biquad is 2nd order
            data_type = self.data_type_combo.currentText()

            if self.include_disabled.isChecked():
                # Include all filters
                original_filters = project.get_all_filters()
                try:
                    # Temporarily set all filters to enabled for calculation
                    for f in original_filters:
                        f.enabled = True
                    coefficients = project.calculate_full_biquad_coefficients(
                        max_sections, data_type
                    )
                    # Restore original enabled state
                    for f in original_filters:
                        f.enabled = f.enabled
                except Exception as e:
                    print(f"Error calculating coefficients: {e}")
                    return []
            else:
                coefficients = project.calculate_full_biquad_coefficients(
                    max_sections, data_type
                )
        else:
            # Use regular export
            coefficients = project.calculate_biquad_coefficients()
            # Convert to target data type
            data_type = self.data_type_combo.currentText()
            dtype = np.dtype(data_type)
            for coeff in coefficients:
                coeff["b0"] = dtype.type(coeff["b0"])
                coeff["b1"] = dtype.type(coeff["b1"])
                coeff["b2"] = dtype.type(coeff["b2"])
                coeff["a1"] = dtype.type(coeff["a1"])
                coeff["a2"] = dtype.type(coeff["a2"])

        return coefficients

"""
Frequency response plotting widget using matplotlib.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from models import Project


class FrequencyResponsePlot(QWidget):
    """Widget for displaying frequency response plots."""

    # Signal emitted when user clicks on the plot
    plot_clicked = pyqtSignal(float, float)  # frequency, magnitude

    def __init__(self, parent=None):
        super().__init__(parent)
        self.projects = []
        self.frequency_range = (20, 20000)  # Hz
        self.magnitude_range = (-60, 10)  # dB

        self.setup_ui()

    def setup_ui(self):
        """Setup the plotting widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        # Create subplots
        self.ax_mag = self.figure.add_subplot(211)
        self.ax_phase = self.figure.add_subplot(212)

        # Setup plots
        self.setup_plots()

        # Connect mouse events
        self.canvas.mpl_connect("button_press_event", self.on_plot_clicked)

        layout.addWidget(self.canvas)

    def setup_plots(self):
        """Setup the initial plot appearance."""
        # Magnitude plot
        self.ax_mag.set_xscale("log")
        self.ax_mag.set_xlabel("Frequency (Hz)")
        self.ax_mag.set_ylabel("Magnitude (dB)")
        self.ax_mag.set_title("Frequency Response")
        self.ax_mag.grid(True, alpha=0.3)
        self.ax_mag.set_xlim(self.frequency_range)
        self.ax_mag.set_ylim(self.magnitude_range)

        # Phase plot
        self.ax_phase.set_xscale("log")
        self.ax_phase.set_xlabel("Frequency (Hz)")
        self.ax_phase.set_ylabel("Phase (degrees)")
        self.ax_phase.set_title("Phase Response")
        self.ax_phase.grid(True, alpha=0.3)
        self.ax_phase.set_xlim(self.frequency_range)

        # Adjust layout
        self.figure.tight_layout()

    def add_project(self, project: Project):
        """Add a project to the plot."""
        if project not in self.projects:
            self.projects.append(project)
            self.update_plot()

    def remove_project(self, project: Project):
        """Remove a project from the plot."""
        if project in self.projects:
            self.projects.remove(project)
            self.update_plot()

    def clear_projects(self):
        """Clear all projects from the plot."""
        self.projects.clear()
        self.update_plot()

    def update_plot(self):
        """Update the frequency response plot."""
        # Clear existing plots
        self.ax_mag.clear()
        self.ax_phase.clear()

        # Setup plots again
        self.setup_plots()

        if not self.projects:
            self.canvas.draw()
            return

        # Generate frequency points
        frequencies = np.logspace(
            np.log10(self.frequency_range[0]), np.log10(self.frequency_range[1]), 1000
        )

        # Plot each project
        colors = plt.cm.get_cmap("tab10")(np.linspace(0, 1, len(self.projects)))

        color_index = 0
        for project in self.projects:
            try:
                print(
                    f"DEBUG: Plotting project {project.name} with {len(project.channels)} channels"
                )

                # Plot each channel separately
                for channel in project.channels:
                    if channel.enabled:
                        magnitude_db, phase_degrees = (
                            channel.calculate_frequency_response(
                                frequencies, project.sample_rate
                            )
                        )
                        print(
                            f"DEBUG: Channel {channel.name} - Magnitude range: {np.min(magnitude_db):.2f} to {np.max(magnitude_db):.2f} dB"
                        )

                        # Plot magnitude
                        self.ax_mag.semilogx(
                            frequencies,
                            magnitude_db,
                            color=colors[color_index % len(colors)],
                            linewidth=2,
                            label=f"{project.name} - {channel.name}",
                        )

                        # Plot phase
                        self.ax_phase.semilogx(
                            frequencies,
                            phase_degrees,
                            color=colors[color_index % len(colors)],
                            linewidth=2,
                            alpha=0.7,
                        )

                        color_index += 1

            except Exception as e:
                print(f"Error plotting project {project.name}: {e}")
                continue

        # Add legend to magnitude plot
        if self.projects:
            self.ax_mag.legend(loc="best")

        # Update plot
        self.canvas.draw()

    def on_plot_clicked(self, event):
        """Handle mouse clicks on the plot."""
        if (
            event.inaxes == self.ax_mag and event.button == 1
        ):  # Left click on magnitude plot
            if event.xdata is not None and event.ydata is not None:
                self.plot_clicked.emit(event.xdata, event.ydata)

    def set_frequency_range(self, min_freq: float, max_freq: float):
        """Set the frequency range for the plot."""
        self.frequency_range = (min_freq, max_freq)
        self.update_plot()

    def set_magnitude_range(self, min_db: float, max_db: float):
        """Set the magnitude range for the plot."""
        self.magnitude_range = (min_db, max_db)
        self.update_plot()

    def export_plot(self, filename: str):
        """Export the current plot to a file."""
        self.figure.savefig(filename, dpi=300, bbox_inches="tight")

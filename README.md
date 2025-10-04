# Biquadr - Frequency Response Designer

A modern PyQt6 desktop application for designing frequency responses and exporting biquad coefficients.

## Features

- **Multiple Target Systems**: Create and manage different target systems with configurable data types and maximum filter orders
- **Butterworth Filter Design**: Design highpass and lowpass Butterworth filters with orders from 2 to 32
- **Real-time Frequency Response Plotting**: Visualize frequency responses with logarithmic axes
- **Multiple Export Formats**: Export biquad coefficients in C header, JSON, CSV, and Python formats
- **Project Management**: Organize filters into projects with specific targets

## Installation

This project uses `uv` for dependency management. Make sure you have `uv` installed, then:

```bash
# Install dependencies
uv sync

# Run the application
uv run main.py
```

## Usage

### 1. Create a Target

1. Click "Add Target" in the Target Management section
2. Enter a name for your target system
3. Select the data type (float32, float64, int16, int32)
4. Set the maximum filter order (2-32)
5. Click OK

### 2. Create a Project

1. Click "New Project" in the Project Management section
2. Enter a project name
3. Select a target system
4. Click OK

### 3. Add Filters

1. With a project selected, click "Add Filter" in the Filter Management section
2. Configure the filter:
   - **Name**: Descriptive name for the filter
   - **Type**: Highpass or Lowpass
   - **Order**: Filter order (2 to target's maximum)
   - **Frequency**: Cutoff frequency in Hz
   - **Enabled**: Whether the filter is active
3. Click OK

### 4. View Frequency Response

The frequency response plot automatically updates when you add or modify filters. You can:

- Adjust the frequency range using the controls above the plot
- Click "Update Plot" to refresh the display
- View both magnitude and phase responses

### 5. Export Coefficients

1. Select your project
2. In the Export section, choose your preferred format:
   - **C Header**: For embedded C/C++ applications
   - **JSON**: For web applications or configuration files
   - **CSV**: For spreadsheet analysis
   - **Python**: For Python applications
3. Adjust precision and other options as needed
4. Click "Export to File" or "Copy to Clipboard"

## Project Structure

```
biquadr/
├── main.py              # Main application
├── models.py            # Data models (Target, Filter, Project)
├── frequency_plot.py    # Matplotlib plotting widget
├── target_dialog.py     # Target creation/editing dialogs
├── filter_widget.py     # Filter management widget
├── export_widget.py     # Coefficient export functionality
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

## Dependencies

- PyQt6: GUI framework
- matplotlib: Plotting and visualization
- numpy: Numerical computations
- scipy: Signal processing (Butterworth filter design)

## License

This project is open source. Feel free to use and modify as needed.

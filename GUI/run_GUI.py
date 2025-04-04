import sys
import time
import json
import os
import matplotlib
import subprocess
import pickle

matplotlib.use('QtAgg')

from io import StringIO
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


from PySide6 import QtCore as qtc
from PySide6.QtCore import QThread, Signal
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as gtg

#import pyqtgraph as pg

from py_files.ui_VIPCALs import Ui_VIPCALs
from py_files.ui_main_window import Ui_main_window
from py_files.ui_manual_window import Ui_manual_window
from py_files.ui_help_window import Ui_help_window
from py_files.ui_json_window import Ui_JSON_window
from py_files.ui_run_window import Ui_run_window
from py_files.ui_plots_window import Ui_plots_window

class OutputRedirector(StringIO):
    """Custom stream to redirect stdout to QTextEdit."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, text):
        """Override write method to append text to QTextEdit."""
        self.text_widget.append(text.strip())  # Append text to QTextEdit

    def flush(self):
        """Flush method (needed for sys.stdout compatibility)."""
        pass
        
class PipelineWorker(QThread):
    output_received = Signal(str)  # Signal to send stdout
    error_received = Signal(str)   # Signal to send stderr
    process_finished = Signal()

    def run(self):
        """Runs mock_pipeline.py in a subprocess and streams output."""
        process = subprocess.Popen(
            #["conda", "run", "--no-capture-output" ,"-n", "vipcals", 
            # "ParselTongue", "../vipcals/__main__.py",
            # "temp.json"],
            ["conda", "run", "--no-capture-output" ,"-n", "vipcals", 
             "ParselTongue", "mock_pipeline.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffering for real-time output
            universal_newlines=True
        )

        # Read stdout line by line
        for line in iter(process.stdout.readline, ''):
            self.output_received.emit(line.strip())  # Emit each line immediately
           

        # Read and emit errors if any
        for err in iter(process.stderr.readline, ''):
            self.error_received.emit("\n[ERROR]: " + err.strip())

        process.wait()  # Ensure process finishes

        self.process_finished.emit()  # Notify when done

        
# Main Window
class MainWindow(qtw.QMainWindow, Ui_VIPCALs):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window with Multiple Widgets")
        self.setupUi(self)

        # Create a QStackedWidget to manage different pages
        self.stack = qtw.QStackedWidget()
        self.setCentralWidget(self.stack)

        # Create different widgets
        self.main_page = MainPage(self)
        self.json_page = JSONWindow(self)
        self.help_page = HelpWindow(self)
        self.manual_page = ManualWindow(self)
        self.run_page = RunWindow(self)
        self.plots_page = PlotsWindow(self)

        # Add widgets to the stacked widget
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.json_page)
        self.stack.addWidget(self.help_page)
        self.stack.addWidget(self.manual_page)
        self.stack.addWidget(self.run_page)
        self.stack.addWidget(self.plots_page)

        # Show the main page by default
        self.stack.setCurrentWidget(self.main_page)
        
        
class MainPage(qtw.QWidget, Ui_main_window):  
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)
        
        self.JSON_input_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.json_page))
        self.help_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.help_page))
        self.man_input_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.manual_page))
        self.exit_btn.clicked.connect(self.main_window.close)

        
class ManualWindow(qtw.QWidget, Ui_manual_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)  

        self.fields = {
            "disk": self.disk_line,
            "paths": self.filepath_line,
            "output_directory": self.output_line,
            "targets": self.target_line,
            "userno": self.userno_line,
            "calib": self.calsour_line,
            "flag_edge": self.edgeflag_line,
            "phase_ref": self.phasref_line,
            "refant": self.refant_line,
            "shifts": self.shift_line,
            "load_all": self.loadall_line
        }
               
        self.loadall_line.addItems(['False', 'True'])
        
        self.selectfile_btn.clicked.connect(self.get_input_file)
        self.more_options_btn.clicked.connect(self.toggle_moreoptions)
        
        self.continue_button.clicked.connect(self.retrieve_inputs)
        self.continue_button.clicked.connect(self.start_pipeline) 
        
        self.return_button.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.main_page)) 
        
    def start_pipeline(self):
        """Switch to RunWindow and execute pipeline."""
        self.main_window.stack.setCurrentWidget(self.main_window.run_page)  # Show RunWindow
        self.main_window.run_page.RunPipeline()  # Call the function when the button is clicked
         
    def toggle_moreoptions(self):
        self.more_options.setVisible(not self.more_options.isVisible())

    def get_input_file(self):
        response = qtw.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select a file",
            #directory=os.getcwd(),
            filter = 'FITS file (*.fits *.uvfits *.idifits)'
        )
        self.filepath_line.setText(str(response[0]))
    def retrieve_inputs(self):
        inputs = {}
        for label, line_edit in self.fields.items():
            print(label, line_edit)
            if label == "load_all":
                inputs[label] = self.loadall_line.currentText()
            elif label == "paths":
                inputs[label] = [line_edit.text()]
            elif label == "targets":
                inputs[label] = [line_edit.text()]
            else:
                inputs[label] = line_edit.text()

        # Save inputs as JSON
        json_inputs = json.dumps(inputs)
        with open('./temp.json', 'w') as f:
            f.write(json_inputs)

        print(f"Inputs: {inputs}")
    
    def showEvent(self, event):
        for label, line_edit in list(self.fields.items()):
            if label != self.loadall_lbl: 
                line_edit.clear() 
        self.loadall_line.setCurrentIndex(0)
        self.more_options.setVisible(False)
        super().showEvent(event)
        
        
class JSONWindow(qtw.QWidget, Ui_JSON_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)
        
        self.return_button.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.main_page))        
        
        
class HelpWindow(qtw.QWidget, Ui_help_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)
        
        self.return_button.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.main_page)) 

class RunWindow(qtw.QWidget, Ui_run_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)

        self.text_output.setReadOnly(True)
        sys.stdout = OutputRedirector(self.text_output)  # Redirect stdout

        self.plots_btn.setVisible(False)
        self.return_btn.setVisible(False)

        self.plots_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.plots_page))
        self.return_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.main_page))

        self.worker = None  # Placeholder for pipeline worker

    def RunPipeline(self):
        """Starts the subprocess in a separate thread for live output."""
        self.text_output.clear()  # Clear previous logs

        # Create worker thread
        self.worker = PipelineWorker()
        self.worker.output_received.connect(self.text_output.append)  # Live update
        self.worker.error_received.connect(self.text_output.append)   # Live error update
        self.worker.process_finished.connect(self.show_buttons)  # Show buttons when finished

        self.worker.start()  # Start pipeline process

    def show_buttons(self):
        """Show plots and return buttons after process finishes."""
        self.plots_btn.setVisible(True)
        self.return_btn.setVisible(True)


class PlotsWindow(qtw.QWidget, Ui_plots_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)

        self.canvas_window = []

        self.vplot_btn.clicked.connect(self.openVplotCanvas)
        self.possm_uncal_btn.clicked.connect(self.openPossmCanvas)
        self.possm_cal_btn.clicked.connect(self.openRadplotCanvas)
        self.uvplot_btn.clicked.connect(self.openUvplotCanvas)
        self.return_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.run_page)) 

    def openVplotCanvas(self):
        canvas = VplotWindow()
        self.canvas_window.append(canvas)
        canvas.show()
    def openPossmCanvas(self):
        canvas = PossmWindow()
        self.canvas_window.append(canvas)
        canvas.show()
    def openRadplotCanvas(self):
        canvas = RadplotWindow()
        self.canvas_window.append(canvas)
        canvas.show()
    def openUvplotCanvas(self):
        canvas = UvplotWindow()
        self.canvas_window.append(canvas)
        canvas.show()
        
class VplotWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VPLOT")

        # Create a central widget and layout
        central_widget = qtw.QWidget()
        layout = qtw.QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Create the matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Create a toolbar for navigation
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Add widgets to layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Plot some data
        self.plot_data()

    def plot_data(self):
        # Load the pickled figure
        loaded_figure = pickle.load(open('./tmp/1_2.vplt.pickle', 'rb'))
        original_axes = loaded_figure.get_axes()

        # Create new figure and canvas
        new_figure = Figure()
        new_canvas = FigureCanvas(new_figure)
        new_toolbar = NavigationToolbar(new_canvas, self)

        # Recreate subplots and copy content
        new_axes = []
        for i, ax in enumerate(original_axes):
            new_ax = new_figure.add_subplot(2, 1, i + 1, sharex=new_axes[0] if new_axes else None)

            # Copy lines
            for line in ax.lines:
                new_ax.plot(line.get_xdata(), line.get_ydata(), label=line.get_label(), color=line.get_color())

            # Copy scatter plots
            for artist in ax.collections:
                if isinstance(artist, PathCollection):
                    offsets = artist.get_offsets()
                    colors = artist.get_facecolor()
                    new_ax.scatter(offsets[:, 0], offsets[:, 1], c=colors, s=artist.get_sizes(), marker='.')

            # Copy labels
            new_ax.set_title(ax.get_title())
            new_ax.set_xlabel(ax.get_xlabel())
            new_ax.set_ylabel(ax.get_ylabel())
            new_axes.append(new_ax)

        # Remove old widgets
        layout = self.centralWidget().layout()
        layout.removeWidget(self.canvas)
        layout.removeWidget(self.toolbar)
        self.canvas.setParent(None)
        self.toolbar.setParent(None)

        # Add new canvas and toolbar
        self.figure = new_figure
        self.canvas = new_canvas
        self.toolbar = new_toolbar

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.canvas.draw()



class PossmWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PySide6 + Matplotlib Example")

        # Create a central widget and layout
        central_widget = qtw.QWidget()
        layout = qtw.QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Create the matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Create a toolbar for navigation
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Add widgets to layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Plot some data
        self.plot_data()

    def plot_data(self):
        ax = self.figure.add_subplot(111)
        ax.plot([0, 1, 2, 3, 4], [10, 1, 20, 3, 40], marker="o", linestyle="-")
        ax.set_title("Matplotlib Plot")
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")

        self.canvas.draw()  # Update the canvas
    
class RadplotWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PySide6 + Matplotlib Example")

        # Create a central widget and layout
        central_widget = qtw.QWidget()
        layout = qtw.QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Create the matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Create a toolbar for navigation
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Add widgets to layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Plot some data
        self.plot_data()

    def plot_data(self):
        # Load the pickled figure
        loaded_figure = pickle.load(open('./tmp/J1329+3154.radplot.pickle', 'rb'))
        original_axes = loaded_figure.get_axes()

        # Create new figure and canvas
        new_figure = Figure()
        new_canvas = FigureCanvas(new_figure)
        new_toolbar = NavigationToolbar(new_canvas, self)

        # Recreate subplots and copy content
        new_axes = []
        for i, ax in enumerate(original_axes):
            new_ax = new_figure.add_subplot(2, 1, i + 1, sharex=new_axes[0] if new_axes else None)

            # Copy lines
            for line in ax.lines:
                new_ax.plot(line.get_xdata(), line.get_ydata(), label=line.get_label(), color=line.get_color())

            # Copy scatter plots
            for artist in ax.collections:
                if isinstance(artist, PathCollection):
                    offsets = artist.get_offsets()
                    colors = artist.get_facecolor()
                    new_ax.scatter(offsets[:, 0], offsets[:, 1], c=colors, s=artist.get_sizes(), marker='.')

            # Copy labels
            new_ax.set_title(ax.get_title())
            new_ax.set_xlabel(ax.get_xlabel())
            new_ax.set_ylabel(ax.get_ylabel())
            new_axes.append(new_ax)

        # Remove old widgets
        layout = self.centralWidget().layout()
        layout.removeWidget(self.canvas)
        layout.removeWidget(self.toolbar)
        self.canvas.setParent(None)
        self.toolbar.setParent(None)

        # Add new canvas and toolbar
        self.figure = new_figure
        self.canvas = new_canvas
        self.toolbar = new_toolbar

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.canvas.draw()

class UvplotWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PySide6 + Matplotlib Example")

        # Create a central widget and layout
        central_widget = qtw.QWidget()
        layout = qtw.QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Create the matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Create a toolbar for navigation
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Add widgets to layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Plot some data
        self.plot_data()

    def plot_data(self):
        # Load the pickled figure
        loaded_figure = pickle.load(open('./tmp/J1329+3154.uvplt.pickle', 'rb'))
        original_axes = loaded_figure.get_axes()

        # Create new figure and canvas
        new_figure = Figure()
        new_canvas = FigureCanvas(new_figure)
        new_toolbar = NavigationToolbar(new_canvas, self)

        # Recreate subplots and copy content
        new_axes = []
        for i, ax in enumerate(original_axes):
            new_ax = new_figure.add_subplot(2, 1, i + 1, sharex=new_axes[0] if new_axes else None)

            # Copy lines
            for line in ax.lines:
                new_ax.plot(line.get_xdata(), line.get_ydata(), label=line.get_label(), color=line.get_color())

            # Copy scatter plots
            for artist in ax.collections:
                if isinstance(artist, PathCollection):
                    offsets = artist.get_offsets()
                    colors = artist.get_facecolor()
                    new_ax.scatter(offsets[:, 0], offsets[:, 1], c=colors, s=artist.get_sizes(), marker='.')

            # Copy labels
            new_ax.set_title(ax.get_title())
            new_ax.set_xlabel(ax.get_xlabel())
            new_ax.set_ylabel(ax.get_ylabel())
            new_ax.set_aspect('equal')
            new_axes.append(new_ax)

        # Remove old widgets
        layout = self.centralWidget().layout()
        layout.removeWidget(self.canvas)
        layout.removeWidget(self.toolbar)
        self.canvas.setParent(None)
        self.toolbar.setParent(None)

        # Add new canvas and toolbar
        self.figure = new_figure
        self.canvas = new_canvas
        self.toolbar = new_toolbar

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.canvas.draw()
  
# Run the Application
if __name__ == "__main__":
    if not qtw.QApplication.instance():
        app = qtw.QApplication(sys.argv)
    else:
        app = qtw.QApplication.instance()
        
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

import sys
import time
import json
import os
import glob
import re
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
plt.style.use('dark_background')



from PySide6 import QtCore as qtc
from PySide6.QtCore import QThread, Signal
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as gtg

import numpy as np

from functools import partial

from py_files.ui_VIPCALs import Ui_VIPCALs
from py_files.ui_main_window import Ui_main_window
from py_files.ui_manual_window import Ui_manual_window
from py_files.ui_help_window import Ui_help_window
from py_files.ui_json_window import Ui_JSON_window
from py_files.ui_run_window import Ui_run_window
from py_files.ui_plots_window import Ui_plots_window

from io import StringIO
from PySide6.QtGui import QTextCursor



class OutputRedirector(StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, text):

        if text == "":
            return
        
        # Get color
        color = self.get_color_static(text)

        # Create format
        fmt = gtg.QTextCharFormat()
        fmt.setForeground(gtg.QColor(color))

        cursor = self.text_widget.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.setCharFormat(fmt)

        # Insert plain text with preserved spacing and newlines
        cursor.insertText(text)

        # Ensure scroll to bottom
        self.text_widget.setTextCursor(cursor)
        self.text_widget.ensureCursorVisible()

    def flush(self):
        pass
    
    @staticmethod
    def get_color_static(text):
        lower = text.lower()
        if "error" in lower:
            return "red"
        elif "warning" in lower:
            return "orange"
        elif "created" in lower:
            return "green"
        elif "____info" in lower:
            return "lightblue"
        return "white"
        
class PipelineWorker(QThread):
    output_received = Signal(str)  # Signal to send stdout
    error_received = Signal(str)   # Signal to send stderr
    process_finished = Signal()

    def run(self):
        """Runs mock_pipeline.py in a subprocess and streams output."""
        process = subprocess.Popen(
            [#"conda", "run", "--no-capture-output" ,"-n", "pyside62", 
             "ParselTongue", "../vipcals/__main__docker.py",
             "../tmp/temp.json"],
            #["conda", "run", "--no-capture-output" ,"-n", "vipcals", 
            # "ParselTongue", "mock_pipeline.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffering for real-time output
            universal_newlines=True
        )

        # Read stdout line by line
        for line in iter(process.stdout.readline, ''):
            self.output_received.emit(line)  # Emit each line immediately
           

        # Read and emit errors if any
        for err in iter(process.stderr.readline, ''):
            self.error_received.emit("\n[ERROR]: " + err)

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
        # self.plots_page = PlotsWindow(self)

        # Add widgets to the stacked widget
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.json_page)
        self.stack.addWidget(self.help_page)
        self.stack.addWidget(self.manual_page)
        self.stack.addWidget(self.run_page)
        # self.stack.addWidget(self.plots_page)

        # Show the main page by default
        self.stack.setCurrentWidget(self.main_page)
        
        
class MainPage(qtw.QWidget, Ui_main_window):  
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)
        
        self.JSON_input_btn.clicked.connect(self.open_json_page)
        #self.help_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.help_page))
        self.man_input_btn.clicked.connect(self.open_manual_page)
        #self.exit_btn.clicked.connect(self.main_window.close)

    def open_manual_page(self):
        self.main_window.manual_page.should_reset_fields = True
        self.main_window.stack.setCurrentWidget(self.main_window.manual_page)

    def open_json_page(self):
        self.main_window.json_page.filepath_line.clear()
        self.main_window.stack.setCurrentWidget(self.main_window.json_page)

        
class ManualWindow(qtw.QWidget, Ui_manual_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)  

        self.should_reset_fields = False  # <- Flag for reset control

        self.fields = {
            #"disk": self.disk_line,
            "paths": self.filepath_line,
            "output_directory": self.output_line,
            "targets": self.target_line,
            #"userno": self.userno_line,
            "calib": self.calsour_line,
            "flag_edge": self.edgeflag_line,
            "phase_ref": self.phasref_line,
            "refant": self.refant_line,
            "shifts": self.shift_line,
            "load_all": self.loadall_line
        }
               
        self.loadall_line.addItems(['False', 'True'])
        
        self.selectfile_btn.clicked.connect(self.get_input_file)
        self.selectdir_btn.clicked.connect(self.get_output_dir)

        self.more_options_btn.clicked.connect(self.toggle_moreoptions)
        
        self.continue_button.clicked.connect(self.retrieve_inputs)
        self.continue_button.clicked.connect(self.start_pipeline) 
        
        self.return_button.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.main_page)) 
        
    def start_pipeline(self):
        """Switch to RunWindow and execute pipeline."""
        # Get list of targets from line (assuming comma-separated or space-separated)
        targets_input = self.target_line.text()
        target_list = [t.strip() for t in targets_input.replace(",", " ").split() if t.strip()]
        
        # Create a new PlotsWindow with this target list
        self.main_window.plots_page = PlotsWindow(self.main_window, target_list)
        self.main_window.stack.addWidget(self.main_window.plots_page)

        # Show run page
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

    def get_output_dir(self):
        response = qtw.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select a folder"#,
            #directory=os.getcwd(),
            #filter = 'FITS file (*.fits *.uvfits *.idifits)'
        )
        if len(response) > 0:
            self.output_line.setText(str(response[0:]))

    def retrieve_inputs(self):
        inputs = {}
        for label, line_edit in self.fields.items():
            print(label, line_edit)
            if label == "load_all":
                inputs[label] = self.loadall_line.currentText() == "True"
            elif label == "paths":
                inputs[label] = [line_edit.text()]
            elif label == "targets":
                inputs[label] = [t.strip() for t in line_edit.text().replace(",", " ").split() if t.strip()]
            else:
                inputs[label] = line_edit.text()

        # Save inputs as JSON
        json_inputs = json.dumps(inputs)
        with open('../tmp/temp.json', 'w') as f:
            f.write(json_inputs)

        print(f"Inputs: {inputs}")
    
    def showEvent(self, event):
        if self.should_reset_fields:
            for label, widget in list(self.fields.items()):
                if isinstance(widget, qtw.QLineEdit):
                    widget.clear()
                elif isinstance(widget, qtw.QComboBox):
                    widget.setCurrentIndex(0)
            self.more_options.setVisible(False)
            self.should_reset_fields = False  # Reset the flag after clearing
        super().showEvent(event)
        
        
class JSONWindow(qtw.QWidget, Ui_JSON_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)       

        self.selectfile_btn.clicked.connect(self.get_input_file)
        self.return_button.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.main_page))        
   
    def get_input_file(self):
        response = qtw.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select a file",
            #directory=os.getcwd(),
            filter = 'JSON file (*.json)'
        )
        self.filepath_line.setText(str(response[0]))
        
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
        #self.text_output.setStyleSheet("""
        #    QTextEdit {
        #        background-color: black;
        #        color: white;
        #        font-size: 13pt;
        #    }
        #""")

        sys.stdout = OutputRedirector(self.text_output)  # Redirect stdout

        self.plots_btn.setVisible(False)
        self.return_btn.setVisible(False)

        self.plots_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.plots_page))
        self.return_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.manual_page))

        self.worker = None  # Placeholder for pipeline worker

    def RunPipeline(self):
        """Starts the subprocess in a separate thread for live output."""
        self.text_output.clear()  # Clear previous logs

        # Create worker thread
        self.worker = PipelineWorker()
        self.worker.output_received.connect(self.append_colored_output)
        self.worker.error_received.connect(self.append_colored_output)   # Live error update
        self.worker.process_finished.connect(self.show_buttons)  # Show buttons when finished

        self.worker.start()  # Start pipeline process

    def show_buttons(self):
        """Show plots and return buttons after process finishes."""
        self.plots_btn.setVisible(True)
        self.return_btn.setVisible(True)

    def append_colored_output(self, text):
        if not text:
            return

        # Get color from static method
        color = OutputRedirector.get_color_static(text)

        # Set up formatting
        fmt = gtg.QTextCharFormat()
        fmt.setForeground(gtg.QColor(color))

        # Insert plain text
        cursor = self.text_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.setCharFormat(fmt)
        cursor.insertText(text)  # <- This preserves \n exactly as they are
        self.text_output.setTextCursor(cursor)
        self.text_output.ensureCursorVisible()




class PlotsWindow(qtw.QWidget):
    def __init__(self, main_window, target_list):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Interactive Plots")

        # Main layout
        self.gridLayout = qtw.QGridLayout(self)
        self.gridLayout.setObjectName(u"gridLayout")

        # Scroll area to contain group boxes
        scroll_area = qtw.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = qtw.QWidget()
        scroll_layout = qtw.QVBoxLayout(scroll_content)

        button_dict = {}
        # Create group boxes dynamically
        for i, target in enumerate(target_list):
            group_box = qtw.QGroupBox(target)

            group_box.setStyleSheet(f"""
                QGroupBox {{
                    font-size: 20px;
                    font-weight: bold;
                    margin-top: 10px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 5px;
                    font-size: 20px;
                    font-weight: bold;
                }}
                    """)
            group_layout = qtw.QGridLayout()
            group_layout.setContentsMargins(10, 30, 10, 10)  # Space for the title

            button_dict[target] = []

            # Add buttons to each group box
            button_texts = ["Amp&&Phase - Frequency", "Amp&&Phase - Time",
                            "Amp&&Phase - UV Distance", "UV Coverage"]
            for j in range(4):
                button = qtw.QPushButton(button_texts[j])
                button.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
                group_layout.addWidget(button, j//2, j%2, 1, 1)
                button_dict[target].append(button)

            group_box.setLayout(group_layout)
            scroll_layout.addWidget(group_box)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        self.gridLayout.addWidget(scroll_area, 0, 0, 1, 2)

        self.canvas_window = []

        for target in target_list:
            button_dict[target][0].clicked.connect(partial(self.openPossmCanvas,target))
            button_dict[target][1].clicked.connect(partial(self.openVplotCanvas,target))
            button_dict[target][2].clicked.connect(partial(self.openRadplotCanvas,target))
            button_dict[target][3].clicked.connect(partial(self.openUvplotCanvas,target))

        #self.return_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.run_page)) 
        

        return_btn = qtw.QPushButton("Return")
        return_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.run_page))
        self.gridLayout.addWidget(return_btn, 2, 0, 1, 1)

        self.verticalSpacer = qtw.QSpacerItem(20, 40, qtw.QSizePolicy.Policy.Minimum, qtw.QSizePolicy.Policy.Expanding)
        self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 2)


    def openVplotCanvas(self, target):
        canvas = VplotWindow(target)
        self.canvas_window.append(canvas)
        canvas.show()
    def openPossmCanvas(self, target):
        canvas = PossmWindow(target)
        self.canvas_window.append(canvas)
        canvas.show()
    def openRadplotCanvas(self, target):
        canvas = RadplotWindow(target)
        self.canvas_window.append(canvas)
        canvas.show()
    def openUvplotCanvas(self, target):
        canvas = UvplotWindow(target)
        self.canvas_window.append(canvas)
        canvas.show()
        
       
class VplotWindow(qtw.QMainWindow):
    def __init__(self, target):
        super().__init__()

        self.setWindowTitle("VPLOT")
        self.target = target

        # Load the VPLOT data
        self.loaded_vplot_data = pickle.load(open(f'../tmp/{self.target}.vplt.pickle', 'rb'))
        self.plot_keys = sorted([key for key in self.loaded_vplot_data.keys() if isinstance(key, tuple)])
        self.current_index = 0
        self.selected_baseline = self.plot_keys[0] if self.plot_keys else None

        # Create central widget and layout
        central_widget = qtw.QWidget()
        self.main_layout = qtw.QVBoxLayout()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # --- Controls Layout ---
        controls_layout = qtw.QHBoxLayout()

        # Baseline selector
        self.bl_selector = qtw.QComboBox()
        for key in self.plot_keys:
            ant1, ant2 = sorted(key)
            self.bl_selector.addItem(f"{ant1}-{ant2}")
        self.bl_selector.currentTextChanged.connect(self.update_baseline_selection)
        controls_layout.addWidget(self.bl_selector)

        # Previous and Next buttons
        self.prev_button = qtw.QPushButton("Previous")
        self.prev_button.clicked.connect(self.show_previous_baseline)
        controls_layout.addWidget(self.prev_button)

        self.next_button = qtw.QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_baseline)
        controls_layout.addWidget(self.next_button)

        self.main_layout.addLayout(controls_layout)

        # --- Matplotlib setup ---
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas)

        # Initial plot
        self.plot_data()

    def update_baseline_selection(self, text):
        """Update selected baseline and replot."""
        ant1, ant2 = map(int, text.split('-'))  # ← cast to integers
        self.selected_baseline = (ant1, ant2)
        self.current_index = self.plot_keys.index(self.selected_baseline)
        self.plot_data()

    def show_previous_baseline(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.selected_baseline = self.plot_keys[self.current_index]
            self.bl_selector.setCurrentText(f"{self.selected_baseline[0]}-{self.selected_baseline[1]}")
            self.plot_data()

    def show_next_baseline(self):
        if self.current_index + 1 < len(self.plot_keys):
            self.current_index += 1
            self.selected_baseline = self.plot_keys[self.current_index]
            self.bl_selector.setCurrentText(f"{self.selected_baseline[0]}-{self.selected_baseline[1]}")
            self.plot_data()

    def plot_data(self):
        if not self.selected_baseline:
            return
        
        # --- NEW PLOT DRAWING ---
        self.figure.clear()  # Clear old plot

        with np.errstate(divide='ignore', invalid='ignore'):
            interactive_vplot(self.loaded_vplot_data, self.selected_baseline, vplot_fig = self.figure)

        self.canvas.draw()

class PossmWindow(qtw.QMainWindow):
    def __init__(self, target):
        super().__init__()

        self.setWindowTitle("POSSM")
        self.target = target
        self.selected_cl = "CL9"  # Default CL version
        self.current_plot_index = 0  # Track the current plot index
        self.selected_baseline = None

        self.possm_data = {}


        # Create a central widget and main layout
        central_widget = qtw.QWidget()
        self.main_layout = qtw.QVBoxLayout()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # --- Controls Layout ---
        controls_layout = qtw.QHBoxLayout()

        # --- CL Selector ---
        self.cl_selector = qtw.QComboBox()

        # Dynamically find all CL options from filenames
        pattern = re.compile(rf"{re.escape(self.target)}_(CL\d+).*\.possm\.npz$")
        cl_options = []

        for file in glob.glob(f"../tmp/{self.target}_*.possm.npz"):
            match = pattern.search(file.split("/")[-1])  # Match CLx without considering "_BP"
            if match:
                cl_options.append(match.group(1))  # Append the matched "CLx" (e.g., "CL1")

        # Sort CL options numerically (e.g., CL1, CL2, CL10)
        cl_options = sorted(set(cl_options), key=lambda x: int(x[2:]))

        self.cl_selector.addItems(cl_options)

        # Set default selection
        if self.selected_cl in cl_options:
            self.cl_selector.setCurrentText(self.selected_cl)
        elif cl_options:
            self.selected_cl = cl_options[0]
            self.cl_selector.setCurrentText(self.selected_cl)

        self.cl_selector.currentTextChanged.connect(self.update_cl_selection)
        controls_layout.addWidget(self.cl_selector)


        # Baseline Selector
        self.bl_selector = qtw.QComboBox()
        self.bl_selector.currentTextChanged.connect(self.update_baseline_selection)
        controls_layout.addWidget(self.bl_selector)

        # Previous and Next Buttons
        self.prev_button = qtw.QPushButton("Previous")
        self.prev_button.clicked.connect(self.show_previous_plot)
        controls_layout.addWidget(self.prev_button)

        self.next_button = qtw.QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_plot)
        controls_layout.addWidget(self.next_button)

        self.main_layout.addLayout(controls_layout)

        # --- Matplotlib Figure and Canvas ---
        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas)

        # Load initial data and plot
        self.load_possm_data()
        self.plot_data()

    def update_cl_selection(self, new_cl):
        """Update the selected CL version and reload data."""
        self.selected_cl = new_cl
        self.load_possm_data()
        self.plot_data()

    def update_baseline_selection(self, text):
        if not text or '-' not in text:
            return  # Ignore empty or invalid selections

        try:
            ant1, ant2 = map(int, text.split('-'))
            self.selected_baseline = (ant1, ant2)

            # Sync index for navigation buttons
            if self.selected_baseline in self.plot_keys:
                self.current_plot_index = self.plot_keys.index(self.selected_baseline)

            self.plot_data()
        except ValueError:
            # Optionally log or show a message if needed
            return

    def show_previous_plot(self):
        """Show the previous plot."""
        if self.current_plot_index > 0:
            self.current_plot_index -= 1
            self.selected_baseline = self.plot_keys[self.current_plot_index]
            self.bl_selector.setCurrentText(f"{self.selected_baseline[0]}-{self.selected_baseline[1]}")
            self.plot_data()

    def show_next_plot(self):
        """Show the next plot."""
        if self.current_plot_index + 1 < len(self.plot_keys):
            self.current_plot_index += 1
            self.selected_baseline = self.plot_keys[self.current_plot_index]
            self.bl_selector.setCurrentText(f"{self.selected_baseline[0]}-{self.selected_baseline[1]}")
            self.plot_data()

    def load_possm_data(self):
        # Extract the number after "CL" from self.selected_cl, e.g., "CL4" -> 4
        cl_number = re.search(r'CL(\d+)', self.selected_cl).group(1)

        # Find the matching files in the directory
        filenames = []
        for file in os.listdir('../tmp'):
            if file.endswith('.possm.npz') and f'CL{cl_number}' in file:
                filenames.append(file)
        
        if not filenames:
            qtw.QMessageBox.warning(self, "File not found", f"No files found for CL{cl_number}")
            self.possm_data = {}
            self.plot_keys = []
            self.bl_selector.clear()
            self.selected_baseline = None
            return

        # Try to load the first matching file (you can modify this if you need to load a specific one)
        filename = f'../tmp/{filenames[0]}'
        try:
            #with open(filename, 'rb') as file:
            #    self.possm_data = pickle.load(file)

            loaded_dict =  np.load(filename, allow_pickle = True)

            for key in loaded_dict:
                # Try to convert back to tuple if it's a string representation of a tuple
                try:
                    original_key = eval(key)  # This converts string '("A", "B")' back to the tuple ('A', 'B')
                except:
                    original_key = key  # If it's not a tuple, just use the string as is
                self.possm_data[original_key] = loaded_dict[key]

            # self.possm_data = {k: loaded_dict[k] for k in loaded_dict}

            self.plot_keys = [key for key in self.possm_data.keys() if isinstance(key, tuple)]
            self.plot_keys.sort()  # Ensure consistent ordering

            # ⬇️ Preserve previous baseline if possible
            prev_baseline = self.selected_baseline

            self.bl_selector.clear()
            for key in self.plot_keys:
                self.bl_selector.addItem(f"{key[0]}-{key[1]}")

            # Try to restore previously selected baseline
            if prev_baseline in self.plot_keys:
                self.selected_baseline = prev_baseline
            else:
                self.selected_baseline = self.plot_keys[0] if self.plot_keys else None

            # Update combo box and index
            if self.selected_baseline:
                self.bl_selector.setCurrentText(f"{self.selected_baseline[0]}-{self.selected_baseline[1]}")
                self.current_plot_index = self.plot_keys.index(self.selected_baseline)

        except FileNotFoundError:
            qtw.QMessageBox.warning(self, "File not found", f"Could not find file: {filename}")
            self.possm_data = {}
            self.plot_keys = []
            self.bl_selector.clear()
            self.selected_baseline = None



    def plot_data(self):
        """Plot data based on the selected baseline and scan index using interactive_possm()."""
        if not self.possm_data or not self.plot_keys or not self.selected_baseline:
            return

        # Get current baseline and scan
        scan = 0  # For now, this is static. Make dynamic later if needed.

        # --- NEW PLOT DRAWING ---
        self.figure.clear()  # Clear old plot

        with np.errstate(divide='ignore', invalid='ignore'):
            interactive_possm(self.possm_data, self.selected_baseline, scan=0, possm_fig=self.figure)

        self.canvas.draw()


    
class RadplotWindow(qtw.QMainWindow):
    def __init__(self, target):
        super().__init__()

        self.setWindowTitle("RADPLOT")
        self.target = target

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
        loaded_figure = pickle.load(open(f'../tmp/{self.target}.radplot.pickle', 'rb'))
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
    def __init__(self, target):
        super().__init__()

        self.setWindowTitle("UVPLOT")
        self.target = target

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
        loaded_figure = pickle.load(open(f'../tmp/{self.target}.uvplt.pickle', 'rb'))
        original_axes = loaded_figure.get_axes()

        # Create new figure and canvas
        new_figure = Figure()
        new_canvas = FigureCanvas(new_figure)
        new_toolbar = NavigationToolbar(new_canvas, self)

        # Recreate subplots and copy content
        new_axes = []
        for i, ax in enumerate(original_axes):
            new_ax = new_figure.add_subplot(1, 1, i + 1)  # <-- Remove sharex

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

            # Set limits before applying aspect
            new_ax.set_xlim(ax.get_xlim())
            new_ax.set_ylim(ax.get_ylim())

            # Apply equal aspect
            new_ax.set_aspect('equal', adjustable='box')  # 'box' works better for layouts

            new_axes.append(new_ax)

        #new_figure.tight_layout()


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

def interactive_possm(POSSM, bline, scan, possm_fig):
    n = scan
    bl = bline

    reals = np.array(POSSM[bl][n])[:,:,:,:,0]
    imags = np.array(POSSM[bl][n])[:,:,:,:,1]
    weights = np.array(POSSM[bl][n])[:,:,:,:,2]
    avg_reals = sum(reals*weights)/sum(weights)
    avg_imags = sum(imags*weights)/sum(weights) 
    amps = np.sqrt(avg_reals**2 + avg_imags**2).flatten()
    phases = (np.arctan2(avg_imags, avg_reals) * 360/(2*np.pi)).flatten()
    
    if_freq = POSSM['if_freq']
    chan_freq = []
    for IF, freq in enumerate(if_freq):
        n_chan = int(POSSM['total_bandwidth'][IF]/POSSM['ch_width'][IF])
        for c in range(n_chan):
            chan_freq.append(POSSM['central_freq'] + freq + c * POSSM['ch_width'][IF]) 
    chan_freq = np.array(chan_freq) / 1e9
    chunk_size = n_chan
    num_chunks = len(chan_freq) // chunk_size

    # Always create axes from possm_fig
    axes = possm_fig.subplots(
        2, num_chunks, #figsize=(8, 4), 
        gridspec_kw = {'height_ratios': [1,2]},
        sharey = 'row')

    axes_top, axes_bottom = axes
    # Plot each chunk in its respective subplot
    for i in range(num_chunks):
        start, end = i * chunk_size, (i + 1) * chunk_size   
        axes_top[i].plot(chan_freq[start:end], phases[start:end], color="g",  mec = 'c', mfc='c', marker="+", markersize = 12,
                        linestyle="none")
        axes_bottom[i].plot(chan_freq[start:end], amps[start:end], color="g",  mec = 'c', mfc='c', marker="+", markersize = 12, )
        axes_top[i].hlines(y = 0, xmin =  chan_freq[start], xmax = chan_freq[end-1], color = 'y')
        axes_top[i].set_ylim(-180,180)
        axes_bottom[i].set_ylim(0, np.nanmax(amps) * 1.10)
        axes_top[i].tick_params(labelbottom=False)
        axes_top[i].spines['bottom'].set_color('yellow')
        axes_top[i].spines['top'].set_color('yellow')
        axes_top[i].spines['right'].set_color('yellow')
        axes_top[i].spines['left'].set_color('yellow')
        axes_bottom[i].spines['bottom'].set_color('yellow')
        axes_bottom[i].spines['top'].set_color('yellow')
        axes_bottom[i].spines['right'].set_color('yellow')
        axes_bottom[i].spines['left'].set_color('yellow')

    # Remove ticks to not saturate the plot
    for i in range(1, num_chunks):
        axes_top[i].tick_params(labelleft=False)
        axes_bottom[i].tick_params(labelleft=False)

    
    axes_top[0].set_ylabel('Phase (Degrees)', fontsize = 15)
    axes_bottom[0].set_ylabel('Amplitude (Jy)', fontsize = 15)
    plt.style.use('dark_background')

    possm_fig.suptitle(f"Baseline {bl[0]}-{bl[1]}", fontsize=20)
    possm_fig.supxlabel("Frequency (GHz)", fontsize = 16)
    possm_fig.subplots_adjust(wspace=0, hspace = 0)  # No horizontal spacing

    return(possm_fig)

def interactive_vplot(vplot, bline, vplot_fig):
            bl = bline
            times = vplot[bl][0]
            amps = vplot[bl][1]
            phases = vplot[bl][2]

            axes = vplot_fig.subplots(2, 1,  sharex=True) 
            vplot_fig.suptitle('Amp&Phase - Time')
            vplot_fig.suptitle(f"Baseline {bl[0]}-{bl[1]}", fontsize=20)

            # First subplot 
            axes[0].scatter(times, amps, label='Amplitude', marker = '.',
                            s = 2, c = 'lime')
            axes[0].set_ylabel('Amplitude (JY)')
            axes[0].set_ylim(bottom = 0, top = 1.15* max(amps))

            # Second subplot 
            axes[1].scatter(times, phases, label='Phase', marker = '.',
                            s = 2, c = 'lime')
            axes[1].set_xlabel('Time')
            axes[1].set_ylabel('Phase (degrees)')


            return(vplot_fig)

def apply_dark_theme(app):
    dark_palette = gtg.QPalette()

    # Set the palette colors
    dark_palette.setColor(gtg.QPalette.Window, gtg.QColor(53, 53, 53))
    dark_palette.setColor(gtg.QPalette.WindowText,  gtg.QColor("white"))
    dark_palette.setColor(gtg.QPalette.Base, gtg.QColor(25, 25, 25))
    dark_palette.setColor(gtg.QPalette.AlternateBase, gtg.QColor(53, 53, 53))
    dark_palette.setColor(gtg.QPalette.ToolTipBase, gtg.QColor("white"))
    dark_palette.setColor(gtg.QPalette.ToolTipText, gtg.QColor("white"))
    dark_palette.setColor(gtg.QPalette.Text, gtg.QColor("white"))
    dark_palette.setColor(gtg.QPalette.Button, gtg.QColor(53, 53, 53))
    dark_palette.setColor(gtg.QPalette.ButtonText, gtg.QColor("white"))
    dark_palette.setColor(gtg.QPalette.BrightText, gtg.QColor("red"))
    dark_palette.setColor(gtg.QPalette.Link, gtg.QColor(42, 130, 218))

    dark_palette.setColor(gtg.QPalette.Highlight, gtg.QColor(42, 130, 218))
    dark_palette.setColor(gtg.QPalette.HighlightedText, gtg.QColor("black"))

    app.setPalette(dark_palette)
    app.setStyle("Fusion")  # Optional, but works well with palettes
  
# Run the Application
if __name__ == "__main__":
    if not qtw.QApplication.instance():
        app = qtw.QApplication(sys.argv)
        apply_dark_theme(app)
    else:
        app = qtw.QApplication.instance()
        apply_dark_theme(app)
        
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

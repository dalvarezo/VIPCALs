import sys
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

from GUI.py_files.ui_VIPCALs import Ui_VIPCALs
from GUI.py_files.ui_main_window import Ui_main_window
from GUI.py_files.ui_manual_window import Ui_manual_window
from GUI.py_files.ui_help_window import Ui_help_window
from GUI.py_files.ui_json_window import Ui_JSON_window
from GUI.py_files.ui_run_window import Ui_run_window

from io import StringIO
from PySide6.QtGui import QTextCursor


tmp_dir = os.path.expanduser("~/.vipcals/tmp")
os.makedirs(tmp_dir, exist_ok=True)
tmp_file = os.path.join(tmp_dir, "temp.json")



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
        elif "pipeline run" in lower:
            return "green"
        elif "fringe fit successful for" in lower:
            return "green"
        elif "data were exported to" in lower:
            return "green"
        elif "there were not enough solutions" in lower:
            return "orange"
        elif "fringe fit failed for all possible solutions. data" in lower:
            return "orange"
        elif "____info" in lower:
            return "lightblue"
        return "white"
        
class PipelineWorker(QThread):
    output_received = Signal(str)  # Signal to send stdout
    error_received = Signal(str)   # Signal to send stderr
    process_finished = Signal()

    def run(self):
        """Runs the pipeline in a subprocess and streams output."""
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        MAIN_PATH = os.path.join(CURRENT_DIR, "..", "vipcals", "__main__.py")

        process = subprocess.Popen(
            ["ParselTongue", MAIN_PATH,
            tmp_file],
            #["cat", "../tmp/temp.json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffering for real-time output
            universal_newlines=True
        )

        # Read stdout line by line
        for line in iter(process.stdout.readline, ''):
            self.output_received.emit(line)  # Emit each line immediately
           

        # Read stderr first but only emit if process fails
        stderr_output = process.stderr.read()

        process.wait()  # Wait for completion

        if process.returncode != 0 and stderr_output:
            for err_line in stderr_output.splitlines():
                self.error_received.emit(f"\n[ERROR]: {err_line}")

        process.wait()  # Ensure process finishes

        self.process_finished.emit()  # Notify when done
        
        
class JsonPipelineWorker(QThread):
    output_received = Signal(str)  # Signal to send stdout
    error_received = Signal(str)   # Signal to send stderr
    process_finished = Signal()

    def __init__(self, json_path):
        super().__init__()
        self.json_path = json_path
        
    def run(self):
        """Runs mock_pipeline.py in a subprocess and streams output."""
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        MAIN_PATH = os.path.join(CURRENT_DIR, "..", "vipcals", "__main__.py")
        process = subprocess.Popen(
            ["ParselTongue", MAIN_PATH,
            self.json_path],
            #["cat", "../tmp/temp.json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffering for real-time output
            universal_newlines=True
        )

        # Read stdout line by line
        for line in iter(process.stdout.readline, ''):
            self.output_received.emit(line)  # Emit each line immediately
           

        # Read stderr first but only emit if process fails
        stderr_output = process.stderr.read()

        process.wait()  # Wait for completion

        if process.returncode != 0 and stderr_output:
            for err_line in stderr_output.splitlines():
                self.error_received.emit(f"\n[ERROR]: {err_line}")

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
        self.json_run_page = JsonRunWindow(self)
        # self.plots_page = PlotsWindow(self)

        # Add widgets to the stacked widget
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.json_page)
        self.stack.addWidget(self.help_page)
        self.stack.addWidget(self.manual_page)
        self.stack.addWidget(self.run_page)
        self.stack.addWidget(self.json_run_page)
        # self.stack.addWidget(self.plots_page)

        # Keep track of the plots opened
        self.canvas_windows = []

        # Show the main page by default
        self.stack.setCurrentWidget(self.main_page)
        
        # Set initial size
        self.setMinimumSize(400, 300)

        # Connect page switching to resizing
        self.stack.currentChanged.connect(self.adjust_mainwindow_size)

    def adjust_mainwindow_size(self, index):
        widget = self.stack.widget(index)
        if hasattr(widget, "suggestedSize"):
            size = widget.suggestedSize()
            self.resize(size)

    def register_canvas_window(self, win):
        self.canvas_windows.append(win)

    def closeEvent(self, event):
        # Close all open plot windows
        for win in self.canvas_windows:
            if win is not None and win.isVisible():
                win.close()
        # Clean the tmp directory
        os.system(f"rm -r {tmp_dir}/*")
        event.accept()
        
        
class MainPage(qtw.QWidget, Ui_main_window):  
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)
        self._suggested_size = qtc.QSize(800,323)
        
        self.JSON_input_btn.clicked.connect(self.open_json_page)
        self.man_input_btn.clicked.connect(self.open_manual_page)

    def suggestedSize(self):
        return self._suggested_size

    def open_manual_page(self):
        self.main_window.manual_page.should_reset_fields = True
        self.main_window.stack.setCurrentWidget(self.main_window.manual_page)

    def open_json_page(self):
        self.main_window.json_page.selectfile_line.clear()
        self.main_window.stack.setCurrentWidget(self.main_window.json_page)

        
class ManualWindow(qtw.QWidget, Ui_manual_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)  
        self._suggested_size = qtc.QSize(800,623)


        ##########   FOR NOW SOME OPTIONS ARE HIDDEN    ##########
        self.calsour_line.setVisible(False)
        self.calsour_lbl.setVisible(False)        
        self.freqsel_line.setVisible(False)
        self.freqsel_lbl.setVisible(False)
        self.subarray_chck.setVisible(False)
        self.subarray_lbl.setVisible(False)
        ##########################################################

        self.should_reset_fields = False  # Flag for reset control
        
        self.target_rows = [(self.target_line, self.addmore_btn)]
        self.phaseref_rows = [(self.phasref_line, self.addmorephasref_btn)]
        self.shift_rows = [(self.shift_line, self.addmoreshift_btn)]

        # Define fields

        self.fields = {
            # Basic inputs
            "userno": self.userno_line,
            "disk": self.disk_line,
            "paths": self.filepath_line,
            "targets": self.target_line,
            "output_directory": self.output_line,
            # Calibration options
            "calib": self.calsour_line,
            "calib_all": self.caliball_chck,
            "phase_ref": self.phasref_line,
            # Loading options
            "load_all": self.loadall_chck,
            "load_tables": self.loadtables_line,
            "freq_sel": self.freqsel_line,
            "subarray": self.subarray_chck,
            "shifts": self.shift_line,
            "time_aver": self.timeaver_line,
            "freq_aver": self.freqaver_line,
            # Reference antenna options
            "refant": self.refant_line,
            "refant_list": self.priorant_line,
            "search_central": self.centrant_chck,
            "max_scan_refant_search": self.maxrefantscans_line,
            # Fringe options
            "solint": self.solint_line,
            "fringe_snr": self.snr_line,
            "min_solint": self.minsolint_line,
            "max_solint": self.maxsolint_line,
            # Export options            
            "channel_out": self.chanout_line,
            "flag_edge": self.edgeflag_line,
            # Plotting options
            "interactive": self.interactive_chck
        }
               
        self.chanout_line.addItems(['SINGLE', 'MULTI'])

        self.selectfile_btn.clicked.connect(self.get_input_file)
        self.selectdir_btn.clicked.connect(self.get_output_dir)
        self.loadtables_btn.clicked.connect(self.get_antab_file)

        self.more_options_btn.clicked.connect(self.toggle_moreoptions)
        
        self.addmore_btn.clicked.connect(self.add_target_row)
        self.addmorephasref_btn.clicked.connect(self.add_phaseref_row)
        self.addmoreshift_btn.clicked.connect(self.add_shift_row)
        
        self.continue_button.clicked.connect(self.retrieve_inputs)
        self.continue_button.clicked.connect(self.start_pipeline) 
        
        self.return_button.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.main_page)) 
        
    def start_pipeline(self):
        """Switch to RunWindow and execute pipeline."""
        if self.interactive_chck.isChecked():
            # Show run page
            self.main_window.run_page.hide_buttons()
            self.main_window.stack.setCurrentWidget(self.main_window.run_page)  # Show RunWindow
            self.main_window.run_page.RunPipeline(interactive = True)  # Call the function when the button is clicked
        else:
            # Show run page
            self.main_window.run_page.hide_buttons()
            self.main_window.stack.setCurrentWidget(self.main_window.run_page)  # Show RunWindow
            self.main_window.run_page.RunPipeline(interactive = False)  # Call the function when the button is clicked
         
    def toggle_moreoptions(self):
        self.calibbox.setVisible(not self.calibbox.isVisible())
        self.loadbox.setVisible(not self.loadbox.isVisible())
        self.refantbox.setVisible(not self.refantbox.isVisible())
        self.fringebox.setVisible(not self.fringebox.isVisible())
        self.exportbox.setVisible(not self.exportbox.isVisible())
        self.plotbox.setVisible(not self.plotbox.isVisible())
        
    def add_target_row(self):
        line_edit = qtw.QLineEdit()
        remove_button = qtw.QPushButton("Remove")
        font3 = gtg.QFont()
        font3.setPointSize(10)
        font3.setBold(False)
        remove_button.setFont(font3)

        # Connect button with lambda including dummy argument for clicked signal
        remove_button.clicked.connect(partial(self.remove_target_row, line_edit))

        self.target_rows.append((line_edit, remove_button))
        self.refresh_layout()

    def remove_target_row(self, target_line_edit):
        for i, (line_edit, remove_button) in enumerate(self.target_rows):
            if line_edit == target_line_edit:
                # Remove widgets from layout explicitly
                self.gridLayout_3.removeWidget(line_edit)
                self.gridLayout_3.removeWidget(remove_button)

                line_edit.deleteLater()
                remove_button.deleteLater()

                self.target_rows.pop(i)
                self.refresh_layout()
                break

    def add_phaseref_row(self):
        line_edit = qtw.QLineEdit()
        remove_button = qtw.QPushButton("Remove")
        font3 = gtg.QFont()
        font3.setPointSize(10)
        font3.setBold(False)
        remove_button.setFont(font3)

        # Connect button with lambda including dummy argument for clicked signal
        remove_button.clicked.connect(partial(self.remove_phaseref_row, line_edit))

        self.phaseref_rows.append((line_edit, remove_button))
        self.refresh_layout()

    def remove_phaseref_row(self, target_line_edit):
        for i, (line_edit, remove_button) in enumerate(self.phaseref_rows):
            if line_edit == target_line_edit:
                # Remove widgets from layout explicitly
                self.gridLayout_3.removeWidget(line_edit)
                self.gridLayout_3.removeWidget(remove_button)

                line_edit.deleteLater()
                remove_button.deleteLater()

                self.phaseref_rows.pop(i)
                self.refresh_layout()
                break

    def add_shift_row(self):
        line_edit = qtw.QLineEdit()
        remove_button = qtw.QPushButton("Remove")
        font3 = gtg.QFont()
        font3.setPointSize(10)
        font3.setBold(False)
        remove_button.setFont(font3)

        # Connect button with lambda including dummy argument for clicked signal
        remove_button.clicked.connect(partial(self.remove_shift_row, line_edit))

        self.shift_rows.append((line_edit, remove_button))
        self.refresh_layout()

    def remove_shift_row(self, target_line_edit):
        for i, (line_edit, remove_button) in enumerate(self.shift_rows):
            if line_edit == target_line_edit:
                # Remove widgets from layout explicitly
                self.gridLayout_3.removeWidget(line_edit)
                self.gridLayout_3.removeWidget(remove_button)

                line_edit.deleteLater()
                remove_button.deleteLater()

                self.shift_rows.pop(i)
                self.refresh_layout()
                break

    def refresh_layout(self):
        # Clear and re-add rows to ensure proper layout
        for i, (line_edit, remove_button) in enumerate(self.target_rows):
            row_index = 6 + i
            self.gridLayout_3.addWidget(line_edit, row_index, 1)
            self.gridLayout_3.addWidget(remove_button, row_index, 2)

        for i, (line_edit, remove_button) in enumerate(self.phaseref_rows):
            row_index = 2 + i
            self.gridLayout_4.addWidget(line_edit, row_index, 1)
            self.gridLayout_4.addWidget(remove_button, row_index, 2)

        for i, (line_edit, remove_button) in enumerate(self.shift_rows):
            row_index = 5 + i
            self.gridLayout_5.addWidget(line_edit, row_index, 1)
            self.gridLayout_5.addWidget(remove_button, row_index, 2)


            # Move "Add" button to the row after the last one
            #self.gridLayout_3.addWidget(self.addmore_btn, 3 + len(self.target_rows), 0, 1, 2)



    def get_input_file(self):
        response = qtw.QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select a file",
            #directory=os.getcwd(),
            filter = 'FITS file (*.fits *.uvfits *.idifits);;All files (*)'
        )
        self.filepath_line.setText(", ".join(response[0]))

    def get_antab_file(self):
        response = qtw.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select a file",
            #directory=os.getcwd(),
            #filter = 'FITS file (*.fits *.uvfits *.idifits);;All files (*)'
        )
        self.loadtables_line.setText(response[0])

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
            # print(label, line_edit)
            if label == "load_all":
                inputs[label] = self.loadall_chck.isChecked()
            elif label == "calib_all":
                inputs[label] = self.caliball_chck.isChecked()
            elif label == "search_central":
                inputs[label] = self.centrant_chck.isChecked()
            elif label == "subarray":
                inputs[label] = self.subarray_chck.isChecked()
            elif label == "interactive":
                inputs[label] = self.interactive_chck.isChecked()
            elif label == "channel_out":
                inputs[label] = self.chanout_line.currentText()         
            elif label == "paths":
                inputs[label] = line_edit.text().split(', ')
            elif label == "targets":
                inputs[label] = [x.text() for x,y in self.target_rows]
            elif label == "phase_ref":
                inputs[label] = [x.text() if x.text() != "" else None for x,y in self.phaseref_rows]
                if inputs[label] == [None]:
                    inputs[label] = None
            elif label == "shifts":
                inputs[label] = [x.text() if x.text() != "" else None for x,y in self.shift_rows]
                if inputs[label] == [None]:
                    inputs[label] = None

            elif label == "refant_list":
                if self.priorant_line.text() == "":
                    inputs[label] = None
                else:
                    inputs[label] = [code.upper() for code in re.split(r'\s*,\s*', self.priorant_line.text().strip()) if code]
            elif label == "max_scan_refant_search":
                inputs[label] = int(self.maxrefantscans_line.text())
            elif label == "min_solint":
                inputs[label] = float(self.minsolint_line.text())
            elif label == "max_solint":
                inputs[label] = float(self.maxsolint_line.text())
            elif label == "time_aver":
                inputs[label] = int(self.timeaver_line.text())
            elif label == "freq_aver":
                inputs[label] = int(self.freqaver_line.text())
            elif label == "fringe_snr":
                inputs[label] = float(self.snr_line.text())
                
            elif line_edit.text() == "":
                inputs[label] = None
            else:
                inputs[label] = line_edit.text()

        # Save inputs as JSON
        json_inputs = json.dumps(inputs)

        with open(tmp_file, 'w') as f:
            f.write(json_inputs)

        print(f"Inputs: {inputs}")
    
    def showEvent(self, event):
        if self.should_reset_fields:
            self.reset_fields()
            #for label, widget in list(self.fields.items()):
            #    if isinstance(widget, qtw.QLineEdit):
            #        widget.clear()
            #    elif isinstance(widget, qtw.QComboBox):
            #        widget.setCurrentIndex(0)
            self.calibbox.setVisible(False)
            self.loadbox.setVisible(False)
            self.refantbox.setVisible(False)
            self.fringebox.setVisible(False)
            self.exportbox.setVisible(False)
            self.plotbox.setVisible(False)
            self.should_reset_fields = False  # Reset the flag after clearing
        super().showEvent(event)
        
    def reset_fields(self):
        # Set default values
        ## Basic inputs
        self.userno_line.setText("")
        self.disk_line.setText("")
        self.filepath_line.setText("")
        for line_edit, button in self.target_rows:
            line_edit.setText("")
        self.target_line.setText("")
        self.output_line.setText("")
        ## Calibration options
        self.calsour_line.setText("")
        self.caliball_chck.setChecked(False)
        self.phasref_line.setText("")
        ## Loading options
        self.loadall_chck.setChecked(False)
        self.loadtables_line.setText("")
        self.freqsel_line.setText("")
        self.subarray_chck.setChecked(False)
        self.shift_line.setText("")
        self.timeaver_line.setText("2")
        self.freqaver_line.setText("500")
        ## Reference antenna options
        self.refant_line.setText("")
        self.priorant_line.setText("")
        self.centrant_chck.setChecked(True)
        self.maxrefantscans_line.setText("10")
        ## Fringe options
        self.snr_line.setText("5")
        self.solint_line.setText("")
        self.minsolint_line.setText("1")
        self.maxsolint_line.setText("10")
        ## Export options            
        self.chanout_line.setCurrentIndex(0)
        self.edgeflag_line.setText("")
        ## Plotting options
        self.interactive_chck.setChecked(True)
        
    def suggestedSize(self):
        return self._suggested_size
        
class JSONWindow(qtw.QWidget, Ui_JSON_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)      

        self._suggested_size = qtc.QSize(800,323) 

        self.selectfile_btn.clicked.connect(self.get_input_file)
        
        self.continue_button.clicked.connect(self.start_pipeline) 
        self.return_button.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.main_page))        
       
    def suggestedSize(self):
        return self._suggested_size


    def get_input_file(self):
        response = qtw.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select a file",
            #directory=os.getcwd(),
            filter = 'JSON file (*.json)'
        )
        self.selectfile_line.setText(str(response[0]))
        
    def start_pipeline(self):
        """Switch to RunWindow and execute pipeline."""
        # Show run page
        self.main_window.json_run_page.hide_buttons()
        self.main_window.stack.setCurrentWidget(self.main_window.json_run_page)  # Show RunWindow
        self.main_window.json_run_page.RunJsonPipeline(self.selectfile_line.text())  # Call the function when the button is clicked
        
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

        self._suggested_size = qtc.QSize(900,623) 

        self.text_output.setReadOnly(True)

        sys.stdout = OutputRedirector(self.text_output)  # Redirect stdout

        self.plots_btn.setVisible(False)
        self.return_btn.setVisible(False)

        self.plots_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.plots_page))
        self.return_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.manual_page))

        self.worker = None  # Placeholder for pipeline worker

    def RunPipeline(self, interactive):
        """Starts the subprocess in a separate thread for live output."""
        self.text_output.clear()  # Clear previous logs

        self.interactive = interactive

        # Create worker thread
        self.worker = PipelineWorker()
        self.worker.output_received.connect(self.append_colored_output)
        self.worker.error_received.connect(self.append_colored_output)   # Live error update
        if self.interactive == True: 
            self.worker.process_finished.connect(self.prepare_plot_window) 
            self.worker.process_finished.connect(self.show_buttons)  # Show buttons when finished
        else:
            self.worker.process_finished.connect(self.show_return_button)  # Show buttons when finished

        self.worker.start()  # Start pipeline process

    def show_buttons(self):
        """Show plots and return buttons after process finishes."""
        self.plots_btn.setVisible(True)
        self.return_btn.setVisible(True)
    
    def show_return_button(self):
        """Show return button after process finishes."""
        self.return_btn.setVisible(True)
    
    def hide_buttons(self):
        """Hide plots and return buttons after process finishes."""
        self.plots_btn.setVisible(False)
        self.return_btn.setVisible(False)
    
    def prepare_plot_window(self):
        # Get list of targets from the /vipcals/tmp directory
        pattern = pattern = re.compile(r'^(.*?_\d+G)_')
        target_list = set()

        for filename in os.listdir(tmp_dir):
            match = pattern.match(filename)
            if match:
                target_list.add(match.group(1))

        target_list = sorted(target_list)
        
        # Create a new PlotsWindow with this target list
        self.main_window.plots_page = PlotsWindow(self.main_window, target_list)
        self.main_window.stack.addWidget(self.main_window.plots_page)

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

    def suggestedSize(self):
        return self._suggested_size


class JsonRunWindow(qtw.QWidget, Ui_run_window):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setupUi(self)

        self.text_output.setReadOnly(True)

        self._suggested_size = qtc.QSize(900,623) 

        sys.stdout = OutputRedirector(self.text_output)  # Redirect stdout

        self.plots_btn.setVisible(False)
        self.return_btn.setVisible(False)

        self.plots_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.plots_page))
        self.return_btn.clicked.connect(lambda: self.main_window.stack.setCurrentWidget(self.main_window.json_page))

        self.worker = None  # Placeholder for pipeline worker


    def RunJsonPipeline(self, json_path):
        """Starts the subprocess in a separate thread for live output."""
        self.text_output.clear()  # Clear previous logs

        # Create worker thread
        self.worker = JsonPipelineWorker(json_path)
        self.worker.output_received.connect(self.append_colored_output)
        self.worker.error_received.connect(self.append_colored_output)   # Live error update
        self.worker.process_finished.connect(self.prepare_plot_window)  # Show buttons when finished
        self.worker.process_finished.connect(self.show_return_button)  # Show buttons when finished

        self.worker.start()  # Start pipeline process

    def show_buttons(self):
        """Show plots and return buttons after process finishes."""
        self.plots_btn.setVisible(True)
        self.return_btn.setVisible(True)
        
    def hide_buttons(self):
        """Hide plots and return buttons after process finishes."""
        self.plots_btn.setVisible(False)
        self.return_btn.setVisible(False)
    
    def show_return_button(self):
        """Show return button after process finishes."""
        self.return_btn.setVisible(True)
    
    def prepare_plot_window(self):
        # Get list of targets from the /vipcals/tmp directory
        pattern = pattern = re.compile(r'^(.*?_\d+G)_')
        target_list = set()

        for filename in os.listdir(tmp_dir):
            match = pattern.match(filename)
            if match:
                target_list.add(match.group(1))

        target_list = sorted(target_list)
        
        # Create a new PlotsWindow with this target list
        self.main_window.plots_page = PlotsWindow(self.main_window, target_list)
        self.main_window.stack.addWidget(self.main_window.plots_page)

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

    def suggestedSize(self):
        return self._suggested_size


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
            group_box = qtw.QGroupBox(target.split('_')[0]+' - ' + target.split('_')[-1])

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
            group_box.setMinimumHeight(200)  
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

        scroll_layout.addStretch(1)  # Add vertical stretch at bottom of scroll area content



    def openVplotCanvas(self, target):
        canvas = VplotWindow(target)
        self.canvas_window.append(canvas)
        self.main_window.register_canvas_window(canvas)
        canvas.show()
    def openPossmCanvas(self, target):
        canvas = PossmWindow(target)
        self.canvas_window.append(canvas)
        self.main_window.register_canvas_window(canvas)
        canvas.show()
    def openRadplotCanvas(self, target):
        canvas = RadplotWindow(target)
        self.canvas_window.append(canvas)
        self.main_window.register_canvas_window(canvas)
        canvas.show()
    def openUvplotCanvas(self, target):
        canvas = UvplotWindow(target)
        self.canvas_window.append(canvas)
        self.main_window.register_canvas_window(canvas)
        canvas.show()
        
       
class VplotWindow(qtw.QMainWindow):
    def __init__(self, target):
        super().__init__()

        self.setWindowTitle("VPLOT")
        self.target = target

        # Load the VPLOT data
        file = glob.glob(f'{tmp_dir}/{self.target}*.vplt.pickle')
        self.loaded_vplot_data = pickle.load(open(file[0], 'rb'))
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
        ant1, ant2 = map(int, text.split('-'))  # cast to integers
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
        pattern = re.compile(rf"{re.escape(self.target)}.*_CL(\d+)(?:_[^.]*)?\.possm\.npz$")
        cl_options = []

        for file in glob.glob(f"{tmp_dir}/{self.target}_*.possm.npz"):
            match = pattern.search(file.split("/")[-1])
            if match:
                cl_options.append(f"CL{match.group(1)}")

        # Sort CL options numerically (e.g., CL1, CL2, CL10)
        cl_options = sorted(set(cl_options), key=lambda x: int(x[2:]))

        self.cl_selector.addItems(cl_options)

        self.selected_cl = cl_options[-1]  # Default CL version

        # Set default selection
        if self.selected_cl in cl_options:
            self.cl_selector.setCurrentText(self.selected_cl)
        elif cl_options:
            self.selected_cl = cl_options[0]
            self.cl_selector.setCurrentText(self.selected_cl)

        self.cl_selector.currentTextChanged.connect(self.update_cl_selection)
        controls_layout.addWidget(self.cl_selector)


        # --- Baseline Selector ---
        self.bl_selector = qtw.QComboBox()
        self.bl_selector.currentTextChanged.connect(self.update_baseline_selection)
        controls_layout.addWidget(self.bl_selector)

        # --- Polarization Selector ---
        self.current_pol = 0  # Default pol index
        self.pol_selector = qtw.QComboBox()
        self.pol_selector.currentIndexChanged.connect(self.update_pol_selection)
        controls_layout.addWidget(self.pol_selector)

        # --- Scan Selector ---
        self.current_scan = 0  # Default scan index
        self.scan_selector = qtw.QComboBox()
        self.scan_selector.currentIndexChanged.connect(self.update_scan_selection)
        controls_layout.addWidget(self.scan_selector)

        # --- Previous and Next Buttons ---
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

    def update_scan_selection(self, index):
        self.current_scan = index
        self.plot_data()

    def update_pol_selection(self, pol):
        self.current_pol = pol
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
        """Load POSSM data for the selected target and CL version."""
        cl_number = re.search(r'CL(\d+)', self.selected_cl).group(1)
        target_prefix = f"{self.target}_"
        cl_label = f"CL{cl_number}"

        # Filter files that match both the current target and CL version
        filenames = [
            file for file in os.listdir(tmp_dir)
            if file.startswith(target_prefix) and f"_{cl_label}" in file and file.endswith('.possm.npz')
        ]

        if not filenames:
            qtw.QMessageBox.warning(self, "File not found", f"No files found for {self.target} {cl_label}")
            self.possm_data = {}
            self.plot_keys = []
            self.bl_selector.clear()
            self.selected_baseline = None
            return

        filename = f'{tmp_dir}/{filenames[0]}'
        self.possm_data = {}

        try:
            loaded_dict = np.load(filename, allow_pickle=True)

            for key in loaded_dict:
                # Safely evaluate only tuple-like keys
                try:
                    original_key = eval(key) if key.startswith("(") and key.endswith(")") else key
                except Exception:
                    original_key = key
                self.possm_data[original_key] = loaded_dict[key]

            self.plot_keys = [key for key in self.possm_data.keys() if isinstance(key, tuple)]
            self.plot_keys.sort()

            prev_baseline = self.selected_baseline

            self.bl_selector.clear()
            for key in self.plot_keys:
                self.bl_selector.addItem(f"{key[0]}-{key[1]}")

            if prev_baseline in self.plot_keys:
                self.selected_baseline = prev_baseline
            else:
                self.selected_baseline = self.plot_keys[0] if self.plot_keys else None

            if self.selected_baseline:
                self.bl_selector.setCurrentText(f"{self.selected_baseline[0]}-{self.selected_baseline[1]}")
                self.current_plot_index = self.plot_keys.index(self.selected_baseline)

            # Populate scan selector
            self.scan_selector.clear()
            if self.selected_baseline in self.possm_data:
                num_scans = len(self.possm_data[self.selected_baseline])
                for i in range(num_scans):
                    self.scan_selector.addItem(f"Scan {i+1}")
                self.current_scan = 0
                self.scan_selector.setCurrentIndex(self.current_scan)

            # Populate pol selector
            self.pol_selector.clear()
            if self.selected_baseline in self.possm_data:
                pols = self.possm_data['pols']
                for i, p in enumerate(pols):
                    self.pol_selector.addItem(f"{p}")
                self.current_pol = 0
                self.pol_selector.setCurrentIndex(self.current_pol)


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
        scan = self.current_scan  
        pol = self.current_pol
        # --- NEW PLOT DRAWING ---
        self.figure.clear()  # Clear old plot

        with np.errstate(divide='ignore', invalid='ignore'):
            interactive_possm(self.possm_data, self.selected_baseline, 
                              polarization = pol ,scan=scan, possm_fig=self.figure)

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
        file = glob.glob(f'{tmp_dir}/{self.target}*.radplot.pickle')
        loaded_figure = pickle.load(open(file[0], 'rb'))
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
        file = glob.glob(f'{tmp_dir}/{self.target}*.uvplt.pickle')
        loaded_figure = pickle.load(open(file[0], 'rb'))
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

def interactive_possm(POSSM, bline, polarization, scan,  possm_fig):
    n = scan
    bl = bline
    pol = polarization #POSSM['pols'].tolist().index(polarization)

    # Indexing goes like:
    # POSSM[baseline][scan][time, IF, channel, polarization, visibility]
    if len(POSSM['pols'].tolist()) < 2:
        reals = np.array(POSSM[bl][n])[:, :, :, :, 0]
        imags = np.array(POSSM[bl][n])[:, :, :, :, 1]
        weights = np.array(POSSM[bl][n])[:, :, :, :, 2]
    else:
        reals = np.array(POSSM[bl][n])[:, :, :, pol, 0]
        imags = np.array(POSSM[bl][n])[:, :, :, pol, 1]
        weights = np.array(POSSM[bl][n])[:, :, :, pol, 2]

    # Compute sums
    weighted_reals = reals * weights
    weighted_imags = imags * weights
    sum_weights = np.sum(weights, axis=0)  

    weighted_reals = np.array(weighted_reals, dtype=float)
    weighted_imags = np.array(weighted_imags, dtype=float)
    sum_weights = np.array(sum_weights, dtype=float)


    avg_reals = np.divide(np.sum(weighted_reals, axis=0), sum_weights)
    avg_imags = np.divide(np.sum(weighted_imags, axis=0), sum_weights)

    amps = np.sqrt((avg_reals**2 + avg_imags**2).astype(float)).flatten()
    phases = (np.arctan2(avg_imags.astype(float), avg_reals.astype(float)) * 360/(2*np.pi)).flatten()
    
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
        if np.all(np.isnan(amps)):
            # Skip plotting or set default limits
            axes_bottom[i].set_ylim(0, 1) 
        else:
            axes_bottom[i].set_ylim(np.nanmin(amps)*0.90, np.nanmax(amps) * 1.10)
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

    # Rotate xtick labels so they overlap a bit less
    for ax in axes_bottom:
        for label in ax.get_xticklabels():
            label.set_rotation(45)
            label.set_ha('right')

    
    axes_top[0].set_ylabel('Phase (Degrees)', fontsize = 15)
    axes_bottom[0].set_ylabel('Amplitude (Jy)', fontsize = 15)
    plt.style.use('dark_background')

    a1 = POSSM['ant_dict'].item()[bl[0]]
    a2 = POSSM['ant_dict'].item()[bl[1]]
    # possm_fig.suptitle(f"Baseline {bl[0]}-{bl[1]}", fontsize=20)
    possm_fig.suptitle(f"{bl[0]}.{a1} - {bl[1]}.{a2}", fontsize=20)
    possm_fig.supxlabel("Frequency (GHz)", fontsize = 16)
    possm_fig.subplots_adjust(bottom=0.18)
    possm_fig.subplots_adjust(wspace=0, hspace = 0)  # No horizontal spacing

    return(possm_fig)

def interactive_vplot(vplot, bline, vplot_fig):
            bl = bline
            times = vplot[bl][0]
            amps = vplot[bl][1]
            phases = vplot[bl][2]
            a1 = vplot['ant_dict'][bl[0]]
            a2 = vplot['ant_dict'][bl[1]]
            axes = vplot_fig.subplots(2, 1,  sharex=True) 

            vplot_fig.suptitle('Amp&Phase - Time')
            vplot_fig.suptitle(f"{bl[0]}.{a1} - {bl[1]}.{a2}", fontsize=20)

            # First subplot 
            axes[0].scatter(times, amps, label='Amplitude', marker = '.',
                            s = 2, c = 'lime')
            axes[0].set_ylabel('Amplitude (JY)')
            axes[0].set_ylim(bottom = 0.85*min(amps), top = 1.15* max(amps))

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
#if __name__ == "__main__":
def main():
    
    if not qtw.QApplication.instance():
        app = qtw.QApplication(sys.argv)
        apply_dark_theme(app)
    else:
        app = qtw.QApplication.instance()
        apply_dark_theme(app)
        
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
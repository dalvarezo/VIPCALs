# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TESTxnjQdt.ui'
##
## Created by: Qt User Interface Compiler version 6.2.4
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLayout, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_manual_window(object):
    def setupUi(self, manual_window):
        if not manual_window.objectName():
            manual_window.setObjectName(u"manual_window")
        manual_window.resize(800, 623)
        manual_window.setMinimumSize(QSize(800, 500))
        self.gridLayout = QGridLayout(manual_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.continue_button = QPushButton(manual_window)
        self.continue_button.setObjectName(u"continue_button")
        font = QFont()
        font.setPointSize(10)
        self.continue_button.setFont(font)

        self.gridLayout.addWidget(self.continue_button, 3, 2, 1, 1)

        self.return_button = QPushButton(manual_window)
        self.return_button.setObjectName(u"return_button")
        self.return_button.setFont(font)

        self.gridLayout.addWidget(self.return_button, 3, 1, 1, 1)

        self.scrollArea = QScrollArea(manual_window)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 766, 1233))
        self.verticalLayout_8 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.basicgroup = QGroupBox(self.scrollAreaWidgetContents)
        self.basicgroup.setObjectName(u"basicgroup")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.basicgroup.sizePolicy().hasHeightForWidth())
        self.basicgroup.setSizePolicy(sizePolicy1)
        font1 = QFont()
        font1.setPointSize(11)
        font1.setBold(False)
        self.basicgroup.setFont(font1)
        self.basicgroup.setAlignment(Qt.AlignCenter)
        self.verticalLayout = QVBoxLayout(self.basicgroup)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetNoConstraint)
        self.basic_top = QWidget(self.basicgroup)
        self.basic_top.setObjectName(u"basic_top")
        sizePolicy1.setHeightForWidth(self.basic_top.sizePolicy().hasHeightForWidth())
        self.basic_top.setSizePolicy(sizePolicy1)
        self.basic_top.setMinimumSize(QSize(0, 0))
        self.horizontalLayout = QHBoxLayout(self.basic_top)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.basic_line_L = QFrame(self.basic_top)
        self.basic_line_L.setObjectName(u"basic_line_L")
        self.basic_line_L.setFrameShape(QFrame.HLine)
        self.basic_line_L.setFrameShadow(QFrame.Raised)

        self.horizontalLayout.addWidget(self.basic_line_L)

        self.basic_label = QLabel(self.basic_top)
        self.basic_label.setObjectName(u"basic_label")
        font2 = QFont()
        font2.setPointSize(12)
        font2.setBold(False)
        self.basic_label.setFont(font2)
        self.basic_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.basic_label)

        self.basic_line_R = QFrame(self.basic_top)
        self.basic_line_R.setObjectName(u"basic_line_R")
        self.basic_line_R.setFrameShape(QFrame.HLine)
        self.basic_line_R.setFrameShadow(QFrame.Raised)

        self.horizontalLayout.addWidget(self.basic_line_R)


        self.verticalLayout.addWidget(self.basic_top)

        self.basic_bottom = QWidget(self.basicgroup)
        self.basic_bottom.setObjectName(u"basic_bottom")
        sizePolicy1.setHeightForWidth(self.basic_bottom.sizePolicy().hasHeightForWidth())
        self.basic_bottom.setSizePolicy(sizePolicy1)
        self.gridLayout_3 = QGridLayout(self.basic_bottom)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setVerticalSpacing(10)
        self.output_line = QLineEdit(self.basic_bottom)
        self.output_line.setObjectName(u"output_line")

        self.gridLayout_3.addWidget(self.output_line, 5, 1, 1, 1)

        self.disk_line = QLineEdit(self.basic_bottom)
        self.disk_line.setObjectName(u"disk_line")

        self.gridLayout_3.addWidget(self.disk_line, 2, 1, 1, 2)

        self.filepath_line = QLineEdit(self.basic_bottom)
        self.filepath_line.setObjectName(u"filepath_line")

        self.gridLayout_3.addWidget(self.filepath_line, 3, 1, 1, 1)

        self.disk_lbl = QLabel(self.basic_bottom)
        self.disk_lbl.setObjectName(u"disk_lbl")
        self.disk_lbl.setFont(font1)

        self.gridLayout_3.addWidget(self.disk_lbl, 2, 0, 1, 1)

        self.selectfile_btn = QPushButton(self.basic_bottom)
        self.selectfile_btn.setObjectName(u"selectfile_btn")
        self.selectfile_btn.setEnabled(True)
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.selectfile_btn.sizePolicy().hasHeightForWidth())
        self.selectfile_btn.setSizePolicy(sizePolicy2)
        self.selectfile_btn.setMaximumSize(QSize(16777215, 16777215))
        self.selectfile_btn.setSizeIncrement(QSize(0, 0))
        font3 = QFont()
        font3.setPointSize(10)
        font3.setBold(False)
        self.selectfile_btn.setFont(font3)
        self.selectfile_btn.setIconSize(QSize(16, 16))

        self.gridLayout_3.addWidget(self.selectfile_btn, 3, 2, 1, 1)

        self.selectdir_btn = QPushButton(self.basic_bottom)
        self.selectdir_btn.setObjectName(u"selectdir_btn")
        sizePolicy2.setHeightForWidth(self.selectdir_btn.sizePolicy().hasHeightForWidth())
        self.selectdir_btn.setSizePolicy(sizePolicy2)
        self.selectdir_btn.setFont(font3)

        self.gridLayout_3.addWidget(self.selectdir_btn, 5, 2, 1, 1)

        self.userno_line = QLineEdit(self.basic_bottom)
        self.userno_line.setObjectName(u"userno_line")

        self.gridLayout_3.addWidget(self.userno_line, 0, 1, 1, 2)

        self.filepath_lbl = QLabel(self.basic_bottom)
        self.filepath_lbl.setObjectName(u"filepath_lbl")
        self.filepath_lbl.setFont(font1)

        self.gridLayout_3.addWidget(self.filepath_lbl, 3, 0, 1, 1)

        self.userno_lbl = QLabel(self.basic_bottom)
        self.userno_lbl.setObjectName(u"userno_lbl")
        self.userno_lbl.setFont(font1)

        self.gridLayout_3.addWidget(self.userno_lbl, 0, 0, 1, 1)

        self.output_lbl = QLabel(self.basic_bottom)
        self.output_lbl.setObjectName(u"output_lbl")
        self.output_lbl.setFont(font1)

        self.gridLayout_3.addWidget(self.output_lbl, 5, 0, 1, 1)

        self.target_lbl = QLabel(self.basic_bottom)
        self.target_lbl.setObjectName(u"target_lbl")
        self.target_lbl.setFont(font1)

        self.gridLayout_3.addWidget(self.target_lbl, 6, 0, 1, 1)

        self.target_line = QLineEdit(self.basic_bottom)
        self.target_line.setObjectName(u"target_line")

        self.gridLayout_3.addWidget(self.target_line, 6, 1, 1, 1)

        self.addmore_btn = QPushButton(self.basic_bottom)
        self.addmore_btn.setObjectName(u"addmore_btn")
        self.addmore_btn.setFont(font3)

        self.gridLayout_3.addWidget(self.addmore_btn, 6, 2, 1, 1)

        self.gridLayout_3.setColumnStretch(0, 3)
        self.gridLayout_3.setColumnStretch(1, 7)
        self.gridLayout_3.setColumnStretch(2, 1)

        self.verticalLayout.addWidget(self.basic_bottom)


        self.verticalLayout_8.addWidget(self.basicgroup)

        self.more_options_btn = QPushButton(self.scrollAreaWidgetContents)
        self.more_options_btn.setObjectName(u"more_options_btn")
        self.more_options_btn.setFont(font)

        self.verticalLayout_8.addWidget(self.more_options_btn)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer)

        self.calibbox = QGroupBox(self.scrollAreaWidgetContents)
        self.calibbox.setObjectName(u"calibbox")
        self.calibbox.setFont(font1)
        self.calibbox.setAlignment(Qt.AlignCenter)
        self.verticalLayout_2 = QVBoxLayout(self.calibbox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.calib_top = QWidget(self.calibbox)
        self.calib_top.setObjectName(u"calib_top")
        self.horizontalLayout_2 = QHBoxLayout(self.calib_top)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.calib_line_L = QFrame(self.calib_top)
        self.calib_line_L.setObjectName(u"calib_line_L")
        self.calib_line_L.setFrameShape(QFrame.HLine)
        self.calib_line_L.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_2.addWidget(self.calib_line_L)

        self.calib_label = QLabel(self.calib_top)
        self.calib_label.setObjectName(u"calib_label")
        self.calib_label.setFont(font2)
        self.calib_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.calib_label)

        self.calib_line_R = QFrame(self.calib_top)
        self.calib_line_R.setObjectName(u"calib_line_R")
        self.calib_line_R.setFrameShape(QFrame.HLine)
        self.calib_line_R.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_2.addWidget(self.calib_line_R)


        self.verticalLayout_2.addWidget(self.calib_top)

        self.calib_bottom = QWidget(self.calibbox)
        self.calib_bottom.setObjectName(u"calib_bottom")
        self.gridLayout_4 = QGridLayout(self.calib_bottom)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setVerticalSpacing(10)
        self.caliball_chck = QCheckBox(self.calib_bottom)
        self.caliball_chck.setObjectName(u"caliball_chck")

        self.gridLayout_4.addWidget(self.caliball_chck, 1, 1, 1, 1)

        self.caliball_lbl = QLabel(self.calib_bottom)
        self.caliball_lbl.setObjectName(u"caliball_lbl")
        self.caliball_lbl.setFont(font1)

        self.gridLayout_4.addWidget(self.caliball_lbl, 1, 0, 1, 1)

        self.calsour_lbl = QLabel(self.calib_bottom)
        self.calsour_lbl.setObjectName(u"calsour_lbl")
        self.calsour_lbl.setFont(font1)

        self.gridLayout_4.addWidget(self.calsour_lbl, 0, 0, 1, 1)

        self.phasref_lbl = QLabel(self.calib_bottom)
        self.phasref_lbl.setObjectName(u"phasref_lbl")
        self.phasref_lbl.setFont(font1)

        self.gridLayout_4.addWidget(self.phasref_lbl, 2, 0, 1, 1)

        self.calsour_line = QLineEdit(self.calib_bottom)
        self.calsour_line.setObjectName(u"calsour_line")

        self.gridLayout_4.addWidget(self.calsour_line, 0, 1, 1, 2)

        self.phasref_line = QLineEdit(self.calib_bottom)
        self.phasref_line.setObjectName(u"phasref_line")

        self.gridLayout_4.addWidget(self.phasref_line, 2, 1, 1, 2)

        self.gridLayout_4.setColumnStretch(0, 3)
        self.gridLayout_4.setColumnStretch(1, 8)

        self.verticalLayout_2.addWidget(self.calib_bottom)


        self.verticalLayout_8.addWidget(self.calibbox)

        self.loadbox = QGroupBox(self.scrollAreaWidgetContents)
        self.loadbox.setObjectName(u"loadbox")
        self.loadbox.setFont(font1)
        self.loadbox.setAlignment(Qt.AlignCenter)
        self.verticalLayout_3 = QVBoxLayout(self.loadbox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.load_top = QWidget(self.loadbox)
        self.load_top.setObjectName(u"load_top")
        self.horizontalLayout_3 = QHBoxLayout(self.load_top)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.load_line_L = QFrame(self.load_top)
        self.load_line_L.setObjectName(u"load_line_L")
        self.load_line_L.setFrameShape(QFrame.HLine)
        self.load_line_L.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_3.addWidget(self.load_line_L)

        self.load_label = QLabel(self.load_top)
        self.load_label.setObjectName(u"load_label")
        font4 = QFont()
        font4.setFamilies([u"Sans Serif"])
        font4.setPointSize(12)
        font4.setBold(False)
        self.load_label.setFont(font4)
        self.load_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.load_label)

        self.load_line_R = QFrame(self.load_top)
        self.load_line_R.setObjectName(u"load_line_R")
        self.load_line_R.setFrameShape(QFrame.HLine)
        self.load_line_R.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_3.addWidget(self.load_line_R)


        self.verticalLayout_3.addWidget(self.load_top)

        self.load_bottom = QWidget(self.loadbox)
        self.load_bottom.setObjectName(u"load_bottom")
        self.gridLayout_5 = QGridLayout(self.load_bottom)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setVerticalSpacing(10)
        self.freqsel_lbl = QLabel(self.load_bottom)
        self.freqsel_lbl.setObjectName(u"freqsel_lbl")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.freqsel_lbl.sizePolicy().hasHeightForWidth())
        self.freqsel_lbl.setSizePolicy(sizePolicy3)
        self.freqsel_lbl.setFont(font1)

        self.gridLayout_5.addWidget(self.freqsel_lbl, 1, 0, 1, 1)

        self.loadall_lbl = QLabel(self.load_bottom)
        self.loadall_lbl.setObjectName(u"loadall_lbl")
        self.loadall_lbl.setFont(font1)

        self.gridLayout_5.addWidget(self.loadall_lbl, 0, 0, 1, 1)

        self.subarray_chck = QCheckBox(self.load_bottom)
        self.subarray_chck.setObjectName(u"subarray_chck")
        self.subarray_chck.setFont(font3)

        self.gridLayout_5.addWidget(self.subarray_chck, 2, 1, 1, 1)

        self.subarray_lbl = QLabel(self.load_bottom)
        self.subarray_lbl.setObjectName(u"subarray_lbl")
        self.subarray_lbl.setFont(font1)

        self.gridLayout_5.addWidget(self.subarray_lbl, 2, 0, 1, 1)

        self.shift_lbl = QLabel(self.load_bottom)
        self.shift_lbl.setObjectName(u"shift_lbl")
        self.shift_lbl.setFont(font1)

        self.gridLayout_5.addWidget(self.shift_lbl, 3, 0, 1, 1)

        self.loadall_chck = QCheckBox(self.load_bottom)
        self.loadall_chck.setObjectName(u"loadall_chck")

        self.gridLayout_5.addWidget(self.loadall_chck, 0, 1, 1, 2)

        self.freqsel_line = QLineEdit(self.load_bottom)
        self.freqsel_line.setObjectName(u"freqsel_line")

        self.gridLayout_5.addWidget(self.freqsel_line, 1, 1, 1, 2)

        self.shift_line = QLineEdit(self.load_bottom)
        self.shift_line.setObjectName(u"shift_line")

        self.gridLayout_5.addWidget(self.shift_line, 3, 1, 1, 2)

        self.gridLayout_5.setColumnStretch(0, 3)
        self.gridLayout_5.setColumnStretch(1, 8)

        self.verticalLayout_3.addWidget(self.load_bottom)


        self.verticalLayout_8.addWidget(self.loadbox)

        self.refantbox = QGroupBox(self.scrollAreaWidgetContents)
        self.refantbox.setObjectName(u"refantbox")
        self.refantbox.setFont(font1)
        self.refantbox.setAlignment(Qt.AlignCenter)
        self.verticalLayout_4 = QVBoxLayout(self.refantbox)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.refant_top = QWidget(self.refantbox)
        self.refant_top.setObjectName(u"refant_top")
        self.horizontalLayout_4 = QHBoxLayout(self.refant_top)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.refant_line_L = QFrame(self.refant_top)
        self.refant_line_L.setObjectName(u"refant_line_L")
        self.refant_line_L.setFont(font3)
        self.refant_line_L.setFrameShape(QFrame.HLine)
        self.refant_line_L.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_4.addWidget(self.refant_line_L)

        self.refant_label = QLabel(self.refant_top)
        self.refant_label.setObjectName(u"refant_label")
        self.refant_label.setFont(font2)
        self.refant_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_4.addWidget(self.refant_label)

        self.refant_line_R = QFrame(self.refant_top)
        self.refant_line_R.setObjectName(u"refant_line_R")
        self.refant_line_R.setFrameShape(QFrame.HLine)
        self.refant_line_R.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_4.addWidget(self.refant_line_R)


        self.verticalLayout_4.addWidget(self.refant_top)

        self.refant_bottom = QWidget(self.refantbox)
        self.refant_bottom.setObjectName(u"refant_bottom")
        self.gridLayout_6 = QGridLayout(self.refant_bottom)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setVerticalSpacing(10)
        self.centrant_lbl = QLabel(self.refant_bottom)
        self.centrant_lbl.setObjectName(u"centrant_lbl")
        self.centrant_lbl.setFont(font1)

        self.gridLayout_6.addWidget(self.centrant_lbl, 2, 0, 1, 1)

        self.centrant_chck = QCheckBox(self.refant_bottom)
        self.centrant_chck.setObjectName(u"centrant_chck")

        self.gridLayout_6.addWidget(self.centrant_chck, 2, 1, 1, 1)

        self.refant_lbl = QLabel(self.refant_bottom)
        self.refant_lbl.setObjectName(u"refant_lbl")
        self.refant_lbl.setFont(font1)

        self.gridLayout_6.addWidget(self.refant_lbl, 0, 0, 1, 1)

        self.priorant_lbl = QLabel(self.refant_bottom)
        self.priorant_lbl.setObjectName(u"priorant_lbl")
        self.priorant_lbl.setFont(font1)

        self.gridLayout_6.addWidget(self.priorant_lbl, 1, 0, 1, 1)

        self.maxrefantscans_lbl = QLabel(self.refant_bottom)
        self.maxrefantscans_lbl.setObjectName(u"maxrefantscans_lbl")
        self.maxrefantscans_lbl.setFont(font1)

        self.gridLayout_6.addWidget(self.maxrefantscans_lbl, 3, 0, 1, 1)

        self.maxrefantscans_line = QLineEdit(self.refant_bottom)
        self.maxrefantscans_line.setObjectName(u"maxrefantscans_line")

        self.gridLayout_6.addWidget(self.maxrefantscans_line, 3, 1, 1, 2)

        self.priorant_line = QLineEdit(self.refant_bottom)
        self.priorant_line.setObjectName(u"priorant_line")

        self.gridLayout_6.addWidget(self.priorant_line, 1, 1, 1, 2)

        self.refant_line = QLineEdit(self.refant_bottom)
        self.refant_line.setObjectName(u"refant_line")

        self.gridLayout_6.addWidget(self.refant_line, 0, 1, 1, 2)

        self.gridLayout_6.setRowStretch(0, 1)
        self.gridLayout_6.setRowStretch(1, 1)
        self.gridLayout_6.setRowStretch(2, 1)
        self.gridLayout_6.setRowStretch(3, 1)
        self.gridLayout_6.setColumnStretch(0, 3)
        self.gridLayout_6.setColumnStretch(1, 8)

        self.verticalLayout_4.addWidget(self.refant_bottom)


        self.verticalLayout_8.addWidget(self.refantbox)

        self.fringebox = QGroupBox(self.scrollAreaWidgetContents)
        self.fringebox.setObjectName(u"fringebox")
        self.fringebox.setFont(font1)
        self.fringebox.setAlignment(Qt.AlignCenter)
        self.verticalLayout_5 = QVBoxLayout(self.fringebox)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.fringe_top = QWidget(self.fringebox)
        self.fringe_top.setObjectName(u"fringe_top")
        self.horizontalLayout_5 = QHBoxLayout(self.fringe_top)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.fringe_line_L = QFrame(self.fringe_top)
        self.fringe_line_L.setObjectName(u"fringe_line_L")
        self.fringe_line_L.setFrameShape(QFrame.HLine)
        self.fringe_line_L.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_5.addWidget(self.fringe_line_L)

        self.fringe_label = QLabel(self.fringe_top)
        self.fringe_label.setObjectName(u"fringe_label")
        self.fringe_label.setFont(font2)
        self.fringe_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_5.addWidget(self.fringe_label)

        self.fringe_line_R = QFrame(self.fringe_top)
        self.fringe_line_R.setObjectName(u"fringe_line_R")
        self.fringe_line_R.setFrameShape(QFrame.HLine)
        self.fringe_line_R.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_5.addWidget(self.fringe_line_R)


        self.verticalLayout_5.addWidget(self.fringe_top)

        self.fringe_bottom = QWidget(self.fringebox)
        self.fringe_bottom.setObjectName(u"fringe_bottom")
        self.gridLayout_7 = QGridLayout(self.fringe_bottom)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setVerticalSpacing(10)
        self.solint_line = QLineEdit(self.fringe_bottom)
        self.solint_line.setObjectName(u"solint_line")

        self.gridLayout_7.addWidget(self.solint_line, 0, 1, 1, 1)

        self.solint_lbl = QLabel(self.fringe_bottom)
        self.solint_lbl.setObjectName(u"solint_lbl")
        self.solint_lbl.setFont(font1)

        self.gridLayout_7.addWidget(self.solint_lbl, 0, 0, 1, 1)

        self.minsolint_lbl = QLabel(self.fringe_bottom)
        self.minsolint_lbl.setObjectName(u"minsolint_lbl")
        self.minsolint_lbl.setFont(font1)

        self.gridLayout_7.addWidget(self.minsolint_lbl, 1, 0, 1, 1)

        self.minsolint_line = QLineEdit(self.fringe_bottom)
        self.minsolint_line.setObjectName(u"minsolint_line")

        self.gridLayout_7.addWidget(self.minsolint_line, 1, 1, 1, 1)

        self.maxsolint_line = QLineEdit(self.fringe_bottom)
        self.maxsolint_line.setObjectName(u"maxsolint_line")

        self.gridLayout_7.addWidget(self.maxsolint_line, 2, 1, 1, 1)

        self.maxsolint_lbl = QLabel(self.fringe_bottom)
        self.maxsolint_lbl.setObjectName(u"maxsolint_lbl")
        self.maxsolint_lbl.setFont(font1)

        self.gridLayout_7.addWidget(self.maxsolint_lbl, 2, 0, 1, 1)

        self.gridLayout_7.setColumnStretch(0, 3)
        self.gridLayout_7.setColumnStretch(1, 8)

        self.verticalLayout_5.addWidget(self.fringe_bottom)


        self.verticalLayout_8.addWidget(self.fringebox)

        self.exportbox = QGroupBox(self.scrollAreaWidgetContents)
        self.exportbox.setObjectName(u"exportbox")
        self.exportbox.setFont(font1)
        self.exportbox.setAlignment(Qt.AlignCenter)
        self.verticalLayout_6 = QVBoxLayout(self.exportbox)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.export_top = QWidget(self.exportbox)
        self.export_top.setObjectName(u"export_top")
        self.horizontalLayout_6 = QHBoxLayout(self.export_top)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.export_line_L = QFrame(self.export_top)
        self.export_line_L.setObjectName(u"export_line_L")
        self.export_line_L.setFrameShape(QFrame.HLine)
        self.export_line_L.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_6.addWidget(self.export_line_L)

        self.export_label = QLabel(self.export_top)
        self.export_label.setObjectName(u"export_label")
        self.export_label.setFont(font2)
        self.export_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.export_label)

        self.export_line_R = QFrame(self.export_top)
        self.export_line_R.setObjectName(u"export_line_R")
        self.export_line_R.setFrameShape(QFrame.HLine)
        self.export_line_R.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_6.addWidget(self.export_line_R)


        self.verticalLayout_6.addWidget(self.export_top)

        self.export_bottom = QWidget(self.exportbox)
        self.export_bottom.setObjectName(u"export_bottom")
        self.gridLayout_8 = QGridLayout(self.export_bottom)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setVerticalSpacing(10)
        self.chanout_lbl = QLabel(self.export_bottom)
        self.chanout_lbl.setObjectName(u"chanout_lbl")
        self.chanout_lbl.setFont(font1)

        self.gridLayout_8.addWidget(self.chanout_lbl, 0, 0, 1, 1)

        self.chanout_line = QComboBox(self.export_bottom)
        self.chanout_line.setObjectName(u"chanout_line")

        self.gridLayout_8.addWidget(self.chanout_line, 0, 1, 1, 1)

        self.edgeflag_lbl = QLabel(self.export_bottom)
        self.edgeflag_lbl.setObjectName(u"edgeflag_lbl")
        self.edgeflag_lbl.setFont(font1)

        self.gridLayout_8.addWidget(self.edgeflag_lbl, 1, 0, 1, 1)

        self.edgeflag_line = QLineEdit(self.export_bottom)
        self.edgeflag_line.setObjectName(u"edgeflag_line")

        self.gridLayout_8.addWidget(self.edgeflag_line, 1, 1, 1, 1)

        self.gridLayout_8.setColumnStretch(0, 3)
        self.gridLayout_8.setColumnStretch(1, 8)

        self.verticalLayout_6.addWidget(self.export_bottom)


        self.verticalLayout_8.addWidget(self.exportbox)

        self.plotbox = QGroupBox(self.scrollAreaWidgetContents)
        self.plotbox.setObjectName(u"plotbox")
        self.plotbox.setFont(font1)
        self.plotbox.setAlignment(Qt.AlignCenter)
        self.verticalLayout_7 = QVBoxLayout(self.plotbox)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.plot_top = QWidget(self.plotbox)
        self.plot_top.setObjectName(u"plot_top")
        self.horizontalLayout_7 = QHBoxLayout(self.plot_top)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.plot_line_L = QFrame(self.plot_top)
        self.plot_line_L.setObjectName(u"plot_line_L")
        self.plot_line_L.setFrameShape(QFrame.HLine)
        self.plot_line_L.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_7.addWidget(self.plot_line_L)

        self.plot_label = QLabel(self.plot_top)
        self.plot_label.setObjectName(u"plot_label")
        self.plot_label.setFont(font2)
        self.plot_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_7.addWidget(self.plot_label)

        self.plot_line_R = QFrame(self.plot_top)
        self.plot_line_R.setObjectName(u"plot_line_R")
        self.plot_line_R.setFrameShape(QFrame.HLine)
        self.plot_line_R.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_7.addWidget(self.plot_line_R)


        self.verticalLayout_7.addWidget(self.plot_top)

        self.plot_bottom = QWidget(self.plotbox)
        self.plot_bottom.setObjectName(u"plot_bottom")
        self.gridLayout_9 = QGridLayout(self.plot_bottom)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.gridLayout_9.setVerticalSpacing(10)
        self.interactive_lbl = QLabel(self.plot_bottom)
        self.interactive_lbl.setObjectName(u"interactive_lbl")
        self.interactive_lbl.setFont(font1)

        self.gridLayout_9.addWidget(self.interactive_lbl, 0, 0, 1, 1)

        self.interactive_chck = QCheckBox(self.plot_bottom)
        self.interactive_chck.setObjectName(u"interactive_chck")

        self.gridLayout_9.addWidget(self.interactive_chck, 0, 1, 1, 1)

        self.gridLayout_9.setColumnStretch(0, 3)
        self.gridLayout_9.setColumnStretch(1, 8)

        self.verticalLayout_7.addWidget(self.plot_bottom)


        self.verticalLayout_8.addWidget(self.plotbox)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 2, 1, 1, 2)


        self.retranslateUi(manual_window)

        QMetaObject.connectSlotsByName(manual_window)
    # setupUi

    def retranslateUi(self, manual_window):
        manual_window.setWindowTitle(QCoreApplication.translate("manual_window", u"VIPCALs", None))
        self.continue_button.setText(QCoreApplication.translate("manual_window", u"Continue", None))
        self.return_button.setText(QCoreApplication.translate("manual_window", u"Return", None))
        self.basicgroup.setTitle("")
        self.basic_label.setText(QCoreApplication.translate("manual_window", u"BASIC INPUTS", None))
        self.disk_lbl.setText(QCoreApplication.translate("manual_window", u"Disk number", None))
        self.selectfile_btn.setText(QCoreApplication.translate("manual_window", u"          Select file(s)          ", None))
        self.selectdir_btn.setText(QCoreApplication.translate("manual_window", u"Select folder", None))
        self.filepath_lbl.setText(QCoreApplication.translate("manual_window", u"Filepath", None))
        self.userno_lbl.setText(QCoreApplication.translate("manual_window", u"User number", None))
        self.output_lbl.setText(QCoreApplication.translate("manual_window", u"Output directory", None))
        self.target_lbl.setText(QCoreApplication.translate("manual_window", u"Target", None))
        self.addmore_btn.setText(QCoreApplication.translate("manual_window", u"Add more", None))
        self.more_options_btn.setText(QCoreApplication.translate("manual_window", u"More Options", None))
        self.calibbox.setTitle("")
        self.calib_label.setText(QCoreApplication.translate("manual_window", u"CALIBRATION OPTIONS", None))
        self.caliball_chck.setText("")
        self.caliball_lbl.setText(QCoreApplication.translate("manual_window", u"Calibrate all", None))
        self.calsour_lbl.setText(QCoreApplication.translate("manual_window", u"Calibrator source", None))
        self.phasref_lbl.setText(QCoreApplication.translate("manual_window", u"Phase ref calibrator", None))
        self.loadbox.setTitle("")
        self.load_label.setText(QCoreApplication.translate("manual_window", u"LOAD OPTIONS", None))
        self.freqsel_lbl.setText(QCoreApplication.translate("manual_window", u"Frequency selection", None))
        self.loadall_lbl.setText(QCoreApplication.translate("manual_window", u"Load all sources", None))
        self.subarray_chck.setText("")
        self.subarray_lbl.setText(QCoreApplication.translate("manual_window", u"Look for subarray", None))
        self.shift_lbl.setText(QCoreApplication.translate("manual_window", u"Phase center shift", None))
        self.loadall_chck.setText("")
        self.refantbox.setTitle("")
        self.refant_label.setText(QCoreApplication.translate("manual_window", u"REFERENCE ANTENNA OPTIONS", None))
        self.centrant_lbl.setText(QCoreApplication.translate("manual_window", u"Search central antennas", None))
        self.centrant_chck.setText("")
        self.refant_lbl.setText(QCoreApplication.translate("manual_window", u"Reference antenna", None))
        self.priorant_lbl.setText(QCoreApplication.translate("manual_window", u"Priority antennas", None))
        self.maxrefantscans_lbl.setText(QCoreApplication.translate("manual_window", u"Maximum scans", None))
        self.fringebox.setTitle("")
        self.fringe_label.setText(QCoreApplication.translate("manual_window", u"FRINGE FIT OPTIONS", None))
        self.solint_lbl.setText(QCoreApplication.translate("manual_window", u"Fixed solution interval", None))
        self.minsolint_lbl.setText(QCoreApplication.translate("manual_window", u"Min. solution interval", None))
        self.maxsolint_lbl.setText(QCoreApplication.translate("manual_window", u"Max. solution interval", None))
        self.exportbox.setTitle("")
        self.export_label.setText(QCoreApplication.translate("manual_window", u"EXPORT OPTIONS", None))
        self.chanout_lbl.setText(QCoreApplication.translate("manual_window", u"Channel out", None))
        self.edgeflag_lbl.setText(QCoreApplication.translate("manual_window", u"Edge flagging", None))
        self.plotbox.setTitle("")
        self.plot_label.setText(QCoreApplication.translate("manual_window", u"PLOT OPTIONS", None))
        self.interactive_lbl.setText(QCoreApplication.translate("manual_window", u"Interactive plots", None))
        self.interactive_chck.setText("")
    # retranslateUi
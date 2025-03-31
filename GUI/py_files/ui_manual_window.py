# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'manual_windowakshzJ.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QWidget)

class Ui_manual_window(object):
    def setupUi(self, manual_window):
        if not manual_window.objectName():
            manual_window.setObjectName(u"manual_window")
        manual_window.resize(871, 623)
        self.gridLayout = QGridLayout(manual_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.more_options_btn = QPushButton(manual_window)
        self.more_options_btn.setObjectName(u"more_options_btn")

        self.gridLayout.addWidget(self.more_options_btn, 1, 0, 1, 2)

        self.return_button = QPushButton(manual_window)
        self.return_button.setObjectName(u"return_button")

        self.gridLayout.addWidget(self.return_button, 4, 0, 1, 1)

        self.continue_button = QPushButton(manual_window)
        self.continue_button.setObjectName(u"continue_button")

        self.gridLayout.addWidget(self.continue_button, 4, 1, 1, 1)

        self.more_options = QGroupBox(manual_window)
        self.more_options.setObjectName(u"more_options")
        self.formLayout_2 = QFormLayout(self.more_options)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.calsour_lbl = QLabel(self.more_options)
        self.calsour_lbl.setObjectName(u"calsour_lbl")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.calsour_lbl)

        self.calsour_line = QLineEdit(self.more_options)
        self.calsour_line.setObjectName(u"calsour_line")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.calsour_line)

        self.refant_lbl = QLabel(self.more_options)
        self.refant_lbl.setObjectName(u"refant_lbl")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.refant_lbl)

        self.refant_line = QLineEdit(self.more_options)
        self.refant_line.setObjectName(u"refant_line")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.refant_line)

        self.phasref_lbl = QLabel(self.more_options)
        self.phasref_lbl.setObjectName(u"phasref_lbl")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.phasref_lbl)

        self.phasref_line = QLineEdit(self.more_options)
        self.phasref_line.setObjectName(u"phasref_line")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.phasref_line)

        self.edgeflag_lbl = QLabel(self.more_options)
        self.edgeflag_lbl.setObjectName(u"edgeflag_lbl")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.edgeflag_lbl)

        self.edgeflag_line = QLineEdit(self.more_options)
        self.edgeflag_line.setObjectName(u"edgeflag_line")

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.edgeflag_line)

        self.shift_lbl = QLabel(self.more_options)
        self.shift_lbl.setObjectName(u"shift_lbl")

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.shift_lbl)

        self.shift_line = QLineEdit(self.more_options)
        self.shift_line.setObjectName(u"shift_line")

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.shift_line)

        self.loadall_lbl = QLabel(self.more_options)
        self.loadall_lbl.setObjectName(u"loadall_lbl")

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.loadall_lbl)

        self.loadall_line = QComboBox(self.more_options)
        self.loadall_line.setObjectName(u"loadall_line")

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.loadall_line)


        self.gridLayout.addWidget(self.more_options, 2, 0, 1, 2)

        self.basic_options = QGroupBox(manual_window)
        self.basic_options.setObjectName(u"basic_options")
        self.gridLayout_2 = QGridLayout(self.basic_options)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.filepath_line = QLineEdit(self.basic_options)
        self.filepath_line.setObjectName(u"filepath_line")

        self.gridLayout_2.addWidget(self.filepath_line, 2, 1, 1, 1)

        self.disk_line = QLineEdit(self.basic_options)
        self.disk_line.setObjectName(u"disk_line")

        self.gridLayout_2.addWidget(self.disk_line, 1, 1, 1, 2)

        self.userno_lbl = QLabel(self.basic_options)
        self.userno_lbl.setObjectName(u"userno_lbl")

        self.gridLayout_2.addWidget(self.userno_lbl, 0, 0, 1, 1)

        self.filepath_lbl = QLabel(self.basic_options)
        self.filepath_lbl.setObjectName(u"filepath_lbl")

        self.gridLayout_2.addWidget(self.filepath_lbl, 2, 0, 1, 1)

        self.output_lbl = QLabel(self.basic_options)
        self.output_lbl.setObjectName(u"output_lbl")

        self.gridLayout_2.addWidget(self.output_lbl, 5, 0, 1, 1)

        self.disk_lbl = QLabel(self.basic_options)
        self.disk_lbl.setObjectName(u"disk_lbl")

        self.gridLayout_2.addWidget(self.disk_lbl, 1, 0, 1, 1)

        self.userno_line = QLineEdit(self.basic_options)
        self.userno_line.setObjectName(u"userno_line")

        self.gridLayout_2.addWidget(self.userno_line, 0, 1, 1, 2)

        self.selectfile_btn = QPushButton(self.basic_options)
        self.selectfile_btn.setObjectName(u"selectfile_btn")
        self.selectfile_btn.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectfile_btn.sizePolicy().hasHeightForWidth())
        self.selectfile_btn.setSizePolicy(sizePolicy)
        self.selectfile_btn.setMaximumSize(QSize(16777215, 16777215))
        self.selectfile_btn.setSizeIncrement(QSize(0, 0))
        self.selectfile_btn.setIconSize(QSize(16, 16))

        self.gridLayout_2.addWidget(self.selectfile_btn, 2, 2, 1, 1)

        self.output_line = QLineEdit(self.basic_options)
        self.output_line.setObjectName(u"output_line")

        self.gridLayout_2.addWidget(self.output_line, 5, 1, 1, 2)

        self.target_lbl = QLabel(self.basic_options)
        self.target_lbl.setObjectName(u"target_lbl")

        self.gridLayout_2.addWidget(self.target_lbl, 4, 0, 1, 1)

        self.target_line = QLineEdit(self.basic_options)
        self.target_line.setObjectName(u"target_line")

        self.gridLayout_2.addWidget(self.target_line, 4, 1, 1, 2)


        self.gridLayout.addWidget(self.basic_options, 0, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 3, 0, 1, 2)


        self.retranslateUi(manual_window)

        QMetaObject.connectSlotsByName(manual_window)
    # setupUi

    def retranslateUi(self, manual_window):
        manual_window.setWindowTitle(QCoreApplication.translate("manual_window", u"VIPCALs", None))
        self.more_options_btn.setText(QCoreApplication.translate("manual_window", u"More Options", None))
        self.return_button.setText(QCoreApplication.translate("manual_window", u"Return", None))
        self.continue_button.setText(QCoreApplication.translate("manual_window", u"Continue", None))
        self.more_options.setTitle("")
        self.calsour_lbl.setText(QCoreApplication.translate("manual_window", u"Calibrator source", None))
        self.refant_lbl.setText(QCoreApplication.translate("manual_window", u"Reference antenna", None))
        self.phasref_lbl.setText(QCoreApplication.translate("manual_window", u"Phase ref calibrator", None))
        self.edgeflag_lbl.setText(QCoreApplication.translate("manual_window", u"Edge flagging", None))
        self.shift_lbl.setText(QCoreApplication.translate("manual_window", u"Phase center shift", None))
        self.loadall_lbl.setText(QCoreApplication.translate("manual_window", u"Load all sources", None))
        self.basic_options.setTitle(QCoreApplication.translate("manual_window", u"Introduce your inputs:", None))
        self.userno_lbl.setText(QCoreApplication.translate("manual_window", u"User number", None))
        self.filepath_lbl.setText(QCoreApplication.translate("manual_window", u"Filepath", None))
        self.output_lbl.setText(QCoreApplication.translate("manual_window", u"Output directory", None))
        self.disk_lbl.setText(QCoreApplication.translate("manual_window", u"Disk number", None))
        self.selectfile_btn.setText(QCoreApplication.translate("manual_window", u"          Select file          ", None))
        self.target_lbl.setText(QCoreApplication.translate("manual_window", u"Target", None))
    # retranslateUi


# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'json_windowgUVtrs.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QPushButton,
    QSizePolicy, QWidget, QLabel, QLineEdit, QSpacerItem, QVBoxLayout, QHBoxLayout,
    QFrame)

class Ui_JSON_window(object):
    def setupUi(self, JSON_window):
        if not JSON_window.objectName():
            JSON_window.setObjectName(u"JSON_window")
        JSON_window.resize(628, 405)
        self.gridLayout = QGridLayout(JSON_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.return_button = QPushButton(JSON_window)
        self.return_button.setObjectName(u"return_button")
        font = QFont()
        font.setPointSize(10)
        self.return_button.setFont(font)

        self.gridLayout.addWidget(self.return_button, 1, 0, 1, 1)

        self.continue_button = QPushButton(JSON_window)
        self.continue_button.setObjectName(u"continue_button")
        self.continue_button.setFont(font)

        self.gridLayout.addWidget(self.continue_button, 1, 1, 1, 1)

        self.jsongroup = QGroupBox(JSON_window)
        self.jsongroup.setObjectName(u"jsongroup")
        self.verticalLayout = QVBoxLayout(self.jsongroup)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.json_top = QWidget(self.jsongroup)
        self.json_top.setObjectName(u"json_top")
        self.horizontalLayout = QHBoxLayout(self.json_top)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.json_line_L = QFrame(self.json_top)
        self.json_line_L.setObjectName(u"json_line_L")
        self.json_line_L.setFrameShape(QFrame.HLine)
        self.json_line_L.setFrameShadow(QFrame.Raised)

        self.horizontalLayout.addWidget(self.json_line_L)

        self.label_2 = QLabel(self.json_top)
        self.label_2.setObjectName(u"label_2")
        font1 = QFont()
        font1.setPointSize(12)
        self.label_2.setFont(font1)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.label_2)

        self.json_line_R = QFrame(self.json_top)
        self.json_line_R.setObjectName(u"json_line_R")
        self.json_line_R.setFrameShape(QFrame.HLine)
        self.json_line_R.setFrameShadow(QFrame.Raised)

        self.horizontalLayout.addWidget(self.json_line_R)


        self.verticalLayout.addWidget(self.json_top)

        self.json_bottom = QWidget(self.jsongroup)
        self.json_bottom.setObjectName(u"json_bottom")
        self.gridLayout_2 = QGridLayout(self.json_bottom)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.selectfile_lbl = QLabel(self.json_bottom)
        self.selectfile_lbl.setObjectName(u"selectfile_lbl")
        font2 = QFont()
        font2.setPointSize(11)
        self.selectfile_lbl.setFont(font2)

        self.gridLayout_2.addWidget(self.selectfile_lbl, 0, 0, 1, 1)

        self.selectfile_line = QLineEdit(self.json_bottom)
        self.selectfile_line.setObjectName(u"selectfile_line")

        self.gridLayout_2.addWidget(self.selectfile_line, 0, 1, 1, 1)

        self.selectfile_btn = QPushButton(self.json_bottom)
        self.selectfile_btn.setObjectName(u"selectfile_btn")
        self.selectfile_btn.setFont(font)

        self.gridLayout_2.addWidget(self.selectfile_btn, 0, 2, 1, 1)

        self.vspacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_2.addItem(self.vspacer, 1, 0, 1, 3)

        self.gridLayout_2.setColumnStretch(0, 3)
        self.gridLayout_2.setColumnStretch(1, 7)
        self.gridLayout_2.setColumnStretch(2, 3)

        self.verticalLayout.addWidget(self.json_bottom)


        self.gridLayout.addWidget(self.jsongroup, 0, 0, 1, 2)


        self.retranslateUi(JSON_window)

        QMetaObject.connectSlotsByName(JSON_window)
    # setupUi

    def retranslateUi(self, JSON_window):
        JSON_window.setWindowTitle(QCoreApplication.translate("JSON_window", u"VIPCALs", None))
        self.return_button.setText(QCoreApplication.translate("JSON_window", u"Return", None))
        self.continue_button.setText(QCoreApplication.translate("JSON_window", u"Continue", None))
        self.jsongroup.setTitle("")
        self.label_2.setText(QCoreApplication.translate("JSON_window", u"JSON FILE", None))
        self.selectfile_lbl.setText(QCoreApplication.translate("JSON_window", u"Filepath", None))
        self.selectfile_btn.setText(QCoreApplication.translate("JSON_window", u"Select file", None))
    # retranslateUi


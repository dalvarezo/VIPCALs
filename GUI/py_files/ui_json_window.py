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
    QSizePolicy, QWidget, QLabel, QLineEdit, QSpacerItem)

class Ui_JSON_window(object):
    def setupUi(self, JSON_window):
        if not JSON_window.objectName():
            JSON_window.setObjectName(u"JSON_window")
        JSON_window.resize(441, 297)
        self.gridLayout = QGridLayout(JSON_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.inputs_box = QGroupBox(JSON_window)
        self.inputs_box.setObjectName(u"inputs")

        self.gridLayout.addWidget(self.inputs_box, 0, 0, 1, 2)

        self.return_button = QPushButton(JSON_window)
        self.return_button.setObjectName(u"return_button")

        self.gridLayout.addWidget(self.return_button, 2, 0, 1, 1)

        self.continue_button = QPushButton(JSON_window)
        self.continue_button.setObjectName(u"continue_button")

        self.gridLayout.addWidget(self.continue_button, 2, 1, 1, 1)

        self.gridLayout_2 = QGridLayout(self.inputs_box)
        self.gridLayout_2.setObjectName(u"gridLayout_2")


        self.filepath_lbl = QLabel(self.inputs_box)
        self.filepath_lbl.setObjectName(u"filepath_lbl")
        self.gridLayout_2.addWidget(self.filepath_lbl, 0, 0, 1, 1)

        self.filepath_line = QLineEdit(self.inputs_box)
        self.filepath_line.setObjectName(u"filepath_line")

        self.gridLayout_2.addWidget(self.filepath_line, 0, 1, 1, 1)

        self.selectfile_btn = QPushButton(self.inputs_box)
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

        self.selectfile_btn.setFixedWidth(150)

        self.gridLayout_2.addWidget(self.selectfile_btn, 0, 2, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 2)


        self.retranslateUi(JSON_window)

        QMetaObject.connectSlotsByName(JSON_window)
    # setupUi

    def retranslateUi(self, JSON_window):
        JSON_window.setWindowTitle(QCoreApplication.translate("JSON_window", u"VIPCALs", None))
        self.inputs_box.setTitle(QCoreApplication.translate("JSON_window", u"Introduce your inputs:", None))
        self.return_button.setText(QCoreApplication.translate("JSON_window", u"Return", None))
        self.continue_button.setText(QCoreApplication.translate("JSON_window", u"Continue", None))
        self.filepath_lbl.setText(QCoreApplication.translate("JSON_window", u"Filepath", None))
        self.selectfile_btn.setText(QCoreApplication.translate("JSON_window", u"        Select file        ", None))

    # retranslateUi


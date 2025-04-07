# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_windowjNQnUe.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QMetaObject, Qt)
from PySide6.QtGui import (QFont)
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QLabel,
    QPushButton, QSizePolicy, QWidget)


class Ui_main_window(object):
    def setupUi(self, main_window):
        if not main_window.objectName():
            main_window.setObjectName(u"main_window")
        main_window.resize(553, 338)
        self.gridLayout = QGridLayout(main_window)
        self.gridLayout.setObjectName(u"gridLayout")

        self.groupBox = QGroupBox(main_window)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.groupBox.setTitle("")  # Remove default title
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")

        # Custom styled QLabel to replace title
        self.title_label = QLabel(self.groupBox)
        self.title_label.setObjectName("title_label")
        self.title_label.setText('<span style="font-size:32pt; font-weight:600;">VIPCALs</span> <span style="font-size:18pt;"> v0.1</span>')
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gridLayout_2.addWidget(self.title_label, 0, 0, 1, 2)

        self.man_input_btn = QPushButton(self.groupBox)
        self.man_input_btn.setObjectName(u"man_input_btn")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy.setHeightForWidth(self.man_input_btn.sizePolicy().hasHeightForWidth())
        self.man_input_btn.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(16)
        self.man_input_btn.setFont(font)

        self.gridLayout_2.addWidget(self.man_input_btn, 1, 0, 1, 1)

        self.JSON_input_btn = QPushButton(self.groupBox)
        self.JSON_input_btn.setObjectName(u"JSON_input_btn")
        sizePolicy.setHeightForWidth(self.JSON_input_btn.sizePolicy().hasHeightForWidth())
        self.JSON_input_btn.setSizePolicy(sizePolicy)
        self.JSON_input_btn.setFont(font)

        self.gridLayout_2.addWidget(self.JSON_input_btn, 1, 1, 1, 1)

        #self.help_btn = QPushButton(self.groupBox)
        #self.help_btn.setObjectName(u"help_btn")
        #sizePolicy.setHeightForWidth(self.help_btn.sizePolicy().hasHeightForWidth())
        #self.help_btn.setSizePolicy(sizePolicy)
        #self.help_btn.setFont(font)

        #self.gridLayout_2.addWidget(self.help_btn, 2, 0, 1, 1)

        #self.exit_btn = QPushButton(self.groupBox)
        #self.exit_btn.setObjectName(u"exit_btn")
        #sizePolicy.setHeightForWidth(self.exit_btn.sizePolicy().hasHeightForWidth())
        #self.exit_btn.setSizePolicy(sizePolicy)
        #self.exit_btn.setFont(font)

        #self.gridLayout_2.addWidget(self.exit_btn, 2, 1, 1, 1)

        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.retranslateUi(main_window)
        QMetaObject.connectSlotsByName(main_window)

    def retranslateUi(self, main_window):
        main_window.setWindowTitle(QCoreApplication.translate("main_window", u"VIPCALs", None))
        self.man_input_btn.setText(QCoreApplication.translate("main_window", u"Manual input", None))
        self.JSON_input_btn.setText(QCoreApplication.translate("main_window", u"JSON input", None))
        #self.help_btn.setText(QCoreApplication.translate("main_window", u"Help", None))
        #self.exit_btn.setText(QCoreApplication.translate("main_window", u"Exit", None))

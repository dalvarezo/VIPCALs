# -*- coding: utf-8 -*-
     #   self.title_label.setText('<span style="font-size:44pt; font-weight:600;">VIPCALs</span> <span style="font-size:22pt;"> v0.1</span>')
################################################################################
## Form generated from reading UI file 'main_windowjNQnUe.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_main_window(object):
    def setupUi(self, main_window):
        if not main_window.objectName():
            main_window.setObjectName(u"main_window")
        #main_window.resize(800, 208)
        self.gridLayout = QGridLayout(main_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.groupBox = QGroupBox(main_window)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.widget = QWidget(self.groupBox)
        self.widget.setObjectName(u"widget")
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        #self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        #self.verticalLayout.setSpacing(15)

        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(44)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)


        self.gridLayout_2.addWidget(self.widget, 0, 0, 1, 2)

        self.man_input_btn = QPushButton(self.groupBox)
        self.man_input_btn.setObjectName(u"man_input_btn")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.man_input_btn.sizePolicy().hasHeightForWidth())
        self.man_input_btn.setSizePolicy(sizePolicy)
        self.man_input_btn.setMinimumSize(QSize(0, 100))
        font1 = QFont()
        font1.setPointSize(16)
        self.man_input_btn.setFont(font1)

        self.gridLayout_2.addWidget(self.man_input_btn, 1, 0, 1, 1)

        self.JSON_input_btn = QPushButton(self.groupBox)
        self.JSON_input_btn.setObjectName(u"JSON_input_btn")
        sizePolicy.setHeightForWidth(self.JSON_input_btn.sizePolicy().hasHeightForWidth())
        self.JSON_input_btn.setSizePolicy(sizePolicy)
        self.JSON_input_btn.setMinimumSize(QSize(0, 100))
        self.JSON_input_btn.setFont(font1)

        self.gridLayout_2.addWidget(self.JSON_input_btn, 1, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 2, 0, 1, 2)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)


        self.retranslateUi(main_window)

        QMetaObject.connectSlotsByName(main_window)
    # setupUi

    def retranslateUi(self, main_window):
        main_window.setWindowTitle(QCoreApplication.translate("main_window", u"VIPCALs", None))
        self.groupBox.setTitle("")
        self.label.setText("<span style='font-size:48pt; font-weight:bold; color: color:#AAAAAA;'>VIPCALs</span>"
                   "<br><span style='font-size:20pt; color:#AAAAAA;'>v0.3.5</span>")

        self.man_input_btn.setText(QCoreApplication.translate("main_window", u"Manual input", None))
        self.JSON_input_btn.setText(QCoreApplication.translate("main_window", u"JSON input", None))
    # retranslateUi

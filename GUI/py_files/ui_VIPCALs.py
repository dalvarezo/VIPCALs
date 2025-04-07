# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'VIPCALsSxSpve.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenuBar,
    QSizePolicy, QStatusBar, QWidget)

class Ui_VIPCALs(object):
    def setupUi(self, VIPCALs):
        if not VIPCALs.objectName():
            VIPCALs.setObjectName(u"VIPCALs")

        # Set initial window size with 1:3 aspect ratio (height:width)
        initial_width = 900
        initial_height = int(initial_width / 3.33)
        VIPCALs.resize(initial_width, initial_height)
        
        self.centralwidget = QWidget(VIPCALs)
        self.centralwidget.setObjectName(u"centralwidget")

        # Allow expansion
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.centralwidget.setSizePolicy(sizePolicy)
        
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        VIPCALs.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(VIPCALs)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        VIPCALs.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(VIPCALs)
        self.statusbar.setObjectName(u"statusbar")
        VIPCALs.setStatusBar(self.statusbar)

        self.retranslateUi(VIPCALs)

        QMetaObject.connectSlotsByName(VIPCALs)
    # setupUi

    def retranslateUi(self, VIPCALs):
        VIPCALs.setWindowTitle(QCoreApplication.translate("VIPCALs", u"VIPCALs", None))
    # retranslateUi


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
    QSizePolicy, QWidget)

class Ui_JSON_window(object):
    def setupUi(self, JSON_window):
        if not JSON_window.objectName():
            JSON_window.setObjectName(u"JSON_window")
        JSON_window.resize(441, 297)
        self.gridLayout = QGridLayout(JSON_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.groupBox = QGroupBox(JSON_window)
        self.groupBox.setObjectName(u"groupBox")

        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.return_button = QPushButton(JSON_window)
        self.return_button.setObjectName(u"return_button")

        self.gridLayout.addWidget(self.return_button, 1, 0, 1, 1)


        self.retranslateUi(JSON_window)

        QMetaObject.connectSlotsByName(JSON_window)
    # setupUi

    def retranslateUi(self, JSON_window):
        JSON_window.setWindowTitle(QCoreApplication.translate("JSON_window", u"VIPCALs", None))
        self.groupBox.setTitle(QCoreApplication.translate("JSON_window", u"Nothing here for now", None))
        self.return_button.setText(QCoreApplication.translate("JSON_window", u"Return", None))
    # retranslateUi


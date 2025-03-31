# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'run_windowCNStuK.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QPushButton, QSizePolicy,
    QTextEdit, QWidget)

class Ui_run_window(object):
    def setupUi(self, run_window):
        if not run_window.objectName():
            run_window.setObjectName(u"run_window")
        run_window.resize(777, 602)
        self.gridLayout = QGridLayout(run_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.return_btn = QPushButton(run_window)
        self.return_btn.setObjectName(u"return_btn")

        self.gridLayout.addWidget(self.return_btn, 1, 0, 1, 1)

        self.plots_btn = QPushButton(run_window)
        self.plots_btn.setObjectName(u"plots_btn")

        self.gridLayout.addWidget(self.plots_btn, 1, 1, 1, 1)

        self.text_output = QTextEdit(run_window)
        self.text_output.setObjectName(u"text_output")

        self.gridLayout.addWidget(self.text_output, 0, 0, 1, 2)


        self.retranslateUi(run_window)

        QMetaObject.connectSlotsByName(run_window)
    # setupUi

    def retranslateUi(self, run_window):
        run_window.setWindowTitle(QCoreApplication.translate("run_window", u"VIPCALs", None))
        self.return_btn.setText(QCoreApplication.translate("run_window", u"Return", None))
        self.plots_btn.setText(QCoreApplication.translate("run_window", u"Examine plots", None))
    # retranslateUi


# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'help_windowAOjmjO.ui'
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
    QSizePolicy, QTextBrowser, QWidget)

class Ui_help_window(object):
    def setupUi(self, help_window):
        if not help_window.objectName():
            help_window.setObjectName(u"help_window")
        help_window.resize(400, 300)
        self.gridLayout = QGridLayout(help_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.groupBox = QGroupBox(help_window)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.textBrowser = QTextBrowser(self.groupBox)
        self.textBrowser.setObjectName(u"textBrowser")

        self.gridLayout_2.addWidget(self.textBrowser, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 2)

        self.return_button = QPushButton(help_window)
        self.return_button.setObjectName(u"return_button")

        self.gridLayout.addWidget(self.return_button, 1, 0, 1, 2)


        self.retranslateUi(help_window)

        QMetaObject.connectSlotsByName(help_window)
    # setupUi

    def retranslateUi(self, help_window):
        help_window.setWindowTitle(QCoreApplication.translate("help_window", u"VIPCALs", None))
        self.groupBox.setTitle(QCoreApplication.translate("help_window", u"HELP:", None))
        self.textBrowser.setHtml(QCoreApplication.translate("help_window", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Ubuntu'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Hello</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.return_button.setText(QCoreApplication.translate("help_window", u"Return", None))
    # retranslateUi


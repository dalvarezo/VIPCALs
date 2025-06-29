# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plots_windowdwRifH.ui'
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

class Ui_plots_window(object):
    def setupUi(self, plots_window):
        if not plots_window.objectName():
            plots_window.setObjectName(u"plots_window")
        plots_window.resize(789, 599)
        self.gridLayout = QGridLayout(plots_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.return_btn = QPushButton(plots_window)
        self.return_btn.setObjectName(u"return_btn")

        self.gridLayout.addWidget(self.return_btn, 2, 0, 1, 1)

        self.groupBox = QGroupBox(plots_window)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.vplot_btn = QPushButton(self.groupBox)
        self.vplot_btn.setObjectName(u"vplot_btn")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.vplot_btn.sizePolicy().hasHeightForWidth())
        self.vplot_btn.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.vplot_btn, 2, 0, 1, 1)

        self.possm_cal_btn = QPushButton(self.groupBox)
        self.possm_cal_btn.setObjectName(u"possm_cal_btn")
        sizePolicy.setHeightForWidth(self.possm_cal_btn.sizePolicy().hasHeightForWidth())
        self.possm_cal_btn.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.possm_cal_btn, 0, 1, 1, 1)

        self.possm_uncal_btn = QPushButton(self.groupBox)
        self.possm_uncal_btn.setObjectName(u"possm_uncal_btn")
        sizePolicy.setHeightForWidth(self.possm_uncal_btn.sizePolicy().hasHeightForWidth())
        self.possm_uncal_btn.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.possm_uncal_btn, 0, 0, 1, 1)

        self.uvplot_btn = QPushButton(self.groupBox)
        self.uvplot_btn.setObjectName(u"uvplot_btn")
        sizePolicy.setHeightForWidth(self.uvplot_btn.sizePolicy().hasHeightForWidth())
        self.uvplot_btn.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.uvplot_btn, 2, 1, 1, 1)


        self.gridLayout.addWidget(self.groupBox, 1, 0, 1, 1)


        self.retranslateUi(plots_window)

        QMetaObject.connectSlotsByName(plots_window)
    # setupUi

    def retranslateUi(self, plots_window):
        plots_window.setWindowTitle(QCoreApplication.translate("plots_window", u"VIPCALs", None))
        self.return_btn.setText(QCoreApplication.translate("plots_window", u"Return", None))
        self.groupBox.setTitle("")
        self.vplot_btn.setText(QCoreApplication.translate("plots_window", u"VPLOT", None))
        self.possm_cal_btn.setText(QCoreApplication.translate("plots_window", u"POSSM_CAL", None))
        self.possm_uncal_btn.setText(QCoreApplication.translate("plots_window", u"POSSM_UNCAL", None))
        self.uvplot_btn.setText(QCoreApplication.translate("plots_window", u"UVPLOT", None))
    # retranslateUi


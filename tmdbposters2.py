#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from sys import argv, exit
from PyQt4 import QtCore, QtGui, uic, Qt
from PyQt4.QtCore import QThread

from os import environ
from urllib import urlretrieve as download
from json import loads
import requests

import imagesize

import time

mainwindow = '/home/manuel/fetchpostergui/mainmenu.ui'
form_class = uic.loadUiType(mainwindow)[0]

class MyThread(QThread):
    def __init__(self):
        QThread.__init__(self)

        self.api_key = environ['TMDBAPI']
        # Available poster sizes: 'w100', 'w500', 'original'
        # See TheMovieDb API for more info
        self.poster_preview_path = '/home/manuel/.tmp'
        self.poster_preview_size = 'original'

        self.poster_download_path = '/home/manuel/Pictures'
        self.poster_download_size = 'original'

    def __del__(self):
        self.wait()

class RequestThread(MyThread):
    def run(self):
        payload = { 'api_key' : self.api_key, 'query' : self.query, 'language' : 'es' }
        self.req = requests.get('http://api.themoviedb.org/3/search/movie', params=payload)
        if self.req.status_code == 200:
            self.reqtext = loads(self.req.text)
        else:
            # if request fails do whatever
            pass

    def __del__(self):
        self.wait()

class DownloadThreadPreview(MyThread):
    def run(self):
        download('https://image.tmdb.org/t/p/%s/%s' % (self.poster_preview_size,self.poster_path), '%s/%s.jpg' %(self.poster_preview_path, self.title))

    def __del__(self):
        print 'Soy preview'
        self.wait()
        print 'Fin soy preview'

class DownloadThread(MyThread):
    def run(self):
        download('https://image.tmdb.org/t/p/%s/%s' % (self.poster_download_size,self.poster_path), '%s/%s.jpg' %(self.poster_download_path, self.title))
    def __del__(self):
        self.wait()

class ProgressBarThread(QThread):
    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        step = 0.01
        self.running = True
        while self.running:
            self.emit(QtCore.SIGNAL('increase(QString)'), '1')
            time.sleep(step)

class MyWindowClass(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.btnSearch.clicked.connect(self.btnSearch_clkd)
        self.btnDownload.clicked.connect(self.btnDownload_clkd)
        self.btnExit.clicked.connect(self.btnExit_clkd)
        self.titleList.currentIndexChanged.connect(self.RefreshForm)

        self.progressBar.setTextVisible(False)
        self.progressBar.hide()

    def btnExit_clkd(self):
        exit(0)

    def RequestProgressBar(self):
        self.MyReqProgressBar = ProgressBarThread()
        self.progressBar.setValue(0)
        self.progressBar.show()
        self.MyReqProgressBar.start()
        self.connect(self.MyReqProgressBar, QtCore.SIGNAL('increase(QString)'), self.UpdateProgressBar)
        self.connect(self.MyReqProgressBar, QtCore.SIGNAL('finished()'), self.StopProgressBar)

    def StopProgressBar(self):
        self.progressBar.hide()
        self.MyReqProgressBar.quit()

    def UpdateProgressBar(self, value):
        actual = self.progressBar.value()
        value = int(value)
        self.progressBar.setValue((actual+value)%100)

    def btnSearch_clkd(self):
        self.MyRequest = RequestThread()
        self.MyRequest.action = 1
        self.MyRequest.query = str(self.textSearch.toPlainText())
        self.MyRequest.start()
        self.connect(self.MyRequest, QtCore.SIGNAL('finished()'), self.InsertData)
        self.RequestProgressBar()

    def StopRequest(self):
        self.MyRequest.quit()

    def RefreshForm(self):
        if self.titleList.count() > 0:
            self.RequestProgressBar()
            self.SetFormValues()

    def ShowPreview(self):
        self.MyReqProgressBar.running = False
        self.MyReqProgressBar.quit()
        scene = QtGui.QGraphicsScene()
        scene.addPixmap(QtGui.QPixmap('%s/%s.jpg' % (self.MyPreviewDownload.poster_preview_path,self.MyPreviewDownload.title)))
        self.posterView.setScene(scene)
        w, h = imagesize.get('%s/%s.jpg' % (self.MyRequest.poster_preview_path,self.MyPreviewDownload.title))
        self.posterView.fitInView(QtCore.QRectF(0, 0, w, h), QtCore.Qt.KeepAspectRatio)


    def InsertData(self):
        self.titleList.clear()
        titleList = []
        for film in self.MyRequest.reqtext['results']:
            titleList.append(film['title'])
        self.titleList.addItems(titleList)
        self.SetFormValues()

    def SetFormValues(self):
        index = self.titleList.currentIndex()
        film = self.MyRequest.reqtext['results'][index]

        originalTitle = 'No hay título original'
        year = ' '
        overview = 'Sin descripción'

        if film.has_key('title'):
            originalTitle = film['title']

        if film.has_key('release_date'):
            year = '%s' % film['release_date'][0:4]

        if film.has_key('overview'):
            overview = film['overview']

        self.originalTitle.setText(originalTitle)
        self.lineYear.setText(year)
        self.textDesc.setText(overview)

        if film.has_key('poster_path'):
            self.MyPreviewDownload = DownloadThreadPreview()
            self.MyPreviewDownload.poster_path = film['poster_path']
            self.MyPreviewDownload.title = film['title']
            self.MyPreviewDownload.start()
            self.connect(self.MyPreviewDownload, QtCore.SIGNAL('finished()'), self.ShowPreview)

    def btnDownload_clkd(self):
        self.MyDownload = DownloadThread()
        index = self.titleList.currentIndex()
        self.MyDownload.poster_path = self.MyRequest.reqtext['results'][index]['poster_path']
        self.MyDownload.title = self.MyRequest.reqtext['results'][index]['title']
        self.MyDownload.start()
        self.connect(self.MyDownload, QtCore.SIGNAL('finished()'), self.DownloadComplete)
        self.RequestProgressBar()

    def DownloadComplete(self):
        self.MyReqProgressBar.running = False

app = QtGui.QApplication(argv)
MyWindow = MyWindowClass(None)
MyWindow.show()
app.exec_()

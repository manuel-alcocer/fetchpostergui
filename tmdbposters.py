#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from sys import argv, exit
from PyQt4 import QtCore, QtGui, uic, Qt

from os import environ
from urllib import urlretrieve as download
from json import loads
import requests

import imagesize

mainwindow = '/home/manuel/fetchpostergui/mainmenu.ui'
form_class = uic.loadUiType(mainwindow)[0]

class tmdbrequest:
    def __init__(self):
        self.api_key = environ['TMDBAPI']
        # Available poster sizes: 'w100', 'w500', 'original'
        # See TheMovieDb API for more info
        self.poster_preview_path = '/home/manuel/.tmp'
        self.poster_preview_size = 'original'

        self.poster_download_path = '/home/manuel/Pictures'
        self.poster_download_size = 'original'

    def MakeRequest(self, query):
        payload = { 'api_key' : self.api_key, 'query' : query, 'language' : 'es' }
        self.req = requests.get('http://api.themoviedb.org/3/search/movie', params=payload)
        self.Searching = False
        if self.req.status_code == 200:
            self.reqtext = loads(self.req.text)
        else:
            # if request fails do whatever
            pass

class MyWindowClass(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.btnSearch.clicked.connect(self.btnSearch_clkd)
        self.btnDownload.clicked.connect(self.btnDownload_clkd)
        self.btnExit.clicked.connect(self.btnExit_clkd)
        self.titleList.currentIndexChanged.connect(self.RefreshForm)

        self.api_key = environ['TMDBAPI']

        # Available poster sizes: 'w100', 'w500', 'original'
        # See TheMovieDb API for more info
        self.poster_preview_path = '/home/manuel/.tmp'
        self.poster_preview_size = 'original'

        self.poster_download_path = '/home/manuel/Pictures'
        self.poster_download_size = 'original'

    def btnExit_clkd(self):
        exit(0)

    def btnSearch_clkd(self):
        self.MakeRequest()
        self.InsertData()

    def RefreshForm(self):
        if self.titleList.count() > 0:
            self.SetFormValues(self.titleList.currentIndex())

    def InsertData(self):
        self.titleList.clear()
        titleList = []
        for film in self.reqtext['results']:
            titleList.append(film['title'])
        self.titleList.addItems(titleList)
        self.SetFormValues(self.titleList.currentIndex())

    def SetFormValues(self, index):
        film = self.reqtext['results'][index]

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
            self.PosterPreview(index)

    def PosterPreview(self, index):
        title = self.reqtext['results'][index]['title']
        poster_path = self.reqtext['results'][index]['poster_path']
        download('https://image.tmdb.org/t/p/%s/%s' % (self.poster_preview_size,poster_path), '%s/%s.jpg' %(self.poster_preview_path, title))
        scene = QtGui.QGraphicsScene()
        scene.addPixmap(QtGui.QPixmap('%s/%s.jpg' % (self.poster_preview_path,title)))
        self.posterView.setScene(scene)
        w, h = imagesize.get('%s/%s.jpg' % (self.poster_preview_path,title))
        self.posterView.fitInView(QtCore.QRectF(0, 0, w, h), QtCore.Qt.KeepAspectRatio)

    def MakeRequest(self):
        searchtext = str(self.textSearch.toPlainText())
        payload = { 'api_key' : self.api_key, 'query' : searchtext, 'language' : 'es' }
        self.req = requests.get('http://api.themoviedb.org/3/search/movie', params=payload)
        if self.req.status_code == 200:
            self.reqtext = loads(self.req.text)
        else:
            # if request fails do whatever
            pass

    def btnDownload_clkd(self):
        index = self.titleList.currentIndex()
        filmid = self.reqtext['results'][index]['id']
        poster_path = self.reqtext['results'][index]['poster_path']
        download('https://image.tmdb.org/t/p/%s/%s' % (self.poster_download_size, poster_path), '%s/%s.jpg' %(self.poster_download_path, filmid))

app = QtGui.QApplication(argv)
MyWindow = MyWindowClass(None)
MyWindow.show()
app.exec_()

#!/usr/bin/env python
import numpy as np
from Particle import *
import math
from PyQt5 import QtWidgets, QtCore, QtGui, QtOpenGL
import ui_for_particles
import OpenGL.GL as gl
import OpenGL.GLU as glu
import decimal
import scipy.integrate
import threading
from multiprocessing import Barrier
import time
import solvers as slv

counter = 0
class glWidget(QtWidgets.QOpenGLWidget, ui_for_particles.Ui_MainWindow):
    xRotationChanged = QtCore.pyqtSignal(int)
    yRotationChanged = QtCore.pyqtSignal(int)
    zRotationChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent, list_p, list_s, gui):
        super(glWidget, self).__init__(parent)
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0
        self.zoom = 200
        self.genl_ = 0
        self.list_of_particles = list_p
        self.list_of_solar_system = list_s
        self.ss_flag = False
        if len(self.list_of_solar_system) == 9:
            self.ss_flag = True
        self.lastPos = QtCore.QPoint()
        self.trolltechGreen = QtGui.QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
        self.trolltechBlack = QtGui.QColor.fromCmykF(0.0, 0.0, 0.0, 1.0)
        self.y_ = 0
        self.gui = gui
        self.computing_time = 0

    def add_and_visualise_particle(self):
        print('тут', len(self.list_of_particles))
        if (len(self.list_of_particles) != 0):
            print('Проверка в glWidget!!!', self.list_of_particles[0].color, self.list_of_particles[0].m, self.list_of_particles[0].x, self.list_of_particles[0].y, self.list_of_particles[0].z, self.list_of_particles[0].xv, self.list_of_particles[0].yv, self.list_of_particles[0].zv)

    def getOpenglInfo(self):
        info = """
            Vendor: {0}
            Renderer: {1}
            OpenGL Version: {2}
            Shader Version: {3}
        """.format(
            gl.glGetString(gl.GL_VENDOR),
            gl.glGetString(gl.GL_RENDERER),
            gl.glGetString(gl.GL_VERSION),
            gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION)
        )
        return info

    def minimumSizeHint(self):
        #print('minimumSizeHint')
        return QtCore.QSize(50, 50)

    def sizeHint(self):
        #print('sizeHint')
        return QtCore.QSize(self.parent().width(),self.parent().height())

    def setXRotation(self, angle):
        #print('setXRotation')
        angle = self.normalizeAngle(angle)
        if angle != self.xRot:
            self.xRot = angle
            self.xRotationChanged.emit(angle)
            self.update()

    def setYRotation(self, angle):
        #print('setYRotation')
        angle = self.normalizeAngle(angle)
        if angle != self.yRot:
            self.yRot = angle
            self.yRotationChanged.emit(angle)
            self.update()

    def setZRotation(self, angle):
        print('setZRotation')
        angle = self.normalizeAngle(angle)
        if angle != self.zRot:
            self.zRot = angle
            self.zRotationChanged.emit(angle)
            self.update()

    def initializeGL(self):
        print('initializeGL')
        print(self.getOpenglInfo())
        self.setClearColor(self.trolltechBlack)
        #self.object = self.makeObject()
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_DEPTH_TEST) # z - буфер
        gl.glEnable(gl.GL_LIGHTING) # включаем освещение
        gl.glEnable(gl.GL_LIGHT0) # включаем нулевую лампу
        gl.glEnable(gl.GL_COLOR_MATERIAL) # управление свойством материала (отражение материала)
        #gl.glColorMaterial(gl.GL_FRONT, gl.GL_SPECULAR)
        gl.glEnable(gl.GL_NORMALIZE) # нормаль единичной длины
        
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, [100,100,100,1]) # позиция нулевой лампы
        gl.glLightf(gl.GL_LIGHT0, gl.GL_CONSTANT_ATTENUATION, 0.1) # постоянная составляющая и расстояние
        gl.glLightf(gl.GL_LIGHT0, gl.GL_LINEAR_ATTENUATION, 0.05) # линейная составляющая
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPOT_DIRECTION, [0,1,1]) # положение источника света (ось конуса)
        gl.glLighti(gl.GL_LIGHT0, gl.GL_SPOT_EXPONENT, 0)
        gl.glLighti(gl.GL_LIGHT0, gl.GL_SPOT_CUTOFF, 5) # угол рассеяния луча
        gl.glShadeModel(gl.GL_SMOOTH)
        gl.glEnable(gl.GL_DEPTH_TEST) # включаем буфер глубины
        gl.glEnable(gl.GL_CULL_FACE)

    def paintGL(self):
        #print('paintGL')
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        gl.glTranslated(0.0, 0.0, -10.0)
        gl.glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
        gl.glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
        gl.glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)

        rad = self.zoom
        x_cam = rad * math.sin(self.yRot) * math.cos(self.xRot)
        y_cam = rad * math.sin(self.yRot) * math.sin(self.xRot)
        z_cam = rad * math.cos(self.yRot) 
        glu.gluLookAt(x_cam, y_cam, z_cam, 0, 0, 0, 0, 1, 0)
        #print(self.genl_)
        #self.end()
        self.visualisation_particle() #отрисовка тут
        #self.gui.computing_time_gl = time.clock() - self.gui.start_time_gl 
        #print('ВРЕМЯ', self.computing_time, self.start_time)
        #self.gui.label_time.setText(str(time.clock() - self.gui.start_time_gl))
        if (len(self.list_of_particles) > 2):
            if self.gui.comboBox.currentIndex() == 1:
                self.verlet()
            if self.gui.comboBox.currentIndex() == 0:
                self.verlet_scipy()
        if len(self.list_of_solar_system) == 9:
            if self.gui.comboBox.currentIndex() == 1:
                self.verlet_ss()
            if self.gui.comboBox.currentIndex() == 0:
                self.verlet_scipy_ss()

    def visualisation_particle(self):
        #print('visualisation_particle')
        if len(self.list_of_solar_system) == 9:
            for k in range(len(self.list_of_solar_system)):
                sphere = glu.gluNewQuadric() 
                gl.glPushMatrix()                      
                gl.glLightModelfv(gl.GL_LIGHT_MODEL_AMBIENT, self.list_of_solar_system[k].color) #цвет задаем
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, self.list_of_solar_system[k].color)
                gl.glTranslatef(self.list_of_solar_system[k].x*7, self.list_of_solar_system[k].y*7, self.list_of_solar_system[k].z*7)
                glu.gluQuadricDrawStyle(sphere, glu.GLU_FILL) 
                if k == 0:   
                    glu.gluSphere(sphere, self.list_of_solar_system[k].m / 150000.0, 16, 16) 
                if k == 1:
                    glu.gluSphere(sphere, self.list_of_solar_system[k].m * 20, 16, 16) 
                if k == 2:
                    glu.gluSphere(sphere, self.list_of_solar_system[k].m * 2, 16, 16) 
                if k == 3:
                    glu.gluSphere(sphere, self.list_of_solar_system[k].m * 1.5, 16, 16) 
                if k == 4:
                    glu.gluSphere(sphere, self.list_of_solar_system[k].m * 7, 16, 16) 
                if k == 5:
                    glu.gluSphere(sphere, self.list_of_solar_system[k].m / 30, 16, 16)
                if k == 6:
                    glu.gluSphere(sphere, self.list_of_solar_system[k].m / 12, 16, 16)
                if k == 7:
                    glu.gluSphere(sphere, self.list_of_solar_system[k].m / 2.3, 16, 16)
                if k == 8:
                    glu.gluSphere(sphere, self.list_of_solar_system[k].m / 3.2, 16, 16)
                
                gl.glTranslatef(-self.list_of_solar_system[k].x*7, -self.list_of_solar_system[k].y*7, -self.list_of_solar_system[k].z*7)
                gl.glPopMatrix() 
                glu.gluDeleteQuadric(sphere)
                self.update()
        else:
            #for l in self.general_list:
                #for k in range(len(l)):
            for k in range(len(self.list_of_particles)):
                sphere = glu.gluNewQuadric() 
                gl.glPushMatrix()                      
                gl.glLightModelfv(gl.GL_LIGHT_MODEL_AMBIENT, self.list_of_particles[k].color) #цвет задаем
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, self.list_of_particles[k].color)
                gl.glTranslatef(self.list_of_particles[k].x, self.list_of_particles[k].y, self.list_of_particles[k].z)
                glu.gluQuadricDrawStyle(sphere, glu.GLU_FILL)    
                glu.gluSphere(sphere, self.list_of_particles[k].m / 100.0, 16, 16) 
                gl.glTranslatef(-self.list_of_particles[k].x, -self.list_of_particles[k].y, -self.list_of_particles[k].z)
                gl.glPopMatrix() 
                glu.gluDeleteQuadric(sphere)
                self.update()

    def resizeGL(self, width, height):
        #print('resizeGL')
        #print('РАЗМЕР',width,height)
        side = min(width, height)
        if side < 0:
            return
        gl.glViewport((width - side) // 2, (height - side) // 2, side, side)
        gl.glMatrixMode(gl.GL_PROJECTION) # команды относятся к проектору
        gl.glLoadIdentity() # считывает текущую матрицу
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        x, y, width, height = gl.glGetDoublev(gl.GL_VIEWPORT)
        glu.gluPerspective(
            90,  # field of view in degrees
           width / float(height or 1),  # aspect ratio
            .25,  # near clipping plane
            2000,  # far clipping plane
        )      
        #gl.glOrtho(-1000.0, +1000.0, +1000.0, -1000.0, -1000.0, +1000.0)
        gl.glMatrixMode(gl.GL_MODELVIEW) #режим просмотра

    def mousePressEvent(self, event):
        #print('mousePressEvent')
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        #print('mouseMoveEvent')
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & QtCore.Qt.LeftButton:
            self.setXRotation(self.xRot + dy/100)
            self.setYRotation(self.yRot + dx/100)
        elif event.buttons() & QtCore.Qt.RightButton:
            self.setXRotation(self.xRot + 100 * dy)
            self.setZRotation(self.zRot + 100 * dx)
        self.lastPos = event.pos()

    def normalizeAngle(self, angle):
        #print('normalizeAngle')
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle

    def setClearColor(self, c):
        #print('setClearColor')
        gl.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

    def setColor(self, c):
        #print('setColor')
        gl.glColor4f(c.redF(), c.greenF(), c.blueF(), c.alphaF())

#---------------------------------methods------------------------------------------

    def verlet(self):
        start_time = time.clock()
        self.gui.paint_gl = self.gui.paint_gl + 1
        G = 6.67408e-11
       
        module = 0
        Time_ = 600000
        delta_t = 6000
        time_iter = np.linspace(0,Time_,delta_t)
        flag = 0
        n = len(self.list_of_particles)
        if n<2:
            return
        print(len(time_iter))
        t = 0
        #print('T ================== ',t)
        x_ = []
        y_ = []
        z_ = []
        x_for_opengl = []
        y_for_opengl = []
        z_for_opengl = []
        vx_n = []
        vy_n = []
        vz_n = []
        m = []
        m_for_opengl = []
        color_ = []

        ax_n = []
        ay_n = []
        az_n = []
        ax_n1 = []
        ay_n1 = []
        az_n1 = []

        del x_ [:] 
        del y_ [:]
        del z_ [:]
        del x_for_opengl [:]
        del y_for_opengl [:]
        del z_for_opengl [:]
        del vx_n [:]
        del vy_n [:]
        del vz_n [:]
        del m [:]
        del m_for_opengl [:]
        del color_ [:]

        del ax_n [:]
        del ay_n [:]
        del az_n [:]
        del ax_n1 [:]
        del ay_n1 [:]
        del az_n1 [:] 

        #print('кол-во частиц', n)
        for p1 in self.list_of_particles:
            for p2 in self.list_of_particles:
                if (math.sqrt((p2.x-p1.x)**2 + (p2.y-p1.y)**2 + (p2.z-p1.z)**2) > 0) & (math.sqrt((p2.x-p1.x)**2 + (p2.y-p1.y)**2 + (p2.z-p1.z)**2) < (p1.m + p2.m)/100):
                    if p1.m > p2.m:
                        p1.m += p2.m
                    else:
                        p1.is_active = False

        for p in self.list_of_particles:
            if p.is_active == True:
                x_.append(p.x)
                y_.append(p.y)
                z_.append(p.z)
                vx_n.append(p.xv)
                vy_n.append(p.yv)
                vz_n.append(p.zv)
                m.append(p.m)
                color_.append(p.color)  

        n_ = len(x_)
        #print('кол-во частиц = ', n_)
        k = 0
        j = 0
        for j in range(n_):
            ax_ = 0
            ay_ = 0
            az_ = 0
            for k in range(n_):
                if k != j:
                    #print('модуль', math.sqrt((x_[k]-x_[j])**2 + (y_[k]-y_[j])**2 + (z_[k]-z_[j])**2)**3, ' ',k,' ', j)
                    ax_ += m[k] * G * (x_[k] - x_[j]) / math.sqrt((x_[k]-x_[j])**2 + (y_[k]-y_[j])**2 + (z_[k]-z_[j])**2)**3
                    ay_ += m[k] * G * (y_[k] - y_[j]) / math.sqrt((x_[k]-x_[j])**2 + (y_[k]-y_[j])**2 + (z_[k]-z_[j])**2)**3
                    az_ += m[k] * G * (z_[k] - z_[j]) / math.sqrt((x_[k]-x_[j])**2 + (y_[k]-y_[j])**2 + (z_[k]-z_[j])**2)**3
            ax_n.append(ax_)
            ay_n.append(ay_)
            az_n.append(az_)
        
        x_n1 = [x_n + u_n*delta_t + 0.5*a_n*delta_t**2 for x_n,u_n,a_n in zip(x_,vx_n,ax_n)]
        y_n1 = [y_n + v_n*delta_t + 0.5*a_n*delta_t**2 for y_n,v_n,a_n in zip(y_,vy_n,ay_n)]
        z_n1 = [z_n + w_n*delta_t + 0.5*a_n*delta_t**2 for z_n,w_n,a_n in zip(z_,vz_n,az_n)]

        k = 0
        j = 0
        for j in range(n_):
            ax_ = 0
            ay_ = 0
            az_ = 0
            for k in range(n_):
                if k != j:
                    ax_ += G*m[k]* (x_n1[k]-x_n1[j]) / math.sqrt((x_n1[k]-x_n1[j])**2 + (y_n1[k]-y_n1[j])**2 + (z_n1[k]-z_n1[j])**2)**3
                    ay_ += G*m[k]* (y_n1[k]-y_n1[j]) / math.sqrt((x_n1[k]-x_n1[j])**2 + (y_n1[k]-y_n1[j])**2 + (z_n1[k]-z_n1[j])**2)**3
                    az_ += G*m[k]* (z_n1[k]-z_n1[j]) / math.sqrt((x_n1[k]-x_n1[j])**2 + (y_n1[k]-y_n1[j])**2 + (z_n1[k]-z_n1[j])**2)**3
            ax_n1.append(ax_)
            ay_n1.append(ay_)
            az_n1.append(az_)
        
        vx_n1 = [u + 0.5*(an + an1)*delta_t for u, an, an1 in zip(vx_n, ax_n, ax_n1)]
        vy_n1 = [v + 0.5*(an + an1)*delta_t for v, an, an1 in zip(vy_n, ay_n, ay_n1)]
        vz_n1 = [w + 0.5*(an + an1)*delta_t for w, an, an1 in zip(vz_n, az_n, az_n1)]

        del self.list_of_particles [:]
        for i in range(n_):
            pos_ = Coord(x_n1[i],y_n1[i],z_n1[i])
            speed_ = Speed(vx_n1[i],vy_n1[i],vz_n1[i])
            self.list_of_particles.append(Particle(pos_,speed_,m[i],color_[i]))

    def verlet_ss(self):
        G = 6.67408e-11
        x_ = []
        y_ = []
        z_ = []
        vx_n = []
        vy_n = []
        vz_n = []
        m = []
        m_for_opengl = []
        color_ = []

        ax_n = []
        ay_n = []
        az_n = []
        ax_n1 = []
        ay_n1 = []
        az_n1 = []

        del x_ [:] 
        del y_ [:]
        del z_ [:]
        del vx_n [:]
        del vy_n [:]
        del vz_n [:]
        del m [:]
        del m_for_opengl [:]
        del color_ [:]

        del ax_n [:]
        del ay_n [:]
        del az_n [:]
        del ax_n1 [:]
        del ay_n1 [:]
        del az_n1 [:] 

        n = len(self.list_of_solar_system)
        au = 149597870700/2
        earth_mass = 5.9726 * 10**24
        delta_t = 100000
        for p in self.list_of_solar_system:
            x_.append(p.x * au)
            y_.append(p.y * au)
            z_.append(p.z * au)
            vx_n.append(p.xv)
            vy_n.append(p.yv)
            vz_n.append(p.zv)
            m.append(p.m * earth_mass)
            m_for_opengl.append(p.m)
            color_.append(p.color)
        
        n_ = len(x_)
        for j in range(n_):
            #pos_ = Coord(x[j],y[j],z[j])
            ax_ = 0
            ay_ = 0
            az_ = 0
            for k in range(n_):
                if k != j:
                    #print('модуль', math.sqrt((x_[k]-x_[j])**2 + (y_[k]-y_[j])**2 + (z_[k]-z_[j])**2)**3)
                    ax_ += m[k] * G * (x_[k] - x_[j]) / math.sqrt((x_[k]-x_[j])**2 + (y_[k]-y_[j])**2 + (z_[k]-z_[j])**2)**3
                    ay_ += m[k] * G * (y_[k] - y_[j]) / math.sqrt((x_[k]-x_[j])**2 + (y_[k]-y_[j])**2 + (z_[k]-z_[j])**2)**3
                    az_ += m[k] * G * (z_[k] - z_[j]) / math.sqrt((x_[k]-x_[j])**2 + (y_[k]-y_[j])**2 + (z_[k]-z_[j])**2)**3
                ax_n.append(ax_)
                ay_n.append(ay_)
                az_n.append(az_)
        
        x_n1 = [x_n + u_n*delta_t + 0.5*a_n*delta_t**2 for x_n,u_n,a_n in zip(x_,vx_n,ax_n)]
        y_n1 = [y_n + v_n*delta_t + 0.5*a_n*delta_t**2 for y_n,v_n,a_n in zip(y_,vy_n,ay_n)]
        z_n1 = [z_n + w_n*delta_t + 0.5*a_n*delta_t**2 for z_n,w_n,a_n in zip(z_,vz_n,az_n)]

        for j in range(n_):
            ax_ = 0
            ay_ = 0
            az_ = 0
            for k in range(n_):
                if k != j:
                    ax_ += G*m[k]* (x_n1[k]-x_n1[j]) / math.sqrt((x_n1[k]-x_n1[j])**2 + (y_n1[k]-y_n1[j])**2 + (z_n1[k]-z_n1[j])**2)**3
                    ay_ += G*m[k]* (y_n1[k]-y_n1[j]) / math.sqrt((x_n1[k]-x_n1[j])**2 + (y_n1[k]-y_n1[j])**2 + (z_n1[k]-z_n1[j])**2)**3
                    az_ += G*m[k]* (z_n1[k]-z_n1[j]) / math.sqrt((x_n1[k]-x_n1[j])**2 + (y_n1[k]-y_n1[j])**2 + (z_n1[k]-z_n1[j])**2)**3
            ax_n1.append(ax_)
            ay_n1.append(ay_)
            az_n1.append(az_)
        
        vx_n1 = [u + 0.5*(an + an1)*delta_t for u, an, an1 in zip(vx_n, ax_n, ax_n1)]
        vy_n1 = [v + 0.5*(an + an1)*delta_t for v, an, an1 in zip(vy_n, ay_n, ay_n1)]
        vz_n1 = [w + 0.5*(an + an1)*delta_t for w, an, an1 in zip(vz_n, az_n, az_n1)]

        del self.list_of_solar_system [:]
        for i in range(n_):
            pos_ = Coord(x_n1[i]/au,y_n1[i]/au,z_n1[i]/au)
            speed_ = Speed(vx_n1[i],vy_n1[i],vz_n1[i])
            self.list_of_solar_system.append(Particle(pos_,speed_,m[i]/earth_mass,color_[i]))

#--------------------------------VERLET SCIPY-------------------------------------------------
    def for_scipy(self,init,t,n,mass):
        print('зашел в for_scipy')
        G = 6.67408e-11
        x_0 = []
        y_0 = []
        z_0 = []
        vx_0 = []
        vy_0 = []
        vz_0 = []
        #m = []
        color_ = []

        ax_n = []
        ay_n = []
        az_n = []
        ax_n1 = []
        ay_n1 = []
        az_n1 = []

        del x_0 [:] 
        del y_0 [:]
        del z_0 [:]
        del vx_0 [:]
        del vy_0 [:]
        del vz_0 [:]
        #del m [:]
        del color_ [:]

        del ax_n [:]
        del ay_n [:]
        del az_n [:]
        del ax_n1 [:]
        del ay_n1 [:]
        del az_n1 [:] 

        module = 0
        # if n == 9:
        #     delta_t = 100000
        #     print(delta_t)
        # else:
        #     delta_t = 6000
        #     print(delta_t)
        # flag = 0
        """n = len(self.list_of_particles)
        print('кол-во частиц', n)
        if n<2:
            return
        for p1 in self.list_of_particles:
            for p2 in self.list_of_particles:
                if (math.sqrt((p2.x-p1.x)**2 + (p2.y-p1.y)**2 + (p2.z-p1.z)**2) > 0) & (math.sqrt((p2.x-p1.x)**2 + (p2.y-p1.y)**2 + (p2.z-p1.z)**2) < (p1.m + p2.m)/100):
                    if p1.m > p2.m:
                        p1.m += p2.m
                    else:
                        p1.is_active = False"""
        for i in range(n):
            x_0.append(init[i*3])
            y_0.append(init[i*3 + 1])
            z_0.append(init[i*3 + 2])
            vx_0.append(init[i*3 + 3*n])
            vy_0.append(init[i*3 + 3*n + 1])
            vz_0.append(init[i*3 + 3*n + 2])
        result = []
        del result [:]
        n_ = n
        for i in range(n_):
            result.append(vx_0[i])
            result.append(vy_0[i])
            result.append(vz_0[i])
        #print('RESULT',len(result))
        for j in range(n_):
            ax_ = 0
            ay_ = 0
            az_ = 0
            for k in range(n_):
                if k != j:
                    #print('модуль', math.sqrt((x_[k]-x_[j])**2 + (y_[k]-y_[j])**2 + (z_[k]-z_[j])**2)**3)
                    ax_ += mass[k] * G * (x_0[k] - x_0[j]) / math.sqrt((x_0[k]-x_0[j])**2 + (y_0[k]-y_0[j])**2 + (z_0[k]-z_0[j])**2)**3
                    ay_ += mass[k] * G * (y_0[k] - y_0[j]) / math.sqrt((x_0[k]-x_0[j])**2 + (y_0[k]-y_0[j])**2 + (z_0[k]-z_0[j])**2)**3
                    az_ += mass[k] * G * (z_0[k] - z_0[j]) / math.sqrt((x_0[k]-x_0[j])**2 + (y_0[k]-y_0[j])**2 + (z_0[k]-z_0[j])**2)**3
            result.append(ax_)
            result.append(ay_)
            result.append(az_)
            #print('LEN RESULT', len(result))
        return result
    
    def verlet_scipy(self):
        #self.gui.timer.stop()
        #print('VERLET_SCIPY')
        T = 6000 #Расчетное время - шаг на самом деле это шаааааааг
        M = 2 #сколько точек 
        time_span = np.linspace(0, T, M)
        mass = []
        xyz = []
        Vxyz = []
        color_ = []
        res = []

        del mass [:]
        del xyz [:]
        del Vxyz [:]
        del color_ [:]
        del res [:]
        
        n = len(self.list_of_particles)
        #print('кол-во частиц', n)
        if n<2:
            return
        for p1 in self.list_of_particles:
            for p2 in self.list_of_particles:
                if (math.sqrt((p2.x-p1.x)**2 + (p2.y-p1.y)**2 + (p2.z-p1.z)**2) > 0) & (math.sqrt((p2.x-p1.x)**2 + (p2.y-p1.y)**2 + (p2.z-p1.z)**2) < (p1.m + p2.m)/100):
                    if p1.m > p2.m:
                        p1.m += p2.m
                    else:
                        p1.is_active = False

        for p in self.list_of_particles:
            if p.is_active == True:
                xyz.append(p.x)
                xyz.append(p.y)
                xyz.append(p.z)
                Vxyz.append(p.xv)
                Vxyz.append(p.yv)
                Vxyz.append(p.zv)
                mass.append(p.m)
                color_.append(p.color)  

        n_ = len(color_)
        init_cond = sum([list(map(float, xyz)), list(map(float, Vxyz))], [])
        #print(init_cond)
        #del res [:]
        res = scipy.integrate.odeint(self.for_scipy, init_cond, time_span, args=(n_,list(map(float,mass))))
        
        x_n1 =[]
        y_n1 =[]
        z_n1 = []
        vx_n1 =[]
        vy_n1 = []
        vz_n1 = []
        del x_n1 [:]
        del y_n1 [:]
        del z_n1 [:]
        del vx_n1 [:]
        del vy_n1 [:]
        del vz_n1 [:]
        
        #print('ПРОВЕРЯЮ',len(init_cond), n_, len(res),len(res[0]))
        #print(res)
        kk = 0 
        for i in range(1,len(res)): #от 0 до 50
            #del self.list_of_particles [:]
            for j in range(n_):# от 0 до 20
                #print(i,j*3)
                x_n1.append(res[i][j*3])
                kk = kk + 1
                #print(kk, len(init_cond), n_, len(res))
                y_n1.append(res[i][j*3+1])
                z_n1.append(res[i][j*3+2])
                vx_n1.append(res[i][j*3 + 3*n_])
                vy_n1.append(res[i][j*3 + 3*n_ + 1])
                vz_n1.append(res[i][j*3 + 3*n_ + 2])
                #print(x_n1[j],y_n1[j],z_n1[j],vx_n1[j],vy_n1[j],vz_n1[j], j)
                #pos_ = Coord(x_n1[j],y_n1[j],z_n1[j])
                #speed_ = Speed(vx_n1[j],vy_n1[j],vz_n1[j])
                #self.list_of_particles.append(Particle(pos_,speed_,mass[j],color_[j]))
                #print('рисую', len(self.list_of_particles))
            #self.visualisation_particle()
        print(len(x_n1), kk)
        #print(y_n1)
        #print(vx_n1)
        #print(vy_n1)

        del self.list_of_particles [:]
        for i in range(n_):
            #print('новый лист')
            pos_ = Coord(x_n1[i],y_n1[i],z_n1[i])
            speed_ = Speed(vx_n1[i],vy_n1[i],vz_n1[i])
            self.list_of_particles.append(Particle(pos_,speed_,mass[i],color_[i]))
        #print('НОВЫЙ ЛИСТ', len(self.list_of_particles))

    def verlet_scipy_ss(self):
        T = 100000 #Расчетное время - шаг на самом деле это шаааааааг
        M = 2 #сколько точек 
        n = len(self.list_of_solar_system)
        au = 149597870700
        earth_mass = 5.9726 * 10**24
        time_span = np.linspace(0, T, M)
        delta_t = 100000
        mass = []
        xyz = []
        Vxyz = []
        color_ = []
        res = []

        del mass [:]
        del xyz [:]
        del Vxyz [:]
        del color_ [:]
        del res [:]
        
        n = len(self.list_of_solar_system)
        for p in self.list_of_solar_system:
                xyz.append(p.x * au)
                xyz.append(p.y * au)
                xyz.append(p.z * au)
                Vxyz.append(p.xv)
                Vxyz.append(p.yv)
                Vxyz.append(p.zv)
                mass.append(p.m * earth_mass)
                color_.append(p.color)  

        n_ = len(color_)
        init_cond = sum([list(map(float, xyz)), list(map(float, Vxyz))], [])
        res = scipy.integrate.odeint(self.for_scipy, init_cond, time_span, args=(n_,list(map(float,mass))))
        
        x_n1 =[]
        y_n1 =[]
        z_n1 = []
        vx_n1 =[]
        vy_n1 = []
        vz_n1 = []
        del x_n1 [:]
        del y_n1 [:]
        del z_n1 [:]
        del vx_n1 [:]
        del vy_n1 [:]
        del vz_n1 [:]

        kk = 0 
        for i in range(1,len(res)):
            for j in range(n_):
                x_n1.append(res[i][j*3])
                kk = kk + 1
                y_n1.append(res[i][j*3+1])
                z_n1.append(res[i][j*3+2])
                vx_n1.append(res[i][j*3 + 3*n_])
                vy_n1.append(res[i][j*3 + 3*n_ + 1])
                vz_n1.append(res[i][j*3 + 3*n_ + 2])

        del self.list_of_solar_system [:]
        for i in range(n_):
            #print('новый лист')
            pos_ = Coord(x_n1[i]/au,y_n1[i]/au,z_n1[i]/au)
            speed_ = Speed(vx_n1[i],vy_n1[i],vz_n1[i])
            self.list_of_solar_system.append(Particle(pos_,speed_,mass[i]/earth_mass,color_[i]))

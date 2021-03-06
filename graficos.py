# coding=utf-8

import OpenGL
OpenGL.ERROR_ON_COPY = True
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import *
import sys, time
from OpenGL.constants import GLfloat
from OpenGL.GL.ARB.multisample import GL_MULTISAMPLE_ARB
import math
import leapmotion
import time

from PIL import Image


# Variables del contexto de OpenGL
vec4 = GLfloat_4
tStart = t0 = time.time()
frames = 0
camara_angulo_x = 90#+10
camara_angulo_y = 0#-45
ventana_pos_x  = 50
ventana_pos_y  = 50
ventana_tam_x  = 1024
ventana_tam_y  = 800
frustum_dis_del = 0.1
frustum_dis_tra = 10.0
frustum_ancho = 0.5 * frustum_dis_del
frustum_factor_escala = 0.008 / 1.05
#strings_ayuda = ["Hola"," Adios"]

# Origen de los ejes de coordenadas
origen_ejes = [-200.0,0.0,-200.0]

posiciones_baquetas = []
direcciones_baquetas = []

tiempo_transcurrido_ultimo_dato = time.time()
margen_tiempo = 0.5

# Traslación de las baterías
desplazamiento_bateria = 100
tamanio_bateria = 75
comienzo_bateria = desplazamiento_bateria - tamanio_bateria

# variable que controla el menu
menu_activo = False


def PNGtoTexture(filename):
    img = Image.open(filename)
    img_data = numpy.array(list(img.getdata()), numpy.uint8)

    texture = glGenTextures(1)
    glPixelStorei(GL_UNPACK_ALIGNMENT,1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.size[0], img.size[1], 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
    return texture

"""
Función para fijar la proyección en OpenGL
"""
def fijarProyeccion():
    ratioYX = float(ventana_tam_y) / float(ventana_tam_x)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glFrustum(-frustum_ancho, +frustum_ancho, -frustum_ancho*ratioYX, +frustum_ancho*ratioYX, +frustum_dis_del, +frustum_dis_tra)
    glTranslatef( 0.0,0.0,-0.5*(frustum_dis_del+frustum_dis_tra))
    glScalef( frustum_factor_escala, frustum_factor_escala,  frustum_factor_escala )

"""
Función para fijar el Viewport y la proyección en OpenGL
"""
def fijarViewportProyeccion():
    glViewport( 0, 0, ventana_tam_x, ventana_tam_y )
    fijarProyeccion()

"""
Función para fijar la cámara en OpenGL
"""
def fijarCamara():
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glRotatef(camara_angulo_x,1,0,0)
    glRotatef(camara_angulo_y,0,1,0)

"""
Función para dibujar la rejilla, "el suelo"
"""
def dibujarRejilla():
    long_grid = 1000.0
    gap = 50.0

    num_lines = int( (long_grid*2)/gap )

    # establecer modo de dibujo a lineas (podría estar en puntos)
    glPolygonMode( GL_FRONT_AND_BACK, GL_LINE );
    # Ancho de línea
    glLineWidth( 0.2 );

    # dibujar las líneas
    glBegin(GL_LINES)
    # Color negro
    glColor3f( 0.2, 0.2, 0.2 )

    for i in range(num_lines):
        # if i != num_lines/2:
        glVertex3f( -long_grid, 0.0, gap*(i-num_lines/2) )
        glVertex3f( +long_grid, 0.0, gap*(i-num_lines/2) )

        glVertex3f( gap*(i-num_lines/2), 0.0, -long_grid )
        glVertex3f( gap*(i-num_lines/2), 0.0, +long_grid )

    glEnd()

"""
Función para dibujar los ejes cartesianos
"""
def dibujarEjes():
    long_ejes = 450.0
    # establecer modo de dibujo a lineas (podría estar en puntos)
    glPolygonMode( GL_FRONT_AND_BACK, GL_LINE );
    # Ancho de línea
    glLineWidth( 1.5 );
    # dibujar tres segmentos
    glBegin(GL_LINES)
    # eje X, color rojo
    glColor3f( 1.0, 0.0, 0.0 )

    glVertex3f( origen_ejes[0]              , origen_ejes[1], origen_ejes[2] )
    glVertex3f( origen_ejes[0] +long_ejes   , origen_ejes[1], origen_ejes[2] )
    # eje Y, color verde
    glColor3f( 0.0, 1.0, 0.0 )
    glVertex3f( origen_ejes[0], origen_ejes[1]              , origen_ejes[2] )
    glVertex3f( origen_ejes[0], origen_ejes[1] +long_ejes-250   , origen_ejes[2] )
    # eje Z, color azul
    glColor3f( 0.0, 0.0, 1.0 )
    glVertex3f( origen_ejes[0], origen_ejes[1]  ,           origen_ejes[2]  )
    glVertex3f( origen_ejes[0], origen_ejes[1]  , origen_ejes[2] +long_ejes )
    glEnd()

    # Dibujar punto
    grey = [0.5,0.5,0.5]
    g1, g2, g3 = grey
    glColor3f( g1, g2, g3 )
    glutSolidSphere( 5.0, 20, 20 )

"""
Función para dibujar una zona de batería
"""
def dibujarZonaBateriaUnitaria():
    glBegin(GL_TRIANGLES)
    glVertex3f(-tamanio_bateria,-0.01,-tamanio_bateria)
    glVertex3f(-tamanio_bateria,-0.01,tamanio_bateria)
    glVertex3f(tamanio_bateria,-0.01,-tamanio_bateria)
    glVertex3f(-tamanio_bateria,-0.01,tamanio_bateria)
    glVertex3f(tamanio_bateria,-0.01,-tamanio_bateria)
    glVertex3f(tamanio_bateria,-0.01,tamanio_bateria)
    glEnd()

"""
Función para dibujar las zonas de las baterías
"""
def dibujarZonasBateria(zonaResaltadas=[0.0]):
    glMatrixMode(GL_MODELVIEW)

    c1 = [1,1,0]
    c2 = [0,1,1]

    grey = [0.1,0.1,0.1]
    g1, g2, g3 = grey

    glColor3f(1,1,1)
    if leapmotion.tutorial_activo_leap: glColor3f(g1,g2,g3)
    elif zonaResaltadas[0] == 1: glColor3f(c1[0],c1[1],c1[2])
    elif zonaResaltadas[1] == 1: glColor3f(c2[0],c2[1],c2[2])
    glPushMatrix()
    glTranslatef(-desplazamiento_bateria,0,-desplazamiento_bateria)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()

    glColor3f(1,1,1)
    if leapmotion.tutorial_activo_leap: glColor3f(g1,g2,g3)
    elif zonaResaltadas[0] == 2: glColor3f(c1[0],c1[1],c1[2])
    elif zonaResaltadas[1] == 2: glColor3f(c2[0],c2[1],c2[2])
    glPushMatrix()
    glTranslatef(-desplazamiento_bateria,0,desplazamiento_bateria)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()

    glColor3f(1,1,1)
    if leapmotion.tutorial_activo_leap: glColor3f(g1,g2,g3)
    elif zonaResaltadas[0] == 3: glColor3f(c1[0],c1[1],c1[2])
    elif zonaResaltadas[1] == 3: glColor3f(c2[0],c2[1],c2[2])
    glPushMatrix()
    glTranslatef(desplazamiento_bateria,0,-desplazamiento_bateria)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()

    glColor3f(1,1,1)
    #if tutorial_activo: glColor3f(0.75,0.75,0.75)
    if zonaResaltadas[0] == 4: glColor3f(c1[0],c1[1],c1[2])
    elif zonaResaltadas[1] == 4: glColor3f(c2[0],c2[1],c2[2])
    glPushMatrix()
    glTranslatef(desplazamiento_bateria,0,desplazamiento_bateria)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()

def dibujarPanelConfig(filename):
    textura = PNGtoTexture(filename)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, textura)
    glBegin(GL_TRIANGLES)
    glVertex3f(-tamanio_bateria,-0.01,-tamanio_bateria)
    glVertex3f(-tamanio_bateria,-0.01,tamanio_bateria)
    glVertex3f(tamanio_bateria,-0.01,-tamanio_bateria)
    glVertex3f(-tamanio_bateria,-0.01,tamanio_bateria)
    glVertex3f(tamanio_bateria,-0.01,-tamanio_bateria)
    glVertex3f(tamanio_bateria,-0.01,tamanio_bateria)
    glEnd()
    glDisable(GL_TEXTURE_2D)

def dibujarMenu():
    #dibujar 3 cajas con y un panel de volumen

    s = "VOLUMEN"
    glWindowPos2i(2*ventana_tam_x/6, 2*ventana_tam_y /4)
    for c in s:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c));

    s = "ZOOM"
    glWindowPos2i(2*ventana_tam_x/6, 3*ventana_tam_y /4)
    for c in s:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c));

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glTranslatef(0,0,-150)
    glScalef(0.5,0.5,0.5)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(100,0,-150)
    glScalef(0.5,0.5,0.5)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(200,0,-150)
    glScalef(0.5,0.5,0.5)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()


    glPushMatrix()
    glTranslatef(0,0,0)
    glScalef(0.5,0.5,0.5)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(100,0,0)
    glScalef(0.5,0.5,0.5)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(200,0,0)
    glScalef(0.5,0.5,0.5)
    dibujarZonaBateriaUnitaria()
    glPopMatrix()

"""
Función auxiliar para dibujar los objetos en pantalla
"""
def dibujarObjetos():
    global posiciones_baquetas, direcciones_baquetas
    global tiempo_transcurrido_ultimo_dato, margen_tiempo

    longitud_baqueta = 60

    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)

    zonaResaltadas = [0,0]

    for j in range(len(posiciones_baquetas)):
        if j == 2: break
        p = posiciones_baquetas[j]
        if p[0] < -comienzo_bateria and p[2] < -comienzo_bateria: zonaResaltadas[j] = 1
        elif p[0] < -comienzo_bateria and p[2] > comienzo_bateria: zonaResaltadas[j] = 2
        elif p[0] > comienzo_bateria and p[2] < -comienzo_bateria: zonaResaltadas[j] = 3
        elif p[0] > comienzo_bateria and p[2] > comienzo_bateria: zonaResaltadas[j] = 4

    dibujarZonasBateria(zonaResaltadas)

    glLineWidth( 10.5 );
    col = [[0.5,0.5,0],[0,0.5,0.5]]
    glBegin(GL_LINES)
    for j in range(len(posiciones_baquetas)):
        if j == 2: break
        glColor3f(col[j][0],col[j][1],col[j][2])
        p = posiciones_baquetas[j]
        d = direcciones_baquetas[j]
        glVertex3f(p[0],p[1],p[2])
        glVertex3f(p[0]-longitud_baqueta*d[0],p[1]-longitud_baqueta*d[1],p[2]-longitud_baqueta*d[2])
    glEnd()

    if  time.time() - tiempo_transcurrido_ultimo_dato > margen_tiempo:
        posiciones_baquetas = []
        direcciones_baquetas = []

"""
Función que muestra ayuda en la ventana
"""
def ayuda():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0.0, ventana_tam_x, 0.0, ventana_tam_y)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1.0, 0.0, 0.0)

    num_lineas = 0
    for s in strings_ayuda:
        glWindowPos2i(10, ventana_tam_y - 15*(num_lineas + 1))
        for c in s:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c));
        num_lineas += 1

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()


"""
Función de dibujado
"""
def dibujar():
    rotationRate = (time.time() - tStart) * 1.05
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    fijarViewportProyeccion()
    fijarCamara()
    if menu_activo:
        glClearColor( 0.9, 1.0, 1.0, 1.0 )
        dibujarMenu()
    else:
        glClearColor( 1.0, 1.0, 1.0, 1.0 )
        dibujarRejilla()
        dibujarEjes()
        dibujarObjetos()
    #ayuda()
    glutPostRedisplay()
    glutSwapBuffers()

"""
Función que gestiona las teclas normales: para cambiar escala y velocidad
"""
def teclaNormal(k, x, y):
    global frustum_factor_escala, vertice_actual, velocidad, camara_angulo_x, camara_angulo_y, dibujoEvoluta

    if k == b'+':
        frustum_factor_escala *= 1.05
    elif k == b'-':
        frustum_factor_escala /= 1.05
    elif k == b'r':
        camara_angulo_x = 90
        camara_angulo_y = 0.0
    elif k == b'q' or k == b'Q' or ord(k) == 27: # Escape
        glutLeaveMainLoop()
    else:
        return

    glutPostRedisplay()

"""
Función que gestiona las teclas especiales: para cambiar la cámara
"""
def teclaEspecial(k, x, y):
    global camara_angulo_x, camara_angulo_y

    if k == GLUT_KEY_UP:
        camara_angulo_x += 5.0
    elif k == GLUT_KEY_DOWN:
        camara_angulo_x -= 5.0
    elif k == GLUT_KEY_LEFT:
        camara_angulo_y += 5.0
    elif k == GLUT_KEY_RIGHT:
        camara_angulo_y -= 5.0
    else:
        return

    glutPostRedisplay()

"""
Función que gestiona el cambio de tamaño de la ventana
"""
def cambioTamanio(width, height):
    global ventana_tam_x,ventana_tam_y
    ventana_tam_x = width
    ventana_tam_y = height
    fijarViewportProyeccion()
    glutPostRedisplay()

"""
Función que gestiona la pulsación de los botones del ratón en la ventana
"""
origen = [-1,-1]
def pulsarRaton(boton,estado,x,y):
    da = 5.0
    redisp = False
    global frustum_factor_escala,origen,camara_angulo_x,camara_angulo_y

    if boton == GLUT_LEFT_BUTTON:
        if estado == GLUT_UP:
            origen = [-1,-1]
        else:
            origen = [x,y]
    elif boton == 3: # Rueda arriba aumenta el zoom
        frustum_factor_escala *= 1.05;
        redisp = True
    elif boton == 4: # Rueda abajo disminuye el zoom
        frustum_factor_escala /= 1.05;
        redisp = True
    elif boton == 5: # Llevar la rueda a la izquierda gira la cámara a la izquierda
        camara_angulo_y -= da
        redisp = True
    elif boton == 6: # Llevar la rueda a la derecha gira la cámara a la derecha
        camara_angulo_y += da
        redisp = True

    if redisp:
        glutPostRedisplay();

"""
Función que gestiona el evento de mover el ratón sobre la ventana
"""
def moverRaton(x,y):
    global camara_angulo_x,camara_angulo_y, origen, tiempo_transcurrido_ultimo_dato, ahora

    tiempo_transcurrido_ultimo_dato = time.time()

    if origen[0] >= 0 and origen[1] >= 0:
        camara_angulo_x += (y - origen[1])*0.25;
        camara_angulo_y += (x - origen[0])*0.25;
        origen[0] = x;
        origen[1] = y;
        # Redibujar
        glutPostRedisplay();

def limpiarTodo():
    pass

"""
Función para redibujar desde leapmotion.py cuando hay baquetas
"""
def redibujar():
    global posiciones_baquetas, direcciones_baquetas, ahora, tiempo_transcurrido_ultimo_dato

    tiempo_transcurrido_ultimo_dato = time.time()
    posiciones_baquetas = leapmotion.posicion_media
    direcciones_baquetas = leapmotion.direccion_media

    glutPostRedisplay()

"""
Función para llamar al mainLoop desde bateria.py
"""
def openGLmainloop():
    glutMainLoop()

"""
Función para inicializar contexto de OpenGL
"""
def inicializarOpenGL():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH | GLUT_MULTISAMPLE | GLUT_ALPHA)
    glutInitWindowPosition(0, 0)
    glutInitWindowSize(ventana_tam_x, ventana_tam_y)
    glutCreateWindow("Bateria")

    glEnable(GL_NORMALIZE)
    glEnable(GL_MULTISAMPLE_ARB)
    glEnable( GL_DEPTH_TEST )
    glColor3f(0.0,0.0,0.0)

    glutIdleFunc(dibujar)
    glutDisplayFunc(dibujar)
    glutReshapeFunc(cambioTamanio)
    glutKeyboardFunc(teclaNormal)
    glutSpecialFunc(teclaEspecial)
    #glutMouseFunc(pulsarRaton)
    #glutMotionFunc(moverRaton)

    glutCloseFunc(limpiarTodo);
    glutSetOption(GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_GLUTMAINLOOP_RETURNS);

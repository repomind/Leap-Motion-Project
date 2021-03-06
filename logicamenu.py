#!/usr/bin/env python2
# coding=utf-8

# Modules
import sys, pygame, random, os
from pygame.locals import *

"""
Clase que contendrá lo necesario para albergar un instrumento.

    @nombre : nombre del instrumento
    @imagen : imagen del instrumento
    @rect   : rectángulo que ocupa el instrumento

"""
class Instrumento(pygame.sprite.Sprite):
    def __init__(self,nombre,imagen,rect):
        pygame.sprite.Sprite.__init__(self)

        self.nombre = nombre
        self.imagen = imagen
        self.rect = rect

    def get_nombre(self):
        return self.nombre

    def get_imagen(self):
        return self.imagen

    def get_rect(self):
        return self.rect

"""
Función para cargar una imagen según un nombre de archivo

    @filename : nombre de archivo a cargar
    @image    : imagen devuelta
"""
def load_image(filename):
    try: image = pygame.image.load(filename)
    except pygame.error as message:
        raise SystemExit(message)
    image = image.convert()
    return image

"""
Función para seleccionar un instrumento desde un lienzo con varios de ellos.

    @string_sonidos_actuales : lista que contiene los sonidos actuales, para no volverlos a coger
    @return : se devuelve el nombre del sonido asociado al instrumento seleccionado por pantalla
"""
def cambio_instrumento(string_sonidos_actuales):

    image_size = 292

    WIDTH = image_size * 2
    HEIGHT = image_size * 2

    strings_sonidos_nuevos = [os.path.splitext(nombre)[0] for nombre in os.listdir("./sonidos/") if nombre.endswith("ogg") and nombre not in string_sonidos_actuales]
    screen = pygame.display.set_mode((WIDTH,HEIGHT),0,32)
    pygame.display.set_caption("Elige un nuevo instrumento")

    posiciones = [ (0,0), (0, image_size), (image_size, 0), (image_size, image_size) ]

    instrumentos = [ Instrumento(strings_sonidos_nuevos[i], load_image("imagenes/" + strings_sonidos_nuevos[i] + ".jpg" ), Rect(posiciones[i],(image_size, image_size))) for i in range(len(strings_sonidos_nuevos)) ]

    nuevo_instrumento = ""

    while True:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = pygame.mouse.get_pos()
                for instrumento in instrumentos:
                   if instrumento.get_rect().collidepoint(click):
                       pygame.display.quit()
                       return instrumento.get_nombre() + ".ogg"

        for instrumento in instrumentos:
            screen.blit(instrumento.get_imagen(), instrumento.get_rect())

        pygame.display.flip()

"""
Función para mostrar una secuencia de imágenes con Pygame. La usamos a modo de
tutorial para el funcionamiento de la batería virtual.
"""
def tutorial():
    WIDTH = 720
    HEIGHT = 540

    screen = pygame.display.set_mode((WIDTH,HEIGHT),0,32)

    pygame.display.set_caption("Tutorial Leap Motion")
    names_images = ['capturas/t'+str(i)+'.png' for i in range(1,8)]
    tutorial_images = ( load_image(name) for name in names_images )
    actual_image = next(tutorial_images)

    fin = False

    while not fin:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    actual_image = next(tutorial_images)
                except StopIteration:
                    fin = True

        screen.blit(actual_image, (0, 0))

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    pygame.init()
    # tutorial()
    print cambio_instrumento(['caja.ogg','platillo.ogg','bombo.ogg','tom-tom.ogg'])

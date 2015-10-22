#!/usr/bin/env python2
# coding=utf-8

import Leap, sys

import leapmotion
import graficos

#import logging # Deberíamos usarlo!

def configurarControlador(controller):
    # Configurando el controller
    # Le cambiamos valores de velocidad, historia y distancia
    # para que consiga reconocer mejor el gesto
    controller.config.set("Gesture.KeyTap.MinDownVelocity", 20.0)
    controller.config.set("Gesture.KeyTap.HistorySeconds", 0.2)
    controller.config.set("Gesture.KeyTap.MinDistance", 1.0)
    controller.config.save()

def main():
    # Inicializamos openGL
    graficos.inicializarOpenGL()

    # Creamos un listener y un controlador
    listener = leapmotion.SampleListener()
    controller = Leap.Controller()
    controller.add_listener(listener) # añadimos el listener al controlador
    configurarControlador(controller)



    graficos.openGLmainloop()

    print "Pulsa enter para salir..."
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass
    finally:
        # Borrar el listener al salir
        controller.remove_listener(listener)

if __name__ == "__main__":
    main()
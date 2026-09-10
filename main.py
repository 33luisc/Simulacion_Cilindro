import pygame
import random
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from config import R_c, H_c, r_e
from pelota import Pelota
from fisica import boca_obstruida, resolver_fisica_paso, acomodar_pelotas_suave
from render import dibujar_esfera, dibujar_vaso_cristal, dibujar_hud

def intentar_tirar(pelotas):
    if boca_obstruida(pelotas):
        return False

    r_rand = np.sqrt(random.uniform(0, (R_c - r_e)**2))
    th_rand = random.uniform(0, 2 * np.pi)
    x_gen = r_rand * np.cos(th_rand)
    z_gen = r_rand * np.sin(th_rand)

    pelotas.append(Pelota(x_gen, H_c + 2.0, z_gen))
    return True

def main():
    pygame.init()
    pygame.font.init()
    fuente_titulo = pygame.font.SysFont('Arial', 17, bold=True)
    fuente_datos = pygame.font.SysFont('Arial', 14, bold=True)
    fuente_sub = pygame.font.SysFont('Arial', 12)

    display = (900, 900)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Simulación 3D: Vaso de Cristal Modularizado")

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glLightfv(GL_LIGHT0, GL_POSITION, (40.0, 80.0, 50.0, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.25, 0.25, 0.3, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.95, 0.95, 0.95, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

    rot_x = 15.0
    rot_y = 0.0
    distancia = H_c * 2.8

    dragging_left = False
    dragging_right = False
    last_mouse = (0, 0)
    clock = pygame.time.Clock()

    pelotas = []
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        dt = min(dt, 0.033)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    intentar_tirar(pelotas)
                elif event.key == K_r:
                    pelotas.clear()
                elif event.key == K_s:
                    acomodar_pelotas_suave(pelotas)
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging_left = True
                    last_mouse = event.pos
                elif event.button == 3:
                    dragging_right = True
                    last_mouse = event.pos
                    acomodar_pelotas_suave(pelotas)
                elif event.button == 4:
                    distancia = max(H_c * 1.2, distancia - 2.0)
                elif event.button == 5:
                    distancia = min(H_c * 6.0, distancia + 2.0)
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    dragging_left = False
                elif event.button == 3:
                    dragging_right = False
            elif event.type == MOUSEMOTION:
                if dragging_left:
                    dx = event.pos[0] - last_mouse[0]
                    dy = event.pos[1] - last_mouse[1]
                    rot_y += dx * 0.4
                    rot_x += dy * 0.4
                    rot_x = max(-85.0, min(85.0, rot_x))
                    last_mouse = event.pos
                elif dragging_right:
                    dx = abs(event.pos[0] - last_mouse[0])
                    dy = abs(event.pos[1] - last_mouse[1])
                    if dx + dy > 5:
                        acomodar_pelotas_suave(pelotas)
                        last_mouse = event.pos

        keys = pygame.key.get_pressed()
        if keys[K_a]:
            intentar_tirar(pelotas)

        resolver_fisica_paso(pelotas, dt)

        # Criterio de desborde y recuento
        pelotas_dentro = sum(1 for p in pelotas if p.pos[1] <= (H_c - r_e))
        pelotas_desbordadas = len(pelotas) - pelotas_dentro
        vaso_lleno = boca_obstruida(pelotas) or pelotas_desbordadas > 0

        # Renderizado
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.06, 0.07, 0.10, 1.0)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (display[0] / display[1]), 0.1, 300.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glTranslatef(3.5, -H_c * 0.45, -distancia)
        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)

        for p in pelotas:
            dibujar_esfera(p)

        dibujar_vaso_cristal()
        dibujar_hud(fuente_titulo, fuente_datos, fuente_sub, pelotas_dentro, pelotas_desbordadas, vaso_lleno)

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()
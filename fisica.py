import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import random
from config import R_c, H_c, r_e, d_e, RESTITUCION, FRICCION_PISO

def obtener_rayo_desde_mouse(mouse_x, mouse_y, display_size):
    """ Convierte las coordenadas 2D de la pantalla a un rayo 3D en el espacio del mundo """
    viewport = glGetIntegerv(GL_VIEWPORT)
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)

    # Invertir Y porque Pygame tiene el origen arriba a la izquierda
    win_y = viewport[3] - float(mouse_y)
    win_x = float(mouse_x)

    # Obtener punto plano cercano (z=0) y lejano (z=1)
    near_point = gluUnProject(win_x, win_y, 0.0, modelview, projection, viewport)
    far_point = gluUnProject(win_x, win_y, 1.0, modelview, projection, viewport)

    origen = np.array(near_point, dtype=float)
    direccion = np.array(far_point, dtype=float) - origen
    direccion /= np.linalg.norm(direccion)

    return origen, direccion

def seleccionar_pelota(origen_rayo, dir_rayo, pelotas):
    """ Busca la pelota más cercana que intersecte con el rayo del cursor """
    pelota_seleccionada = None
    dist_minima = float('inf')

    for p in pelotas:
        # Vector desde el origen del rayo al centro de la esfera
        oc = p.pos - origen_rayo
        t = np.dot(oc, dir_rayo)

        if t > 0:  # La pelota está delante de la cámara
            punto_cercano = origen_rayo + t * dir_rayo
            dist_al_rayo = np.linalg.norm(p.pos - punto_cercano)

            if dist_al_rayo <= r_e and t < dist_minima:
                dist_minima = t
                pelota_seleccionada = p

    return pelota_seleccionada, dist_minima

def aplicar_fuerza_arrastre(pelota, objetivo_3d, dt):
    """ Aplica una fuerza elástica (muelle) hacia el punto objetivo manteniendo la física """
    K_STIFFNESS = 150.0  # Rigidez del resorte
    DAMPING = 12.0       # Amortiguación para evitar oscilaciones descontroladas

    diferencia = objetivo_3d - pelota.pos
    fuerza = diferencia * K_STIFFNESS - pelota.vel * DAMPING
    
    # F = m * a  (asumiendo masa = 1.0)
    pelota.vel += fuerza * dt

def boca_obstruida(pelotas):
    """ Determina si hay pelotas en el borde superior del vaso obstruyendo el paso """
    for p in pelotas:
        if p.pos[1] >= (H_c - r_e):
            dist_centro = np.sqrt(p.pos[0]**2 + p.pos[2]**2)
            if dist_centro < (R_c - r_e):
                return True
    return False

def resolver_fisica_paso(pelotas, dt):
    for p in pelotas:
        p.integrar_movimiento(dt)

    ITERACIONES = 12
    MARGEN_PISO = 0.05

    for _ in range(ITERACIONES):
        # A) Piso Sólido (y = 0)
        for p in pelotas:
            if p.pos[1] - r_e < MARGEN_PISO:
                p.pos[1] = r_e + MARGEN_PISO
                if p.vel[1] < 0:
                    p.vel[1] = -p.vel[1] * RESTITUCION
                    p.vel[0] *= FRICCION_PISO
                    p.vel[2] *= FRICCION_PISO

        # B) Paredes Cilíndricas Extendidas
        max_r = R_c - r_e
        for p in pelotas:
            if p.pos[1] <= H_c + d_e:
                dist_radial = np.sqrt(p.pos[0]**2 + p.pos[2]**2)
                if dist_radial > max_r and dist_radial > 0:
                    nx = p.pos[0] / dist_radial
                    nz = p.pos[2] / dist_radial

                    p.pos[0] = nx * max_r
                    p.pos[2] = nz * max_r

                    v_radial = p.vel[0] * nx + p.vel[2] * nz
                    if v_radial > 0:
                        p.vel[0] -= (1 + RESTITUCION) * v_radial * nx
                        p.vel[2] -= (1 + RESTITUCION) * v_radial * nz

        # C) Colisiones Esfera vs Esfera
        num_p = len(pelotas)
        for i in range(num_p):
            p1 = pelotas[i]
            for j in range(i + 1, num_p):
                p2 = pelotas[j]

                delta = p1.pos - p2.pos
                dist_sq = np.dot(delta, delta)
                dist_min = d_e

                if 0 < dist_sq < dist_min**2:
                    dist = np.sqrt(dist_sq)
                    normal = delta / dist
                    overlap = dist_min - dist

                    p1.pos += normal * (overlap * 0.5)
                    p2.pos -= normal * (overlap * 0.5)

                    vel_rel = p1.vel - p2.vel
                    v_separacion = np.dot(vel_rel, normal)

                    if v_separacion < 0:
                        impulso = -(1 + RESTITUCION) * v_separacion * 0.5
                        p1.vel += normal * impulso
                        p2.vel -= normal * impulso

def acomodar_pelotas_suave(pelotas):
    """ Aplica pequeños impulsos para acomodar las pelotas """
    for p in pelotas:
        p.vel[0] += random.uniform(-12.0, 12.0)
        p.vel[2] += random.uniform(-12.0, 12.0)
        p.vel[1] -= random.uniform(0.0, 15.0)
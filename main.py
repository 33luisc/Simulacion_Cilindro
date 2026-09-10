import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random

# ==========================================
# 1. MEDIDAS REALES (Centímetros cm)
# ==========================================
D_c = 18.40   # Diámetro del vaso (cm)
H_c = 30.00   # Altura del vaso (cm)
d_e = 5.88    # Diámetro de las pelotas (cm)

R_c = D_c / 2.0  # Radio del vaso (9.20 cm)
r_e = d_e / 2.0  # Radio de la pelota (2.94 cm)

# Parámetros físicos
GRAVEDAD = -981.0     # cm/s^2
RESTITUCION = 0.25    # Menor rebote para evitar que "brinquen"
FRICCION_PISO = 0.70  # Amortiguación al rodar

# Variable global declarada explícitamente
pelotas = []

# ==========================================
# 2. CLASE PELOTA
# ==========================================
class Pelota:
    def __init__(self, x, y, z):
        self.pos = np.array([x, y, z], dtype=float)
        self.vel = np.array([0.0, -40.0, 0.0], dtype=float)
        self.color = [random.uniform(0.3, 1.0), random.uniform(0.3, 1.0), random.uniform(0.3, 1.0)]

    def integrar_movimiento(self, dt):
        self.vel[1] += GRAVEDAD * dt
        self.pos += self.vel * dt

# ==========================================
# 3. MOTOR FÍSICO CORREGIDO
# ==========================================
def boca_obstruida():
    """ Revisa si la parte superior del vaso ya tiene pelotas bloqueando el ingreso """
    for p in pelotas:
        if p.pos[1] >= (H_c - r_e):
            dist_centro = np.sqrt(p.pos[0]**2 + p.pos[2]**2)
            if dist_centro < (R_c - r_e):
                return True
    return False

def resolver_fisica_paso(dt):
    for p in pelotas:
        p.integrar_movimiento(dt)

    ITERACIONES = 12
    MARGEN_PISO = 0.1  # Evita que las esferas traspasen la base en OpenGL

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

                if dist_sq < dist_min**2 and dist_sq > 0:
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

# ==========================================
# 4. RENDERIZADO DE TEXTO (HUD 2D)
# ==========================================
def render_texto(pantalla, texto, x, y, fuente):
    text_surface = fuente.render(texto, True, (255, 230, 0))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    w, h = text_surface.get_size()

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 900, 0, 900, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glRasterPos2i(x, y)
    glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    glDisable(GL_BLEND)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ==========================================
# 5. FUNCIONES DE DIBUJO OPENGL
# ==========================================
def dibujar_vaso():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Reja del cilindro
    glColor4f(0.0, 0.85, 1.0, 0.35)
    quadric = gluNewQuadric()
    gluQuadricDrawStyle(quadric, GLU_LINE)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quadric, R_c, R_c, H_c, 36, 18)
    glPopMatrix()

    # Base semi-transparente (sin bloquear la profundidad Z-buffer)
    glDepthMask(GL_FALSE)
    glColor4f(0.1, 0.2, 0.3, 0.4)
    glBegin(GL_POLYGON)
    for i in range(48):
        theta = i * 2.0 * np.pi / 48
        glVertex3f(R_c * np.cos(theta), 0.0, R_c * np.sin(theta))
    glEnd()

    # Anillo inferior
    glColor4f(0.0, 1.0, 1.0, 0.8)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    for i in range(48):
        theta = i * 2.0 * np.pi / 48
        glVertex3f(R_c * np.cos(theta), 0.0, R_c * np.sin(theta))
    glEnd()

    # Anillo superior
    glColor4f(0.0, 1.0, 1.0, 0.95)
    glLineWidth(2.5)
    glBegin(GL_LINE_LOOP)
    for i in range(48):
        theta = i * 2.0 * np.pi / 48
        glVertex3f(R_c * np.cos(theta), H_c, R_c * np.sin(theta))
    glEnd()

    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)

def dibujar_esfera(p):
    glPushMatrix()
    glTranslatef(p.pos[0], p.pos[1], p.pos[2])
    glColor3f(*p.color)
    quadric = gluNewQuadric()
    gluQuadricDrawStyle(quadric, GLU_FILL)
    gluQuadricNormals(quadric, GLU_SMOOTH)
    gluSphere(quadric, r_e, 20, 20)
    glPopMatrix()

# ==========================================
# 6. BUCLE PRINCIPAL
# ==========================================
def main():
    pygame.init()
    pygame.font.init()
    fuente_hud = pygame.font.SysFont('Arial', 24, bold=True)
    fuente_sub = pygame.font.SysFont('Arial', 16)

    display = (900, 900)
    pantalla = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Simulación 3D: Vaso Cilíndrico con Límite de Capacidad")

    gluPerspective(45, (display[0] / display[1]), 0.1, 300.0)
    glTranslatef(0.0, -H_c * 0.45, -H_c * 2.8)
    glRotatef(15, 1, 0, 0)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, (20.0, 50.0, 30.0, 1.0))

    dragging_left = False
    dragging_right = False
    last_mouse = (0, 0)
    clock = pygame.time.Clock()

    def intentar_tirar():
        if boca_obstruida():
            return False

        r_rand = np.sqrt(random.uniform(0, (R_c - r_e)**2))
        th_rand = random.uniform(0, 2 * np.pi)
        x_gen = r_rand * np.cos(th_rand)
        z_gen = r_rand * np.sin(th_rand)
        
        pelotas.append(Pelota(x_gen, H_c + 2.0, z_gen))
        return True

    def acomodar_pelotas_suave():
        """ Vibra sutilmente las pelotas para acomodarlas sin romper colisiones """
        for p in pelotas:
            # Solo un pequeño impulso lateral suave para que rueden a los huecos
            p.vel[0] += random.uniform(-12.0, 12.0)
            p.vel[2] += random.uniform(-12.0, 12.0)
            # Ligero asentamiento hacia abajo
            p.vel[1] -= random.uniform(0.0, 15.0)

    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        dt = min(dt, 0.033)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    intentar_tirar()
                elif event.key == K_r:
                    pelotas.clear()
                elif event.key == K_s:
                    acomodar_pelotas_suave()
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:       # Clic Izquierdo -> Rotar vista
                    dragging_left = True
                    last_mouse = event.pos
                elif event.button == 3:     # Clic Derecho -> Vibrar suave
                    dragging_right = True
                    last_mouse = event.pos
                    acomodar_pelotas_suave()
                elif event.button == 4:
                    glTranslatef(0, 0, 2.5)
                elif event.button == 5:
                    glTranslatef(0, 0, -2.5)
            elif event.type == MOUSEBUTTONUP:
                # Se limpian adecuadamente ambos estados
                if event.button == 1:
                    dragging_left = False
                elif event.button == 3:
                    dragging_right = False
            elif event.type == MOUSEMOTION:
                if dragging_left:
                    dx = event.pos[0] - last_mouse[0]
                    dy = event.pos[1] - last_mouse[1]
                    glRotatef(dx * 0.4, 0, 1, 0)
                    glRotatef(dy * 0.4, 1, 0, 0)
                    last_mouse = event.pos
                elif dragging_right:
                    # Mover el ratón con clic derecho solo agita con baja intensidad
                    dx = abs(event.pos[0] - last_mouse[0])
                    dy = abs(event.pos[1] - last_mouse[1])
                    if dx + dy > 5:
                        acomodar_pelotas_suave()
                        last_mouse = event.pos

        keys = pygame.key.get_pressed()
        if keys[K_a]:
            intentar_tirar()

        # Actualizar física
        resolver_fisica_paso(dt)

        pelotas_dentro = sum(1 for p in pelotas if p.pos[1] <= H_c)
        vaso_lleno = boca_obstruida()

        # Renderizado
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.08, 0.09, 0.12, 1.0)

        dibujar_vaso()
        for p in pelotas:
            dibujar_esfera(p)

        # HUD en pantalla
        texto_contador = f"Pelotas dentro: {pelotas_dentro}"
        if vaso_lleno:
            texto_contador += " (¡VASO LLENO!)"

        render_texto(pantalla, texto_contador, 30, 850, fuente_hud)
        render_texto(pantalla, "[ESPACIO] Tirar | [A] Continuo | [Clic Der / S] Acomodar | [R] Vaciar", 30, 825, fuente_sub)

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()
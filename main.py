import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random
import math

# ==========================================
# 1. MEDIDAS REALES (Centímetros cm)
# ==========================================
D_c = 18.40   # Diámetro del vaso (cm)
H_c = 30.00   # Altura del vaso (cm)
d_e = 5.88    # Diámetro de las pelotas (cm)

R_c = D_c / 2.0  # Radio del vaso (9.20 cm)
r_e = d_e / 2.0  # Radio de la pelota (2.94 cm)

# Volúmenes teóricos (cm^3)
VOLUMEN_VASO = math.pi * (R_c**2) * H_c
VOLUMEN_PELOTA = (4.0 / 3.0) * math.pi * (r_e**3)

# Parámetros físicos
GRAVEDAD = -981.0     # cm/s^2
RESTITUCION = 0.25    # Menor rebote
FRICCION_PISO = 0.70  # Amortiguación al rodar

pelotas = []

# ==========================================
# 2. CLASE PELOTA
# ==========================================
class Pelota:
    def __init__(self, x, y, z):
        self.pos = np.array([x, y, z], dtype=float)
        self.vel = np.array([0.0, -40.0, 0.0], dtype=float)
        self.color = [random.uniform(0.4, 1.0), random.uniform(0.4, 1.0), random.uniform(0.4, 1.0)]

    def integrar_movimiento(self, dt):
        self.vel[1] += GRAVEDAD * dt
        self.pos += self.vel * dt

# ==========================================
# 3. MOTOR FÍSICO
# ==========================================
def boca_obstruida():
    """ Determina si hay pelotas en el borde superior del vaso obstruyendo el paso """
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

# ==========================================
# 4. RENDERIZADO DE UI (HUD 2D CORREGIDO)
# ==========================================
def iniciar_modo_2d(w_win=900, h_win=900):
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, w_win, 0, h_win, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

def finalizar_modo_2d():
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def render_texto(texto, x, y, fuente, color=(255, 255, 255)):
    text_surface = fuente.render(texto, True, color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    w, h = text_surface.get_size()
    glRasterPos2i(x, y)
    glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

def dibujar_rectangulo_2d(x, y, w, h, color_rgba):
    glColor4f(*color_rgba)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()

def dibujar_hud(fuente_titulo, fuente_datos, fuente_sub, pelotas_dentro, pelotas_desbordadas, vaso_lleno):
    iniciar_modo_2d()

    # Panel lateral más compacto (Ancho 250px) para evitar solapamiento
    dibujar_rectangulo_2d(15, 650, 250, 230, (0.04, 0.07, 0.12, 0.92))
    
    # Borde cian del panel
    glColor4f(0.0, 0.75, 1.0, 0.7)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(15, 650)
    glVertex2f(265, 650)
    glVertex2f(265, 880)
    glVertex2f(15, 880)
    glEnd()

    # Título y datos
    render_texto("ESTADO DEL VASO", 28, 852, fuente_titulo, (0, 215, 255))
    
    vol_ocupado = pelotas_dentro * VOLUMEN_PELOTA
    pct_ocupacion = min(100.0, (vol_ocupado / VOLUMEN_VASO) * 100.0)

    color_estado = (0, 255, 150) if not vaso_lleno else (255, 60, 60)
    texto_estado = f"Pelotas dentro: {pelotas_dentro}"
    if vaso_lleno:
        texto_estado += " (¡LLENO!)"

    render_texto(texto_estado, 28, 822, fuente_datos, color_estado)
    
    # Contador de Desborde con resalte visual
    color_desborde = (255, 70, 70) if pelotas_desbordadas > 0 else (160, 160, 160)
    render_texto(f"Bolas desbordadas: {pelotas_desbordadas}", 28, 794, fuente_datos, color_desborde)

    # Medición de Volumen en cm³
    render_texto(f"Vol. ocupado: {vol_ocupado:.1f} cm³", 28, 766, fuente_datos, (255, 230, 0))
    render_texto(f"Capacidad: {VOLUMEN_VASO:.1f} cm³ ({pct_ocupacion:.1f}%)", 28, 738, fuente_sub, (180, 200, 220))

    # Barra de Capacidad Visual
    dibujar_rectangulo_2d(28, 670, 224, 14, (0.1, 0.15, 0.22, 0.9))
    
    if pct_ocupacion < 60:
        c_bar = (0.0, 0.8, 0.4, 0.95)
    elif pct_ocupacion < 90:
        c_bar = (0.9, 0.7, 0.0, 0.95)
    else:
        c_bar = (0.9, 0.2, 0.2, 0.95)

    w_fill = int((pct_ocupacion / 100.0) * 224)
    if w_fill > 0:
        dibujar_rectangulo_2d(28, 670, w_fill, 14, c_bar)

    # Panel Inferior de Controles
    dibujar_rectangulo_2d(15, 15, 870, 38, (0.04, 0.07, 0.12, 0.90))
    render_texto("[ESPACIO] Tirar | [A] Continuo | [Clic Izq] Orbitar | [Clic Der / S] Acomodar | [R] Vaciar", 28, 27, fuente_sub, (200, 220, 240))

    finalizar_modo_2d()

# ==========================================
# 5. RENDERIZADO 3D (VASO Y ESFERAS)
# ==========================================
def dibujar_vaso_cristal():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    especular_vidrio = [1.0, 1.0, 1.0, 1.0]
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, especular_vidrio)
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 96.0)

    slices = 48
    stacks = 1

    glEnable(GL_CULL_FACE)
    glCullFace(GL_FRONT)
    glColor4f(0.4, 0.7, 0.9, 0.12)
    quadric = gluNewQuadric()
    gluQuadricDrawStyle(quadric, GLU_FILL)
    gluQuadricNormals(quadric, GLU_SMOOTH)
    
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quadric, R_c, R_c, H_c, slices, stacks)
    glPopMatrix()

    glCullFace(GL_BACK)
    glColor4f(0.5, 0.8, 1.0, 0.22)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quadric, R_c, R_c, H_c, slices, stacks)
    glPopMatrix()
    
    glDisable(GL_CULL_FACE)

    glDepthMask(GL_FALSE)
    glColor4f(0.3, 0.6, 0.8, 0.4)
    glBegin(GL_POLYGON)
    glNormal3f(0.0, 1.0, 0.0)
    for i in range(slices):
        theta = i * 2.0 * np.pi / slices
        glVertex3f(R_c * np.cos(theta), 0.0, R_c * np.sin(theta))
    glEnd()

    glLineWidth(2.5)
    glColor4f(0.7, 0.9, 1.0, 0.7)
    glBegin(GL_LINE_LOOP)
    for i in range(slices):
        theta = i * 2.0 * np.pi / slices
        glVertex3f(R_c * np.cos(theta), 0.0, R_c * np.sin(theta))
    glEnd()

    glColor4f(0.8, 0.95, 1.0, 0.9)
    glBegin(GL_LINE_LOOP)
    for i in range(slices):
        theta = i * 2.0 * np.pi / slices
        glVertex3f(R_c * np.cos(theta), H_c, R_c * np.sin(theta))
    glEnd()

    glDepthMask(GL_TRUE)

def dibujar_esfera(p):
    glPushMatrix()
    glTranslatef(p.pos[0], p.pos[1], p.pos[2])
    
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.6, 0.6, 0.6, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)
    
    glColor3f(*p.color)
    quadric = gluNewQuadric()
    gluQuadricDrawStyle(quadric, GLU_FILL)
    gluQuadricNormals(quadric, GLU_SMOOTH)
    gluSphere(quadric, r_e, 24, 24)
    glPopMatrix()

# ==========================================
# 6. BUCLE PRINCIPAL
# ==========================================
def main():
    pygame.init()
    pygame.font.init()
    fuente_titulo = pygame.font.SysFont('Arial', 17, bold=True)
    fuente_datos = pygame.font.SysFont('Arial', 14, bold=True)
    fuente_sub = pygame.font.SysFont('Arial', 12)

    display = (900, 900)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Simulación 3D: Vaso de Cristal con Medición de Volumen")

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
        for p in pelotas:
            p.vel[0] += random.uniform(-12.0, 12.0)
            p.vel[2] += random.uniform(-12.0, 12.0)
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
                if event.button == 1:
                    dragging_left = True
                    last_mouse = event.pos
                elif event.button == 3:
                    dragging_right = True
                    last_mouse = event.pos
                    acomodar_pelotas_suave()
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
                        acomodar_pelotas_suave()
                        last_mouse = event.pos

        keys = pygame.key.get_pressed()
        if keys[K_a]:
            intentar_tirar()

        resolver_fisica_paso(dt)

        # --- CRITERIO DE DESBORDE CORREGIDO ---
        # Una pelota cuenta como dentro solo si su centro está totalmente por debajo del borde superior (H_c - r_e)
        pelotas_dentro = sum(1 for p in pelotas if p.pos[1] <= (H_c - r_e))
        pelotas_desbordadas = len(pelotas) - pelotas_dentro
        vaso_lleno = boca_obstruida() or pelotas_desbordadas > 0

        # Renderizado
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.06, 0.07, 0.10, 1.0)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (display[0] / display[1]), 0.1, 300.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Desplazamiento horizontal (+3.5 cm) para descentrar el cilindro y despejar el HUD izquierdo
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
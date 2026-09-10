import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from config import R_c, H_c, r_e, VOLUMEN_VASO, VOLUMEN_PELOTA

# --- MODO 2D (HUD) ---
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

    # Panel lateral
    dibujar_rectangulo_2d(15, 650, 250, 230, (0.04, 0.07, 0.12, 0.92))
    
    # Borde cian
    glColor4f(0.0, 0.75, 1.0, 0.7)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(15, 650)
    glVertex2f(265, 650)
    glVertex2f(265, 880)
    glVertex2f(15, 880)
    glEnd()

    # Textos y estado
    render_texto("ESTADO DEL VASO", 28, 852, fuente_titulo, (0, 215, 255))
    
    vol_ocupado = pelotas_dentro * VOLUMEN_PELOTA
    pct_ocupacion = min(100.0, (vol_ocupado / VOLUMEN_VASO) * 100.0)

    color_estado = (0, 255, 150) if not vaso_lleno else (255, 60, 60)
    texto_estado = f"Pelotas dentro: {pelotas_dentro}"
    if vaso_lleno:
        texto_estado += " (¡LLENO!)"

    render_texto(texto_estado, 28, 822, fuente_datos, color_estado)
    
    color_desborde = (255, 70, 70) if pelotas_desbordadas > 0 else (160, 160, 160)
    render_texto(f"Bolas desbordadas: {pelotas_desbordadas}", 28, 794, fuente_datos, color_desborde)

    render_texto(f"Vol. ocupado: {vol_ocupado:.1f} cm³", 28, 766, fuente_datos, (255, 230, 0))
    render_texto(f"Capacidad: {VOLUMEN_VASO:.1f} cm³ ({pct_ocupacion:.1f}%)", 28, 738, fuente_sub, (180, 200, 220))

    # Barra de estado
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

    # Panel Inferior
    dibujar_rectangulo_2d(15, 15, 870, 38, (0.04, 0.07, 0.12, 0.90))
    # Cambiar la siguiente línea dentro de dibujar_hud():
    render_texto("[ESPACIO] Tirar | [A] Continuo | [Clic Izq] Orbitar | [Clic Der] Arrastrar / Sacudir | [R] Vaciar", 28, 27, fuente_sub, (200, 220, 240))

    finalizar_modo_2d()

# --- RENDERIZADO 3D ---
def dibujar_vaso_cristal():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 96.0)

    slices, stacks = 48, 1

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
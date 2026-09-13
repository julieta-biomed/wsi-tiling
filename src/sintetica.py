"""Genera una WSI sintetica con estructura histologica H&E creible."""
import numpy as np
from scipy import ndimage as ndi

def tejido_he(alto, ancho, semilla=7, densidad_nuclear=1.0, escala=1.0):
    """Tejido tenido con hematoxilina-eosina.

    Estroma rosa (eosina) + nucleos morados (hematoxilina). La densidad
    nuclear distingue tumor de tejido sano: el tumor es hipercelular.
    """
    rng = np.random.default_rng(semilla)
    # estroma: textura fibrilar rosa
    # estroma fibrilar: dos escalas de textura
    fino = ndi.gaussian_filter(rng.random((alto, ancho)), 1.2)
    grueso = ndi.zoom(ndi.gaussian_filter(rng.random((alto//16, ancho//16)), 2.0),
                      16, order=1)[:alto, :ancho]
    base = 0.45*(fino-fino.mean())/max(fino.std(),1e-6)*0.5 + 0.55*grueso
    img = np.zeros((alto,ancho,3), np.float32)
    img[...,0] = 0.88 - 0.10*base    # R
    img[...,1] = 0.70 - 0.18*base    # G
    img[...,2] = 0.82 - 0.08*base    # B

    # nucleos: elipses moradas
    n = int(densidad_nuclear * alto*ancho / 320)
    ys = rng.integers(0, alto, n); xs = rng.integers(0, ancho, n)
    rr = rng.normal(3.2*escala, 0.9*escala, n).clip(1.6, 9.0)
    mascara = np.zeros((alto,ancho), np.float32)
    yy,xx = np.ogrid[:alto,:ancho]
    # dibujo vectorizado por bloques para no reventar memoria
    for y,x,r in zip(ys,xs,rr):
        y0,y1 = max(0,int(y-r*2)), min(alto,int(y+r*2)+1)
        x0,x1 = max(0,int(x-r*2)), min(ancho,int(x+r*2)+1)
        if y1<=y0 or x1<=x0: continue
        sy,sx = np.ogrid[y0:y1, x0:x1]
        ex = r*rng.uniform(0.65, 1.0)          # elipticidad variable
        d = ((sy-y)/r)**2 + ((sx-x)/ex)**2
        mascara[y0:y1,x0:x1] = np.maximum(mascara[y0:y1,x0:x1], np.exp(-d*1.9))
    img[...,0] -= 0.46*mascara
    img[...,1] -= 0.50*mascara
    img[...,2] -= 0.12*mascara
    return np.clip(img,0,1), mascara

def wsi(alto=8192, ancho=8192, semilla=7):
    """WSI completa: cristal vacio, tejido en forma irregular, foco tumoral."""
    rng = np.random.default_rng(semilla)
    img = np.ones((alto,ancho,3), np.float32)*0.985     # cristal
    img += rng.normal(0,0.004,(alto,ancho,3))           # ruido del escaner

    # forma del tejido: mancha irregular que NO llena el porta
    campo = rng.random((32,32))
    campo = ndi.zoom(ndi.gaussian_filter(campo,2.2), (alto/32, ancho/32), order=3)
    forma = campo > np.percentile(campo, 58)
    forma = ndi.binary_closing(forma, np.ones((25,25)))
    forma = ndi.binary_opening(forma, np.ones((25,25)))

    sano,_ = tejido_he(alto,ancho,semilla=semilla, densidad_nuclear=1.0)
    img[forma] = sano[forma]

    # foco tumoral: hipercelular, dentro del tejido
    cy,cx = int(alto*0.62), int(ancho*0.40)
    R = int(min(alto,ancho)*0.13)
    yy,xx = np.ogrid[:alto,:ancho]
    borde = ndi.zoom(ndi.gaussian_filter(rng.random((24,24)),1.6),
                     (alto/24,ancho/24), order=3)
    tumor = (((yy-cy)**2+(xx-cx)**2) < (R*(0.75+0.5*borde))**2) & forma
    tum,_ = tejido_he(alto,ancho,semilla=semilla+1, densidad_nuclear=3.1, escala=1.15)
    img[tumor] = tum[tumor]
    return (np.clip(img,0,1)*255).astype(np.uint8), forma, tumor

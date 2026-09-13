"""Artefactos reales de una laminilla escaneada."""
import numpy as np
from scipy import ndimage as ndi

def agregar(img, semilla=13):
    """Marca de marcador, sombra de iluminacion, burbuja y polvo."""
    rng=np.random.default_rng(semilla)
    out=img.astype(np.float32).copy()
    H,W=out.shape[:2]
    yy,xx=np.ogrid[:H,:W]

    # 1. Marca de marcador del patologo (trazo negro-azulado en el borde)
    t=np.linspace(0,1,400)
    cy=(0.12+0.06*np.sin(6*t))*H; cx=(0.08+0.84*t)*W
    marca=np.zeros((H,W),bool)
    for y,x in zip(cy,cx):
        r=int(0.011*min(H,W))
        y0,y1=max(0,int(y-r)),min(H,int(y+r)); x0,x1=max(0,int(x-r)),min(W,int(x+r))
        marca[y0:y1,x0:x1]=True
    out[marca]=np.array([30,35,90],np.float32)

    # 2. Sombra de iluminacion: vinetado del escaner
    vin=1-0.16*(((yy-H/2)/(H/2))**2+((xx-W/2)/(W/2))**2)
    out*=vin[...,None]

    # 3. Burbuja de aire: anillo claro con borde oscuro
    by,bx,br=int(0.78*H),int(0.80*W),int(0.09*min(H,W))
    d=np.sqrt((yy-by)**2+(xx-bx)**2)
    anillo=(d>br*0.82)&(d<br)
    out[d<br*0.82]=np.minimum(out[d<br*0.82]*1.18+18,255)
    out[anillo]*=0.72

    # 4. Polvo y suciedad sobre el cristal
    for _ in range(60):
        y,x=rng.integers(0,H),rng.integers(0,W); r=rng.integers(2,7)
        y0,y1=max(0,y-r),min(H,y+r); x0,x1=max(0,x-r),min(W,x+r)
        out[y0:y1,x0:x1]*=rng.uniform(0.35,0.65)
    return np.clip(out,0,255).astype(np.uint8)

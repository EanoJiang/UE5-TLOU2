"""Documented reconstruction of stripped eye shader from original maps.

This derives a portable base colour and tangent normal. The 3.2 iris UV scale
is a reconstruction parameter inferred from the original sclera transition,
not an extracted Naughty Dog shader constant.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/TexturesDecoded'
size=2048
scale=3.2

def sample(path,u,v):
    a=np.asarray(Image.open(path).convert('RGB'),dtype=np.float64)/255
    x=np.clip(u*(a.shape[1]-1),0,a.shape[1]-1)
    y=np.clip(v*(a.shape[0]-1),0,a.shape[0]-1)
    x0=x.astype(int);y0=y.astype(int)
    x1=np.minimum(x0+1,a.shape[1]-1);y1=np.minimum(y0+1,a.shape[0]-1)
    fx=(x-x0)[...,None];fy=(y-y0)[...,None]
    return (a[y0,x0]*(1-fx)+a[y0,x1]*fx)*(1-fy)+(a[y1,x0]*(1-fx)+a[y1,x1]*fx)*fy

v,u=np.mgrid[0:size,0:size].astype(np.float64)/(size-1)
iu=(u-.5)*scale+.5
iv=(v-.5)*scale+.5
radius=np.sqrt((iu-.5)**2+(iv-.5)**2)
alpha=np.clip((.5-radius)/.025,0,1)
alpha=alpha*alpha*(3-2*alpha)
alpha=alpha[...,None]
iris=sample(OUT/'ellie-eyes-iris-color.png',iu,iv)
sclera=sample(OUT/'ellie-eye-sclera.png',u,v)
# Mix in linear light, retaining all original source pixels through resampling.
def linear(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def srgb(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
base=np.clip(srgb(linear(iris)*alpha+linear(sclera)*(1-alpha)),0,1)
basepath=OUT/'ellie-eyes-reconstructed-basecolor.png'
Image.fromarray(np.uint8(np.round(base*255))).save(basepath)
normal=sample(OUT/'iris-normal.png',iu,iv)*2-1
normal=normal*alpha+np.array([0,0,1])*(1-alpha)
normal/=np.maximum(np.linalg.norm(normal,axis=2,keepdims=True),1e-8)
normalpath=OUT/'ellie-eyes-reconstructed-normal.png'
Image.fromarray(np.uint8(np.round(np.clip(normal*.5+.5,0,1)*255))).save(normalpath)
report={'status':'reconstructed portable eye material; original shader constants unavailable',
        'source_color':['ellie-eyes-iris-color.png','ellie-eye-sclera.png'],
        'source_normal':'iris-normal.png','iris_uv_scale':scale,'iris_uv_center':[.5,.5],
        'iris_edge_width_in_scaled_uv':.025,'color_space_mix':'linear light',
        'base_color':str(basepath),'normal':str(normalpath),
        'limitation':'No captured corneal refraction, parallax or wetness shader is claimed.'}
(ROOT/'Exports/reconstructed_eye_material_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

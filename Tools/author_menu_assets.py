"""Create original line icons and Unity metadata; leave background artwork unchanged."""
from PIL import Image, ImageDraw
import math
import unity_writer as u

BASE='Assets/Game/Resources/BlackstoneFoundation/Menu'

def icon(name):
    im=Image.new('RGBA',(192,192));d=ImageDraw.Draw(im);ink=(237,219,181,255)
    def line(points):d.line([(x*2,y*2) for x,y in points],fill=ink,width=7,joint='curve')
    def box(rect):d.rectangle(tuple(x*2 for x in rect),outline=ink,width=7)
    def oval(rect):d.ellipse(tuple(x*2 for x in rect),outline=ink,width=7)
    if name=='play':line([(25,16),(76,48),(25,80),(25,16)])
    elif name=='book':
        line([(48,80),(48,23),(26,16),(12,20),(12,76),(30,73),(48,80),(66,73),(84,76),(84,20),(70,16),(48,23)])
    elif name=='map':
        oval((32,12,64,44));oval((43,23,53,33));line([(34,37),(48,66),(62,37)]);line([(33,56),(19,78),(77,78),(63,56)])
    elif name=='settings':
        oval((29,29,67,67));oval((41,41,55,55))
        for a in range(8):
            t=a*math.pi/4;line([(48+19*math.cos(t),48+19*math.sin(t)),(48+31*math.cos(t),48+31*math.sin(t))])
    elif name=='controls':
        line([(31,25),(65,25),(77,37),(86,69),(79,76),(59,60),(37,60),(17,76),(10,69),(19,37),(31,25)])
        line([(24,43),(42,43)]);line([(33,34),(33,52)]);oval((61,34,68,41));oval((70,45,77,52))
    elif name=='exit':
        line([(56,17),(20,17),(20,79),(56,79)]);line([(40,48),(82,48),(68,34)]);line([(82,48),(68,62)])
    elif name=='cell':
        box((14,14,82,82))
        for x in (27,41,55,69):line([(x,14),(x,82)])
        line([(14,48),(82,48)])
    elif name=='boat':
        line([(13,53),(83,53),(66,76),(31,76),(13,53)]);line([(32,53),(39,35),(66,35),(72,53)]);line([(47,35),(47,22),(59,22)]);line([(10,84),(86,84)])
    elif name=='helicopter':
        oval((24,39,70,64));line([(18,27),(78,27)]);line([(47,27),(47,39)]);line([(67,48),(84,39),(84,27)]);line([(31,64),(31,75),(67,75),(67,64)]);line([(44,40),(44,63)])
    elif name=='boxing':
        for x in (12,53):
            line([(x+5,48),(x+11,22),(x+23,18),(x+30,30),(x+27,53),(x+21,65),(x+4,63),(x,55),(x+5,48)])
            box((x+4,65,x+21,79))
    elif name=='cards':
        box((17,22,54,77));box((44,15,81,70));line([(63,31),(73,42),(63,53),(53,42),(63,31)])
    elif name=='inmate':
        oval((32,9,64,41));line([(24,81),(24,57),(33,47),(63,47),(72,57),(72,81)]);line([(34,60),(34,81)]);line([(62,60),(62,81)])
    elif name=='id':
        box((8,20,88,76));oval((20,32,38,50));line([(16,64),(20,55),(38,55),(42,64)]);line([(52,37),(77,37)]);line([(52,52),(77,52)]);line([(52,65),(68,65)])
    elif name=='key':
        oval((12,13,48,49));oval((24,25,36,37));line([(43,45),(77,79),(84,72)]);line([(63,65),(70,58)])
    elif name=='phone':
        box((27,8,69,88));line([(27,20),(69,20)]);line([(27,73),(69,73)]);oval((44,78,52,84))
    elif name=='knife':
        line([(19,78),(74,23),(77,12),(63,16),(41,38),(43,45)]);line([(34,43),(53,62)]);line([(31,53),(20,64),(14,75),(19,78)])
    elif name=='tattoo':
        oval((12,12,84,84));line([(28,63),(38,29),(47,56),(57,29),(68,63)]);line([(24,73),(72,73)])
    elif name=='uniform':
        line([(32,17),(17,24),(8,43),(24,50),(28,40),(28,80),(68,80),(68,40),(72,50),(88,43),(79,24),(64,17),(57,29),(39,29),(32,17)])
    im.resize((96,96),Image.Resampling.LANCZOS).save(u.ROOT/BASE/(name+'.png'))


def main():
    for name in ('play','book','map','settings','controls','exit','cell','boat','helicopter','boxing','cards','inmate','id','key','phone','knife','tattoo','uniform'):icon(name)
    u.write(BASE+'.meta','fileFormatVersion: 2\nguid: '+u.guid(BASE)+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
    for p in sorted((u.ROOT/BASE).iterdir()):
        rel=str(p.relative_to(u.ROOT))
        if p.suffix=='.png':
            u.meta(rel,'TextureImporter','  serializedVersion: 13\n  mipmaps:\n    enableMipMap: 0\n    sRGBTexture: 1\n  textureType: 0\n  maxTextureSize: 2048\n  alphaIsTransparency: 1\n  textureSettings:\n    filterMode: 1\n    wrapU: 1\n    wrapV: 1\n')
        elif p.suffix=='.ttf':
            u.meta(rel,'TrueTypeFontImporter','  serializedVersion: 4\n  fontSize: 32\n  fontNames: [Anton]\n  includeFontData: 1\n  fontRenderingMode: 0\n  ascentCalculationMode: 1\n  useLegacyBoundsCalculation: 0\n')

if __name__=='__main__':main()

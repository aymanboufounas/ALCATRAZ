"""Original noise/resonance Foley and non-derivative cinematic cues, mono PCM."""
import numpy as np,math
from scipy.signal import butter,sosfilt
from scipy.ndimage import gaussian_filter1d
from author_chapter_audio import save_wav
RATE=22050;rng=np.random.default_rng(710)
def time(seconds):return np.arange(int(RATE*seconds))/RATE
def filtered(n,low,high):return sosfilt(butter(3,[low,high],btype='bandpass',fs=RATE,output='sos'),n)
def save(name,a,peak=.65):
 a=np.asarray(a);a-=a.mean();a*=min(1,peak/max(np.max(np.abs(a)),.001));fade=min(240,len(a)//10)
 a[:fade]*=np.linspace(0,1,fade);a[-fade:]*=np.linspace(1,0,fade)
 save_wav('Assets/Game/Audio/'+name+'.wav',a,RATE)
def reverb(a):
 out=a.copy()
 for sec,gain in [(.065,.14),(.121,.075),(.193,.04)]:
  n=int(sec*RATE)
  if n<len(a):out[n:]+=a[:-n]*gain
 return out
for kind in ['concrete','metal']:
 for k in range(4):
  t=time(.27);n=rng.normal(size=len(t));hz=70+k*8
  a=filtered(n,130 if kind=='concrete' else 450,4800)*np.exp(-t*35)*.29
  a+=np.sin(2*math.pi*hz*t)*np.exp(-t*42)*.11
  if kind=='metal':a+=sum(np.sin(2*math.pi*f*t)*np.exp(-t*19)*.019 for f in [379,697,1103])
  scuff=filtered(rng.normal(size=len(t)),650,4500)*np.exp(-((t-.055)/.035)**2)*.07
  save('Footstep_'+kind+'_'+str(k),reverb(a+scuff),.62)
for name,duration in [('MetalDoor',1.6),('DoorKnock',2.1),('Punch',.32),('ClothHide',.62),('CardShuffle',1.1),('CardDeal',.24),('KnifeDrop',.68),('PhoneRing',2.4),('PhoneClick',.13),('TattooBuzz',5),('Whistle',.9),('CellAmbience',24),('YardAmbience',28),('Tension',24),('MissionComplete',2.9),('Missed',2.4),('Sob',2.4)]:
 t=time(duration);n=rng.normal(size=len(t));a=np.zeros_like(t)
 if name=='MetalDoor':
  a=filtered(n,300,5800)*np.exp(-((t-.08)/.10)**2)*.22
  for start in [.13,.72]:
   u=np.maximum(t-start,0);gate=t>=start
   a+=gate*(filtered(n,80,2500)*np.exp(-u*38)*.22+sum(np.sin(2*math.pi*f*u)*np.exp(-u*8)*.02 for f in [83,191,337,511]))
 elif name=='DoorKnock':
  for start in [.10,.54,1.09]:
   u=np.maximum(t-start,0);a+=(t>=start)*np.exp(-u*31)*(filtered(n,90,4200)*.27+np.sin(2*math.pi*113*u)*.11)
 elif name=='Punch':a=filtered(n,90,5100)*np.exp(-t*31)*.34+np.sin(2*math.pi*68*t)*np.exp(-t*40)*.14
 elif name in ['ClothHide','CardShuffle','CardDeal']:
  a=filtered(n,350,6300)*.13*(np.sin(t/duration*math.pi)**2)
  if name=='CardShuffle':a*=.35+.65*np.sin(t*47)**8
  if name=='CardDeal':a+=filtered(n,800,7200)*np.exp(-t*45)*.09
 elif name=='KnifeDrop':
  for start,gain in [(0,.35),(.16,.13),(.33,.06)]:
   u=np.maximum(0,t-start);a+=(t>=start)*(filtered(n,500,6200)*np.exp(-u*65)*gain+sum(np.sin(2*math.pi*f*u)*np.exp(-u*20)*gain*.05 for f in [947,1871,3143]))
 elif name=='PhoneRing':
  for start in [.08,.25,.72,.89,1.36,1.53]:
   u=np.maximum(0,t-start);a+=(t>=start)*np.exp(-u*23)*(.12*np.sin(2*math.pi*880*u)+.035*np.sin(2*math.pi*1320*u))
 elif name=='PhoneClick':a=filtered(n,900,6600)*np.exp(-t*65)*.15
 elif name=='TattooBuzz':a=(.035*np.sin(2*math.pi*112*t)+.015*np.sin(2*math.pi*224*t)+filtered(n,350,2500)*.01)*(.9+.1*np.sin(t*4))
 elif name=='Whistle':a=.11*np.sin(2*math.pi*(2380*t+8*np.sin(t*22)))*np.sin(t/duration*math.pi)**2
 elif name=='CellAmbience':
  a=gaussian_filter1d(n,22)*.027+np.sin(2*math.pi*50*t)*.005
  for start in [3.2,11,18]:
   u=np.maximum(0,t-start);a+=(t>=start)*np.exp(-u*13)*np.sin(2*math.pi*218*u)*.008
 elif name=='YardAmbience':
  a=gaussian_filter1d(n,38)*.045*(.7+.3*np.sin(t*.31))
  for start in [2,6.8,13,21]:
   u=np.maximum(0,t-start);env=(t>=start)*(u<.25)*np.sin(np.clip(u/.25,0,1)*math.pi)**2
   a+=env*.011*np.sin(2*math.pi*(2100*u+350*u*u))
 elif name in ['Tension','MissionComplete','Missed']:
  notes=[55,82.4,110] if name=='Tension' else [196,246.94,293.66,392] if name=='MissionComplete' else [196,174.61,155.56]
  for k,hz in enumerate(notes):
   u=np.maximum(0,t-k*.18);env=np.minimum(u/.20,1)*np.exp(-u*(.035 if name=='Tension' else 2))*(t>=k*.18)
   a+=env*sum(np.sin(2*math.pi*hz*j*u+np.sin(u*.6)*.006*j)/j**1.65 for j in range(1,7))*(.022 if name=='Tension' else .063)
  if name=='Tension':a*=.5+.5*np.sin(t/duration*math.pi)**2
 else:a=filtered(n,80,650)*np.sin(t*2.5)**4*.035
 save(name,reverb(a),.74)
print('25 newly authored Foley, ambience and score clips.')

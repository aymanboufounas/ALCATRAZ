"""Original story text, synthesized sound effects and replaceable scratch dialogue.
Voice recordings are optional eSpeak NG takes. No third-party game recordings.
"""
import json, math, os, shutil, subprocess, wave, io
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from unity_writer import ROOT, meta, write

SCENES={
 'intro': [('ELIAS','Another night in B-04. Keep your head down. Learn who you can trust.'),('GUARD','Vale! Yard period. No trouble today.')],
 'reader':[('TOMAS','New face. Tomas. Keep your eyes open: the yard belongs to two gangs.'),('ELIAS','Elias Vale. I am looking for people I can trust.'),('TOMAS','Trust is earned here. Niko runs with Blue Meridian. Malik leads them.')],
 'cook':[('SAMIR','These trays will not move themselves. Give me a hand.'),('ELIAS','I will take this side.'),('SAMIR','Thanks, Vale. That is how you make acquaintances in here.')],
 'fixer':[('WORKSHOP CONTACT','The workshop doors open after roll call. Nobody gets special treatment.'),('ELIAS','I just need to understand the routine.'),('WORKSHOP CONTACT','Stay in the yard until the next whistle. Watch the people, not just the walls.')],
 'conceal':[('GUARD','Enough! Both of you, step back.'),('NIKO','You saw nothing, officer.'),('ELIAS','I have it. Keep walking.')],
 'thanks':[('NIKO','You kept that knife out of his hands. I would have lost everything.'),('ELIAS','It is hidden. Nobody saw.'),('NIKO','Then you have my respect. Come meet Malik. We remember who stands with us.')],
 'gang_oath':[('MALIK','Niko says you helped him when everyone else watched.'),('ELIAS','I am not looking for another enemy.'),('MALIK','Blue Meridian looks after its own. Earn your place and we stand with you.'),('ELIAS','I am in.'),('MALIK','Rafi will give you our mark. Then get that knife safely into your cell.')],
 'tattoo':[('RAFI','This mark means you belong to Blue Meridian. Hold still.'),('ELIAS','I understand.'),('RAFI','Done. Now hide the knife before the next search.')],
 'stash':[('ELIAS','Under the mattress, in B-04. Out of sight. It stays here.')],
 'phone_gift':[('NIKO','You kept your word. Malik trusts you. Take this phone.'),('ELIAS','To keep in touch with the gang?'),('NIKO','Exactly. Keep it hidden. Answer when Malik calls.')],
 'phone_call':[('MALIK','Vale. Good. We can talk without a crowd listening.'),('ELIAS','I hear you.'),('MALIK','The Iron Rooks have been pushing our people around. Find their man in the yard. Do not bring the knife.')],
 'rival':[('IRON ROOKS','You wear their mark now? That was a mistake.'),('ELIAS','Leave our people alone.'),('IRON ROOKS','Make me.')],
 'arrest':[('GUARD','Break it up! All of you. Hands up, now.'),('GUARD','Every fighter gets a separate cell. Twenty-four hours in isolation.'),('ELIAS','Fine. I am not resisting.')],
 'isolation':[('ELIAS','One day. Nothing to do but sleep.')],
 'wake':[('GUARD','Vale! Wake up. Your twenty-four hours are over. You have a visitor.')],
 'guard_visit':[('GUARD','Your brother is waiting. Step outside. You are coming with me.'),('ELIAS','My brother? All right.')],
 'brother_visit':[('THEO','Elias... I did not know who else to tell.'),('ELIAS','Theo, look at me. What happened?'),('THEO','Dad is gone. The Cinder Syndicate took him. The same people who framed you.'),('ELIAS','Is he alive?'),('THEO','He was alive when they took him. They said we have until next week.'),('ELIAS','I will get him back. Go somewhere safe. I will find you.'),('THEO','Please... do not let them take you too.')],
 'reflection':[('ELIAS','They put me here to keep me out of their way. Now they have my father.'),('ELIAS','Six days. I have to escape before next week. Then I find him, and I make them answer.')],
 'escape_plan':[('ELIAS','Malik, my father was kidnapped by the gang that framed me. I have to get out before next week.'),('MALIK','You are asking for something bigger than a phone or a favor.'),('ELIAS','Help me get enough cooperation inside. If we build a way out, I will get you out too.'),('MALIK','Enough people, enough trust, and the right moment. Bring me that cooperation and I am with you.'),('ELIAS','We leave together. Six days.'),('MALIK','Then we start planning.')]
}
VOICES={'ELIAS':('en-us+m3',42,152),'GUARD':('en-us+m1',32,157),'MALIK':('en-us+m2',31,145),'NIKO':('en-us+m4',48,159),'THEO':('en-us+m3',53,137),'RAFI':('en-us+m2',50,153),'TOMAS':('en-us+m1',58,148),'SAMIR':('en-us+m4',51,154),'WORKSHOP CONTACT':('en-us+m2',47,151),'IRON ROOKS':('en-us+m1',37,159)}

def save_wav(path,data,rate=22050):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    encoded=io.BytesIO()
    with wave.open(encoded,'wb') as f:
        f.setparams((1,2,rate,0,'NONE','not compressed'))
        f.writeframes((np.clip(data,-.94,.94)*32767).astype('<i2').tobytes())
    content=encoded.getvalue();pending=p.with_suffix('.pending')
    with pending.open('wb',buffering=0) as f:
        offset=0
        while offset<len(content):
            written=f.write(content[offset:offset+32768])
            if not written:raise IOError('Short audio write')
            offset+=written
    if pending.read_bytes()!=content:raise IOError('Audio byte verification failed')
    with wave.open(str(pending)) as check:
        if check.getnframes()!=len(data):raise IOError('Audio frame verification failed')
    os.replace(pending,p)
    audio_meta(path)
def audio_meta(path):
    meta(path,'AudioImporter','''  serializedVersion: 7
  defaultSettings:
    serializedVersion: 2
    loadType: 0
    sampleRateSetting: 0
    sampleRateOverride: 22050
    compressionFormat: 1
    quality: 0.7
    conversionMode: 0
  forceToMono: 1
  normalize: 0
  preloadAudioData: 1
  loadInBackground: 0
  ambisonic: 0
  3D: 0
''')
def effects():
    rng=np.random.default_rng(512)
    lengths={'MissionComplete':2.5,'Missed':2,'KnifeDrop':.7,'ClothHide':.75,'TattooBuzz':5,'PhoneRing':2.5,'PhoneClick':.15,'Punch':.26,'Whistle':1.1,'MetalDoor':1.7,'DoorKnock':2.8,'Sob':2.5,'CellAmbience':18,'Tension':16}
    for name,duration in lengths.items():
        rate=22050;t=np.arange(int(rate*duration))/rate;noise=rng.normal(0,1,len(t));a=np.zeros_like(t)
        if name in ['MissionComplete','Missed']:
            notes=[261.63,329.63,392,523.25] if name=='MissionComplete' else [196,155.56,130.81]
            for k,hz in enumerate(notes):
                start=k*.26;u=np.maximum(0,t-start);env=(t>=start)*np.exp(-u*3.3)*np.minimum(u/.012,1)
                a+=env*(.16*np.sin(2*math.pi*hz*u)+.035*np.sin(2*math.pi*hz*2*u))
        elif name=='KnifeDrop':
            a=(.4*gaussian_filter1d(noise,1)*np.exp(-t*30)+.19*np.sin(2*math.pi*1870*t)*np.exp(-t*12))
        elif name=='ClothHide':a=gaussian_filter1d(noise,5)*np.sin(t/duration*math.pi)**2*.7
        elif name=='TattooBuzz':a=.045*np.sin(2*math.pi*109*t)+.022*np.sin(2*math.pi*218*t)+.018*gaussian_filter1d(noise,2)
        elif name=='PhoneRing':a=(.14*np.sin(2*math.pi*620*t)+.14*np.sin(2*math.pi*790*t))*((t%.8)<.4)
        elif name=='PhoneClick':a=.3*gaussian_filter1d(noise,2)*np.exp(-t*70)
        elif name=='Punch':a=.6*gaussian_filter1d(noise,3)*np.exp(-t*25)+.2*np.sin(2*math.pi*72*t)*np.exp(-t*30)
        elif name=='Whistle':a=.16*np.sin(2*math.pi*(2600*t+70*np.sin(t*30)))*np.sin(t/duration*math.pi)
        elif name=='MetalDoor':a=.23*gaussian_filter1d(noise,4)*np.exp(-t*2)+.14*np.sin(2*math.pi*113*t)*np.exp(-t*5)
        elif name=='DoorKnock':
            for start in [.05,.5,1.08,1.56]:
                u=np.maximum(0,t-start);a+=(t>=start)*np.exp(-u*24)*(.25*np.sin(2*math.pi*135*u)+.2*gaussian_filter1d(noise,3))
        elif name=='Sob':a=gaussian_filter1d(noise,10)*(.28+.5*np.maximum(0,np.sin(t*8)))*np.sin(t/duration*math.pi)
        elif name=='CellAmbience':a=.035*gaussian_filter1d(noise,25)+.012*np.sin(2*math.pi*50*t)+.006*np.sin(2*math.pi*100*t)
        else:
            a=.04*np.sin(2*math.pi*55*t)+.026*np.sin(2*math.pi*82.4*t)+.018*np.sin(2*math.pi*116.5*t)
            a*=.5+.5*np.sin(2*math.pi*t/duration)**2
        fade=min(1000,len(a)//10);a[:fade]*=np.linspace(0,1,fade);a[-fade:]*=np.linspace(1,0,fade)
        save_wav('Assets/Game/Audio/'+name+'.wav',a)

def main():
    effects();book=[];espeak=os.environ.get('BLACKSTONE_ESPEAK') or shutil.which('espeak-ng')
    generated=0
    for scene,lines in SCENES.items():
        group=[]
        for i,(speaker,text) in enumerate(lines):
            ident=f'{scene}_{i+1:02d}';seconds=max(2.2,len(text)/17)
            group.append(dict(id=ident,speaker=speaker,text=text,seconds=round(seconds,2)))
            if espeak:
                path='Assets/Game/Resources/Blackstone/Dialogue/'+ident+'.wav';p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
                voice,pitch,speed=VOICES[speaker]
                subprocess.run([espeak,'-v',voice,'-p',str(pitch),'-s',str(speed),'-a','120','-w',str(p),text],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                audio_meta(path);generated+=1
        book.append(dict(id=scene,lines=group))
    for ident,speaker,text in [('incident_niko','NIKO',"Back off. You do not own this yard."),('incident_guard','GUARD',"Break it up! Hands where I can see them!")]:
        if espeak:
            path='Assets/Game/Resources/Blackstone/Dialogue/'+ident+'.wav';p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
            voice,pitch,speed=VOICES[speaker]
            subprocess.run([espeak,'-v',voice,'-p',str(pitch),'-s',str(speed),'-w',str(p),text],check=True,stderr=subprocess.DEVNULL);audio_meta(path);generated+=1
    path='Assets/Game/Resources/Blackstone/story-dialogue.json';write(path,json.dumps(dict(scenes=book),indent=2));meta(path,'TextScriptImporter')
    write('Documentation/Chapter01_Dialogue.md','# Chapter 01 dialogue\n\n'+'\n\n'.join('## '+scene+'\n\n'+'\n\n'.join('**'+speaker+':** '+text for speaker,text in lines) for scene,lines in SCENES.items()))
    print(f'14 original SFX/ambience clips; {generated} synthesized dialogue lines; {len(book)} scenes.')
if __name__=='__main__':main()

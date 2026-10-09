"""Optional offline voice production with Piper. The game ships the WAV files only.
Install piper-tts in a separate environment; set BLACKSTONE_PIPER_MODEL to the
LibriTTS-R medium model. Engine/model dependencies are not part of this game.
"""
import os,json,wave,hashlib,io,argparse
from pathlib import Path
import numpy as np
import onnxruntime as ort
from piper import PiperVoice,SynthesisConfig
from author_chapter_audio import audio_meta,save_wav
from unity_writer import ROOT,write
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only',nargs='+',help='Regenerate only these clip IDs; preserve the other provenance records')
args=parser.parse_args()
model=Path(os.environ['BLACKSTONE_PIPER_MODEL'])
voice=PiperVoice.load(str(model));options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
voice.session=ort.InferenceSession(str(model),sess_options=options,providers=['CPUExecutionProvider'])
# Five distinct measured voices; timing gives the remaining cast their own delivery.
cast={'ELIAS':(7,1.07),'MALIK':(3,1.15),'GUARD':(5,1.01),'NIKO':(8,1.03),'THEO':(102,1.16),'RAFI':(5,1.10),'TOMAS':(7,1.18),'SAMIR':(3,1.04),'WORKSHOP CONTACT':(8,.97),'IRON ROOKS':(5,.95)}
lines=json.loads((ROOT/'Documentation/VoiceProduction.json').read_text())
report_path=ROOT/'Documentation/VoiceProduction_Provenance.json'
previous=json.loads(report_path.read_text())['clips'] if args.only and report_path.exists() else []
records={record['id']:record for record in previous}
if args.only and not set(args.only)<=set(line['id'] for line in lines):raise ValueError('Unknown clip ID')
for index,line in enumerate(lines):
 if args.only and line['id'] not in args.only:continue
 speaker,timing=cast[line['speaker']];path='Assets/Game/Resources/Blackstone/Dialogue/'+line['id']+'.wav';p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
 buffer=io.BytesIO()
 with wave.open(buffer,'wb') as out:voice.synthesize_wav(line['text'],out,syn_config=SynthesisConfig(speaker_id=speaker,length_scale=timing,noise_scale=.55,noise_w_scale=.72))
 buffer.seek(0)
 with wave.open(buffer) as wav:
  rate=wav.getframerate();samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float64)/32768
 # Gentle trim and consistent dialogue loudness, with no clipping.
 samples-=samples.mean();active=np.flatnonzero(np.abs(samples)>.008)
 if len(active):samples=samples[max(0,int(active[0])-int(rate*.045)):min(len(samples),int(active[-1])+int(rate*.12))]
 rms=np.sqrt(np.mean(samples*samples));gain=min(.105/max(rms,1e-5),.86/max(np.max(np.abs(samples)),1e-5));samples*=gain
 save_wav(path,samples,rate)
 records[line['id']]=dict(id=line['id'],speaker=line['speaker'],model_speaker_id=speaker,duration=round(len(samples)/rate,3),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 if index%10==9:print('Neural dialogue recorded:',index+1,flush=True)
ordered=[records[line['id']] for line in lines]
report=dict(provider='Piper local neural TTS',voice_model='en_US-libritts_r-medium',sample_rate=22050,model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),distinct_speakers=5,clips=ordered,source='https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/libritts_r/medium',dataset='https://www.openslr.org/141/',dataset_license='CC BY 4.0',engine='https://github.com/OHF-Voice/piper1-gpl',engine_packaged=False,model_packaged=False)
write('Documentation/VoiceProduction_Provenance.json',json.dumps(report,indent=2))
print('Completed:',len(ordered),'packaged neural speech clips; regenerated',len(args.only) if args.only else len(ordered),flush=True)

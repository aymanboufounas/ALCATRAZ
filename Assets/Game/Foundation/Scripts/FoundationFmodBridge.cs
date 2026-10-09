using UnityEngine;

namespace Blackstone.Foundation
{
    public static class FoundationFmodBridge
    {
        public static bool Enabled;
        // Optional adapter only. SDK, project and banks are supplied separately.
        public static bool TryPlay(string clip,Vector3 position,float volume,float pitch)
        {
#if BLACKSTONE_FMOD
            if(!Enabled)return false;
            try
            {
                var instance=FMODUnity.RuntimeManager.CreateInstance("event:/Blackstone/"+clip);
                instance.set3DAttributes(FMODUnity.RuntimeUtils.To3DAttributes(position));
                instance.setVolume(volume);instance.setPitch(pitch);instance.start();instance.release();return true;
            }
            catch(System.Exception){return false;}
#else
            return false;
#endif
        }
        public static void SetPaused(bool paused)
        {
#if BLACKSTONE_FMOD
            if(!Enabled)return;
            try{FMODUnity.RuntimeManager.GetBus("bus:/").setPaused(paused);}catch(System.Exception){}
#endif
        }
        public static void SetVolume(float volume)
        {
#if BLACKSTONE_FMOD
            if(!Enabled)return;
            try{FMODUnity.RuntimeManager.GetBus("bus:/").setVolume(volume);}catch(System.Exception){}
#endif
        }
    }
}

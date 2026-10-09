using UnityEngine;

namespace Blackstone.Foundation
{
    public sealed class FoundationTarget : MonoBehaviour
    {
        public int Hits { get; private set; }
        float flash;
        Renderer display;
        MaterialPropertyBlock block;
        void Awake(){display=GetComponent<Renderer>();block=new MaterialPropertyBlock();}
        public void Hit(){Hits++;flash=Time.time+.12f;}
        void Update()
        {
            if(display==null)return;
            block.SetColor("_BaseColor",Time.time<flash?new Color(.45f,1,.5f,1):Color.white);
            display.SetPropertyBlock(block);
        }
    }
}

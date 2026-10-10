using System;
using UnityEngine;

namespace Blackstone.Supplied
{
    public static class SuppliedModel
    {
        public static GameObject Create(string name,Transform parent=null)
        {
            var prefab=Resources.Load<GameObject>("AlcatrazSupplied/Prepared/"+name);
            if(prefab==null)throw new InvalidOperationException("Missing prepared "+name+". In Unity choose Alcatraz > Prepare Supplied Assets before Play.");
            var model=UnityEngine.Object.Instantiate(prefab,parent,false);model.name="Supplied "+name;return model;
        }
        public static Bounds Bounds(GameObject model)
        {
            var renderers=model.GetComponentsInChildren<Renderer>();
            if(renderers.Length==0)throw new InvalidOperationException("No visible geometry in "+model.name);
            Bounds result=renderers[0].bounds;
            foreach(var renderer in renderers)if(renderer.enabled)result.Encapsulate(renderer.bounds);
            return result;
        }
        public static void SizeAndGround(GameObject model,float height,Vector3 position)
        {
            var bounds=Bounds(model);model.transform.localScale*=height/Mathf.Max(.001f,bounds.size.y);
            bounds=Bounds(model);model.transform.position+=position-new Vector3(bounds.center.x,bounds.min.y,bounds.center.z);
        }
        public static void Attach(string name,Transform bone,float height,Vector3 offset)
        {
            if(bone==null)return;var model=Create(name,bone);model.transform.localRotation=Quaternion.identity;
            var bounds=Bounds(model);model.transform.localScale*=height/Mathf.Max(.001f,bounds.size.y);
            bounds=Bounds(model);model.transform.position+=bone.TransformPoint(offset)-bounds.center;
        }
    }
}

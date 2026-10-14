using System;
using UnityEngine;

namespace Blackstone.Supplied
{
    public static class SuppliedModel
    {
        public static GameObject Load(string name)
        {
            var native=Resources.Load<GameObject>("AlcatrazSupplied/Baked/"+name);
            return native!=null?native:Resources.Load<GameObject>("AlcatrazSupplied/Prepared/"+name);
        }
        public static GameObject Create(string name,Transform parent=null)
        {
            var prefab=Load(name);
            if(prefab==null)throw new InvalidOperationException("Missing prepared "+name+". In Unity choose Alcatraz > Prepare Supplied Assets before Play.");
            var model=UnityEngine.Object.Instantiate(prefab,parent,false);model.name="Supplied "+name;return model;
        }
        public static Bounds Bounds(GameObject model)
        {
            var renderers=model.GetComponentsInChildren<Renderer>();
            if(renderers.Length==0)throw new InvalidOperationException("No visible geometry in "+model.name);
            Bounds result=VisibleBounds(renderers[0]);
            foreach(var renderer in renderers)if(renderer.enabled)result.Encapsulate(VisibleBounds(renderer));
            return result;
        }
        static Bounds VisibleBounds(Renderer renderer)
        {
            // A skinned renderer's conservative culling box is not its body size.
            // Measure the actual bind/animated vertices when fitting supplied rigs.
            var skin=renderer as SkinnedMeshRenderer;
            if(skin==null||skin.sharedMesh==null)return renderer.bounds;
            var baked=new Mesh();skin.BakeMesh(baked);
            var points=baked.vertices;
            if(points.Length==0){UnityEngine.Object.Destroy(baked);return renderer.bounds;}
            var bounds=new Bounds(skin.transform.TransformPoint(points[0]),Vector3.zero);
            foreach(var point in points)bounds.Encapsulate(skin.transform.TransformPoint(point));
            UnityEngine.Object.Destroy(baked);return bounds;
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
        public static Bounds MeshBounds(GameObject model,Transform frame,float minY=float.NegativeInfinity,
            float maxY=float.PositiveInfinity,float centerX=0,float halfWidth=float.PositiveInfinity)
        {
            Bounds result=new Bounds();bool found=false;
            foreach(var filter in model.GetComponentsInChildren<MeshFilter>())
            {
                if(filter.sharedMesh==null)continue;
                foreach(var vertex in filter.sharedMesh.vertices)
                {
                    Vector3 p=frame.InverseTransformPoint(filter.transform.TransformPoint(vertex));
                    if(p.y<minY||p.y>maxY||Mathf.Abs(p.x-centerX)>halfWidth)continue;
                    if(!found){result=new Bounds(p,Vector3.zero);found=true;}else result.Encapsulate(p);
                }
            }
            if(!found)throw new InvalidOperationException("No fitting vertices in "+model.name);
            return result;
        }
        public static GameObject AttachFitted(string name,Transform anchor,Vector3 size)
        {
            var model=Create(name,anchor);model.transform.localRotation=Quaternion.identity;
            var bounds=MeshBounds(model,anchor);
            if(bounds.size.x<=0||bounds.size.y<=0||bounds.size.z<=0)
                throw new InvalidOperationException("Invalid equipment dimensions for "+name);
            model.transform.localScale=Vector3.Scale(model.transform.localScale,
                new Vector3(size.x/bounds.size.x,size.y/bounds.size.y,size.z/bounds.size.z));
            bounds=MeshBounds(model,anchor);
            model.transform.localPosition-=bounds.center;
            return model;
        }
    }
}

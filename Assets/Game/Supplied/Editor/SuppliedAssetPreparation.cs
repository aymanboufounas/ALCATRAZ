#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine.SceneManagement;

namespace Blackstone.Supplied.Editor
{
    // Generated native assets are reproducible and are prepared before Play or a build.
    public sealed class SuppliedAssetPreparation : IPreprocessBuildWithReport
    {
        const string Root="Assets/Game/Supplied/";
        const string Generated="Assets/GeneratedSupplied/Resources/AlcatrazSupplied/";
        const string Revision="supplied-09.4";
        static readonly string[] Names={"Island","Pistol10mm","Revolver","Police","Dog","Helmet","Vest","Helicopter","House"};
        static bool preparing,scheduled;
        [Serializable] sealed class HouseParts { public string destination,sha256; public string[] parts; public int bytes; }
        [Serializable] sealed class Coastline { public Point[] points; }
        [Serializable] struct Point { public float x,z; }
        public int callbackOrder=>2;
        [InitializeOnLoadMethod] static void Initialize()
        { Schedule();EditorApplication.playModeStateChanged+=BeforePlay; }
        static void Schedule()
        { if(scheduled)return;scheduled=true;EditorApplication.delayCall+=Automatic; }
        static void Automatic()
        {
            scheduled=false;
            if(EditorApplication.isCompiling||EditorApplication.isUpdating){Schedule();return;}
            try{Prepare();}catch(Exception e){Debug.LogError("Supplied Alcatraz assets: "+e.Message+". Use Alcatraz > Prepare Supplied Assets.");}
        }
        static void BeforePlay(PlayModeStateChange state)
        {
            if(state!=PlayModeStateChange.ExitingEditMode||!SuppliedSceneIsOpen())return;
            try{Prepare();}catch(Exception e){EditorApplication.isPlaying=false;Debug.LogError("Cannot enter Play Mode: "+e.Message);}
        }
        [MenuItem("Alcatraz/Prepare Supplied Assets",priority=6)]
        public static void Prepare()
        {
            if(preparing)return;preparing=true;
            try
            {
                string stamp=Generated+"PreparedRevision.txt";
                string signature=Signature();
                if(File.Exists(stamp)&&File.ReadAllText(stamp)==signature&&Names.All(name=>AssetDatabase.LoadAssetAtPath<GameObject>(Generated+"Prepared/"+name+".prefab")!=null))return;
                ReconstructHouse();Directory.CreateDirectory(Generated+"Prepared");AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
                // Check every source before replacing any generated mesh or prefab.
                var sources=Names.ToDictionary(name=>name,name=>SuppliedImportRecovery.Load(SourcePath(name),name));
                AssetDatabase.DeleteAsset(stamp);
                var coastline=JsonUtility.FromJson<Coastline>(File.ReadAllText(Root+"Resources/AlcatrazSupplied/Island/Coastline.json"));
                foreach(string name in Names)
                {
                    var model=UnityEngine.Object.Instantiate(sources[name]);model.name=name;
                    try
                    {
                        foreach(var collider in model.GetComponentsInChildren<Collider>(true))UnityEngine.Object.DestroyImmediate(collider);
                        if(name=="House")
                        {
                            foreach(var renderer in model.GetComponentsInChildren<Renderer>(true))
                                if(renderer.name=="TreeBranches.001"||renderer.name=="WindowLightRefl"||renderer.sharedMaterials.Any(m=>m!=null&&ExcludedHouseMaterial(m.name)))renderer.gameObject.SetActive(false);
                        }
                        if(name=="Island")PrepareIsland(model,coastline);
                        else if(name=="House")
                            foreach(var filter in model.GetComponentsInChildren<MeshFilter>())
                                if(filter.sharedMesh!=null){var collider=filter.gameObject.AddComponent<MeshCollider>();collider.sharedMesh=filter.sharedMesh;}
                        if(name=="Dog")
                        {
                            var animation=model.GetComponentInChildren<Animation>();
                            if(animation==null)throw new InvalidOperationException("Dog must import with Legacy animation enabled.");
                            foreach(AnimationState clip in animation)clip.wrapMode=WrapMode.Loop;
                            animation.playAutomatically=false;
                        }
                        PrefabUtility.SaveAsPrefabAsset(model,Generated+"Prepared/"+name+".prefab",out bool saved);
                        if(!saved)throw new InvalidOperationException("Could not save the prepared "+name+" prefab.");
                    }
                    finally{UnityEngine.Object.DestroyImmediate(model);}
                }
                AssetDatabase.SaveAssets();File.WriteAllText(stamp,Signature());AssetDatabase.Refresh();
                Debug.Log("All nine supplied Alcatraz assets prepared, with a cropped island collision mesh.");
            }
            finally{preparing=false;}
        }
        [MenuItem("Alcatraz/Repair Supplied Imports",priority=7)]
        public static void Repair()
        {
            if(preparing)return;preparing=true;
            try
            {
                AssetDatabase.DeleteAsset(Generated+"PreparedRevision.txt");
                ReconstructHouse();AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
                foreach(string name in Names)SuppliedImportRecovery.Load(SourcePath(name),name,true);
            }
            finally{preparing=false;}
            Prepare();
        }
        static string Signature()
        {
            return Revision+":"+Hash(File.ReadAllBytes(Root+"Resources/AlcatrazSupplied/Catalog.json"))+":"+
                Hash(File.ReadAllBytes(Root+"Resources/AlcatrazSupplied/Island/Coastline.json"))+":"+
                string.Join(":",Names.Select(name=>AssetDatabase.GetAssetDependencyHash(SourcePath(name)).ToString()));
        }
        static string SourcePath(string name)
        {
            string folder=name=="House"?Generated+"House/":Root+"Resources/AlcatrazSupplied/"+name+"/";
            string extension=name=="House"||name=="Pistol10mm"||name=="Revolver"?".fbx":name=="Police"?".obj":".gltf";
            return folder+name+extension;
        }
        static bool SuppliedSceneIsOpen()
        {
            for(int i=0;i<SceneManager.sceneCount;i++)
            {
                var scene=SceneManager.GetSceneAt(i);
                if(scene.isLoaded&&scene.GetRootGameObjects().Any(root=>root.GetComponentInChildren<SuppliedIslandWorld>(true)!=null))return true;
            }
            return false;
        }
        static bool ExcludedHouseMaterial(string name)
        { return new[]{"Sea","Sky","Mist","Waves","ParticleDustShdr","ReflShdr","BushesRefl","ShrubsRefl","TreeTrunkRefl"}.Any(n=>name=="House_"+n||name==n); }
        static void ReconstructHouse()
        {
            var spec=JsonUtility.FromJson<HouseParts>(File.ReadAllText(Root+"HouseSource/HouseParts.json"));
            if(File.Exists(spec.destination)&&new FileInfo(spec.destination).Length==spec.bytes&&Hash(File.ReadAllBytes(spec.destination))==spec.sha256)return;
            using(var output=new MemoryStream())
            {
                foreach(string path in spec.parts){byte[] part=File.ReadAllBytes(path);output.Write(part,0,part.Length);}
                byte[] bytes=output.ToArray();
                if(bytes.Length!=spec.bytes||Hash(bytes)!=spec.sha256)throw new InvalidOperationException("House source parts are missing or damaged. Download the complete repository ZIP.");
                Directory.CreateDirectory(Path.GetDirectoryName(spec.destination));File.WriteAllBytes(spec.destination,bytes);
            }
            AssetDatabase.ImportAsset(spec.destination,ImportAssetOptions.ForceSynchronousImport);
        }
        static string Hash(byte[] bytes)
        { using(var hash=SHA256.Create())return BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-","").ToLowerInvariant(); }
        static bool Inside(Vector3 p,Point[] points)
        {
            bool inside=false;
            for(int i=0,j=points.Length-1;i<points.Length;j=i++)
                if((points[i].z>p.z)!=(points[j].z>p.z)&&p.x<(points[j].x-points[i].x)*(p.z-points[i].z)/(points[j].z-points[i].z)+points[i].x)inside=!inside;
            return inside;
        }
        static void PrepareIsland(GameObject model,Coastline coast)
        {
            foreach(var filter in model.GetComponentsInChildren<MeshFilter>())
            {
                Mesh source=filter.sharedMesh;if(source==null)continue;
                var vertices=source.vertices;var kept=new List<int>();
                foreach(int[] triangleSet in Enumerable.Range(0,source.subMeshCount).Select(index=>source.GetTriangles(index)))
                    for(int i=0;i<triangleSet.Length;i+=3)
                    {
                        Vector3 center=filter.transform.TransformPoint((vertices[triangleSet[i]]+vertices[triangleSet[i+1]]+vertices[triangleSet[i+2]])/3)+new Vector3(-63,45,12);
                        if(Inside(center,coast.points)){kept.Add(triangleSet[i]);kept.Add(triangleSet[i+1]);kept.Add(triangleSet[i+2]);}
                    }
                if(kept.Count<3000)throw new InvalidOperationException("The island coastline removed too much geometry.");
                var mesh=UnityEngine.Object.Instantiate(source);mesh.name="Alcatraz Island Land";mesh.subMeshCount=1;mesh.SetTriangles(kept,0);mesh.RecalculateBounds();
                string path=Generated+"Prepared/IslandLand.asset";AssetDatabase.DeleteAsset(path);AssetDatabase.CreateAsset(mesh,path);
                filter.sharedMesh=mesh;var collider=filter.gameObject.AddComponent<MeshCollider>();collider.sharedMesh=mesh;
            }
        }
        public void OnPreprocessBuild(BuildReport report)
        { if(EditorBuildSettings.scenes.Any(s=>s.enabled&&s.path==Blackstone.Alcatraz.Editor.AlcatrazPreparation.Supplied))Prepare(); }
    }

    public sealed class SuppliedModelImporter : AssetPostprocessor
    {
        bool Supplied=>assetPath.StartsWith("Assets/Game/Supplied/",StringComparison.Ordinal)||assetPath.StartsWith("Assets/GeneratedSupplied/",StringComparison.Ordinal);
        void OnPreprocessModel()
        {
            if(!Supplied)return;var importer=(ModelImporter)assetImporter;
            importer.globalScale=1;importer.useFileScale=true;importer.bakeAxisConversion=true;
            importer.importAnimation=false;importer.importCameras=false;importer.importLights=false;
            importer.importNormals=ModelImporterNormals.Import;importer.importTangents=ModelImporterTangents.CalculateMikk;
            importer.isReadable=true;importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;
            importer.materialLocation=ModelImporterMaterialLocation.InPrefab;
        }
        Material OnAssignMaterialModel(Material source,Renderer renderer)
        {
            if(!Supplied)return null;
            string name=assetPath.Contains("/House/")?"House_"+source.name:
                assetPath.Contains("/Police/")?"Police_"+source.name:
                assetPath.Contains("/Pistol10mm/")?"Pistol10mm":assetPath.Contains("/Revolver/")?"Revolver":null;
            return name==null?null:AssetDatabase.LoadAssetAtPath<Material>("Assets/Game/Supplied/Materials/"+name+".mat");
        }
    }
}
#endif

#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using GLTFast.Logging;

namespace Blackstone.Supplied.Editor
{
    internal static class SuppliedImportRecovery
    {
        const ImportAssetOptions ImportNow=ImportAssetOptions.ForceUpdate|ImportAssetOptions.ForceSynchronousImport;
        [Serializable] sealed class Dependency { public string uri; public long byteLength; }
        [Serializable] sealed class GltfDependencies { public Dependency[] buffers,images; }

        public static GameObject Load(string path,string name,bool force=false)
        {
            if(!File.Exists(path))throw new FileNotFoundException("Missing model: "+path+". Extract the complete repository ZIP.");
            var model=FindModel(path);
            if(force||!Ready(model,name))
            {
                if(path.EndsWith(".gltf",StringComparison.OrdinalIgnoreCase))
                {
                    ImportDependencies(path);
                    SetGltfSettings(path);
                }
                AssetDatabase.ImportAsset(path,ImportNow);
                model=FindModel(path);
            }
            if(!Ready(model,name))throw new InvalidOperationException(Failure(path,name,model));
            return model;
        }

        static GameObject FindModel(string path)
        {
            var main=AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if(main!=null)return main;
            // A glTF scene may be a sub-asset rather than the selected main asset.
            return AssetDatabase.LoadAllAssetsAtPath(path).OfType<GameObject>()
                .OrderByDescending(go=>go.GetComponentsInChildren<Renderer>(true).Length).FirstOrDefault();
        }

        static bool Ready(GameObject model,string name)
        {
            if(model==null||model.GetComponentsInChildren<Renderer>(true).Length==0)return false;
            if(name!="Dog")return true;
            var animation=model.GetComponentInChildren<Animation>(true);
            return animation!=null&&animation.GetClipCount()==17;
        }

        static void ImportDependencies(string path)
        {
            var document=JsonUtility.FromJson<GltfDependencies>(File.ReadAllText(path));
            var dependencies=(document.buffers??Array.Empty<Dependency>()).Concat(document.images??Array.Empty<Dependency>());
            foreach(var dependency in dependencies)
            {
                if(string.IsNullOrEmpty(dependency.uri)||dependency.uri.StartsWith("data:",StringComparison.OrdinalIgnoreCase))continue;
                string file=Path.Combine(Path.GetDirectoryName(path),Uri.UnescapeDataString(dependency.uri)).Replace('\\','/');
                if(!File.Exists(file))throw new FileNotFoundException("Missing glTF dependency: "+file+". Extract the complete repository ZIP.");
                if(dependency.byteLength>0&&new FileInfo(file).Length!=dependency.byteLength)
                    throw new InvalidDataException("Incomplete glTF buffer: "+file+". Extract the complete repository ZIP.");
                // glTFast loads imported textures, so their imports must finish first.
                AssetDatabase.ImportAsset(file,ImportNow);
            }
        }

        static void SetGltfSettings(string path)
        {
            var importer=AssetImporter.GetAtPath(path);
            if(importer==null||importer.GetType().FullName!="GLTFast.Editor.GltfImporter")return;
            var settings=new SerializedObject(importer);
            Set(settings,"importSettings.animationMethod",1);
            Set(settings,"importSettings.nodeNameMethod",1);
            Set(settings,"instantiationSettings.sceneObjectCreation",1);
            Set(settings,"instantiationSettings.mask",-1);
            if(settings.ApplyModifiedPropertiesWithoutUndo())AssetDatabase.WriteImportSettingsIfDirty(path);
        }

        static void Set(SerializedObject settings,string path,int value)
        { var property=settings.FindProperty(path);if(property!=null)property.intValue=value; }

        static string Failure(string path,string name,GameObject model)
        {
            var importer=AssetImporter.GetAtPath(path);
            string reason=model==null?"No model prefab was produced":"The imported model is incomplete";
            if(name=="Dog"&&model!=null)reason="Dog did not import all 17 Legacy animation clips";
            if(path.EndsWith(".gltf",StringComparison.OrdinalIgnoreCase)&&
                (importer==null||importer.GetType().FullName!="GLTFast.Editor.GltfImporter"))
                return reason+": "+path+". Unity glTFast 6.14.1 must finish installing in Package Manager before import.";
            var errors=new List<string>();
            if(importer!=null)
            {
                var serialized=new SerializedObject(importer);
                var report=serialized.FindProperty("reportItems");
                if(report!=null&&report.isArray)
                    for(int i=0;i<report.arraySize&&errors.Count<6;i++)
                    {
                        var item=report.GetArrayElementAtIndex(i);
                        var type=item.FindPropertyRelative("type");
                        var code=item.FindPropertyRelative("code");
                        var messages=item.FindPropertyRelative("messages");
                        if(type==null||code==null)continue;
                        var level=(LogType)type.intValue;
                        if(level!=LogType.Error&&level!=LogType.Exception&&level!=LogType.Assert)continue;
                        var arguments=messages!=null&&messages.isArray?
                            Enumerable.Range(0,messages.arraySize).Select(j=>messages.GetArrayElementAtIndex(j).stringValue).ToArray():Array.Empty<string>();
                        errors.Add(new LogItem(level,(LogCode)(uint)code.intValue,arguments).ToString());
                    }
            }
            return reason+" after dependency reimport: "+path+". "+
                (errors.Count>0?string.Join(" | ",errors):"Select this model in Project to inspect its import report and any earlier Console error.");
        }
    }
}
#endif

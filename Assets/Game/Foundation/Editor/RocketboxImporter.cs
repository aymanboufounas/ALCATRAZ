#if UNITY_EDITOR
using System;
using System.IO;
using UnityEngine;
using UnityEditor;

namespace Blackstone.Foundation.Editor
{
    public sealed class RocketboxImporter : AssetPostprocessor
    {
        public const string Characters="Assets/Game/Resources/BlackstoneFoundation/Characters/";
        public const string Animations="Assets/Game/Foundation/Animations/Rocketbox/";
        public static bool IsSource(string path) => path.EndsWith(".fbx",StringComparison.OrdinalIgnoreCase)
            && (path.StartsWith(Characters,StringComparison.Ordinal)||path.StartsWith(Animations,StringComparison.Ordinal));
        void OnPreprocessModel()
        {
            if(IsSource(assetPath))Configure((ModelImporter)assetImporter,assetPath);
        }
        public static void Configure(ModelImporter importer,string path)
        {
            importer.animationType=ModelImporterAnimationType.Generic;
            importer.avatarSetup=ModelImporterAvatarSetup.CreateFromThisModel;
            importer.globalScale=1;importer.useFileScale=true;importer.bakeAxisConversion=true;
            importer.motionNodeName="Bip01";importer.preserveHierarchy=true;
            importer.importCameras=false;importer.importLights=false;importer.importBlendShapes=path.StartsWith(Characters,StringComparison.Ordinal);
            importer.importNormals=ModelImporterNormals.Import;importer.importTangents=ModelImporterTangents.CalculateMikk;
            importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;
            importer.materialLocation=ModelImporterMaterialLocation.InPrefab;
            importer.importAnimation=path.StartsWith(Animations,StringComparison.Ordinal);
            importer.animationCompression=ModelImporterAnimationCompression.Off;
            if(!importer.importAnimation)return;
            var defaults=importer.defaultClipAnimations;
            if(defaults==null||defaults.Length==0)return;
            string name=Path.GetFileNameWithoutExtension(path);
            bool loop=name=="Idle"||name=="WalkSlow"||name=="Walk"||name=="WalkFast"||name=="Run"||name=="RunFast"||name=="Crouch"||name=="Seated";
            foreach(var clip in defaults)
            {
                clip.name=name;clip.loopTime=loop;clip.loopPose=loop;clip.wrapMode=loop?WrapMode.Loop:WrapMode.Once;
                clip.lockRootPositionXZ=true;clip.lockRootHeightY=true;clip.lockRootRotation=true;
                clip.keepOriginalPositionXZ=true;clip.keepOriginalPositionY=true;clip.keepOriginalOrientation=true;
            }
            importer.clipAnimations=defaults;
        }
        Material OnAssignMaterialModel(Material source,Renderer renderer)
        {
            if(!assetPath.StartsWith(Characters,StringComparison.Ordinal))return null;
            string path=Path.GetDirectoryName(assetPath).Replace('\\','/')+"/"+source.name+".mat";
            return AssetDatabase.LoadAssetAtPath<Material>(path);
        }
        void OnPreprocessTexture()
        {
            if(!assetPath.StartsWith(Characters,StringComparison.Ordinal))return;
            var importer=(TextureImporter)assetImporter;
            bool normal=assetPath.IndexOf("_normal",StringComparison.OrdinalIgnoreCase)>=0;
            importer.textureType=normal?TextureImporterType.NormalMap:TextureImporterType.Default;
            importer.sRGBTexture=!normal&&assetPath.IndexOf("_specular",StringComparison.OrdinalIgnoreCase)<0;
            importer.maxTextureSize=2048;importer.mipmapEnabled=true;importer.isReadable=false;
        }
        void OnPostprocessAnimation(GameObject root,AnimationClip clip)
        {
            if(!assetPath.StartsWith(Animations,StringComparison.Ordinal))return;
            bool turning=Path.GetFileNameWithoutExtension(assetPath).StartsWith("Turn",StringComparison.Ordinal);
            foreach(var binding in AnimationUtility.GetCurveBindings(clip))
            {
                bool rootBone=binding.path=="Bip01"||binding.path.EndsWith("/Bip01",StringComparison.Ordinal);
                string property=binding.propertyName;
                bool horizontal=rootBone&&(property=="m_LocalPosition.x"||property=="m_LocalPosition.z");
                horizontal |= string.IsNullOrEmpty(binding.path)&&(property=="RootT.x"||property=="RootT.z"||property=="MotionT.x"||property=="MotionT.z");
                bool rotation=turning&&(rootBone||string.IsNullOrEmpty(binding.path))
                    &&(property.StartsWith("m_LocalRotation.",StringComparison.Ordinal)||property.StartsWith("localEulerAnglesRaw.",StringComparison.Ordinal)
                       ||property.StartsWith("RootQ.",StringComparison.Ordinal)||property.StartsWith("MotionQ.",StringComparison.Ordinal));
                if(!horizontal&&!rotation)continue;
                var curve=AnimationUtility.GetEditorCurve(clip,binding);if(curve==null||curve.length==0)continue;
                AnimationUtility.SetEditorCurve(clip,binding,AnimationCurve.Constant(0,Mathf.Max(.01f,clip.length),curve.Evaluate(0)));
            }
            clip.EnsureQuaternionContinuity();
        }
    }
}
#endif

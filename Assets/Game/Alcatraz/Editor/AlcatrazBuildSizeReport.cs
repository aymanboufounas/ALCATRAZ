#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Blackstone.Alcatraz.Editor
{
    // Reports a real player build, rather than estimating it from source files.
    public sealed class AlcatrazBuildSizeReport : IPostprocessBuildWithReport
    {
        [Serializable] sealed class SizeReport
        {
            public string builtUtc,target,outputPath,result;
            public long reportedPlayerBytes;
            public string scope="Unity BuildReport totalSize; source checkout size and runtime VRAM are different measurements.";
        }
        public int callbackOrder=>100;
        public void OnPostprocessBuild(BuildReport report)
        {
            if(report.summary.result!=BuildResult.Succeeded)return;
            var size=new SizeReport{builtUtc=DateTime.UtcNow.ToString("o"),target=report.summary.platform.ToString(),
                outputPath=report.summary.outputPath,result=report.summary.result.ToString(),
                reportedPlayerBytes=checked((long)report.summary.totalSize)};
            try
            {
                string directory=Path.Combine("Builds","Reports");Directory.CreateDirectory(directory);
                string path=Path.Combine(directory,"LatestPlayerBuild.json");
                File.WriteAllText(path,JsonUtility.ToJson(size,true));
                Debug.Log("Player build size: "+size.reportedPlayerBytes+" bytes. Report: "+path);
            }
            catch(Exception error){Debug.LogWarning("The build succeeded, but its size report could not be saved: "+error.Message);}
        }
    }
}
#endif

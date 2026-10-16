#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace Blackstone.Alcatraz.Editor
{
    // A successful build is measured, never padded to satisfy a size target.
    // The receipt and its digest establish file integrity, not Unity authenticity
    // or evidence that somebody launched and completed the game.
    public sealed class AlcatrazBuildSizeReport : IPostprocessBuildWithReport
    {
        public const long TargetInstalledBytes = 5000000000L;
        public const string ReceiptName = "AlcatrazPlayerBuildReceipt.json";
        const string LatestReport = "Builds/Reports/LatestPlayerBuild.json";

        [Serializable] sealed class SourceState
        {
            public bool available, dirty;
            public string commit, error;
        }
        [Serializable] sealed class InstalledFile
        {
            public string path, sha256, unityRole;
            public long bytes, unityReportedBytes;
            public bool reportedByUnity;
        }
        [Serializable] sealed class PackedContributor
        {
            public string sourceAssetPath;
            public long packedBytes;
        }
        [Serializable] sealed class SizeReport
        {
            public int schemaVersion = 2;
            public string receiptKind = "AlcatrazWindowsPlayer";
            public string builtUtc, target, outputPath, executable, result, buildGuid;
            public string unityVersion, productName, applicationVersion, buildOptions;
            public string packedAssetsStatus = "Packed-asset appendix unavailable.";
            public long buildOptionsValue, reportedPlayerBytes, installedPlayerBytes;
            public long targetInstalledBytes = TargetInstalledBytes;
            public double installedDecimalGB, installedGiB;
            public bool targetMet, contextCaptured, developmentBuild, packedAssetsAvailable;
            public bool runtimeVerified = false, finishedGameVerified = false;
            public string[] scenes, unreportedFiles;
            public SourceState source;
            public InstalledFile[] installedFiles;
            public PackedContributor[] largestPackedContributors;
            public string scope = "Installed logical file bytes, excluding this receipt and its digest. "
                + "Unity summary and packed-object sizes are reported separately. Archive, source checkout, VRAM, "
                + "gameplay completion and launch verification are not measured by this receipt.";
            public string integrity = "The adjacent SHA-256 detects accidental or one-sided receipt edits. "
                + "It is not a signature or independent proof of a Unity build; both files can be forged.";
        }

        sealed class BuildContext
        {
            public string output;
            public BuildTarget target;
            public BuildOptions options;
            public string[] scenes;
            public SourceState source;
        }
        static BuildContext activeBuild;
        public int callbackOrder => 100;

        // Capture the actual invocation. EditorBuildSettings can differ from the
        // scene array passed to BuildPipeline and cannot prove a complete export.
        public static BuildReport BuildPlayer(BuildPlayerOptions options)
        {
            if (activeBuild != null) throw new InvalidOperationException("An Alcatraz build is already in progress.");
            var context = new BuildContext { output = Path.GetFullPath(options.locationPathName),
                target = options.target, options = options.options,
                scenes = options.scenes != null ? (string[])options.scenes.Clone() : new string[0],
                source = ReadSourceState() };
            InvalidateReceipt(context.output);
            activeBuild = context;
            try
            {
                var report = BuildPipeline.BuildPlayer(options);
                // Measure only after all postprocessors have completed. A later
                // failing callback must not leave an earlier qualifying receipt.
                if (report != null && report.summary.result == BuildResult.Succeeded) TryWriteReceipt(report, context);
                return report;
            }
            finally { activeBuild = null; }
        }

        static void InvalidateReceipt(string output)
        {
            string root = Path.GetDirectoryName(output);
            foreach (string path in new[] { Path.Combine(root, ReceiptName), LatestReport })
            {
                if (File.Exists(path)) File.Delete(path);
                if (File.Exists(path + ".sha256")) File.Delete(path + ".sha256");
            }
        }

        public void OnPostprocessBuild(BuildReport report)
        {
            if (activeBuild == null && report.summary.result == BuildResult.Succeeded) TryWriteReceipt(report, null);
        }

        static void TryWriteReceipt(BuildReport report, BuildContext context)
        {
            try
            {
                string output = Path.GetFullPath(report.summary.outputPath);
                bool captured = context != null && context.output == output && context.target == report.summary.platform
                    && context.options == report.summary.options;
                var size = new SizeReport { builtUtc = DateTime.UtcNow.ToString("o"), target = report.summary.platform.ToString(),
                    outputPath = output, executable = Path.GetFileName(output), result = report.summary.result.ToString(),
                    buildGuid = report.summary.guid.ToString(), unityVersion = Application.unityVersion,
                    productName = Application.productName, applicationVersion = Application.version,
                    buildOptions = report.summary.options.ToString(), buildOptionsValue = (long)report.summary.options,
                    developmentBuild = (report.summary.options & BuildOptions.Development) != 0,
                    reportedPlayerBytes = checked((long)report.summary.totalSize), contextCaptured = captured,
                    scenes = captured ? context.scenes : new string[0],
                    source = captured ? context.source : new SourceState { error = "Build invocation was not captured by the Alcatraz wrapper." },
                    installedFiles = new InstalledFile[0], unreportedFiles = new string[0],
                    largestPackedContributors = new PackedContributor[0] };
                string root = Path.GetDirectoryName(output);
                if (report.summary.platform == BuildTarget.StandaloneWindows64 && File.Exists(output))
                {
                    var reported = new Dictionary<string, BuildFile>(StringComparer.OrdinalIgnoreCase);
                    foreach (var file in report.GetFiles())
                    {
                        if (string.IsNullOrEmpty(file.path)) continue;
                        string path = Path.GetFullPath(file.path);
                        if (Within(root, path)) reported[path] = file;
                    }
                    var files = new List<InstalledFile>();
                    foreach (string path in EnumerateRegularFiles(root))
                    {
                        string relative = path.Substring(root.Length + 1).Replace('\\', '/');
                        if (relative == ReceiptName || relative == ReceiptName + ".sha256") continue;
                        var before = new FileInfo(path);
                        long length = before.Length; DateTime modified = before.LastWriteTimeUtc;
                        string hash = HashFile(path);
                        before.Refresh();
                        if (before.Length != length || before.LastWriteTimeUtc != modified)
                            throw new IOException("A player file changed while its receipt was being measured.");
                        bool known = reported.TryGetValue(path, out var unity);
                        files.Add(new InstalledFile { path = relative, bytes = length, sha256 = hash,
                            reportedByUnity = known, unityReportedBytes = known ? checked((long)unity.size) : 0,
                            unityRole = known ? unity.role : "not present in this Unity BuildReport" });
                        size.installedPlayerBytes = checked(size.installedPlayerBytes + length);
                    }
                    size.installedFiles = files.OrderBy(file => file.path, StringComparer.Ordinal).ToArray();
                    size.unreportedFiles = files.Where(file => !file.reportedByUnity).Select(file => file.path).ToArray();
                    CollectPackedContributors(report, size);
                }
                size.installedDecimalGB = size.installedPlayerBytes / 1000000000d;
                size.installedGiB = size.installedPlayerBytes / 1073741824d;
                size.targetMet = size.installedPlayerBytes >= TargetInstalledBytes;
                string json = JsonUtility.ToJson(size, true) + "\n";
                WriteWithDigest(LatestReport, json);
                if (report.summary.platform == BuildTarget.StandaloneWindows64 && File.Exists(output))
                    WriteWithDigest(Path.Combine(root, ReceiptName), json);
                Debug.Log("Installed player: " + size.installedPlayerBytes + " bytes; 5,000,000,000-byte target "
                    + (size.targetMet ? "met" : "not met") + ". Receipt: " + LatestReport
                    + ". File audit and Unity gameplay acceptance are still required.");
            }
            catch (Exception error)
            { Debug.LogWarning("The build succeeded, but its player audit could not be saved: " + error.Message); }
        }

        static bool Within(string root, string path)
        { return path.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase); }

        static IEnumerable<string> EnumerateRegularFiles(string root)
        {
            var pending = new Stack<string>(); pending.Push(root);
            while (pending.Count > 0)
                foreach (string path in Directory.EnumerateFileSystemEntries(pending.Pop()))
                {
                    var attributes = File.GetAttributes(path);
                    if ((attributes & FileAttributes.ReparsePoint) != 0)
                        throw new IOException("A player export contains a symbolic link or reparse point; export regular files before qualifying it.");
                    if ((attributes & FileAttributes.Directory) != 0) pending.Push(path);
                    else yield return path;
                }
        }

        static void CollectPackedContributors(BuildReport report, SizeReport size)
        {
            // Official UnityCsReference 6000.0: BuildReport.GetFiles(),
            // packedAssets[].contents[].sourceAssetPath / packedSize. These are
            // packed-object contributions, not an additive installed-file total.
            // https://github.com/Unity-Technologies/UnityCsReference/tree/6000.0/Modules/BuildReportingEditor/Managed
            try
            {
                var totals = new Dictionary<string, long>(StringComparer.Ordinal);
                var packs = report.packedAssets;
                if (packs == null) return;
                foreach (var pack in packs)
                {
                    if (pack == null) continue;
                    var contents = pack.contents;
                    if (contents == null) continue;
                    foreach (var asset in contents)
                    {
                        string path = string.IsNullOrEmpty(asset.sourceAssetPath) ? "(built-in or unidentified)" : asset.sourceAssetPath;
                        totals.TryGetValue(path, out long previous);
                        totals[path] = checked(previous + (long)asset.packedSize);
                    }
                }
                size.packedAssetsAvailable = totals.Count > 0;
                size.packedAssetsStatus = size.packedAssetsAvailable ? "Packed-object contributions available; not installed-file totals."
                    : "This build report has no packed-asset appendix; no contributor sizes are claimed.";
                size.largestPackedContributors = totals.OrderByDescending(item => item.Value).Take(30)
                    .Select(item => new PackedContributor { sourceAssetPath = item.Key, packedBytes = item.Value }).ToArray();
            }
            catch (Exception error)
            { size.packedAssetsStatus = "Optional contributor appendix unavailable (" + error.GetType().Name + ")."; }
        }

        static SourceState ReadSourceState()
        {
            try
            {
                string commit = QueryGit("rev-parse HEAD").Trim();
                if (commit.Length != 40 && commit.Length != 64) throw new InvalidOperationException("Git object ID unavailable.");
                return new SourceState { available = true, commit = commit,
                    dirty = QueryGit("status --porcelain --untracked-files=normal").Length != 0, error = "" };
            }
            catch (Exception error)
            { return new SourceState { error = "Source provenance unavailable (" + error.GetType().Name + ")." }; }
        }

        static string QueryGit(string arguments)
        {
            var start = new ProcessStartInfo { FileName = "git", Arguments = arguments,
                WorkingDirectory = Directory.GetParent(Application.dataPath).FullName,
                UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            using (var process = Process.Start(start))
            {
                var output = process.StandardOutput.ReadToEndAsync();
                var errors = process.StandardError.ReadToEndAsync();
                if (!process.WaitForExit(10000)) { process.Kill(); throw new IOException("Git provenance check timed out."); }
                string text = output.GetAwaiter().GetResult(); errors.GetAwaiter().GetResult();
                if (process.ExitCode != 0) throw new IOException("Git provenance check failed.");
                return text;
            }
        }

        static string HashFile(string path)
        {
            using (var hash = SHA256.Create())
            using (var input = File.OpenRead(path)) return Hex(hash.ComputeHash(input));
        }
        static string Hex(byte[] bytes) { return BitConverter.ToString(bytes).Replace("-", "").ToLowerInvariant(); }
        static void WriteWithDigest(string path, string json)
        {
            string directory = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(directory)) Directory.CreateDirectory(directory);
            byte[] data = new UTF8Encoding(false).GetBytes(json);
            File.WriteAllBytes(path, data);
            using (var hash = SHA256.Create())
                File.WriteAllText(path + ".sha256", Hex(hash.ComputeHash(data)) + "  " + Path.GetFileName(path) + "\n", new UTF8Encoding(false));
        }
    }
}
#endif

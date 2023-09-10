using UnityEditor;
using System;

class Builder
{
    static void Build()
    {
        string[] arguments = Environment.GetCommandLineArgs();
        
        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
        buildPlayerOptions.scenes = new[] {"Assets/Scenes/SampleScene.unity"};
        buildPlayerOptions.locationPathName = arguments[arguments.Length-1];
        string plataform = arguments[arguments.Length-2];
        
        if (plataform == "webgl") buildPlayerOptions.target = BuildTarget.WebGL;
        else if (plataform == "linux") buildPlayerOptions.target = BuildTarget.StandaloneLinux64;
        else if (plataform == "android" || plataform == "google"){
            buildPlayerOptions.target = BuildTarget.Android;
            EditorUserBuildSettings.buildAppBundle = plataform == "google";
            AndroidArchitecture aac = plataform == "android"? AndroidArchitecture.ARMv7: (AndroidArchitecture.ARM64 | AndroidArchitecture.ARMv7);
            PlayerSettings.Android.targetArchitectures = aac;

            PlayerSettings.Android.keystoreName = "/directory/to/user.keystore";
            PlayerSettings.Android.keystorePass = "";
            PlayerSettings.Android.keyaliasName = "";
            PlayerSettings.Android.keyaliasPass = "";
        }
        else buildPlayerOptions.target = BuildTarget.StandaloneWindows64;
        
        BuildPipeline.BuildPlayer(buildPlayerOptions);

        //var errorMsg = BuildPipeline.BuildPlayer(sceneNames, buildPath, BuildTarget.StandaloneLinux64, buildOptions);
    }

}
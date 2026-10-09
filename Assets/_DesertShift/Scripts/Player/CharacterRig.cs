using System;
using System.Collections.Generic;
using UnityEngine;

namespace DesertShift.Player
{
    [DefaultExecutionOrder(-150)]
    public sealed class CharacterRig : MonoBehaviour
    {
        [Serializable] public struct BoneMapping { public string humanName; public Transform bone; }
        public BoneMapping[] humanBones;
        public Animator animator;
        Avatar runtimeAvatar;
        Avatar boneAnimationAvatar;
        public Avatar HumanoidAvatar => runtimeAvatar;
        public bool AvatarReady => runtimeAvatar != null && runtimeAvatar.isValid && runtimeAvatar.isHuman;
        void Awake()
        {
            if (animator == null) animator = GetComponent<Animator>();
            var transforms = GetComponentsInChildren<Transform>();
            var pose = new Quaternion[transforms.Length];
            for (int i = 0; i < transforms.Length; i++)
            {
                pose[i] = transforms[i].localRotation;
                if (transforms[i] != transform) transforms[i].localRotation = Quaternion.identity;
            }
            var human = new List<HumanBone>();
            foreach (var mapping in humanBones)
                if (mapping.bone != null)
                    human.Add(new HumanBone { boneName = mapping.bone.name, humanName = mapping.humanName,
                        limit = new HumanLimit { useDefaultValues = true } });
            var skeleton = new SkeletonBone[transforms.Length];
            for (int i = 0; i < transforms.Length; i++)
                skeleton[i] = new SkeletonBone { name = transforms[i].name, position = transforms[i].localPosition,
                    rotation = transforms[i].localRotation, scale = transforms[i].localScale };
            var description = new HumanDescription { human = human.ToArray(), skeleton = skeleton,
                upperArmTwist = .5f, lowerArmTwist = .5f, upperLegTwist = .5f, lowerLegTwist = .5f,
                armStretch = .05f, legStretch = .05f, feetSpacing = 0, hasTranslationDoF = false };
            runtimeAvatar = AvatarBuilder.BuildHumanAvatar(gameObject, description);
            runtimeAvatar.name = "AV_" + gameObject.name + "_Humanoid";
            if (!runtimeAvatar.isValid || !runtimeAvatar.isHuman)
                Debug.LogError(gameObject.name + " humanoid Avatar failed validation. Use the scene validation tool.", this);
            // The supplied original clips are direct bone curves, so they use a Generic
            // playback Avatar. The same weighted skeleton exposes HumanoidAvatar for
            // retargeting humanoid clips without changing the model or its skin weights.
            boneAnimationAvatar = AvatarBuilder.BuildGenericAvatar(gameObject, "Root");
            boneAnimationAvatar.name = "AV_" + gameObject.name + "_BoneClips";
            animator.avatar = boneAnimationAvatar;
            for (int i = 0; i < transforms.Length; i++) transforms[i].localRotation = pose[i];
            animator.applyRootMotion = false;
        }
        void OnDestroy()
        {
            if (runtimeAvatar != null) Destroy(runtimeAvatar);
            if (boneAnimationAvatar != null) Destroy(boneAnimationAvatar);
        }
    }
}

using UnityEngine;

namespace Blackstone.Foundation
{
    // Uniform UI scaling preserves text and map proportions on any aspect ratio.
    public readonly struct FoundationViewport
    {
        public readonly float Scale, Width, Height;
        public FoundationViewport(int pixelWidth, int pixelHeight)
        {
            pixelWidth = Mathf.Max(1, pixelWidth); pixelHeight = Mathf.Max(1, pixelHeight);
            Scale = Mathf.Min(pixelWidth / 1600f, pixelHeight / 900f);
            Width = pixelWidth / Scale; Height = pixelHeight / Scale;
        }
        public Matrix4x4 Matrix => Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(Scale, Scale, 1));
        public Rect Equipment => new Rect(Width-341, Height-148, 316, 112);
        public Rect Map(bool supplied) => supplied
            ? new Rect(25, Height-226, 231, 154) : new Rect(25, Height-284, 140, 210);
        public Rect InventoryCard(int index) => new Rect(Width-341, 123+index*108, 316, 100);
    }
}

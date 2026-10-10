# Neural dialogue attribution

All 68 current dialogue WAVs were generated locally from original Blackstone Island scripts using the **en_US-libritts_r-medium** Piper voice model. Five speaker identities and different speaking timings were used for the cast. Packaged files are normalized, trimmed generated recordings; no voice engine, model weights or training recordings are bundled.

- Model: [rhasspy/piper-voices — LibriTTS-R medium](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/libritts_r/medium), produced by the Piper voice project.
- Source corpus: [LibriTTS-R, OpenSLR resource 141](https://www.openslr.org/141/), a restored multi-speaker English corpus derived from LibriTTS/LibriSpeech and public-domain LibriVox readings. The source corpus is distributed under **CC BY 4.0**.
- License: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
- Local synthesis engine: [OHF-Voice Piper](https://github.com/OHF-Voice/piper1-gpl). The GPL engine was used separately during authoring; its executable, libraries and model weights are not redistributed in this project.
- Model checksum, speaker IDs, clip durations and generated-file SHA-256 hashes: `VoiceProduction_Provenance.json`.

The use of synthesized voices does not imply endorsement by the model authors or corpus readers. New sound effects, footstep variations, card sounds, ambience and music in `Assets/Game/Audio` are original procedural recordings. The earlier scratch voice authoring script is retained as source only; the current chapter uses the neural WAVs.

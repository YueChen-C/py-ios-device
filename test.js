var TIMEBASE_NUMER = 125;
var TIMEBASE_DENOM = 3;// input: num_cores - the number of FSTP cores.;
// input: num_gps - the number of GTP GPs.;
// we default initialize the inputs so that generate_derived_ctr_plists.py does not deduce that they are counters
var num_cores = 4;
var num_gps = 4;
var _d56cff6c89d6a3f5f8561cd89f1b36b2760c125d908074d984bc36678982991a = 768;
var _55d0c180ad87ec962138c5c289baadd6969fdd2cd21ef68ab1f91190b6c33812 = 32;
var TileWidth = 0;
var TileHeight = 0;
var _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6 = (1000.0 / 24.0);

// name: GPU Time
// description: GPU Time in nSec
// type: Count
function GPUTime() {
    return MTLStat_nSec;
}

// name: Vertex Pipeline %
// description: % of vertex processing
// type: Percentage
function VertexPipelinePercent() {
    return (MTLStatTotalGPUCycles_vtx * 100) / (MTLStatTotalGPUCycles_frg + MTLStatTotalGPUCycles_vtx);
}

// name: Fragment Pipeline %
// description: % of fragment processing
// type: Percentage
function FragmentPipelinePercent() {
    return (MTLStatTotalGPUCycles_frg * 100) / (MTLStatTotalGPUCycles_frg + MTLStatTotalGPUCycles_vtx);
}

// name: Shader Core Vertex Utilization %
// description: % Shader Core Vertex Utilization
// type: Percentage
function ShaderCoreVertexUtilization() {
    return _4bb4a72bfa974f38e0143eef87e93ae69847e8612684f014350fb4a8c0692050_norm_vtx / (_d56cff6c89d6a3f5f8561cd89f1b36b2760c125d908074d984bc36678982991a * num_cores);
}

// name: Shader Core Fragment Utilization %
// description: % Shader Core Fragment Utilization
// type: Percentage
function ShaderCoreFragmentUtilization() {
    return _367a60a3f4d39b45114c57a560ad1bad4f9f62798346ead3a98f790ad32537a6_norm_frg / (_d56cff6c89d6a3f5f8561cd89f1b36b2760c125d908074d984bc36678982991a * num_cores);
}

// name: Shader Core Compute Utilization %
// description: % Shader Core Compute Utilization
// type: Percentage
function ShaderCoreComputeUtilization() {
    return _6b3a9b25a65b692ad1039bcc4c052d5a85e40a9410946c0cdf5dc85d993e2131_norm / (_d56cff6c89d6a3f5f8561cd89f1b36b2760c125d908074d984bc36678982991a * num_cores);
}

// name: VS ALU Instructions
// description: VS ALU Instructions
// type: Count
function VSALUInstructions() {
    return _55d0c180ad87ec962138c5c289baadd6969fdd2cd21ef68ab1f91190b6c33812 * _c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2_vtx * 4;
}

// name: VS ALU FP32 Instructions %
// description: VS ALU FP32 Instructions
// type: Percentage
function VSALUF32Percent() {
    return 100 * (_8e70441b8b0d9ded3ed900ec761f9f5960b106c5a304b44d62781621d5d1861a_vtx * 16) / VSALUInstructions();
}

// name: VS ALU FP16 Instructions %
// description: VS ALU FP16 Instructions
// type: Percentage
function VSALUF16Percent() {
    return 100 * (_82b2f93079459b00fb869444cfcf44604cc1a91d28078cd6bfd7bb6ea6ba423d_vtx * 16) / VSALUInstructions();
}

// name: VS ALU 32-bit Integer and Conditional Instructions %
// description: VS ALU Select, Conditional, 32-bit Integer and Boolean Instructions
// type: Percentage
function VSALUInt32AndCondPercent() {
    return 100 * (_23c51175314006fa4b6798dcb173a814349e2e5947244cfdba868be736d2bc03_vtx * 16) / VSALUInstructions();
}

// name: VS ALU Integer and Complex Instructions %
// description: VS ALU Integer and Complex Instructions
// type: Percentage
function VSALUIntAndComplexPercent() {
    return 100 * (_827783963eafa9275a53fc2b3ef13214ab90939fcc81572c4260e2eac9bd2acb_vtx * 16) / VSALUInstructions();
}

// name: FS ALU Instructions
// description: FS ALU Instructions
// type: Count
function FSALUInstructions() {
    return _55d0c180ad87ec962138c5c289baadd6969fdd2cd21ef68ab1f91190b6c33812 * _c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2_frg * 4;
}

// name: FS ALU FP32 Instructions %
// description: FS ALU FP32 Instructions
// type: Percentage
function FSALUF32Percent() {
    return 100 * (_8e70441b8b0d9ded3ed900ec761f9f5960b106c5a304b44d62781621d5d1861a_frg * 16) / FSALUInstructions();
}

// name: FS ALU FP16 Instructions %
// description: FS ALU FP16 Instructions
// type: Percentage
function FSALUF16Percent() {
    return 100 * (_82b2f93079459b00fb869444cfcf44604cc1a91d28078cd6bfd7bb6ea6ba423d_frg * 16) / FSALUInstructions();
}

// name: FS ALU 32-bit Integer and Conditional Instructions %
// description: FS ALU Select, Conditional, 32-bit Integer and Boolean Instructions
// type: Percentage
function FSALUInt32AndCondPercent() {
    return 100 * (_23c51175314006fa4b6798dcb173a814349e2e5947244cfdba868be736d2bc03_frg * 16) / FSALUInstructions();
}

// name: FS ALU Integer and Complex Instructions %
// description: FS ALU Integer and Complex Instructions
// type: Percentage
function FSALUIntAndComplexPercent() {
    return 100 * (_827783963eafa9275a53fc2b3ef13214ab90939fcc81572c4260e2eac9bd2acb_frg * 16) / FSALUInstructions();
}

// name: CS ALU Instructions
// description: CS ALU Instructions
// type: Count
function CSALUInstructions() {
    return _55d0c180ad87ec962138c5c289baadd6969fdd2cd21ef68ab1f91190b6c33812 * _c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2_cmp * 4;
}

// name: CS ALU FP32 Instructions %
// description: CS ALU FP32 Instructions
// type: Percentage
function CSALUF32Percent() {
    return 100 * (_8e70441b8b0d9ded3ed900ec761f9f5960b106c5a304b44d62781621d5d1861a_cmp * 16) / CSALUInstructions();
}

// name: CS ALU FP16 Instructions %
// description: CS ALU FP16 Instructions
// type: Percentage
function CSALUF16Percent() {
    return 100 * (_82b2f93079459b00fb869444cfcf44604cc1a91d28078cd6bfd7bb6ea6ba423d_cmp * 16) / CSALUInstructions();
}

// name: CS ALU 32-bit Integer and Conditional Instructions %
// description: CS ALU Select, Conditional, 32-bit Integer and Boolean Instructions
// type: Percentage
function CSALUInt32AndCondPercent() {
    return 100 * (_23c51175314006fa4b6798dcb173a814349e2e5947244cfdba868be736d2bc03_cmp * 16) / CSALUInstructions();
}

// name: CS ALU Integer and Complex Instructions %
// description: CS ALU Integer and Complex Instructions
// type: Percentage
function CSALUIntAndComplexPercent() {
    return 100 * (_827783963eafa9275a53fc2b3ef13214ab90939fcc81572c4260e2eac9bd2acb_cmp * 16) / CSALUInstructions();
}

// name: VS Invocations
// description: Number of times vertex shader is invoked
// type: Count
function VSInvocation() {
    return _da2d5f5fd43e7edda6d5635752a29f09d285cf47c2ecd0a1b83b1ba3eddcef55_vtx;
}

// name: FS Invocations
// description: Number of times fragment shader is invoked
// type: Count
function PSInvocation() {
    return _448897b2730c90c177c3e468d3780d048b4ef0c6feb09887550eb9e5e71373c0 * 32;
}

// name: CS Invocations
// description: Number of times compute shader is invoked
// type: Count
function CSInvocation() {
    return _e319ade855d6fde34a28ecc2a2266f86d6d99b5e413e08b4884629844476c571 + _83b4492da25346ffc6c1820a633ef533874dda8e2939056928ffd92384775e38 + _a3104b8f0a1ab0931761cf851c8ac5ce3212eff30deff24a1f9a5ef67453adca + _bd9f890bd3bdbe08af5851fb3dfa228a36a5e54b72c7d74d5985af75bafa6217;
}

// name: Vertex Rate
// description: Number of vertices processed per nanosecond
// type: Rate
function VerticesPerNSec() {
    return VSInvocation() / (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e_vtx * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6);
}

// name: Primitive Rate
// description: Number of primitives processed per nanosecond
// type: Rate
function PrimitivesPerNSec() {
    return PrimitivesSubmitted() / (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e_vtx * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6);
}

// name: Pixel Rate
// description: Number of fragments processed per nanosecond
// type: Rate
function PixelsPerNSec() {
    return PSInvocation() / (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e_frg * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6);
}

// name: Pixel To Vertex Ratio
// description: Number of pixels per vertex
// type: Rate
function PixelToVertexRatio() {
    return PSInvocation() / VSInvocation();
}

// name: Pixel Per Triangle
// description: Number of pixels per triangle
// type: Rate
function PixelPerTriangle() {
    return PSInvocation() / PrimitivesSubmitted();
}

// name: Draw Calls
// description: Number of draw calls
// type: Count
function DrawCalls() {
    return _f6c3f9b835930ff834f081ab2dfaacbdfbe451f6f2100abcdecec1c3c7999e0b_vtx / num_gps;
}

// name: Vertex Count
// description: Number of vertices being submitted to input assembly
// type: Count
function VerticesSubmitted() {
    return _427543bc9ae51e5f3520629f8bbe54e3a18d14de616f0c418cf7190a55cd7d9c_vtx;
}

// name: Vertices Reused
// description: Number of vertices being reused
// type: Count
function VerticesReused() {
    return VerticesSubmitted() - VSInvocation();
}

// name: Vertices Reused %
// description: % of vertices being reused
// type: Percentage
function VerticesReusedPercent() {
    return (VerticesSubmitted() - VSInvocation()) * 100 / VerticesSubmitted();
}

// name: Primitives Submitted
// description: Number of primitives gathered by input assembly
// type: Count
function PrimitivesSubmitted() {
    return _0c33d520d54b5d5f84a71398d6ae71152426874088128bd3c18ad78df5f6d8b7_vtx;
}

// name: Primitives Rasterized
// description: Number of primitives rasterized
// type: Count
function PrimitivesRasterized() {
    return _2d3c257f33af88b8488658fb5b6a86f64cb02169b680e1250d3f37d373a4197f_vtx;
}

// name: Primitives Rendered %
// description: % of primitives rasterized
// type: Percentage
function PrimitivesRasterizedPercent() {
    return PrimitivesRasterized() * 100 / PrimitivesSubmitted();
}

// name: Primitives Clipped
// description: Number of primitives being clipped
// type: Count
function ClippedPrimitives() {
    return _29091329a1ff8f86d51ab9b84da709de18ba8aa1d94003a519a0663db7add4a1_vtx + _6169af48fcc4f2c5d036243de6acd153bd0308c644bd7e4afc67499ad1aef2c7_vtx;
}

// name: Primitives Clipped %
// description: % of primitives clipped
// type: Percentage
function ClippedPrimitivesPercent() {
    return ClippedPrimitives() * 100 / PrimitivesSubmitted();
}

// name: Back-Facing Cull Primitives
// description: Number of primitives being culled due to being back-facing
// type: Count
function BackFaceCullPrims() {
    return _b466c606c4b7e98fcde3adad24a292c946f1f1130670918262ebf9f660e0173c_vtx;
}

// name: Small Triangle Cull Primitives
// description: Number of primitives being culled due to having small triangles
// type: Count
function SmallTriangleCullPrims() {
    return _01038280d9d6c505432733b12946359b7c301c69b32369f4b921b6fa206c2211_vtx;
}

// name: Back-Facing Cull Primitives %
// description: % of primitives being culled due to being back-facing
// type: Percentage
function BackFaceCullPrimsPercent() {
    return BackFaceCullPrims() * 100 / PrimitivesSubmitted();
}

// name: Small Triangle Cull Primitives %
// description: % of primitives being culled due small area triangles
// type: Percentage
function SmallTriangleCullPrimsPercent() {
    return SmallTriangleCullPrims() * 100 / PrimitivesSubmitted();
}

// name: Guard Band Cull Primitives
// description: Number of primitives being culled due to being outside guard band
// type: Count
function GuardBandCullPrims() {
    return _4b1f5c87264cd5cd23bb5eb652d21194fb7f49f9b1d70433f180b31a7a22dcab_vtx + _4bb4ab3f3e64c565175f4fbe0f75df41b12c3bc2b4242b99cd4a330773d475d4_vtx + _d7b92925765e8d20627989863f1b950ec5d6dffbd815c4c100730b3a7e7801fd_vtx;
}

// name: Guard Band Cull Primitives %
// description: % of primitives being culled due to being outside guard band
// type: Percentage
function GuardBandCullPrimsPercent() {
    return GuardBandCullPrims() * 100 / PrimitivesSubmitted();
}

// name: Off-screen Cull Primitives
// description: Number of primitives being culled due to being off-screen
// type: Count
function OffscreenCullPrims() {
    return _0f9aab25f0863ace3de6f9832139250c806045a7ac0d6f8cf06c682c282005f1_vtx + _dbe3d527893309548e6eebdee711a622433c869e148727cf18e31ae63cf116d3_vtx + _3bd7a95222e8315bf62e84ba01a511e64bd7aa7487bed322a8ac96e4c4e628e1_vtx;
}

// name: Off-screen Cull Primitives %
// description: % of primitives being culled due to being off-screen
// type: Percentage
function OffscreenCullPrimsPercent() {
    return OffscreenCullPrims() * 100 / PrimitivesSubmitted();
}

// name: Fragments Rasterized
// description: Number of fragments rasterized
// type: Count
function FragmentsRasterized() {
    return Math.max(_24be79c8d8f70844505a88372d5027b6f8afd064ccbab97ac3ffe36dd5a0ef2b - _9177fce9b3d9e2a64a816854b3084588e4673c25a1c069c53b5909a77fb853eb, 0.0) * 32 + _9177fce9b3d9e2a64a816854b3084588e4673c25a1c069c53b5909a77fb853eb * TileWidth * TileHeight;
}

// name: Pre Z Pass Count
// description: Pre Z Pass Count
// type: Count
function PreZPassCount() {
    return Math.max(_24be79c8d8f70844505a88372d5027b6f8afd064ccbab97ac3ffe36dd5a0ef2b - _9177fce9b3d9e2a64a816854b3084588e4673c25a1c069c53b5909a77fb853eb, 0.0) * 32 + _9177fce9b3d9e2a64a816854b3084588e4673c25a1c069c53b5909a77fb853eb * TileWidth * TileHeight;
}

// name: Pre Z Fail Count
// description: Pre Z Fail Count
// type: Count
function PreZFailCount() {
    return Math.max(FragmentsRasterized() - PreZPassCount(), 0.0);
}

// name: Pre Z Fail %
// description: % Pre Z Fail
// type: Percentage
function PreZFailCountPercent() {
    return PreZFailCount() * 100 / FragmentsRasterized();
}

// name: Pre Z Pass %
// description: % Pre Z Pass
// type: Percentage
function PreZPassCountPercent() {
    return (PreZPassCount() * 100) / FragmentsRasterized();
}

// name: Pixels Per Tile
// description: Pixels per tile
// type: Count
function PixelsPerTile() {
    return TileWidth * TileHeight;
}

// name: Average Overdraw
// description: Pixel Overdraw
// type: Count
function AverageOverdraw() {
    if (TileWidth * TileHeight > 0) {
        return PSInvocation() / (_eda5bce70befa39e7c6029505c0269211092c220048a502fd8fa2fe30895465b * TileWidth * TileHeight);
    }
    return 0;
}

// name: VS Texture Cache Miss Rate
// description: Percentage of time L1 Texture Cache access is a Miss
// type: Percentage
function VSTextureCacheMissRate() {
    return _19109618d2fc2db66c23fe425a0a19ec06c81f05bb676c40aa572b76891428e6_vtx * 100 / (4.0 * _a8aac8549e9e4a65ca6d3143f42067a6b99241a9a056d0bb512624ee4a91ebc6_vtx + 3.0 * _c0d09f7c090cf4aba7f28554d5fbc55c24426ef3c548a77fa8def417b1823500_vtx + 2.0 * _5a879b789f129c90cada6c1f3173468a47dbc0b43eb8f7e0f8c9602136a0ae0d_vtx + _c5abc56251535ca5b6258367a41d21e518b437e511763fe0d6f0e84ec115ff41_vtx)
}

// name: FS Texture Cache Miss Rate
// description: Percentage of time L1 Texture Cache access is a Miss
// type: Percentage
function FSTextureCacheMissRate() {
    return _19109618d2fc2db66c23fe425a0a19ec06c81f05bb676c40aa572b76891428e6_frg * 100 / (4.0 * _a8aac8549e9e4a65ca6d3143f42067a6b99241a9a056d0bb512624ee4a91ebc6_frg + 3.0 * _c0d09f7c090cf4aba7f28554d5fbc55c24426ef3c548a77fa8def417b1823500_frg + 2.0 * _5a879b789f129c90cada6c1f3173468a47dbc0b43eb8f7e0f8c9602136a0ae0d_frg + _c5abc56251535ca5b6258367a41d21e518b437e511763fe0d6f0e84ec115ff41_frg)
}

// name: VS USC L1 Cache Hits
// description: VS L1 Request Hits
// type: Count
function VSBufferL1RequestHits() {
    return _0b21821861563cc7963f603f7e5e23c70e5a880cfde9c726a3058746854ff882_vtx + _1d940c54d6f56bab841c80e54d16161b2b11c5cc2818b10a3b8e97cd88631cb8_vtx;
}

// name: VS USC L1 Cache Miss Rate
// description: Percentage of time VS USC L1 Requests are misses
// type: Percentage
function VSBufferL1RequestMissRate() {
    var uscL1Requests = _8cd74591f03ed3eb90e0c547b8bf21ae7eed4129053f40570cce56a39a690015_vtx + _3dfa6da703ded5b65a76ddf0aa3f7f28f19b4a624ef77347a925f55bf66a82f5_vtx;
    return 100.0 * Math.max(uscL1Requests - VSBufferL1RequestHits(), 0.0) / Math.max(uscL1Requests, 1.0);
}

// name: FS USC L1 Cache Hits
// description: FS L1 Request Hits
// type: Count
function FSBufferL1RequestHits() {
    return _0b21821861563cc7963f603f7e5e23c70e5a880cfde9c726a3058746854ff882_frg + _1d940c54d6f56bab841c80e54d16161b2b11c5cc2818b10a3b8e97cd88631cb8_frg;
}

// name: FS USC L1 Cache Miss Rate
// description: Percentage of time VS USC L1 Requests are misses
// type: Percentage
function FSBufferL1RequestMissRate() {
    var uscL1Requests = _8cd74591f03ed3eb90e0c547b8bf21ae7eed4129053f40570cce56a39a690015_frg + _3dfa6da703ded5b65a76ddf0aa3f7f28f19b4a624ef77347a925f55bf66a82f5_frg;
    return 100.0 * Math.max(uscL1Requests - FSBufferL1RequestHits(), 0.0) / Math.max(uscL1Requests, 1.0);
}

// name: USC L1 Cache Hits
// description: L1 Request Hits
// type: Count
function BufferL1RequestHits() {
    return _0b21821861563cc7963f603f7e5e23c70e5a880cfde9c726a3058746854ff882 + _1d940c54d6f56bab841c80e54d16161b2b11c5cc2818b10a3b8e97cd88631cb8;
}

// name: USC L1 Cache Miss Rate
// description: Percentage of time USC L1 Requests are misses
// type: Percentage
function BufferL1RequestMissRate() {
    var uscL1Requests = _8cd74591f03ed3eb90e0c547b8bf21ae7eed4129053f40570cce56a39a690015 + _3dfa6da703ded5b65a76ddf0aa3f7f28f19b4a624ef77347a925f55bf66a82f5;
    return 100.0 * Math.max(uscL1Requests - BufferL1RequestHits(), 0.0) / Math.max(uscL1Requests, 1.0);
}

// name: VS Texture samples
// description: VS Texture samples
// type: Count
function VSTextureSamples() {
    return Math.max((_ae304fc8bce5708ffef30935687e442d6bea78f814055a5fe6e3380013d7e507_vtx * 64) - (_f46268d72ed52af703d1b490e193d71605d5c756930dfe9385a5433c9b4f264f_vtx * 4), 0);
}

// name: FS Texture samples
// description: FS Texture samples
// type: Count
function FSTextureSamples() {
    return Math.max((_ae304fc8bce5708ffef30935687e442d6bea78f814055a5fe6e3380013d7e507_frg * 64) - (_f46268d72ed52af703d1b490e193d71605d5c756930dfe9385a5433c9b4f264f_frg * 4), 0);
}

// name: CS Texture samples
// description: CS Texture samples
// type: Count
function CSTextureSamples() {
    return Math.max((_ae304fc8bce5708ffef30935687e442d6bea78f814055a5fe6e3380013d7e507_cmp * 64) - (_f46268d72ed52af703d1b490e193d71605d5c756930dfe9385a5433c9b4f264f_cmp * 4), 0);
}

// name: Texture samples per invocation
// description: VS Texture samples per invocation
// type: Rate
function VSTextureSamplesPerInvocation() {
    return VSTextureSamples() / VSInvocation()
}

// name: Texture samples per invocation
// description: FS Texture samples per invocation
// type: Rate
function FSTextureSamplesPerInvocation() {
    return FSTextureSamples() / PSInvocation()
}

// name: Texture samples per invocation
// description: CS Texture samples per invocation
// type: Rate
function CSTextureSamplesPerInvocation() {
    return CSTextureSamples() / CSInvocation()
}

// name: Average Anisotropic Ratio
// description: Average Anisotropic Ratio
// type: Rate
function AverageAnisotropicRatio() {
    var total = _a7e72038471917bb4125254ae57103538d43fd9d4a233b06a1f248ca3bfc11ac +
        2 * _f76e110e78dbd810843354c733691fcfcd8a5624a46d34e887797178f903ab95 +
        3 * _ce8d2278e7b086459bd4cccfe0b5c79b13ff287bf60e12cb62113d7478856b46 +
        4 * _88a70ef450a839c73c44e1ebf268aa13bf92a5179d6ff3ab45ac0006fa8544cd +
        6 * _851e2825825612ac09e7b26350dc1b5b05998c3aab3198f4a2921768a84dfbbb +
        8 * _b48ed13a188e430f6a5bd26a74642ceabd518b8d290fe8322ebc00a7671bef9d +
        10 * _3b22188697e2c64b322decfb2df85c2cd7a7f264312a00737b10231811737d35 +
        12 * _14a170fde3d2efeda34d72f062b69852d6b927feb012e65ae602e9c41c3565ba +
        14 * _57bf025a3b6e220efeee5fb9ecd97ad51c6adcccb96ca62426cc096e38eb9aa0 +
        16 * _d86114b5bc1b6abf8638dd305669a55d8b394e5709b8e33e585d73c184d18943;

    return Math.round(total / _838e506beb7a1376c2242cd5738a6016661bdfccb78c105f3ce081c89735bc9d);
}

// name: Total Texture Accesses
// description: Total Number of texture accesses read, sample, gather
// type: Count
function TextureAccesses() {
    return _ae304fc8bce5708ffef30935687e442d6bea78f814055a5fe6e3380013d7e507 * 64;
}

// name: Total Texture Quads
// description: Total Number of texture quads
// type: Count
function TextureQuads() {
    return _0927651557827fd5468721c2ee04ff7924ebb553f9e0acc6b504a791aefdf935 * 64;
}

// name: Total Texture Quads Gathered
// description: Total Number of texture quads gathered
// type: Count
function TextureQuadsGathered() {
    return _f46268d72ed52af703d1b490e193d71605d5c756930dfe9385a5433c9b4f264f * 4;
}

// name: Total Texture Samples
// description: Total Number of texture samples
// type: Count
function TextureSamples() {
    return Math.max((_ae304fc8bce5708ffef30935687e442d6bea78f814055a5fe6e3380013d7e507 * 64) - (_f46268d72ed52af703d1b490e193d71605d5c756930dfe9385a5433c9b4f264f * 4), 0);
}

// name: Anisotropic Samples
// description: Number of texture samples with anisotropic filtering
// type: Count
function AnisotropicSamples() {
    return _838e506beb7a1376c2242cd5738a6016661bdfccb78c105f3ce081c89735bc9d * 4;
}

// name: Anisotropic Samples %
// description: % of texture samples with anisotropic filtering
// type: Percentage
function AnisotropicSamplesPercent() {
    return (_838e506beb7a1376c2242cd5738a6016661bdfccb78c105f3ce081c89735bc9d * 100) / TextureQuads();
}

// name: Mipmap Linear Samples
// description: Number of texture samples with linear mipmap filter
// type: Count
function MipmapLinearSamples() {
    return _b7afe579643b48d1495eb528fa5a78db4c0a065f75636f39f24f9cf4578912cf * 4;
}

// name: Mipmap Linear Samples %
// description: % of texture samples with linear mipmap filter
// type: Percentage
function MipmapLinearSamplesPercent() {
    return (_b7afe579643b48d1495eb528fa5a78db4c0a065f75636f39f24f9cf4578912cf * 100) / TextureQuads();
}

// name: Mipmap Nearest Samples
// description: Number of texture samples with nearest mipmap filter
// type: Count
function MipmapNearestSamples() {
    return _443fdcc2095b4dca2f7e327fb6af5914523d670164b66d05316044de82474149 * 4;
}

// name: Mipmap Nearest Samples %
// description: % of texture samples with nearest mipmap filter
// type: Percentage
function MipmapNearestSamplesPercent() {
    return (_443fdcc2095b4dca2f7e327fb6af5914523d670164b66d05316044de82474149 * 100) / TextureQuads();
}

// name: Compressed Texture Samples
// description: Number of compressed texture samples
// type: Count
function CompressedSamples() {
    var CompressedSamples = _c9c95eb1a34eb7174e53a1b1edaf53792e68f9976bc8eb07fce8ad493bddc08e +
        _3de788cd53ebf174aa407ea16ef4db42a9c5b26ec73c4d2f90713dd56d65f333 +
        _fa01d5329f611805a99f4699e796d485f8f993df07816be0c8b15ac5e39951ea +
        _0b4c966855c4b581f07ec85a1491cb234d31a838aaf82adc9427d3b2497bd31c +
        _3bdd2971a0eab63c90d85f332aaf54f1f94663a4057f3c5d7619e2442d091a31 +
        _4e088158f4d8adbbe88420686b1cb8700f71b4a42277c8b25c3f00bb97008361 +
        _0427b329a9bf6f3b297e589bdebcd2e8a222101e677f95061e2fbe6fbe4ffa6f +
        _4abe7d6426efbcb52bcc749d398c408464e07bccc54a687a42b794009dee6158 +
        _71b154ef77c3d0492cf30c6594c523c8abe3285ee44c7f73c15ab86fabc4f05e +
        _e2eebf0eaa57027e8dfa6003d4f8f90fb00c3666b62e391d060b8730c80b020f +
        _46ed86682cc445fce72ee444d0a285905c9acb73971662dc88cf1fbc7f637928 +
        _ccbd9b2a02319dfae2b510714bf280d5869ae5b980a89f854023778e59e8fb8b +
        _0170b0014687cc7dc054a9619094bc011a05d098930b07f0b7dab0bcabae9406 +
        _282cfcc4b531f88df1917e61edd71b551c4de0f3cc74785a95cdeaf421efefe2;

    return CompressedSamples * 4;
}

// name: Compressed Samples %
// description: Percentage of samples to compressed textures
// type: Percentage
function CompressedSamplesPercent() {
    return Math.min((CompressedSamples() * 100.0) / Math.max(TextureQuads() * 4, 1.0), 100.0);
}

// name: Lossless Compressed Texture Samples
// description: Number of lossless compressed texture samples
// type: Count
function LosslessCompressedSamples() {
    return _7cdc2c85e61923202c5936567bb447b8929b55e3fadd72277ff0796a99a7bdb4 * 4;
}

// name: Lossless Compressed Samples %
// description: Percentage of samples to compressed textures
// type: Percentage
function LosslessCompressedSamplesPercent() {
    return Math.min((LosslessCompressedSamples() * 100.0) / Math.max(TextureQuads() * 4, 1.0), 100.0);
}

// name: Uncompressed Texture Samples
// description: Number of uncompressed texture samples
// type: Count
function UncompressedSamples() {
    return Math.max(TextureQuads() * 4 - (CompressedSamples() + LosslessCompressedSamples()), 0);
}

// name: Uncompressed Samples %
// description: Percentage of samples to compressed textures
// type: Percentage
function UnCompressedSamplesPercent() {
    return Math.min(100.0 * UncompressedSamples() / Math.max(TextureQuads() * 4, 1.0), 100.0);
}

// name: Pixels Written to Memory Unbiased
// description: Number of pixels unbiased written to memory
// type: Count
function PixelsUnbiasedWrittenToMemory() {
    return _f406f88bdd312ec0455d0943c388de77e53b86cf0109624b028c3aa596ec3bf4 * 4;
}

// name: Texture Pixels Written to Memory by Pixel Write Instructions
// description: Number of texture pixels written to memory
// type: Count
function TexturePixelsWrittenToMemory() {
    return _03e06857325a0de8f5a4a0e55c75600fdbc3320b641d3263a95784fa16e2aaa1 * 4;
}

// name: Pixels Written to Memory
// description: Number of pixels written to memory
// type: Count
function PixelsWrittenToMemory() {
    return Math.max(PixelsUnbiasedWrittenToMemory(), TexturePixelsWrittenToMemory());
}

// name: Attachment Pixels Written to Memory
// description: Number of pixels written to memory
// type: Count
function AttachmentPixelsWrittenToMemory() {
    return Math.max(PixelsUnbiasedWrittenToMemory() - TexturePixelsWrittenToMemory(), 0.0);
}

// name: Compressed Pixels Written to Memory
// description: Number of compressed pixels written to memory
// type: Count
function CompressedPixelsWrittenToMemory() {
    return _d2a9ad5555cf691ed8c64858ebd4a530a83d601bb356314c24c2f03df645597c * 4;
}

// name: Percentage of Texture Pixels Written to Memory by Pixel Write Instructions
// description: Number of texture pixels written to memory
// type: Percentage
function TexturePixelsWrittenToMemoryPercent() {
    return 100.0 * TexturePixelsWrittenToMemory() / Math.max(PixelsWrittenToMemory(), 1.0);
}

// name: Percentage of Attachment Pixels Written to Memory
// description: Percentage of number of attachment pixels written to memory
// type: Percentage
function AttachmentPixelsWrittenToMemoryPercent() {
    return 100.0 * AttachmentPixelsWrittenToMemory() / Math.max(PixelsWrittenToMemory(), 1.0);
}

// name: Percentage of Compressed Pixels Written to Memory
// description: Percentage of number of compressed pixels written to memory
// type: Percentage
function CompressedPixelsWrittenToMemoryPercent() {
    return 100.0 * CompressedPixelsWrittenToMemory() / Math.max(PixelsWrittenToMemory(), 1.0);
}

// name: Number of 2xMSAA Resolved Pixels
// description: Number of 2xMSAA resolved pixels
// type: Count
function MSAA2XResolvedPixels() {
    return _66eafb3ddb63687a1eef3817f25c70385aeb51f41d76b5cbdc5aa69a556bb76c * 4;
}

// name: Number of 4xMSAA Resolved Pixels
// description: Number of 4xMSAA resolved pixels
// type: Count
function MSAA4XResolvedPixels() {
    return _788f9865b6b4897849bedfd577403fe30b882c1c6c2afcdbf2a9f8a0d41e741b * 4;
}

// name: Number of 2xMSAA Resolved Pixels
// description: Number of 2xMSAA resolved pixels
// type: Percentage
function MSAA2XResolvedPixelsPercent() {
    return 100.0 * (MSAA2XResolvedPixels() / Math.max(PixelsWrittenToMemory(), 1.0));
}

// name: Number of 4xMSAA Resolved Pixels
// description: Number of 4xMSAA resolved pixels
// type: Percentage
function MSAA4XResolvedPixelsPercent() {
    return 100.0 * (MSAA4XResolvedPixels() / Math.max(PixelsWrittenToMemory(), 1.0));
}


// name: Number of Total Resolved Pixels
// description: Number of total resolved pixels
// type: Count
function TotalResolvedPixels() {
    return (_92e4033c73762edd1ce117ae25bceecf0ae126712bf861ca430c8049f845b9ff + _37b62c762d1c23168d0c25f1bc6033c6ee17922f5e31eab8d0cd946eb40ff5f3 + _984b0993354750161fe0018879ef125f6e3d98a5cbd800796dba5fb611df1651 + _6bb7d08e271a527bc1e586380563ec0de8de7e58c81e7b417ac1ecb39790c288) * 4.0;
}

// name: Average Unique Colors Per Resolved Pixels
// description: Average unique colors per resolved pixels
// type: Rate
function AverageUniqueColorsPerResolvedPixels() {
    return 4.0 * (_92e4033c73762edd1ce117ae25bceecf0ae126712bf861ca430c8049f845b9ff + 2.0 * _37b62c762d1c23168d0c25f1bc6033c6ee17922f5e31eab8d0cd946eb40ff5f3 + 3.0 * _984b0993354750161fe0018879ef125f6e3d98a5cbd800796dba5fb611df1651 + 4.0 * _6bb7d08e271a527bc1e586380563ec0de8de7e58c81e7b417ac1ecb39790c288) / Math.max(TotalResolvedPixels(), 1.0);
}

// name: Texture Sample Limiter
// description: Measures the time during which texture samples are attempted to execute as a percentage of peak texture sample performance.
// type: Percentage
function TPULimiter() {
    return _7646a8523871192073a29fb3af219f4dbddae3339e969e0da8ef8d84a3d46ec5_norm / (2.0 * num_cores);
}

// name: Vertex Texture Sample Limiter
// description: Vertex texture sample limiter
// type: Percentage
function VertexTPULimiter() {
    return _7646a8523871192073a29fb3af219f4dbddae3339e969e0da8ef8d84a3d46ec5_norm_vtx / (2.0 * num_cores);
}

// name: Fragment Texture Sample Limiter
// description: Fragment texture sample limiter
// type: Percentage
function FragmentTPULimiter() {
    return _7646a8523871192073a29fb3af219f4dbddae3339e969e0da8ef8d84a3d46ec5_norm_frg / (2.0 * num_cores);
}

// name: ALU Limiter
// description: Measures the time during which ALU work is attempted to execute as a percentage of peak ALU performance.
// type: Percentage
function ALULimiter() {
    return (_c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2_norm + _d201fed97c60848e3714502b203a0ad4e2820937c140dbf6a9db1cb31be194dd_norm) / num_cores;
}

// name: Vertex ALU Limiter
// description: Vertex ALU Limiter
// type: Percentage
function VertexALULimiter() {
    return (_c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2_norm_vtx + _d201fed97c60848e3714502b203a0ad4e2820937c140dbf6a9db1cb31be194dd_norm_vtx) / num_cores;
}

// name: Fragment ALU Limiter
// description: Fragment ALU Limiter
// type: Percentage
function FragmentALULimiter() {
    return (_c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2_norm_frg + _d201fed97c60848e3714502b203a0ad4e2820937c140dbf6a9db1cb31be194dd_norm_frg) / num_cores;
}

// name: Texture Write Limiter
// description: Texture write limiter
// type: Percentage
function PBELimiter() {
    return (_bb9dbea90df77e54beebae872b35923d727fd2a59d6905410b32092d6d561402_norm + _63b42fb9d33e39b5f913060438c759d841275b394631cb7a8145853e9a04ef67_norm) / num_cores;
}

// name: VS Texture Write Limiter
// description: VS Texture write limiter
// type: Percentage
function VertexPBELimiter() {
    return (_bb9dbea90df77e54beebae872b35923d727fd2a59d6905410b32092d6d561402_norm_vtx + _63b42fb9d33e39b5f913060438c759d841275b394631cb7a8145853e9a04ef67_norm_vtx) / num_cores;
}

// name: FS Texture Write Limiter
// description: FS Texture write limiter
// type: Percentage
function FragmentPBELimiter() {
    return (_bb9dbea90df77e54beebae872b35923d727fd2a59d6905410b32092d6d561402_norm_frg + _63b42fb9d33e39b5f913060438c759d841275b394631cb7a8145853e9a04ef67_norm_frg) / num_cores;
}

// name: Sample Limiter
// description: % Sample Limiter
// type: Percentage
function SampleLimiter() {
    return (_450c6190714cff4c691e85516367dccd4a988a331215ec899dc89670b4d6fbfa_norm + _bdd31d464f4dbd8a42028ce4a2b5885958d98a8cfbf4f34e09d601dd6425efa9_norm) * 0.5 / num_cores;
}

// name: VS Sample Limiter
// description: % VS Sample Limiter
// type: Percentage
function VertexSampleLimiter() {
    return (_450c6190714cff4c691e85516367dccd4a988a331215ec899dc89670b4d6fbfa_norm_vtx + _bdd31d464f4dbd8a42028ce4a2b5885958d98a8cfbf4f34e09d601dd6425efa9_norm_vtx) * 0.5 / num_cores;
}

// name: FS Sample Limiter
// description: % FS Sample Limiter
// type: Percentage
function FragmentSampleLimiter() {
    return (_450c6190714cff4c691e85516367dccd4a988a331215ec899dc89670b4d6fbfa_norm_frg + _bdd31d464f4dbd8a42028ce4a2b5885958d98a8cfbf4f34e09d601dd6425efa9_norm_frg) * 0.5 / num_cores;
}

// name: Threadgroup/Imageblock Load Limiter
// description: Measures the time during which threadgroup and imageblock threadgroup loads are attempted to execute as a percentage of peak threadgroup and imageblock threadgroup performance.
// type: Percentage
function LocalLoadLimiter() {
    return _7297c7ee63bc3f774b2e5f2e665cd87efcbf40dd3e6b66a9c08f8ebfdae4019e_norm / (4.0 * num_cores);
}

// name: VS Threadgroup/Imageblock Load Limiter
// description: VS Threadgroup/Imageblock load limiter
// type: Percentage
function VertexLocalLoadLimiter() {
    return _7297c7ee63bc3f774b2e5f2e665cd87efcbf40dd3e6b66a9c08f8ebfdae4019e_norm_vtx / (4.0 * num_cores);
}

// name: FS Threadgroup/Imageblock Load Limiter
// description: FS Threadgroup/Imageblock load limiter
// type: Percentage
function FragmentLocalLoadLimiter() {
    return _7297c7ee63bc3f774b2e5f2e665cd87efcbf40dd3e6b66a9c08f8ebfdae4019e_norm_frg / (4.0 * num_cores);
}

// name: Threadgroup/Imageblock Store Limiter
// description: Measures the time during which threadgroup and imageblock threadgroup stores are attempted to execute as a percentage of peak threadgroup and imageblock threadgroup performance.
// type: Percentage
function LocalStoreLimiter() {
    return _192193e6c7ce23b86614fecbd983be5c3d4ea08d47c42ee19db85a736c0cbf7e_norm / (4.0 * num_cores);
}

// name: VS Threadgroup/Imageblock Store Limiter
// description: VS Threadgroup/Imageblock store limiter
// type: Percentage
function VertexLocalStoreLimiter() {
    return _192193e6c7ce23b86614fecbd983be5c3d4ea08d47c42ee19db85a736c0cbf7e_norm_vtx / (4.0 * num_cores);
}

// name: FS Threadgroup/Imageblock Store Limiter
// description: FS Threadgroup/Imageblock store limiter
// type: Percentage
function FragmentLocalStoreLimiter() {
    return _192193e6c7ce23b86614fecbd983be5c3d4ea08d47c42ee19db85a736c0cbf7e_norm_frg / (4.0 * num_cores);
}

// name: Texture Cache Read Miss Rate
// description: Percentage of time L1 Texture Cache read access is a Miss
// type: Percentage
function TextureCacheMissRate() {
    return _19109618d2fc2db66c23fe425a0a19ec06c81f05bb676c40aa572b76891428e6 * 100 / (4.0 * _a8aac8549e9e4a65ca6d3143f42067a6b99241a9a056d0bb512624ee4a91ebc6 + 3.0 * _c0d09f7c090cf4aba7f28554d5fbc55c24426ef3c548a77fa8def417b1823500 + 2.0 * _5a879b789f129c90cada6c1f3173468a47dbc0b43eb8f7e0f8c9602136a0ae0d + _c5abc56251535ca5b6258367a41d21e518b437e511763fe0d6f0e84ec115ff41);
}

// name: Texture Cache Write Miss Rate in Vertex Shader
// description: Percentage of time L1 Texture Cache write access is a Miss for Vertex Shader
// type: Percentage
function VSTextureCacheWriteMissRate() {
    return _f430991e42f778aeda210861eca9b8cef241898007339644eff469d83e5a6c9d_vtx * 100.0 / (_f430991e42f778aeda210861eca9b8cef241898007339644eff469d83e5a6c9d_vtx + _3459b3e3f2f8a441719d05aae2161786eded99c72d7215bb6797f836d46a3426_vtx);
}

// name: Texture Cache Write Miss Rate in Fragment Shader
// description: Percentage of time L1 Texture Cache write access is a Miss for Fragment Shader
// type: Percentage
function FSTextureCacheWriteMissRate() {
    return _f430991e42f778aeda210861eca9b8cef241898007339644eff469d83e5a6c9d_frg * 100.0 / (_f430991e42f778aeda210861eca9b8cef241898007339644eff469d83e5a6c9d_frg + _3459b3e3f2f8a441719d05aae2161786eded99c72d7215bb6797f836d46a3426_frg);
}

// name: Texture Cache Write Miss Rate
// description: Percentage of time L1 Texture Cache write access is a Miss
// type: Percentage
function TextureCacheWriteMissRate() {
    return _f430991e42f778aeda210861eca9b8cef241898007339644eff469d83e5a6c9d * 100.0 / (_f430991e42f778aeda210861eca9b8cef241898007339644eff469d83e5a6c9d + _3459b3e3f2f8a441719d05aae2161786eded99c72d7215bb6797f836d46a3426);
}

// name: VS Bytes Read From Main Memory
// description: Total bytes read from main memory in Vertex Shader
// type: Value
function VSBytesReadFromMainMemory() {
    return 64.0 * (_e7982344eb9c10ce1e1e9e179c01bb8a55934656fd5d499f956d6e35e42f1f10_vtx + _aac2d2ece8ff1acbf2ab0f821c8f1e4e2dbb2ca4c3a6918e2dc458dfab8ee05c_vtx);
}

// name: FS Bytes Read From Main Memory
// description: Total bytes read from main memory in Fragment Shader
// type: Value
function FSBytesReadFromMainMemory() {
    return 64.0 * (_e7982344eb9c10ce1e1e9e179c01bb8a55934656fd5d499f956d6e35e42f1f10_frg + _aac2d2ece8ff1acbf2ab0f821c8f1e4e2dbb2ca4c3a6918e2dc458dfab8ee05c_frg);
}

// name: Bytes Read From Main Memory
// description: Total bytes read from main memory
// type: Value
function BytesReadFromMainMemory() {
    return 64.0 * (_e7982344eb9c10ce1e1e9e179c01bb8a55934656fd5d499f956d6e35e42f1f10 + _aac2d2ece8ff1acbf2ab0f821c8f1e4e2dbb2ca4c3a6918e2dc458dfab8ee05c);
}

// name: Bytes Written To Main Memory in Vertex Shader
// description: Total bytes written to main memory in vertex shader
// type: Value
function VSBytesWrittenToMainMemory() {
    return 64.0 * _190175e7010a5c90cc957e3f3eed64c3910111ef228808fbb2462cd269524ef5_vtx;
}

// name: Bytes Written To Main Memory in Fragment Shader
// description: Total bytes written to main memory in fragment shader
// type: Value
function FSBytesWrittenToMainMemory() {
    return 64.0 * _190175e7010a5c90cc957e3f3eed64c3910111ef228808fbb2462cd269524ef5_frg;
}

// name: Bytes Written To Main Memory
// description: Total bytes written to main memory
// type: Value
function BytesWrittenToMainMemory() {
    return 64.0 * _190175e7010a5c90cc957e3f3eed64c3910111ef228808fbb2462cd269524ef5;
}

// name: VS Global Atomic Bytes Read
// description: Total global atomic bytes read in Vertex Shader
// type: Value
function VSTotalGlobalAABytesRead() {
    return 64.0 * Math.max(_3c6dba64fd85b35b8b8339f1d322943087d45cbb9b6689c587fd76259587a9d8_vtx - _ac73411a986e90adcd0a1181ace1f2684e4a900be931343385b93f58de650db4_vtx, 0.0);
}

// name: FS Global Atomic Bytes Read
// description: Total global atomic bytes read in fragment shader
// type: Value
function FSTotalGlobalAABytesRead() {
    return 64.0 * Math.max(_3c6dba64fd85b35b8b8339f1d322943087d45cbb9b6689c587fd76259587a9d8_frg - _ac73411a986e90adcd0a1181ace1f2684e4a900be931343385b93f58de650db4_frg, 0.0);
}

// name: Global Atomic Bytes Read
// description: Total global atomic bytes read
// type: Value
function TotalGlobalAABytesRead() {
    return 64.0 * Math.max(_3c6dba64fd85b35b8b8339f1d322943087d45cbb9b6689c587fd76259587a9d8 - _ac73411a986e90adcd0a1181ace1f2684e4a900be931343385b93f58de650db4, 0.0);
}

// name: VS Global Atomic Bytes Written
// description: Total global atomic bytes written in Vertex Shader
// type: Value
function VSTotalGlobalAABytesWritten() {
    return 64.0 * (_3c6dba64fd85b35b8b8339f1d322943087d45cbb9b6689c587fd76259587a9d8_vtx);
}

// name: FS Global Atomic Bytes Written
// description: Total global atomic bytes written in fragment shader
// type: Value
function FSTotalGlobalAABytesWritten() {
    return 64.0 * (_3c6dba64fd85b35b8b8339f1d322943087d45cbb9b6689c587fd76259587a9d8_frg);
}

// name: Global Atomic Bytes Written
// description: Total global atomic bytes written
// type: Value
function TotalGlobalAABytesWritten() {
    return 64.0 * (_3c6dba64fd85b35b8b8339f1d322943087d45cbb9b6689c587fd76259587a9d8);
}

// name: VS Global Atomic Instructions With Return Data
// description: Total global atomic instructions with return data in Vertex Shader
// type: Value
function VSTotalGlobalAAInstructions() {
    return 16.0 * _5573f0ed078d893d618327787a93dccd1ac9197b27429c1a36a320ac1540db2a_vtx;
}

// name: VS Global Atomic Instructions With No Return Data
// description: Total global atomic instructions with no return data in Vertex Shader
// type: Value
function VSTotalGlobalAAInstructionsNoReturn() {
    return 16.0 * _638ed0f36a4187b9ecad2646b42a73d9269d37f3458bf8140de61a5a5448252c_vtx;
}

// name: FS Global Atomic Instructions With Return Data
// description: Total global atomic instructions with return data in Fragment Shader
// type: Value
function FSTotalGlobalAAInstructions() {
    return 16.0 * _5573f0ed078d893d618327787a93dccd1ac9197b27429c1a36a320ac1540db2a_frg;
}

// name: FS Global Atomic Instructions With No Return Data
// description: Total global atomic instructions with no return data in Fragment Shader
// type: Value
function FSTotalGlobalAAInstructionsNoReturn() {
    return 16.0 * _638ed0f36a4187b9ecad2646b42a73d9269d37f3458bf8140de61a5a5448252c_frg;
}

// name: FS Global Atomic Instructions With Return Data
// description: Total global atomic instructions with return data in shaders
// type: Value
function TotalGlobalAAInstructions() {
    return 16.0 * _5573f0ed078d893d618327787a93dccd1ac9197b27429c1a36a320ac1540db2a;
}

// name: FS Global Atomic Instructions With No Return Data
// description: Total global atomic instructions with no return data in shaders
// type: Value
function TotalGlobalAAInstructionsNoReturn() {
    return 16.0 * _638ed0f36a4187b9ecad2646b42a73d9269d37f3458bf8140de61a5a5448252c;
}


// name: VS L2 Bytes Read
// description: Total L2 bytes read in Vertex Shader
// type: Value
function VSTotalL2BytesRead() {
    return 64.0 * (_ef52925e500884ba6b276e576ae78b97fd8448dfadeba596c2202b5202e246c3_vtx + _43fe12d20dfe3a9ea7b303773d624405e026e20b2c550822f2587997d2557f13_vtx + _0d5290b07753d1bbf223d0700438322c356bc6d3f028bf47df09e81f21da75c6_vtx + _3329a7bf90f5b81c24f86beffadfc66daefb2b2f45b08cdb822f931dac7370d6_vtx) + VSTotalGlobalAABytesRead();
}

// name: FS L2 Bytes Read
// description: Total L2 bytes read in fragment shader
// type: Value
function FSTotalL2BytesRead() {
    return 64.0 * (_ef52925e500884ba6b276e576ae78b97fd8448dfadeba596c2202b5202e246c3_frg + _43fe12d20dfe3a9ea7b303773d624405e026e20b2c550822f2587997d2557f13_frg + _0d5290b07753d1bbf223d0700438322c356bc6d3f028bf47df09e81f21da75c6_frg + _3329a7bf90f5b81c24f86beffadfc66daefb2b2f45b08cdb822f931dac7370d6_frg) + FSTotalGlobalAABytesRead();
}

// name: L2 Bytes Read
// description: Total L2 bytes read
// type: Value
function TotalL2BytesRead() {
    return 64.0 * (_ef52925e500884ba6b276e576ae78b97fd8448dfadeba596c2202b5202e246c3 + _43fe12d20dfe3a9ea7b303773d624405e026e20b2c550822f2587997d2557f13 + _0d5290b07753d1bbf223d0700438322c356bc6d3f028bf47df09e81f21da75c6 + _3329a7bf90f5b81c24f86beffadfc66daefb2b2f45b08cdb822f931dac7370d6) + TotalGlobalAABytesRead();
}

// name: VS L2 bytes written
// description: Total L2 Bytes Written in vertex shader
// type: Value
function VSTotalL2BytesWritten() {
    return 64.0 * (_d7a23701e11432625d46f02ff35668e60e55a7706704976facfe5fbeea3b1936_vtx + _88723e1253a5c3264f69b1fbf3a6b7f3ab67bbd9fe97afeedb649146b3b8b043_vtx + _56a63abf333e0f9f06f1a00635d4125c3910b3c00286e4fb3652687402916c8a_vtx) + VSTotalGlobalAABytesWritten()
}

// name: FS L2 Bytes Written
// description: Total L2 bytes written in fragment shader
// type: Value
function FSTotalL2BytesWritten() {
    return 64.0 * (_d7a23701e11432625d46f02ff35668e60e55a7706704976facfe5fbeea3b1936_frg + _88723e1253a5c3264f69b1fbf3a6b7f3ab67bbd9fe97afeedb649146b3b8b043_frg + _56a63abf333e0f9f06f1a00635d4125c3910b3c00286e4fb3652687402916c8a_frg) + FSTotalGlobalAABytesWritten()
}

// name: L2 Bytes Written
// description: Total L2 bytes written
// type: Value
function TotalL2BytesWritten() {
    return 64.0 * (_d7a23701e11432625d46f02ff35668e60e55a7706704976facfe5fbeea3b1936 + _88723e1253a5c3264f69b1fbf3a6b7f3ab67bbd9fe97afeedb649146b3b8b043 + _56a63abf333e0f9f06f1a00635d4125c3910b3c00286e4fb3652687402916c8a) + TotalGlobalAABytesWritten()
}

// name: VS Total Texture L1 Bytes Read
// description: Total bytes read from texture L1 cache in vertex shader
// type: Value
function VSTotalBytesReadFromTextureL1Cache() {
    return 16.0 * (4.0 * _a8aac8549e9e4a65ca6d3143f42067a6b99241a9a056d0bb512624ee4a91ebc6_vtx + 3.0 * _c0d09f7c090cf4aba7f28554d5fbc55c24426ef3c548a77fa8def417b1823500_vtx + 2.0 * _5a879b789f129c90cada6c1f3173468a47dbc0b43eb8f7e0f8c9602136a0ae0d_vtx + _c5abc56251535ca5b6258367a41d21e518b437e511763fe0d6f0e84ec115ff41_vtx);
}

// name: FS Total Texture L1 Bytes Read
// description: Total bytes read from texture L1 cache in fragment shader
// type: Value
function FSTotalBytesReadFromTextureL1Cache() {
    return 16.0 * (4.0 * _a8aac8549e9e4a65ca6d3143f42067a6b99241a9a056d0bb512624ee4a91ebc6_frg + 3.0 * _c0d09f7c090cf4aba7f28554d5fbc55c24426ef3c548a77fa8def417b1823500_frg + 2.0 * _5a879b789f129c90cada6c1f3173468a47dbc0b43eb8f7e0f8c9602136a0ae0d_frg + _c5abc56251535ca5b6258367a41d21e518b437e511763fe0d6f0e84ec115ff41_frg);
}

// name: Texture L1 Bytes Read
// description: Total bytes read from texture L1 cache
// type: Value
function TotalBytesReadFromTextureL1Cache() {
    return 16.0 * (4.0 * _a8aac8549e9e4a65ca6d3143f42067a6b99241a9a056d0bb512624ee4a91ebc6 + 3.0 * _c0d09f7c090cf4aba7f28554d5fbc55c24426ef3c548a77fa8def417b1823500 + 2.0 * _5a879b789f129c90cada6c1f3173468a47dbc0b43eb8f7e0f8c9602136a0ae0d + _c5abc56251535ca5b6258367a41d21e518b437e511763fe0d6f0e84ec115ff41);
}

// name: VS Buffer L1 Bytes Read
// description: Total bytes read from buffer L1 cache in vertex shader
// type: Value
function VSTotalBytesReadFromBufferL1Cache() {
    return _f3b0ac2ff165c0670b2240e2ab5a6536283a3731be38544cccd5d6393815b687_vtx * 16.0;
}

// name: FS Buffer L1 Bytes Read
// description: Total bytes read from buffer L1 cache in fragment shader
// type: Value
function FSTotalBytesReadFromBufferL1Cache() {
    return _f3b0ac2ff165c0670b2240e2ab5a6536283a3731be38544cccd5d6393815b687_frg * 16.0;
}

// name: Buffer L1 Bytes Read
// description: Total bytes read from buffer L1 cache
// type: Value
function TotalBytesReadFromBufferL1Cache() {
    return _f3b0ac2ff165c0670b2240e2ab5a6536283a3731be38544cccd5d6393815b687 * 16.0;
}

// name: VS Buffer L1 Bytes Written
// description: Total bytes written to buffer L1 cache in vertex shader
// type: Value
function VSTotalBytesWrittenBufferL1Cache() {
    return _dcc19066dda99b0411d8c63a3e83f6f7f1d98ab35e1abb6ea67d0cc2c48fb902_vtx * 16.0;
}

// name: FS Buffer L1 Bytes Written
// description: Total bytes written to buffer L1 cache in fragment shader
// type: Value
function FSTotalBytesWrittenBufferL1Cache() {
    return _dcc19066dda99b0411d8c63a3e83f6f7f1d98ab35e1abb6ea67d0cc2c48fb902_frg * 16.0;
}

// name: Buffer L1 Bytes Written
// description: Total bytes written to buffer L1 cache
// type: Value
function TotalBytesWrittenBufferL1Cache() {
    return _dcc19066dda99b0411d8c63a3e83f6f7f1d98ab35e1abb6ea67d0cc2c48fb902 * 16.0;
}

// name: Predicated Texture Thread Writes
// description: Percentage thread predicated out due to divergent control flow or small primitives covering part of quad in the render target on texture writes
// type: Percentage
function PredicatedTextureWritePercentage() {
    if (_f406f88bdd312ec0455d0943c388de77e53b86cf0109624b028c3aa596ec3bf4 + _9da983fb76d81017bb17c1307769e9cdaa3547cc33eadcf7f389043343c66b31 > 0) {
        return Math.max(100.0 * (1.0 - _f406f88bdd312ec0455d0943c388de77e53b86cf0109624b028c3aa596ec3bf4 / _9da983fb76d81017bb17c1307769e9cdaa3547cc33eadcf7f389043343c66b31), 0.0);
    }
    return 0.0;
}

// name: Predicated Texture Thread Reads
// description: Percentage threads predicated out due to divergent control flow or small primitives covering part of quad in the render target on texture reads
// type: Percentage
function PredicatedTextureReadPercentage() {
    if (TextureAccesses() > 0) {
        return Math.max(100.0 * (1.0 - TextureAccesses() / Math.max(4.0 * TextureQuads(), 1.0)), 0.0);
    }
    return 0.0;
}

// name: Samples Shaded Per Tile
// description: Samples shaded per tile
// type: Rate
function SamplesShadedPerTile() {
    return 64.0 * _416b2a4855c3ad10e45eaab8493e7651ad66f8e3d44ad880fa8111c87ccd090a / _eda5bce70befa39e7c6029505c0269211092c220048a502fd8fa2fe30895465b;
}

// name: Samples Shaded Per Quad
// description: Samples shaded per quad
// type: Rate
function SamplesShadedPerQuad() {
    return 64.0 * _416b2a4855c3ad10e45eaab8493e7651ad66f8e3d44ad880fa8111c87ccd090a / Math.max(4.0 * _ca0d54323c1777d994357aaacdb7beac572bea11cd16afed4c756f3dc9496a18, 1.0);
}

// name: VS Predicated Out ALU Percentage
// description: Percentage issued ALU operations predicated out due to divergent control flow in the verex shader
// type: Percentage
function VSPredicatedALUPercentage() {
    var instructionsIssued = 128.0 * (_0af59bb3dd0a90f2664cd5e5601b3c56bf91e40478def55647411007dc5394d3_vtx + _a6e6cc683eebf697b2a31bd7d4f877afee2419f6882f55b2f4ea296c9a368b99_vtx + _4ffbecab1c5697bfb927de016f6ddd4b010ddb0588049be5243c148e62d21409_vtx + _04ec68f75ab42cefa364623ffb059b101b9d6d35ed0e59abbbc94170b4ec6cbe_vtx);
    var instructionsExecuted = 16.0 * (_82b2f93079459b00fb869444cfcf44604cc1a91d28078cd6bfd7bb6ea6ba423d_vtx + _8e70441b8b0d9ded3ed900ec761f9f5960b106c5a304b44d62781621d5d1861a_vtx + _23c51175314006fa4b6798dcb173a814349e2e5947244cfdba868be736d2bc03_vtx + _827783963eafa9275a53fc2b3ef13214ab90939fcc81572c4260e2eac9bd2acb_vtx);

    if (instructionsIssued + instructionsExecuted > 0) {
        return Math.max(100.0 * (1.0 - instructionsExecuted / instructionsIssued), 0.0);
    }
    return 0.0;
}

// name: FS Predicated Out ALU Percentage
// description: Percentage issued ALU operations predicated out due to divergent control flow in the fragment shader
// type: Percentage
function FSPredicatedALUPercentage() {
    var instructionsIssued = 128.0 * (_0af59bb3dd0a90f2664cd5e5601b3c56bf91e40478def55647411007dc5394d3_frg + _a6e6cc683eebf697b2a31bd7d4f877afee2419f6882f55b2f4ea296c9a368b99_frg + _4ffbecab1c5697bfb927de016f6ddd4b010ddb0588049be5243c148e62d21409_frg + _04ec68f75ab42cefa364623ffb059b101b9d6d35ed0e59abbbc94170b4ec6cbe_frg);
    var instructionsExecuted = 16.0 * (_82b2f93079459b00fb869444cfcf44604cc1a91d28078cd6bfd7bb6ea6ba423d_frg + _8e70441b8b0d9ded3ed900ec761f9f5960b106c5a304b44d62781621d5d1861a_frg + _23c51175314006fa4b6798dcb173a814349e2e5947244cfdba868be736d2bc03_frg + _827783963eafa9275a53fc2b3ef13214ab90939fcc81572c4260e2eac9bd2acb_frg);

    if (instructionsIssued + instructionsExecuted > 0) {
        return Math.max(100.0 * (1.0 - instructionsExecuted / instructionsIssued), 0.0);
    }
    return 0.0;
}

// name: Kernel Predicated Out ALU Percentage
// description: Percentage issued ALU operations predicated out due to divergent control flow in the compute shader
// type: Percentage
function CSPredicatedALUPercentage() {
    var instructionsIssued = 128.0 * (_0af59bb3dd0a90f2664cd5e5601b3c56bf91e40478def55647411007dc5394d3_cmp + _a6e6cc683eebf697b2a31bd7d4f877afee2419f6882f55b2f4ea296c9a368b99_cmp + _4ffbecab1c5697bfb927de016f6ddd4b010ddb0588049be5243c148e62d21409_cmp + _04ec68f75ab42cefa364623ffb059b101b9d6d35ed0e59abbbc94170b4ec6cbe_cmp);
    var instructionsExecuted = 16.0 * (_82b2f93079459b00fb869444cfcf44604cc1a91d28078cd6bfd7bb6ea6ba423d_cmp + _8e70441b8b0d9ded3ed900ec761f9f5960b106c5a304b44d62781621d5d1861a_cmp + _23c51175314006fa4b6798dcb173a814349e2e5947244cfdba868be736d2bc03_cmp + _827783963eafa9275a53fc2b3ef13214ab90939fcc81572c4260e2eac9bd2acb_cmp);

    if (instructionsIssued + instructionsExecuted > 0) {
        return Math.max(100.0 * (1.0 - instructionsExecuted / instructionsIssued), 0.0);
    }
    return 0.0;
}

// name: Thread Group Bytes Read
// description: Total bytes read from thread group memory
// type: Value
function TotalBytesReadFromThreadGroupMemory() {
    return 16.0 * _4f6aebbe216cd96fa4684995ac68478cbdb59c6706480ecbbb9f101d892bb540;
}

// name: Thread Group Bytes Written
// description: Total bytes written to thread group memory
// type: Value
function TotalBytesWrittenThreadGroupMemory() {
    return 16.0 * _968353d331d798ff8c65ce5f1d5294c1f4bcd54f8004fe37c0ec8e0327bdb887;
}

// name: Compression Ratio of Texture Memory Written
// description: Ratio of compressed to uncomressed texture memory written
// type: Rate
function CompressionRatioTextureMemoryWritten() {
    var cmpUncompressedDataBytes =
        16 * _b0c17a5c575cab4f46333e38bd6c5902886cb23f0b0bdd39ee50a545af04f980 +
        16 * _29d1821c8f9a15b9486ef2d149a664089d8baf032b29051eb8c4dbffad95563a +
        8 * _ab00529c9f233f26d1887a6552565a5c815d7206fae8e841e96653d6e44d9720 +
        32 * _73a07a4eb409d7dcb5949ffd6f41cd2f15b0af9dff6303cff06971131fd13dff +
        16 * _820d6093023c1b36179134d53e2590bc112fb8589e446faccb6c1ff32b803a44 +
        8 * Math.min(_3f4145264446ac3fa9165321f5ce12ea5284d0b621920a5fd65e32beac4d6f8e, _152d131e904395c94f62600b1aee804dd01f6413a377d420b51aab9b3f3f9eea) + 32 * Math.max(_3f4145264446ac3fa9165321f5ce12ea5284d0b621920a5fd65e32beac4d6f8e - _152d131e904395c94f62600b1aee804dd01f6413a377d420b51aab9b3f3f9eea, 0) +
        8 * _36cab0e3ce544617b00b2244cfa7202ae54954238de0d91881ca83f4e6006890 +
        32 * _ed166f4251f67b6fe851d995eef5a54810e539a33c13bebd46871f67c1257db9 +
        16 * _671c439841f54003d8b1841ee0686bae625654ce991af1ece3a9b85634720775 +
        32 * _7bfee75e8041af01e3f7bd62a11b4cbda9b5ecb054574ace923b113697916b22 +
        32 * _9bb1a0053cbf09e81970aafc5720e4e418c43e0b2c326f087ded04c65dbc0e9b +
        16 * Math.min(_f8d45e0cb94a971819230fc94c9950574e128a668e4eb6af960d96a404e90992, _9ecd8b7f3f81f6032e49e5badac7785219bc515959163b44cf2ff0e729fb5ceb) + 32 * Math.max(_f8d45e0cb94a971819230fc94c9950574e128a668e4eb6af960d96a404e90992 - _9ecd8b7f3f81f6032e49e5badac7785219bc515959163b44cf2ff0e729fb5ceb, 0) +
        8 * _1c29b926ad18fee198bc9230dfdfdae383ec4d829a4be6b302ec5674f781ae10 +
        8 * _31f574c0d389246aecbc0a13edc218efe1f3530ad60535b352359f1b972a4ba4 +
        8 * _a73165b1618dd20a1cb5f732d8b79c01aa4e6de5d3a38bfb671bac7f386d7af7 +
        16 * _0b35f4e73bc24b0ddbf89f7eacab636514e7feb92400e7043d49c3a3f16085a6 +
        16 * _d1e5b9d556bef5fca687ee5e774d58e824d8aafbdf63f1d2ef7a5c0821a1baa2 +
        8 * _14df6325787f09d7a0686db47d6ac8d39ec78702b4ad93734091074e6e0b91ab +
        4 * Math.min(_6ccf72e51e7667238e3c39f661809a1fae562f5649a8cbf8664352226c10d500, _70df27b9e10f246504668289db86105460e36602cf247efab6b18d4934c670b2) + 32 * Math.max(_6ccf72e51e7667238e3c39f661809a1fae562f5649a8cbf8664352226c10d500 - _70df27b9e10f246504668289db86105460e36602cf247efab6b18d4934c670b2, 0);


    var cmpCompressedDataBytes = 32 * (_65651dd1b153cec80500d6665894d232894f2c83df5507865e1ef0c3f01bc6d0 + 2.0 * (_908f85285b4abff4a9dadb179123e90ac796cbfd79ff8c48df85253894e112bc + 2.0 * _95f000cd0a64e23286a0e749df3b5efaefc8e76bc15a12bf049ed47b71e67ae7));

    return cmpUncompressedDataBytes / Math.max(cmpCompressedDataBytes, 1);
}

// name: Compression Ratio of Texture Memory Read
// description: Ratio of compressed to uncomressed texture memory read
// type: Rate
function CompressionRatioTextureMemoryRead() {
    return (_1827ca25b7318e2df60eb0fe4f0c290b43054021ec3233e1fcdcf7b622fe4589 + _d71cecc319ceee3a8b2139d8eb4f992d7c1d97634b28c764596c845c528e79ff) / Math.max(_8788387fa2f782d31f4553bc55eb34284415d12b986df376e394838d5075f058, 1);
}

// name: VS Arithmetic Intensity
// description: ALU ops per byte of main memory traffic in vertex shader
// type: Rate
function VSArithmeticIntensity() {
    return VSALUInstructions() / Math.max(1, VSBytesReadFromMainMemory() + VSBytesWrittenToMainMemory());
}

// name: FS Arithmetic Intensity
// description: ALU Time in nSec per byte of main memory transfer in fragment shader
// type: Rate
function FSArithmeticIntensity() {
    return FSALUInstructions() / Math.max(1, FSBytesReadFromMainMemory() + FSBytesWrittenToMainMemory());
}

// name: CS Arithmetic Intensity
// description: ALU ops per byte of main memory traffic in compute shader
// type: Rate
function CSArithmeticIntensity() {
    return CSALUInstructions() / Math.max(1, BytesReadFromMainMemory() + BytesWrittenToMainMemory());
}

// name: VS Main Memory Throughput
// description: Main memory throughput in GB/s in a vertex shader
// type: Rate
function VSMainMemoryThroughput() {
    return (VSBytesReadFromMainMemory() + VSBytesWrittenToMainMemory()) / Math.max(1, (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e_vtx * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6));
}

// name: FS Main Memory Throughput
// description: Main memory throughput in GB/s in a fragment shader
// type: Rate
function FSMainMemoryThroughput() {
    return (FSBytesReadFromMainMemory() + FSBytesWrittenToMainMemory()) / Math.max(1, (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e_frg * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6));
}

// name: Main Memory Throughput
// description: Main memory throughput in GB/s
// type: Rate
function MainMemoryThroughput() {
    return (BytesReadFromMainMemory() + BytesWrittenToMainMemory()) / Math.max(1, (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6));
}

// name: VS ALU Performance
// description: ALU performance in Giga Ops / Sec in vertex shader
// type: Rate
function VSALUPerformance() {
    return VSALUInstructions() / Math.max(1, (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e_vtx * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6));
}

// name: FS ALU Performance
// description: ALU performance in Giga Ops / Sec in fragment shader
// type: Rate
function FSALUPerformance() {
    return FSALUInstructions() / Math.max(1, (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e_frg * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6));
}

// name: CS ALU Performance
// description: ALU performance in Giga Ops / Sec in compute shader
// type: Rate
function CSALUPerformance() {
    return CSALUInstructions() / Math.max(1, (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e_cmp * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6));
}

// name: Buffer Main Memory Bytes Read
// description: Total bytes read for buffers from main memory
// type: Value
function BytesReadForBuffersFromMainMemory() {
    return 64.0 * _3524ddd7c801ffbe5b629d1aae54b01dce1bd5cbabcadbac658fb15c9f1135fa;
}

// name: VS Buffer Main Memory Bytes Read
// description: Total bytes read for buffers from main memory for vertex shader
// type: Value
function VSBytesReadForBuffersFromMainMemory() {
    return 64.0 * _3524ddd7c801ffbe5b629d1aae54b01dce1bd5cbabcadbac658fb15c9f1135fa_vtx;
}

// name: FS Buffer Main Memory Bytes Read
// description: Total bytes read for buffers from main memory for fragment shader
// type: Value
function FSBytesReadForBuffersFromMainMemory() {
    return 64.0 * _3524ddd7c801ffbe5b629d1aae54b01dce1bd5cbabcadbac658fb15c9f1135fa_frg;
}

// name: Buffer Main Memory Bytes Written
// description: Total bytes written for buffers from main memory
// type: Value
function BytesWrittenForBuffersFromMainMemory() {
    return 64.0 * _d693bda8a291d4a4929c36b50377680028df60b900d0bae2e1feb5aef41d5404;
}

// name: VS Buffer Main Memory Bytes Written
// description: Total bytes written for buffers from main memory for vertex shader
// type: Value
function VSBytesWrittenForBuffersFromMainMemory() {
    return 64.0 * _d693bda8a291d4a4929c36b50377680028df60b900d0bae2e1feb5aef41d5404_vtx;
}

// name: FS Buffer Main Memory Bytes Written
// description: Total bytes written for buffers from main memory for fragment shader
// type: Value
function FSBytesWrittenForBuffersFromMainMemory() {
    return 64.0 * _d693bda8a291d4a4929c36b50377680028df60b900d0bae2e1feb5aef41d5404_frg;
}

// name: Texture Main Memory Bytes Written
// description: Total bytes written for textures to main memory
// type: Value
function TextureBytesWrittenToMainMemory() {
    return 64.0 * (_969097e14ac458fc664d8855c4cf42930633f3e7953b630ac64cefbfc631b504 + 2.0 * _762d4c9354eb1d7a3a6756b9847937475c7d144b361e89916be6793785daccf1 + _306343175ea6938c9a677c4a545c1b9c2d2d4b0f30fb496daca682a08b929e03 + 2.0 * _e01b12f6e785736c5416b03a1ac9de509c7bcc6311692077d53497150db6cb55 +
        _5bd1614f0c8060aefca1a2bd9a9e9ee750163626cdc0c38d723e94470730cfe6 + 2.0 * _c5b103e58e91d43549acb4af04601a97cecc95caa0e6fe0c9c3c35a3a60fbd45 + _5d503a1872859aa411818cfbcb70e41b501704501f31a039c3acb306fb382113 + 2.0 * _b6489d493ca65c9e43746d81294f5f613015fde58abf9a2945b0e6131c921e85)
}

// name: Z Main Memory Bytes Written
// description: Total bytes written for textures to main memory
// type: Value
function ZBytesWrittenToMainMemory() {
    return 64.0 * (_513d287e274b210e0367b2abc7ef2608b0059fb5a6acf749144343586fe1c637 + 2.0 * _4e90e2533a170479afd8d0b83a68177595b7245bf4ab6e20096a9e0c0529012e + _38ac6faf9eaef3f9faf843a65ce0c1f445989a19ba86e9386abeca4e0e01cf3d + 2.0 * _6d4821165f0bbae1363beb8117b91295a3ffad188a87aa55b06b10f7370fca85);
}

// name: Texture Main Memory Bytes Read
// description: Total bytes read for textures from main memory
// type: Value
function TextureBytesReadFromMainMemory() {
    return 64.0 * (_5dcbce50d229822aa963dcf83c2de8fbe54d8328f89e076ef096ddfd2fa7dd52 + _58ef35a421546beb70de0b899c35b32fe4d93474d5120fa782ebb62bf1f9683c);
}

// name: Buffer Read Limiter
// description: Measures the time during which buffer loads are attempted to execute as a percentage of peak buffer load performance.
// type: Percentage
function BufferLoadLimiter() {
    return _224fc5057da0739817ec8947d2fb1ad3ff63c2ceb3fabe0e34719c0eb465d7e9_norm / (4.0 * num_cores);
}

// name: VS Buffer Read Limiter
// description: VS Buffer read limiter
// type: Percentage
function VertexBufferLoadLimiter() {
    return _224fc5057da0739817ec8947d2fb1ad3ff63c2ceb3fabe0e34719c0eb465d7e9_norm_vtx / (4.0 * num_cores);
}

// name: FS Buffer Read Limiter
// description: FS Buffer read limiter
// type: Percentage
function FragmentBufferLoadLimiter() {
    return _224fc5057da0739817ec8947d2fb1ad3ff63c2ceb3fabe0e34719c0eb465d7e9_norm_frg / (4.0 * num_cores);
}

// name: Buffer Write Limiter
// description: Measures the time during which buffer stores are attempted to execute as a percentage of peak buffer load performance.
// type: Percentage
function BufferStoreLimiter() {
    return _b39850e6fdaf024c59701c0ee69b15fce7e4f6c92aa385e9920569a6f595745f_norm / (2.0 * num_cores);
}

// name: VS Buffer Write Limiter
// description: VS Buffer write limiter
// type: Percentage
function VertexBufferStoreLimiter() {
    return _b39850e6fdaf024c59701c0ee69b15fce7e4f6c92aa385e9920569a6f595745f_norm_vtx / (2.0 * num_cores);
}

// name: FS Buffer Write Limiter
// description: FS Buffer write limiter
// type: Percentage
function FragmentBufferStoreLimiter() {
    return _b39850e6fdaf024c59701c0ee69b15fce7e4f6c92aa385e9920569a6f595745f_norm_frg / (2.0 * num_cores);
}

// name: Fragment Input Interpolation Limiter
// description: Measures the time during which fragment shader input interpolation work is attempted to execute as a percentage of peak input interpolation performance.
// type: Percentage
function FragmentInputInterpolationLimiter() {
    return _e5f2d8a6cf9651b49b3b00bebdf815a5269b8c89fc3bc02057a3a14e28733495_norm / (1.0 * num_cores);
}

// name: GPU Last Level Cache Limiter
// description: Measures the time during which GPU’s last level cache is attempting to service read and write requests as a percentage of cache’s peak performance.
// type: Percentage
function L2CacheLimiter() {
    return (_5c5c55d05fb355aa5be61ac63c88eb4a2a521a47dd8f79c18b5c1df163d5cb55_norm + _c9bcd5df6397dc8477a12ddf9358bccbbb3d8e52fc3dadab320be9bbb14fe157_norm) / 4.0;
}

// name: GPU Last Level Cache Limiter Miss Rate
// description: Percentage of times GPU’s last level cache lookups are misses
// type: Percentage
function L2CacheMissRate() {
    return 100.0 * _44e2790fe56248cd45e2248d0f69699da605c77fab749daf6c865f1ab5f16563 / Math.max(_5c5c55d05fb355aa5be61ac63c88eb4a2a521a47dd8f79c18b5c1df163d5cb55, 1.0);
}

// name: Vertex Occupancy
// description: Measures how many vertex shader simdgroups are concurrently running in the GPU relative to the GPU’s maximum number of concurrently running simdgroups.
// type: Percentage
function VertexOccupancy() {
    return _4bb4a72bfa974f38e0143eef87e93ae69847e8612684f014350fb4a8c0692050_norm / (_d56cff6c89d6a3f5f8561cd89f1b36b2760c125d908074d984bc36678982991a * num_cores);
}

// name: Fragment Occupancy
// description: Measures how many fragment shader simdgroups are concurrently running in the GPU relative to the GPU’s maximum number of concurrently running simdgroups.
// type: Percentage
function FragmentOccupancy() {
    return _367a60a3f4d39b45114c57a560ad1bad4f9f62798346ead3a98f790ad32537a6_norm / (_d56cff6c89d6a3f5f8561cd89f1b36b2760c125d908074d984bc36678982991a * num_cores);
}

// name: Compute Occupancy
// description: Measures how many compute shader simdgroups are concurrently running in the GPU relative to the GPU’s maximum number of concurrently running simdgroups.
// type: Percentage
function ComputeOccupancy() {
    return _6b3a9b25a65b692ad1039bcc4c052d5a85e40a9410946c0cdf5dc85d993e2131_norm / (_d56cff6c89d6a3f5f8561cd89f1b36b2760c125d908074d984bc36678982991a * num_cores);
}

// name: GPU Read Bandwidth
// description: Measures how much memory, in gigabytes per second, are read by the GPU from a memory external to the GPU (potentially main memory).
// type: Rate
function GPUReadBandwidth() {
    return BytesReadFromMainMemory() / Math.max(1, (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6));
}

// name: GPU Write Bandwidth
// description: Measures how much memory, in gigabytes per second, are written by the GPU to a memory external to the GPU (potentially main memory).
// type: Rate
function GPUWriteBandwidth() {
    return BytesWrittenToMainMemory() / Math.max(1, (_792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e * _ca35e381a2fdcb4f0dbc27e38f0b0bd85835a4197c6256f58d2c59888cb0fce6));
}

// name: ALU Utilization
// description: ALU utilization
// type: Percentage
function ALUUtilization() {
    return _c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2_norm / num_cores;
}

// name: F32 Utilization
// description: F32 utilization
// type: Percentage
function F32Utilization() {
    return (_55d0c180ad87ec962138c5c289baadd6969fdd2cd21ef68ab1f91190b6c33812 * _a6e6cc683eebf697b2a31bd7d4f877afee2419f6882f55b2f4ea296c9a368b99_norm * 4) / (64 * num_cores);
}

// name: F16 Utilization
// description: F16 utilization
// type: Percentage
function F16Utilization() {
    return (_55d0c180ad87ec962138c5c289baadd6969fdd2cd21ef68ab1f91190b6c33812 * _0af59bb3dd0a90f2664cd5e5601b3c56bf91e40478def55647411007dc5394d3_norm * 4) / (128 * num_cores);
}

// name: IC Utilization
// description: IC utilization
// type: Percentage
function ICUtilization() {
    return (_55d0c180ad87ec962138c5c289baadd6969fdd2cd21ef68ab1f91190b6c33812 * _04ec68f75ab42cefa364623ffb059b101b9d6d35ed0e59abbbc94170b4ec6cbe_norm * 4) / (32 * num_cores);
}

// name: SCIB Utilization
// description: SCIB utilization
// type: Percentage
function SCIBUtilization() {
    return (_55d0c180ad87ec962138c5c289baadd6969fdd2cd21ef68ab1f91190b6c33812 * _4ffbecab1c5697bfb927de016f6ddd4b010ddb0588049be5243c148e62d21409_norm * 4) / (128 * num_cores);
}

// name: Texture Sample Utilization
// description: Texture sample utilization
// type: Percentage
function TextureSamplesUtilization() {
    return _6d86d89a09a872e62b809325d49d6967e2327aa5d1d4ea471d700f29696b9560_norm / (2.0 * num_cores);
}

// name: Texture Write Utilization
// description: Texture write utilization
// type: Percentage
function TextureWritesUtilization() {
    return _bb9dbea90df77e54beebae872b35923d727fd2a59d6905410b32092d6d561402_norm / (1.0 * num_cores);
}

// name: Buffer Load Utilization
// description: Buffer load utilization
// type: Percentage
function BufferLoadUtilization() {
    return _8cd74591f03ed3eb90e0c547b8bf21ae7eed4129053f40570cce56a39a690015_norm / (4 * num_cores);
}

// name: Buffer Store Utilization
// description: Buffer store utilization
// type: Percentage
function BufferStoreUtilization() {
    return _3dfa6da703ded5b65a76ddf0aa3f7f28f19b4a624ef77347a925f55bf66a82f5_norm / (2 * num_cores);
}

// name: Threadgroup/Imageblock Load Utilization
// description: Threadgroup/Imageblock load utilization
// type: Percentage
function LocalLoadUtilization() {
    return _4f6aebbe216cd96fa4684995ac68478cbdb59c6706480ecbbb9f101d892bb540_norm / (4.0 * num_cores);
}

// name: Threadgroup/Imageblock Store Utilization
// description: Threadgroup/Imageblock store utilization
// type: Percentage
function LocalStoreUtilization() {
    return _968353d331d798ff8c65ce5f1d5294c1f4bcd54f8004fe37c0ec8e0327bdb887_norm / (4.0 * num_cores);
}

// name: Fragment Input Interpolation Utilization
// description: Fragment input interpolation utilization
// type: Percentage
function FragmentInputInterpolationUtilization() {
    return _95b5e692e6eefd3c235ce8ef2be2b781023c467a45108be8e5bb4beea25dfe6f_norm / (1.0 * num_cores);
}

// name: GPU Last Level Cache Utilization
// description: GPU last level cache utilization
// type: Percentage
function L2CacheUtilization() {
    return _5c5c55d05fb355aa5be61ac63c88eb4a2a521a47dd8f79c18b5c1df163d5cb55_norm / 4.0;
}

// name: Partial Renders count
// description: Count number of partial renders in the encoder
// type: Count
function PartialRenders() {
    return _5018ff101ee67fee86c0348828e1c15e0a4dfdc0e37c99134711930a1c5eaa79;
}

// name: Parameter Buffer Bytes Used
// description: Parameter Buffer Bytes Used
// type: Count
function ParameterBufferBytesUsed() {
    return _4d198d9a415b725cd301ce6cf3ecaa00d37481ec5d44c0d72094acf20d374c74;
}

// name: Frag Ticks Count
// description: Frag Tick for limiters
// type: Value
function FRGTicks() {
    return _06f73dd77cc4f21054a372b34a28a1d5d054ff7241ee73be67f927d897211048;
}

// name: Comprehensive Fragment Input Interpolation Limiter
// description: Comprehensive Fragment Input Interpolation limiter
// type: Percentage
function ComprehensiveFragmentInputInterpolationLimiter() {
    return Math.max(FragmentInputInterpolationLimiter(), Math.min((_81e94ff007a99cc84c59352583de71dad427a422d70be052cff38c6e018907ee_norm + _c1043a6e3112f17390996d9c7e6ccd58dd5e1fd64f7fb92fa4f59c07e569bf95_norm) / (1.0 * num_cores), 100.0));
}

// name: Comprehensive Fragment Input Interpolation Utilization
// description: Comprehensive Fragment Input Interpolation Utilization
// type: Percentage
function ComprehensiveFragmentInputInterpolationUtilization() {
    return Math.max(FragmentInputInterpolationUtilization(), Math.min(_81e94ff007a99cc84c59352583de71dad427a422d70be052cff38c6e018907ee_norm / (1.0 * num_cores), 100.0));
}

// name: Texture Cache Limiter
// description: Texture cache limiter
// type: Percentage
function TextureCacheLimiter() {
    return Math.min((_e04363b0193aecfc56d5f1c5edb7fc2147625522e4ecdb3a8d24ae32f45eaa5c_norm + _f89636291d4d2848204d266a1eff5d7b231750cc967f91d005cb1fc30779b1cc_norm) / (num_cores), 100.0);
}

// name: Sparse Texture Translation Limiter
// description: Sparse texture address translation limiter
// type: Percentage
function SparseTextureTranslationLimiter() {
    return Math.min(Math.max(_1f271f3430e8ca846395d050220e5ad9537ae2993c95071369b9613db4c36b9b_norm + _d8ecb4c1fc88e27e17d6826cdc602f8657919610ca490526acdf21bcc5394ab7_norm, _adcaa1bfdaea7d31b4a776ffd13089ba401d5c9c533c77378b5f378062215fdb_norm + _883c062d224c59ccd4c4303a7caeacbd0aa87cd6fffd5347dfedb52a23f4a6e5_norm, _d37f73c804be99f61d4e0d20151d2305f2c4fec5990853e47d56da4a0d75cb31_norm + _37354b6e4ee3693b3b82dcc6cc0c4aaf5fbbdf1e2a44b7ce11d6ed6f45dad635_norm) / (num_cores), 100.0);
}

// name: Number of Sparse Texture Requests
// description: Sparse texture requests
// type: Value
function SparseTextureRequests() {
    return _d2acb8217628c8c28df030d3f819e3831a16760dc5af79722487d789d9cbe02d + _847829852334f2b320f2b2890d9a9c3dd7022b760b29a94540ba4fe13d1dd91a + _a7dd90063ddd29bf1b2d1259297cca0904b949cc92e9dee2e929fec2294f0422;
}

// name: Average Sparse Texture Request Size
// description: Average Sparse Texture Request Size in KB
// type: Rate
function AverageSparseTextureRequestSize() {
    return 16.0 * (_d2acb8217628c8c28df030d3f819e3831a16760dc5af79722487d789d9cbe02d + 4.0 * _847829852334f2b320f2b2890d9a9c3dd7022b760b29a94540ba4fe13d1dd91a + 16.0 * _a7dd90063ddd29bf1b2d1259297cca0904b949cc92e9dee2e929fec2294f0422) / Math.max(SparseTextureRequests(), 1.0);
}

// name: Fragment Generator Primitive Utilization
// description: Fragment generator primitive processing utilization
// type: Percentage
function FragmentGeneratorPrimitiveUtilization() {
    return (_64a10cb112e74a4ec02f177b245e3f83edd61c0f78bc5bc7ae4978ce28f07f83_norm) / (0.25 * num_cores);
}

// name: Fragment Rasterizer Utilization
// description: Fragment Rasterizer utilization
// type: Percentage
function FragmentRasterizerUtilization() {
    var msaa = 2.0 * _aabc9758d4e52fd36dfb1a0e38171798aa7bf2ec665135dc298c1aa1a7c10760_frg / Math.max(_7cef4e481233623472ea3e1f6b4131fabb20f247f7e5eae173dfd693aa60d0ff_frg, 1.0);
    if (msaa > 1.1) {
        return Math.min((_aabc9758d4e52fd36dfb1a0e38171798aa7bf2ec665135dc298c1aa1a7c10760_norm_frg) / (num_cores), 100.0);
    }
    return Math.min((2.0 * _aabc9758d4e52fd36dfb1a0e38171798aa7bf2ec665135dc298c1aa1a7c10760_norm_frg) / (num_cores), 100.0);
}

// name: Fragment Quad Processor Utilization
// description: Fragment quad processor utilization
// type: Percentage
function FragmentQuadProcessingUtilization() {
    return Math.min((4.0 * _ca0d54323c1777d994357aaacdb7beac572bea11cd16afed4c756f3dc9496a18_norm_frg) / (2.0 * num_cores), 100.0);
}

// name: Pre Culling Primitive Block Utilization
// description: Pre Culling primitive block utilization
// type: Percentage
function PreCullPrimitiveBlockUtilization() {
    return Math.min(_46210435e8bd691719dc45391f51ef552bf7e745c1401ee9943aa6f85086336e_norm_vtx / (0.5 * num_gps), 100.0);
}

// name: Pre Culling Primitive Count
// description: Pre Culling primitive count
// type: Percentage
function PreCullPrimitiveCount() {
    return _46210435e8bd691719dc45391f51ef552bf7e745c1401ee9943aa6f85086336e_vtx;
}

// name: Post Clipping Culling Primitive Block Utilization
// description: Post Clipping Culling primitive block utilization
// type: Percentage
function PostClipCullPrimitiveBlockUtilization() {
    return Math.min(_2d3c257f33af88b8488658fb5b6a86f64cb02169b680e1250d3f37d373a4197f_norm_vtx / (num_gps), 100.0);
}

// name: Primitive Tile Intersection Utilization
// description: Primitive tile intersection utilization
// type: Percentage
function PrimitiveTileIntersectionUtilization() {
    return Math.min(_149b69750a3c80a27d163a4ca69ec03e3b39b3c0afe9c90c8cd37a128832cb13_norm_vtx / (num_gps), 100.0);
}

// name: Tiler Utilization
// description: Tiling block utilization
// type: Percentage
function TilerUtilization() {
    return Math.min(_da824fe9269c1efd80cb71a6e5415be160b6f43b41e858cb83976c4140b052a5_norm_vtx / (num_gps), 100.0);
}

// name: GPU to main memory limiter
// description: GPU to main memory limiter
// type: Percentage
function MainMemoryTrafficLimiter() {
    return Math.min((_6d6a7c8efb15986fa71f8bf4a6a06f8942199b36680e516766e92490607c958d_norm + _fdc48a2370f6885da6ac169661812057de2cf71fbbbcb5df8348a78f112992dc_norm) / 4.0, 100.0);
}


// name: GPU to main memory bidirectional traffic in bytes
// description: GPU to main memory bidirectional traffic in bytes
// type: Value
function MainMemoryTraffic() {
    return 64.0 * _6d6a7c8efb15986fa71f8bf4a6a06f8942199b36680e516766e92490607c958d;
}

// name: VS Invocation Unit Utilization
// description: VS invocation unit utilization
// type: Percentage
function VSInvocationUtilization() {
    return Math.min(_da2d5f5fd43e7edda6d5635752a29f09d285cf47c2ecd0a1b83b1ba3eddcef55_norm_vtx / (0.5 * num_gps), 100.0);
}

// name: Fragment Z Store Unit Utilization
// description: Fragment Z store unit utilization
// type: Percentage
function FragmentZStoreUtilization() {
    return Math.min((_63b721bdb7ff9f45f3835f7e6a8a4595b1fed0038ae9a76cb853fc36756386c9_norm_frg) / num_cores, 100.0);
}

// name: Fragment Z Store Unit Bytes Written
// description: Fragment Z store unit bytes written
// type: Value
function FragmentZStoreBytes() {
    return _63b721bdb7ff9f45f3835f7e6a8a4595b1fed0038ae9a76cb853fc36756386c9 * 32;
}

// name: Compression Ratio of Z Texture Memory Written
// description: Ratio of compressed to uncomressed depth/stencil texture memory written
// type: Rate
function CompressionRatioZTextureMemoryWritten() {
    return FragmentZStoreBytes() / Math.max(ZBytesWrittenToMainMemory(), 1);
}

// name: Fragment Generator Primitive Processed
// description: Fragment generator primitive processed
// type: Value
function FragmentGeneratorPrimitiveProcessed() {
    return _64a10cb112e74a4ec02f177b245e3f83edd61c0f78bc5bc7ae4978ce28f07f83;
}

// name: Fragment Quads Processed
// description: Fragment generated quads processed
// type: Value
function FragmentQuadsProcessed() {
    return 4.0 * _ca0d54323c1777d994357aaacdb7beac572bea11cd16afed4c756f3dc9496a18_frg;
}

// name: Pre Culling Primitive Count
// description: Pre Culling primitive count
// type: Value
function PreCullPrimitiveCount() {
    return _46210435e8bd691719dc45391f51ef552bf7e745c1401ee9943aa6f85086336e_vtx;
}

// name: Fragment Bytes Written
// description: Fragment bytes written
// type: Value
function FragmentStoreBytes() {
    return 4.0 * (_60b74ec0e06a7b2279ca3c1131155a13c4a5b231d1e5d98a55a0990939e88168 + 2.0 * _9290d4f55ee82ba67532c0cd99b14ce8e3cc547e714255c25f52f81ad7050ab2 + 4.0 * _4e9aebe595eff4fd33ee46fa2962bd3955adb83eb002404513ce342f8cfca446 + 8.0 * _893ab5dd2699dd85fb9a6332f8bf65d8ca8b3cfe21c74531833f012637d9694b + 16.0 * _afb0184e960da27de79a4a2c74fcee8a7eab380f37462d19d027b357c8005eae);
}

// name: Primitive Tile Intersections
// description: Primitive tile intersections
// type: Value
function PrimitiveTileIntersections() {
    return _149b69750a3c80a27d163a4ca69ec03e3b39b3c0afe9c90c8cd37a128832cb13_vtx;
}

// name: Tiles Processed in Tiler
// description: Tiles processed by tiling block
// type: Value
function TilerTilesProcessed() {
    return _da824fe9269c1efd80cb71a6e5415be160b6f43b41e858cb83976c4140b052a5_vtx;
}

// name: Fragment Generator Tiles Processed
// description: Fragment Generator Tiles Processed
// type: Value
function FragmentGeneratorTilesProcessed() {
    return _eda5bce70befa39e7c6029505c0269211092c220048a502fd8fa2fe30895465b;
}

// name: Texture Cache Read Misses
// description: Texture cache miss count
// type: Value
function TextureCacheMissCount() {
    return _19109618d2fc2db66c23fe425a0a19ec06c81f05bb676c40aa572b76891428e6;
}

// name: Depth Stencil Texture Main Memory Bytes Read
// description: Total bytes read for depth / stencil textures from main memory
// type: Value
function ZTextureBytesReadFromMainMemory() {
    return 64.0 * (_71b7e9060085fee2d685ddb1202c79855cb96962ceb1328f9b5a993944ef2800 + _4f09bffac0ab5e557c43c129b54a4ea67269654b4cd033eccf3120127543505c);
}

// name: Fragment Z Unit Bytes Read
// description: Fragment Z unit bytes read
// type: Value
function FragmentZLoadBytes() {
    return _40680272e25f5a98ef1fdae57c0be82cc7fb940000907f1a4d46547de8525db0 * 64;
}

// name: Fragment Interpolation Instructions
// description: Fragment interpolation instructions
// type: Value
function FragmentInterpolationInstructions() {
    return 32 * (_81e94ff007a99cc84c59352583de71dad427a422d70be052cff38c6e018907ee + _95b5e692e6eefd3c235ce8ef2be2b781023c467a45108be8e5bb4beea25dfe6f);
}

// name: ALU FP32 Instructions Executed
// description: ALU FP32 Instructions executed
// type: Value
function ALUF32() {
    return (_8e70441b8b0d9ded3ed900ec761f9f5960b106c5a304b44d62781621d5d1861a * 16);
}

// name: ALU FP16 Instructions Executed
// description: CS ALU FP16 Instructions executed
// type: Value
function ALUF16() {
    return (_82b2f93079459b00fb869444cfcf44604cc1a91d28078cd6bfd7bb6ea6ba423d * 16);
}

// name: ALU 32-bit Integer and Conditional Instructions Executed
// description: ALU Select, Conditional, 32-bit Integer and Boolean Instructions executed
// type: Value
function ALUInt32AndCond() {
    return (_23c51175314006fa4b6798dcb173a814349e2e5947244cfdba868be736d2bc03 * 16);
}

// name: ALU Integer and Complex Instructions Executed
// description: ALU Integer and Complex Instructions executed
// type: Value
function ALUIntAndComplex() {
    return (_827783963eafa9275a53fc2b3ef13214ab90939fcc81572c4260e2eac9bd2acb * 16);
}

// name: ALU FP32 Instructions Issued
// description: ALU FP32 Instructions issued
// type: Value
function ALUF32Issued() {
    return (_a6e6cc683eebf697b2a31bd7d4f877afee2419f6882f55b2f4ea296c9a368b99 * 128);
}

// name: ALU FP16 Instructions Issued
// description: CS ALU FP16 Instructions issued
// type: Value
function ALUF16Issued() {
    return (_0af59bb3dd0a90f2664cd5e5601b3c56bf91e40478def55647411007dc5394d3 * 128);
}

// name: ALU 32-bit Integer and Conditional Instructions Issued
// description: ALU Select, Conditional, 32-bit Integer and Boolean Instructions issued
// type: Value
function ALUInt32AndCondIssued() {
    return (_4ffbecab1c5697bfb927de016f6ddd4b010ddb0588049be5243c148e62d21409 * 128);
}

// name: ALU Integer and Complex Instructions Issued
// description: ALU Integer and Complex Instructions issued
// type: Value
function ALUIntAndComplexIssued() {
    return (_04ec68f75ab42cefa364623ffb059b101b9d6d35ed0e59abbbc94170b4ec6cbe * 128);
}

// name: Fragment Generator Primitive Processed Per Tile
// description: Fragment generator primitive processed per tile
// type: Rate
function AveragePrimitiveProcessedPerTile() {
    return FragmentGeneratorPrimitiveProcessed() / FragmentGeneratorTilesProcessed();
}

// name: Opaque Fragment Quads Processed
// description: Percentage of opaque quads processed out of total quads
// type: Percentage
function OpaqueFragmentQuadsProcessed() {
    return Math.min(100.0 * 4.0 * _719a713b390f2b37bbbe8ca62f3053819539a3fc60d05b02f21b2c8435fb73a6 / Math.max(FragmentQuadsProcessed(), 1.0), 100.0);
}

// name: Translucent Fragment Quads Processed
// description: Percentage of translucent quads processed out of total quads
// type: Percentage
function TranslucentFragmentQuadsProcessed() {
    return Math.min(100.0 * 4.0 * _fade8eea03e1fbf9a3d3cd6ab6bfd82b70bc1595ffb23f1b638746baa6c672e0 / Math.max(FragmentQuadsProcessed(), 1.0), 100.0);
}

// name: Feedback Fragment Quads Processed
// description: Percentage of feedback quads processed out of total quads
// type: Percentage
function FeedBackFragmentQuadsProcessed() {
    return Math.min(100.0 * 4.0 * (_db1f507c85a72a4148283a69481d823edb23fbfb999acf18fb2d155eb7edc768 + _879d7622b5c9023712d7cc6c70f432757ab72505afba79be4dcb023459f9658a) / Math.max(FragmentQuadsProcessed(), 1.0), 100.0);
}

// name: Texture Filtering Limiter
// description: Measures the time during which texture filtering is attempted to execute as a percentage of peak texture filtering performance.
// type: Percentage
function TextureFilteringLimiter() {
    return (_d11d0ca656849a8048dbe7d1d6761d3cbcf463d9196a20b3da7e6a554fd0652f_norm + _8e40208f4632cf3bab4b21f7d8df3129241f89d2bfbac698efbd3f75a909833c_norm) / (8.0 * num_cores);
}

// name: Texture Filtering Utilization
// description: Texture filtering utilization
// type: Percentage
function TextureFilteringUtilization() {
    return _d11d0ca656849a8048dbe7d1d6761d3cbcf463d9196a20b3da7e6a554fd0652f_norm / (8.0 * num_cores);
}

// name: Texture Cache Utilization
// description: Texture cache utilization
// type: Percentage
function TextureCacheUtilization() {
    return Math.min(_e04363b0193aecfc56d5f1c5edb7fc2147625522e4ecdb3a8d24ae32f45eaa5c_norm / num_cores, 100.0);
}

var GRC_TIMESTAMP = 0;
var GRC_GPU_CYCLES = 0;
var GRC_ENCODER_ID = 0;
var GRC_KICK_TRACE_ID = 0;
var GRC_SAMPLE_TYPE = 0;
var _7297c7ee63bc3f774b2e5f2e665cd87efcbf40dd3e6b66a9c08f8ebfdae4019e = 0;
var _192193e6c7ce23b86614fecbd983be5c3d4ea08d47c42ee19db85a736c0cbf7e = 0;
var _c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2 = 0;
var _aac2d2ece8ff1acbf2ab0f821c8f1e4e2dbb2ca4c3a6918e2dc458dfab8ee05c = 0;
var _4bb4a72bfa974f38e0143eef87e93ae69847e8612684f014350fb4a8c0692050 = 0;
var _7646a8523871192073a29fb3af219f4dbddae3339e969e0da8ef8d84a3d46ec5 = 0;
var _6b3a9b25a65b692ad1039bcc4c052d5a85e40a9410946c0cdf5dc85d993e2131 = 0;
var _c9bcd5df6397dc8477a12ddf9358bccbbb3d8e52fc3dadab320be9bbb14fe157 = 0;
var _d11d0ca656849a8048dbe7d1d6761d3cbcf463d9196a20b3da7e6a554fd0652f = 0;
var _367a60a3f4d39b45114c57a560ad1bad4f9f62798346ead3a98f790ad32537a6 = 0;
var _e7982344eb9c10ce1e1e9e179c01bb8a55934656fd5d499f956d6e35e42f1f10 = 0;
var _b39850e6fdaf024c59701c0ee69b15fce7e4f6c92aa385e9920569a6f595745f = 0;
var _224fc5057da0739817ec8947d2fb1ad3ff63c2ceb3fabe0e34719c0eb465d7e9 = 0;
var _5c5c55d05fb355aa5be61ac63c88eb4a2a521a47dd8f79c18b5c1df163d5cb55 = 0;
var _d201fed97c60848e3714502b203a0ad4e2820937c140dbf6a9db1cb31be194dd = 0;
var _190175e7010a5c90cc957e3f3eed64c3910111ef228808fbb2462cd269524ef5 = 0;
var _bb9dbea90df77e54beebae872b35923d727fd2a59d6905410b32092d6d561402 = 0;
var _63b42fb9d33e39b5f913060438c759d841275b394631cb7a8145853e9a04ef67 = 0;
var _8e40208f4632cf3bab4b21f7d8df3129241f89d2bfbac698efbd3f75a909833c = 0;
var _792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e = 0;
var _e5f2d8a6cf9651b49b3b00bebdf815a5269b8c89fc3bc02057a3a14e28733495 = 0;
var _DerivedCounterResult = [];
var _LastTimestamp = 0;

function _SetAndEvaluateRawCounterValues(numSamples) {
    _DerivedCounterResult = [];
    for (var sampleIndex = 0; sampleIndex < numSamples; ++sampleIndex) {
        var timestamp = (_RawCounterValues[0 + sampleIndex * 27]) * TIMEBASE_NUMER / TIMEBASE_DENOM;
        MTLStat_nSec = timestamp - _LastTimestamp;
        if (MTLStat_nSec > 1330000) { MTLStat_nSec = 1330000;}
        var sampleStartIndex = sampleIndex * 27 + 1;
        GRC_TIMESTAMP = _RawCounterValues[0 + sampleStartIndex];
        GRC_TIMESTAMP_norm = _RawCounterValues[0 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        GRC_GPU_CYCLES = _RawCounterValues[1 + sampleStartIndex];
        GRC_GPU_CYCLES_norm = _RawCounterValues[1 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        GRC_ENCODER_ID = _RawCounterValues[2 + sampleStartIndex];
        GRC_ENCODER_ID_norm = _RawCounterValues[2 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        GRC_KICK_TRACE_ID = _RawCounterValues[3 + sampleStartIndex];
        GRC_KICK_TRACE_ID_norm = _RawCounterValues[3 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        GRC_SAMPLE_TYPE = _RawCounterValues[4 + sampleStartIndex];
        GRC_SAMPLE_TYPE_norm = _RawCounterValues[4 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _7297c7ee63bc3f774b2e5f2e665cd87efcbf40dd3e6b66a9c08f8ebfdae4019e = _RawCounterValues[5 + sampleStartIndex];
        _7297c7ee63bc3f774b2e5f2e665cd87efcbf40dd3e6b66a9c08f8ebfdae4019e_norm = _RawCounterValues[5 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _192193e6c7ce23b86614fecbd983be5c3d4ea08d47c42ee19db85a736c0cbf7e = _RawCounterValues[6 + sampleStartIndex];
        _192193e6c7ce23b86614fecbd983be5c3d4ea08d47c42ee19db85a736c0cbf7e_norm = _RawCounterValues[6 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2 = _RawCounterValues[7 + sampleStartIndex];
        _c4c7e4c8f7b6488a9a980bba9f849c9e5d8e4bbb1e2c134cef7620b6faf7d6a2_norm = _RawCounterValues[7 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _aac2d2ece8ff1acbf2ab0f821c8f1e4e2dbb2ca4c3a6918e2dc458dfab8ee05c = _RawCounterValues[8 + sampleStartIndex];
        _aac2d2ece8ff1acbf2ab0f821c8f1e4e2dbb2ca4c3a6918e2dc458dfab8ee05c_norm = _RawCounterValues[8 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _4bb4a72bfa974f38e0143eef87e93ae69847e8612684f014350fb4a8c0692050 = _RawCounterValues[9 + sampleStartIndex];
        _4bb4a72bfa974f38e0143eef87e93ae69847e8612684f014350fb4a8c0692050_norm = _RawCounterValues[9 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _7646a8523871192073a29fb3af219f4dbddae3339e969e0da8ef8d84a3d46ec5 = _RawCounterValues[10 + sampleStartIndex];
        _7646a8523871192073a29fb3af219f4dbddae3339e969e0da8ef8d84a3d46ec5_norm = _RawCounterValues[10 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _6b3a9b25a65b692ad1039bcc4c052d5a85e40a9410946c0cdf5dc85d993e2131 = _RawCounterValues[11 + sampleStartIndex];
        _6b3a9b25a65b692ad1039bcc4c052d5a85e40a9410946c0cdf5dc85d993e2131_norm = _RawCounterValues[11 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _c9bcd5df6397dc8477a12ddf9358bccbbb3d8e52fc3dadab320be9bbb14fe157 = _RawCounterValues[12 + sampleStartIndex];
        _c9bcd5df6397dc8477a12ddf9358bccbbb3d8e52fc3dadab320be9bbb14fe157_norm = _RawCounterValues[12 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _d11d0ca656849a8048dbe7d1d6761d3cbcf463d9196a20b3da7e6a554fd0652f = _RawCounterValues[13 + sampleStartIndex];
        _d11d0ca656849a8048dbe7d1d6761d3cbcf463d9196a20b3da7e6a554fd0652f_norm = _RawCounterValues[13 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _367a60a3f4d39b45114c57a560ad1bad4f9f62798346ead3a98f790ad32537a6 = _RawCounterValues[14 + sampleStartIndex];
        _367a60a3f4d39b45114c57a560ad1bad4f9f62798346ead3a98f790ad32537a6_norm = _RawCounterValues[14 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _e7982344eb9c10ce1e1e9e179c01bb8a55934656fd5d499f956d6e35e42f1f10 = _RawCounterValues[15 + sampleStartIndex];
        _e7982344eb9c10ce1e1e9e179c01bb8a55934656fd5d499f956d6e35e42f1f10_norm = _RawCounterValues[15 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _b39850e6fdaf024c59701c0ee69b15fce7e4f6c92aa385e9920569a6f595745f = _RawCounterValues[16 + sampleStartIndex];
        _b39850e6fdaf024c59701c0ee69b15fce7e4f6c92aa385e9920569a6f595745f_norm = _RawCounterValues[16 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _224fc5057da0739817ec8947d2fb1ad3ff63c2ceb3fabe0e34719c0eb465d7e9 = _RawCounterValues[17 + sampleStartIndex];
        _224fc5057da0739817ec8947d2fb1ad3ff63c2ceb3fabe0e34719c0eb465d7e9_norm = _RawCounterValues[17 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _5c5c55d05fb355aa5be61ac63c88eb4a2a521a47dd8f79c18b5c1df163d5cb55 = _RawCounterValues[18 + sampleStartIndex];
        _5c5c55d05fb355aa5be61ac63c88eb4a2a521a47dd8f79c18b5c1df163d5cb55_norm = _RawCounterValues[18 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _d201fed97c60848e3714502b203a0ad4e2820937c140dbf6a9db1cb31be194dd = _RawCounterValues[19 + sampleStartIndex];
        _d201fed97c60848e3714502b203a0ad4e2820937c140dbf6a9db1cb31be194dd_norm = _RawCounterValues[19 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _190175e7010a5c90cc957e3f3eed64c3910111ef228808fbb2462cd269524ef5 = _RawCounterValues[20 + sampleStartIndex];
        _190175e7010a5c90cc957e3f3eed64c3910111ef228808fbb2462cd269524ef5_norm = _RawCounterValues[20 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _bb9dbea90df77e54beebae872b35923d727fd2a59d6905410b32092d6d561402 = _RawCounterValues[21 + sampleStartIndex];
        _bb9dbea90df77e54beebae872b35923d727fd2a59d6905410b32092d6d561402_norm = _RawCounterValues[21 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _63b42fb9d33e39b5f913060438c759d841275b394631cb7a8145853e9a04ef67 = _RawCounterValues[22 + sampleStartIndex];
        _63b42fb9d33e39b5f913060438c759d841275b394631cb7a8145853e9a04ef67_norm = _RawCounterValues[22 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _8e40208f4632cf3bab4b21f7d8df3129241f89d2bfbac698efbd3f75a909833c = _RawCounterValues[23 + sampleStartIndex];
        _8e40208f4632cf3bab4b21f7d8df3129241f89d2bfbac698efbd3f75a909833c_norm = _RawCounterValues[23 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e = _RawCounterValues[24 + sampleStartIndex];
        _792173079ffc5aacc2cea817d8812166e71ea17309e294d24ee2cc88d2fb1e8e_norm = _RawCounterValues[24 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        _e5f2d8a6cf9651b49b3b00bebdf815a5269b8c89fc3bc02057a3a14e28733495 = _RawCounterValues[25 + sampleStartIndex];
        _e5f2d8a6cf9651b49b3b00bebdf815a5269b8c89fc3bc02057a3a14e28733495_norm = _RawCounterValues[25 + sampleStartIndex] / _RawCounterValues[1 + sampleStartIndex];
        try {
            value = ALULimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = TPULimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = TextureFilteringLimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = PBELimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = BufferLoadLimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = BufferStoreLimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = LocalLoadLimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = LocalStoreLimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = FragmentInputInterpolationLimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = L2CacheLimiter();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = VertexOccupancy();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = FragmentOccupancy();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = ComputeOccupancy();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = GPUReadBandwidth();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        try {
            value = GPUWriteBandwidth();
            if (!isFinite(value)) {
                value = 0;
            }
            _DerivedCounterResult.push(value);
        } catch (err) {
            jsLog.error(err);
            _DerivedCounterResult.push(0);
        }
        _LastTimestamp = timestamp
    }
}

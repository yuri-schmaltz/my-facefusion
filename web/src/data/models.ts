export interface ModelMetadata {
    label: string;
    description?: string;
    category?: 'Performance' | 'Quality' | 'Balanced' | 'Experimental' | 'Legacy' | 'Style';
}

export const MODEL_DESCRIPTIONS: Record<string, Record<string, ModelMetadata>> = {
    face_swapper: {
        'blendswap_256': { label: 'BlendSwap (256px)', category: 'Balanced', description: 'Good for occlusion handling' },
        'inswapper_128': { label: 'InSwapper (128px)', category: 'Performance', description: 'Fastest, lower resolution' },
        'inswapper_128_fp16': { label: 'InSwapper FP16 (128px)', category: 'Performance', description: 'Fastest, lower memory' },
        'simswap_256': { label: 'SimSwap (256px)', category: 'Quality', description: 'Good identity preservation' },
        'simswap_512_unofficial': { label: 'SimSwap (512px)', category: 'Quality', description: 'High resolution, slower' },
        'unisim_256': { label: 'UniSim (256px)', category: 'Balanced' },
        'hyperswap_1a_256': { label: 'HyperSwap (256px)', category: 'Experimental', description: 'Newer architecture' },
        'ghost_256_unet': { label: 'Ghost UNet (256px)', category: 'Quality' },
        'ghost_256_resnet': { label: 'Ghost ResNet (256px)', category: 'Quality' },
    },
    face_enhancer: {
        'codeformer': { label: 'CodeFormer', category: 'Quality', description: 'High fidelity restoration' },
        'gfpgan_1.2': { label: 'GFPGAN 1.2', category: 'Legacy' },
        'gfpgan_1.3': { label: 'GFPGAN 1.3', category: 'Balanced' },
        'gfpgan_1.4': { label: 'GFPGAN 1.4', category: 'Quality', description: 'Best overall restoration' },
        'gpen_bfr_256': { label: 'GPEN (256px)', category: 'Performance' },
        'gpen_bfr_512': { label: 'GPEN (512px)', category: 'Balanced' },
        'restoreformer_plus_plus': { label: 'RestoreFormer++', category: 'Quality' },
    },
    frame_enhancer: {
        'real_esrgan_x2plus': { label: 'RealESRGAN x2', category: 'Balanced', description: '2x scaling' },
        'real_esrgan_x4plus': { label: 'RealESRGAN x4', category: 'Quality', description: '4x scaling, slower' },
        'real_esrnet_x4plus': { label: 'RealESRNet x4', category: 'Quality' },
        'realsr_x2_clear': { label: 'RealSR x2 - Clear', category: 'Quality' },
        'span_kendata_x4': { label: 'Span Kendata x4', category: 'Quality' },
        'lsdir_x4': { label: 'LSDIR x4', category: 'Quality' },
    },
    lip_syncer: {
        'wav2lip_gan': { label: 'Wav2Lip GAN', category: 'Quality', description: 'Better visual quality' },
        'wav2lip_gan_96': { label: 'Wav2Lip GAN (96px)', category: 'Performance' },
    },
    face_editor: {
        'live_portrait': { label: 'Live Portrait', category: 'Quality', description: 'Advanced expression editing' },
    },
    age_modifier: {
        'styleganex_age': { label: 'StyleGAN-EX Age', category: 'Quality' },
    },
    background_remover: {
        'u2net': { label: 'U2Net', category: 'Balanced' },
        'u2netp': { label: 'U2Net (Pruned)', category: 'Performance', description: 'Lightweight version' },
        'u2net_human': { label: 'U2Net Human', category: 'Quality', description: 'Optimized for portraits' },
        'modnet': { label: 'ModNet', category: 'Balanced' },
        'rmbg_2.0': { label: 'RMBG 2.0', category: 'Quality', description: 'Latest standard' },
        'ben_2': { label: 'Ben 2', category: 'Balanced' },
        'birefnet_general': { label: 'BiRefNet General', category: 'Quality' },
    }
};

export const getModelMetadata = (processor: string, model: string): ModelMetadata => {
    return MODEL_DESCRIPTIONS[processor]?.[model] || { label: model, category: 'Balanced' };
};

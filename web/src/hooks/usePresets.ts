import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/ToastContext';

export interface Preset {
    id: string;
    name: string;
    settings: Record<string, any>;
    timestamp: number;
}

const STORAGE_KEY = 'faceforge_presets';
const LEGACY_STORAGE_KEY = 'facefusion_presets';

export const usePresets = (
    currentSettings: Record<string, any>,
    onApplySettings: (settings: Record<string, any>) => void
) => {
    const [presets, setPresets] = useState<Preset[]>([]);
    const { addToast } = useToast();

    // Load presets on mount
    useEffect(() => {
        const stored = localStorage.getItem(STORAGE_KEY) ?? localStorage.getItem(LEGACY_STORAGE_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                setPresets(parsed);
                if (!localStorage.getItem(STORAGE_KEY)) {
                    localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
                }
            } catch (e) {
                console.error("Failed to parse presets", e);
            }
        }
    }, []);

    const savePreset = (name: string) => {
        if (!name.trim()) {
            addToast("Please enter a preset name", "warning");
            return;
        }

        const newPreset: Preset = {
            id: Date.now().toString(),
            name: name.trim(),
            settings: { ...currentSettings }, // Deep copy relevant settings
            timestamp: Date.now()
        };

        const updated = [...presets, newPreset];
        setPresets(updated);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        addToast(`Preset "${name}" saved!`, "success");
    };

    const loadPreset = (presetId: string) => {
        const preset = presets.find(p => p.id === presetId);
        if (preset) {
            onApplySettings(preset.settings);
            addToast(`Preset "${preset.name}" loaded!`, "success");
        }
    };

    const deletePreset = (presetId: string) => {
        const updated = presets.filter(p => p.id !== presetId);
        setPresets(updated);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        addToast("Preset deleted", "info");
    };

    return {
        presets,
        savePreset,
        loadPreset,
        deletePreset
    };
};

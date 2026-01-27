import React, { useEffect, useState } from 'react';
import { processors } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Select, SelectItem } from './ui/select';
import { Slider } from './ui/slider';
import { Settings2 } from 'lucide-react';

interface ProcessorChoices {
    [key: string]: {
        models?: string[];
        set?: { [key: string]: string[] };
        weight_range?: number[];
        blend_range?: number[];
        direction_range?: number[];
        factor_range?: number[];
        areas?: string[];
    };
}

interface ProcessorSettingsProps {
    activeProcessors: string[];
    currentSettings: any;
    onUpdate: (key: string, value: any) => void;
}

const ProcessorSettings: React.FC<ProcessorSettingsProps> = ({
    activeProcessors,
    currentSettings,
    onUpdate
}) => {
    const [choices, setChoices] = useState<ProcessorChoices | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchChoices = async () => {
            try {
                const res = await processors.getChoices();
                setChoices(res.data);
            } catch (err) {
                console.error("Failed to fetch processor choices:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchChoices();
    }, []);

    if (loading || !choices || activeProcessors.length === 0) return null;

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-2 text-neutral-400 px-1 mb-2">
                <Settings2 className="w-4 h-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">Processor Settings</span>
            </div>

            {activeProcessors.map((proc) => {
                const procChoices = choices[proc];
                if (!procChoices) return null;

                return (
                    <Card key={proc} className="bg-neutral-900/50 border-neutral-800 backdrop-blur-sm overflow-hidden">
                        <CardHeader className="py-3 px-4 border-b border-neutral-800 bg-neutral-900/30">
                            <CardTitle className="text-sm font-medium text-neutral-200 capitalize">
                                {proc.replace('_', ' ')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 space-y-4">
                            {/* Model Selection */}
                            {procChoices.models && (
                                <div className="space-y-2">
                                    <Label className="text-xs text-neutral-400">Model</Label>
                                    <Select
                                        value={currentSettings[`${proc}_model`]}
                                        onChange={(e) => onUpdate(`${proc}_model`, (e.target as HTMLSelectElement).value)}
                                    >
                                        {procChoices.models.map((m) => (
                                            <SelectItem key={m} value={m}>
                                                {m}
                                            </SelectItem>
                                        ))}
                                    </Select>
                                </div>
                            )}

                            {/* Pixel Boost (Dependent on Face Swapper Model) */}
                            {proc === 'face_swapper' && procChoices.set && (
                                <div className="space-y-2">
                                    <Label className="text-xs text-neutral-400">Pixel Boost</Label>
                                    <Select
                                        value={currentSettings[`face_swapper_pixel_boost`]}
                                        onChange={(e) => onUpdate(`face_swapper_pixel_boost`, (e.target as HTMLSelectElement).value)}
                                    >
                                        {(procChoices.set[currentSettings['face_swapper_model']] || []).map((pb) => (
                                            <SelectItem key={pb} value={pb}>
                                                {pb}
                                            </SelectItem>
                                        ))}
                                    </Select>
                                </div>
                            )}

                            {/* Weight Slider */}
                            {procChoices.weight_range && (
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <Label className="text-xs text-neutral-400">Weight</Label>
                                        <span className="text-[10px] text-neutral-500 font-mono">
                                            {currentSettings[`${proc}_weight`]?.toFixed(2)}
                                        </span>
                                    </div>
                                    <Slider
                                        value={[currentSettings[`${proc}_weight`]]}
                                        min={Math.min(...procChoices.weight_range)}
                                        max={Math.max(...procChoices.weight_range)}
                                        step={0.05}
                                        onValueChange={(val) => onUpdate(`${proc}_weight`, val[0])}
                                        className="py-1"
                                    />
                                </div>
                            )}

                            {/* Blend Slider */}
                            {procChoices.blend_range && (
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <Label className="text-xs text-neutral-400">Blend</Label>
                                        <span className="text-[10px] text-neutral-500 font-mono">
                                            {currentSettings[`${proc}_blend`]}%
                                        </span>
                                    </div>
                                    <Slider
                                        value={[currentSettings[`${proc}_blend`]]}
                                        min={Math.min(...procChoices.blend_range)}
                                        max={Math.max(...procChoices.blend_range)}
                                        step={1}
                                        onValueChange={(val) => onUpdate(`${proc}_blend`, val[0])}
                                        className="py-1"
                                    />
                                </div>
                            )}

                            {/* Direction Slider (Age Modifier) */}
                            {procChoices.direction_range && (
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <Label className="text-xs text-neutral-400">Direction</Label>
                                        <span className="text-[10px] text-neutral-500 font-mono">
                                            {currentSettings[`${proc}_direction`]}
                                        </span>
                                    </div>
                                    <Slider
                                        value={[currentSettings[`${proc}_direction`]]}
                                        min={Math.min(...procChoices.direction_range)}
                                        max={Math.max(...procChoices.direction_range)}
                                        step={1}
                                        onValueChange={(val) => onUpdate(`${proc}_direction`, val[0])}
                                        className="py-1"
                                    />
                                </div>
                            )}

                            {/* Factor Slider (Expression Restorer) */}
                            {procChoices.factor_range && (
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <Label className="text-xs text-neutral-400">Factor</Label>
                                        <span className="text-[10px] text-neutral-500 font-mono">
                                            {currentSettings[`${proc}_factor`]}%
                                        </span>
                                    </div>
                                    <Slider
                                        value={[currentSettings[`${proc}_factor`]]}
                                        min={Math.min(...procChoices.factor_range)}
                                        max={Math.max(...procChoices.factor_range)}
                                        step={1}
                                        onValueChange={(val) => onUpdate(`${proc}_factor`, val[0])}
                                        className="py-1"
                                    />
                                </div>
                            )}
                        </CardContent>
                    </Card>
                );
            })}
        </div>
    );
};

export default ProcessorSettings;

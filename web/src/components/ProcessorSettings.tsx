import React, { useEffect, useState } from 'react';
import { processors } from '@/services/api';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectItem } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Settings2, Info } from 'lucide-react';
import { Tooltip } from '@/components/ui/Tooltip';

interface ProcessorChoices {
    [key: string]: {
        models?: string[];
        set?: { [key: string]: string[] };
        weight_range?: number[];
        blend_range?: number[];
        direction_range?: number[];
        factor_range?: number[];
        areas?: string[];
        sizes?: string[];
        items?: string[];
        // Dynamic keys for other ranges
        [key: string]: any;
    };
}

interface ProcessorSettingsProps {
    activeProcessors: string[];
    currentSettings: any;
    onUpdate: (key: string, value: any) => void;
    helpTexts: Record<string, string>;
}

const ProcessorSettings: React.FC<ProcessorSettingsProps> = ({
    activeProcessors,
    currentSettings,
    onUpdate,
    helpTexts
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

                // Identify all range keys that are NOT weight or blend (handled separately)
                const rangeKeys = Object.keys(procChoices).filter(key =>
                    key.endsWith('_range') &&
                    !['weight_range', 'blend_range'].includes(key)
                );

                return (
                    <Card key={proc} className="bg-neutral-900/50 border-neutral-800 backdrop-blur-sm overflow-hidden">
                        <CardHeader className="py-2 px-3 border-b border-neutral-800 bg-neutral-900/30">
                            <CardTitle className="text-sm font-medium text-neutral-200 capitalize flex items-center gap-2">
                                {proc.replace(/_/g, ' ')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-3 space-y-3">
                            {/* Model Selection */}
                            {procChoices.models && (
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <Label className="text-xs text-neutral-400">Model</Label>
                                        <Tooltip content={helpTexts[`${proc}_model`]}>
                                            <Info size={12} className="text-neutral-500 cursor-help" />
                                        </Tooltip>
                                    </div>
                                    <Select
                                        value={currentSettings[`${proc}_model`]}
                                        onChange={(e: any) => onUpdate(`${proc}_model`, (e.target as HTMLSelectElement).value)}
                                    >
                                        {(() => {
                                            const modelHints: Record<string, string> = {
                                                "realesrgan": "Balanced • Quality",
                                                "esrgan": "High Detail",
                                                "swinir": "Premium • Slow",
                                                "lsdir": "Sharp • Modern",
                                                "clear_reality": "Clean • Recommended",
                                                "ultra_sharp": "Precision Sharp",
                                                "codeformer": "Best • Recommended",
                                                "gfpgan": "Fast • Natural",
                                                "restoreformer": "High Fidelity",
                                                "yolo": "Standard • Recommended",
                                                "scrfd": "Ultra Fast",
                                                "retinaface": "Maximum Precision",
                                                "inswapper": "Pro • Recommended",
                                                "simswap": "Fast Swapper"
                                            };

                                            const getHint = (name: string) => {
                                                const lower = name.toLowerCase();
                                                for (const [key, hint] of Object.entries(modelHints)) {
                                                    if (lower.includes(key)) return ` [${hint}]`;
                                                }
                                                return "";
                                            };

                                            const formatName = (name: string) => {
                                                const formatted = name
                                                    .replace(/_/g, ' ')
                                                    .replace(/\sfp16/i, '')
                                                    .replace(/\sx(\d+)/i, ' ($1x)')
                                                    .split(' ')
                                                    .map(w => w.length > 2 ? w.charAt(0).toUpperCase() + w.slice(1) : w.toUpperCase())
                                                    .join(' ');

                                                return formatted + getHint(name);
                                            };

                                            const groups: Record<string, string[]> = {
                                                "Upscalers": [],
                                                "Face Restore": [],
                                                "Detectors & Swappers": [],
                                                "Other": []
                                            };

                                            procChoices.models.forEach(m => {
                                                const lower = m.toLowerCase();
                                                if (lower.includes('esrgan') || lower.includes('swin') || lower.includes('dir') || lower.includes('sharp') || lower.includes('dat') || lower.includes('realistic') || lower.includes('nomos')) {
                                                    groups["Upscalers"].push(m);
                                                } else if (lower.includes('codeformer') || lower.includes('gfpgan') || lower.includes('restoreformer')) {
                                                    groups["Face Restore"].push(m);
                                                } else if (lower.includes('yolo') || lower.includes('scrfd') || lower.includes('inswapper') || lower.includes('simswap') || lower.includes('retina')) {
                                                    groups["Detectors & Swappers"].push(m);
                                                } else {
                                                    groups["Other"].push(m);
                                                }
                                            });

                                            return Object.entries(groups).map(([label, items]) => items.length > 0 && (
                                                <optgroup key={label} label={label} className="bg-neutral-900 text-neutral-500 font-bold text-[10px] uppercase tracking-wider">
                                                    {items.map(m => (
                                                        <option key={m} value={m} className="bg-neutral-950 text-neutral-200 normal-case font-normal text-xs">
                                                            {formatName(m)}
                                                        </option>
                                                    ))}
                                                </optgroup>
                                            ));
                                        })()}
                                    </Select>
                                </div>
                            )}

                            {/* Size Selection (e.g. Frame Colorizer) */}
                            {procChoices.sizes && (
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <Label className="text-xs text-neutral-400">Size</Label>
                                        <Tooltip content={helpTexts[`${proc}_size`]}>
                                            <Info size={12} className="text-neutral-500 cursor-help" />
                                        </Tooltip>
                                    </div>
                                    <Select
                                        value={currentSettings[`${proc}_size`]}
                                        onChange={(e: any) => onUpdate(`${proc}_size`, (e.target as HTMLSelectElement).value)}
                                    >
                                        {procChoices.sizes.map((s) => (
                                            <SelectItem key={s} value={s}>
                                                {s}
                                            </SelectItem>
                                        ))}
                                    </Select>
                                </div>
                            )}

                            {/* Set Selection (Pixel Boost) */}
                            {proc === 'face_swapper' && procChoices.set && (
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <Label className="text-xs text-neutral-400">Pixel Boost</Label>
                                        <Tooltip content={helpTexts[`face_swapper_pixel_boost`]}>
                                            <Info size={12} className="text-neutral-500 cursor-help" />
                                        </Tooltip>
                                    </div>
                                    <Select
                                        value={currentSettings[`face_swapper_pixel_boost`]}
                                        onChange={(e: any) => onUpdate(`face_swapper_pixel_boost`, (e.target as HTMLSelectElement).value)}
                                    >
                                        {(procChoices.set[currentSettings['face_swapper_model']] || []).map((pb) => (
                                            <SelectItem key={pb} value={pb}>
                                                {pb}
                                            </SelectItem>
                                        ))}
                                    </Select>
                                </div>
                            )}

                            {/* Watermark Remover Area Configuration */}
                            {proc === 'watermark_remover' && (
                                <div className="space-y-4 pt-2 border-t border-neutral-800/50">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <Label className="text-[10px] font-bold text-neutral-500 uppercase">Area Config</Label>
                                            <Tooltip content="Define the rectangular area for removal using coordinates (top-left and bottom-right).">
                                                <Info size={12} className="text-neutral-500 cursor-help" />
                                            </Tooltip>
                                        </div>
                                        <button
                                            onClick={() => {
                                                onUpdate('watermark_remover_area_start', [0, 0]);
                                                onUpdate('watermark_remover_area_end', [0, 0]);
                                            }}
                                            className="text-[10px] text-neutral-500 hover:text-white transition-colors"
                                        >
                                            Clear Area
                                        </button>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-2">
                                            <Label className="text-[10px] text-neutral-500 uppercase">Start (X, Y)</Label>
                                            <div className="flex gap-2">
                                                <input
                                                    type="number"
                                                    className="w-full bg-neutral-950 border border-neutral-800 rounded p-1.5 text-xs text-center focus:border-blue-500 outline-none transition-colors"
                                                    value={currentSettings['watermark_remover_area_start']?.[0] || 0}
                                                    onChange={(e) => {
                                                        const val = parseInt(e.target.value) || 0;
                                                        onUpdate('watermark_remover_area_start', [val, currentSettings['watermark_remover_area_start']?.[1] || 0])
                                                    }}
                                                />
                                                <input
                                                    type="number"
                                                    className="w-full bg-neutral-950 border border-neutral-800 rounded p-1.5 text-xs text-center focus:border-blue-500 outline-none transition-colors"
                                                    value={currentSettings['watermark_remover_area_start']?.[1] || 0}
                                                    onChange={(e) => {
                                                        const val = parseInt(e.target.value) || 0;
                                                        onUpdate('watermark_remover_area_start', [currentSettings['watermark_remover_area_start']?.[0] || 0, val])
                                                    }}
                                                />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label className="text-[10px] text-neutral-500 uppercase">End (X, Y)</Label>
                                            <div className="flex gap-2">
                                                <input
                                                    type="number"
                                                    className="w-full bg-neutral-950 border border-neutral-800 rounded p-1.5 text-xs text-center focus:border-blue-500 outline-none transition-colors"
                                                    value={currentSettings['watermark_remover_area_end']?.[0] || 0}
                                                    onChange={(e) => {
                                                        const val = parseInt(e.target.value) || 0;
                                                        onUpdate('watermark_remover_area_end', [val, currentSettings['watermark_remover_area_end']?.[1] || 0])
                                                    }}
                                                />
                                                <input
                                                    type="number"
                                                    className="w-full bg-neutral-950 border border-neutral-800 rounded p-1.5 text-xs text-center focus:border-blue-500 outline-none transition-colors"
                                                    value={currentSettings['watermark_remover_area_end']?.[1] || 0}
                                                    onChange={(e) => {
                                                        const val = parseInt(e.target.value) || 0;
                                                        onUpdate('watermark_remover_area_end', [currentSettings['watermark_remover_area_end']?.[0] || 0, val])
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Items Selection (e.g. Face Debugger) */}
                            {procChoices.items && (
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <Label className="text-xs text-neutral-400 mb-1">Items</Label>
                                        <Tooltip content={helpTexts[`${proc}_items`]}>
                                            <Info size={12} className="text-neutral-500 cursor-help" />
                                        </Tooltip>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2">
                                        {procChoices.items.map((item) => {
                                            const currentItems = currentSettings[`${proc}_items`] || [];
                                            const isSelected = currentItems.includes(item);
                                            return (
                                                <button
                                                    key={item}
                                                    onClick={() => {
                                                        const newItems = isSelected
                                                            ? currentItems.filter((i: string) => i !== item)
                                                            : [...currentItems, item];
                                                        onUpdate(`${proc}_items`, newItems);
                                                    }}
                                                    className={`px-2 py-1.5 text-[10px] rounded border text-center transition-all ${isSelected
                                                        ? "bg-blue-600/20 border-blue-500 text-blue-500 font-bold"
                                                        : "bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-600"
                                                        }`}
                                                >
                                                    {item}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                            {/* Dynamic Range Sliders (e.g. Face Editor specific ranges) */}
                            {rangeKeys.map(key => {
                                const settingName = key.replace('_range', ''); // e.g. 'head_pitch'
                                const fullSettingKey = `${proc}_${settingName}`; // e.g. 'face_editor_head_pitch'
                                const range = procChoices[key as keyof typeof procChoices] as number[];
                                const val = currentSettings[fullSettingKey];

                                // Skip if value is missing (backend sync issue)
                                if (val === undefined) return null;

                                return (
                                    <div key={key} className="space-y-3">
                                        <div className="flex justify-between items-center">
                                            <div className="flex items-center gap-2">
                                                <Label className="text-xs text-neutral-400 capitalize">
                                                    {settingName.replace(/_/g, ' ')}
                                                </Label>
                                                <Tooltip content={helpTexts[fullSettingKey]}>
                                                    <Info size={12} className="text-neutral-500 cursor-help" />
                                                </Tooltip>
                                            </div>
                                            <span className="text-[10px] text-neutral-500 font-mono">
                                                {typeof val === 'number' ? val.toFixed(2) : val}
                                            </span>
                                        </div>
                                        <Slider
                                            value={[val]}
                                            min={Math.min(...range)}
                                            max={Math.max(...range)}
                                            step={0.05}
                                            onValueChange={(v) => onUpdate(fullSettingKey, v[0])}
                                            className="py-1"
                                        />
                                    </div>
                                );
                            })}

                            {/* Standard Weight Slider */}
                            {procChoices.weight_range && (
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <div className="flex items-center gap-2">
                                            <Label className="text-xs text-neutral-400">Weight</Label>
                                            <Tooltip content={helpTexts[`${proc}_weight`]}>
                                                <Info size={12} className="text-neutral-500 cursor-help" />
                                            </Tooltip>
                                        </div>
                                        <span className="text-[10px] text-neutral-500 font-mono">
                                            {currentSettings[`${proc}_weight`]?.toFixed(2)}
                                        </span>
                                    </div>
                                    <Slider
                                        value={[currentSettings[`${proc}_weight`]]}
                                        min={Math.min(...procChoices.weight_range)}
                                        max={Math.max(...procChoices.weight_range)}
                                        step={0.05}
                                        onValueChange={(val: any) => onUpdate(`${proc}_weight`, val[0])}
                                        className="py-1"
                                    />
                                </div>
                            )}

                            {/* Standard Blend Slider */}
                            {procChoices.blend_range && (
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <div className="flex items-center gap-2">
                                            <Label className="text-xs text-neutral-400">Blend</Label>
                                            <Tooltip content={helpTexts[`${proc}_blend`]}>
                                                <Info size={12} className="text-neutral-500 cursor-help" />
                                            </Tooltip>
                                        </div>
                                        <span className="text-[10px] text-neutral-500 font-mono">
                                            {currentSettings[`${proc}_blend`]}%
                                        </span>
                                    </div>
                                    <Slider
                                        value={[currentSettings[`${proc}_blend`]]}
                                        min={Math.min(...procChoices.blend_range)}
                                        max={Math.max(...procChoices.blend_range)}
                                        step={1}
                                        onValueChange={(val: any) => onUpdate(`${proc}_blend`, val[0])}
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

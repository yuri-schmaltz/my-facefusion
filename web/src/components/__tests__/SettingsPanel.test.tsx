import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SettingsPanel } from '../SettingsPanel';
import { vi, describe, it, expect } from 'vitest';
import * as api from '@/services/api';

// Mock the API calls
vi.mock('@/services/api', () => ({
    config: {
        getSettings: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({}),
    },
}));

describe('SettingsPanel', () => {
    const mockSystemInfo = {
        execution_providers: ['cpu', 'cuda', 'openvino']
    };

    const mockHelpTexts = {
        'face_mask_types': 'Types of face mask',
        'execution_thread_count': 'Number of threads',
        'execution_providers': 'Execution providers'
    };

    it('renders critical sections correctly', async () => {
        render(<SettingsPanel systemInfo={mockSystemInfo} helpTexts={mockHelpTexts} />);

        // Check for section headers
        expect(screen.getByText('Media Settings')).toBeInTheDocument();
        expect(screen.getByText('JOBS')).toBeInTheDocument();

        // Check for specific inputs
        expect(screen.getByText('Face Selector Mode')).toBeInTheDocument();
        expect(screen.getByText('Execution Threads')).toBeInTheDocument();
    });



    it('triggers config update immediately on change (Auto-Save)', async () => {
        render(<SettingsPanel systemInfo={mockSystemInfo} helpTexts={mockHelpTexts} />);

        // Use the Face Selector Mode dropdown which is a combobox
        // We can use getByDisplayValue or just the role if it's the only select
        // There are other selects (Audio Encoder, Video Encoder), so let's be specific
        // We can find the label and then the select

        // Actually, let's just use getAllByRole('combobox') since we just need to test *any* update
        const selects = screen.getAllByRole('combobox');
        const faceSelector = selects[0]; // First one is Face Selector Mode

        // Change value to 'one'
        fireEvent.change(faceSelector, { target: { value: 'one' } });

        // Verify update was called
        await waitFor(() => {
            expect(api.config.update).toHaveBeenCalled();
            expect(api.config.update).toHaveBeenCalledWith(expect.objectContaining({
                face_selector_mode: 'one'
            }));
        });
    });
});

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SettingsPanel } from '../SettingsPanel';
import { ToastProvider } from '../ui/ToastContext';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import * as jobsApi from '@/services/api';

// Mock dependencies
vi.mock('@/services/api', () => ({
    jobs: {
        list: vi.fn().mockResolvedValue({ data: { jobs: [] } }),
        unqueue: vi.fn().mockResolvedValue({ data: {} }),
        submit: vi.fn().mockResolvedValue({ data: {} }),
        delete: vi.fn().mockResolvedValue({ data: {} }),
        run: vi.fn().mockResolvedValue({ data: { jobs_started: 1 } }),
        getDetails: vi.fn().mockResolvedValue({ data: {} }),
    }
}));

// Mock usePresets if we want to isolate it, but let's test integration with localStorage
// So no mock for usePresets, just clean localStorage

describe('Presets and Toasts', () => {
    const mockSettings = {
        execution_thread_count: 4,
        video_memory_strategy: 'strict'
    };
    const mockOnChange = vi.fn();
    const mockSystemInfo = { name: 'Test', version: '1.0', execution_providers: ['cpu'], execution_devices: [] };

    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
        // Default mock implementation for jobs
        (jobsApi.jobs.list as any).mockResolvedValue({
            data: {
                jobs: [
                    { id: 'job1', status: 'queued', step_count: 1 },
                    { id: 'job2', status: 'drafted', step_count: 1 }
                ]
            }
        });
    });

    const renderPanel = () => {
        return render(
            <ToastProvider>
                <SettingsPanel
                    settings={mockSettings}
                    choices={{}}
                    systemInfo={mockSystemInfo}
                    onChange={mockOnChange}
                    currentTargetPath="test.mp4"
                />
            </ToastProvider>
        );
    };

    it('Presets: can save and load a preset', async () => {
        renderPanel();

        // Navigate to System tab
        const systemTab = screen.getByText('System');
        fireEvent.click(systemTab);

        // Find Preset Input
        const input = screen.getByPlaceholderText(/Preset Name/i);
        const saveBtn = screen.getByText('Save', { selector: 'button' });

        // Save a preset
        fireEvent.change(input, { target: { value: 'My Super Preset' } });
        fireEvent.click(saveBtn);

        // Verify toast "saved" appears
        await waitFor(() => {
            expect(screen.getByText(/Preset "My Super Preset" saved!/i)).toBeInTheDocument();
        });

        // Verify it appears in the list
        expect(screen.getByText('My Super Preset')).toBeInTheDocument();

        // ----------------------------------------------------
        // Test Loading
        // ----------------------------------------------------
        // Find the load button (folder down icon)
        // Since we don't have aria-label easily, we query by title which we added
        const loadBtn = screen.getByTitle('Load Preset');
        fireEvent.click(loadBtn);

        // Verify onChange was called with saved settings
        // content of preset is mockSettings
        expect(mockOnChange).toHaveBeenCalled();
    });

    it('Presets: can delete a preset', async () => {
        // Pre-seed a preset
        localStorage.setItem('faceforge_presets', JSON.stringify([{
            id: '123',
            name: 'Old Preset',
            settings: mockSettings,
            timestamp: Date.now()
        }]));

        renderPanel();

        // Go to System tab
        fireEvent.click(screen.getByText('System'));

        // Verify it's there
        expect(screen.getByText('Old Preset')).toBeInTheDocument();

        // Delete it
        const deleteBtn = screen.getByTitle('Delete Preset');
        fireEvent.click(deleteBtn);

        // Verify toast
        await waitFor(() => {
            expect(screen.getByText(/Preset deleted/i)).toBeInTheDocument();
        });

        // Verify gone
        expect(screen.queryByText('Old Preset')).not.toBeInTheDocument();
    });

    it('Toasts: Job actions trigger toasts instead of alerts', async () => {
        renderPanel();

        // Go to Jobs tab
        fireEvent.click(screen.getByText('Jobs'));

        // Wait for jobs to load
        await waitFor(() => screen.findByText('job1'));

        // Select 'job1' (queued)
        // Clicking the job row toggles selection
        const jobRow = screen.getByText('job1').closest('div[class*="border"]');
        if (jobRow) fireEvent.click(jobRow);

        // Find 'Unqueue' button
        const unqueueBtn = screen.getByText(/Unqueue/i, { selector: 'button' });

        // Ensure not disabled
        expect(unqueueBtn).not.toBeDisabled();

        // Click Unqueue
        fireEvent.click(unqueueBtn);

        // Verify API called
        expect(jobsApi.jobs.unqueue).toHaveBeenCalled();

        // Verify Toast appears
        await waitFor(() => {
            expect(screen.getByText(/job\(s\) returned to drafted/i)).toBeInTheDocument();
        });

        // Ensure NO window.alert was called (we didn't mock it, but if it was called jsdom might log or we could spy on it.
        // But the main proof is the toast appearing).
    });
});

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FaceSelector from '../FaceSelector';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { api } from '@/services/api';

// Mock API
vi.mock('@/services/api', () => ({
    api: {
        post: vi.fn(),
    },
}));

describe('FaceSelector', () => {
    const mockFaces = [
        { index: 0, score: 0.95, gender: 'female', age: 25, race: 'white', thumbnail: 'thumb1.jpg' },
        { index: 1, score: 0.88, gender: 'male', age: 30, race: 'black', thumbnail: 'thumb2.jpg' }
    ];

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders nothing if no targetPath is provided', () => {
        const { container } = render(<FaceSelector targetPath={null} />);
        expect(container).toBeEmptyDOMElement();
    });

    it('fetches and displays faces on mount', async () => {
        (api.post as any).mockResolvedValue({ data: { faces: mockFaces } });

        render(<FaceSelector targetPath="/tmp/video.mp4" />);

        // Should show loading or directly the title
        expect(screen.getByText('Detected Faces')).toBeInTheDocument();

        // Wait for API call
        await waitFor(() => {
            expect(api.post).toHaveBeenCalledWith('/faces/detect', {
                path: '/tmp/video.mp4',
                time_seconds: 0
            });
        });

        // Check if faces are rendered
        expect(screen.getByAltText('Face 0')).toBeInTheDocument();
        expect(screen.getByAltText('Face 1')).toBeInTheDocument();
        expect(screen.getByText('#0')).toBeInTheDocument();
    });

    it('handles scan button click', async () => {
        (api.post as any).mockResolvedValue({ data: { faces: mockFaces } });
        render(<FaceSelector targetPath="/tmp/video.mp4" currentTime={10} />);

        // Initial call
        await waitFor(() => expect(api.post).toHaveBeenCalledTimes(1));

        // Click scan
        const scanButton = screen.getByTitle('Scan current frame');
        fireEvent.click(scanButton);

        // Verify call with new time
        await waitFor(() => {
            expect(api.post).toHaveBeenCalledTimes(2);
            expect(api.post).toHaveBeenCalledWith('/faces/detect', {
                path: '/tmp/video.mp4',
                time_seconds: 10
            });
        });
    });

    it('calls onSelect when a face is clicked', async () => {
        (api.post as any).mockResolvedValue({ data: { faces: mockFaces } });
        const onSelect = vi.fn();

        render(<FaceSelector targetPath="/tmp/video.mp4" onSelect={onSelect} />);

        await waitFor(() => screen.getByAltText('Face 0'));

        fireEvent.click(screen.getByAltText('Face 0'));
        expect(onSelect).toHaveBeenCalledWith(0);
    });

    it('shows empty message when no faces found', async () => {
        (api.post as any).mockResolvedValue({ data: { faces: [] } });

        render(<FaceSelector targetPath="/tmp/video.mp4" />);

        await waitFor(() => {
            expect(screen.getByText('No faces found')).toBeInTheDocument();
        });
    });
});

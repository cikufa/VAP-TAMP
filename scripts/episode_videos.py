"""Encode captured observations; video playback rate is not simulation time."""
from pathlib import Path


def encode_videos(root):
    import cv2
    videos = []
    for folder in sorted(Path(root).rglob('third_person')):
        for view in (folder, folder.parent / 'first_person'):
            frames = sorted(view.glob('*.png'), key=lambda path: int(path.stem))
            if not frames:
                continue
            first = cv2.imread(str(frames[0]))
            if first is None:
                raise ValueError('Unreadable video frame')
            path = view.parent / (view.name + '.mp4')
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), 12, first.shape[1::-1])
            if not writer.isOpened():
                raise RuntimeError('Video writer could not open')
            try:
                for frame in frames:
                    pixels = cv2.imread(str(frame))
                    if pixels is None or pixels.shape != first.shape:
                        raise ValueError('Inconsistent video frames')
                    writer.write(pixels)
            finally:
                writer.release()
            reader = cv2.VideoCapture(str(path))
            decoded = 0
            while reader.read()[0]:
                decoded += 1
            reader.release()
            if decoded != len(frames):
                raise RuntimeError('Encoded video did not decode all frames')
            videos.append(dict(path=str(path), frames=decoded, playback_fps=12,
                               timing='observation sequence; event log holds simulation timestamps'))
    return videos

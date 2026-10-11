"""Vision adapters. Everything outside this module uses normalized Detection values."""
from dataclasses import dataclass
from typing import Protocol, Any
import math

CLASSES = frozenset({'bottle', 'cup', 'laptop', 'keyboard', 'mouse', 'cell phone', 'book', 'cat', 'dog'})

@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]  # normalized x1, y1, x2, y2

    def __post_init__(self):
        x1, y1, x2, y2 = self.bbox
        if not all(math.isfinite(v) for v in (*self.bbox, self.confidence)):
            raise ValueError('Detection values must be finite')
        if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1 and 0 <= self.confidence <= 1):
            raise ValueError('Detection requires a normalized valid box and confidence')

    @property
    def center(self):
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

class VisionBackend(Protocol):
    def detect(self, frame: Any) -> list[Detection]: ...

class YoloBackend:
    def __init__(self, model='yolo11n.pt', confidence=0.35, device='cpu', image_size=640):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError('Webcam mode needs dependencies: pip install -r requirements.txt') from exc
        self.model = YOLO(model)
        self.confidence, self.device, self.image_size = confidence, device, image_size

    def detect(self, frame):
        result = self.model.predict(frame, conf=self.confidence, device=self.device,
                                    imgsz=self.image_size, verbose=False)[0]
        if result.boxes is None:
            return []
        boxes = result.boxes.xyxyn.cpu().tolist()
        labels = result.boxes.cls.cpu().tolist()
        scores = result.boxes.conf.cpu().tolist()
        detections = []
        for box, label, score in zip(boxes, labels, scores):
            name = result.names[int(label)]
            if name not in CLASSES:
                continue
            box = tuple(max(0.0, min(1.0, float(v))) for v in box)
            if box[2] > box[0] and box[3] > box[1]:
                detections.append(Detection(name, float(score), box))
        return detections

class HailoBackend:
    """Deployment seam only; no UGen300/HailoRT inference is implemented or claimed."""
    def __init__(self, *args, **kwargs):
        raise NotImplementedError('Requires UGen300 hardware, HailoRT, a compatible HEF, and validated preprocessing/postprocessing. See docs/architecture.md.')
    def detect(self, frame):
        raise NotImplementedError

class DemoBackend:
    """Scripted detections, explicitly simulation; a 40-second repeating scenario."""
    def detect(self, frame):
        t = float(frame) % 40
        items = [Detection('laptop', .96, (.35, .12, .67, .42)),
                 Detection('keyboard', .94, (.32, .49, .68, .61))]
        # Deliberate single-frame misses exercise debouncing.
        if int(float(frame) * 5) % 37 != 11:
            x = .12 if t < 10 or t >= 32 else .72
            if t < 20 or t >= 27:
                items.append(Detection('bottle', .92, (x, .38, x + .08, .65)))
        if t < 16 or t >= 30:
            items.append(Detection('cell phone', .90, (.77, .72, .88, .86)))
        if 5 <= t < 12:
            items.append(Detection('cat', .91, (.42, .65, .61, .92)))
        return items

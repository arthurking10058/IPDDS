from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

import cv2
import numpy as np

from .constants import WEIGHTS_FILE

_MODEL_LOCK = Lock()


@dataclass
class DetectionRecord:
    type: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int


def load_model():
    """Load and warm up the YOLO model."""
    if not WEIGHTS_FILE.exists():
        raise FileNotFoundError(f"模型文件不存在: {WEIGHTS_FILE}")

    try:
        from ultralytics import YOLO
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("缺少 ultralytics 依赖，请先安装 requirements.txt 中的依赖。") from exc

    with _MODEL_LOCK:
        model = YOLO(str(WEIGHTS_FILE))
        model.predict(np.zeros((160, 160, 3), dtype=np.uint8), verbose=False)
    return model


def predict_single_image(model, image_rgb: np.ndarray):
    """Run detection on a single RGB image and return the annotated image and records."""
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    results = model(image_bgr)
    annotated = image_rgb.copy()
    records: list[DetectionRecord] = []

    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        confidence = float(box.conf.item())
        class_id = int(box.cls.item())
        class_name = model.names[class_id]

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{class_name} {confidence:.2f}"
        cv2.putText(
            annotated,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
        records.append(
            DetectionRecord(
                type=class_name,
                confidence=confidence,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
            )
        )

    return annotated, results, records

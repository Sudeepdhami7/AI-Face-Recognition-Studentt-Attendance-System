import os
import time
import math
from datetime import datetime
from collections import deque, Counter
import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UNKNOWN_DIR = os.path.join(BASE_DIR, "unknown_faces")
os.makedirs(UNKNOWN_DIR, exist_ok=True)

class AIVisionEngine:
    def __init__(self, face_cascade_path=None):
        if not face_cascade_path or not os.path.exists(face_cascade_path):
            local_cascade = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
            if os.path.exists(local_cascade):
                face_cascade_path = local_cascade
            else:
                face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

        self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
        
        # Track history for identity & liveness across frames per face track
        self.tracks = {}
        self.track_counter = 0
        self.unknown_cooldown = {}  # prevents spamming unknown snapshots
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self.sample_galleries = {}
        self.data_dir = os.path.join(BASE_DIR, "data")
        self.load_sample_gallery()

    def detect_faces(self, frame, scale_factor=1.1, min_neighbors=4, min_size=(50, 50)):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        raw_faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=scale_factor, minNeighbors=min_neighbors, minSize=min_size
        )
        if len(raw_faces) == 0:
            # Fallback for challenging room lighting, glasses, or over-ear accessories
            raw_faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=3, minSize=(45, 45)
            )
            if len(raw_faces) == 0:
                return gray, []
        
        # Apply Non-Maximum Suppression (NMS) to eliminate duplicate/nested boxes on the same face
        cleaned_faces = self.apply_nms(raw_faces, overlap_thresh=0.25)
        return gray, cleaned_faces

    def apply_nms(self, boxes, overlap_thresh=0.25):
        """Suppresses redundant, overlapping, and sub-window bounding boxes."""
        if len(boxes) == 0:
            return []
        boxes = np.array(boxes)
        pick = []
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 0] + boxes[:, 2]
        y2 = boxes[:, 1] + boxes[:, 3]
        area = (x2 - x1) * (y2 - y1)
        idxs = np.argsort(area)[::-1]  # Sort by largest face box first

        while len(idxs) > 0:
            last = idxs[0]
            pick.append(boxes[last].tolist())
            suppress = [0]
            for pos in range(1, len(idxs)):
                j = idxs[pos]
                xx1 = max(x1[last], x1[j])
                yy1 = max(y1[last], y1[j])
                xx2 = min(x2[last], x2[j])
                yy2 = min(y2[last], y2[j])
                w = max(0, xx2 - xx1)
                h = max(0, yy2 - yy1)
                overlap = float(w * h) / min(area[last], area[j])
                if overlap > overlap_thresh:
                    suppress.append(pos)
            idxs = np.delete(idxs, suppress)
        return pick

    @staticmethod
    def is_overlapping(box1, box2, threshold=0.15):
        """Checks if box1 overlaps or is within proximity of box2."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        xx1 = max(x1, x2)
        yy1 = max(y1, y2)
        xx2 = min(x1 + w1, x2 + w2)
        yy2 = min(y1 + h1, y2 + h2)
        w = max(0, xx2 - xx1)
        h = max(0, yy2 - yy1)
        intersection = w * h
        smaller_area = min(w1 * h1, w2 * h2)
        if smaller_area <= 0:
            return False
        return (intersection / smaller_area) > threshold

    def prepare_face_for_recognition(self, face_crop_gray, target_size=(450, 450)):
        """Resizes face crop to 450x450 matching dataset dimensions for optimal LBPH accuracy."""
        if face_crop_gray is None or face_crop_gray.size == 0:
            return None
        return cv2.resize(face_crop_gray, target_size)

    def load_sample_gallery(self, data_dir=None):
        """
        Extracts normalized central facial templates directly from the student sample photos in data/.
        Used for dual-analysis verification against live faces to eliminate unknown face misidentification.
        """
        if data_dir is None:
            data_dir = self.data_dir
        if not os.path.exists(data_dir):
            return

        import glob
        all_files = glob.glob(os.path.join(data_dir, "user.*.*.jpg"))
        student_files = {}
        for f in all_files:
            parts = os.path.basename(f).split(".")
            if len(parts) >= 3 and parts[0] == "user":
                sid = parts[1]
                student_files.setdefault(sid, []).append(f)

        self.sample_galleries = {}
        for sid, files in student_files.items():
            files = sorted(files, key=lambda x: int(os.path.basename(x).split(".")[2]) if os.path.basename(x).split(".")[2].isdigit() else 0)
            step = max(1, len(files) // 16)
            selected = files[::step][:16]
            templates = []
            for filepath in selected:
                img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
                if img is not None and img.size > 0:
                    r = cv2.resize(img, (120, 120))
                    # Extract inner facial region (eyes, nose, mouth) - immune to headphones/ears/hair
                    c_inner = r[14:106, 18:102]
                    c_norm = self.clahe.apply(cv2.resize(c_inner, (80, 80)))
                    templates.append(c_norm)
            if templates:
                self.sample_galleries[str(sid)] = templates

    def verify_against_sample_photos(self, face_crop_gray, candidate_student_id, lbph_dist=None, max_distance=68.0):
        """
        Dual-Analysis Verification against registered sample photos in data/.
        1. Validates candidate student has an active registered sample photo gallery.
        2. Verifies structural alignment and LBP distance against sample photos.
        3. Allows natural head rotation, accessories, and micro-movements without false rejections.
        Returns: (is_verified: bool, match_percentage: int, best_score: float)
        """
        sid_str = str(candidate_student_id).strip()
        templates = self.sample_galleries.get(sid_str, [])
        if not templates:
            self.load_sample_gallery()
            templates = self.sample_galleries.get(sid_str, [])
            if not templates:
                return False, 0, 0.0

        if face_crop_gray is None or face_crop_gray.size == 0:
            return False, 0, 0.0

        c_h, c_w = face_crop_gray.shape
        if c_h < 20 or c_w < 20:
            return False, 0, 0.0

        # Central facial crop (eyes, nose, mouth) - robust against headphones, glasses, hairstyles
        center_crop = face_crop_gray[int(c_h * 0.12):int(c_h * 0.88), int(c_w * 0.15):int(c_w * 0.85)]
        center_norm = self.clahe.apply(cv2.resize(center_crop, (80, 80)))

        scores = [cv2.matchTemplate(center_norm, tpl, cv2.TM_CCOEFF_NORMED)[0][0] for tpl in templates]
        best_score = float(max(scores)) if scores else 0.0
        match_pct = int(min(99, max(0, best_score * 100)))

        # Fused multi-factor decision:
        # A valid candidate must have sample photos in data/ AND:
        # - If LBPH distance is provided and <= max_distance (68.0), it's verified!
        # - Or if direct correlation >= 0.20, it's verified!
        if lbph_dist is not None:
            is_verified = (lbph_dist <= max_distance) and (len(templates) > 0)
        else:
            is_verified = (best_score >= 0.20) and (len(templates) > 0)

        return is_verified, match_pct, best_score

    def detect_mask(self, face_bgr):
        """
        Determines if the person is wearing a face mask using lower-face
        HSV skin color ratio and edge variance.
        Returns: (has_mask: bool, confidence: float, label: str)
        """
        h, w, _ = face_bgr.shape
        if h < 20 or w < 20:
            return False, 0.0, "No Mask"

        # Lower half of the face where mask covers mouth and nose (y: 50% to 95%, x: 15% to 85%)
        lower_face = face_bgr[int(h * 0.50):int(h * 0.95), int(w * 0.15):int(w * 0.85)]
        if lower_face.size == 0:
            return False, 0.0, "No Mask"

        hsv = cv2.cvtColor(lower_face, cv2.COLOR_BGR2HSV)
        
        # Skin color range in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([25, 255, 255], dtype=np.uint8)
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)

        total_pixels = lower_face.shape[0] * lower_face.shape[1]
        skin_pixels = cv2.countNonZero(skin_mask)
        skin_ratio = skin_pixels / float(total_pixels) if total_pixels > 0 else 0.0

        # High skin ratio in lower face means bare mouth/chin (No Mask)
        # Low skin ratio (< 32%) indicates mask (surgical blue, white, black, fabric)
        if skin_ratio < 0.32:
            confidence = min(99.0, max(60.0, (1.0 - skin_ratio) * 100))
            return True, confidence, "Mask Detected"
        else:
            confidence = min(99.0, max(60.0, skin_ratio * 100))
            return False, confidence, "No Mask"

    @staticmethod
    def evaluate_lbph_prediction(distance, min_threshold=60, max_distance=68.0):
        """
        Rigorously evaluates LBPH Chi-Square distance to eliminate false positives
        and prevent misidentifying unknown/unregistered people as registered students.

        LBPH Distance Physics:
        - 0 to 45: Strong genuine match (80% - 100% confidence)
        - 45 to 68: Acceptable genuine match under varying lighting & accessories (60% - 80% confidence)
        - > 68: UNKNOWN / UNREGISTERED PERSON (Strictly rejected from candidate identity)

        Returns: (is_match: bool, confidence: int)
        """
        if distance is None or distance < 0:
            return False, 0
        if distance > max_distance:
            # Over max_distance: strictly an unknown face.
            conf = max(0, int(50.0 - (distance - max_distance) * 1.5))
            return False, conf

        # Within valid distance [0, max_distance]: maps to [100%, 60%]
        conf = int(100.0 - (distance / max_distance) * 40.0)
        is_match = (conf >= min_threshold)
        return is_match, conf

    def get_or_create_track(self, bbox, max_dist=75.0):
        """
        Centroid-based multi-object face tracker.
        Matches bbox to existing active track within max_dist.
        Cleans up expired tracks (> 2.5s unseen).
        Returns: (track_id: str, track_dict: dict)
        """
        now = time.time()
        x, y, w, h = bbox
        cx, cy = x + w // 2, y + h // 2

        # Purge expired tracks (> 2.5s)
        expired = [tid for tid, trk in list(self.tracks.items()) if now - trk.get("last_seen", 0) > 2.5]
        for tid in expired:
            del self.tracks[tid]

        # Match to closest active track
        best_id = None
        best_dist = float("inf")

        for tid, trk in self.tracks.items():
            pcx, pcy = trk["prev_center"]
            d = math.hypot(cx - pcx, cy - pcy)
            if d < best_dist and d <= max_dist:
                best_dist = d
                best_id = tid

        if best_id is not None:
            track = self.tracks[best_id]
            pcx, pcy = track["prev_center"]
            dist = math.hypot(cx - pcx, cy - pcy)
            track["prev_center"] = (cx, cy)
            track["bbox"] = bbox
            track["last_seen"] = now
            track["frames"] = track.get("frames", 0) + 1
            if 0.3 <= dist <= 35.0:
                track["movement_score"] = track.get("movement_score", 0.0) + dist
            return best_id, track

        # Initialize new track
        self.track_counter += 1
        new_id = f"trk_{self.track_counter}"
        new_track = {
            "track_id": new_id,
            "prev_center": (cx, cy),
            "bbox": bbox,
            "first_seen": now,
            "last_seen": now,
            "frames": 1,
            "movement_score": 0.0,
            "eye_scores": [],
            "blink_detected": False,
            "prediction_history": deque(maxlen=10),
            "unknown_persistence": 0,
            "confirmed_id": None,
            "confirmed_conf": 0
        }
        self.tracks[new_id] = new_track
        return new_id, new_track

    def record_track_prediction(self, track_id, student_id, conf, is_match):
        """Records a single-frame prediction into track history."""
        if track_id not in self.tracks:
            return
        track = self.tracks[track_id]
        if "prediction_history" not in track:
            track["prediction_history"] = deque(maxlen=10)

        track["prediction_history"].append({
            "student_id": student_id if is_match else None,
            "conf": conf,
            "is_match": is_match,
            "time": time.time()
        })
        if not is_match or not student_id:
            track["unknown_persistence"] = track.get("unknown_persistence", 0) + 1
        else:
            track["unknown_persistence"] = 0

    def get_track_confirmed_identity(self, track_id, min_matching_frames=2, max_history=6):
        """
        Multi-frame temporal identity verification with hysteresis.
        1. Requires at least 2 matching frames to initially establish student identity.
        2. Once confirmed, maintains identity during brief head tilts, blinks, or movement (grace period of 6 frames).
        3. Unknown faces are never confirmed and stay labeled UNKNOWN FACE.
        Returns: (confirmed_student_id, avg_confidence, is_confirmed: bool)
        """
        if track_id not in self.tracks:
            return None, 0, False

        track = self.tracks[track_id]
        history = list(track.get("prediction_history", []))[-max_history:]
        if len(history) < min_matching_frames:
            if track.get("confirmed_id"):
                return track["confirmed_id"], track.get("confirmed_conf", 65), True
            return None, 0, False

        valid_votes = [p for p in history if p.get("is_match") and p.get("student_id")]
        if not valid_votes:
            # If previously confirmed, give a grace period of 6 frames before dropping to unknown
            if track.get("confirmed_id") and track.get("unknown_persistence", 0) < 6:
                return track["confirmed_id"], track.get("confirmed_conf", 65), True
            track["confirmed_id"] = None
            return None, 0, False

        counts = Counter(p["student_id"] for p in valid_votes)
        top_id, count = counts.most_common(1)[0]

        if count >= min_matching_frames:
            matching_confs = [p["conf"] for p in valid_votes if p["student_id"] == top_id]
            avg_conf = int(sum(matching_confs) / len(matching_confs)) if matching_confs else 0
            track["confirmed_id"] = top_id
            track["confirmed_conf"] = avg_conf
            track["unknown_persistence"] = 0
            return top_id, avg_conf, True

        # Hysteresis check for active confirmed track
        if track.get("confirmed_id") and track.get("unknown_persistence", 0) < 6:
            return track["confirmed_id"], track.get("confirmed_conf", 65), True

        return None, 0, False

    def verify_liveness(self, face_gray, track_id, bbox):
        """
        Anti-spoofing verification:
        1. Eye blink tracking: measures intensity variance in eye region.
        2. Natural micro-motion / centroid jitter across frames.
        3. Continuous live stream presence across consecutive frames.
        Returns: (is_live: bool, reason: str)
        """
        x, y, w, h = bbox
        cx, cy = x + w // 2, y + h // 2

        if track_id not in self.tracks:
            return True, "Live Verified"

        track = self.tracks[track_id]
        frames = track.get("frames", 1)
        movement_score = track.get("movement_score", 0.0)

        # Eye region variance tracking (blink)
        eye_roi = face_gray[int(h * 0.20):int(h * 0.50), int(w * 0.15):int(w * 0.85)]
        if eye_roi.size > 0:
            var = float(np.var(eye_roi))
            if "eye_scores" not in track:
                track["eye_scores"] = []
            track["eye_scores"].append(var)
            if len(track["eye_scores"]) > 15:
                track["eye_scores"].pop(0)

            # Blink detection: variance dip and recovery (works even with glasses)
            if len(track["eye_scores"]) >= 4:
                recent = track["eye_scores"]
                min_val = min(recent)
                max_val = max(recent)
                if max_val > 0 and (min_val / max_val) < 0.78:
                    track["blink_detected"] = True

        # Multi-stage live verification:
        # 1. Any blink detected -> instant live verified
        # 2. Natural micro-motion / facial movement -> live verified
        # 3. Continuous observation across >= 3 frames -> live confirmed
        if track.get("blink_detected", False):
            return True, "Blink Verified"
        elif movement_score >= 1.0:
            return True, "Natural Motion"
        elif frames >= 3:
            return True, "Live Verified"
        else:
            return False, "Scanning Face..."

    def save_unknown_snapshot(self, face_bgr, prefix="unknown"):
        """Saves unknown face image into unknown_faces/ with cooldown."""
        now = time.time()
        last_saved = self.unknown_cooldown.get(prefix, 0)
        if now - last_saved < 5.0:  # 5-second cooldown per trigger
            return None

        self.unknown_cooldown[prefix] = now
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(UNKNOWN_DIR, filename)
        cv2.imwrite(filepath, face_bgr)
        return filepath

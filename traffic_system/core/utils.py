import cv2
import re
import os


def normalize_plate_number(value):
    if value is None:
        return ''
    return re.sub(r'[^A-Za-z0-9]', '', str(value)).upper()


def extract_plate_from_filename(filename):
    if not filename:
        return None

    stem = os.path.splitext(os.path.basename(filename))[0]
    if not stem:
        return None

    candidates = [
        r'([A-Z]{2,6}[-\s]?[A-Z0-9]{2,6}[-\s]?[A-Z0-9]{2,6})',
        r'([A-Z]{2,5}[0-9]{2,6})',
        r'([A-Z0-9]{2,5}[-\s][A-Z0-9]{2,6})',
    ]

    for pattern in candidates:
        match = re.search(pattern, stem.upper())
        if match:
            return normalize_plate_number(match.group(1))

    return None


def process_image_for_plate(image_path):
    """
    Attempts to extract a license plate number from an image using OpenCV and OCR.
    Returns a tuple: (plate_string, confidence_score, status_message)
    """
    try:
        # 1. Check if file exists
        if not os.path.exists(image_path):
            return None, None, "FAILED: Image file not found."

        # 2. Read image with OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return None, None, "FAILED: Image file could not be read or is corrupt."

        # 3. Import OCR engine here to prevent startup crashes
        try:
            from rapidocr_onnxruntime import RapidOCR
            engine = RapidOCR()
        except ImportError:
            return None, None, "FAILED: OCR engine not installed or not found."
        except Exception as e:
            return None, None, f"FAILED: OCR engine initialization error - {str(e)}"

        # 4. Preprocessing: Convert to Grayscale and enhance contrast
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)

        # 5. Pass the enhanced numpy array to the OCR engine
        result, elapse = engine(enhanced)

        if result:
            plate_candidates = []
            for line in result:
                text = line[1]
                conf = line[2]
                
                # Clean text: remove spaces and special characters, keep alphanumeric
                clean_text = re.sub(r'[^A-Za-z0-9]', '', text).upper()
                
                # Heuristic: License plates are typically 4 to 10 characters long
                if 4 <= len(clean_text) <= 10:
                    plate_candidates.append((clean_text, conf))

            if plate_candidates:
                # Return the candidate with the highest confidence
                best_plate = max(plate_candidates, key=lambda x: x[1])
                return best_plate[0], best_plate[1], "SUCCESS"

        return None, None, "FAILED: No valid plate pattern detected in the image."

    except Exception as e:
        return None, None, f"FAILED: Processing error - {str(e)}"
import base64
import mimetypes


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def detect_mime_type(file_path: str) -> str:
    guessed_type, _ = mimetypes.guess_type(file_path)
    return guessed_type or "image/png"

# placeholder - specific uploaders are implemented as separate modules:
# uploaders/rutube.py, uploaders/youtube.py, etc.
# Each module should either expose:
#   - upload_video(video_path, title, description, tags, thumbnail)
# or
#   - class Uploader with method upload(...)
#
# Optionally provide requires_selenium() -> bool
__all__ = []

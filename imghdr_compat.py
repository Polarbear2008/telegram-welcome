"""Compatibility module for imghdr in Python 3.13+."""
import sys

# Only patch if we're on Python 3.13 or later
if sys.version_info >= (3, 13):
    import builtins
    
    def test_jpeg(h, f):
        """Test for JPEG data."""
        if h.startswith(b'\xff\xd8'):
            return 'jpeg'
    
    def test_png(h, f):
        """Test for PNG data."""
        if h.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
    
    def test_gif(h, f):
        """Test for GIF data."""
        if h.startswith(b'GIF89a') or h.startswith(b'GIF87a'):
            return 'gif'
    
    def test_webp(h, f):
        """Test for WebP data."""
        if h.startswith(b'RIFF') and len(h) >= 16 and h[8:16] == b'WEBPVP8':
            return 'webp'
    
    # Create a minimal imghdr module
    class ImghdrModule:
        """Minimal imghdr module implementation."""
        def __init__(self):
            self.tests = []
            # Add default tests
            self.test_jpeg = test_jpeg
            self.test_png = test_png
            self.test_gif = test_gif
            self.test_webp = test_webp
            self.tests = [
                (test_jpeg, None, None),
                (test_png, None, None),
                (test_gif, None, None),
                (test_webp, None, None),
            ]
        
        def test(self, h, f, test_func):
            """Test if the file data matches the given test function."""
            return test_func(h, f)
        
        def what(self, filename, h=None):
            """Determine the type of an image file."""
            if h is None:
                with open(filename, 'rb') as f:
                    h = f.read(32)
            
            for test_func, _, _ in self.tests:
                result = test_func(h, None)
                if result:
                    return result
            return None
    
    # Replace the imghdr module with our implementation
    import sys
    sys.modules['imghdr'] = ImghdrModule()
    
    # Also patch the builtins in case something tries to import it directly
    builtins.imghdr = ImghdrModule()

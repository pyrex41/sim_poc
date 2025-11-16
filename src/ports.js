// ports.js - JS interop for Elm file uploads and navigation
const app = Elm.Main.init({ node: document.getElementById('elm-app') });

// Request to read file from file input
if (app.ports.requestFileRead) {
  app.ports.requestFileRead.subscribe(function() {
    const fileInput = document.getElementById('media-upload');
    if (fileInput && fileInput.files && fileInput.files[0]) {
      const file = fileInput.files[0];
      const reader = new FileReader();
      reader.onload = function(e) {
        const base64 = e.target.result;  // Include data URL prefix for type detection
        app.ports.fileLoaded.send(base64);
      };
      reader.readAsDataURL(file);
    }
  });
}

// Legacy file upload port (if needed)
if (app.ports.fileSelected) {
  app.ports.fileSelected.subscribe(function(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      const base64 = e.target.result.split(',')[1];  // Remove data URL prefix
      app.ports.fileLoaded.send(base64);
    };
    reader.readAsDataURL(file);
  });
}

// Navigation port
if (app.ports.navigateTo) {
  app.ports.navigateTo.subscribe(function(route) {
    window.location.href = route;
  });
}

// API key port (set default for demo)
if (app.ports.setApiKey) {
  app.ports.setApiKey.send('test-key-123');  // Default for testing
}
# AI-Powered Physics Simulator

A sophisticated 3D physics simulation platform that uses cutting-edge AI to generate and refine physics scenes through natural language prompts. Built with Elm frontend and FastAPI backend, featuring real-time physics simulation powered by Rapier.js.

## 🚀 Features

### AI-Powered Scene Generation
- **Claude Sonnet 4.5**: Latest Anthropic AI model for intelligent scene creation
- **Natural Language Prompts**: Generate complex physics scenes from text descriptions
- **Scene Refinement**: Modify existing scenes with conversational AI
- **Context-Aware**: AI understands physics principles and realistic object interactions

### Real-Time 3D Physics Simulation
- **Rapier Physics Engine**: High-performance, WebAssembly-powered physics
- **Realistic Physics**: Gravity, collisions, friction, and restitution
- **Multiple Object Types**: Boxes, spheres, cylinders with customizable properties
- **Dynamic Interactions**: Objects interact naturally in real-time

### Interactive 3D Editor
- **Transform Controls**: Move, rotate, and scale objects with visual gizmos
- **Property Editing**: Adjust mass, friction, restitution, and visual properties
- **Object Selection**: Click to select objects with visual feedback
- **Real-Time Updates**: See physics changes instantly

### Advanced Features
- **Undo/Redo System**: Full history tracking with keyboard shortcuts
- **Local Storage**: Scenes persist across browser sessions
- **Keyboard Shortcuts**: Space (play/pause), G/R/S (transform modes), Ctrl+Z/Y (undo/redo)
- **Responsive UI**: Modern, clean interface optimized for physics simulation

## 🛠️ Technology Stack

### Frontend
- **Elm 0.19.1**: Functional programming language for reliable UIs
- **Three.js**: 3D graphics and rendering
- **Rapier.js**: WebAssembly physics engine
- **Vite**: Fast development server and build tool

### Backend
- **FastAPI**: High-performance Python web framework
- **OpenRouter API**: Access to Claude Sonnet 4.5 via OpenAI-compatible interface
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

### AI Integration
- **Claude Sonnet 4.5**: Anthropic's most advanced AI model
- **1M Token Context**: Massive context window for complex scene generation
- **OpenRouter**: Multi-provider AI routing with automatic fallbacks

## 📋 Prerequisites

- **Python 3.14+** with virtual environment support
- **Node.js 16+** and npm
- **OpenRouter API Key** (for AI scene generation)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd physics-simulator
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
# In a separate terminal
npm install
```

### 4. Environment Configuration
Create a `.env` file in the backend directory:
```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 5. Start the Application
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate
OPENROUTER_API_KEY=your_key python main.py

# Terminal 2: Frontend
npm run dev
```

### 6. Open in Browser
Navigate to `http://localhost:5173`

## 🎮 Usage Guide

### Generating Scenes
1. Enter a natural language prompt in the left panel
2. Click "Generate Scene" to create a new physics scene
3. Watch as AI creates realistic objects with proper physics properties

### Example Prompts
- "a red ball bouncing on a wooden table"
- "stack of colorful boxes with a sphere rolling between them"
- "pyramid of spheres on a ramp with a cube at the bottom"

### Editing Scenes
1. **Select Objects**: Click on objects in the 3D view
2. **Transform**: Use G (move), R (rotate), S (scale) keys
3. **Properties**: Adjust physics properties in the right panel
4. **Refine**: Use the "Refine Scene" feature to modify with AI

### Physics Controls
- **Play/Pause**: Spacebar or play button
- **Reset**: Reload the page to reset the scene
- **Undo/Redo**: Ctrl+Z / Ctrl+Y

## 🔧 API Reference

### Backend Endpoints

#### Generate Scene
```http
POST /api/generate
Content-Type: application/json

{
  "prompt": "a bouncing ball and a wooden box"
}
```

#### Refine Scene
```http
POST /api/refine
Content-Type: application/json

{
  "scene": {...},
  "prompt": "make the ball blue"
}
```

### Scene Format
```json
{
  "objects": {
    "object_id": {
      "id": "object_id",
      "transform": {
        "position": {"x": 0.0, "y": 5.0, "z": 0.0},
        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
        "scale": {"x": 1.0, "y": 1.0, "z": 1.0}
      },
      "physicsProperties": {
        "mass": 1.0,
        "friction": 0.5,
        "restitution": 0.3
      },
      "visualProperties": {
        "color": "#ff0000",
        "shape": "Box"
      }
    }
  },
  "selectedObject": null
}
```

## 🏗️ Architecture

### Frontend Architecture (Elm)
```
Main.elm
├── Model: Scene, UI state, simulation state
├── Update: Message handling and state transitions
├── View: Three-panel layout with canvas integration
└── Ports: Communication with JavaScript/Three.js
```

### Backend Architecture (FastAPI)
```
main.py
├── AI Client: OpenRouter integration with Claude Sonnet 4.5
├── Scene Generation: AI-powered scene creation
├── Scene Refinement: Conversational scene modification
└── API Endpoints: RESTful physics scene management
```

### Physics Integration
```
PhysicsRenderer.js (Three.js + Rapier)
├── Scene Management: Object creation and updates
├── Physics Simulation: Real-time physics calculations
├── Transform Controls: Interactive object manipulation
└── Rendering: WebGL-accelerated 3D graphics
```

## 🔒 Security & Privacy

- **API Key Security**: OpenRouter API key stored server-side only
- **No Data Persistence**: Scenes exist only in browser memory
- **Local Storage**: Optional scene saving in browser localStorage
- **CORS Protection**: Configured for localhost development

## 🚀 Deployment

### Development
```bash
# Backend
cd backend && source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
npm run dev -- --host 0.0.0.0
```

### Production Build
```bash
# Frontend
npm run build

# Backend (using gunicorn)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit changes: `git commit -am 'Add feature'`
5. Push to branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Anthropic**: For Claude Sonnet 4.5 AI model
- **OpenRouter**: For AI model access and routing
- **Rapier Physics**: For high-performance WebAssembly physics
- **Three.js**: For 3D graphics and WebGL rendering
- **Elm**: For reliable functional programming frontend

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Check the troubleshooting section below

## 🔧 Troubleshooting

### Common Issues

**Backend won't start:**
- Ensure Python virtual environment is activated
- Check OPENROUTER_API_KEY environment variable
- Verify all dependencies are installed: `pip install -r requirements.txt`

**Frontend compilation errors:**
- Run `npm install` to ensure all dependencies
- Check Elm version: `elm --version` (should be 0.19.1)
- Clear Elm cache: `rm -rf elm-stuff && elm install`

**Physics not working:**
- Check browser console for WebAssembly errors
- Ensure modern browser with WebGL support
- Try refreshing the page

**AI generation fails:**
- Verify OpenRouter API key is valid
- Check API quota and billing status
- Ensure internet connection for API calls

### Development Tips

- Use browser developer tools to inspect 3D scene
- Check browser console for Elm runtime errors
- Monitor network tab for API request/response
- Use browser localStorage inspector for saved scenes

---

**Built with ❤️ using cutting-edge AI and modern web technologies**
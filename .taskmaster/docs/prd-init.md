# Product Requirements Document: PhysicsPlayground

**Version:** 1.0  
**Last Updated:** November 12, 2025  
**Status:** Updated

---

## 1. Core Concept

**PhysicsPlayground** enables rapid iteration on physics simulations:
1. User describes scene in natural language
2. System generates validated 3D physics scene (<10s)
3. User manipulates objects visually (drag, rotate, scale)
4. User simulates, observes, resets
5. User refines via text or manual edits
6. Repeat instantly

**Goal:** Collapse "idea → working physics" from 30 minutes to 30 seconds.

---

## 2. User Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    PRIMARY WORKFLOW                          │
└─────────────────────────────────────────────────────────────┘

1. TEXT INPUT
   User: "Stack 3 red boxes with a blue sphere on top"
   ↓
2. AI GENERATION (3-8s)
   Claude → Structured JSON → Genesis validation
   ↓
3. SCENE RENDER
   Three.js displays scene, objects selectable
   ↓
4. MANUAL ADJUSTMENT
   - Click box → Drag to new position
   - Press 'R' → Rotate handle appears
   - Press 'S' → Scale handle appears
   - Edit properties panel (mass, friction, etc.)
   ↓
5. SIMULATE
   Press Space → Rapier physics runs at 60 FPS
   ↓
6. ITERATE
   Option A: Reset → Adjust → Simulate again
   Option B: Type refinement: "Make boxes heavier"
   ↓
   Loop back to step 4 or 2
```

---

## 3. Technical Architecture

### 3.1 System Diagram

```
┌───────────────────── BROWSER ─────────────────────────┐
│                                                        │
│  ┌──────────────────────────────────────┐            │
│  │         Elm Application              │            │
│  │  - Pure state management             │            │
│  │  - UI rendering (HTML)               │            │
│  │  - Business logic                    │            │
│  └────┬─────────────────────────────┬───┘            │
│       │ Ports                       │ Ports          │
│       ▼                             ▼                │
│  ┌─────────────┐         ┌──────────────────┐       │
│  │ Three.js    │◀───────▶│ Rapier Physics   │       │
│  │ (WebGL)     │         │ (WASM)           │       │
│  │             │         │                  │       │
│  │ - Rendering │         │ - Simulation     │       │
│  │ - Transform │         │ - Collision      │       │
│  │   Controls  │         │ - Forces         │       │
│  └─────────────┘         └──────────────────┘       │
│       │                             │                │
│       └─────────────┬───────────────┘                │
│                     │ Events                         │
│                     ▼                                │
│         Browser APIs (IndexedDB, LocalStorage)       │
│                                                        │
└────────────────────┬───────────────────────────────────┘
                     │ HTTP/JSON
┌────────────────────▼───────────────────────────────────┐
│                   BACKEND SERVER                        │
│                                                         │
│  ┌─────────────────────────────────────────────┐      │
│  │         FastAPI / Axum Server               │      │
│  │                                             │      │
│  │  POST /api/generate                         │      │
│  │  POST /api/refine                           │      │
│  │  POST /api/validate                         │      │
│  └─────────────────────────────────────────────┘      │
│         │                │                │            │
│         ▼                ▼                ▼            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │ Claude   │    │ Genesis  │    │ LMDB     │        │
│  │ API      │    │ Validator│    │ Cache    │        │
│  └──────────┘    └──────────┘    └──────────┘        │
│                                                         │
│                          ┌──────────┐                  │
│                          │ SQLite   │                  │
│                          │ (scenes) │                  │
│                          └──────────┘                  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Frontend Architecture (Elm + Three.js)

**Philosophy:**
- **Elm owns state** - all application logic, no mutation
- **Three.js owns rendering** - via ports, treated as side effect
- **Clear boundary** - Elm sends commands, receives events

#### Elm Application Structure

```elm
-- src/Main.elm

module Main exposing (main)

import Browser
import Json.Decode as Decode
import Json.Encode as Encode

-- MODEL

type alias Model =
    { scene : Scene
    , uiState : UiState
    , simulationState : SimulationState
    }

type alias Scene =
    { objects : Dict ObjectId PhysicsObject
    , environment : Environment
    }

type alias PhysicsObject =
    { id : ObjectId
    , objectType : ObjectType
    , transform : Transform
    , physics : PhysicsProperties
    , visual : VisualProperties
    , selected : Bool
    }

type ObjectType
    = Box Vec3
    | Sphere Float
    | Cylinder Float Float
    | Capsule Float Float

type alias Transform =
    { position : Vec3
    , rotation : Quaternion  -- (x, y, z, w)
    , scale : Vec3
    }

type alias PhysicsProperties =
    { bodyType : BodyType
    , mass : Float
    , friction : Float
    , restitution : Float
    , linearVelocity : Vec3
    , angularVelocity : Vec3
    }

type BodyType
    = Dynamic
    | Static
    | Kinematic

type alias UiState =
    { textInput : String
    , selectedObjectId : Maybe ObjectId
    , transformMode : TransformMode
    , isGenerating : Bool
    , isPanelOpen : Bool
    }

type TransformMode
    = Translate
    | Rotate
    | Scale

type alias SimulationState =
    { isRunning : Bool
    , initialStates : Dict ObjectId Transform
    , currentFrame : Int
    }

-- UPDATE

type Msg
    = -- Text Input & Generation
      UpdateTextInput String
    | GenerateScene
    | SceneGenerated (Result Http.Error Scene)
    | RefineScene String
    | SceneRefined (Result Http.Error Scene)
    
    -- Object Selection & Manipulation
    | ObjectClicked ObjectId
    | ObjectTransformUpdated ObjectId Transform
    | DeselectAll
    
    -- Transform Controls
    | SetTransformMode TransformMode
    | ToggleTransformSpace  -- World vs Local
    
    -- Property Editing
    | UpdateObjectProperty ObjectId PropertyUpdate
    | ApplyPreset ObjectId Preset
    
    -- Simulation Control
    | ToggleSimulation
    | ResetSimulation
    | StepSimulation Int  -- Frame delta from Rapier
    
    -- Keyboard/UI
    | KeyPressed Key
    | TogglePanel
    
    -- Ports (from JS)
    | ThreeJsEvent ThreeJsEventData

type PropertyUpdate
    = SetMass Float
    | SetFriction Float
    | SetRestitution Float
    | SetColor String
    | SetBodyType BodyType

type alias ThreeJsEventData =
    { eventType : String
    , objectId : Maybe ObjectId
    , transform : Maybe Transform
    , raycastHit : Maybe Vec3
    }

update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        UpdateTextInput text ->
            ( { model | uiState = updateTextInput text model.uiState }
            , Cmd.none
            )
        
        GenerateScene ->
            ( { model | uiState = setGenerating True model.uiState }
            , generateSceneRequest model.uiState.textInput
            )
        
        SceneGenerated (Ok scene) ->
            ( { model 
                | scene = scene
                , uiState = setGenerating False model.uiState
                , simulationState = initSimulationState scene
              }
            , Cmd.batch
                [ sendSceneToThreeJs scene
                , saveSceneToLocalStorage scene
                ]
            )
        
        ObjectClicked objectId ->
            let
                updatedScene = selectObject objectId model.scene
            in
            ( { model 
                | scene = updatedScene
                , uiState = setSelectedObject (Just objectId) model.uiState
              }
            , sendSelectionToThreeJs objectId
            )
        
        ObjectTransformUpdated objectId transform ->
            ( { model 
                | scene = updateObjectTransform objectId transform model.scene
              }
            , Cmd.none
            )
        
        SetTransformMode mode ->
            ( { model | uiState = setTransformMode mode model.uiState }
            , sendTransformModeToThreeJs mode
            )
        
        ToggleSimulation ->
            if model.simulationState.isRunning then
                ( { model | simulationState = pauseSimulation model.simulationState }
                , sendToPhysics (Encode.object [ ("command", Encode.string "pause") ])
                )
            else
                ( { model 
                    | simulationState = startSimulation model.simulationState model.scene
                  }
                , sendToPhysics (Encode.object [ ("command", Encode.string "start") ])
                )
        
        ResetSimulation ->
            let
                resetScene = restoreInitialStates model.scene model.simulationState.initialStates
            in
            ( { model 
                | scene = resetScene
                , simulationState = resetSimulationState model.simulationState
              }
            , Cmd.batch
                [ sendToPhysics (Encode.object [ ("command", Encode.string "reset") ])
                , sendSceneToThreeJs resetScene
                ]
            )
        
        StepSimulation frameDelta ->
            -- Physics engine has updated, sync state back to Elm
            ( model, Cmd.none )
        
        ThreeJsEvent eventData ->
            -- Handle events from Three.js (clicks, drags, etc)
            handleThreeJsEvent eventData model
        
        KeyPressed key ->
            handleKeyPress key model
        
        _ ->
            ( model, Cmd.none )

-- VIEW

view : Model -> Html Msg
view model =
    div [ class "app-container" ]
        [ viewHeader
        , div [ class "main-content" ]
            [ viewLeftPanel model
            , viewCanvas  -- Just a placeholder div, Three.js renders here
            , viewRightPanel model
            ]
        , viewBottomBar model
        ]

viewLeftPanel : Model -> Html Msg
viewLeftPanel model =
    aside [ class "left-panel" ]
        [ h2 [] [ text "Generate Scene" ]
        , textarea
            [ placeholder "Describe your physics scene..."
            , value model.uiState.textInput
            , onInput UpdateTextInput
            ]
            []
        , button
            [ onClick GenerateScene
            , disabled model.uiState.isGenerating
            ]
            [ text (if model.uiState.isGenerating then "Generating..." else "Generate") ]
        , hr [] []
        , h2 [] [ text "Refine Scene" ]
        , textarea [ placeholder "Modify with text..." ] []
        , button [ onClick (RefineScene "") ] [ text "Refine" ]
        ]

viewRightPanel : Model -> Html Msg
viewRightPanel model =
    aside [ class "right-panel" ]
        [ h2 [] [ text "Properties" ]
        , case model.uiState.selectedObjectId of
            Just objectId ->
                case Dict.get objectId model.scene.objects of
                    Just obj ->
                        viewObjectProperties obj
                    Nothing ->
                        text "Object not found"
            Nothing ->
                text "No object selected"
        ]

viewObjectProperties : PhysicsObject -> Html Msg
viewObjectProperties obj =
    div [ class "properties-panel" ]
        [ section []
            [ h3 [] [ text "Transform" ]
            , viewVec3Input "Position" obj.transform.position
            , viewQuaternionInput "Rotation" obj.transform.rotation
            , viewVec3Input "Scale" obj.transform.scale
            ]
        , section []
            [ h3 [] [ text "Physics" ]
            , viewSlider "Mass" obj.physics.mass 0.01 1000 (UpdateObjectProperty obj.id << SetMass)
            , viewSlider "Friction" obj.physics.friction 0 2 (UpdateObjectProperty obj.id << SetFriction)
            , viewSlider "Restitution" obj.physics.restitution 0 1 (UpdateObjectProperty obj.id << SetRestitution)
            , viewBodyTypeSelect obj.physics.bodyType
            ]
        , section []
            [ h3 [] [ text "Visual" ]
            , viewColorPicker obj.visual.color
            , viewSlider "Metalness" obj.visual.metallic 0 1 identity
            , viewSlider "Roughness" obj.visual.roughness 0 1 identity
            ]
        ]

viewBottomBar : Model -> Html Msg
viewBottomBar model =
    footer [ class "bottom-bar" ]
        [ button [ onClick ToggleSimulation ]
            [ text (if model.simulationState.isRunning then "⏸ Pause" else "▶ Play") ]
        , button [ onClick ResetSimulation ] [ text "↻ Reset" ]
        , div [ class "stats" ]
            [ text ("Objects: " ++ String.fromInt (Dict.size model.scene.objects))
            , text " | "
            , text ("Frame: " ++ String.fromInt model.simulationState.currentFrame)
            ]
        ]

-- PORTS

port sendSceneToThreeJs : Encode.Value -> Cmd msg
port sendSelectionToThreeJs : String -> Cmd msg
port sendTransformModeToThreeJs : String -> Cmd msg
port sendToPhysics : Encode.Value -> Cmd msg

port receiveFromThreeJs : (Decode.Value -> msg) -> Sub msg
port receiveFromPhysics : (Decode.Value -> msg) -> Sub msg

-- SUBSCRIPTIONS

subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ receiveFromThreeJs (decodeThreeJsEvent >> ThreeJsEvent)
        , receiveFromPhysics (decodePhysicsUpdate >> StepSimulation)
        , Browser.Events.onKeyDown (Decode.map KeyPressed keyDecoder)
        ]

-- MAIN

main : Program () Model Msg
main =
    Browser.element
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }
```

#### JavaScript/Three.js Bridge

```javascript
// src/index.js (Vite entry point)

import { Elm } from './Main.elm'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { TransformControls } from 'three/examples/jsm/controls/TransformControls'
import RAPIER from '@dimforge/rapier3d-compat'

// Initialize Elm
const app = Elm.Main.init({
  node: document.getElementById('app'),
  flags: null
})

// Three.js setup
class PhysicsRenderer {
  constructor(containerId) {
    this.container = document.getElementById(containerId)
    this.scene = new THREE.Scene()
    this.objects = new Map() // objectId -> {mesh, body, collider}
    
    this.setupRenderer()
    this.setupCamera()
    this.setupControls()
    this.setupLights()
    this.setupPhysics()
    
    this.animate()
  }
  
  async setupPhysics() {
    await RAPIER.init()
    this.world = new RAPIER.World({ x: 0, y: -9.81, z: 0 })
    this.isSimulating = false
  }
  
  setupRenderer() {
    this.renderer = new THREE.WebGLRenderer({ antialias: true })
    this.renderer.setSize(window.innerWidth, window.innerHeight)
    this.renderer.shadowMap.enabled = true
    this.container.appendChild(this.renderer.domElement)
  }
  
  setupCamera() {
    this.camera = new THREE.PerspectiveCamera(
      75, 
      window.innerWidth / window.innerHeight, 
      0.1, 
      1000
    )
    this.camera.position.set(5, 5, 5)
  }
  
  setupControls() {
    this.orbitControls = new OrbitControls(this.camera, this.renderer.domElement)
    
    this.transformControls = new TransformControls(this.camera, this.renderer.domElement)
    this.transformControls.addEventListener('dragging-changed', (event) => {
      this.orbitControls.enabled = !event.value
    })
    
    this.transformControls.addEventListener('objectChange', () => {
      if (this.transformControls.object) {
        const obj = this.transformControls.object
        app.ports.receiveFromThreeJs.send({
          type: 'transformUpdate',
          objectId: obj.userData.id,
          position: obj.position.toArray(),
          rotation: obj.quaternion.toArray(),
          scale: obj.scale.toArray()
        })
      }
    })
    
    this.scene.add(this.transformControls)
    
    // Raycasting for selection
    this.raycaster = new THREE.Raycaster()
    this.mouse = new THREE.Vector2()
    
    this.renderer.domElement.addEventListener('click', (e) => {
      this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1
      this.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1
      
      this.raycaster.setFromCamera(this.mouse, this.camera)
      const intersects = this.raycaster.intersectObjects(
        Array.from(this.objects.values()).map(o => o.mesh)
      )
      
      if (intersects.length > 0) {
        const objectId = intersects[0].object.userData.id
        app.ports.receiveFromThreeJs.send({
          type: 'objectClicked',
          objectId: objectId
        })
      }
    })
  }
  
  setupLights() {
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    this.scene.add(ambientLight)
    
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
    dirLight.position.set(10, 20, 10)
    dirLight.castShadow = true
    this.scene.add(dirLight)
    
    // Ground
    const groundGeometry = new THREE.PlaneGeometry(100, 100)
    const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x808080 })
    const ground = new THREE.Mesh(groundGeometry, groundMaterial)
    ground.rotation.x = -Math.PI / 2
    ground.receiveShadow = true
    this.scene.add(ground)
    
    // Physics ground
    const groundBodyDesc = RAPIER.RigidBodyDesc.fixed()
    const groundBody = this.world.createRigidBody(groundBodyDesc)
    const groundColliderDesc = RAPIER.ColliderDesc.cuboid(50, 0.1, 50)
    this.world.createCollider(groundColliderDesc, groundBody)
  }
  
  loadScene(sceneData) {
    // Clear existing
    this.clearScene()
    
    // Add objects from Elm
    for (const obj of sceneData.objects) {
      this.addObject(obj)
    }
  }
  
  addObject(objDesc) {
    // Create Three.js mesh
    let geometry
    switch(objDesc.type) {
      case 'Box':
        geometry = new THREE.BoxGeometry(...objDesc.size)
        break
      case 'Sphere':
        geometry = new THREE.SphereGeometry(objDesc.radius, 32, 32)
        break
      case 'Cylinder':
        geometry = new THREE.CylinderGeometry(objDesc.radius, objDesc.radius, objDesc.height, 32)
        break
    }
    
    const material = new THREE.MeshStandardMaterial({
      color: objDesc.visual.color,
      metalness: objDesc.visual.metallic,
      roughness: objDesc.visual.roughness
    })
    
    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(...objDesc.transform.position)
    mesh.quaternion.set(...objDesc.transform.rotation)
    mesh.scale.set(...objDesc.transform.scale)
    mesh.castShadow = true
    mesh.receiveShadow = true
    mesh.userData.id = objDesc.id
    
    this.scene.add(mesh)
    
    // Create Rapier body
    const rigidBodyDesc = RAPIER.RigidBodyDesc.dynamic()
      .setTranslation(...objDesc.transform.position)
      .setRotation({
        w: objDesc.transform.rotation[3],
        x: objDesc.transform.rotation[0],
        y: objDesc.transform.rotation[1],
        z: objDesc.transform.rotation[2]
      })
    
    const body = this.world.createRigidBody(rigidBodyDesc)
    
    // Create collider
    let colliderDesc
    switch(objDesc.type) {
      case 'Box':
        colliderDesc = RAPIER.ColliderDesc.cuboid(
          objDesc.size[0] / 2,
          objDesc.size[1] / 2,
          objDesc.size[2] / 2
        )
        break
      case 'Sphere':
        colliderDesc = RAPIER.ColliderDesc.ball(objDesc.radius)
        break
    }
    
    colliderDesc
      .setMass(objDesc.physics.mass)
      .setRestitution(objDesc.physics.restitution)
      .setFriction(objDesc.physics.friction)
    
    const collider = this.world.createCollider(colliderDesc, body)
    
    this.objects.set(objDesc.id, { mesh, body, collider })
  }
  
  selectObject(objectId) {
    const obj = this.objects.get(objectId)
    if (obj) {
      this.transformControls.attach(obj.mesh)
    }
  }
  
  setTransformMode(mode) {
    const modeMap = {
      'Translate': 'translate',
      'Rotate': 'rotate',
      'Scale': 'scale'
    }
    this.transformControls.setMode(modeMap[mode])
  }
  
  startSimulation() {
    this.isSimulating = true
    this.transformControls.detach()
  }
  
  pauseSimulation() {
    this.isSimulating = false
  }
  
  resetSimulation() {
    this.isSimulating = false
    // Physics bodies will be reset by reloading scene from Elm
  }
  
  animate() {
    requestAnimationFrame(() => this.animate())
    
    if (this.isSimulating) {
      this.world.step()
      
      // Sync Three.js meshes with Rapier bodies
      for (const [id, obj] of this.objects) {
        const pos = obj.body.translation()
        const rot = obj.body.rotation()
        
        obj.mesh.position.set(pos.x, pos.y, pos.z)
        obj.mesh.quaternion.set(rot.x, rot.y, rot.z, rot.w)
      }
      
      // Send frame update to Elm
      app.ports.receiveFromPhysics.send({
        frame: this.currentFrame++
      })
    }
    
    this.orbitControls.update()
    this.renderer.render(this.scene, this.camera)
  }
  
  clearScene() {
    for (const [id, obj] of this.objects) {
      this.scene.remove(obj.mesh)
      this.world.removeRigidBody(obj.body)
    }
    this.objects.clear()
  }
}

// Initialize renderer
const renderer = new PhysicsRenderer('canvas-container')

// Connect Elm ports
app.ports.sendSceneToThreeJs.subscribe((sceneData) => {
  renderer.loadScene(sceneData)
})

app.ports.sendSelectionToThreeJs.subscribe((objectId) => {
  renderer.selectObject(objectId)
})

app.ports.sendTransformModeToThreeJs.subscribe((mode) => {
  renderer.setTransformMode(mode)
})

app.ports.sendToPhysics.subscribe((command) => {
  switch(command.command) {
    case 'start':
      renderer.startSimulation()
      break
    case 'pause':
      renderer.pauseSimulation()
      break
    case 'reset':
      renderer.resetSimulation()
      break
  }
})
```

#### Build Configuration (Vite)

```javascript
// vite.config.js

import { defineConfig } from 'vite'
import { plugin as elm } from 'vite-plugin-elm'

export default defineConfig({
  plugins: [
    elm({
      debug: true,
      optimize: process.env.NODE_ENV === 'production'
    })
  ],
  optimizeDeps: {
    exclude: ['@dimforge/rapier3d-compat']
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

```json
// package.json

{
  "name": "physics-playground",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "three": "^0.160.0",
    "@dimforge/rapier3d-compat": "^0.12.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "vite-plugin-elm": "^3.0.0",
    "elm": "^0.19.1"
  }
}
```

```html
<!-- index.html -->

<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PhysicsPlayground</title>
  <style>
    body { 
      margin: 0; 
      overflow: hidden; 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .app-container {
      display: flex;
      flex-direction: column;
      height: 100vh;
    }
    
    .main-content {
      display: flex;
      flex: 1;
      overflow: hidden;
    }
    
    .left-panel, .right-panel {
      width: 300px;
      background: #1e293b;
      color: #f1f5f9;
      padding: 20px;
      overflow-y: auto;
    }
    
    #canvas-container {
      flex: 1;
      position: relative;
    }
    
    .bottom-bar {
      display: flex;
      gap: 10px;
      padding: 15px;
      background: #0f172a;
      color: #f1f5f9;
      align-items: center;
    }
    
    button {
      padding: 10px 20px;
      background: #3b82f6;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
    }
    
    button:hover {
      background: #2563eb;
    }
    
    button:disabled {
      background: #64748b;
      cursor: not-allowed;
    }
    
    textarea {
      width: 100%;
      min-height: 100px;
      padding: 10px;
      background: #334155;
      color: #f1f5f9;
      border: 1px solid #475569;
      border-radius: 6px;
      font-family: inherit;
      font-size: 14px;
      resize: vertical;
    }
    
    input[type="range"] {
      width: 100%;
    }
  </style>
</head>
<body>
  <div id="app"></div>
  <div id="canvas-container"></div>
  <script type="module" src="/src/index.js"></script>
</body>
</html>
```

### 3.3 Backend Architecture

**Tech Stack:**
- **Language:** Python 3.11+ (FastAPI) - chosen for simplicity and native Genesis integration
- **Physics Validation:** Genesis Python bindings
- **AI:** Anthropic Python SDK / reqwest for Rust
- **Database:** SQLite (scenes, history)
- **Cache:** LMDB or Redis (scene generation cache)

#### Python/FastAPI Implementation

```python
# backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal
import anthropic
import genesis as gs
import json
import hashlib
import lmdb

app = FastAPI()

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
ai_client = get_ai_client()  # Configurable AI provider (e.g., via env vars: Claude, Grok, etc.)
cache_env = lmdb.open('./cache_db', map_size=10**9)

# Models

class Vec3(BaseModel):
    x: float
    y: float
    z: float

class Quaternion(BaseModel):
    x: float
    y: float
    z: float
    w: float

class Transform(BaseModel):
    position: Vec3
    rotation: Quaternion
    scale: Vec3

class PhysicsProperties(BaseModel):
    bodyType: Literal["Dynamic", "Static", "Kinematic"]
    mass: float
    friction: float
    restitution: float
    linearVelocity: Optional[Vec3] = None
    angularVelocity: Optional[Vec3] = None

class VisualProperties(BaseModel):
    color: str
    metallic: float
    roughness: float

class PhysicsObject(BaseModel):
    id: str
    type: Literal["Box", "Sphere", "Cylinder", "Capsule"]
    size: Optional[List[float]] = None
    radius: Optional[float] = None
    height: Optional[float] = None
    transform: Transform
    physics: PhysicsProperties
    visual: VisualProperties

class Environment(BaseModel):
    gravity: Vec3
    ground: bool

class Scene(BaseModel):
    objects: List[PhysicsObject]
    environment: Environment

class GenerateRequest(BaseModel):
    text: str

class RefineRequest(BaseModel):
    scene: Scene
    instruction: str

# Scene Generation

SCENE_SCHEMA = """
{
  "objects": [
    {
      "id": "unique_string",
      "type": "Box" | "Sphere" | "Cylinder" | "Capsule",
      "size": [width, height, depth],  // for Box
      "radius": float,  // for Sphere, Cylinder
      "height": float,  // for Cylinder
      "transform": {
        "position": {"x": float, "y": float, "z": float},
        "rotation": {"x": float, "y": float, "z": float, "w": float},
        "scale": {"x": 1.0, "y": 1.0, "z": 1.0}
      },
      "physics": {
        "bodyType": "Dynamic" | "Static" | "Kinematic",
        "mass": float,
        "friction": float,
        "restitution": float
      },
      "visual": {
        "color": "#RRGGBB",
        "metallic": float,
        "roughness": float
      }
    }
  ],
  "environment": {
    "gravity": {"x": 0, "y": -9.81, "z": 0},
    "ground": true
  }
}
"""

GENERATION_PROMPT_TEMPLATE = """You are a physics scene generator. Create a realistic physics scene from this description.

USER DESCRIPTION: "{text}"

Output ONLY valid JSON matching this schema:
{schema}

RULES:
1. Objects must not overlap (check positions and sizes)
2. All objects must be above ground (y ≥ 0)
3. Use realistic masses: small objects ~1kg, scale appropriately
4. Default friction: 0.5, restitution: 0.3
5. Max 20 objects for performance
6. Generate unique IDs (box1, sphere1, etc.)
7. Include ground unless explicitly excluded

PHYSICAL INTUITION:
- "Heavy" = 10-100x normal mass
- "Bouncy" = restitution 0.7-0.9
- "Slippery" = friction 0.05-0.15
- "Stack" = align centers vertically, touching
- "Scatter" = randomize in 5x5 area

Output ONLY the JSON, no explanation."""

@app.post("/api/generate")
async def generate_scene(request: GenerateRequest):
    # Check cache first
    cache_key = hashlib.sha256(request.text.encode()).digest()
    
    with cache_env.begin() as txn:
        cached = txn.get(cache_key)
        if cached:
            return json.loads(cached)
    
    # Generate with Claude
    try:
        response = ai_client.messages.create(
            model=os.getenv("AI_MODEL", "default-model"),  # Configurable model
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": GENERATION_PROMPT_TEMPLATE.format(
                    text=request.text,
                    schema=SCENE_SCHEMA
                )
            }]
        )
        
        scene_json = response.content[0].text
        scene_data = json.loads(scene_json)
        scene = Scene(**scene_data)
        
        # Validate with Genesis
        validation_result = validate_with_genesis(scene)
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Physics validation failed: {validation_result['error']}"
            )
        
        # Cache successful generation
        with cache_env.begin(write=True) as txn:
            txn.put(cache_key, json.dumps(scene_data).encode())
        
        return scene_data
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse Claude response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def validate_with_genesis(scene: Scene) -> dict:
    """Quick physics validation - simulate 1 second"""
    try:
        gs_scene = gs.Scene(show_viewer=False)
        
        for obj in scene.objects:
            if obj.type == "Box":
                morph = gs.morphs.Box(size=obj.size)
            elif obj.type == "Sphere":
                morph = gs.morphs.Sphere(radius=obj.radius)
            else:
                continue  # Skip unsupported types for now
            
            gs_scene.add_entity(
                morph=morph,
                material=gs.materials.Rigid(
                    rho=obj.physics.mass,
                    restitution=obj.physics.restitution,
                    friction=obj.physics.friction
                ),
                pos=(obj.transform.position.x, obj.transform.position.y, obj.transform.position.z)
            )
        
        gs_scene.build()
        
        # Simulate 60 frames
        for _ in range(60):
            gs_scene.step()
        
        # Check for instability (objects flying off, NaN, etc.)
        # This is simplified - you'd want more robust checks
        
        return {"valid": True, "error": None}
        
    except Exception as e:
        return {"valid": False, "error": str(e)}

@app.post("/api/refine")
async def refine_scene(request: RefineRequest):
    """Modify existing scene based on text instruction"""
    
    prompt = f"""You are modifying a physics scene.

CURRENT SCENE:
{request.scene.json()}

USER INSTRUCTION: "{request.instruction}"

Output the COMPLETE modified scene as JSON (same schema as before).
Apply the requested changes while preserving all other objects.

Output ONLY the JSON."""

    try:
        response = ai_client.messages.create(
            model=os.getenv("AI_MODEL", "default-model"),  # Configurable model
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        refined_json = response.content[0].text
        refined_data = json.loads(refined_json)
        refined_scene = Scene(**refined_data)
        
        return refined_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate")
async def validate_scene(scene: Scene):
    """Just validate a scene without generating"""
    result = validate_with_genesis(scene)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```python
# requirements.txt

fastapi==0.109.0
uvicorn[standard]==0.27.0
# AI provider SDKs configured via env vars
genesis-world==0.3.7
pydantic==2.6.0
lmdb==1.4.1
```

---

## 4. Data Models

### 4.1 Scene Schema (Shared between Elm & Backend)

```elm
-- Elm types (already shown above)
```

```json
// JSON Wire Format

{
  "objects": [
    {
      "id": "box1",
      "type": "Box",
      "size": [1.0, 1.0, 1.0],
      "transform": {
        "position": {"x": 0.0, "y": 5.0, "z": 0.0},
        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "scale": {"x": 1.0, "y": 1.0, "z": 1.0}
      },
      "physics": {
        "bodyType": "Dynamic",
        "mass": 1.0,
        "friction": 0.5,
        "restitution": 0.3,
        "linearVelocity": null,
        "angularVelocity": null
      },
      "visual": {
        "color": "#ff6b6b",
        "metallic": 0.1,
        "roughness": 0.7
      }
    }
  ],
  "environment": {
    "gravity": {"x": 0.0, "y": -9.81, "z": 0.0},
    "ground": true
  }
}
```

### 4.2 SQLite Schema

```sql
-- scenes table
CREATE TABLE scenes (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,  -- Original prompt
    scene_json TEXT,   -- Full scene as JSON
    created_at INTEGER,
    updated_at INTEGER
);

CREATE INDEX idx_scenes_created ON scenes(created_at);

-- refinement_history table
CREATE TABLE refinement_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id TEXT,
    instruction TEXT,
    timestamp INTEGER,
    before_json TEXT,
    after_json TEXT,
    FOREIGN KEY (scene_id) REFERENCES scenes(id)
);

CREATE INDEX idx_refinements_scene ON refinement_history(scene_id);
```

---

## 5. Key Features & User Stories

### 5.1 Core Features

**Must Have (MVP):**
1. Text → Scene generation (<10s)
2. Object selection (click to select)
3. Transform controls (translate/rotate/scale via keyboard: G/R/S)
4. Property editing panel (mass, friction, restitution, color)
5. Play/pause/reset simulation
6. Camera orbit controls
7. Export scene as JSON

**Should Have (v1.0):**
8. AI refinement ("make boxes heavier")
9. Undo/redo (Elm makes this trivial)
10. Local scene save/load (browser IndexedDB)
11. Keyboard shortcuts
12. Object presets (bouncy ball, heavy crate, etc.)

**Nice to Have (v1.1+):**
13. Video export (MP4 recording)
14. URDF/MJCF export
15. Custom mesh import (OBJ files)
16. Constraints (hinges, springs)
17. Multiple scene tabs

### 5.2 User Stories

```
As a user, I want to:

1. Describe a scene in plain English
   - So I don't need to learn physics engine APIs
   - Acceptance: Scene generates in <10s

2. Click any object to select it
   - So I can manipulate individual objects
   - Acceptance: Outline appears, properties panel updates

3. Drag objects to reposition them
   - So I can adjust the scene layout
   - Acceptance: Press G, drag with mouse, object moves in real-time

4. Rotate objects with visual handles
   - So I can orient objects precisely
   - Acceptance: Press R, circular handles appear, mouse drag rotates

5. Change object mass via slider
   - So I can test different weight scenarios
   - Acceptance: Slider updates, physics updates on next simulation

6. Press spacebar to simulate
   - So I can quickly preview physics
   - Acceptance: Physics runs at 60 FPS, objects move realistically

7. Reset simulation to initial state
   - So I can try again with same setup
   - Acceptance: All objects return to positions before play

8. Refine scene with text
   - So I can iterate without manual editing
   - Acceptance: "Make all boxes red" changes colors

9. Undo my last change
   - So I can experiment freely
   - Acceptance: Ctrl+Z reverts last action

10. Export scene as JSON
    - So I can use it in other tools
    - Acceptance: Downloads valid JSON matching schema
```

---

## 6. Non-Functional Requirements

### Performance Targets

| Metric | Target |
|--------|--------|
| Text → Scene generation | <10s (p95) |
| Scene refinement | <5s (p95) |
| Initial page load | <2s |
| Physics simulation FPS (20 objects) | 60 FPS |
| UI responsiveness | <16ms (60 FPS) |
| Transform control lag | <100ms |

### Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Requires: WebGL 2.0, WebAssembly

### Reliability

- Elm's type system prevents runtime errors in UI logic
- Genesis validation catches unstable physics
- Graceful degradation: template fallback if Claude fails

---

## 7. Development Phases

### Phase 1: Foundation (Week 1-2)

**Elm Setup:**
- [ ] Basic Elm app structure
- [ ] Scene model types
- [ ] UI layout (3-panel)
- [ ] Ports defined

**Three.js/JavaScript:**
- [ ] Three.js renderer setup
- [ ] Rapier WASM integration
- [ ] Basic object rendering (box, sphere, ground)
- [ ] Camera orbit controls
- [ ] Port communication with Elm

**Backend:**
- [ ] FastAPI server setup
- [ ] Claude API integration
- [ ] `/api/generate` endpoint
- [ ] Genesis validation

**Deliverable:** Can type "red box", see it render, orbit camera

### Phase 2: Interaction (Week 3-4)

**Elm:**
- [ ] Object selection logic
- [ ] Property editing panel
- [ ] Transform mode switching (G/R/S)
- [ ] Simulation state management

**Three.js:**
- [ ] Raycasting for selection
- [ ] TransformControls integration
- [ ] Selection highlighting
- [ ] Physics simulation loop

**Deliverable:** Can select, move, rotate objects; press space to simulate

### Phase 3: AI Refinement (Week 5)

**Elm:**
- [ ] Refinement text input
- [ ] Scene diff visualization (what changed)

**Backend:**
- [ ] `/api/refine` endpoint
- [ ] Prompt engineering for modifications
- [ ] Cache layer (LMDB)

**Deliverable:** Can refine scene with "make boxes bigger"

### Phase 4: Polish (Week 6)

**Elm:**
- [ ] Undo/redo system
- [ ] Keyboard shortcuts
- [ ] Local storage (IndexedDB)
- [ ] Error handling & loading states

**Three.js:**
- [ ] Better lighting/shadows
- [ ] Ground grid
- [ ] Visual polish

**Backend:**
- [ ] SQLite scene storage
- [ ] Better error messages

**Deliverable:** Public beta ready

---

## 8. Open Questions

1. **Animation/Interpolation Handling:** JS handles all visual interpolation, Elm tracks discrete state.

2. **Initial States Storage:** Elm stores initial states and sends to JS on reset (Elm as source of truth).

3. **Undo/Redo with Active Simulation:** Undo auto-pauses simulation, reverts state, resets physics; history stored in Elm.

4. **Mobile Support in v1:** No - desktop-first, defer mobile to later versions.

5. **Export Formats Priority:** Defer decision; MVP: JSON only, evaluate others post-MVP.

---

## 9. Success Metrics

**MVP Success:**
- 10 users can generate → edit → simulate → export
- Average iteration time <30 seconds
- <5 crashes/errors per user session

**v1.0 Success:**
- 100 MAU
- Average 5 iterations per session
- 90%+ scene generation success rate
- Users self-report "faster than Unity/Blender"

---

## 10. What We're NOT Building (v1.0)

- Soft body simulation
- Fluid simulation  
- Custom shaders/materials
- Multiplayer/collaboration
- User accounts (MVP is local-only)
- Mobile app
- VR/AR support
- Video export
- Mesh editing
- Animation timeline
- Scripting API

These may come later, but out of scope for MVP.

---

**Next Step:** Start with Phase 1, beginning with Elm app scaffold and basic Three.js integration via ports.

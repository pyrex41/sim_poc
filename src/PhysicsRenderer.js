import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { TransformControls } from 'three/examples/jsm/controls/TransformControls.js';
import RAPIER from '@dimforge/rapier3d';

class PhysicsRenderer {
    constructor(canvasContainer) {
        this.canvasContainer = canvasContainer;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.world = null;
        this.objects = new Map();
        this.animationId = null;
        this.isInitialized = false;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.selectedObjectId = null;
        this.transformControls = null;
        this.currentTransformMode = 'translate';
    }

    async init() {
        if (this.isInitialized) return;

        try {
            // Initialize Rapier physics - default export is already initialized
            const gravity = { x: 0, y: -9.81, z: 0 };
            this.world = new RAPIER.World(gravity);

            // Initialize Three.js
            this.setupRenderer();
            this.setupCamera();
            this.setupControls();
            this.setupLights();
            this.setupGround();

            this.isInitialized = true;
            console.log('PhysicsRenderer initialized successfully');
        } catch (error) {
            console.error('Failed to initialize PhysicsRenderer:', error);
        }
    }

    setupRenderer() {
        this.scene = new THREE.Scene();

        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.canvasContainer.clientWidth, this.canvasContainer.clientHeight);
        this.renderer.setClearColor(0x000000);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.canvasContainer.appendChild(this.renderer.domElement);

        // Handle window resize
        window.addEventListener('resize', () => {
            this.camera.aspect = this.canvasContainer.clientWidth / this.canvasContainer.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(this.canvasContainer.clientWidth, this.canvasContainer.clientHeight);
        });
    }

    setupCamera() {
        const aspect = this.canvasContainer.clientWidth / this.canvasContainer.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(5, 5, 5);
        this.camera.lookAt(0, 0, 0);
    }

    setupControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.enableZoom = true;
        this.controls.enablePan = true;

        // Initialize transform controls
        this.transformControls = new TransformControls(this.camera, this.renderer.domElement);
        this.transformControls.setMode(this.currentTransformMode);
        this.transformControls.setSize(0.8);
        this.transformControls.addEventListener('objectChange', () => this.onTransformChange());

        // Disable orbit controls when dragging transform controls
        this.transformControls.addEventListener('dragging-changed', (event) => {
            this.controls.enabled = !event.value;
        });

        this.scene.add(this.transformControls);

        // Add mouse event listeners for object selection
        this.renderer.domElement.addEventListener('click', (event) => this.onMouseClick(event));
        this.renderer.domElement.addEventListener('mousemove', (event) => this.onMouseMove(event));
    }

    setupLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        this.scene.add(ambientLight);

        // Directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
    }

    setupGround() {
        // Create ground plane
        const groundGeometry = new THREE.PlaneGeometry(20, 20);
        const groundMaterial = new THREE.MeshLambertMaterial({ color: 0x888888 });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        ground.userData = { selectable: false }; // Mark ground as non-selectable
        this.scene.add(ground);

        // Add ground collider
        const groundColliderDesc = RAPIER.ColliderDesc.cuboid(10, 0.1, 10);
        this.world.createCollider(groundColliderDesc);
    }

    loadScene(sceneData) {
        if (!this.isInitialized) return;

        // Store initial scene for reset functionality
        if (!this.initialScene) {
            this.initialScene = JSON.parse(JSON.stringify(sceneData));
        }

        // Clear existing objects
        this.clearScene();

        // Parse scene data and create objects
        if (sceneData && sceneData.objects) {
            Object.values(sceneData.objects).forEach(objData => {
                this.addObject(objData);
            });
        }
    }

    addObject(objData) {
        const { id, transform, physicsProperties, visualProperties } = objData;

        // Create Three.js mesh
        const geometry = this.createGeometry(visualProperties.shape);
        const material = new THREE.MeshLambertMaterial({
            color: new THREE.Color(visualProperties.color)
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData = { id, selectable: true }; // Mark mesh as selectable

        // Set transform
        mesh.position.set(transform.position.x, transform.position.y, transform.position.z);
        mesh.rotation.set(transform.rotation.x, transform.rotation.y, transform.rotation.z);
        mesh.scale.set(transform.scale.x, transform.scale.y, transform.scale.z);

        this.scene.add(mesh);

        // Create Rapier rigid body and collider
        const rigidBodyDesc = RAPIER.RigidBodyDesc.dynamic()
            .setTranslation(transform.position.x, transform.position.y, transform.position.z)
            .setRotation({ x: transform.rotation.x, y: transform.rotation.y, z: transform.rotation.z, w: 1 });

        const rigidBody = this.world.createRigidBody(rigidBodyDesc);
        rigidBody.setAdditionalMass(physicsProperties.mass);

        let colliderDesc;
        switch (visualProperties.shape) {
            case 'Box':
                colliderDesc = RAPIER.ColliderDesc.cuboid(
                    transform.scale.x / 2,
                    transform.scale.y / 2,
                    transform.scale.z / 2
                );
                break;
            case 'Sphere':
                colliderDesc = RAPIER.ColliderDesc.ball(transform.scale.x / 2);
                break;
            case 'Cylinder':
                colliderDesc = RAPIER.ColliderDesc.cylinder(transform.scale.y / 2, transform.scale.x / 2);
                break;
            default:
                colliderDesc = RAPIER.ColliderDesc.cuboid(0.5, 0.5, 0.5);
        }

        colliderDesc.setFriction(physicsProperties.friction);
        colliderDesc.setRestitution(physicsProperties.restitution);

        const collider = this.world.createCollider(colliderDesc, rigidBody);

        // Store object data
        this.objects.set(id, {
            mesh,
            rigidBody,
            collider,
            originalData: objData
        });
    }

    createGeometry(shape) {
        switch (shape) {
            case 'Box':
                return new THREE.BoxGeometry(1, 1, 1);
            case 'Sphere':
                return new THREE.SphereGeometry(0.5, 16, 16);
            case 'Cylinder':
                return new THREE.CylinderGeometry(0.5, 0.5, 1, 16);
            default:
                return new THREE.BoxGeometry(1, 1, 1);
        }
    }

    clearScene() {
        // Remove all rigid bodies and meshes
        this.objects.forEach(obj => {
            if (obj.rigidBody && this.world) {
                this.world.removeRigidBody(obj.rigidBody);
            }
            if (obj.mesh) {
                this.scene.remove(obj.mesh);
            }
        });

        // Clear objects map
        this.objects.clear();
    }

    startSimulation() {
        if (!this.animationId) {
            // Detach transform controls during simulation to prevent conflicts
            if (this.transformControls) {
                this.transformControls.detach();
            }
            this.animate();
        }
    }

    pauseSimulation() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
            // Re-attach transform controls when simulation is paused
            if (this.selectedObjectId && this.transformControls) {
                const selectedObject = this.objects.get(this.selectedObjectId);
                if (selectedObject) {
                    this.transformControls.attach(selectedObject.mesh);
                }
            }
        }
    }

    resetSimulation() {
        this.pauseSimulation();
        this.loadScene(this.initialScene);
    }

    animate = () => {
        this.animationId = requestAnimationFrame(this.animate);

        // Update physics
        if (!this.world) return;
        this.world.step();

        // Sync Three.js meshes with physics bodies
        this.objects.forEach(obj => {
            const position = obj.rigidBody.translation();
            const rotation = obj.rigidBody.rotation();

            obj.mesh.position.set(position.x, position.y, position.z);
            obj.mesh.quaternion.set(rotation.x, rotation.y, rotation.z, rotation.w);
        });

        // Update controls
        this.controls.update();

        // Render
        this.renderer.render(this.scene, this.camera);
    }

    onMouseClick(event) {
        if (!this.isInitialized) return;

        // Update mouse position
        this.updateMousePosition(event);

        // Perform raycasting
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.scene.children, false);

        // Find the first selectable object
        let selectedObject = null;
        for (const intersect of intersects) {
            if (intersect.object.userData.selectable) {
                selectedObject = intersect.object;
                break;
            }
        }

        // Update selection
        this.selectObject(selectedObject ? selectedObject.userData.id : null);
    }

    onMouseMove(event) {
        if (!this.isInitialized) return;
        this.updateMousePosition(event);
    }

    updateMousePosition(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }

    selectObject(objectId) {
        // Clear previous selection
        if (this.selectedObjectId) {
            const prevObject = this.objects.get(this.selectedObjectId);
            if (prevObject) {
                // Reset material color
                prevObject.mesh.material.color.setHex(prevObject.originalData.visualProperties.color.replace('#', '0x'));
                // Detach transform controls
                this.transformControls.detach();
            }
        }

        this.selectedObjectId = objectId;

        // Apply selection highlight and attach transform controls
        if (objectId) {
            const selectedObject = this.objects.get(objectId);
            if (selectedObject) {
                // Highlight selected object (make it brighter)
                const originalColor = new THREE.Color(selectedObject.originalData.visualProperties.color);
                selectedObject.mesh.material.color.setRGB(
                    Math.min(originalColor.r * 1.3, 1),
                    Math.min(originalColor.g * 1.3, 1),
                    Math.min(originalColor.b * 1.3, 1)
                );
                // Attach transform controls (only if not simulating)
                if (!this.animationId) {
                    this.transformControls.attach(selectedObject.mesh);
                }
            }
        }

        // Notify Elm about selection change
        if (window.elmApp && window.elmApp.ports.sendSelectionToElm) {
            window.elmApp.ports.sendSelectionToElm.send(objectId);
        }
    }

    getSelectedObjectId() {
        return this.selectedObjectId;
    }

    setTransformMode(mode) {
        this.currentTransformMode = mode;
        if (this.transformControls) {
            this.transformControls.setMode(mode);
        }
    }

    onTransformChange() {
        if (!this.selectedObjectId) return;

        const selectedObject = this.objects.get(this.selectedObjectId);
        if (!selectedObject) return;

        const mesh = selectedObject.mesh;
        const rigidBody = selectedObject.rigidBody;

        // Update physics body position and rotation
        const position = mesh.position;
        const quaternion = mesh.quaternion;

        rigidBody.setTranslation({ x: position.x, y: position.y, z: position.z }, true);
        rigidBody.setRotation({ x: quaternion.x, y: quaternion.y, z: quaternion.z, w: quaternion.w }, true);

        // Notify Elm about transform change
        const transform = {
            position: { x: position.x, y: position.y, z: position.z },
            rotation: { x: mesh.rotation.x, y: mesh.rotation.y, z: mesh.rotation.z },
            scale: { x: mesh.scale.x, y: mesh.scale.y, z: mesh.scale.z }
        };

        if (window.elmApp && window.elmApp.ports.sendTransformUpdateToElm) {
            window.elmApp.ports.sendTransformUpdateToElm.send({
                objectId: this.selectedObjectId,
                transform: transform
            });
        }
    }

    destroy() {
        this.pauseSimulation();
        if (this.transformControls) {
            this.scene.remove(this.transformControls);
        }
        if (this.renderer) {
            // Remove event listeners
            this.renderer.domElement.removeEventListener('click', this.onMouseClick);
            this.renderer.domElement.removeEventListener('mousemove', this.onMouseMove);

            this.canvasContainer.removeChild(this.renderer.domElement);
            this.renderer.dispose();
        }
    }
}



export default PhysicsRenderer;
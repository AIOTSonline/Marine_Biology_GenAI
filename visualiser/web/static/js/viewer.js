// viewer.js
/* global SERVER_URL */
document.addEventListener("DOMContentLoaded", () => {
    // --- Page Elements ---
    const promptPage = document.getElementById('prompt-page');
    const viewerPage = document.getElementById('viewer-page');
    const generateBtn = document.getElementById('generate-btn');
    const fetchBtn = document.getElementById('fetch-btn');
    const backBtn = document.getElementById('back-btn');
    const viewerContainer = document.getElementById('viewer-container');
    const loaderContainer = document.getElementById('loader-container');
    const loaderText = document.getElementById('loader-text');

    let scene, camera, renderer, controls;
    let meshModel, paintedModel, modelGroup; // models + group
    let isPaintedVisible = false; // default mesh.glb

    // --- PiP Image Swap ---
    let mainIsMesh = true;
    let miniContainer, miniImg;
    let mainImageContainer, miniMesh;

    // --- Page Navigation ---
    function showViewerPage() {
        promptPage.classList.remove('visible-page');
        promptPage.classList.add('hidden-page');
        setTimeout(() => {
            promptPage.style.display = 'none';
            viewerPage.style.display = 'flex';
            viewerPage.classList.remove('hidden-page');
            viewerPage.classList.add('visible-page');
        }, 300);
    }

    function showPromptPage() {
        viewerPage.classList.remove('visible-page');
        viewerPage.classList.add('hidden-page');
        setTimeout(() => {
            viewerPage.style.display = 'none';
            promptPage.style.display = 'flex';
            promptPage.classList.remove('hidden-page');
            promptPage.classList.add('visible-page');
            destroy3DViewer();
        }, 300);
    }

    // --- Generate / Fetch Handlers ---
    async function handleGeneration(method) {
        const concept = document.getElementById('prompt').value.trim();
        if (!concept) { alert("Enter a prompt"); return; }

        showViewerPage();
        setLoadingState(true, method === "genai" ? 'Forging Your Asset...' : 'Fetching from Library...');

        try {
            const resp = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ concept, method })
            });

            if (!resp.ok) throw new Error("API request failed");
            const data = await resp.json();

            if (data.status !== "done") throw new Error(data.error || "Generation failed");
            if (!data.files || data.files.length < 2) throw new Error("Both GLB files not returned");

            const meshUrl = `${SERVER_URL}/download/${data.files[0]}`;
            const paintedUrl = `${SERVER_URL}/download/${data.files[1]}`;
            init3DViewer(meshUrl, paintedUrl);

        } catch (err) {
            console.error(err);
            loaderText.innerHTML = `<p class="text-red-400 text-lg font-orbitron">Error</p><p class="text-gray-400 mt-2">${err.message}</p>`;
        }
    }

    generateBtn.addEventListener('click', () => handleGeneration("genai"));
    fetchBtn.addEventListener('click', () => handleGeneration("fathomnet"));
    backBtn.addEventListener('click', showPromptPage);

    // --- Three.js Viewer ---
    function init3DViewer(meshUrl, paintedUrl) {
        setLoadingState(true, 'Loading 3D Asset...');

        viewerContainer.innerHTML = "";
        scene = new THREE.Scene();

        camera = new THREE.PerspectiveCamera(
            75,
            viewerContainer.clientWidth / viewerContainer.clientHeight,
            0.01,
            5000
        );

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(viewerContainer.clientWidth, viewerContainer.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setClearColor(0x000000, 0);
        viewerContainer.appendChild(renderer.domElement);

        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;

        // --- Lighting ---
        const ambient = new THREE.AmbientLight(0xffffff, 1.2);
        scene.add(ambient);

        const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
        dirLight.position.set(5, 10, 7.5);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const fill1 = new THREE.PointLight(0xffffff, 0.5);
        fill1.position.set(-5, 5, 5);
        scene.add(fill1);

        const fill2 = new THREE.PointLight(0xffffff, 0.5);
        fill2.position.set(5, 5, -5);
        scene.add(fill2);

        // --- Parent group for models ---
        modelGroup = new THREE.Group();
        scene.add(modelGroup);

        const loader = new THREE.GLTFLoader();
        let loadedCount = 0;

        function finalizeModel(model) {
            const box = new THREE.Box3().setFromObject(model);
            const size = box.getSize(new THREE.Vector3());
            const center = box.getCenter(new THREE.Vector3());
            model.position.sub(center);

            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 5 / maxDim;
            model.scale.set(scale, scale, scale);

            modelGroup.add(model);

            loadedCount++;
            if (loadedCount === 2) {
                setLoadingState(false);
                updateModelVisibility();

                const box2 = new THREE.Box3().setFromObject(meshModel);
                const size2 = box2.getSize(new THREE.Vector3());
                const fov = camera.fov * (Math.PI / 180);
                const cameraZ = Math.abs(size2.y / 2 / Math.tan(fov / 2));
                camera.position.set(0, size2.y / 2, cameraZ * 1.5);
                controls.target.set(0, 0, 0);
                controls.update();

                createToggleButton();
                createMiniImage(meshUrl);

                // add wheel listener AFTER models loaded
                renderer.domElement.addEventListener("wheel", onMouseWheel);
            }
        }

        loader.load(meshUrl,
            (gltf) => { meshModel = gltf.scene; finalizeModel(meshModel); },
            undefined,
            (err) => console.error("Error loading mesh.glb", err)
        );

        loader.load(paintedUrl,
            (gltf) => { paintedModel = gltf.scene; finalizeModel(paintedModel); },
            undefined,
            (err) => console.error("Error loading painted.glb", err)
        );

        animate();
        window.addEventListener('resize', onWindowResize);
    }

    // --- Zoom-out scaling ---
    let currentScale = 1;
    function onMouseWheel(event) {
        if (!modelGroup) return;
        const delta = event.deltaY > 0 ? 0.9 : 1.1; // scroll down = shrink
        currentScale *= delta;
        modelGroup.scale.multiplyScalar(delta);
    }

    function updateModelVisibility() {
        if (meshModel) meshModel.visible = !isPaintedVisible;
        if (paintedModel) paintedModel.visible = isPaintedVisible;
    }

    function createToggleButton() {
        const toggle = document.createElement("button");
        toggle.textContent = "Painted";
        toggle.className = `
            absolute top-6 right-6
            px-3 py-1.5
            text-sm font-semibold
            text-white
            rounded-full
            bg-gradient-to-r from-purple-600 to-indigo-500
            shadow-lg
            hover:from-purple-500 hover:to-indigo-400
            transition
            z-20
        `;
        toggle.style.backdropFilter = "blur(6px)";
        toggle.onclick = () => {
            isPaintedVisible = !isPaintedVisible;
            updateModelVisibility();
            toggle.textContent = isPaintedVisible ? "Mesh" : "Painted";
        };
        viewerPage.appendChild(toggle);
    }

    function createMiniImage(meshUrl) {
        const imageUrl = `${SERVER_URL}/download/image.png`;

        miniContainer = document.createElement("div");
        miniContainer.style.position = "absolute";
        miniContainer.style.bottom = "20px";
        miniContainer.style.right = "20px";
        miniContainer.style.width = "150px";
        miniContainer.style.height = "150px";
        miniContainer.style.border = "2px solid white";
        miniContainer.style.cursor = "pointer";
        miniContainer.style.zIndex = "30";
        miniContainer.style.overflow = "hidden";
        miniContainer.style.borderRadius = "12px";

        miniImg = document.createElement("img");
        miniImg.src = imageUrl;
        miniImg.style.width = "100%";
        miniImg.style.height = "100%";
        miniImg.style.objectFit = "cover";
        miniContainer.appendChild(miniImg);
        viewerPage.appendChild(miniContainer);

        mainImageContainer = document.createElement("img");
        mainImageContainer.src = imageUrl;
        mainImageContainer.style.position = "absolute";
        mainImageContainer.style.top = "0";
        mainImageContainer.style.left = "0";
        mainImageContainer.style.width = "100%";
        mainImageContainer.style.height = "100%";
        mainImageContainer.style.objectFit = "contain";
        mainImageContainer.style.display = "none";
        mainImageContainer.style.zIndex = "15";
        viewerContainer.appendChild(mainImageContainer);

        miniMesh = renderer.domElement.cloneNode(true);
        miniMesh.style.width = "100%";
        miniMesh.style.height = "100%";
        miniMesh.style.display = "none";
        miniContainer.appendChild(miniMesh);

        miniContainer.addEventListener("click", () => {
            if (mainIsMesh) {
                mainImageContainer.style.display = "block";
                renderer.domElement.style.display = "none";
                miniImg.style.display = "none";
                miniMesh.style.display = "block";
            } else {
                mainImageContainer.style.display = "none";
                renderer.domElement.style.display = "block";
                miniImg.style.display = "block";
                miniMesh.style.display = "none";
            }
            mainIsMesh = !mainIsMesh;
        });
    }

    function setLoadingState(isLoading, text = 'Loading...') {
        if (isLoading) {
            loaderContainer.style.display = 'flex';
            viewerContainer.style.display = 'none';
            loaderText.textContent = text;
        } else {
            loaderContainer.style.display = 'none';
            viewerContainer.style.display = 'block';
        }
    }

    function onWindowResize() {
        if (!renderer) return;
        camera.aspect = viewerContainer.clientWidth / viewerContainer.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(viewerContainer.clientWidth, viewerContainer.clientHeight);
    }

    function animate() {
        if (!renderer) return;
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }

    function destroy3DViewer() {
        window.removeEventListener('resize', onWindowResize);
        if (renderer) {
            renderer.domElement.removeEventListener("wheel", onMouseWheel);
            renderer.dispose();
            if (viewerContainer.contains(renderer.domElement)) {
                viewerContainer.removeChild(renderer.domElement);
            }
        }
        meshModel = paintedModel = scene = camera = renderer = controls = modelGroup = null;

        const oldToggle = viewerPage.querySelector("button.absolute.top-6.right-6");
        if (oldToggle) oldToggle.remove();

        if (miniContainer) miniContainer.remove();
        if (mainImageContainer) mainImageContainer.remove();

        isPaintedVisible = false;
        mainIsMesh = true;
    }

    console.log("Stellar Forge viewer.js loaded and initialized");
});

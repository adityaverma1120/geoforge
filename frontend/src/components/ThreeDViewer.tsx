import React, {
  useEffect,
  useRef,
  useState,
} from 'react';

import * as THREE from 'three';

import {
  GLTFLoader,
} from 'three/examples/jsm/loaders/GLTFLoader.js';


interface ThreeDViewerProps {
  modelUrl?: string;

  onModelLoadError?: (
    error: Error
  ) => void;

  onModelLoaded?: () => void;

  className?: string;
}


export const ThreeDViewer: React.FC<
  ThreeDViewerProps
> = ({
  modelUrl,
  onModelLoadError,
  onModelLoaded,
  className = '',
}) => {

  /*
   * =========================================================
   * REFS
   * =========================================================
   */

  const containerRef =
    useRef<HTMLDivElement>(null);

  const canvasRef =
    useRef<HTMLCanvasElement>(null);

  const onModelLoadErrorRef =
    useRef(onModelLoadError);

  const onModelLoadedRef =
    useRef(onModelLoaded);

  useEffect(() => {
    onModelLoadErrorRef.current = onModelLoadError;
    onModelLoadedRef.current = onModelLoaded;
  }, [onModelLoadError, onModelLoaded]);


  /*
   * =========================================================
   * STATE
   * =========================================================
   */

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    isFullscreen,
    setIsFullscreen,
  ] = useState(false);

  const [
    fov,
    setFov,
  ] = useState(45);

  const [
    activeTool,
    setActiveTool,
  ] = useState<
    'rotate' | 'pan' | 'zoom'
  >('rotate');


  /*
   * =========================================================
   * THREE.JS REFERENCES
   * =========================================================
   */

  const sceneRef =
    useRef<THREE.Scene | null>(null);

  const cameraRef =
    useRef<THREE.PerspectiveCamera | null>(
      null
    );

  const rendererRef =
    useRef<THREE.WebGLRenderer | null>(
      null
    );

  const modelGroupRef =
    useRef<THREE.Group | null>(null);


  /*
   * =========================================================
   * MODEL / CAMERA REFERENCES
   * =========================================================
   */

  const cameraTargetRef =
    useRef(
      new THREE.Vector3(
        0,
        0,
        0
      )
    );


  const initialCameraPosRef =
    useRef(
      new THREE.Vector3(
        5,
        4,
        8
      )
    );


  /*
   * =========================================================
   * MODEL GROUND HEIGHT
   *
   * IMPORTANT:
   *
   * The model will be positioned so that its
   * lowest point sits exactly on the ground plane.
   * =========================================================
   */

  const groundYRef =
    useRef(-3);


  /*
   * =========================================================
   * POINTER STATE
   * =========================================================
   */

  const isDraggingRef =
    useRef(false);


  const previousMousePositionRef =
    useRef({
      x: 0,
      y: 0,
    });


  /*
   * =========================================================
   * RESET CAMERA
   * =========================================================
   */

  const handleResetCamera = () => {

    const camera =
      cameraRef.current;

    if (!camera) {
      return;
    }


    /*
     * Restore automatically calculated
     * camera position.
     */

    camera.position.copy(
      initialCameraPosRef.current
    );


    /*
     * Look at the model.
     */

    camera.lookAt(
      cameraTargetRef.current
    );


    /*
     * Reset model rotation.
     */

    if (
      modelGroupRef.current
    ) {

      modelGroupRef.current.rotation.set(
        0,
        0,
        0
      );

    }

  };


  /*
   * =========================================================
   * ZOOM
   * =========================================================
   */

  const handleZoom = (
    amount: number
  ) => {

    const camera =
      cameraRef.current;

    if (!camera) {
      return;
    }


    const direction =
      new THREE.Vector3();


    camera.getWorldDirection(
      direction
    );


    camera.position.addScaledVector(
      direction,
      amount
    );


    const target =
      cameraTargetRef.current;


    const distance =
      camera.position.distanceTo(
        target
      );


    /*
     * Minimum distance.
     */

    if (
      distance < 0.5
    ) {

      const safeDirection =
        camera.position
          .clone()
          .sub(target)
          .normalize();


      camera.position.copy(
        target
          .clone()
          .add(
            safeDirection.multiplyScalar(
              0.5
            )
          )
      );

    }


    /*
     * Maximum distance.
     */

    if (
      distance > 500
    ) {

      const safeDirection =
        camera.position
          .clone()
          .sub(target)
          .normalize();


      camera.position.copy(
        target
          .clone()
          .add(
            safeDirection.multiplyScalar(
              500
            )
          )
      );

    }

  };


  /*
   * =========================================================
   * FULLSCREEN
   * =========================================================
   */

  const handleToggleFullscreen =
    async () => {

      const container =
        containerRef.current;

      if (!container) {
        return;
      }


      try {

        if (
          !document.fullscreenElement
        ) {

          await container.requestFullscreen();

        } else {

          await document.exitFullscreen();

        }

      } catch (
        error
      ) {

        console.error(
          'Fullscreen error:',
          error
        );

      }

    };


  /*
   * =========================================================
   * FULLSCREEN EVENT
   * =========================================================
   */

  useEffect(() => {

    const handleFullscreenChange =
      () => {

        setIsFullscreen(
          Boolean(
            document.fullscreenElement
          )
        );

      };


    document.addEventListener(
      'fullscreenchange',
      handleFullscreenChange
    );


    return () => {

      document.removeEventListener(
        'fullscreenchange',
        handleFullscreenChange
      );

    };

  }, []);


  /*
   * =========================================================
   * THREE.JS SETUP
   * =========================================================
   */

  useEffect(() => {

    const container =
      containerRef.current;

    const canvas =
      canvasRef.current;


    if (
      !container ||
      !canvas
    ) {

      return;

    }


    let cancelled =
      false;


    /*
     * =======================================================
     * SCENE
     * =======================================================
     */

    const scene =
      new THREE.Scene();


    scene.background =
      new THREE.Color(
        0x020617
      );


    sceneRef.current =
      scene;


    /*
     * =======================================================
     * CAMERA
     * =======================================================
     */

    const width =
      Math.max(
        container.clientWidth,
        1
      );


    const height =
      Math.max(
        container.clientHeight,
        1
      );


    const camera =
      new THREE.PerspectiveCamera(
        fov,
        width / height,
        0.001,
        100000
      );


    camera.position.copy(
      initialCameraPosRef.current
    );


    camera.lookAt(
      cameraTargetRef.current
    );


    cameraRef.current =
      camera;


    /*
     * =======================================================
     * RENDERER
     * =======================================================
     */

    const renderer =
      new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: false,
        powerPreference:
          'high-performance',
      });


    renderer.setSize(
      width,
      height,
      false
    );


    renderer.setPixelRatio(
      Math.min(
        window.devicePixelRatio || 1,
        2
      )
    );


    renderer.toneMapping =
      THREE.ACESFilmicToneMapping;


    renderer.toneMappingExposure =
      1.2;


    rendererRef.current =
      renderer;


    /*
     * =======================================================
     * LIGHTING
     * =======================================================
     */

    const ambientLight =
      new THREE.AmbientLight(
        0xffffff,
        2
      );


    scene.add(
      ambientLight
    );


    const directionalLight =
      new THREE.DirectionalLight(
        0xffffff,
        3
      );


    directionalLight.position.set(
      10,
      20,
      10
    );


    scene.add(
      directionalLight
    );


    const directionalLight2 =
      new THREE.DirectionalLight(
        0x8db5ff,
        1.5
      );


    directionalLight2.position.set(
      -10,
      5,
      -10
    );


    scene.add(
      directionalLight2
    );


    /*
     * =======================================================
     * GROUND GRID
     * =======================================================
     *
     * This is the reference surface.
     */

    const grid =
      new THREE.GridHelper(
        40,
        40,
        0x2563eb,
        0x1e293b
      );


    /*
     * The reconstructed model will be
     * placed so that its LOWEST POINT
     * touches this exact Y position.
     */

    grid.position.y =
      groundYRef.current;


    scene.add(
      grid
    );


    /*
     * =======================================================
     * GROUND REFERENCE PLANE
     * =======================================================
     *
     * A very subtle plane makes it easier
     * to visually understand where the
     * terrain is sitting.
     */

    const groundGeometry =
      new THREE.PlaneGeometry(
        40,
        40
      );


    const groundMaterial =
      new THREE.MeshStandardMaterial({
        color: 0x020617,
        transparent: true,
        opacity: 0.15,
        roughness: 1,
        metalness: 0,
        side: THREE.DoubleSide,
      });


    const groundPlane =
      new THREE.Mesh(
        groundGeometry,
        groundMaterial
      );


    groundPlane.rotation.x =
      -Math.PI / 2;


    groundPlane.position.y =
      groundYRef.current;


    scene.add(
      groundPlane
    );


    /*
     * =======================================================
     * MODEL GROUP
     * =======================================================
     */

    const modelGroup =
      new THREE.Group();


    scene.add(
      modelGroup
    );


    modelGroupRef.current =
      modelGroup;


    /*
     * =======================================================
     * LOAD MODEL
     * =======================================================
     */

    const loadModel =
      () => {

        setIsLoading(true);


        /*
         * If backend provides model URL,
         * use it.
         *
         * Otherwise use local fallback.
         */

        const url =
          modelUrl &&
          modelUrl.trim().length > 0
            ? modelUrl
            : '/video_model.glb';


        console.log(
          'Loading 3D model:',
          url
        );


        const loader =
          new GLTFLoader();


        loader.load(

          url,


          /*
           * =================================================
           * SUCCESS
           * =================================================
           */

          (gltf) => {

            if (cancelled) {
              return;
            }


            console.log(
              'GLB loaded successfully.'
            );


            /*
             * Remove previous models.
             */

            while (
              modelGroup.children.length >
              0
            ) {

              const child =
                modelGroup.children[0];


              modelGroup.remove(
                child
              );

            }


            const model =
              gltf.scene;


            /*
             * =================================================
             * MAKE ALL MESHES VISIBLE
             * =================================================
             */

            let meshCount =
              0;


            model.traverse(
              (object) => {

                const mesh =
                  object as THREE.Mesh;


                if (
                  mesh.isMesh
                ) {

                  meshCount++;


                  mesh.visible =
                    true;


                  /*
                   * Render both sides.
                   *
                   * This is important for
                   * reconstructed meshes because
                   * some faces may have reversed
                   * normals.
                   */

                  if (
                    mesh.material
                  ) {

                    if (
                      Array.isArray(
                        mesh.material
                      )
                    ) {

                      mesh.material.forEach(
                        (material) => {

                          material.side =
                            THREE.DoubleSide;

                          material.needsUpdate =
                            true;

                        }
                      );

                    } else {

                      mesh.material.side =
                        THREE.DoubleSide;

                      mesh.material.needsUpdate =
                        true;

                    }

                  }

                }

              }
            );


            console.log(
              'Mesh count:',
              meshCount
            );


            /*
             * =================================================
             * ORIGINAL BOUNDS
             * =================================================
             */

            model.updateMatrixWorld(
              true
            );


            const originalBox =
              new THREE.Box3()
                .setFromObject(
                  model
                );


            const originalSize =
              originalBox.getSize(
                new THREE.Vector3()
              );


            const originalCenter =
              originalBox.getCenter(
                new THREE.Vector3()
              );


            const originalMin =
              originalBox.min.clone();


            const originalMax =
              originalBox.max.clone();


            console.log(
              'Original model bounds:',
              originalBox
            );


            console.log(
              'Original model size:',
              originalSize
            );


            console.log(
              'Original model center:',
              originalCenter
            );


            console.log(
              'Original model minimum:',
              originalMin
            );


            console.log(
              'Original model maximum:',
              originalMax
            );


            /*
             * =================================================
             * VALIDATE MODEL
             * =================================================
             */

            const originalMaxDimension =
              Math.max(
                originalSize.x,
                originalSize.y,
                originalSize.z
              );


            if (
              !Number.isFinite(
                originalMaxDimension
              ) ||
              originalMaxDimension <= 0
            ) {

              console.error(
                'Invalid GLB dimensions.',
                originalSize
              );


              setIsLoading(
                false
              );


              onModelLoadErrorRef.current?.(
                new Error(
                  'The GLB loaded, but it contains no visible geometry.'
                )
              );


              return;

            }


            /*
             * =================================================
             * RESET MODEL TRANSFORM
             * =================================================
             */

            model.position.set(
              0,
              0,
              0
            );


            model.rotation.set(
              0,
              0,
              0
            );


            model.scale.set(
              1,
              1,
              1
            );


            /*
             * =================================================
             * SCALE MODEL
             * =================================================
             *
             * Largest dimension becomes 6 units.
             */

            const scale =
              6 /
              originalMaxDimension;


            model.scale.setScalar(
              scale
            );


            /*
             * IMPORTANT:
             *
             * Update world matrix BEFORE
             * calculating the scaled bounds.
             */

            model.updateMatrixWorld(
              true
            );


            /*
             * =================================================
             * SCALED BOUNDS
             * =================================================
             */

            const scaledBox =
              new THREE.Box3()
                .setFromObject(
                  model
                );


            const scaledSize =
              scaledBox.getSize(
                new THREE.Vector3()
              );


            const scaledCenter =
              scaledBox.getCenter(
                new THREE.Vector3()
              );


            console.log(
              'Scaled model bounds:',
              scaledBox
            );


            console.log(
              'Scaled model size:',
              scaledSize
            );


            console.log(
              'Scaled model center:',
              scaledCenter
            );


            /*
             * =================================================
             * CRITICAL GROUNDING FIX
             * =================================================
             *
             * DO NOT center the model vertically.
             *
             * Instead:
             *
             * bottom of model
             *       ↓
             *       ↓
             * groundY
             *
             * This makes the reconstructed terrain
             * physically sit on the ground.
             */

            const bottomY =
              scaledBox.min.y;


            const verticalOffset =
              groundYRef.current -
              bottomY;


            model.position.y +=
              verticalOffset;


            /*
             * =================================================
             * CENTER MODEL HORIZONTALLY
             * =================================================
             *
             * We only center X and Z.
             *
             * We intentionally DO NOT center Y.
             */

            const horizontalOffsetX =
              -scaledCenter.x;


            const horizontalOffsetZ =
              -scaledCenter.z;


            model.position.x +=
              horizontalOffsetX;


            model.position.z +=
              horizontalOffsetZ;


            /*
             * Update matrices again.
             */

            model.updateMatrixWorld(
              true
            );


            /*
             * =================================================
             * FINAL BOUNDS
             * =================================================
             */

            const finalBox =
              new THREE.Box3()
                .setFromObject(
                  model
                );


            const finalSize =
              finalBox.getSize(
                new THREE.Vector3()
              );


            const finalCenter =
              finalBox.getCenter(
                new THREE.Vector3()
              );


            console.log(
              'FINAL MODEL BOUNDS:',
              finalBox
            );


            console.log(
              'FINAL MODEL SIZE:',
              finalSize
            );


            console.log(
              'FINAL MODEL CENTER:',
              finalCenter
            );


            console.log(
              'FINAL MODEL BOTTOM Y:',
              finalBox.min.y
            );


            console.log(
              'GROUND Y:',
              groundYRef.current
            );


            /*
             * =================================================
             * GROUNDING VALIDATION
             * =================================================
             */

            const groundingError =
              Math.abs(
                finalBox.min.y -
                groundYRef.current
              );


            console.log(
              'GROUNDING ERROR:',
              groundingError
            );


            /*
             * If there is a tiny floating/
             * penetrating error caused by
             * floating point precision,
             * correct it.
             */

            if (
              groundingError >
              0.000001
            ) {

              model.position.y +=
                groundYRef.current -
                finalBox.min.y;

            }


            /*
             * Update matrix.
             */

            model.updateMatrixWorld(
              true
            );


            /*
             * =================================================
             * ADD MODEL
             * =================================================
             */

            modelGroup.add(
              model
            );


            /*
             * =================================================
             * FINAL FINAL BOUNDS
             * =================================================
             */

            const groundedBox =
              new THREE.Box3()
                .setFromObject(
                  model
                );


            const groundedCenter =
              groundedBox.getCenter(
                new THREE.Vector3()
              );


            const groundedSize =
              groundedBox.getSize(
                new THREE.Vector3()
              );


            console.log(
              'GROUNDED MODEL:',
              groundedBox
            );


            console.log(
              'GROUNDED MODEL BOTTOM:',
              groundedBox.min.y
            );


            console.log(
              'GROUND:',
              groundYRef.current
            );


            /*
             * =================================================
             * CAMERA TARGET
             * =================================================
             *
             * Look slightly above the center
             * of the reconstructed scene.
             */

            const cameraTarget =
              groundedCenter.clone();


            /*
             * Move target upward slightly.
             *
             * This gives a more natural
             * aerial inspection view.
             */

            cameraTarget.y +=
              groundedSize.y * 0.05;


            cameraTargetRef.current.copy(
              cameraTarget
            );


            /*
             * =================================================
             * CAMERA FIT
             * =================================================
             */

            const maxFinalDimension =
              Math.max(
                groundedSize.x,
                groundedSize.y,
                groundedSize.z
              );


            const radius =
              Math.max(
                maxFinalDimension * 0.5,
                0.5
              );


            const fovRadians =
              THREE.MathUtils.degToRad(
                camera.fov
              );


            const cameraDistance =
              radius /
              Math.tan(
                fovRadians / 2
              );


            /*
             * Add comfortable space around
             * the reconstruction.
             */

            const distance =
              Math.max(
                cameraDistance * 1.7,
                4
              );


            /*
             * =================================================
             * CAMERA POSITION
             * =================================================
             */

            const fittedCameraPosition =
              new THREE.Vector3(
                distance,
                distance * 0.65,
                distance
              );


            initialCameraPosRef.current.copy(
              fittedCameraPosition
            );


            camera.position.copy(
              fittedCameraPosition
            );


            camera.lookAt(
              cameraTarget
            );


            /*
             * =================================================
             * CAMERA CLIPPING
             * =================================================
             */

            camera.near =
              Math.max(
                0.001,
                distance / 10000
              );


            camera.far =
              Math.max(
                1000,
                distance * 100
              );


            camera.updateProjectionMatrix();


            /*
             * =================================================
             * RESET ROTATION
             * =================================================
             */

            modelGroup.rotation.set(
              0,
              0,
              0
            );


            /*
             * =================================================
             * IMPORTANT:
             * SAVE THE GROUND-BASED MODEL PIVOT
             * =================================================
             *
             * The model is now positioned correctly.
             *
             * The model group rotates around its
             * center by default, which can visually
             * make the terrain appear disconnected
             * from the ground.
             *
             * Therefore automatic rotation is disabled
             * for now.
             *
             * User-controlled rotation is still available.
             * =================================================
             */

            console.log(
              '3D MODEL SUCCESSFULLY GROUNDED.'
            );


            console.log(
              'Model bottom should equal ground Y:',
              groundedBox.min.y,
              groundYRef.current
            );


            /*
             * =================================================
             * FINISHED
             * =================================================
             */

            setIsLoading(
              false
            );


            onModelLoadedRef.current?.();

          },


          /*
           * ===================================================
           * PROGRESS
           * ===================================================
           */

          (progress) => {

            if (
              progress.total &&
              progress.total > 0
            ) {

              const percent =
                (
                  progress.loaded /
                  progress.total
                ) *
                100;


              console.log(
                `GLB loading: ${percent.toFixed(
                  1
                )}%`
              );

            } else {

              console.log(
                `GLB loading: ${(
                  progress.loaded /
                  1024 /
                  1024
                ).toFixed(
                  1
                )} MB`
              );

            }

          },


          /*
           * ===================================================
           * ERROR
           * ===================================================
           */

          (error) => {

            if (cancelled) {
              return;
            }


            console.error(
              'Failed to load GLB:',
              error
            );


            setIsLoading(
              false
            );


            const loadError =
              error instanceof Error
                ? error
                : new Error(
                    'Failed to load the 3D GLB model.'
                  );


            onModelLoadErrorRef.current?.(
              loadError
            );

          }

        );

      };


    loadModel();


    /*
     * =======================================================
     * ANIMATION LOOP
     * =======================================================
     */

    let animationFrameId =
      0;


    const animate =
      () => {

        if (cancelled) {
          return;
        }


        animationFrameId =
          window.requestAnimationFrame(
            animate
          );


        /*
         * IMPORTANT:
         *
         * Automatic rotation is intentionally
         * disabled.
         *
         * The reconstructed terrain should
         * remain grounded.
         *
         * Rotation is controlled by the user.
         */


        renderer.render(
          scene,
          camera
        );

      };


    animate();


    /*
     * =======================================================
     * RESIZE
     * =======================================================
     */

    const resizeObserver =
      new ResizeObserver(
        (entries) => {

          for (
            const entry of entries
          ) {

            const newWidth =
              entry.contentRect.width;


            const newHeight =
              entry.contentRect.height;


            if (
              newWidth <= 0 ||
              newHeight <= 0
            ) {

              continue;

            }


            camera.aspect =
              newWidth /
              newHeight;


            camera.updateProjectionMatrix();


            renderer.setSize(
              newWidth,
              newHeight,
              false
            );

          }

        }
      );


    resizeObserver.observe(
      container
    );


    /*
     * =======================================================
     * CLEANUP
     * =======================================================
     */

    return () => {

      cancelled =
        true;


      window.cancelAnimationFrame(
        animationFrameId
      );


      resizeObserver.disconnect();


      /*
       * Dispose renderer.
       */

      renderer.dispose();


      /*
       * Dispose ground.
       */

      groundGeometry.dispose();

      groundMaterial.dispose();


      /*
       * Dispose model.
       */

      modelGroup.traverse(
        (object) => {

          const mesh =
            object as THREE.Mesh;


          if (
            mesh.geometry
          ) {

            mesh.geometry.dispose();

          }


          if (
            mesh.material
          ) {

            if (
              Array.isArray(
                mesh.material
              )
            ) {

              mesh.material.forEach(
                (material) => {

                  material.dispose();

                }
              );

            } else {

              mesh.material.dispose();

            }

          }

        }
      );


      sceneRef.current =
        null;

      cameraRef.current =
        null;

      rendererRef.current =
        null;

      modelGroupRef.current =
        null;

    };

  }, [
    modelUrl,
  ]);

  useEffect(() => {
    if (cameraRef.current) {
      cameraRef.current.fov = fov;
      cameraRef.current.updateProjectionMatrix();
    }
  }, [fov]);


  /*
   * =========================================================
   * POINTER DOWN
   * =========================================================
   */

  const handlePointerDown = (
    event: React.PointerEvent<HTMLCanvasElement>
  ) => {

    isDraggingRef.current =
      true;


    previousMousePositionRef.current = {
      x: event.clientX,
      y: event.clientY,
    };


    event.currentTarget.setPointerCapture(
      event.pointerId
    );

  };


  /*
   * =========================================================
   * POINTER MOVE
   * =========================================================
   */

  const handlePointerMove = (
    event: React.PointerEvent<HTMLCanvasElement>
  ) => {

    if (
      !isDraggingRef.current ||
      !modelGroupRef.current ||
      !cameraRef.current
    ) {

      return;

    }


    const deltaX =
      event.clientX -
      previousMousePositionRef.current.x;


    const deltaY =
      event.clientY -
      previousMousePositionRef.current.y;


    /*
     * =======================================================
     * ROTATE
     * =======================================================
     */

    if (
      activeTool ===
      'rotate'
    ) {

      modelGroupRef.current.rotation.y +=
        deltaX * 0.008;


      modelGroupRef.current.rotation.x +=
        deltaY * 0.008;

    }


    /*
     * =======================================================
     * PAN
     * =======================================================
     */

    if (
      activeTool ===
      'pan'
    ) {

      const camera =
        cameraRef.current;


      const panSpeed =
        0.01;


      camera.position.x -=
        deltaX *
        panSpeed;


      camera.position.y +=
        deltaY *
        panSpeed;

    }


    /*
     * =======================================================
     * ZOOM
     * =======================================================
     */

    if (
      activeTool ===
      'zoom'
    ) {

      handleZoom(
        deltaY * 0.05
      );

    }


    previousMousePositionRef.current = {
      x: event.clientX,
      y: event.clientY,
    };

  };


  /*
   * =========================================================
   * POINTER UP
   * =========================================================
   */

  const handlePointerUp = (
    event: React.PointerEvent<HTMLCanvasElement>
  ) => {

    isDraggingRef.current =
      false;


    try {

      event.currentTarget.releasePointerCapture(
        event.pointerId
      );

    } catch {

      /*
       * Pointer capture may already
       * have been released.
       */

    }

  };


  /*
   * =========================================================
   * WHEEL
   * =========================================================
   */

  const handleWheel = (
    event: React.WheelEvent<HTMLCanvasElement>
  ) => {

    event.preventDefault();


    handleZoom(
      event.deltaY * -0.01
    );

  };


  /*
   * =========================================================
   * RENDER
   * =========================================================
   */

  return (

    <div
      ref={containerRef}
      className={`relative w-full h-full bg-[#020617] overflow-hidden select-none ${className}`}
    >

      {/* ===================================================
          HUD
          =================================================== */}

      <div className="absolute top-0 left-0 w-full p-3 flex justify-between items-start z-10 pointer-events-none">

        <div className="bg-[#101415]/80 backdrop-blur-sm border border-[#1E293B] rounded px-3 py-1.5 font-mono text-[12px] leading-[18px] text-[#c3c6d7] shadow-md">

          CAM: [PERSPECTIVE] FOV:{' '}
          {fov}°

        </div>


        <div className="bg-[#101415]/80 backdrop-blur-sm border border-[#1E293B] rounded px-3 py-1.5 font-mono text-[12px] leading-[18px] text-[#c3c6d7] flex items-center gap-2 shadow-md">

          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />

          3D MODEL LOADED

        </div>

      </div>


      {/* ===================================================
          CANVAS
          =================================================== */}

      <canvas
        ref={canvasRef}

        onPointerDown={
          handlePointerDown
        }

        onPointerMove={
          handlePointerMove
        }

        onPointerUp={
          handlePointerUp
        }

        onPointerCancel={
          handlePointerUp
        }

        onWheel={
          handleWheel
        }

        className="w-full h-full cursor-grab active:cursor-grabbing block"
      />


      {/* ===================================================
          LOADING
          =================================================== */}

      {isLoading && (

        <div className="absolute inset-0 flex items-center justify-center bg-[#020617]/85 backdrop-blur-sm z-20">

          <div className="flex flex-col items-center gap-3">

            <div className="w-12 h-12 rounded-full border-2 border-[#323537] border-t-[#2563EB] animate-spin" />

            <span className="text-[12px] font-medium tracking-widest text-[#e0e3e5] uppercase">

              Loading 3D Model

            </span>

            <span className="text-[10px] text-[#8d90a0] font-mono">

              {modelUrl
                ? 'Backend GLB'
                : 'video_model.glb'}

            </span>

          </div>

        </div>

      )}


      {/* ===================================================
          TOOLBAR
          =================================================== */}

      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1 bg-[#101415]/85 backdrop-blur-sm border border-[#1E293B] p-1.5 rounded-lg z-10 shadow-xl">

        {/* ROTATE */}

        <button
          onClick={() =>
            setActiveTool(
              'rotate'
            )
          }

          className={`p-1.5 rounded transition-colors cursor-pointer ${
            activeTool ===
            'rotate'
              ? 'bg-[#2563EB] text-white'
              : 'text-[#c3c6d7] hover:text-[#e0e3e5] hover:bg-[#1d2022]'
          }`}

          title="Rotate"
        >

          <span className="material-symbols-outlined text-[20px]">

            360

          </span>

        </button>


        {/* PAN */}

        <button
          onClick={() =>
            setActiveTool(
              'pan'
            )
          }

          className={`p-1.5 rounded transition-colors cursor-pointer ${
            activeTool ===
            'pan'
              ? 'bg-[#2563EB] text-white'
              : 'text-[#c3c6d7] hover:text-[#e0e3e5] hover:bg-[#1d2022]'
          }`}

          title="Pan"
        >

          <span className="material-symbols-outlined text-[20px]">

            pan_tool

          </span>

        </button>


        {/* ZOOM IN */}

        <button
          onClick={() =>
            handleZoom(-1)
          }

          className="p-1.5 text-[#c3c6d7] hover:text-[#e0e3e5] hover:bg-[#1d2022] rounded transition-colors cursor-pointer"

          title="Zoom In"
        >

          <span className="material-symbols-outlined text-[20px]">

            zoom_in

          </span>

        </button>


        {/* ZOOM OUT */}

        <button
          onClick={() =>
            handleZoom(1)
          }

          className="p-1.5 text-[#c3c6d7] hover:text-[#e0e3e5] hover:bg-[#1d2022] rounded transition-colors cursor-pointer"

          title="Zoom Out"
        >

          <span className="material-symbols-outlined text-[20px]">

            zoom_out

          </span>

        </button>


        <div className="w-[1px] h-5 bg-[#323537] mx-1" />


        {/* RESET */}

        <button
          onClick={
            handleResetCamera
          }

          className="p-1.5 text-[#c3c6d7] hover:text-[#e0e3e5] hover:bg-[#1d2022] rounded transition-colors cursor-pointer"

          title="Reset Camera"
        >

          <span className="material-symbols-outlined text-[20px]">

            center_focus_strong

          </span>

        </button>


        {/* FULLSCREEN */}

        <button
          onClick={
            handleToggleFullscreen
          }

          className="p-1.5 text-[#c3c6d7] hover:text-[#e0e3e5] hover:bg-[#1d2022] rounded transition-colors cursor-pointer"

          title={
            isFullscreen
              ? 'Exit Fullscreen'
              : 'Fullscreen'
          }
        >

          <span className="material-symbols-outlined text-[20px]">

            {isFullscreen
              ? 'fullscreen_exit'
              : 'fullscreen'}

          </span>

        </button>

      </div>

    </div>

  );

};
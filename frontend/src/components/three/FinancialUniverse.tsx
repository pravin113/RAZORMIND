import React, { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface FinancialUniverseProps {
  stage: number; // 0 to 9 representing the 10 stages
}

export const FinancialUniverse: React.FC<FinancialUniverseProps> = ({ stage }) => {
  const pointsRef = useRef<THREE.Points>(null!);
  const centralCoreRef = useRef<THREE.Mesh>(null!);
  const transactionRef = useRef<THREE.Group>(null!);
  const gateRef = useRef<THREE.Group>(null!);

  // Mobile / desktop dynamic particle count
  const isMobile = typeof window !== "undefined" && window.innerWidth < 768;
  const particleCount = isMobile ? 250 : 800;

  // Generate particle coordinates, colors, and velocities
  const [positions, originalPositions, colors] = useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    const origPos = new Float32Array(particleCount * 3);
    const cols = new Float32Array(particleCount * 3);

    const cyan = new THREE.Color("#00E5FF");
    const blue = new THREE.Color("#2979FF");

    for (let i = 0; i < particleCount; i++) {
      // Cylindrical flow field
      const theta = Math.random() * Math.PI * 2;
      const radius = 2 + Math.random() * 8;
      const x = Math.cos(theta) * radius;
      const y = (Math.random() - 0.5) * 12;
      const z = Math.sin(theta) * radius;

      pos[i * 3] = x;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = z;

      origPos[i * 3] = x;
      origPos[i * 3 + 1] = y;
      origPos[i * 3 + 2] = z;

      // Blend cyan and blue
      const c = Math.random() > 0.4 ? cyan : blue;
      cols[i * 3] = c.r;
      cols[i * 3 + 1] = c.g;
      cols[i * 3 + 2] = c.b;
    }

    return [pos, origPos, cols];
  }, [particleCount]);

  useFrame((state, delta) => {
    if (!pointsRef.current) return;

    const time = state.clock.getElapsedTime();
    const positionAttr = pointsRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const colorAttr = pointsRef.current.geometry.attributes.color as THREE.BufferAttribute;

    const redColor = new THREE.Color("#FF1744");
    const greenColor = new THREE.Color("#00E676");
    const cyanColor = new THREE.Color("#00E5FF");

    // Dynamic animation per stage
    for (let i = 0; i < particleCount; i++) {
      const idx = i * 3;
      const origX = originalPositions[idx];
      const origY = originalPositions[idx + 1];
      const origZ = originalPositions[idx + 2];

      if (stage === 0) {
        // Stage 0: Contracting into central seed
        positionAttr.array[idx] = THREE.MathUtils.lerp(positionAttr.array[idx], origX * 0.15, 0.05);
        positionAttr.array[idx + 1] = THREE.MathUtils.lerp(positionAttr.array[idx + 1], origY * 0.15, 0.05);
        positionAttr.array[idx + 2] = THREE.MathUtils.lerp(positionAttr.array[idx + 2], origZ * 0.15, 0.05);
      } else if (stage === 4 || stage === 5) {
        // Stage 4-5: Pull into AI vortex core
        const targetX = Math.cos(time * 2 + i) * 1.5;
        const targetZ = Math.sin(time * 2 + i) * 1.5;
        positionAttr.array[idx] = THREE.MathUtils.lerp(positionAttr.array[idx], targetX, 0.04);
        positionAttr.array[idx + 1] = THREE.MathUtils.lerp(positionAttr.array[idx + 1], Math.sin(time + i) * 1.2, 0.04);
        positionAttr.array[idx + 2] = THREE.MathUtils.lerp(positionAttr.array[idx + 2], targetZ, 0.04);
      } else if (stage === 7 || stage === 8) {
        // Stage 7-8: Stream through policy gate
        positionAttr.array[idx + 1] = origY + Math.sin(time * 3 + origX) * 0.8;
        positionAttr.array[idx + 2] = (origZ + time * 3) % 12 - 6;

        // Color transition to emerald on recovery
        if (stage === 8 && i % 3 === 0) {
          colorAttr.array[idx] = greenColor.r;
          colorAttr.array[idx + 1] = greenColor.g;
          colorAttr.array[idx + 2] = greenColor.b;
        }
      } else {
        // Normal gentle flow
        positionAttr.array[idx] = origX + Math.sin(time + origY) * 0.3;
        positionAttr.array[idx + 1] = origY + Math.cos(time * 0.8 + origX) * 0.3;
        positionAttr.array[idx + 2] = origZ + Math.sin(time * 0.5 + i) * 0.2;

        if (stage === 3 && i < particleCount * 0.4) {
          // Failure stage turning red
          colorAttr.array[idx] = redColor.r;
          colorAttr.array[idx + 1] = redColor.g;
          colorAttr.array[idx + 2] = redColor.b;
        } else if (stage < 3) {
          colorAttr.array[idx] = cyanColor.r;
          colorAttr.array[idx + 1] = cyanColor.g;
          colorAttr.array[idx + 2] = cyanColor.b;
        }
      }
    }

    positionAttr.needsUpdate = true;
    colorAttr.needsUpdate = true;

    // Rotate the overall particle sphere
    pointsRef.current.rotation.y += delta * 0.12;

    // Central core pulsing
    if (centralCoreRef.current) {
      const scale = 1 + Math.sin(time * 3) * 0.15;
      centralCoreRef.current.scale.set(scale, scale, scale);
      centralCoreRef.current.rotation.y += delta * 0.5;
      centralCoreRef.current.rotation.x += delta * 0.2;
    }

    // Policy Gate rotation
    if (gateRef.current) {
      gateRef.current.rotation.z += delta * 0.3;
      gateRef.current.rotation.y = Math.sin(time * 0.5) * 0.2;
    }
  });

  return (
    <group>
      {/* Central AI / Financial Seed Core */}
      <mesh ref={centralCoreRef} position={[0, 0, 0]}>
        <octahedronGeometry args={[stage >= 4 ? 0.9 : 0.4, 0]} />
        <meshBasicMaterial
          color={
            stage >= 8
              ? "#00E676"
              : stage === 3 || stage === 4
              ? "#FF1744"
              : "#00E5FF"
          }
          wireframe
        />
      </mesh>

      {/* Primary Particle Streams */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={particleCount}
            array={positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={particleCount}
            array={colors}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={isMobile ? 0.08 : 0.06}
          vertexColors
          transparent
          opacity={0.85}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Isolated Transaction Node (Stage 2-3) */}
      {(stage === 2 || stage === 3) && (
        <group ref={transactionRef} position={[0, 0, 2]}>
          <mesh>
            <sphereGeometry args={[0.3, 16, 16]} />
            <meshBasicMaterial
              color={stage === 3 ? "#FF1744" : "#00E5FF"}
              wireframe
            />
          </mesh>
        </group>
      )}

      {/* 3D Policy Gate (Stage 6-7) */}
      {(stage === 6 || stage === 7) && (
        <group ref={gateRef} position={[0, 0, 1]}>
          <mesh>
            <torusGeometry args={[2.2, 0.04, 16, 64]} />
            <meshBasicMaterial
              color={stage === 7 ? "#00E676" : "#00E5FF"}
              transparent
              opacity={0.8}
            />
          </mesh>
          <mesh rotation={[0, 0, Math.PI / 4]}>
            <torusGeometry args={[1.8, 0.03, 16, 64]} />
            <meshBasicMaterial
              color={stage === 7 ? "#00E676" : "#2979FF"}
              transparent
              opacity={0.5}
            />
          </mesh>
        </group>
      )}
    </group>
  );
};

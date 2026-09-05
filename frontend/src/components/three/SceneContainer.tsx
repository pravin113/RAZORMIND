import React, { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { FinancialUniverse } from "./FinancialUniverse";

interface SceneContainerProps {
  stage: number;
}

export const SceneContainer: React.FC<SceneContainerProps> = ({ stage }) => {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
      <Canvas
        camera={{ position: [0, 0, 7], fov: 45 }}
        dpr={[1, 1.5]} // Clamped DPR for guaranteed smooth frame rate
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <ambientLight intensity={0.5} />
        <Suspense fallback={null}>
          <FinancialUniverse stage={stage} />
        </Suspense>
      </Canvas>
    </div>
  );
};

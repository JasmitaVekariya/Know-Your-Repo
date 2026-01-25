import React from 'react';
import { Particles } from './ui/particles';

const ParticleBackground = () => {
    return (
        <div className="fixed inset-0 -z-10 w-full h-full bg-black overflow-hidden pointer-events-none">
            <Particles
                className="absolute inset-0"
                quantity={120}
                staticity={50}
                ease={20}
                size={0.4}
                color="#666666"
                vx={0}
                vy={0}
            />
            {/* Radial Gradient overlays from MinimalAuthPage */}
            <div aria-hidden className="absolute inset-0 isolate -z-10 contain-strict opacity-70">
                <div className="bg-[radial-gradient(68.54%_68.72%_at_55.02%_31.46%,hsla(0,0%,85%,.06)_0,hsla(0,0%,55%,.02)_50%,hsla(0,0%,85%,.01)_80%)] absolute top-0 left-0 h-[80rem] w-[35rem] -translate-y-[21.875rem] -rotate-45 rounded-full" />
                <div className="bg-[radial-gradient(50%_50%_at_50%_50%,hsla(0,0%,85%,.04)_0,hsla(0,0%,85%,.01)_80%,transparent_100%)] absolute top-0 left-0 h-[80rem] w-[15rem] translate-x-[5%] -translate-y-[50%] -rotate-45 rounded-full" />
                <div className="bg-[radial-gradient(50%_50%_at_50%_50%,hsla(0,0%,85%,.04)_0,hsla(0,0%,85%,.01)_80%,transparent_100%)] absolute top-0 left-0 h-[80rem] w-[15rem] -translate-y-[21.875rem] -rotate-45 rounded-full" />
            </div>
        </div>
    );
};

export default ParticleBackground;

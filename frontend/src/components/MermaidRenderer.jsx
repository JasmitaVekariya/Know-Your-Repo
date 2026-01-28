import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

const MermaidRenderer = ({ chart }) => {
    const [svg, setSvg] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        // Initialize mermaid with enhanced configuration
        mermaid.initialize({
            startOnLoad: false,
            suppressErrorRendering: true, // CRITICAL: Tell Mermaid not to render error diagrams
            theme: 'base',
            themeVariables: {
                primaryColor: '#4F46E5',
                primaryTextColor: '#fff',
                primaryBorderColor: '#4338CA',
                lineColor: '#6366F1',
                secondaryColor: '#10B981',
                tertiaryColor: '#F59E0B',
                background: '#1F2937',
                mainBkg: '#4F46E5',
                secondBkg: '#10B981',
                tertiaryBkg: '#F59E0B',
                nodeBorder: '#4338CA',
                clusterBkg: '#374151',
                clusterBorder: '#6B7280',
                titleColor: '#F3F4F6',
                edgeLabelBackground: '#1F2937',
                nodeTextColor: '#ffffff'
            },
            securityLevel: 'loose',
            fontFamily: 'Inter, system-ui, sans-serif',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis',
                padding: 20,
                nodeSpacing: 50,
                rankSpacing: 50
            }
        });

        const renderDiagram = async () => {
            if (!chart) return;

            // PRE-VALIDATION: Aggressively fail bad syntax before Mermaid sees it
            // This prevents the "Parse error" causing UI glitches
            if (chart.includes("['") || chart.includes("']") || chart.includes('["') || chart.includes('"]')) {
                setError("Invalid syntax detected");
                return;
            }
            if (chart.includes("[image][url]")) {
                setError("Invalid syntax detected");
                return;
            }

            try {
                // Generate unique ID for this diagram
                const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;

                // Suppress Mermaid console errors
                const originalConsoleError = console.error;
                console.error = () => { }; // Temporarily disable console.error

                // Render the diagram
                // Note: We use a try-catch block specifically around render
                const { svg: renderedSvg } = await mermaid.render(id, chart);

                // Restore console.error
                console.error = originalConsoleError;

                if (renderedSvg) {
                    setSvg(renderedSvg);
                    setError(null);
                } else {
                    setError("No SVG generated");
                }
            } catch (err) {
                // Restore console.error if it was suppressed
                console.error = console.error || (() => { });
                setError(err.message || 'Failed to render diagram');
            }
        };

        renderDiagram();
    }, [chart]);

    // ABSOLUTE ZERO HEIGHT ON ERROR
    if (error || !svg) {
        return null;
    }

    return (
        <div
            className="mermaid-diagram my-4 flex justify-center"
            dangerouslySetInnerHTML={{ __html: svg }}
        />
    );
};

// Optimization: Prevent re-renders if chart content hasn't changed
export default React.memo(MermaidRenderer);

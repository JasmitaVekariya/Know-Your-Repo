import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

const MermaidRenderer = ({ chart }) => {
    const elementRef = useRef(null);
    const [svg, setSvg] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        // Initialize mermaid with enhanced configuration
        mermaid.initialize({
            startOnLoad: false,
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

            try {
                // Generate unique ID for this diagram
                const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;

                // Suppress Mermaid console errors
                const originalConsoleError = console.error;
                console.error = () => { }; // Temporarily disable console.error

                // Render the diagram
                const { svg: renderedSvg } = await mermaid.render(id, chart);

                // Restore console.error
                console.error = originalConsoleError;

                setSvg(renderedSvg);
                setError(null);
            } catch (err) {
                // Restore console.error if it was suppressed
                console.error = console.error || (() => { });

                // Only log to console in development
                if (process.env.NODE_ENV === 'development') {
                    console.warn('Mermaid rendering error:', err);
                }

                setError(err.message || 'Failed to render diagram');
            }
        };

        renderDiagram();
    }, [chart]);

    if (error) {
        // Silently fail - don't show error messages to user
        // Backend validation should have caught this, but if it didn't, just hide it
        return null;
    }

    if (!svg) {
        return null;
    }

    return (
        <div
            className="mermaid-diagram my-4 flex justify-center"
            dangerouslySetInnerHTML={{ __html: svg }}
        />
    );
};

export default MermaidRenderer;

import React from 'react';
import { CheckCircle, Circle, ArrowRight, BookOpen } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import CodeBlock from '../components/CodeBlock';

const MindMapPanel = ({ mindMap, currentStepIndex, onNext, onStepClick, onRetry, processingNext }) => {
    if (!mindMap || mindMap.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 p-8">
                <BookOpen className="w-12 h-12 mb-4 opacity-50" />
                <p>Generating curriculum...</p>
            </div>
        );
    }

    const currentStep = mindMap[currentStepIndex];

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-800">
                <h2 className="text-lg font-bold text-gray-800 dark:text-gray-100 flex items-center">
                    <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
                    Learning Path
                </h2>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-3">
                    <div
                        className="bg-blue-600 h-1.5 rounded-full transition-all duration-500"
                        style={{ width: `${((currentStepIndex + 1) / mindMap.length) * 100}%` }}
                    ></div>
                </div>
            </div>

            <div className="flex-1 overflow-hidden flex">
                {/* Step List (Sidebar of Sidebar) */}
                <div className="w-16 flex-shrink-0 bg-gray-50 dark:bg-gray-950 overflow-y-auto border-r border-gray-100 dark:border-gray-800 flex flex-col items-center py-4 space-y-4">
                    {mindMap.map((step, idx) => {
                        // Progressive Disclosure:
                        // Show if:
                        // 1. Step has content (already generated/unlocked)
                        // 2. Step is the current one (active)
                        // 3. Step is the next one being generated (processingNext)
                        // 4. Step is previous to current (history) - implicit in logic usually, but let's be explicit:
                        //    Actually, we want to show everything up to the "furthest reached".

                        const hasContent = step.content && step.content.length > 0;
                        const isReachable = idx <= currentStepIndex || hasContent; // processingNext step remains hidden until transition completes

                        if (!isReachable) return null;

                        const isCompleted = idx < currentStepIndex;
                        const isCurrent = idx === currentStepIndex;

                        return (
                            <button
                                key={step.step_id || idx}
                                onClick={() => onStepClick(idx)}
                                className={`group relative flex items-center justify-center w-8 h-8 rounded-full transition-all
                                    ${isCompleted ? 'bg-green-100 text-green-600' :
                                        isCurrent ? 'bg-blue-600 text-white ring-2 ring-blue-200 dark:ring-blue-900' :
                                            'bg-gray-200 dark:bg-gray-800 text-gray-400'}
                                `}
                                title={step.title}
                            >
                                {isCompleted ? <CheckCircle className="w-5 h-5" /> : <span className="text-xs font-bold">{idx + 1}</span>}
                            </button>
                        );
                    })}
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto p-6">
                    <div className="mb-2">
                        <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                            Phase {currentStepIndex + 1} of {mindMap.length}
                        </span>
                        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mt-1 mb-4">
                            {currentStep?.title}
                        </h1>
                    </div>

                    <div className="markdown-body prose prose-lg dark:prose-invert max-w-none">
                        {currentStep?.loading ? (
                            <div className="flex flex-col items-center justify-center p-12 text-center">
                                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                                <p className="text-gray-500 animate-pulse">Generating deep dive analysis for this phase...</p>
                            </div>
                        ) : (
                            <ReactMarkdown
                                components={{
                                    code({ node, inline, className, children, ...props }) {
                                        const match = /language-(\w+)/.exec(className || '');
                                        const content = String(children).replace(/\n$/, '');
                                        const isInline = inline || (!match && content.length < 50 && !content.includes('\n'));

                                        if (!isInline) {
                                            return (
                                                <CodeBlock className={className} {...props}>
                                                    {children}
                                                </CodeBlock>
                                            );
                                        }
                                        return <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-blue-600 dark:text-blue-400 font-mono text-sm font-semibold" {...props}>{children}</code>;
                                    },
                                    p: ({ node, ...props }) => <p className="mb-4 leading-relaxed text-gray-800 dark:text-gray-200" {...props} />,
                                    h2: ({ node, ...props }) => <h2 className="text-xl font-bold mt-6 mb-3 text-gray-900 dark:text-white" {...props} />,
                                    h3: ({ node, ...props }) => <h3 className="text-lg font-bold mt-4 mb-2 text-gray-900 dark:text-white" {...props} />,
                                    ul: ({ node, ...props }) => <ul className="list-disc pl-5 mb-4 space-y-1" {...props} />,
                                    li: ({ node, ...props }) => <li className="text-gray-800 dark:text-gray-300" {...props} />
                                }}
                            >
                                {currentStep?.content || currentStep?.description}
                            </ReactMarkdown>
                        )}

                        {/* Empty State / Retry */}
                        {!currentStep?.loading && !currentStep?.content && (
                            <div className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-xl mt-4">
                                <p className="text-gray-500 dark:text-gray-400 mb-4 text-center">Content not generated yet.</p>
                                <button
                                    onClick={onRetry}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                >
                                    Generate Content
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Footer Action */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 flex justify-end">
                <button
                    onClick={onNext}
                    disabled={currentStepIndex >= mindMap.length - 1 || processingNext}
                    className="flex items-center px-4 py-2 bg-black dark:bg-white text-white dark:text-black rounded-lg hover:opacity-80 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
                >
                    {processingNext ? (
                        <>
                            <div className="w-4 h-4 border-2 border-gray-400 border-t-white dark:border-t-black rounded-full animate-spin mr-2"></div>
                            Analyzing Next Phase...
                        </>
                    ) : (
                        <>
                            {currentStepIndex >= mindMap.length - 1 ? 'Course Completed' : 'Next Phase'}
                            <ArrowRight className="w-4 h-4 ml-2" />
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

export default MindMapPanel;

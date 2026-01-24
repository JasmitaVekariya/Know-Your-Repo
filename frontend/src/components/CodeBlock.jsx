import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeBlock = ({ children, className }) => {
    const [copied, setCopied] = useState(false);

    // Extract language from className (e.g. "language-python")
    const match = /language-(\w+)/.exec(className || '');
    const language = match ? match[1] : 'text';
    const content = String(children).replace(/\n$/, '');

    const handleCopy = () => {
        navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="rounded-lg overflow-hidden my-4 border border-gray-700 bg-[#1e1e1e]">
            {/* Header */}
            <div className="flex justify-between items-center px-4 py-2 bg-[#252526] text-gray-300 text-xs select-none border-b border-gray-700">
                <span className="font-sans uppercase font-semibold text-gray-400">{language}</span>
                <button
                    onClick={handleCopy}
                    className="flex items-center space-x-1 hover:text-white transition-colors focus:outline-none"
                >
                    {copied ? (
                        <>
                            <Check className="w-3 h-3 text-green-400" />
                            <span>Copied!</span>
                        </>
                    ) : (
                        <>
                            <Copy className="w-3 h-3" />
                            <span>Copy</span>
                        </>
                    )}
                </button>
            </div>
            {/* Code content */}
            <div className="text-sm">
                <SyntaxHighlighter
                    language={language}
                    style={vscDarkPlus}
                    customStyle={{
                        margin: 0,
                        padding: '1rem',
                        background: 'transparent',
                        fontSize: '0.9rem',
                        lineHeight: '1.5',
                    }}
                    wrapLongLines={true}
                >
                    {content}
                </SyntaxHighlighter>
            </div>
        </div>
    );
};

export default CodeBlock;

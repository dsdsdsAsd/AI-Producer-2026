import React, { useRef, useEffect, useState, useMemo } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import SpriteText from 'three-spritetext';
import { Loader2, Zap, Info } from 'lucide-react';

export default function KnowledgeGraph() {
    const fgRef = useRef();
    const [data, setData] = useState({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);
    const [selectedNode, setSelectedNode] = useState(null);

    useEffect(() => {
        const fetchGraphData = async () => {
            setLoading(true);
            try {
                // Вызов реального API: /api/knowledge/graph
                const response = await fetch('http://localhost:8000/api/knowledge/graph?limit=150');
                if (!response.ok) throw new Error('Failed to fetch graph data');

                const result = await response.json();

                // Преобразуем данные если нужно (бэкенд уже отдает нужный формат)
                setData(result);
                setLoading(false);
            } catch (error) {
                console.error('Error fetching graph data:', error);
                // Fallback на пустые данные или сообщение об ошибке
                setLoading(false);
            }
        };

        fetchGraphData();
    }, []);

    const graphContent = useMemo(() => (
        <ForceGraph3D
            ref={fgRef}
            graphData={data}
            nodeLabel="name"
            nodeColor={node => node.color || '#fff'}
            nodeVal={node => node.val || 1}
            linkThreeObjectExtend={true}
            linkOpacity={0.3}
            linkWidth={1}
            backgroundColor="#0a0a0a"
            onNodeClick={node => {
                setSelectedNode(node);
                // Фокус на ноде
                if (fgRef.current) {
                    const distance = 40;
                    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
                    fgRef.current.cameraPosition(
                        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
                        node,
                        3000
                    );
                }
            }}
            nodeThreeObject={node => {
                const sprite = new SpriteText(node.name);
                sprite.color = node.color || '#fff';
                sprite.textHeight = 4;
                sprite.padding = [2, 1];
                sprite.backgroundColor = 'rgba(0,0,0,0.5)';
                sprite.borderRadius = 2;
                return sprite;
            }}
        />
    ), [data]);

    return (
        <div className="relative w-full h-full bg-[#0a0a0a]">
            {loading && (
                <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm">
                    <Loader2 className="animate-spin text-purple-500 mb-4" size={48} />
                    <p className="text-purple-400 font-medium animate-pulse">Инициализация 3D нейросети знаний...</p>
                </div>
            )}

            {/* UI Overlay */}
            <div className="absolute top-8 left-8 z-10 pointer-events-none">
                <div className="flex items-center gap-4 mb-2">
                    <div className="w-10 h-10 bg-gradient-to-tr from-purple-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-900/20 pointer-events-auto">
                        <Zap size={20} className="text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white uppercase tracking-tighter">Корреляции Знаний</h1>
                        <p className="text-textMuted text-xs font-mono uppercase">Data Source: Velizhanin Transcripts</p>
                    </div>
                </div>
            </div>

            {/* Info Panel */}
            {selectedNode && (
                <div className="absolute bottom-8 right-8 z-10 w-80 bg-surface/80 backdrop-blur-xl border border-white/10 p-6 rounded-3xl shadow-2xl animate-in fade-in slide-in-from-right-4">
                    <div className="flex items-start justify-between mb-4">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <Info size={18} className="text-blue-400" />
                            {selectedNode.name}
                        </h2>
                        <button
                            onClick={() => setSelectedNode(null)}
                            className="text-textMuted hover:text-white transition-colors"
                        >
                            ×
                        </button>
                    </div>
                    <p className="text-sm text-textMuted leading-relaxed mb-4">
                        {selectedNode.content}
                    </p>
                    <div className="bg-white/5 rounded-2xl p-4 border border-white/5">
                        <span className="text-[10px] font-bold text-blue-400 uppercase mb-2 block tracking-widest">Статус в базе</span>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                            <span className="text-white text-xs font-medium">Активный узел (RAG Ready)</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Graph Controls Legend */}
            <div className="absolute bottom-8 left-8 z-10 p-4 bg-black/40 border border-white/5 rounded-2xl backdrop-blur-sm text-[10px] text-textMuted font-mono">
                [ЛКМ] - Вращение | [ПКМ] - Панорама | [Scroll] - Зум | [Click Node] - Фокус
            </div>

            {graphContent}
        </div>
    );
}

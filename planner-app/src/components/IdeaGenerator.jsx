import React, { useState } from 'react';
import { Sparkles, Send, Loader2, Video, Target, Zap } from 'lucide-react';

export default function IdeaGenerator() {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [focus, setFocus] = useState('viral_shorts');
    const [loading, setLoading] = useState(false);
    const [scouting, setScouting] = useState(false);
    const [result, setResult] = useState(null);
    const [candidates, setCandidates] = useState([]);

    const handleTrendHunt = async () => {
        setScouting(true);
        setCandidates([]);
        try {
            const response = await fetch('http://localhost:8000/api/trend-ideas', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer local-dev-token'
                },
                body: JSON.stringify({ topic: focus })
            });
            if (!response.ok) throw new Error('Ошибка поиска');
            const data = await response.json();
            setCandidates(data.ideas);
        } catch (error) {
            console.error('Trend hunt error:', error);
            alert('Не удалось найти тренды. Проверь backend.');
        } finally {
            setScouting(false);
        }
    };

    const selectCandidate = (cand) => {
        setTitle(cand.title);
        setContent(cand.description);
        setCandidates([]);
    };

    const handleEnhance = async (e) => {
        if (e) e.preventDefault();
        setLoading(true);
        setResult(null);

        try {
            const response = await fetch('http://localhost:8000/api/enhance-idea', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer local-dev-token'
                },
                body: JSON.stringify({
                    title,
                    content,
                    focus,
                    persona: 'velizhanin'
                })
            });

            if (!response.ok) throw new Error('Ошибка сервера');

            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error('Enhance error:', error);
            alert('Не удалось связаться с ИИ-мозгом. Проверь, запущен ли backend на порту 8000.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-y-auto">
            <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 bg-gradient-to-tr from-purple-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-900/20">
                    <Sparkles size={24} className="text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-white">Разбор по Велижанину</h1>
                    <p className="text-textMuted text-sm">Использование 394 транскриптов для создания вирусной структуры</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Form Section */}
                <form onSubmit={handleEnhance} className="space-y-6 bg-surface border border-white/5 p-6 rounded-3xl shadow-xl">
                    <div className="flex items-center justify-between mb-2">
                        <label className="block text-sm font-medium text-textMuted">Рабочее название</label>
                        <button
                            type="button"
                            onClick={handleTrendHunt}
                            disabled={scouting}
                            className="text-xs font-bold text-purple-400 hover:text-purple-300 flex items-center gap-1 transition-colors"
                        >
                            {scouting ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                            Найти тренды
                        </button>
                    </div>

                    {candidates.length > 0 && (
                        <div className="space-y-2 mb-4 animate-in fade-in slide-in-from-top-2 duration-300">
                            <p className="text-[10px] uppercase tracking-widest text-textMuted font-bold">Горячие темы (выбери одну):</p>
                            <div className="grid grid-cols-1 gap-2">
                                {candidates.map((cand, idx) => (
                                    <button
                                        key={idx}
                                        type="button"
                                        onClick={() => selectCandidate(cand)}
                                        className="text-left p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 transition-all group"
                                    >
                                        <div className="font-bold text-white text-sm group-hover:text-purple-300">{cand.title}</div>
                                        <div className="text-textMuted text-[11px] line-clamp-1">{cand.description}</div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="space-y-6">
                        <div>
                            <input
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="Название видео..."
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500/50 transition-all font-medium"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-textMuted mb-2">Сырая идея / Боли аудитории</label>
                            <textarea
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                rows={4}
                                placeholder="О чем видео? Какие проблемы оно решает?"
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500/50 transition-all resize-none"
                                required
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-textMuted mb-2">Цель / Фокус</label>
                        <div className="grid grid-cols-2 gap-3">
                            {['viral_shorts', 'educational', 'sales', 'story'].map((f) => (
                                <button
                                    key={f}
                                    type="button"
                                    onClick={() => setFocus(f)}
                                    className={`py-3 px-4 rounded-xl text-sm font-medium border transition-all ${focus === f
                                        ? 'bg-purple-500/20 border-purple-500/50 text-purple-300'
                                        : 'bg-white/5 border-white/10 text-textMuted hover:border-white/20'
                                        }`}
                                >
                                    {f === 'viral_shorts' && 'Виральность'}
                                    {f === 'educational' && 'Польза'}
                                    {f === 'sales' && 'Продажи'}
                                    {f === 'story' && 'История'}
                                </button>
                            ))}
                        </div>
                    </div>

                    <button
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-bold py-4 rounded-2xl shadow-xl shadow-purple-900/40 flex items-center justify-center gap-3 transition-all active:scale-[0.98] disabled:opacity-50"
                    >
                        {loading ? (
                            <Loader2 className="animate-spin" />
                        ) : (
                            <>
                                <Zap size={20} />
                                <span>Разогнать идею</span>
                            </>
                        )}
                    </button>
                </form>

                {/* Result Section */}
                <div className="space-y-6">
                    {!result && !loading && (
                        <div className="h-full flex flex-col items-center justify-center text-center p-12 bg-white/[0.02] border border-dashed border-white/10 rounded-3xl">
                            <Video size={48} className="text-white/10 mb-4" />
                            <p className="text-textMuted">Заполни форму слева,<br />чтобы получить структуру ролика</p>
                        </div>
                    )}

                    {loading && (
                        <div className="h-full flex flex-col items-center justify-center text-center p-12 bg-white/[0.02] border border-white/10 rounded-3xl animate-pulse">
                            <Loader2 size={48} className="text-purple-500/50 animate-spin mb-4" />
                            <p className="text-purple-400/50 font-medium">Мозг Велижанина анализирует базу...</p>
                        </div>
                    )}

                    {result && (
                        <div className="bg-surface border border-white/5 rounded-3xl overflow-hidden shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="bg-gradient-to-r from-purple-600/20 to-blue-600/20 p-6 border-b border-white/5">
                                <span className="text-xs font-bold uppercase tracking-wider text-purple-400 mb-2 block">Рекомендованный заголовок</span>
                                <h3 className="text-xl font-bold text-white leading-tight">{result.suggested_title}</h3>
                            </div>

                            <div className="p-6 space-y-6">
                                <div className="flex gap-4">
                                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500 font-bold">1</div>
                                    <div>
                                        <h4 className="font-bold text-white mb-1">ХУК (0-3 сек)</h4>
                                        <p className="text-textMuted text-sm leading-relaxed">{result.hook}</p>
                                    </div>
                                </div>

                                <div className="flex gap-4">
                                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-500 font-bold">2</div>
                                    <div>
                                        <h4 className="font-bold text-white mb-1">ЦЕННОСТЬ</h4>
                                        <p className="text-textMuted text-sm leading-relaxed">{result.value_proposition}</p>
                                    </div>
                                </div>

                                <div className="flex gap-4">
                                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center text-green-500 font-bold">3</div>
                                    <div>
                                        <h4 className="font-bold text-white mb-1">ПЛАН СЦЕНАРИЯ</h4>
                                        <p className="text-textMuted text-sm leading-relaxed whitespace-pre-wrap">{result.script_outline}</p>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-white/5">
                                    <div className="bg-white/5 p-4 rounded-2xl border border-white/10 flex items-center justify-between">
                                        <div>
                                            <h4 className="text-xs font-bold uppercase text-textMuted mb-1">Призыв к действию (CTA)</h4>
                                            <p className="text-white font-medium">{result.call_to_action}</p>
                                        </div>
                                        <Target className="text-purple-500" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

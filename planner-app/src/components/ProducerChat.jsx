import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, User, Bot, Sparkles } from 'lucide-react';

export default function ProducerChat() {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: 'Привет! Я твой ИИ-Продюсер. Я изучил сотни твоих кейсов и транскриптов. Можем просто поболтать о контенте, или я могу накидать идей на основе того, что мы уже делали. Есть мысли?'
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [showContextPanel, setShowContextPanel] = useState(false);
    const [strategy, setStrategy] = useState(null);
    const [userContext, setUserContext] = useState(
        localStorage.getItem('userContext') ||
        `# ЧЕМ Я ЗАНИМАЮСЬ:
- Мультиагентные ИИ-системы (RAG)
- Голосовые боты для бизнеса
- Компьютерное зрение (YOLOv8)
- Автоматизация процессов

# МОЯ ЦЕЛЬ:
Привлечь топовые компании и учеников через YouTube.`
    );
    const [useContext, setUseContext] = useState(
        localStorage.getItem('useContext') === 'true'
    );
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        const fetchStrategy = async () => {
            try {
                const response = await fetch('http://localhost:8000/planner/strategy');
                const data = await response.json();
                setStrategy(data);

                // Formulate initial auto-context for AI
                const autoCtx = `
# ТВОЕ ПОЗИЦИОНИРОВАНИЕ (Кто я):
${data.positioning || 'Не указано'}

# ТВОЯ АУДИТОРИЯ (ЦА):
${data.target_audience || 'Не указана'}

# БОЛИ КЛИЕНТОВ:
${data.customer_pains || 'Не указаны'}

# ТРИГГЕРЫ:
${data.triggers || 'Не указаны'}
                `.trim();
                setUserContext(autoCtx);
                setUseContext(true); // Always true for strategy sync
            } catch (err) {
                console.error("Strategy Load Error:", err);
            }
        };
        fetchStrategy();
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const suggestions = [
        "Накидай 3 идеи на основе моих кейсов",
        "Как мне улучшить удержание в Shorts?",
        "Какие темы сейчас залетают в AI-нише?",
        "Разбери мой план: Экспертный контент + ИИ"
    ];

    const applySuggestion = (text) => {
        setInput(text);
    };

    const saveContext = () => {
        localStorage.setItem('userContext', userContext);
        localStorage.setItem('useContext', useContext);
        alert('✅ Контекст сохранен!');
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        // Добавляем пользовательский контекст к сообщению, если включен
        const messageToSend = useContext
            ? `${userContext}\n\n---\n\nВОПРОС: ${input}`
            : input;

        const userMessage = { role: 'user', content: input }; // Показываем только вопрос в UI
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/test-rag', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: messageToSend // Отправляем с контекстом
                })
            });

            if (!response.ok) throw new Error('Ошибка связи с бэкендом');

            // Handling SSE manually
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = { role: 'assistant', content: '' };
            setMessages(prev => [...prev, assistantMessage]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'token' && data.content) {
                                assistantMessage.content += data.content;
                                setMessages(prev => {
                                    const newMsgs = [...prev];
                                    newMsgs[newMsgs.length - 1] = { ...assistantMessage };
                                    return newMsgs;
                                });
                            }
                        } catch (e) {
                            // Skip non-json or incomplete json
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Ой, что-то пошло не так. Проверь, запущен ли бэкенд!' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full max-w-4xl mx-auto p-4 md:p-8 relative">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                        <Bot size={20} className="text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white">Чат с Продюсером</h1>
                        <p className="text-textMuted text-xs">Свободное общение по твоим кейсам и знаниям</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {useContext && (
                        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full border border-green-500/30">
                            📝 Контекст активен
                        </span>
                    )}
                    <button
                        onClick={() => setShowContextPanel(!showContextPanel)}
                        className="px-3 py-2 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 rounded-lg text-sm transition-all border border-purple-500/30"
                    >
                        {showContextPanel ? 'Закрыть' : '⚙️ Мой контекст'}
                    </button>
                </div>
            </div>

            {/* Context Panel */}
            {showContextPanel && (
                <div className="mb-6 bg-surface border border-white/10 rounded-2xl p-6 shadow-2xl animate-in slide-in-from-top duration-300">
                    <h3 className="text-sm font-bold text-white mb-3">📝 Настройка контекста</h3>
                    <p className="text-xs text-textMuted mb-4">
                        Этот контекст будет добавляться к каждому твоему вопросу, чтобы ИИ понимал твои цели.
                    </p>
                    <textarea
                        value={userContext}
                        onChange={(e) => setUserContext(e.target.value)}
                        className="w-full h-40 bg-black/30 border border-white/10 rounded-xl p-4 text-sm text-white font-mono resize-none focus:outline-none focus:border-purple-500/50 mb-4"
                        placeholder="Опиши свои навыки, цели, текущие проекты..."
                    />
                    <div className="flex items-center justify-between">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={useContext}
                                onChange={(e) => setUseContext(e.target.checked)}
                                className="w-4 h-4 rounded border-white/20 bg-black/30 text-purple-600 focus:ring-purple-500/50"
                            />
                            <span className="text-sm text-white">Использовать в запросах</span>
                        </label>
                        <button
                            onClick={saveContext}
                            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm transition-all"
                        >
                            💾 Сохранить
                        </button>
                    </div>
                </div>
            )}

            {/* Chat Area */}
            <div className="flex-1 bg-surface border border-white/5 rounded-3xl p-4 md:p-6 mb-6 overflow-y-auto space-y-4 shadow-2xl custom-scrollbar">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center ${msg.role === 'user' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'
                            }`}>
                            {msg.role === 'user' ? <User size={16} /> : <Sparkles size={16} />}
                        </div>
                        <div className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${msg.role === 'user'
                            ? 'bg-blue-600/20 text-blue-100 rounded-tr-none border border-blue-500/20'
                            : 'bg-white/5 text-text rounded-tl-none border border-white/10'
                            }`}>
                            {msg.content || (loading && idx === messages.length - 1 ? '...' : '')}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Suggestions */}
            {!loading && messages.length === 1 && (
                <div className="flex flex-wrap gap-2 mb-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                    {suggestions.map((s, i) => (
                        <button
                            key={i}
                            onClick={() => applySuggestion(s)}
                            className="text-[11px] px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-textMuted hover:bg-white/10 hover:text-white transition-all"
                        >
                            {s}
                        </button>
                    ))}
                </div>
            )}

            {/* Input Area */}
            <form onSubmit={handleSend} className="relative">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Спроси что угодно про план или предложи тему..."
                    className="w-full bg-surface border border-white/10 rounded-2xl px-6 py-4 pr-16 text-white focus:outline-none focus:border-blue-500/50 transition-all shadow-xl"
                    disabled={loading}
                />
                <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="absolute right-2 top-2 bottom-2 px-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                </button>
            </form>
        </div>
    );
}

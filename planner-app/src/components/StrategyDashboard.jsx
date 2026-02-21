import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Target, Users, Zap, Flame, Save, RefreshCw, BarChart3,
    ListChecks, Goal, Layers, Briefcase, Wallet,
    ArrowRight, ChevronDown, ChevronUp, Sparkles, AlertCircle,
    FileText, Code, Database
} from 'lucide-react';

const StrategicCard = ({ title, icon: Icon, value, onChange, placeholder, color, description, isPrimary }) => (
    <motion.div
        whileHover={{ y: -5 }}
        className={`bg-surface/50 backdrop-blur-xl border ${isPrimary ? 'border-blue-500/30 ring-1 ring-blue-500/10' : 'border-white/5'} rounded-3xl p-6 shadow-2xl flex flex-col gap-4 relative overflow-hidden`}
    >
        {isPrimary && <div className="absolute top-0 right-0 p-2"><Sparkles size={14} className="text-blue-400" /></div>}
        <div className="flex justify-between items-start">
            <div className="flex gap-4">
                <div className={`p-3 rounded-2xl bg-${color}-500/20 text-${color}-400`}>
                    <Icon size={24} />
                </div>
                <div>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">{title}</h3>
                    <p className="text-[10px] text-textMuted leading-tight mt-1">{description}</p>
                </div>
            </div>
        </div>
        <textarea
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="bg-black/20 border border-white/5 rounded-2xl p-4 text-white text-sm leading-relaxed resize-none h-40 focus:outline-none focus:border-blue-500/30 transition-all font-mono"
        />
    </motion.div>
);

const StageItem = ({ number, title, active, completed, onClick, icon: Icon }) => (
    <div
        onClick={onClick}
        className={`flex items-center gap-3 p-3 rounded-2xl cursor-pointer transition-all ${active ? 'bg-blue-600/20 border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]' : 'hover:bg-white/5 border border-transparent'}`}
    >
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${completed ? 'bg-green-500/20 text-green-400 border border-green-500/30' : active ? 'bg-blue-500 text-white' : 'bg-white/10 text-white/40'}`}>
            {Icon ? <Icon size={14} /> : (completed ? '✓' : number)}
        </div>
        <span className={`text-xs font-bold uppercase tracking-widest ${active ? 'text-white' : 'text-white/40'}`}>{title}</span>
    </div>
);

export default function StrategyDashboard() {
    // ВШИТЫЕ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ (FALLBACK) - чтобы никогда не было пусто
    const defaultContext = `МЫ СТРОИМ: AI-продюсер, который понимает этап, узкое место и какой контент нужен для продажи.
ЛОГИКА: 1. Цель -> 2. Позиционирование -> 3. Аудитория -> 4. Боли -> 5. Триггеры -> 6. Архитектура -> 7. План -> 8. Вирусные темы -> 9. Сценарии -> 10. Рекомендации.

ОБО МНЕ:
- Инженер-программист. Проектирую мультимодальные RAG-системы.
- Кейсы: E-commerce (конверсия), Voice AI (автосервис - полный цикл), EdTech (RAG по книгам), ML & CV (растения).
- Активы: YouTube, Школа, Курс (50 000 руб).
- Цель: 3-5 клиентов за 30-60 дней.
- Готов: Shorts каждый день, 1-2 длинных видео в месяц.

ВИРУСНЫЕ ТЕМЫ (ПРИМЕРЫ):
1. Ломка иллюзий: "90% людей никогда не станут AI-инженерами".
2. Поляризация: "AI - это не профессия. Это фильтр".

СТРУКТУРА SHORTS:
- Хук (3 сек) -> Боль -> Инсайт -> Поляризация -> CTA`;

    const [strategy, setStrategy] = useState({
        goals: 'Получить первых 3–5 клиентов на дорогой курс (50 000 руб) в течение 30–60 дней. KPI: 5 созвонов в месяц.',
        positioning: 'Практик-инженер (AI Architect). Показ реальной архитектуры RAG-систем, а не инфошума.',
        target_audience: 'Junior-разработчики, техлиды, фаундеры IT-бизнеса. Боли: нет roadmap, страх отстать.',
        customer_pains: 'Логические ( roadmap/стек), Эмоциональные (страх отстать), Скрытые (деньги/статус).',
        triggers: 'Страх будущего, Деньги (400k+), Поляризация, Авторитет, Разрушение иллюзий.',
        cases: '- E-commerce: нейро-эксперт\n- Voice AI: агент для автосервиса\n- EdTech: RAG по книгам\n- ML & CV: анализ растений',
        full_context: defaultContext,
        shorts_logic: {
            structure: ["Хук (3 сек)", "Боль", "Инсайт", "Поляризация", "CTA"],
            hook_examples: ["Ты никогда не станешь AI-инженером"],
            polarization_examples: ["Курсы за 20к - мусор"]
        },
        monetization: {
            product: 'Дорогой курс / Личная работа',
            price: '50 000 ₽',
            assets: ['YouTube', 'Школа'],
            model: 'Ограниченный набор'
        },
        content_architecture: { viral: 40, expert: 30, case: 20, warmup: 10 }
    });

    const [activeStage, setActiveStage] = useState(0);
    const [isSaving, setIsSaving] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const stages = [
        { id: 0, title: 'ЭТАЛОННЫЙ КОНТЕКСТ', icon: Database },
        { id: 1, title: 'Цель' },
        { id: 2, title: 'Позиционирование' },
        { id: 3, title: 'Аудитория' },
        { id: 4, title: 'Боли & Кейсы' },
        { id: 5, title: 'Триггеры & Продукт' },
        { id: 6, title: 'Архитектура' }
    ];

    useEffect(() => {
        fetchStrategy();
    }, []);

    const fetchStrategy = async () => {
        try {
            const response = await fetch('http://localhost:8000/planner/strategy');
            if (response.ok) {
                const data = await response.json();

                // Only override if data is not empty
                if (data.positioning || data.goals || data.full_context) {
                    let monetization = data.monetization;
                    if (typeof monetization === 'string') monetization = JSON.parse(monetization);

                    let shorts_logic = data.shorts_logic;
                    if (typeof shorts_logic === 'string') shorts_logic = JSON.parse(shorts_logic);

                    setStrategy({
                        ...data,
                        monetization: monetization || strategy.monetization,
                        shorts_logic: shorts_logic || strategy.shorts_logic,
                        content_architecture: data.content_architecture || strategy.content_architecture
                    });
                }
            }
        } catch (err) {
            console.error("Fetch Error:", err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const response = await fetch('http://localhost:8000/planner/strategy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(strategy)
            });
            if (response.ok) {
                alert('🚀 СИСТЕМА ОБНОВЛЕНА. Данные засинхронены с мозгами ИИ-Продюсера.');
            }
        } catch (err) {
            alert('Ошибка при сохранении');
        } finally {
            setIsSaving(false);
        }
    };

    const calculateIntegrity = () => {
        const fields = ['goals', 'positioning', 'target_audience', 'customer_pains', 'triggers', 'cases', 'full_context'];
        const filled = fields.filter(f => strategy[f] && strategy[f].length > 20).length;
        return Math.round((filled / fields.length) * 100);
    };

    if (isLoading) return (
        <div className="flex flex-col items-center justify-center h-full gap-4">
            <RefreshCw className="animate-spin text-blue-500" size={40} />
            <p className="text-textMuted font-mono text-sm uppercase tracking-widest">Accessing Strategy Vault...</p>
        </div>
    );

    return (
        <div className="p-4 md:p-8 max-w-[1500px] mx-auto min-h-full flex flex-col gap-8">
            {/* Top Bar */}
            <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
                <div>
                    <h1 className="text-4xl font-black tracking-tighter text-white flex items-center gap-3">
                        <BarChart3 className="text-blue-500" size={32} />
                        AI PRODUCER <span className="text-blue-500">CORE</span>
                    </h1>
                    <p className="text-textMuted text-sm mt-1 uppercase tracking-widest font-bold">Strategic Mapping System 2026</p>
                </div>

                <div className="flex items-center gap-6 bg-surface/80 p-4 rounded-3xl border border-white/5 shadow-2xl">
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] font-bold text-textMuted uppercase tracking-widest">Integrity Score</span>
                        <div className="flex items-center gap-2">
                            <div className="w-32 h-2 bg-white/5 rounded-full overflow-hidden border border-white/10">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${calculateIntegrity()}%` }}
                                    className="h-full bg-gradient-to-r from-blue-600 to-purple-600"
                                />
                            </div>
                            <span className="text-xl font-black text-blue-400 font-mono">{calculateIntegrity()}%</span>
                        </div>
                    </div>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="flex items-center gap-3 bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-2xl font-black transition-all shadow-xl shadow-blue-500/20 disabled:opacity-50"
                    >
                        {isSaving ? <RefreshCw className="animate-spin" size={20} /> : <Save size={20} />}
                        <span>{isSaving ? 'СИНХРОН...' : 'ПРИМЕНИТЬ'}</span>
                    </button>
                </div>
            </header>

            {/* Main Stage Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1">

                {/* Sidebar Stages */}
                <div className="lg:col-span-3 flex flex-col gap-2 bg-surface/30 p-4 rounded-3xl border border-white/5 h-fit">
                    <h2 className="text-[10px] font-black text-textMuted uppercase tracking-[0.2em] mb-4 px-2">ARCHITECTURE</h2>
                    {stages.map(s => (
                        <StageItem
                            key={s.id}
                            number={s.id}
                            title={s.title}
                            icon={s.icon}
                            active={activeStage === s.id}
                            completed={strategy[Object.keys(strategy)[s.id === 0 ? 11 : s.id - 1]]?.length > 30}
                            onClick={() => setActiveStage(s.id)}
                        />
                    ))}
                    <div className="mt-8 p-4 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex gap-3">
                        <FileText className="text-blue-400 shrink-0" size={18} />
                        <p className="text-[10px] text-blue-200 leading-relaxed font-medium">
                            ВСЁ ЗАПОЛНЕНО: Николай уже знает про твою школу, курс за 50к и кейсы. Тебе осталось только подкорректировать то, что тебе не нравится.
                        </p>
                    </div>
                </div>

                {/* Content Area */}
                <div className="lg:col-span-9 space-y-8 min-h-[600px]">

                    {activeStage === 0 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300 h-full flex flex-col gap-6">
                            <div className="bg-blue-600/10 border border-blue-500/30 rounded-3xl p-8 relative overflow-hidden">
                                <div className="flex gap-4 mb-6">
                                    <div className="p-3 rounded-2xl bg-blue-500/20 text-blue-400">
                                        <Database size={24} />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-black text-white uppercase tracking-wider">ЭТАЛОННЫЙ КОНТЕКСТ</h3>
                                        <p className="text-xs text-textMuted leading-tight mt-1">Я уже собрал сюда всё из твоих файлов. Просто отредактируй, если я где-то ошибся.</p>
                                    </div>
                                </div>
                                <textarea
                                    value={strategy.full_context || ''}
                                    onChange={(e) => setStrategy({ ...strategy, full_context: e.target.value })}
                                    className="w-full bg-black/40 border border-white/10 rounded-2xl p-6 text-white text-sm leading-relaxed h-[400px] focus:outline-none focus:border-blue-500/50 transition-all font-mono shadow-inner"
                                    placeholder="Вставь сюда весь текст о себе, кейсах, воронках..."
                                />
                                <div className="mt-4 flex items-center gap-2 text-[10px] text-blue-400 font-bold uppercase tracking-widest">
                                    <Sparkles size={12} />
                                    <span>ДАННЫЕ ЗАГРУЖЕНЫ ИЗ ТВОИХ СООБЩЕНИЙ</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeStage === 1 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <StrategicCard
                                title="ЦЕЛЬ (Зачем это всё?)"
                                icon={Goal}
                                color="green"
                                description="KPI, деньги, кол-во клиентов. Что считаем успехом?"
                                value={strategy.goals}
                                onChange={(v) => setStrategy({ ...strategy, goals: v })}
                                isPrimary={true}
                                placeholder="Например: 5 продаж курса за 50к. 10 созвонов в месяц..."
                            />
                        </div>
                    )}

                    {activeStage === 2 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <StrategicCard
                                title="ПОЗИЦИОНИРОВАНИЕ"
                                icon={Target}
                                color="blue"
                                description="Твоя роль, твой 'угол' и отличие от конкурентов."
                                value={strategy.positioning}
                                onChange={(v) => setStrategy({ ...strategy, positioning: v })}
                                isPrimary={true}
                                placeholder="Пример: Практик-инженер. Показываю логику RAG, а не хайп..."
                            />
                        </div>
                    )}

                    {activeStage === 3 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <StrategicCard
                                title="ЦЕЛЕВАЯ АУДИТОРИЯ (ЦА)"
                                icon={Users}
                                color="purple"
                                description="Кто смотрит? Стек, уровень дохода, мечты."
                                value={strategy.target_audience}
                                onChange={(v) => setStrategy({ ...strategy, target_audience: v })}
                                isPrimary={true}
                                placeholder="Пример: Junior-разработчики, техлиды, фаундеры стартапов..."
                            />
                        </div>
                    )}

                    {activeStage === 4 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-right-4 duration-300">
                            <StrategicCard
                                title="БОЛИ КЛИЕНТОВ"
                                icon={Flame}
                                color="red"
                                description="Логические, эмоциональные и скрытые боли."
                                value={strategy.customer_pains}
                                onChange={(v) => setStrategy({ ...strategy, customer_pains: v })}
                                placeholder="Пример: Боятся не успеть в AI. Синдром самозванца."
                            />
                            <StrategicCard
                                title="ТВОИ КЕЙСЫ (ПРУФЫ)"
                                icon={Briefcase}
                                color="blue"
                                description="Реальные проекты: E-commerce, Voice AI, EdTech..."
                                value={strategy.cases}
                                onChange={(v) => setStrategy({ ...strategy, cases: v })}
                                placeholder="Опиши свои лучшие внедрения..."
                            />
                        </div>
                    )}

                    {activeStage === 5 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-right-4 duration-300">
                            <StrategicCard
                                title="ТРИГГЕРЫ ВНИМАНИЯ"
                                icon={Zap}
                                color="yellow"
                                description="Рычаги внимания: деньги, страх, поляризация."
                                value={strategy.triggers}
                                onChange={(v) => setStrategy({ ...strategy, triggers: v })}
                                placeholder="Деньги (400к), Страх будущего, Провокация..."
                            />
                            <motion.div className="bg-surface/50 border border-white/5 rounded-3xl p-6 shadow-2xl flex flex-col gap-4">
                                <div className="flex gap-4">
                                    <div className="p-3 rounded-2xl bg-orange-500/20 text-orange-400">
                                        <Wallet size={24} />
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">ПРОДУКТ & МОНЕТИЗАЦИЯ</h3>
                                        <p className="text-[10px] text-textMuted leading-tight mt-1">Твой оффер и цена</p>
                                    </div>
                                </div>
                                <div className="space-y-4 font-mono text-xs">
                                    <div className="flex flex-col gap-1">
                                        <label className="text-white/40 uppercase text-[9px]">Оффер</label>
                                        <input
                                            value={strategy.monetization.product}
                                            onChange={(e) => setStrategy({ ...strategy, monetization: { ...strategy.monetization, product: e.target.value } })}
                                            className="bg-black/40 border border-white/5 rounded-xl p-3 text-white focus:outline-none focus:ring-1 ring-blue-500/30"
                                            placeholder="Личное наставничество..."
                                        />
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <label className="text-white/40 uppercase text-[9px]">Цена (Ticket)</label>
                                        <input
                                            value={strategy.monetization.price}
                                            onChange={(e) => setStrategy({ ...strategy, monetization: { ...strategy.monetization, price: e.target.value } })}
                                            className="bg-black/40 border border-white/5 rounded-xl p-3 text-blue-400 font-black focus:outline-none focus:ring-1 ring-blue-500/30"
                                            placeholder="50 000 ₽"
                                        />
                                    </div>
                                    <div className="p-4 bg-blue-500/5 rounded-2xl border border-blue-500/10">
                                        <p className="text-[9px] text-blue-300 uppercase font-black leading-relaxed">
                                            ИИ будет фильтровать все идеи через чек-лист «Продаст ли это продукт за {strategy.monetization.price || '...'}?»
                                        </p>
                                    </div>
                                </div>
                            </motion.div>
                        </div>
                    )}

                    {activeStage === 6 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-right-4 duration-300 h-fit">
                            <motion.div className="bg-surface/50 border border-blue-500/20 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 blur-3xl -z-10" />
                                <h3 className="text-xl font-black text-white mb-6 uppercase tracking-widest flex items-center gap-3">
                                    <Layers className="text-blue-500" />
                                    CONTENT GRID
                                </h3>
                                <div className="space-y-6">
                                    {[
                                        { label: 'Виральные (Ломка иллюзий)', key: 'viral', color: 'bg-red-500', desc: 'Захват холодного трафика' },
                                        { label: 'Экспертные (Архитектура)', key: 'expert', color: 'bg-blue-500', desc: 'Построение авторитета' },
                                        { label: 'Кейсы (Результаты)', key: 'case', color: 'bg-green-500', desc: 'Социальное доказательство' },
                                        { label: 'Прогрев (Продажа)', key: 'warmup', color: 'bg-purple-500', desc: 'Конверсия в клиента' },
                                    ].map((item) => (
                                        <div key={item.key} className="space-y-2">
                                            <div className="flex justify-between items-end font-mono">
                                                <div>
                                                    <span className="text-[10px] text-white font-bold block">{item.label}</span>
                                                    <span className="text-[9px] text-textMuted uppercase">{item.desc}</span>
                                                </div>
                                                <span className="text-lg font-black text-blue-400">{strategy.content_architecture[item.key]}%</span>
                                            </div>
                                            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden border border-white/5">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${strategy.content_architecture[item.key]}%` }}
                                                    className={`h-full ${item.color} shadow-[0_0_15px_rgba(59,130,246,0.3)]`}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>

                            <div className="flex flex-col gap-6">
                                <div className="bg-blue-600 rounded-3xl p-8 text-white shadow-2xl shadow-blue-500/40 flex flex-col justify-between flex-1 relative overflow-hidden group">
                                    <ArrowRight className="absolute -bottom-4 -right-4 w-32 h-32 opacity-10 group-hover:scale-110 transition-transform" />
                                    <div>
                                        <h4 className="text-2xl font-black uppercase tracking-tighter leading-tight">Готов к запуску?</h4>
                                        <p className="text-blue-100 text-xs mt-2 font-medium">После сохранения Николай будет использовать эти настройки для ежедневной генерации Shorts.</p>
                                    </div>
                                    <button
                                        onClick={handleSave}
                                        className="mt-6 bg-white text-blue-600 font-black py-4 rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all"
                                    >
                                        АКТИВИРОВАТЬ ПРОДЮСЕРА
                                    </button>
                                </div>
                                <div className="bg-black/40 border border-white/5 rounded-3xl p-6 flex items-center gap-4">
                                    <div className="p-4 bg-white/5 rounded-2xl group-hover:rotate-12 transition-transform">
                                        <Sparkles className="text-yellow-400" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-[10px] text-white/40 uppercase font-black">AI STATUS</p>
                                        <p className="text-xs text-white font-bold">Опираюсь на 300+ видео Велижанина</p>
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

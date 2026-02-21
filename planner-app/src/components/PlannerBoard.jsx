import React, { useState, useRef, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../db';
import { Plus, MoreHorizontal, Calendar, ArrowRight, Mic, Square, Play, Trash2, StopCircle, Sparkles, Download } from 'lucide-react';
import * as htmlToImage from 'html-to-image';
import { motion } from 'framer-motion';

// Helper for random gradients
const GRADIENTS = [
    'linear-gradient(135deg, #1e1e24 0%, #2a2a35 100%)',
    'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
    'linear-gradient(135deg, #10b981 0%, #047857 100%)',
    'linear-gradient(135deg, #8b5cf6 0%, #5b21b6 100%)',
    'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)',
];

function getRandomGradient() {
    return GRADIENTS[Math.floor(Math.random() * GRADIENTS.length)];
}

function IdeaCard({ idea, onClick }) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const audioRef = useRef(null);
    const cardRef = useRef(null);

    // Create audio URL if blob exists
    const audioUrl = (idea.audioBlob instanceof Blob) ? URL.createObjectURL(idea.audioBlob) : null;

    const toggleAudio = (e) => {
        e.stopPropagation();
        if (!audioRef.current) return;

        if (isPlaying) {
            audioRef.current.pause();
        } else {
            audioRef.current.play();
        }
        setIsPlaying(!isPlaying);
    };

    // Handle audio end
    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.onended = () => setIsPlaying(false);
        }
    }, [audioUrl]);

    const handleDownload = async (e) => {
        e.stopPropagation(); // Prevent opening the modal
        if (!cardRef.current || isDownloading) return;

        setIsDownloading(true);
        try {
            const filterExport = (node) => !node.classList?.contains('hide-on-export');
            const dataUrl = await htmlToImage.toPng(cardRef.current, {
                quality: 1.0,
                pixelRatio: 2, // High resolution for mobile
                style: { transform: 'scale(1)', margin: 0 }, // Ensure it captures correctly without hover scale
                filter: filterExport
            });
            const link = document.createElement('a');
            link.download = `cover-${idea.title.slice(0, 15)}.png`;
            link.href = dataUrl;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (err) {
            console.error('Failed to download image', err);
            alert('Не удалось скачать обложку: ' + (err.message || 'неизвестная ошибка'));
        } finally {
            setIsDownloading(false);
        }
    };

    return (
        <motion.div
            onClick={onClick}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ y: -4, scale: 1.02 }}
            className="group relative bg-surface rounded-xl overflow-hidden border border-white/5 hover:border-blue-500/30 transition-all cursor-pointer shadow-lg flex flex-col h-full"
        >
            {/* 9:16 Aspect Ratio Cover */}
            <div
                ref={cardRef}
                className="w-full aspect-[9/16] bg-cover bg-center relative p-4 flex flex-col items-center justify-center text-center"
                style={{ background: idea.metadata?.gradient || GRADIENTS[0] }}
            >
                <h3 className="font-bold text-lg leading-tight text-white drop-shadow-md break-words w-full line-clamp-4">
                    {idea.title}
                </h3>

                {/* Status Badge */}
                <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-black/40 backdrop-blur-md text-[9px] font-bold border border-white/10 uppercase tracking-wider text-white/80">
                    {idea.status || 'Draft'}
                </div>

                {/* Download Button (Hover only) */}
                <button
                    onClick={handleDownload}
                    className="hide-on-export absolute top-2 left-2 p-1.5 rounded-lg bg-black/40 backdrop-blur-md border border-white/10 text-white/80 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/60 hover:text-white z-10"
                    title="Скачать обложку"
                >
                    <Download size={14} className={isDownloading ? "animate-bounce" : ""} />
                </button>

                {/* Audio Player Overlay */}
                {audioUrl && (
                    <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-2 py-1.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 transition-transform hover:scale-105" onClick={(e) => e.stopPropagation()}>
                        <audio ref={audioRef} src={audioUrl} className="hidden" />
                        <button onClick={toggleAudio} className="text-white hover:text-blue-400 transition-colors">
                            {isPlaying ? <Square size={12} fill="currentColor" /> : <Play size={12} fill="currentColor" />}
                        </button>
                    </div>
                )}
            </div>
        </motion.div>
    );
}

function AddIdeaModal({ onClose, initialData }) {
    const [title, setTitle] = useState(initialData?.title || '');
    const [content, setContent] = useState(initialData?.content || '');
    const [isRecording, setIsRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState(initialData?.audioBlob || null);
    const [isEnhancing, setIsEnhancing] = useState(false); // AI State
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    // Recording Preview Logic
    const [isPlayingPreview, setIsPlayingPreview] = useState(false);
    const [previewUrl, setPreviewUrl] = useState(null);
    const previewAudioRef = useRef(null);

    // Update preview URL when blob changes
    useEffect(() => {
        if (audioBlob instanceof Blob) {
            const url = URL.createObjectURL(audioBlob);
            setPreviewUrl(url);
            return () => URL.revokeObjectURL(url);
        } else {
            setPreviewUrl(null);
        }
    }, [audioBlob]);

    const togglePreview = () => {
        if (!previewAudioRef.current) return;

        if (isPlayingPreview) {
            previewAudioRef.current.pause();
            previewAudioRef.current.currentTime = 0; // Reset to start
        } else {
            previewAudioRef.current.play();
        }
        setIsPlayingPreview(!isPlayingPreview);
    };

    // Recording Logic
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);
            chunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorderRef.current.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                setAudioBlob(blob);
                stream.getTracks().forEach(track => track.stop()); // Stop mic
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
        } catch (err) {
            console.error("Mic Error:", err);
            alert("Не удалось получить доступ к микрофону");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const deleteRecording = () => {
        setAudioBlob(null);
        chunksRef.current = [];
    };

    // AI Enhancement Logic
    const handleEnhance = async () => {
        if (!title && !content) {
            alert("Напиши хоть что-нибудь (заголовок или мысль), чтобы ИИ мог работать!");
            return;
        }

        setIsEnhancing(true);
        try {
            // Try to call local RAG server
            const response = await fetch('http://localhost:8000/api/enhance-idea', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title || "Untitled Idea",
                    content: content || "Just a visual concept.",
                    focus: "viral_shorts"
                })
            });

            if (!response.ok) throw new Error("Server Offline");

            const data = await response.json();

            // Format the AI response into the content area
            const formattedContent = `
✨ **AI Suggested Title:** ${data.suggested_title}

🎣 **Hook:** ${data.hook}

💎 **Value:** ${data.value_proposition}

📜 **Script Outline:**
${data.script_outline}

🔥 **CTA:** ${data.call_to_action}
            `.trim();

            setContent(formattedContent);
            if (!title) setTitle(data.suggested_title); // Auto-set title if empty

        } catch (error) {
            console.warn("AI Backend Offline, using Mock", error);
            // Mock Response for testing UI without backend
            setTimeout(() => {
                const mockResponse = `
✨ **[MOCK] AI Title:** 5 Secrets of Productivity

🎣 **Hook:** "Stop using To-Do lists. Do this instead..."

💎 **Value:** Lists creates anxiety. Time-blocking creates results.

📜 **Script Outline:**
1. Show a long messy list (Bad).
2. Tear it up.
3. Show a calendar block (Good).
4. Explain 'Deep Work'.

🔥 **CTA:** "Comment 'FOCUS' for my template!"
                `.trim();
                setContent(mockResponse);
                if (!title) setTitle("5 Secrets of Productivity");
                setIsEnhancing(false);
            }, 1000);
            return; // Exit to avoid double toggle
        }
        setIsEnhancing(false);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!title) return;

        const requestBody = {
            title,
            content,
            status: initialData?.status || 'todo',
            cover_type: initialData?.cover_type || 'gradient',
            metadata: {
                gradient: initialData?.metadata?.gradient || getRandomGradient(),
                audioUrl: initialData?.metadata?.audioUrl // Временно так
            }
        };

        try {
            const url = initialData?.id
                ? `http://localhost:8000/planner/ideas/${initialData.id}`
                : 'http://localhost:8000/planner/ideas';

            const method = initialData?.id ? 'PATCH' : 'POST';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail ? JSON.stringify(errData.detail) : 'API Error');
            }

            onClose();
            // Refresh parent state if needed, but here onClose will trigger it via re-render or explicit callback
        } catch (err) {
            console.error("Save Error:", err);
            alert("Ошибка сохранения в базу! Причина: " + err.message);
        }
    };

    const handleDelete = async () => {
        if (initialData?.id && confirm('Удалить эту карточку?')) {
            try {
                await fetch(`http://localhost:8000/planner/ideas/${initialData.id}`, {
                    method: 'DELETE'
                });
                onClose();
            } catch (err) {
                alert("Ошибка удаления!");
            }
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="bg-[#1a1a1d] border border-white/10 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
                <div className="p-6 overflow-y-auto">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <span className="w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-sm">✨</span>
                            {initialData ? 'Редактировать Shorts' : 'Новый Shorts'}
                        </h2>
                        {initialData && (
                            <button onClick={handleDelete} className="text-red-400 hover:text-red-300 p-2 rounded-lg hover:bg-red-500/10">
                                <Trash2 size={18} />
                            </button>
                        )}
                    </div>

                    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                        <div>
                            <label className="text-xs font-medium text-textMuted uppercase mb-2 block">Заголовок (Обложка)</label>
                            <input
                                autoFocus
                                type="text"
                                placeholder="Текст на видео..."
                                className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
                                value={title}
                                onChange={e => setTitle(e.target.value)}
                            />
                        </div>

                        {/* Voice Recorder */}
                        <div>
                            <label className="text-xs font-medium text-textMuted uppercase mb-2 block">Голос</label>
                            <div className="flex items-center gap-3 p-3 rounded-xl bg-black/20 border border-white/5">
                                {!isRecording && !audioBlob && (
                                    <button
                                        type="button"
                                        onClick={startRecording}
                                        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors text-sm font-medium w-full justify-center"
                                    >
                                        <Mic size={16} />
                                        Начать запись
                                    </button>
                                )}

                                {isRecording && (
                                    <button
                                        type="button"
                                        onClick={stopRecording}
                                        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-600 text-white animate-pulse transition-colors text-sm font-medium w-full justify-center"
                                    >
                                        <StopCircle size={16} />
                                        Стоп
                                    </button>
                                )}

                                {audioBlob && (
                                    <div className="flex items-center gap-3 w-full">
                                        <button
                                            type="button"
                                            onClick={togglePreview}
                                            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-green-500/10 text-green-400 text-sm font-medium flex-1 hover:bg-green-500/20 transition-colors text-left"
                                        >
                                            {isPlayingPreview ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
                                            {isPlayingPreview ? "Стоп" : "Прослушать запись"}
                                        </button>

                                        <audio
                                            ref={previewAudioRef}
                                            src={previewUrl}
                                            onEnded={() => setIsPlayingPreview(false)}
                                            className="hidden"
                                        />

                                        <button
                                            type="button"
                                            onClick={deleteRecording}
                                            className="p-2 rounded-lg hover:bg-white/10 text-textMuted hover:text-red-400"
                                            title="Удалить запись"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <label className="text-xs font-medium text-textMuted uppercase block">Заметки / Сценарий</label>
                                <button
                                    type="button"
                                    onClick={handleEnhance}
                                    disabled={isEnhancing}
                                    className="text-xs font-bold text-purple-400 hover:text-purple-300 flex items-center gap-1 bg-purple-500/10 px-2 py-1 rounded-lg transition-colors disabled:opacity-50"
                                >
                                    {isEnhancing ? (
                                        <>⏳ Думаю...</>
                                    ) : (
                                        <><Sparkles size={12} /> Улучшить с AI</>
                                    )}
                                </button>
                            </div>
                            <textarea
                                rows={8}
                                placeholder="Сценарий, мысли..."
                                className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 transition-colors resize-none font-mono text-sm leading-relaxed"
                                value={content}
                                onChange={e => setContent(e.target.value)}
                            />
                        </div>

                        <div className="flex gap-3 mt-4">
                            <button
                                type="button"
                                onClick={onClose}
                                className="flex-1 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors font-medium text-sm"
                            >
                                Отмена
                            </button>
                            <button
                                type="submit"
                                className="flex-1 px-4 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white transition-colors font-medium text-sm shadow-lg shadow-blue-900/20"
                            >
                                Сохранить
                            </button>
                        </div>
                    </form>
                </div>
            </motion.div>
        </div>
    );
}

export default function PlannerBoard() {
    const [ideas, setIdeas] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const fetchIdeas = async () => {
        try {
            const response = await fetch('http://localhost:8000/planner/ideas');
            const data = await response.json();
            setIdeas(data);
        } catch (err) {
            console.error("Fetch Error:", err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchIdeas();
    }, [isModalOpen]); // Reload whenever modal closes (could be more optimized)

    const [editingIdea, setEditingIdea] = useState(null); // Track formatted idea
    const fileInputRef = React.useRef(null);

    const openModal = (idea = null) => {
        setEditingIdea(idea);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setEditingIdea(null);
        setIsModalOpen(false);
        fetchIdeas(); // Trigger manual refresh
    }

    // Export Logic
    const handleExport = async () => {
        if (!ideas || ideas.length === 0) {
            alert("Нечего экспортировать! Добавь пару идей.");
            return;
        }
        // Note: Audio blobs won't serialize directly to JSON! 
        // We strictly need to convert blobs to Base64 for JSON export.
        // Simplifying for now: Warning user about audio.
        // Ideally: Convert Blob -> Base64 string before export.

        // Quick Fix for Exporting Audio:
        const exportData = await Promise.all(ideas.map(async (idea) => {
            if (idea.audioBlob) {
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        resolve({ ...idea, audioBase64: reader.result, audioBlob: undefined }); // Swap Blob for Base64
                    };
                    reader.readAsDataURL(idea.audioBlob);
                });
            }
            return idea;
        }));

        const dataStr = JSON.stringify(exportData, null, 2);
        const blob = new Blob([dataStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = `vibe_backup_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Import Logic
    const handleImport = (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const importedData = JSON.parse(e.target.result);
                if (!Array.isArray(importedData)) throw new Error("Invalid format");

                // Convert Base64 back to Blobs
                const processedData = await Promise.all(importedData.map(async item => {
                    if (item.audioBase64) {
                        const res = await fetch(item.audioBase64);
                        const blob = await res.blob();
                        return { ...item, audioBlob: blob, audioBase64: undefined };
                    }
                    return item;
                }));

                await db.ideas.bulkPut(processedData);
                alert(`Успешно восстановлено ${processedData.length} идей! 🚀`);
            } catch (error) {
                alert("Ошибка при чтении файла: " + error.message);
            }
        };
        reader.readAsText(file);
        event.target.value = null;
    };


    return (
        <div className="p-8 max-w-[1800px] mx-auto">
            {/* Header */}
            <div className="flex items-end justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold mb-1">Shorts Planner</h1>
                    <p className="text-textMuted text-sm">Визуализируй поток контента.</p>
                </div>

                <div className="flex gap-2">
                    <input type="file" ref={fileInputRef} onChange={handleImport} className="hidden" accept=".json" />
                    <button onClick={() => fileInputRef.current.click()} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white" title="Импорт">📥</button>
                    <button onClick={handleExport} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white" title="Экспорт">💾</button>
                    <button
                        onClick={() => openModal()}
                        className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-xl font-bold hover:bg-gray-200 transition-colors text-sm"
                    >
                        <Plus size={18} />
                        <span>Новый</span>
                    </button>
                </div>
            </div>

            {/* Denser Grid for "2 Rows" feel */}
            {!ideas || ideas.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 border-2 border-dashed border-white/5 rounded-3xl bg-white/[0.02]">
                    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center text-3xl mb-4 grayscale opacity-50">🎬</div>
                    <h3 className="text-lg font-medium text-white/50">Пока пусто...</h3>
                    <p className="text-sm text-textMuted mb-6">Добавь первую идею!</p>
                    <button
                        onClick={() => openModal()}
                        className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center gap-1"
                    >
                        Создать Shorts <ArrowRight size={14} />
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
                    {ideas.map(idea => (
                        <IdeaCard key={idea.id} idea={idea} onClick={() => openModal(idea)} />
                    ))}
                </div>
            )}

            {/* Modal */}
            {isModalOpen && <AddIdeaModal onClose={closeModal} initialData={editingIdea} />}
        </div>
    );
}


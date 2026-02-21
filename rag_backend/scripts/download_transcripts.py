import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

def get_video_id(url):
    """Извлекает ID видео из ссылки."""
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url

def download_transcripts(video_urls, output_dir="data/knowledge/transcripts"):
    """Скачивает транскрипты для списка видео."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Создана папка: {output_dir}")

    formatter = TextFormatter()

    for url in video_urls:
        video_id = get_video_id(url)
        print(f"Обработка видео {video_id}...")
        
        try:
            # Пытаемся получить русские субтитры
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            try:
                transcript = transcript_list.find_transcript(['ru'])
                print(f"Найдена русская дорожка.")
            except:
                # Если русских нет, берем доступную
                transcript = transcript_list.find_generated_transcript(['ru']) or \
                             transcript_list.find_transcript(['en'])
                print(f"Берем доступную дорожку: {transcript.language}")

            text = transcript.fetch()
            formatted_text = formatter.format_transcript(text)
            
            file_path = os.path.join(output_dir, f"{video_id}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(formatted_text)
            
            print(f"✅ Сохранено: {file_path}")
            
        except Exception as e:
            print(f"❌ Ошибка для видео {video_id}: {str(e)}")

if __name__ == "__main__":
    # Список ссылок. Можно добавить сколько угодно.
    urls = [
        "https://www.youtube.com/watch?v=EXAMPLE1",
        "https://www.youtube.com/watch?v=EXAMPLE2"
    ]
    
    # При реальном запуске замени EXAMPLE на реальные ID
    print("Начинаю скачивание...")
    # download_transcripts(urls) # Раскомментируй при запуске
    print("\nИнструкция: Добавь реальные ссылки в список urls и запусти скрипт.")

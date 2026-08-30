# -*- coding: utf-8 -*-
"""
Localization module for Storm Tag Editor.
Contains all translatable strings in Russian and English.
"""

TRANSLATIONS = {
    'ru': {
        # Main window
        'app_title': 'STORM TAG EDITOR',
        'ready': 'Готов к работе',
        'drag_drop_enabled': 'Drag & Drop включен',
        'selected': 'Выбрано',
        
        # Header buttons
        'open_files': '📄 Добавить файлы',
        'open_folder': '📁 Добавить папку',
        'save': '💾 Сохранить',
        'save_all': '💾 Сохранить всё',
        'auto_update': '🔄 Авто-обновление',
        
        # File list panel
        'files': '🎵 Файлы',
        'files_count': '{} файлов',
        'select_all': '☑️ Выбрать все',
        'deselect_all': '⬜ Снять выбор',
        'clear_list': '❌ Очистить список',
        'drop_hint': 'Перетащите файлы сюда',
        'remove_list': '❌ Убрать из списка',
        
        # Tag editor panel
        'converter_title': "Аудио Конвертер",
        'tag_editor': 'Редактор тегов',
        'select_file_hint': 'Выберите файл',
        'title': 'Название',
        'artist': 'Исполнитель',
        'album': 'Альбом',
        'year': 'Год',
        'genre': 'Жанр',
        'track': 'Трек',
        'track_num': 'Трек',
        'track_total': 'Всего треков',
        'disk': 'Диск',
        'disc_num': 'Диск',
        'disc_total': 'Всего дисков',
        'composer': 'Композитор',
        'comment': 'Комментарий',
        'lyrics': 'Текст песни',
        
        # Cover art panel
        'album_cover': 'Обложка',
        'no_cover': 'Нет обложки',
        'change_cover': 'Выбрать',
        'remove_cover': 'Удалить',
        'extract_cover': 'Извлечь',
        
        # Batch editor panel
        'batch_editor': 'Массовое редактирование',
        'batch_hint': 'Применить к выбранным:',
        'auto_numbering': 'Авто-нумерация',
        'apply_cover_all': 'Обложка для всех',
        
        # Player
        'set_start': 'Начало',
        'set_end': 'Конец',
        'save_trim': 'Сохр. фрагмент',
        'start_set': 'Начало: {}',
        'end_set': 'Конец: {}',
        'ok': 'OK',
        'cancel': 'Отмена',
        'equalizer': 'Эквалайзер',
        'visualization': 'Визуализация',
        'filter_format': 'Формат:',
        'all_formats': 'Все',
        
        # Dialogs
        'info': 'Информация',
        'converter_title': 'Аудио Конвертер',
        'error': 'Ошибка',
        'warning': 'Внимание',
        'source_files': 'Исходные файлы',
        'settings': '⚙️ Настройки',
        'format': 'Формат',
        'quality': 'Качество',
        'output_folder': 'Папка вывода',
        'same_as_source': 'Как исходный файл',
        'browse': 'Обзор...',
        'convert': 'Конвертировать',
        'cancel': 'Отмена',
        'converting': 'Конвертация...',
        'conversion_complete': 'Конвертация завершена!',
        'conversion_errors': 'Завершено с ошибками',
        'close': 'Закрыть',
        'stop': 'Стоп',
        'ffmpeg_not_found': 'FFMPEG не найден!',
        'ffmpeg_hint': 'Для работы конвертера требуется FFMPEG.\nПоместите ffmpeg.exe в папку программы или добавьте в PATH.',
        'select_file_to_save': 'Выберите файл для сохранения',
        'select_files_to_save': 'Выберите файлы для сохранения',
        'saved': 'Сохранено',
        'save_error': 'Ошибка сохранения',
        'studio_processing': 'Студийная обработка',
        'studio_processing_desc': 'Применяет фильтры для улучшения звука: убирает шум, нормализует громкость, насыщает басс и "чистит" верхние частоты.',
        'converted_files': 'Конвертировано файлов: {}.',
        'app_running_error': 'Приложение уже запущено!',
        
        # Context Menu
        'undo': 'Отменить',
        'redo': 'Повторить',
        'cut': 'Вырезать',
        'copy': 'Копировать',
        'paste': 'Вставить',
        'delete': 'Удалить',
        'select_all': 'Выбрать все',
        'saving': 'Сохранение...',
        'saved_count': 'Сохранено {} из {}',
        'cover_extracted': 'Обложка извлечена!',
        'error_save': 'Не удалось сохранить',
        'no_files_convert': 'Нет файлов для конвертации.',
        
        # File dialogs
        'audio_files': 'Аудио файлы',
        'all_files': 'Все файлы',
        'image_files': 'Изображения',
        'select_audio': 'Выберите аудио файлы',
        'select_folder': 'Выберите папку',
        'select_image': 'Выберите изображение',
        'save_image_as': 'Сохранить изображение как',
        
        # Update dialog
        'update_available': 'Доступно обновление',
        'new_version_available': 'Доступна новая версия!',
        'current_version': 'Текущая версия',
        'new_version': 'Новая версия',
        'update_btn': 'Обновить',
        'later': 'Позже',
        'downloading': 'Скачивание обновления... {}%',
        'download_progress': 'Загрузка: {}%',
        'applying_update': 'Применение обновления...',
        'download_error': 'Ошибка загрузки!',
        'apply_error': 'Не удалось применить обновление',
        
        # Language
        'language': 'Язык / Language',
        'russian': '🇷🇺 Русский',
        'english': '🇬🇧 English',
        'restart_required': 'Перезапустите программу для применения нового языка',
        'success': 'Успешно',
        'converted_files': 'Конвертировано файлов: {}.',
    },
    
    'en': {
        # Main window
        'app_title': 'STORM TAG EDITOR',
        'ready': 'Ready',
        'drag_drop_enabled': 'Drag & Drop enabled',
        'selected': 'Selected',
        
        # Header buttons
        'open_files': '📄 Add Files',
        'open_folder': '📁 Add Folder',
        'save': '💾 Save',
        'save_all': '💾 Save All',
        'auto_update': '🔄 Auto-update',
        
        # File list panel
        'files': '🎵 Files',
        'files_count': '{} files',
        'select_all': '☑️ Select All',
        'deselect_all': '⬜ Deselect All',
        'clear_list': '❌ Clear List',
        'drop_hint': 'Drop files or folders here\n\nor use buttons above',
        'remove_list': '❌ Remove from list',
        
        # Tag editor panel
        'tag_editor': 'Tag Editor',
        'select_file_hint': 'Select a file to edit',
        'title': 'Title',
        'artist': 'Artist',
        'album': 'Album',
        'year': 'Year',
        'track': 'Track',
        'track_num': 'Track',
        'track_total': 'Total Tracks',
        'disc_num': 'Disc',
        'disc_total': 'Total Discs',
        'composer': 'Composer',
        'comment': 'Comment',
        'lyrics': 'Lyrics',
        
        # Cover art panel
        'album_cover': 'Album Cover',
        'no_cover': 'No cover',
        'change_cover': 'Change',
        'remove_cover': 'Remove',
        'extract_cover': 'Extract',
        
        # Batch editor panel
        'batch_editor': 'Batch Editor',
        'batch_hint': 'Check fields to apply to selected files:',
        'auto_numbering': 'Auto-number tracks',
        'apply_cover_all': 'Apply cover to all',
        
        # Player
        'set_start': 'Set Start',
        'set_end': 'Set End',
        'save_trim': 'Save Trimmed',
        'start_set': 'Start: {}',
        'end_set': 'End: {}',
        'ok': 'OK',
        'cancel': 'Cancel',
        'equalizer': 'Equalizer',
        'visualization': 'Visualization',
        'filter_format': 'Format:',
        'all_formats': 'All',
        
        # Dialogs
        'info': 'Information',
        'error': 'Error',
        'warning': 'Warning',
        'converter_title': '🎵 Audio Converter',
        'source_files': 'Source Files',
        'settings': '⚙️ Settings',
        'format': 'Format',
        'quality': 'Quality',
        'output_folder': 'Output Folder',
        'same_as_source': 'Same as source',
        'browse': 'Browse...',
        'convert': 'Convert',
        'cancel': 'Cancel',
        'converting': 'Converting...',
        'conversion_complete': 'Conversion Complete!',
        'conversion_errors': 'Completed with errors',
        'close': 'Close',
        'stop': 'Stop',
        'ffmpeg_not_found': 'FFMPEG not found!',
        'ffmpeg_hint': 'FFMPEG is required for the converter.\nPlease place ffmpeg.exe in the app folder or add to PATH.',
        'select_file_to_save': 'Select a file to save',
        'select_files_to_save': 'Select files to save',
        'saved': 'Saved',
        'save_error': 'Save error',
        'studio_processing': 'Studio Processing',
        'studio_processing_desc': 'Applies sound enhancement filters: removes rumble, normalizes loudness, boosts bass and clears up highs.',
        'saving': 'Saving...',
        'saved_count': 'Saved {} of {}',
        'cover_extracted': 'Cover extracted!',
        'error_save': 'Failed to save',
        'no_files_convert': 'No files to convert.',
        
        # File dialogs
        'audio_files': 'Audio Files',
        'all_files': 'All Files',
        'image_files': 'Images',
        'select_audio': 'Select Audio Files',
        'select_folder': 'Select Folder',
        'select_image': 'Select Image',
        'save_image_as': 'Save Image As',
        
        # Update dialog
        'update_available': 'Update Available',
        'new_version_available': 'New version available!',
        'current_version': 'Current version',
        'new_version': 'New version',
        'update_btn': 'Update',
        'later': 'Later',
        'downloading': 'Downloading... {}%',
        'download_progress': 'Downloading: {}%',
        'applying_update': 'Applying update...',
        'download_error': 'Download error!',
        'apply_error': 'Failed to apply update',
        
        # Language
        'language': 'Language / Язык',
        'russian': '🇷🇺 Русский',
        'english': '🇬🇧 English',
        'restart_required': 'Restart the app to apply the new language',
        'success': 'Success',
        'converted_files': 'Converted {} files.',
        'app_running_error': 'Application is already running!',
    }
}

# Global language state
_current_lang = 'ru'

def set_language(lang: str):
    """Set the current language."""
    global _current_lang
    if lang in TRANSLATIONS:
        _current_lang = lang

def get_language() -> str:
    """Get the current language code."""
    return _current_lang

def t(key: str, *args) -> str:
    """Get translated string by key. Supports format arguments."""
    text = TRANSLATIONS.get(_current_lang, {}).get(key, key)
    if args:
        try:
            return text.format(*args)
        except:
            return text
    return text

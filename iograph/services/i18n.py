from __future__ import annotations

from PyQt6.QtCore import QLocale

from .settings import AppSettings, SettingsKeys


class I18nService:
    AUTO_MODE = "auto"
    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = (
        "en",
        "de",
        "fr",
        "es",
        "pt",
        "it",
        "ru",
        "uk",
        "tr",
        "ar",
        "zh-Hans",
        "zh-Hant",
    )

    LANGUAGE_LABELS = {
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
        "es": "Español",
        "pt": "Português",
        "it": "Italiano",
        "ru": "Русский",
        "uk": "Українська",
        "tr": "Türkçe",
        "ar": "العربية",
        "zh-Hans": "简体中文",
        "zh-Hant": "繁體中文",
    }

    _TRANSLATIONS = {
        "de": {
            "Language": "Sprache",
            "Auto (System)": "Automatisch (System)",
            "Hide Settings": "Einstellungen ausblenden",
            "Show Settings": "Einstellungen anzeigen",
            "Check for Updates": "Nach Updates suchen",
            "Checking for Updates...": "Suche nach Updates...",
            "Downloading Update...": "Update wird heruntergeladen...",
        },
        "fr": {
            "Language": "Langue",
            "Auto (System)": "Automatique (Système)",
            "Hide Settings": "Masquer les réglages",
            "Show Settings": "Afficher les réglages",
            "Check for Updates": "Vérifier les mises à jour",
            "Checking for Updates...": "Vérification des mises à jour...",
            "Downloading Update...": "Téléchargement de la mise à jour...",
        },
        "es": {
            "Language": "Idioma",
            "Auto (System)": "Automático (Sistema)",
            "Hide Settings": "Ocultar ajustes",
            "Show Settings": "Mostrar ajustes",
            "Check for Updates": "Buscar actualizaciones",
            "Checking for Updates...": "Buscando actualizaciones...",
            "Downloading Update...": "Descargando actualización...",
        },
        "pt": {
            "Language": "Idioma",
            "Auto (System)": "Automático (Sistema)",
            "File": "Arquivo",
            "Tracking": "Rastreamento",
            "Options": "Opções",
            "Help": "Ajuda",
            "Save Image...": "Salvar imagem...",
            "Save Raw Data...": "Salvar dados RAW...",
            "Reset": "Redefinir",
            "Exit": "Sair",
            "Start": "Iniciar",
            "Ignore Mouse Stops": "Ignorar paradas do mouse",
            "Colorful Scheme": "Esquema colorido",
            "Use Desktop Background": "Usar plano de fundo do desktop",
            "Use Multiple Monitors": "Usar múltiplos monitores",
            "Update Desktop Snapshot": "Atualizar captura do desktop",
            "Check for Updates Automatically": "Verificar atualizações automaticamente",
            "Update now": "Atualizar agora",
            "Resources": "Recursos",
            "About IOGraphica": "Sobre IOGraphica",
            "IOGraph Website": "Site do IOGraph",
            "Get Source Code": "Obter código-fonte",
            "Support IOGraphica": "Apoiar IOGraphica",
            "More": "Mais",
            "Quit": "Encerrar",
            "Hide Settings": "Ocultar configurações",
            "Show Settings": "Mostrar configurações",
            "Check for Updates": "Verificar atualizações",
            "Checking for Updates...": "Verificando atualizações...",
            "Downloading Update...": "Baixando atualização...",
            "Ready": "Pronto",
            "Reset confirmation": "Confirmação de redefinição",
            "Total Time": "Tempo total",
            "Time Period": "Período",
            "Canvas reset": "Tela redefinida",
            "Export is already running": "A exportação já está em execução",
            "Save image": "Salvar imagem",
            "PNG image (*.png)": "Imagem PNG (*.png)",
            "Save Raw Data": "Salvar dados RAW",
            "CSV file (*.csv)": "Arquivo CSV (*.csv)",
            "CSV saved": "CSV salvo",
            "First Graphic Saved": "Primeiro gráfico salvo",
            "Done - your first IOGraph is saved.": "Pronto: seu primeiro IOGraph foi salvo.",
            "Thanks for using IOGraph. If you'd like to support the project, I'd really appreciate it.": "Obrigado por usar o IOGraph. Se quiser apoiar o projeto, eu agradeço muito.",
            "RAW Data Saved": "Dados RAW salvos",
            "Your RAW data is saved.": "Seus dados RAW foram salvos.",
            "If IOGraph is helpful to you, you can support its continued development.": "Se o IOGraph é útil para você, você pode apoiar seu desenvolvimento contínuo.",
            "Desktop background disabled": "Plano de fundo da área de trabalho desativado",
            "About IOGraph": "Sobre o IOGraph",
            "Update download is in progress.\nPlease wait until it finishes.": "O download da atualização está em andamento.\nAguarde até terminar.",
            "Update check is already running.\nPlease wait a few seconds and try again.": "A verificação de atualização já está em andamento.\nAguarde alguns segundos e tente novamente.",
            "Checking for updates...": "Verificando atualizações...",
            "Unable to check for updates:": "Não foi possível verificar atualizações:",
            "You are up to date": "Você está atualizado",
            "No updates found": "Nenhuma atualização encontrada",
            "Update Ready": "Atualização pronta",
            "Update Available": "Atualização disponível",
            "is available.": "está disponível.",
            "Download now?": "Baixar agora?",
            "Update available": "Atualização disponível",
            "Downloading update...": "Baixando atualização...",
            "Update Download": "Download de atualização",
            "Failed to download IOGraph": "Falha ao baixar o IOGraph",
            "Background update download failed": "Falha no download de atualização em segundo plano",
            "Update downloaded": "Atualização baixada",
            "Install Downloaded Update": "Instalar atualização baixada",
            "No downloaded update was found.": "Nenhuma atualização baixada foi encontrada.",
            "Downloaded update file no longer exists.": "O arquivo de atualização baixado não existe mais.",
            "Update installation is already in progress.": "A instalação da atualização já está em andamento.",
            "Automatic install is available only in bundled app.": "A instalação automática está disponível apenas no app empacotado.",
            "Preparing update installation...": "Preparando instalação da atualização...",
            "Installing Update": "Instalando atualização",
            "Automatic install failed. Opening downloaded package for manual installation.": "A instalação automática falhou. Abrindo o pacote baixado para instalação manual.",
            "Automatic install failed:": "A instalação automática falhou:",
            "Opening downloaded package for manual installation.": "Abrindo o pacote baixado para instalação manual.",
            "Language preference saved. Some labels may require app restart to fully apply.": "Preferência de idioma salva. Alguns rótulos podem exigir reinício do app para aplicar totalmente.",
        },
        "it": {
            "Language": "Lingua",
            "Auto (System)": "Automatico (Sistema)",
            "File": "File",
            "Tracking": "Monitoraggio",
            "Options": "Opzioni",
            "Help": "Aiuto",
            "Save Image...": "Salva immagine...",
            "Save Raw Data...": "Salva dati RAW...",
            "Reset": "Reimposta",
            "Exit": "Esci",
            "Start": "Avvia",
            "Ignore Mouse Stops": "Ignora pause del mouse",
            "Colorful Scheme": "Schema colori",
            "Use Desktop Background": "Usa sfondo desktop",
            "Use Multiple Monitors": "Usa più monitor",
            "Update Desktop Snapshot": "Aggiorna snapshot desktop",
            "Check for Updates Automatically": "Controlla aggiornamenti automaticamente",
            "Update now": "Aggiorna ora",
            "Resources": "Risorse",
            "About IOGraphica": "Informazioni su IOGraphica",
            "IOGraph Website": "Sito IOGraph",
            "Get Source Code": "Ottieni codice sorgente",
            "Support IOGraphica": "Supporta IOGraphica",
            "More": "Altro",
            "Quit": "Esci",
            "Hide Settings": "Nascondi impostazioni",
            "Show Settings": "Mostra impostazioni",
            "Check for Updates": "Controlla aggiornamenti",
            "Checking for Updates...": "Controllo aggiornamenti...",
            "Downloading Update...": "Download aggiornamento...",
            "Ready": "Pronto",
            "Reset confirmation": "Conferma reimpostazione",
            "Total Time": "Tempo totale",
            "Time Period": "Intervallo",
            "Canvas reset": "Canvas reimpostato",
            "Export is already running": "L'esportazione è già in esecuzione",
            "Save image": "Salva immagine",
            "PNG image (*.png)": "Immagine PNG (*.png)",
            "Save Raw Data": "Salva dati RAW",
            "CSV file (*.csv)": "File CSV (*.csv)",
            "CSV saved": "CSV salvato",
            "First Graphic Saved": "Primo grafico salvato",
            "Done - your first IOGraph is saved.": "Fatto: il tuo primo IOGraph è stato salvato.",
            "Thanks for using IOGraph. If you'd like to support the project, I'd really appreciate it.": "Grazie per aver usato IOGraph. Se vuoi supportare il progetto, lo apprezzerei molto.",
            "RAW Data Saved": "Dati RAW salvati",
            "Your RAW data is saved.": "I tuoi dati RAW sono stati salvati.",
            "If IOGraph is helpful to you, you can support its continued development.": "Se IOGraph ti è utile, puoi supportarne lo sviluppo continuo.",
            "Desktop background disabled": "Sfondo del desktop disattivato",
            "About IOGraph": "Informazioni su IOGraph",
            "Update download is in progress.\nPlease wait until it finishes.": "Il download dell'aggiornamento è in corso.\nAttendi che finisca.",
            "Update check is already running.\nPlease wait a few seconds and try again.": "Il controllo aggiornamenti è già in corso.\nAttendi qualche secondo e riprova.",
            "Checking for updates...": "Controllo aggiornamenti...",
            "Unable to check for updates:": "Impossibile controllare aggiornamenti:",
            "You are up to date": "Sei aggiornato",
            "No updates found": "Nessun aggiornamento trovato",
            "Update Ready": "Aggiornamento pronto",
            "Update Available": "Aggiornamento disponibile",
            "is available.": "è disponibile.",
            "Download now?": "Scaricare ora?",
            "Update available": "Aggiornamento disponibile",
            "Downloading update...": "Download aggiornamento...",
            "Update Download": "Download aggiornamento",
            "Failed to download IOGraph": "Download di IOGraph non riuscito",
            "Background update download failed": "Download aggiornamento in background non riuscito",
            "Update downloaded": "Aggiornamento scaricato",
            "Install Downloaded Update": "Installa aggiornamento scaricato",
            "No downloaded update was found.": "Nessun aggiornamento scaricato trovato.",
            "Downloaded update file no longer exists.": "Il file di aggiornamento scaricato non esiste più.",
            "Update installation is already in progress.": "L'installazione dell'aggiornamento è già in corso.",
            "Automatic install is available only in bundled app.": "L'installazione automatica è disponibile solo nell'app distribuita.",
            "Preparing update installation...": "Preparazione installazione aggiornamento...",
            "Installing Update": "Installazione aggiornamento",
            "Automatic install failed. Opening downloaded package for manual installation.": "Installazione automatica non riuscita. Apertura del pacchetto scaricato per installazione manuale.",
            "Automatic install failed:": "Installazione automatica non riuscita:",
            "Opening downloaded package for manual installation.": "Apertura del pacchetto scaricato per installazione manuale.",
            "Language preference saved. Some labels may require app restart to fully apply.": "Preferenza lingua salvata. Alcune etichette potrebbero richiedere il riavvio dell'app per applicarsi completamente.",
        },
        "ru": {
            "Language": "Язык",
            "Auto (System)": "Авто (системный)",
            "Hide Settings": "Скрыть настройки",
            "Show Settings": "Показать настройки",
            "Check for Updates": "Проверить обновления",
            "Checking for Updates...": "Проверка обновлений...",
            "Downloading Update...": "Загрузка обновления...",
        },
        "uk": {
            "Language": "Мова",
            "Auto (System)": "Авто (системна)",
            "Hide Settings": "Сховати налаштування",
            "Show Settings": "Показати налаштування",
            "Check for Updates": "Перевірити оновлення",
            "Checking for Updates...": "Перевірка оновлень...",
            "Downloading Update...": "Завантаження оновлення...",
        },
        "tr": {
            "Language": "Dil",
            "Auto (System)": "Otomatik (Sistem)",
            "Hide Settings": "Ayarları Gizle",
            "Show Settings": "Ayarları Göster",
            "Check for Updates": "Güncellemeleri Denetle",
            "Checking for Updates...": "Güncellemeler denetleniyor...",
            "Downloading Update...": "Güncelleme indiriliyor...",
        },
        "ar": {
            "Language": "اللغة",
            "Auto (System)": "تلقائي (النظام)",
            "Hide Settings": "إخفاء الإعدادات",
            "Show Settings": "إظهار الإعدادات",
            "Check for Updates": "التحقق من التحديثات",
            "Checking for Updates...": "جارٍ التحقق من التحديثات...",
            "Downloading Update...": "جارٍ تنزيل التحديث...",
        },
        "zh-Hans": {
            "Language": "语言",
            "Auto (System)": "自动（系统）",
            "Hide Settings": "隐藏设置",
            "Show Settings": "显示设置",
            "Check for Updates": "检查更新",
            "Checking for Updates...": "正在检查更新...",
            "Downloading Update...": "正在下载更新...",
        },
        "zh-Hant": {
            "Language": "語言",
            "Auto (System)": "自動（系統）",
            "Hide Settings": "隱藏設定",
            "Show Settings": "顯示設定",
            "Check for Updates": "檢查更新",
            "Checking for Updates...": "正在檢查更新...",
            "Downloading Update...": "正在下載更新...",
        },
    }

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._mode = self._normalize_mode(
            self._settings.get_str(SettingsKeys.OPTION_LANGUAGE, self.AUTO_MODE)
        )

    @classmethod
    def _normalize_mode(cls, mode: str) -> str:
        normalized = (mode or "").strip()
        if normalized == cls.AUTO_MODE:
            return normalized
        if normalized in cls.SUPPORTED_LANGUAGES:
            return normalized
        lower = normalized.lower()
        if lower in cls.SUPPORTED_LANGUAGES:
            return lower
        return cls.AUTO_MODE

    def current_mode(self) -> str:
        return self._mode

    def set_language_mode(self, mode: str) -> str:
        self._mode = self._normalize_mode(mode)
        self._settings.set(SettingsKeys.OPTION_LANGUAGE, self._mode, sync=True)
        return self._mode

    def effective_language(self) -> str:
        if self._mode != self.AUTO_MODE:
            return self._mode
        return self._resolve_system_language()

    def language_menu_options(self) -> list[tuple[str, str]]:
        options = [(self.AUTO_MODE, self.tr("Auto (System)"))]
        for code in self.SUPPORTED_LANGUAGES:
            options.append((code, self.LANGUAGE_LABELS.get(code, code)))
        return options

    @classmethod
    def _resolve_system_language(cls) -> str:
        locale = QLocale.system()
        bcp47 = (locale.bcp47Name() or "").strip()
        if bcp47.lower().startswith("zh-hant"):
            return "zh-Hant"
        if bcp47.lower().startswith("zh-hans"):
            return "zh-Hans"
        name = (locale.name() or "").strip().lower().replace("-", "_")
        if name.startswith("zh_tw") or name.startswith("zh_hk") or name.startswith("zh_mo"):
            return "zh-Hant"
        if name.startswith("zh_"):
            return "zh-Hans"
        base = (bcp47.split("-", 1)[0] or name.split("_", 1)[0]).lower()
        if base in cls.SUPPORTED_LANGUAGES:
            return base
        return cls.DEFAULT_LANGUAGE

    def tr(self, source_text: str) -> str:
        lang = self.effective_language()
        return self._TRANSLATIONS.get(lang, {}).get(source_text, source_text)

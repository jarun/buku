��    ?                              ,  �  :  �   �  
  �	  Y  �  �   #  v  �       N   :  S   �  6   �  R     	   g     q     �  (   �  '   �  (   �  -     .   B  "   q  -   �     �     �     �  +         ,     ;     J  &   Z  &   �  &   �  '   �  ,   �  -   $      R      c      x      �   %   �      �      �      �      �      !     !     ,!     A!     V!     f!  
   w!     �!     �!     �!  '   �!     �!     "     +"     ?"     O"     ^"  H  m"  /   �#     �#  2	  �#     ,-  O  M.  �  �@  �   *F  �   G  0   �M  �   N  �   �N  �   �O  �   5P     �P  &   �P  -   Q  M   AQ  L   �Q  M   �Q  R   *R  S   }R  9   �R  A   S  /   MS     }S  -   �S  \   �S     (T     HT     fT  H   |T  A   �T  A   U  B   IU  G   �U  H   �U     V  *   :V      eV     �V  Y   �V     �V  >   W     KW     hW  $   �W  ,   �W  /   �W  /   X  *   8X      cX     �X  /   �X     �X  &   �X  D   Y  7   TY  1   �Y  $   �Y  ,   �Y  *   Z     ;Z   [7mbuku (? for help)[0m  
Interrupted. 
PROMPT KEYS:
    1-N                    browse search result indices and/or ranges
    O [id|range [...]]     open search results/indices in GUI browser
                           toggle try GUI browser if no arguments
    a                      open all results in browser
    s keyword [...]        search for records with ANY keyword
    S keyword [...]        search for records with ALL keywords
    d                      match substrings ('pen' matches 'opened')
    r expression           run a regex search
    t [tag, ...]           search by tags; show taglist, if no args
    g taglist id|range [...] [>>|>|<<] [record id|range ...]
                           append, set, remove (all or specific) tags
                           search by taglist id(s) if records are omitted
    n                      show next page of search results
    o id|range [...]       browse bookmarks by indices and/or ranges
    p id|range [...]       print bookmarks by indices and/or ranges
    w [editor|id]          edit and add or update a bookmark
    c id                   copy url at search result index to clipboard
    ?                      show this help
    q, ^D, double Enter    exit buku

 
SYMBOLS:
      >                    url
      +                    comment
      #                    tags

Version %s
Copyright © 2015-2022 %s
License: %s
Webpage: https://github.com/jarun/buku
     --ai                 auto-import bookmarks from web browsers
                         Firefox, Chrome, Chromium, Vivaldi, Edge
    -e, --export file    export bookmarks to Firefox format HTML
                         export XBEL, if file ends with '.xbel'
                         export Markdown, if file ends with '.md'
                         format: [title](url) <!-- TAGS -->
                         export Orgfile, if file ends with '.org'
                         format: *[[url][title]] :tags:
                         export buku DB, if file ends with '.db'
                         combines with search results, if opted
    -i, --import file    import bookmarks from file
                         supports .html .xbel .json .md .org .db
    -p, --print [...]    show record details by indices, ranges
                         print all bookmarks, if no arguments
                         -n shows the last n results (like tail)
    -f, --format N       limit fields in -p or JSON search output
                         N=1: URL; N=2: URL, tag; N=3: title;
                         N=4: URL, title, tag; N=5: title, tag;
                         N0 (10, 20, 30, 40, 50) omits DB index
    -j, --json [file]    JSON formatted output for -p and search.
                         prints to stdout if argument missing.
                         otherwise writes to given file
    --colors COLORS      set output colors in five-letter string
    --nc                 disable color output
    -n, --count N        show N results per page (default 10)
    --np                 do not show the subprompt, run and exit
    -o, --open [...]     browse bookmarks by indices and ranges
                         open a random bookmark, if no arguments
    --oa                 browse all search results immediately
    --replace old new    replace old tag with new tag everywhere
                         delete old tag, if new tag not specified
    --shorten index|URL  fetch shortened url from tny.im service
    --expand index|URL   expand a tny.im shortened url
    --cached index|URL   browse a cached page from Wayback Machine
    --suggest            show similar tags when adding bookmarks
    --tacit              reduce verbosity, skip some confirmations
    --nostdin            do not wait for input (must be first arg)
    --threads N          max network connections in full refresh
                         default N=4, min N=1, max N=10
    -V                   check latest upstream version available
    -g, --debug          show debug information and verbose logs     -a, --add URL [tag, ...]
                         bookmark URL with comma-separated tags
    -u, --update [...]   update fields of an existing bookmark
                         accepts indices and ranges
                         refresh title and desc if no edit options
                         if no arguments:
                         - update results when used with search
                         - otherwise refresh all titles and desc
    -w, --write [editor|index]
                         edit and add a new bookmark in editor
                         else, edit bookmark at index in EDITOR
                         edit last bookmark, if index=-1
                         if no args, edit new bookmark in EDITOR
    -d, --delete [...]   remove bookmarks from DB
                         accepts indices or a single range
                         if no arguments:
                         - delete results when used with search
                         - otherwise delete all bookmarks
    -h, --help           show this information and exit
    -v, --version        show the program version and exit     -l, --lock [N]       encrypt DB in N (default 8) # iterations
    -k, --unlock [N]     decrypt DB in N (default 8) # iterations     -s, --sany [...]     find records with ANY matching keyword
                         this is the default search option
    -S, --sall [...]     find records matching ALL the keywords
                         special keywords -
                         "blank": entries with empty title/tag
                         "immutable": entries with locked title
    --deep               match substrings ('pen' matches 'opens')
    -r, --sreg expr      run a regex search
    -t, --stag [tag [,|+] ...] [- tag, ...]
                         search bookmarks by tags
                         use ',' to find entries matching ANY tag
                         use '+' to find entries matching ALL tags
                         excludes entries with tags after ' - '
                         list all tags, if no search keywords
    -x, --exclude [...]  omit records matching specified keywords  exists. Overwrite? (y/n):  # Add COMMENTS in next line(s). Leave blank to web fetch, "-" for no comments. # Add TITLE in next line (single line). Leave blank to web fetch, "-" for no title. # Add comma-separated TAGS in next line (single line). # Lines beginning with "#" will be stripped.
# Add URL in next line (single line). 0 results All bookmarks deleted Cannot open editor Could not import bookmarks from Firefox. Could not import bookmarks from Vivaldi Could not import bookmarks from chromium Could not import bookmarks from google-chrome Could not import bookmarks from microsoft-edge Delete the search results? (y/n):  Delete the tag(s) from ALL bookmarks? (y/n):  Delete this bookmark? (y/n):  ENCRYPTION OPTIONS Edit aborted Failed to locate suitable clipboard utility File decrypted File encrypted GENERAL OPTIONS Generate auto-tag (YYYYMonDD)? (y/n):  Import bookmarks from Firefox? (y/n):  Import bookmarks from Vivaldi? (y/n):  Import bookmarks from chromium? (y/n):  Import bookmarks from google chrome? (y/n):  Import bookmarks from microsoft edge? (y/n):  Index %d deleted Index %d moved to %d Index %d updated Interrupted. Invalid index or range or combination Invalid input Latest upstream release is %s Malformed URL Malformed URL
 No bookmarks deleted No matching index No matching index %d No matching index %s No more results No records found POWER TOYS Remove ALL bookmarks? (y/n):  SEARCH OPTIONS This is the latest release Title: [%s]
[92mIndex %d: updated[0m
 URL copied to tmux buffer. Update ALL bookmarks? (y/n):  buku (? for help):  deep search off deep search on similar tags:
 Project-Id-Version: PACKAGE VERSION
POT-Creation-Date: 2023-01-18 16:27+0300
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language-Team: LANGUAGE <LL@li.org>
Language: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Generated-By: pygettext.py 1.5
 [7mbuku (? вызов справки)[0m  
Прервано. 
PROMPT KEYS:
    1-N                    просмотр индекса(ов) и/или диапазона(ов)
                           результатов поиска
    O [id|диапазон [...]]  открыть результаты поиска/индексы в браузере
                           с графическим интерфейсом
                           toggle try GUI browser if no arguments
    a                      открыть все результаты в браузере
    s ключевое слово [...] искать записи с ЛЮБЫМ ключевым словом
    S ключевое слово [...] искать записи со ВСЕМИ ключевыми словами
    d                      соответствие подстрокам ('pen' соответствует
                           'opened')
    r выражение            поиск по регулярному выражению
    t [тег, ...]           поиск по тегам; показать список тегов,
                           если нет аргументов
    g id теглиста|диапазон [...] [>>|>|<<] [id записи|диапазон ...]
                           добавить, выбрать, удалить (все или
                           определенные) теги
                           поиск по идентификатору(ам) списка тегов,
                           если записи опущены
    n                      показать следующую страницу результатов поиска
    o id|диапазон [...]    просматривать закладки по индексам и/или диапазонам
    p id|диапазон [...]    печатать закладки по индексам и/или диапазонам
    w [редактор|id]        изменить и добавить или обновить закладку
    c id                   скопировать URL-адрес индекса из результатов
                           поиска в буфер обмена
    ?                      показать эту справку
    q, ^D, двойной Enter   выход из buku

 
СИМВОЛЫ:
      >                    url
      +                    комментарий
      #                    теги

Версия %s
Авторские права © 2015-2022 %s
Лицензия: %s
Страница в Интернете: https://github.com/jarun/buku
     --ai                 автоимпорт закладок из веб-браузеров
                         Firefox, Chrome, Chromium, Vivaldi, Edge
    -e, --export файл    экспортировать закладки в формат Firefox
                         HTML
                         экспорт в XBEL, если файл заканчивается
                         '.xbel'
                         экспорт в Markdown, если файл заканчивается
                         на '.md'
                         формат: [заголовок](url) <!-- ТЕГИ -->
                         экспорт в Orgfile, если файл заканчивается
                         на '.org'
                         формат: *[[url][заголовок]] :теги:
                         экспорт в buku DB, если файл заканчивается
                         на '.db'
                         комбинируется с результатами поиска, если
                         выбрано
    -i, --import файл    импортировать закладки из файла
                         поддерживает .html .xbel .json .md .org .db
    -p, --print [...]    показать подробности записи по индексам,
                         диапазонам
                         вывести все закладки, если нет аргументов
    -n                   показывает последние n результатов (как tail)
    -f, --format N       ограничить поля в -p или выводе поиска JSON
                         N=1: URL; N=2: URL, tag; N=3: title;
                         N=4: URL, title, tag; N=5: title, tag;
                         N0 (10, 20, 30, 40, 50) опускает индекс БД
    -j, --json [файл]    вывод в формате JSON для -p и поиска.
                         печатает на стандартный вывод, если
                         аргумент отсутствует.
                         в противном случае пишет в данный файл
    --colors COLORS      установить выходные цвета в пятибуквенной
                         строке
    --nc                 отключить цветной вывод
    -n, --count N        показывать N результатов на странице
                         (по умолчанию 10)
    --np                 не показывать подсказку, запустить и выйти
    -o, --open [...]     просматривать закладки по индексам и
                         диапазонам
                         открыть случайную закладку, если нет
                         аргументов
    --oa                 просмотреть все результаты поиска сразу
    --replace старый новый
                         заменить везде старый тег новым тегом
                         удалить старый тег, если новый тег не указан
    --shorten индекс|URL получить укороченный URL из сервиса tny.im
    --expand индекс|URL  расширить сокращенный URL tny.im
    --cached индекс|URL  просмотреть кешированную страницу из
                         Wayback Machine
    --suggest            показывать похожие теги при добавлении
                         закладок
    --tacit              уменьшить многословие, пропустить некоторые
                         подтверждения
    --nostdin            не ждать ввода (должен быть первым
                         аргументом)
    --threads N          максимальное количество сетевых соединений
                         при полном обновлении
                         по умолчанию N=4, мин N=1, макс N=10
    -V                   проверьте последнюю доступную версию
                         основной ветки
    -g, --debug          показать отладочную информацию и подробные
                         журналы     -a, --add URL [тег, ...]
                         добавить URL закладки с тегами, разделенными
                         запятыми
    -u, --update [...]   update fields of an existing bookmark
                         accepts indices and ranges
                         refresh title and desc if no edit options
                         if no arguments:
                         - update results when used with search
                         - otherwise refresh all titles and desc
    -w, --write [editor|index]
                         edit and add a new bookmark in editor
                         else, edit bookmark at index in EDITOR
                         edit last bookmark, if index=-1
                         if no args, edit new bookmark in EDITOR
    -d, --delete [...]   удалить закладки из БД
                         принимает индексы или один диапазон
                         если нет аргументов:
                         - удаляет результаты при использовании с
                         поиском
                         - иначе удалит все закладки
    -h, --help           показать эту информацию и выйти
    -v, --version        показать версию программы и выйти     -l, --lock [N]       зашифровать БД в N (по умолчанию 8) # итераций
    -k, --unlock [N]     расшифровать БД за N (по умолчанию 8) # итераций     -s, --sany [...]     найти записи с ЛЮБЫМ совпадающим ключевым
                         словом
                         это опция поиска по умолчанию
    -S, --sall [...]     найти записи, соответствующие ВСЕМ ключевым
                         словам
                         специальные ключевые слова -
                         "blank": записи с пустым заголовком/тегом
                         "immutable": записи с заблокированным
                         заголовком
    --deep               соответствие подстрокам ('pen' соответствует
                         'opened')
    -r, --sreg выражение поиск по регулярному выражению
    -t, --stag [тег [,|+] ...] [- тег, ...]
                         искать закладки по тегам
                         используйте ',' для поиска записей,
                         соответствующих ЛЮБОМУ тегу
                         используйте '+', чтобы найти записи,
                         соответствующие ВСЕМ тегам
                         исключает записи с тегами после ' - '
                         перечислить все теги, если нет ключевых
                         слов для поиска
    -x, --exclude [...]  пропустить записи, соответствующие
                         указанным ключевым словам существует. Перезаписать?  # Добавьте КОММЕНТАРИИ в следующую строку (строки). Оставьте пустым для загрузки из Интернета, "-" без комментариев. # Добавьте ЗАГОЛОВОК в следующую строку (одна строка). Оставьте пустым для загрузки из Интернета, "-" без заголовка. # Добавить ТЕГИ, разделенные запятыми, в следующей строке (одна строка). # Строки, начинающиеся с "#", будут удалены.
#Добавьте URL в следующую строку (одна строка). 0 результатов Все закладки удалены Не могу открыть редактор Не удалось импортировать закладки из Firefox. Не удалось импортировать закладки из Vivaldi Не удалось импортировать закладки из chromium Не удалось импортировать закладки из google-chrome Не удалось импортировать закладки из microsoft-edge Удалить результаты поиска? (y/n):  Удалить тег(и) из ВСЕХ закладок? (y/n):  Удалить эту закладку? (y/n):  ОПЦИИ ШИФРОВАНИЯ Редактирование прервано Не удалось найти подходящую утилиту буфера обмена Файл расшифрован Файл зашифрован ОБЩИЕ ОПЦИИ Сгенерировать авто-тег (ГГГГМесДД)? (y/n):  Импортировать закладки из Firefox? (y/n):  Импортировать закладки из Vivaldi? (y/n):  Импортировать закладки из chromium? (y/n):  Импортировать закладки из google chrome? (y/n):  Импортировать закладки из microsoft edge? (y/n):  Индекс %d удален Индекс %d перемещен на %d Индекс %d обновлен Прервано. Недопустимый индекс или диапазон или комбинация Неверный ввод Последний выпуск основной ветки %s Неправильный URL Неправильный URL
 Закладки не удалены Нет подходящего индекса Нет подходящего индекса %d Нет подходящего индекса %s Нет больше результатов Записи не найдены МОЩНЫЕ ИГРУШКИ Удалить ВСЕ закладки? (y/n):  ОПЦИИ ПОИСКА Это последний выпуск Заголовок: [%s]
[92mИндекс %d: обновлен[0m
 URL-адрес скопирован в буфер tmux. Обновить ВСЕ закладки? (y/n):  buku (? вызов справки):  глубокий поиск выключен глубокий поиск включен похожие теги:
 
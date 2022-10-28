### Баян полиция - болиция

#### Спецификация
1. Бот слушает все сообщения в чате и реагирует на картинку, если она приложена к медии
2. При обнаружении картинки он делает ее average или  preceptional (тут надо разобраться что лучше для пресечения коллизий и оптимизации сравнения почти одинаковых картинок, например с вотермарками или на разных языках) и сохраняет ее в базу с id этого сообщения
3. Если в чат отправлено еще одно сообщение с картинкой, он проходится по индексу хэша картинок. При совпадении хэша с хэшем предыдущимих картинок, выводит в чат баян и прикладывает сообщение, где картинка уже была.

#### Технологии
1. Python - PIL, ImageHash, Pyrogram
2. MongoDB
3. Docker/Podman

#### Возможные проблемы
1. Коллизии - библиотека надежная, не должно быть при относительно небольшом обьеме
2. Обычные картинки, которые не являются контентом и которые используются как средство общения - идея устраивать голосование, является ли картинка баяном. Если да, то человек банится на 5 минут. Если нет, то картинке добавляется флаг неактивной и в дальнейшем при проверку хешей она не участвует.  (Можно еще прикладывать картинку "Соре, быканул чет")
3. Подгрузка всей предыдущей медии, если в чате есть история - этот процесс будет занимать время

#### Задачи на 28.10.2022
- [] добавить логи в функциях и логгирование в файл
- [] убирать документ из проверки, если человек оправдан
- [] при обработке истории сообщений добавлять более старый message_id в базу
- [] время мьюта рандомайзится в соотношении с ratio голосования

- [] возможно сменить phash на avg hash для большего разброса по коллизиям 
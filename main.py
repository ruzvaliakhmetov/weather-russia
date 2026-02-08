import os
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta

import requests
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot, InputSticker
from telegram.error import BadRequest


IMAGES_DIR = Path(__file__).parent / "images"
ICONS_DIR = IMAGES_DIR / "icons"  # сюда кладём PNG-иконки погоды 225x225 (01d.png, 02n.png и т.п.)


# ==========================
#   НАСТРОЙКИ МАКЕТА
# ==========================

@dataclass
class BlockLayout:
    x: int | None        # если right_align=False: x от левого края
                         # если right_align=True: отступ от правого края
    y: int | None        # y от верхнего края; если None — используем default_y или считаем от низа
    font_size: int
    right_align: bool = False  # правая выключка по x


@dataclass
class DetailsLayout:
    x: int
    y: int
    font_size: int
    line_spacing: int = 6


# ---- Лэйауты блоков (можно твикать под себя) ----

# Город
CITY_LAYOUT = BlockLayout(
    x=50,   # None = центр по горизонтали
    y=400,   # None = автоматически чуть выше низа
    font_size=58,
)

# Температура (цифры) — ПРАВАЯ ВЫКЛЮЧКА
# x = отступ от ПРАВОГО края стикера
TEMP_LAYOUT = BlockLayout(
    x=80,          # правый край цифр будет в 80 px от правого края картинки
    y=30,
    font_size=140,
    right_align=True,
)

# Блок "°C" — отдельный независимый блок
DEGREE_LAYOUT = BlockLayout(
    x=430,          # обычный x от левого края
    y=56,          # можешь поставить None и задать default_y при вызове
    font_size=42,
    right_align=False,
)

# День (например "07")
DAY_LAYOUT = BlockLayout(
    x=396,
    y=310,
    font_size=48,
)

# Месяц (например "Dec")
MONTH_LAYOUT = BlockLayout(
    x=396,
    y=280,
    font_size=30,
)

# Время (например "20:55")
TIME_LAYOUT = BlockLayout(
    x=400,
    y=366,
    font_size=20,
)

# Блок деталей (humidity, wind, conditions) — три строки
DETAILS_LAYOUT = DetailsLayout(
    x=50,
    y=290,       # стартовая Y для первой строки
    font_size=30,
    line_spacing=6,
)

# Позиция иконки погоды (из локальных PNG 225x225)
ICON_X = 0
ICON_Y = 0
ICON_SIZE = (225, 225)


# ==========================
#   КОНФИГ ГОРОДОВ
# ==========================

@dataclass
class CityConfig:
    name: str          # как написать город на стикере
    query: str         # как отдать город в API
    emoji: str         # эмодзи для стикера
    output: str        # куда сохранить png
    background: str    # фон города (PNG), путь относительно IMAGES_DIR
    tz_offset_hours: int = 0  # смещение от UTC, для локального времени города


CITIES = [
    CityConfig(
        name="Tula",
        query="Tula,RU",
        emoji="🏙️",
        output="sticker_tula.png",
        background="bg_tula.png",
        tz_offset_hours=3,   # UTC+3
    ),
    CityConfig(
        name="Moscow",
        query="Moscow,RU",
        emoji="🏙️",
        output="sticker_moscow.png",
        background="bg_moscow.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Korolev",
        query="Korolev,RU",
        emoji="🏙️",
        output="sticker_korolev.png",
        background="bg_korolev.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Odintsovo",
        query="Odintsovo,RU",
        emoji="🏙️",
        output="sticker_odintsovo.png",
        background="bg_odintsovo.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Ramenskoe",
        query="Ramenskoye,RU",
        emoji="🏙️",
        output="sticker_ramenskoe.png",
        background="bg_ramenskoe.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="St. Petersburg",
        query="Saint Petersburg,RU",
        emoji="🏙️",
        output="sticker_saintpetersburg.png",
        background="bg_petersburg.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Murmansk",
        query="Murmansk,RU",
        emoji="🏙️",
        output="sticker_murmansk.png",
        background="bg_murmansk.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Kondopoga",
        query="Kondopoga,RU",
        emoji="🏙️",
        output="sticker_kondopoga.png",
        background="bg_kondopoga.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Petrozavodsk",
        query="Petrozavodsk,RU",
        emoji="🏙️",
        output="sticker_petrozavodsk.png",
        background="bg_petrozavodsk.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Krasnodar",
        query="Krasnodar,RU",
        emoji="🏙️",
        output="sticker_krasnodar.png",
        background="bg_krasnodar.png",
        tz_offset_hours=3,   # UTC+3
    ),
    CityConfig(
        name="Vladikavkaz",
        query="Vladikavkaz,RU",
        emoji="🏙️",
        output="sticker_vladikavkaz.png",
        background="bg_vladikavkaz.png",
        tz_offset_hours=3,   # UTC+3
    ),
    CityConfig(
        name="Rostov-on-Don",
        query="Rostov-na-Donu,RU",
        emoji="🏙️",
        output="sticker_rostovondon.png",
        background="bg_rostovondon.png",
        tz_offset_hours=3,   # UTC+3
    ),
    CityConfig(
        name="Ryazan",
        query="Ryazan,RU",
        emoji="🏙️",
        output="sticker_ryazan.png",
        background="bg_ryazan.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Voronezh",
        query="Voronezh,RU",
        emoji="🏙️",
        output="sticker_voronezh.png",
        background="bg_voronezh.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="N. Novgorod",
        query="Nizhny Novgorod,RU",
        emoji="🏙️",
        output="sticker_novgorod.png",
        background="bg_novgorod.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Volgograd",
        query="Volgograd,RU",
        emoji="🏙️",
        output="sticker_volgograd.png",
        background="bg_volgograd.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Penza",
        query="Penza,RU",
        emoji="🏙️",
        output="sticker_penza.png",
        background="bg_penza.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Yoshkar-Ola",
        query="Yoshkar-Ola,RU",
        emoji="🏙️",
        output="sticker_yoshkarola.png",
        background="bg_yoshkarola.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Kazan",
        query="Kazan,RU",
        emoji="🏙️",
        output="sticker_kazan.png",
        background="bg_kazan.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Naryan-Mar",
        query="Nar'yan-Mar,RU",
        emoji="🏙️",
        output="sticker_naryanmar.png",
        background="bg_naryanmar.png",
        tz_offset_hours=3,  # UTC+3
    ),
    CityConfig(
        name="Samara",
        query="Samara,RU",
        emoji="🏙️",
        output="sticker_samara.png",
        background="bg_samara.png",
        tz_offset_hours=4,  # примерно UTC+4
    ),
    CityConfig(
        name="Ukhta",
        query="Ukhta,RU",
        emoji="🏙️",
        output="sticker_ukhta.png",
        background="bg_ukhta.png",
        tz_offset_hours=4,  # примерно UTC+4
    ),
    CityConfig(
        name="Neftekamsk",
        query="Neftekamsk,RU",
        emoji="🏙️",
        output="sticker_neftekamsk.png",
        background="bg_neftekamsk.png",
        tz_offset_hours=5,  # примерно UTC+5
    ),
    CityConfig(
        name="Ufa",
        query="Ufa,RU",
        emoji="🏙️",
        output="sticker_ufa.png",
        background="bg_ufa.png",
        tz_offset_hours=5,  # примерно UTC+5
    ),
    CityConfig(
        name="Perm",
        query="Perm,RU",
        emoji="🏙️",
        output="sticker_perm.png",
        background="bg_perm.png",
        tz_offset_hours=5,  # UTC+5
    ),
    CityConfig(
        name="Ekaterinburg",
        query="Yekaterinburg,RU",
        emoji="🏙️",
        output="sticker_ekaterinburg.png",
        background="bg_ekaterinburg.png",
        tz_offset_hours=5,  # UTC+5
    ),
    CityConfig(
        name="Chelyabinsk",
        query="Chelyabinsk,RU",
        emoji="🏙️",
        output="sticker_chelyabinsk.png",
        background="bg_chelyabinsk.png",
        tz_offset_hours=5,  # UTC+5
    ),
    CityConfig(
        name="Tyumen",
        query="Tyumen,RU",
        emoji="🏙️",
        output="sticker_tyumen.png",
        background="bg_tyumen.png",
        tz_offset_hours=5,  # UTC+5
    ),
    CityConfig(
        name="Omsk",
        query="Omsk,RU",
        emoji="🏙️",
        output="sticker_omsk.png",
        background="bg_omsk.png",
        tz_offset_hours=6,  # UTC+6
    ),
    CityConfig(
        name="Novosibirsk",
        query="Novosibirsk,RU",
        emoji="🏙️",
        output="sticker_novosibirsk.png",
        background="bg_novosibirsk.png",
        tz_offset_hours=7,  # UTC+7
    ),
    CityConfig(
        name="Tomsk",
        query="Tomsk,RU",
        emoji="🏙️",
        output="sticker_tomsk.png",
        background="bg_tomsk.png",
        tz_offset_hours=7,  # UTC+7
    ),
    CityConfig(
        name="Barnaul",
        query="Barnaul,RU",
        emoji="🏙️",
        output="sticker_barnaul.png",
        background="bg_barnaul.png",
        tz_offset_hours=7,  # UTC+7
    ),
    CityConfig(
        name=" ",
        query="Blagoveshchensk,RU",
        emoji="🏙️",
        output="sticker_blagoveshchensk.png",
        background="bg_blagoveshchensk.png",
        tz_offset_hours=9,  # UTC+9
    ),
    CityConfig(
        name="Oymyakon",
        query="Oymyakon,RU",
        emoji="🏙️",
        output="sticker_oymyakon.png",
        background="bg_oymyakon.png",
        tz_offset_hours=10,  # UTC+10
    ),
    CityConfig(
        name="Vladivostok",
        query="Vladivostok,RU",
        emoji="🏙️",
        output="sticker_vladivostok.png",
        background="bg_vladivostok.png",
        tz_offset_hours=10,  # UTC+10
    ),
]


# ==========================
#   ШРИФТ
# ==========================

def get_font(size: int) -> ImageFont.FreeTypeFont:
    font_paths = [
        "font.ttf",
        "Font.ttf",
        "fonts/font.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


# ==========================
#   ПОГОДА
# ==========================

@dataclass
class WeatherInfo:
    temp: float
    humidity: int
    wind_speed: float
    description: str
    condition_main: str  # Clear, Clouds, Rain и т.п.
    icon_code: str       # код иконки, например "01d"


def fetch_weather(city: CityConfig) -> WeatherInfo:
    api_key = os.environ["WEATHER_API_KEY"]
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city.query,
        "appid": api_key,
        "units": "metric",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    main = data["main"]
    wind = data.get("wind", {})
    weather0 = data["weather"][0]

    return WeatherInfo(
        temp=main["temp"],
        humidity=main["humidity"],
        wind_speed=wind.get("speed", 0.0),
        description=weather0.get("description", "").capitalize(),
        condition_main=weather0.get("main", "Default"),
        icon_code=weather0.get("icon", ""),  # например: "01d"
    )


# ==========================
#   РИСОВАЛКИ
# ==========================

def _draw_text_block(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    text: str,
    layout: BlockLayout,
    *,
    default_x: int | None = None,
    default_y: int | None = None,
    fill=(255, 255, 255, 255),
) -> tuple[int, int, int, int]:
    """
    Универсальный рисователь текста.

    - Если layout.x не None:
        - при right_align=False: x — от левого края;
        - при right_align=True: x — от правого края (отступ), текст выровнен по правому краю.
    - Если layout.x None, но задан default_x — используем его.
    - Иначе центрируем по горизонтали.

    Аналогично с y: layout.y / default_y / позиция "чуть выше низа".
    """
    font = get_font(layout.font_size)
    tb = draw.textbbox((0, 0), text, font=font)
    text_w = tb[2] - tb[0]
    text_h = tb[3] - tb[1]

    # ---------- X ----------
    if layout.x is not None:
        if layout.right_align:
            # x — отступ от ПРАВОГО края, делаем правую выключку
            x = img.width - layout.x - text_w
        else:
            # обычный x от левого края
            x = layout.x
    elif default_x is not None:
        x = default_x
    else:
        # центрируем, если ничего не задано
        x = (img.width - text_w) // 2

    # ---------- Y ----------
    if layout.y is not None:
        y = layout.y
    elif default_y is not None:
        y = default_y
    else:
        # по умолчанию — чуть выше низа (для города, если не задано иное)
        y = img.height - text_h - 40

    draw.text((x, y), text, font=font, fill=fill)
    return x, y, text_w, text_h


def _draw_details_block(draw: ImageDraw.ImageDraw, img: Image.Image, weather: WeatherInfo) -> None:
    font = get_font(DETAILS_LAYOUT.font_size)
    lines = [
        f"Humidity: {weather.humidity}%",
        f"Wind: {weather.wind_speed:.1f} m/s",
        weather.description,
    ]

    x = DETAILS_LAYOUT.x
    y = DETAILS_LAYOUT.y

    for line in lines:
        lb = draw.textbbox((0, 0), line, font=font)
        h = lb[3] - lb[1]
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += h + DETAILS_LAYOUT.line_spacing


def _paste_icon(img: Image.Image, icon_code: str) -> None:
    if not icon_code:
        return

    icon_path = ICONS_DIR / f"{icon_code}.png"
    if not icon_path.exists():
        print(f"[warn] icon not found: {icon_path}")
        return

    icon = Image.open(icon_path).convert("RGBA")
    if icon.size != ICON_SIZE:
        icon = icon.resize(ICON_SIZE, Image.LANCZOS)

    # Вклеиваем иконку в левый верхний угол
    img.alpha_composite(icon, (ICON_X, ICON_Y))


# ==========================
#   ГЕНЕРАЦИЯ КАРТИНКИ
# ==========================

def generate_weather_image(
    city: CityConfig,
    weather: WeatherInfo,
    output_path: str,
    day_text: str,
    month_text: str,
    time_text: str,
) -> None:
    # --- фон города ---
    bg_path = IMAGES_DIR / city.background
    if not bg_path.exists():
        raise FileNotFoundError(
            f"Background image not found: {bg_path}. "
            f"Put city backgrounds (e.g. {city.background}) into {IMAGES_DIR}"
        )

    img = Image.open(bg_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # --- иконка погоды ---
    _paste_icon(img, weather.icon_code)

    # --- ТЕМПЕРАТУРА (цифры) с правой выключкой (через TEMP_LAYOUT) ---
    temp_text = f"{round(weather.temp):d}"
    _draw_text_block(
        draw,
        img,
        temp_text,
        TEMP_LAYOUT,
        default_y=70,  # на случай, если TEMP_LAYOUT.y = None
    )

    # --- БЛОК "°C" — полностью независим ---
    _draw_text_block(
        draw,
        img,
        "°C",
        DEGREE_LAYOUT,
        default_y=70,  # можно изменить/убрать, если хочешь другой дефолт
    )

    # --- Город ---
    _draw_text_block(
        draw,
        img,
        city.name,
        CITY_LAYOUT,
        # default_y не задаём — по умолчанию город внизу
    )

    # --- Дата / время обновления ---
    _draw_text_block(draw, img, day_text, DAY_LAYOUT)
    _draw_text_block(draw, img, month_text, MONTH_LAYOUT)
    _draw_text_block(draw, img, time_text, TIME_LAYOUT)

    # --- Детали (3 строки) ---
    _draw_details_block(draw, img, weather)

    img.save(output_path, format="PNG")


# ==========================
#   ОБНОВЛЕНИЕ СТИКЕРОВ
# ==========================

async def update_stickers() -> None:
    token = os.environ["BOT_TOKEN"]
    set_name = os.environ["STICKER_SET_NAME"]
    set_title = os.environ["STICKER_SET_TITLE"]
    owner_user_id = int(os.environ["TELEGRAM_USER_ID"])

    bot = Bot(token)

    new_stickers: list[InputSticker] = []

    for city in CITIES:
        weather = fetch_weather(city)

        # Локальное время города по его часовому поясу (через фиксированный offset от UTC)
        utc_now = datetime.utcnow()
        city_now = utc_now + timedelta(hours=city.tz_offset_hours)

        day_text = city_now.strftime("%d")     # "07"
        month_text = city_now.strftime("%b")   # "Dec"
        time_text = city_now.strftime("%H:%M") # "20:55"

        generate_weather_image(city, weather, city.output, day_text, month_text, time_text)

        with open(city.output, "rb") as f:
            uploaded = await bot.upload_sticker_file(
                user_id=owner_user_id,
                sticker=f,
                sticker_format="static",
            )

        new_stickers.append(
            InputSticker(
                sticker=uploaded.file_id,
                emoji_list=[city.emoji],
                format="static",
            )
        )

    # 2) Пробуем получить набор
    try:
        sticker_set = await bot.get_sticker_set(set_name)
    except BadRequest as e:
        msg = getattr(e, "message", str(e)).lower()
        print("get_sticker_set error:", msg)
        if "stickerset_invalid" in msg or "stickerset not found" in msg:
            # набора нет — создаём новый сразу со всеми городами
            await bot.create_new_sticker_set(
                user_id=owner_user_id,
                name=set_name,
                title=set_title,
                stickers=new_stickers,
                sticker_type="regular",
            )
            print(f"Created new sticker set {set_name} with weather stickers")
            return
        else:
            raise

    # 3) Набор существует — делаем replace там, где можем
    old_stickers = sticker_set.stickers
    old_count = len(old_stickers)
    new_count = len(new_stickers)
    common = min(old_count, new_count)

    # 3a) replace для общих позиций
    for i in range(common):
        old_id = old_stickers[i].file_id
        new_st = new_stickers[i]
        try:
            await bot.replace_sticker_in_set(
                user_id=owner_user_id,
                name=set_name,
                old_sticker=old_id,
                sticker=new_st,
            )
            print(f"Replaced sticker {old_id} with new one at position {i}")
        except BadRequest as e:
            print("replace_sticker_in_set error:", getattr(e, "message", str(e)))

    # 3б) если новых больше — добавляем хвост
    if new_count > old_count:
        for i in range(common, new_count):
            st = new_stickers[i]
            try:
                await bot.add_sticker_to_set(
                    user_id=owner_user_id,
                    name=set_name,
                    sticker=st,
                )
                print(f"Added extra sticker at position {i}")
            except BadRequest as e:
                print("add_sticker_to_set error:", getattr(e, "message", str(e)))

    # 3в) если старых больше — удаляем лишние в конце
    elif old_count > new_count:
        for i in range(common, old_count):
            old_id = old_stickers[i].file_id
            try:
                await bot.delete_sticker_from_set(old_id)
                print(f"Deleted extra old sticker {old_id} at position {i}")
            except BadRequest as e:
                print("delete_sticker_from_set error:", getattr(e, "message", str(e)))

    print(f"Updated sticker set {set_name} with weather for {new_count} cities")


if __name__ == "__main__":
    import asyncio

    asyncio.run(update_stickers())

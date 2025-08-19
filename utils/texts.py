# utils/texts.py
from typing import Dict

TEXTS: Dict[str, Dict[str, str]] = {
    # ------- COMMON -------
    "welcome": {
        "ru": "🌞 Добро пожаловать в SUNERA! Выберите пункт меню:",
        "en": "🌞 Welcome to SUNERA! Choose an option:",
        "es": "🌞 ¡Bienvenido a SUNERA! Elige una opción:",
        "pl": "🌞 Witamy w SUNERA! Wybierz opcję:",
        "de": "🌞 Willkommen bei SUNERA! Wählen Sie eine Option:",
        "uk": "🌞 Ласкаво просимо до SUNERA! Оберіть пункт меню:",
    },
    "menu_about": {"ru": "ℹ️ О компании","en": "ℹ️ About us","es": "ℹ️ Sobre la empresa","pl": "ℹ️ O firmie","de": "ℹ️ Über uns","uk": "ℹ️ Про компанію"},
    "menu_services": {"ru": "☀️ Услуги","en": "☀️ Services","es": "☀️ Servicios","pl": "☀️ Usługi","de": "☀️ Leistungen","uk": "☀️ Послуги"},
    "menu_form": {"ru": "📩 Заявка/Консультация","en": "📩 Request/Consultation","es": "📩 Solicitud/Consulta","pl": "📩 Zgłoszenie/Konsultacja","de": "📩 Anfrage/Beratung","uk": "📩 Заявка/Консультація"},
    "menu_credit": {"ru": "💳 Кредитный калькулятор","en": "💳 Loan calculator","es": "💳 Calculadora de crédito","pl": "💳 Kalkulator kredytu","de": "💳 Kreditrechner","uk": "💳 Кредитний калькулятор"},
    "menu_solar": {"ru": "🔆 Солнечный калькулятор","en": "🔆 Solar calculator","es": "🔆 Calculadora solar","pl": "🔆 Kalkulator PV","de": "🔆 PV-Rechner","uk": "🔆 Сонячний калькулятор"},
    "menu_site": {"ru": "🌐 Сайт","en": "🌐 Website","es": "🌐 Sitio web","pl": "🌐 Strona","de": "🌐 Website","uk": "🌐 Вебсайт"},
    "menu_whatsapp": {"ru": "💬 WhatsApp","en": "💬 WhatsApp","es": "💬 WhatsApp","pl": "💬 WhatsApp","de": "💬 WhatsApp","uk": "💬 WhatsApp"},
    "menu_call": {"ru": "📞 Позвонить","en": "📞 Call us","es": "📞 Llamar","pl": "📞 Zadzwoń","de": "📞 Anrufen","uk": "📞 Зателефонувати"},
    "menu_lang": {"ru": "🌍 Сменить язык","en": "🌍 Change language","es": "🌍 Cambiar idioma","pl": "🌍 Zmień język","de": "🌍 Sprache ändern","uk": "🌍 Змінити мову"},

    "unknown": {
        "ru": "Не понял. Пожалуйста, используйте меню.",
        "en": "I didn't understand. Please use the menu.",
        "es": "No entendí. Por favor, usa el menú.",
        "pl": "Nie zrozumiałem. Użyj menu.",
        "de": "Ich habe das nicht verstanden. Bitte verwenden Sie das Menü.",
        "uk": "Не зрозумів. Будь ласка, користуйтеся меню.",
    },
    "about_text": {
        "ru": "☀️ SUNERA — проектирование и установка солнечных систем. Гибридные, сетевые, автономные решения. Помогаем с субсидиями и финансированием.",
        "en": "☀️ SUNERA — design and installation of solar PV systems. Hybrid, grid-tied, off-grid. We help with subsidies and financing.",
        "es": "☀️ SUNERA — diseño e instalación de sistemas fotovoltaicos. Híbridos, conectados a red, aislados. Ayudamos con subvenciones y financiación.",
        "pl": "☀️ SUNERA — projektowanie i montaż instalacji PV. Hybrydowe, on-grid, off-grid. Pomagamy w dotacjach i finansowaniu.",
        "de": "☀️ SUNERA — Planung und Installation von PV-Anlagen. Hybrid, netzgekoppelt, Insel. Wir helfen bei Förderungen und Finanzierung.",
        "uk": "☀️ SUNERA — проектування та монтаж сонячних систем. Гібридні, мережеві, автономні. Допомагаємо з субсидіями та фінансуванням.",
    },

    # ------- FORM -------
    "form_name": {"ru": "Как вас зовут?","en": "What's your name?","es": "¿Cómo te llamas?","pl": "Jak masz na imię?","de": "Wie heißen Sie?","uk": "Як вас звати?"},
    "form_phone": {"ru": "Ваш телефон (с кодом страны)? Отправьте текстом или прикрепите контакт.","en": "Your phone (with country code)? Send text or share a contact.","es": "Tu teléfono (con prefijo). Texto o comparte contacto.","pl": "Telefon (z kierunkowym). Tekst lub udostępnij kontakt.","de": "Telefon (mit Ländervorwahl). Text oder Kontakt teilen.","uk": "Ваш телефон (з кодом країни). Текстом або надішліть контакт."},
    "form_city": {"ru": "Город/адрес установки?","en": "City/address for installation?","es": "Ciudad/dirección de instalación?","pl": "Miasto/adres instalacji?","de": "Stadt/Adresse der Installation?","uk": "Місто/адреса монтажу?"},
    "form_note": {"ru": "Кратко опишите задачу (мощность/бюджет/сроки) — по желанию.","en": "Briefly describe your request (power/budget/timing) — optional.","es": "Describe brevemente (potencia/presupuesto/plazos) — opcional.","pl": "Krótko opisz (moc/budżet/terminy) — opcjonalnie.","de": "Kurz beschreiben (Leistung/Budget/Fristen) — optional.","uk": "Коротко опишіть (потужність/бюджет/строки) — за бажанням."},
    "form_ok": {"ru": "✅ Спасибо! Заявка принята. Мы свяжемся с вами.","en": "✅ Thanks! Your request has been received. We'll contact you.","es": "✅ ¡Gracias! Hemos recibido tu solicitud. Te contactaremos.","pl": "✅ Dziękujemy! Zgłoszenie przyjęte. Skontaktujemy się.","de": "✅ Danke! Ihre Anfrage ist eingegangen. Wir melden uns.","uk": "✅ Дякуємо! Заявку отримано. Ми з вами зв’яжемося."},
    "phone_invalid": {"ru": "Похоже, телефон некорректный. Введите в формате +48123456789.","en": "Phone looks invalid. Please send like +48123456789.","es": "Teléfono no válido. Envía así: +48123456789.","pl": "Nieprawidłowy numer. Wyślij np. +48123456789.","de": "Ungültige Nummer. Senden Sie z. B. +48123456789.","uk": "Невірний номер. Надішліть так: +48123456789."},

    # ------- CREDIT -------
    "credit_prompt": {
        "ru": "Введите: СУММА(€) СРОК_ЛЕТ СТАВКА_%\nНапример: 8000 5 8",
        "en": "Enter: AMOUNT(€) YEARS RATE_%\nExample: 8000 5 8",
        "es": "Ingresa: MONTO(€) AÑOS TASA_%\nEjemplo: 8000 5 8",
        "pl": "Podaj: KWOTA(€) LATA OPROC_%\nNp.: 8000 5 8",
        "de": "Geben Sie ein: BETRAG(€) JAHRE ZINS_%\nBeispiel: 8000 5 8",
        "uk": "Введіть: СУМА(€) РОКИ СТАВКА_%\nПриклад: 8000 5 8",
    },
    "credit_badfmt": {
        "ru": "Формат неверный. Пример: 8000 5 8",
        "en": "Wrong format. Example: 8000 5 8",
        "es": "Formato incorrecto. Ej: 8000 5 8",
        "pl": "Błędny format. Np.: 8000 5 8",
        "de": "Falsches Format. Bsp.: 8000 5 8",
        "uk": "Невірний формат. Приклад: 8000 5 8",
    },
    "credit_result": {
        "ru": "Ежемесячный платёж: {monthly} €\nСумма выплат: {total} €\nПереплата: {over} €",
        "en": "Monthly: {monthly} €\nTotal paid: {total} €\nOverpayment: {over} €",
        "es": "Mensual: {monthly} €\nTotal: {total} €\nIntereses: {over} €",
        "pl": "Rata miesięczna: {monthly} €\nSuma: {total} €\nNadpłata: {over} €",
        "de": "Monatlich: {monthly} €\nGesamt: {total} €\nZinsen: {over} €",
        "uk": "Щомісячно: {monthly} €\nРазом: {total} €\nПереплата: {over} €",
    },

    # ------- SOLAR -------
    "solar_prompt": {
        "ru": "Введи: ПОТРЕБЛЕНИЕ_кВт·ч/мес ТАРИФ_€/кВт·ч [PSH=4.5]\nНапр.: 450 0.22 4.2",
        "en": "Enter: CONSUMPTION_kWh/month TARIFF_€/kWh [PSH=4.5]\nE.g.: 450 0.22 4.2",
        "es": "Ingresa: CONSUMO_kWh/mes TARIFA_€/kWh [PSH=4.5]\nEj.: 450 0.22 4.2",
        "pl": "Podaj: ZUŻYCIE_kWh/mies TARYFA_€/kWh [PSH=4.5]\nNp.: 450 0.22 4.2",
        "de": "Eingabe: VERBRAUCH_kWh/Monat TARIF_€/kWh [PSH=4.5]\nz.B.: 450 0.22 4.2",
        "uk": "Введіть: СПОЖИВАННЯ_кВт·год/міс ТАРИФ_€/кВт·год [PSH=4.5]\nНапр.: 450 0.22 4.2",
    },
    "solar_badfmt": {
        "ru": "Формат неверный. Пример: 450 0.22 4.2",
        "en": "Wrong format. Example: 450 0.22 4.2",
        "es": "Formato incorrecto. Ej.: 450 0.22 4.2",
        "pl": "Błędny format. Np.: 450 0.22 4.2",
        "de": "Falsches Format. Bsp.: 450 0.22 4.2",
        "uk": "Невірний формат. Приклад: 450 0.22 4.2",
    },
    "solar_result": {
        "ru": "Система: ~{kw} кВт\nЦена: ~{cost} € ({cperkW} €/кВт)\nГодовая генерация: ~{gen} кВт·ч\nЭкономия/год: ~{save} €\nОкупаемость: ~{payback} лет",
        "en": "System: ~{kw} kW\nCost: ~{cost} € ({cperkW} €/kW)\nYearly generation: ~{gen} kWh\nYearly saving: ~{save} €\nPayback: ~{payback} years",
        "es": "Sistema: ~{kw} kW\nCosto: ~{cost} € ({cperkW} €/kW)\nGeneración anual: ~{gen} kWh\nAhorro/año: ~{save} €\nRetorno: ~{payback} años",
        "pl": "System: ~{kw} kW\nKoszt: ~{cost} € ({cperkW} €/kW)\nRoczna produkcja: ~{gen} kWh\nOszczędność/rok: ~{save} €\nZwrot: ~{payback} lat",
        "de": "Anlage: ~{kw} kW\nKosten: ~{cost} € ({cperkW} €/kW)\nJahresertrag: ~{gen} kWh\nErsparnis/Jahr: ~{save} €\nAmortisation: ~{payback} Jahre",
        "uk": "Система: ~{kw} кВт\nВартість: ~{cost} € ({cperkW} €/кВт)\nРічна генерація: ~{gen} кВт·год\nЕкономія/рік: ~{save} €\nОкупність: ~{payback} років",
    },
}

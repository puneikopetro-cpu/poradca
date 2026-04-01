/* FinAdvisor SK — i18n (SK / UA)
   Usage: data-i18n="key"  data-i18n-placeholder="key"
   Auto-detects browser language; saved in localStorage('lang') */

const TRANSLATIONS = {
  sk: {
    /* ── NAV ─────────────────────────────────── */
    nav_features:   'Funkcie',
    nav_how:        'Ako to funguje',
    nav_pricing:    'Ceny',
    nav_login:      'Prihlásiť sa',
    nav_start:      'Začať zadarmo →',
    nav_continue:   'Pokračovať v učení',

    /* ── HERO ───────────────────────────────── */
    hero_badge:     '🇸🇰 Platforma pre finančnú gramotnosť',
    hero_title:     'Vaša finančná sloboda začína tu',
    hero_sub:       'Moderná vzdelávacia platforma — kurzy, AI radca, kalkulačky a príprava na NBS skúšku. Všetko na jednom mieste.',
    hero_cta:       'Začať zadarmo →',
    hero_features:  '▶ Pozrieť funkcie',
    trust_rating:   '★ 4.9/5 hodnotenie',
    trust_users:    '✓ 2 400+ používateľov',
    trust_gdpr:     '🔒 GDPR chránené',
    trust_sk:       '🇸🇰 Platforma SR',

    /* ── STATS ──────────────────────────────── */
    stat_finances:  'sledovaných financií',
    stat_nbs:       'NBS otázok v databáze',
    stat_calc:      'finančných kalkulačiek',
    stat_satis:     'spokojnosť používateľov',

    /* ── FEATURES ───────────────────────────── */
    feat_title:     'Všetko čo potrebujete pre finančnú nezávislosť',
    feat_sub:       'Od základov osobných financií až po pokročilé investičné stratégie a prípravu na licenciu.',
    feat1_title:    '📚 Štruktúrované kurzy',
    feat1_text:     '18 kurzov rozdelených do 4 kategórií. Od osobného rozpočtu po krypto reguláciu MiCA.',
    feat2_title:    '🤖 AI Finančný radca',
    feat2_text:     'Opýtajte sa čokoľvek — ETF, hypotéky, dane, dôchodok. Odpovede v slovenčine 24/7.',
    feat3_title:    '🧮 Finančné kalkulačky',
    feat3_text:     '12 kalkulačiek: hypotéka, ETF výnos, dôchodkový cieľ, daňová optimalizácia a ďalšie.',
    feat4_title:    '📊 NBS Príprava',
    feat4_text:     '1 334 reálnych otázok zo skúšky. Testuj sa, sleduj pokrok, opakuj slabé miesta.',
    feat5_title:    '📈 Financial IQ Score',
    feat5_text:     'Zisti svoju finančnú úroveň. Personalizované odporúčania podľa výsledkov.',
    feat6_title:    '🔒 Bezpečnosť a súkromie',
    feat6_text:     'GDPR compliant. Dáta šifrované. Žiadne predávanie tretím stranám.',

    /* ── HOW IT WORKS ───────────────────────── */
    how_title:      'Ako to funguje',
    how_sub:        'Tri kroky k finančnej gramotnosti',
    how1_title:     '1. Registruj sa zadarmo',
    how1_text:      'Vytvor účet za 30 sekúnd. Žiadna kreditná karta.',
    how2_title:     '2. Vyber kurz alebo sa opýtaj AI',
    how2_text:      'Kurzy, kalkulačky, NBS testy — všetko okamžite dostupné.',
    how3_title:     '3. Aplikuj a rastu',
    how3_text:      'Sleduj pokrok, zbieraj XP, buduj finančné znalosti krok za krokom.',

    /* ── PRICING ────────────────────────────── */
    pricing_title:  'Transparentné ceny',
    pricing_sub:    'Začnite zadarmo. Plaťte len za to, čo naozaj potrebujete.',
    plan_free:      'Bezplatné',
    plan_free_price:'€0/mes',
    plan_free_desc: 'navždy bezplatné',
    plan_starter:   'Starter',
    plan_starter_price: '€4.90/mes',
    plan_pro:       'Pro',
    plan_pro_price: '€9.90/mes',
    plan_expert:    'Expert',
    plan_expert_price: '€14.90/mes',
    plan_popular:   '⭐ Najpopulárnejší',
    btn_start_free: 'Začať bezplatne',
    btn_choose:     'Vybrať',
    btn_start_pro:  'Začať Pro ✨',

    /* ── CTA ────────────────────────────────── */
    cta_title:      'Začnite dnes — zadarmo',
    cta_sub:        'Prvých 5 kurzov, kalkulačky a AI radca sú dostupné zadarmo.',
    cta_btn:        'Vytvoriť bezplatný účet →',

    /* ── FOOTER ─────────────────────────────── */
    footer_desc:    'Vzdelávacia platforma pre finančnú gramotnosť. Nie sme finančný poradca.',
    footer_platform:'Platforma',
    footer_login:   'Prihlásenie',
    footer_register:'Registrácia',
    footer_prices:  'Ceny',
    footer_features:'Funkcie',
    footer_legal:   'Právne',
    footer_terms:   'Podmienky použitia',
    footer_privacy: 'Ochrana údajov',
    footer_contact: 'Kontakt',
    footer_warning: '⚠️ Obsah tejto platformy slúži výlučne na vzdelávacie účely. Neposkytujeme finančné poradenstvo v zmysle zákona č. 186/2009 Z.z.',

    /* ── APP ─────────────────────────────────── */
    tab_courses:    'Kurzy',
    tab_ai:         'AI Radca',
    tab_profile:    'Profil',
    login_title:    'Vitajte späť',
    login_sub:      'Prihláste sa do svojho účtu',
    reg_title:      'Vytvorte účet',
    reg_sub:        'Začnite zadarmo ešte dnes',
    lbl_name:       'Celé meno',
    lbl_email:      'Email',
    lbl_password:   'Heslo',
    btn_login:      'Prihlásiť sa',
    btn_register:   'Registrovať sa',
    btn_logout:     'Odhlásiť sa',
    courses_title:  'Finančné kurzy',
    chat_title:     'AI Finančný radca',
    chat_welcome:   '👋 Dobrý deň! Som váš AI finančný asistent. Opýtajte sa ma na ETF, hypotéky, dane, dôchodkové sporenie alebo kryptomeny.',
    chat_send:      'Odoslať',
    profile_title:  'Môj profil',
    btn_save_pass:  'Zmeniť heslo',

    /* ── LEARN ──────────────────────────────── */
    btn_back:       '← Späť',
    btn_prev:       '← Predchádzajúca',
    btn_next:       'Ďalej →',
    btn_finish:     '✓ Dokončiť kurz',
    progress_text:  'Lekcia',
    of_text:        'z',

    /* ── ADMIN ──────────────────────────────── */
    admin_title:    'Admin Panel',
    admin_overview: 'Prehľad',
    admin_users:    'Používatelia',
    admin_courses:  'Kurzy',
    admin_leads:    'Leady',
    admin_settings: 'Nastavenia',
    btn_add:        'Pridať',
    btn_save:       'Uložiť',
    btn_delete:     'Zmazať',
    btn_edit:       'Upraviť',
    btn_export:     'Exportovať',

    /* ── COMMON ─────────────────────────────── */
    err_required:   'Toto pole je povinné',
    err_email:      'Neplatný email',
    err_login:      'Nesprávny email alebo heslo',
    err_network:    'Chyba siete. Skúste znova.',
    loading:        'Načítava sa…',
    success:        'Úspešne uložené',
  },

  uk: {
    /* ── NAV ─────────────────────────────────── */
    nav_features:   'Функції',
    nav_how:        'Як це працює',
    nav_pricing:    'Ціни',
    nav_login:      'Увійти',
    nav_start:      'Почати безкоштовно →',
    nav_continue:   'Продовжити навчання',

    /* ── HERO ───────────────────────────────── */
    hero_badge:     '🇸🇰 Платформа фінансової грамотності',
    hero_title:     'Ваша фінансова свобода починається тут',
    hero_sub:       'Сучасна навчальна платформа — курси, AI-радник, калькулятори і підготовка до іспиту NBS. Все в одному місці.',
    hero_cta:       'Почати безкоштовно →',
    hero_features:  '▶ Переглянути функції',
    trust_rating:   '★ 4.9/5 оцінка',
    trust_users:    '✓ 2 400+ користувачів',
    trust_gdpr:     '🔒 Захист GDPR',
    trust_sk:       '🇸🇰 Платформа СР',

    /* ── STATS ──────────────────────────────── */
    stat_finances:  'відстежуваних фінансів',
    stat_nbs:       'питань NBS у базі',
    stat_calc:      'фінансових калькуляторів',
    stat_satis:     'задоволеність користувачів',

    /* ── FEATURES ───────────────────────────── */
    feat_title:     'Все необхідне для фінансової незалежності',
    feat_sub:       'Від основ особистих фінансів до інвестиційних стратегій і підготовки до ліцензії.',
    feat1_title:    '📚 Структуровані курси',
    feat1_text:     '18 курсів у 4 категоріях. Від особистого бюджету до крипто-регуляції MiCA.',
    feat2_title:    '🤖 AI Фінансовий радник',
    feat2_text:     'Запитайте про ETF, іпотеки, податки, пенсії. Відповіді 24/7 вашою мовою.',
    feat3_title:    '🧮 Фінансові калькулятори',
    feat3_text:     '12 калькуляторів: іпотека, дохідність ETF, пенсійна мета, оптимізація податків.',
    feat4_title:    '📊 Підготовка до NBS',
    feat4_text:     '1 334 реальних питань з іспиту. Тестуйтесь, відстежуйте прогрес.',
    feat5_title:    '📈 Фінансовий IQ',
    feat5_text:     'Дізнайтесь свій рівень. Персоналізовані рекомендації за результатами.',
    feat6_title:    '🔒 Безпека і приватність',
    feat6_text:     'GDPR compliant. Зашифровані дані. Не передаємо третім особам.',

    /* ── HOW IT WORKS ───────────────────────── */
    how_title:      'Як це працює',
    how_sub:        'Три кроки до фінансової грамотності',
    how1_title:     '1. Зареєструйтесь безкоштовно',
    how1_text:      'Створіть акаунт за 30 секунд. Без кредитної картки.',
    how2_title:     '2. Оберіть курс або запитайте AI',
    how2_text:      'Курси, калькулятори, тести NBS — все одразу доступно.',
    how3_title:     '3. Застосовуйте та зростайте',
    how3_text:      'Відстежуйте прогрес, збирайте XP, нарощуйте знання.',

    /* ── PRICING ────────────────────────────── */
    pricing_title:  'Прозорі ціни',
    pricing_sub:    'Починайте безкоштовно. Платіть лише за те, що дійсно потрібно.',
    plan_free:      'Безкоштовно',
    plan_free_price:'€0/міс',
    plan_free_desc: 'назавжди безкоштовно',
    plan_starter:   'Starter',
    plan_starter_price: '€4.90/міс',
    plan_pro:       'Pro',
    plan_pro_price: '€9.90/міс',
    plan_expert:    'Expert',
    plan_expert_price: '€14.90/міс',
    plan_popular:   '⭐ Найпопулярніший',
    btn_start_free: 'Почати безкоштовно',
    btn_choose:     'Обрати',
    btn_start_pro:  'Почати Pro ✨',

    /* ── CTA ────────────────────────────────── */
    cta_title:      'Почніть сьогодні — безкоштовно',
    cta_sub:        'Перші 5 курсів, калькулятори та AI-радник доступні безкоштовно.',
    cta_btn:        'Створити безкоштовний акаунт →',

    /* ── FOOTER ─────────────────────────────── */
    footer_desc:    'Навчальна платформа фінансової грамотності. Ми не є фінансовим радником.',
    footer_platform:'Платформа',
    footer_login:   'Вхід',
    footer_register:'Реєстрація',
    footer_prices:  'Ціни',
    footer_features:'Функції',
    footer_legal:   'Правова інформація',
    footer_terms:   'Умови використання',
    footer_privacy: 'Захист даних',
    footer_contact: 'Контакт',
    footer_warning: '⚠️ Вміст цієї платформи призначений виключно для навчальних цілей. Ми не надаємо фінансових консультацій у розумінні закону № 186/2009 З.з.',

    /* ── APP ─────────────────────────────────── */
    tab_courses:    'Курси',
    tab_ai:         'AI Радник',
    tab_profile:    'Профіль',
    login_title:    'З поверненням',
    login_sub:      'Увійдіть до свого акаунту',
    reg_title:      'Створіть акаунт',
    reg_sub:        'Почніть безкоштовно вже сьогодні',
    lbl_name:       'Повне ім\'я',
    lbl_email:      'Електронна пошта',
    lbl_password:   'Пароль',
    btn_login:      'Увійти',
    btn_register:   'Зареєструватись',
    btn_logout:     'Вийти',
    courses_title:  'Фінансові курси',
    chat_title:     'AI Фінансовий радник',
    chat_welcome:   '👋 Вітаємо! Я ваш AI фінансовий асистент. Запитуйте про ETF, іпотеки, податки, пенсійне накопичення або криптовалюти.',
    chat_send:      'Надіслати',
    profile_title:  'Мій профіль',
    btn_save_pass:  'Змінити пароль',

    /* ── LEARN ──────────────────────────────── */
    btn_back:       '← Назад',
    btn_prev:       '← Попередня',
    btn_next:       'Далі →',
    btn_finish:     '✓ Завершити курс',
    progress_text:  'Урок',
    of_text:        'з',

    /* ── ADMIN ──────────────────────────────── */
    admin_title:    'Панель адміна',
    admin_overview: 'Огляд',
    admin_users:    'Користувачі',
    admin_courses:  'Курси',
    admin_leads:    'Ліди',
    admin_settings: 'Налаштування',
    btn_add:        'Додати',
    btn_save:       'Зберегти',
    btn_delete:     'Видалити',
    btn_edit:       'Редагувати',
    btn_export:     'Експортувати',

    /* ── COMMON ─────────────────────────────── */
    err_required:   'Це поле обов\'язкове',
    err_email:      'Невірний email',
    err_login:      'Невірний email або пароль',
    err_network:    'Помилка мережі. Спробуйте ще раз.',
    loading:        'Завантаження…',
    success:        'Успішно збережено',
  }
};

/* ── Core functions ─────────────────────────────────────── */
function getLang() {
  return localStorage.getItem('lang') ||
    (navigator.language?.toLowerCase().startsWith('uk') ? 'uk' : 'sk');
}

function applyLang(lang) {
  if (!TRANSLATIONS[lang]) lang = 'sk';
  const T = TRANSLATIONS[lang];

  // text content
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (T[key] !== undefined) el.textContent = T[key];
  });
  // placeholders
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (T[key] !== undefined) el.placeholder = T[key];
  });
  // html (for rich content)
  document.querySelectorAll('[data-i18n-html]').forEach(el => {
    const key = el.getAttribute('data-i18n-html');
    if (T[key] !== undefined) el.innerHTML = T[key];
  });

  document.documentElement.lang = lang;
  localStorage.setItem('lang', lang);

  // update all lang buttons
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.textContent = lang === 'uk' ? '🇸🇰 SK' : '🇺🇦 UA';
    btn.title = lang === 'uk' ? 'Prepnúť na slovenčinu' : 'Переключити на українську';
  });

  // fire event so pages can react
  document.dispatchEvent(new CustomEvent('langChanged', { detail: { lang } }));
}

function toggleLang() {
  applyLang(getLang() === 'sk' ? 'uk' : 'sk');
}

/* ── Lang button factory ─────────────────────────────────── */
function createLangBtn() {
  const btn = document.createElement('button');
  btn.className = 'lang-btn';
  btn.onclick = toggleLang;
  btn.style.cssText = 'background:none;border:1px solid rgba(255,255,255,.35);border-radius:7px;padding:5px 11px;cursor:pointer;font-size:13px;font-weight:600;color:inherit;transition:.2s;white-space:nowrap;';
  btn.addEventListener('mouseenter', () => btn.style.background = 'rgba(255,255,255,.15)');
  btn.addEventListener('mouseleave', () => btn.style.background = 'none');
  return btn;
}

/* ── Auto-init on DOMContentLoaded ──────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // inject lang button into .nav-actions or #nav-actions if present
  const navActions = document.querySelector('.nav-actions, #nav-actions');
  if (navActions && !document.querySelector('.lang-btn')) {
    const btn = createLangBtn();
    navActions.prepend(btn);
  }
  applyLang(getLang());
});

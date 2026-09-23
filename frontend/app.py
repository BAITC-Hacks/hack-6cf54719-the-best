import streamlit as st


st.set_page_config(
    page_title="AI Sana · каталог задач",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


TASKS = [
    {
        "id": "T-1042",
        "title": "Снизить число пропущенных записей в клинике",
        "company": "MedPoint",
        "industry": "Здравоохранение",
        "level": "Рабочая",
        "score": 68,
        "summary": "Нужно повысить подтверждение записи пациентов без сложной CRM.",
        "users": "Пациенты и администраторы",
        "data": "История записей за 6 месяцев",
        "deadline": "2 недели",
        "tags": ["web", "данные готовы", "healthcare"],
        "missing": ["Измеримый target по снижению пропусков", "Примеры сообщений пациентам"],
        "proposals": 3,
    },
    {
        "id": "T-1038",
        "title": "Понять, почему пользователи бросают анкету",
        "company": "FinStart",
        "industry": "Финтех",
        "level": "Готовая",
        "score": 82,
        "summary": "Исследовать воронку анкеты и предложить быстрые UX-улучшения.",
        "users": "Новые клиенты сервиса",
        "data": "События воронки и 12 интервью",
        "deadline": "10 дней",
        "tags": ["analytics", "ux research"],
        "missing": ["Нет критичных пропусков"],
        "proposals": 5,
    },
    {
        "id": "T-1029",
        "title": "Автоматизировать сводку обратной связи клиентов",
        "company": "Qazaq Market",
        "industry": "Ритейл",
        "level": "Приоритетная",
        "score": 94,
        "summary": "Собрать отзывы из нескольких каналов и выделять повторяющиеся проблемы.",
        "users": "Команда поддержки и продукта",
        "data": "CSV с отзывами и категории обращений",
        "deadline": "3 недели",
        "tags": ["ai", "python", "csv"],
        "missing": ["Нет критичных пропусков"],
        "proposals": 7,
    },
    {
        "id": "T-1017",
        "title": "Сделать понятнее отчёт для руководителя школы",
        "company": "Bilim Hub",
        "industry": "Образование",
        "level": "Черновик",
        "score": 34,
        "summary": "Сейчас отчёт содержит много таблиц, но не помогает быстро увидеть риски.",
        "users": "Директора и кураторы",
        "data": "Excel-отчёты за прошлый семестр",
        "deadline": "Не определён",
        "tags": ["dashboard", "data viz"],
        "missing": ["Критерии успеха", "Ограничения по срокам", "Примеры решений"],
        "proposals": 1,
    },
]


def level_color(level: str) -> str:
    return {
        "Приоритетная": "#0f8a6f",
        "Готовая": "#5276ff",
        "Рабочая": "#b17a00",
        "Черновик": "#a34b48",
    }.get(level, "#64748b")


def score_color(score: int) -> str:
    if score >= 90:
        return "#0f8a6f"
    if score >= 70:
        return "#5276ff"
    if score >= 40:
        return "#b17a00"
    return "#a34b48"


st.markdown(
    """
    <style>
    :root { font-family: Inter, system-ui, sans-serif; }
    [data-testid="stAppViewContainer"] { background: #f6f8fc; }
    [data-testid="stSidebar"] { background: #121a2b; }
    [data-testid="stSidebar"] * { color: #e8eef8 !important; }
    .brand { font-size: 26px; font-weight: 800; letter-spacing: -.04em; color: #121a2b; }
    .muted { color: #64748b; font-size: 14px; }
    .task-card { background: white; border: 1px solid #dbe3ef; border-radius: 16px; padding: 20px; margin-bottom: 14px; }
    .task-card:hover { border-color: #aab9d3; box-shadow: 0 10px 26px rgba(33,50,85,.08); }
    .task-top { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }
    .task-title { font-size: 19px; line-height: 1.25; font-weight: 750; color: #111827; margin: 6px 0 8px; }
    .task-summary { color: #64748b; margin: 0 0 14px; }
    .badge { display:inline-block; padding: 4px 9px; border-radius: 999px; font-size: 12px; font-weight: 750; background: #edf2ff; color: #4055b4; margin-right: 5px; }
    .score { min-width: 82px; text-align: right; font-size: 28px; font-weight: 800; line-height: 1; }
    .score small { display:block; color:#64748b; font-size:11px; font-weight:500; margin-top:5px; }
    .metric { color:#64748b; font-size: 13px; }
    .metric b { color:#111827; }
    .detail-box { background:white; border:1px solid #dbe3ef; border-radius:16px; padding:24px; }
    </style>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("## ✦ AI Sana")
    st.caption("Открытый каталог бизнес-задач")
    st.divider()
    st.markdown("### Фильтры")
    industry = st.selectbox("Отрасль", ["Все отрасли"] + sorted({task["industry"] for task in TASKS}))
    level = st.selectbox("Готовность", ["Все уровни", "Приоритетная", "Готовая", "Рабочая", "Черновик"])
    min_score = st.slider("Минимальный рейтинг", 0, 100, 0, 5)
    st.divider()
    st.markdown("### Правило каталога")
    st.caption("Низкий рейтинг не скрывает задачу. Он показывает, сколько уточнений потребуется команде.")


st.markdown('<div class="brand">Общий каталог задач</div>', unsafe_allow_html=True)
st.markdown('<p class="muted">Выберите задачу, изучите контекст и отправьте предложение своей команды.</p>', unsafe_allow_html=True)


col1, col2, col3 = st.columns([2.5, 1.2, 1.2])
with col1:
    search = st.text_input("Поиск", placeholder="Например: данные, клиника, AI…", label_visibility="collapsed")
with col2:
    sort_by = st.selectbox("Сортировка", ["Рейтинг: сначала высокий", "Рейтинг: сначала низкий", "Сначала новые"], label_visibility="collapsed")
with col3:
    st.metric("Опубликовано", len(TASKS))


filtered = TASKS[:]
if industry != "Все отрасли":
    filtered = [task for task in filtered if task["industry"] == industry]
if level != "Все уровни":
    filtered = [task for task in filtered if task["level"] == level]
if min_score:
    filtered = [task for task in filtered if task["score"] >= min_score]
if search:
    query = search.lower()
    filtered = [task for task in filtered if query in (task["title"] + task["summary"] + task["industry"]).lower()]

if sort_by == "Рейтинг: сначала высокий":
    filtered.sort(key=lambda task: task["score"], reverse=True)
elif sort_by == "Рейтинг: сначала низкий":
    filtered.sort(key=lambda task: task["score"])


st.write(f"**{len(filtered)} задач** доступны для отклика")

if not filtered:
    st.info("По этим фильтрам задач не найдено. Попробуйте убрать часть ограничений.")

for task in filtered:
    st.markdown('<div class="task-card">', unsafe_allow_html=True)
    left, right = st.columns([5, 1])
    with left:
        st.caption(f'{task["id"]}  ·  {task["company"]}  ·  {task["industry"]}')
        st.markdown(f'<div class="task-title">{task["title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="task-summary">{task["summary"]}</p>', unsafe_allow_html=True)
        st.markdown("".join(f'<span class="badge">{tag}</span>' for tag in task["tags"]), unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="score" style="color:{score_color(task["score"])}">{task["score"]}<small>из 100</small></div>', unsafe_allow_html=True)
    st.divider()
    m1, m2, m3, action = st.columns([1.2, 1.5, 1.4, 1.2])
    m1.markdown(f'<span class="metric">Готовность<br><b style="color:{level_color(task["level"])}">{task["level"]}</b></span>', unsafe_allow_html=True)
    m2.markdown(f'<span class="metric">Срок<br><b>{task["deadline"]}</b></span>', unsafe_allow_html=True)
    m3.markdown(f'<span class="metric">Откликов<br><b>{task["proposals"]}</b></span>', unsafe_allow_html=True)
    with action:
        if st.button("Подробнее", key=f"details-{task['id']}", use_container_width=True):
            st.session_state["selected_task"] = task["id"]
    st.markdown('</div>', unsafe_allow_html=True)


selected_id = st.session_state.get("selected_task")
selected = next((task for task in TASKS if task["id"] == selected_id), None)
if selected:
    st.divider()
    st.markdown(f"## Детали: {selected['title']}")
    left, right = st.columns([1.5, 1])
    with left:
        st.markdown('<div class="detail-box">', unsafe_allow_html=True)
        st.markdown(f"**Контекст**  \n{selected['summary']}")
        st.markdown(f"**Пользователи**  \n{selected['users']}")
        st.markdown(f"**Доступные данные**  \n{selected['data']}")
        st.markdown(f"**Ограничение по сроку**  \n{selected['deadline']}")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="detail-box">', unsafe_allow_html=True)
        st.metric("Рейтинг готовности", f"{selected['score']} / 100")
        st.markdown("**Что ещё уточнить:**")
        for item in selected["missing"]:
            st.markdown(f"- {item}")
        if st.button("Подать предложение", type="primary", use_container_width=True):
            st.success("Демо: экран подачи предложения можно подключить к POST /tasks/:id/proposals")
        st.markdown('</div>', unsafe_allow_html=True)

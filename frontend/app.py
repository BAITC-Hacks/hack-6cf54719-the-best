from html import escape

import streamlit as st

from api import ApiError, request


READINESS_FIELDS = [
    ("title", "Название задачи", 10, "Коротко обозначьте, что нужно сделать."),
    ("description", "Описание проблемы", 25, "Опишите контекст, проблему и ожидаемый результат."),
    ("industry", "Отрасль", 10, "Укажите сферу, чтобы задачу было проще найти."),
    ("target_users", "Для кого решается задача", 10, "Назовите пользователей или процесс, для которого ищется решение."),
    ("available_data", "Доступные данные или ресурсы", 15, "Перечислите только ресурсы, которые действительно можно предоставить."),
    ("success_criteria", "Критерии успеха", 20, "Опишите, по каким признакам компания оценит результат."),
    ("deadline", "Сроки", 5, "Укажите ожидаемый срок или дату."),
    ("tags", "Теги", 5, "Добавьте технологии и навыки, нужные для поиска команды."),
]


st.set_page_config(
    page_title="AI Sana — учебные задачи от компаний",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');
    :root { font-family: 'DM Sans', system-ui, sans-serif; }
    [data-testid="stAppViewContainer"] { background: #f7f8f5; }
    [data-testid="stHeader"] { background: rgba(247,248,245,.86); }
    [data-testid="stSidebar"] { background: #182722; }
    [data-testid="stSidebar"] * { color: #e8f0e9; }
    .brand { font-family: 'Manrope', sans-serif; font-size: 35px; font-weight: 800; letter-spacing: -.055em; color: #17251f; }
    .eyebrow { color: #4d8066; text-transform: uppercase; letter-spacing: .12em; font-size: 11px; font-weight: 800; }
    .muted { color: #65736b; }
    .task-title { font-family: 'Manrope', sans-serif; font-size: 20px; line-height: 1.25; font-weight: 750; color: #17251f; }
    .pill { display:inline-block; padding: 4px 9px; border-radius: 999px; background:#e5f0e7; color:#326447; font-size:12px; font-weight:700; margin-right:5px; }
    div[data-testid="stMetric"] { background:#fff; border:1px solid #e5e9e3; border-radius:14px; padding:14px 16px; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-color:#e3e8e0; }
    div.stButton > button[kind="primary"] { background:#397653; border-color:#397653; }
    [data-testid="stSidebar"] .st-key-logout button {
        background: #000;
        border-color: #000;
        color: #fff;
    }
    [data-testid="stSidebar"] .st-key-logout button * { color: #fff; }
    [data-testid="stSidebar"] .st-key-logout button:hover { background: #222; border-color: #222; }
    [data-testid="stSidebar"] .st-key-logout button:focus-visible { outline: 2px solid #fff; outline-offset: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def show_error(error: Exception) -> None:
    st.error(str(error))


def form_readiness(payload: dict) -> tuple[int, list[dict]]:
    rows = []
    for key, label, weight, guidance in READINESS_FIELDS:
        value = payload.get(key, []) if key == "tags" else payload.get(key, "")
        present = bool(value) if isinstance(value, list) else bool(str(value).strip())
        rows.append({"key": key, "label": label, "weight": weight, "points": weight if present else 0,
                     "present": present, "guidance": guidance})
    return sum(row["points"] for row in rows), rows


def render_readiness_explanation(score: int, rows: list[dict], title: str = "Как считается готовность") -> None:
    st.metric("Готовность карточки", f"{score} / 100")
    st.progress(score / 100)
    with st.expander(title):
        st.caption("Это показатель полноты описания. Он не оценивает качество команды или будущего решения.")
        for row in rows:
            marker = "✓" if row["present"] else "○"
            points = row.get("points", 0)
            weight = row["weight"]
            guidance = row.get("guidance", "")
            st.markdown(f"**{marker} {row['label']} — {points} из {weight} баллов**")
            if guidance:
                st.caption(guidance if row["present"] else f"Уточните: {guidance}")


def set_login(result: dict) -> None:
    st.session_state["access_token"] = result["access_token"]
    st.session_state["user"] = result["user"]
    st.session_state["next_page"] = "Каталог"
    st.rerun()


def navigate_to(page: str) -> None:
    st.session_state["next_page"] = page
    st.rerun()


def render_auth() -> None:
    st.markdown('<p class="eyebrow">Начните работу</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand">Добро пожаловать в AI Sana</div>', unsafe_allow_html=True)
    st.write("Здесь компании делятся реальными задачами, а студенческие команды предлагают решения.")
    login_tab, register_tab = st.tabs(["Войти", "Создать аккаунт"])

    with login_tab:
        with st.form("login-form"):
            email = st.text_input("Email", key="login-email")
            password = st.text_input("Пароль", type="password", key="login-password")
            submitted = st.form_submit_button("Войти", type="primary", use_container_width=True)
        if submitted:
            try:
                set_login(request("POST", "/auth/login", json_body={"email": email, "password": password}))
            except ApiError as error:
                show_error(error)

    with register_tab:
        with st.form("register-form"):
            role_label = st.selectbox("Я представляю", ["Студенческую команду", "Компанию"])
            name = st.text_input("Ваше имя")
            email = st.text_input("Email", key="register-email")
            password = st.text_input("Пароль (минимум 8 символов)", type="password", key="register-password")
            company_name = st.text_input("Название компании (для роли компании)")
            team_name = st.text_input("Название команды (необязательно для роли студента)")
            submitted = st.form_submit_button("Создать аккаунт", type="primary", use_container_width=True)
        if submitted:
            role = "company" if role_label == "Компанию" else "student"
            payload = {"name": name, "email": email, "password": password, "role": role}
            if role == "company":
                payload["company_name"] = company_name
            elif team_name.strip():
                payload["team_name"] = team_name
            try:
                set_login(request("POST", "/auth/register", json_body=payload))
            except ApiError as error:
                show_error(error)
        st.caption("Компания регистрируется самостоятельно; внешняя проверка юридического статуса пока не предусмотрена.")


def render_catalog(user: dict | None) -> None:
    st.markdown('<p class="eyebrow">Практика на реальных задачах</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand">Общий каталог задач</div>', unsafe_allow_html=True)
    st.markdown('<p class="muted">Изучите условия и предложите решение своей команды. Компании принимают решение сами.</p>', unsafe_allow_html=True)
    try:
        all_tasks = request("GET", "/tasks")
    except ApiError as error:
        show_error(error)
        return

    industries = sorted({task["industry"] for task in all_tasks if task["industry"]})
    f1, f2 = st.columns([2, 1])
    search = f1.text_input("Поиск", placeholder="Название, проблема, отрасль…", key="catalog-search")
    industry = f2.selectbox("Отрасль", ["Все отрасли", *industries])
    f3, f4 = st.columns([1, 1])
    min_score = f3.slider("Готовность от", min_value=0, max_value=100, value=0, step=5)
    sort_label = f4.selectbox("Сортировать", ["Сначала новые", "Высокая готовность", "Низкая готовность"])
    sort = {"Сначала новые": "newest", "Высокая готовность": "score_desc", "Низкая готовность": "score_asc"}[sort_label]
    params = {"sort": sort, "min_score": min_score}
    if search.strip():
        params["q"] = search.strip()
    if industry != "Все отрасли":
        params["industry"] = industry
    try:
        tasks = request("GET", "/tasks", params=params)
    except ApiError as error:
        show_error(error)
        return

    st.markdown(f"**{len(tasks)} задач доступны для отклика**")
    if not tasks:
        st.info("Подходящих опубликованных задач пока нет. Попробуйте изменить фильтры или загляните позже.")
    else:
        if any(task.get("is_imported") for task in tasks):
            st.info("Внешние карточки импортированы из Astana Hub для локального сценария. Отклики и решения остаются в AI Sana и не передаются компаниям-источникам.")
        for task in tasks:
            with st.container(border=True):
                head, score_col = st.columns([5, 1])
                with head:
                    st.caption(f"{task['company_name']}  ·  {task['industry']}  ·  {task['deadline'] or 'Срок не указан'}")
                    if task.get("is_imported"):
                        st.caption("Внешняя задача · локальная копия")
                    st.markdown(f"<div class='task-title'>{escape(task['title'])}</div>", unsafe_allow_html=True)
                    st.write(task["description"])
                    if task["tags"]:
                        st.markdown("".join(f"<span class='pill'>{escape(tag)}</span>" for tag in task["tags"]), unsafe_allow_html=True)
                with score_col:
                    st.metric("Готовность", f"{task['readiness_score']}%")
                    st.caption(task["readiness_label"])
                foot, btn = st.columns([5, 1])
                foot.caption(f"Откликов: {task['applications_count']}  ·  {len(task['missing_fields'])} полей требуют уточнения")
                if btn.button("Подробнее", key=f"open-task-{task['id']}", use_container_width=True):
                    st.session_state["selected_task_id"] = task["id"]
                    st.rerun()

    selected_id = st.session_state.get("selected_task_id")
    if selected_id:
        try:
            task = request("GET", f"/tasks/{selected_id}")
        except ApiError:
            st.session_state.pop("selected_task_id", None)
            return
        st.divider()
        st.markdown(f"## {task['title']}")
        st.caption(f"{task['company_name']}  ·  {task['industry']}  ·  {task['deadline']}")
        if task.get("is_imported"):
            st.warning("Это копия карточки из Astana Hub. Отклики внутри AI Sana видны локальному куратору каталога, но не отправляются исходной компании.")
            st.markdown(f"[Проверить оригинальную публикацию]({task['source_url']})")
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("### Описание задачи")
            st.write(task["description"])
            st.markdown("### Для кого решается")
            st.write(task["target_users"])
            st.markdown("### Доступные данные и ресурсы")
            st.write(task["available_data"])
            st.markdown("### Критерии успеха")
            st.write(task["success_criteria"])
        with c2:
            render_readiness_explanation(task["readiness_score"], task["readiness_breakdown"], "Из чего складывается рейтинг")
            if task["missing_fields"]:
                st.markdown("**Что стоит уточнить компании:**")
                for item in task["missing_fields"]:
                    st.markdown(f"- {item}")
            if user and user["role"] == "student":
                try:
                    teams = request("GET", "/teams/mine")
                except ApiError as error:
                    show_error(error)
                    teams = []
                if not teams:
                    st.info("Чтобы отправить отклик, сначала создайте команду или присоединитесь к ней.")
                    if st.button("Настроить команду", key="goto-teams"):
                        navigate_to("Моя команда")
                else:
                    try:
                        existing = request("GET", "/applications/mine")
                        applied_team_ids = {item["team_id"] for item in existing if item["task_id"] == task["id"]}
                    except ApiError as error:
                        show_error(error)
                        applied_team_ids = set()
                    available_teams = [team_item for team_item in teams if team_item["id"] not in applied_team_ids]
                    if not available_teams:
                        st.info("Все ваши команды уже отправили отклик на эту задачу. Статус можно посмотреть в разделе «Мои отклики».")
                    else:
                        with st.form(f"application-{task['id']}"):
                            team = st.selectbox("Команда", available_teams, format_func=lambda item: item["name"], key=f"apply-team-{task['id']}")
                            pitch = st.text_area("Расскажите о подходе команды (минимум 20 символов)", key=f"pitch-{task['id']}")
                            prototype = st.text_input("Ссылка на прототип (необязательно)", key=f"prototype-{task['id']}")
                            submitted = st.form_submit_button("Отправить отклик", type="primary", use_container_width=True)
                        if submitted:
                            try:
                                result = request(
                                    "POST",
                                    f"/tasks/{task['id']}/applications",
                                    json_body={"team_id": team["id"], "pitch": pitch, "prototype_url": prototype.strip() or None},
                                )
                                st.success(f"Отклик команды «{result['team_name']}» отправлен компании.")
                            except ApiError as error:
                                show_error(error)
            elif user and user["role"] == "company":
                st.info("Компании просматривают собственные отклики в кабинете.")
            else:
                st.info("Войдите как студент и выберите команду, чтобы отправить отклик.")
        if st.button("Закрыть подробности", key="close-task-detail"):
            st.session_state.pop("selected_task_id", None)
            st.rerun()


def task_payload_from_form() -> dict:
    tags = [tag.strip() for tag in st.session_state.get("new_tags", "").split(",") if tag.strip()]
    return {
        "title": st.session_state.get("new_title", ""),
        "description": st.session_state.get("new_description", ""),
        "industry": st.session_state.get("new_industry", ""),
        "target_users": st.session_state.get("new_target_users", ""),
        "available_data": st.session_state.get("new_available_data", ""),
        "success_criteria": st.session_state.get("new_success_criteria", ""),
        "deadline": st.session_state.get("new_deadline", ""),
        "tags": tags,
    }


def render_new_task() -> None:
    pending = st.session_state.pop("pending_ai_suggestions", None)
    if pending:
        key_map = {
            "title": "new_title",
            "description": "new_description",
            "industry": "new_industry",
            "target_users": "new_target_users",
            "available_data": "new_available_data",
            "success_criteria": "new_success_criteria",
            "deadline": "new_deadline",
        }
        for field, key in key_map.items():
            if pending.get(field):
                st.session_state[key] = pending[field]

    task_id = st.session_state.get("new_task_id")
    task_status = st.session_state.get("new_task_status", "draft")
    is_published_edit = bool(task_id and task_status == "published")
    title = "Редактирование задачи" if task_id else "Новая учебная задача"
    st.markdown('<p class="eyebrow">Для компаний</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="brand">{title}</div>', unsafe_allow_html=True)
    st.write("Опишите настоящую проблему и укажите, по чему поймёте, что команда справилась.")
    if "new_task_form_initialized" not in st.session_state:
        st.session_state["new_title"] = ""
        st.session_state["new_description"] = ""
        st.session_state["new_industry"] = ""
        st.session_state["new_target_users"] = ""
        st.session_state["new_available_data"] = ""
        st.session_state["new_success_criteria"] = ""
        st.session_state["new_deadline"] = ""
        st.session_state["new_tags"] = ""
        st.session_state["new_task_form_initialized"] = True

    left, right = st.columns(2)
    with left:
        st.text_input("Название задачи *", key="new_title", max_chars=180)
        st.text_area("Описание проблемы *", key="new_description", height=155, max_chars=10000,
                     help="Опишите, что сейчас происходит и почему это проблема.")
        st.text_input("Отрасль *", key="new_industry", placeholder="Например: образование")
        st.text_area("Для кого решается задача *", key="new_target_users", height=90)
    with right:
        st.text_area("Доступные данные и ресурсы *", key="new_available_data", height=120,
                     help="Укажите только то, что действительно доступно команде.")
        st.text_area("Критерии успеха *", key="new_success_criteria", height=120,
                     help="Как компания будет оценивать результат?")
        st.text_input("Сроки *", key="new_deadline", placeholder="Например: 4 недели")
        st.text_input("Теги через запятую", key="new_tags", placeholder="python, аналитика")

    current_payload = task_payload_from_form()
    score, rows = form_readiness(current_payload)
    render_readiness_explanation(score, rows, "Вклад полей и что стоит уточнить")

    if task_id:
        kind = "Опубликованная задача" if is_published_edit else "Черновик"
        st.info(f"{kind} #{task_id}: изменения увидят команды после сохранения." if is_published_edit else
                f"Черновик #{task_id} сохранён. Поправьте поля и опубликуйте, когда будете готовы.")
    if st.session_state.get("ai_suggestions"):
        with st.container(border=True):
            st.markdown("#### Предложения AI")
            st.caption("AI может ошибиться. Проверьте факты и подтвердите вручную; пустые поля помощник не заполняет.")
            if st.session_state.get("ai_note"):
                st.caption(st.session_state["ai_note"])
            for field, value in st.session_state["ai_suggestions"].items():
                st.markdown(f"**{field.replace('_', ' ').capitalize()}:** {value}")
            if st.button("Применить предложения в форму", type="primary", key="apply-ai"):
                st.session_state["pending_ai_suggestions"] = st.session_state["ai_suggestions"]
                st.session_state.pop("ai_suggestions", None)
                st.rerun()

    ai_col, draft_col, publish_col = st.columns([1.2, 1, 1.2])
    if ai_col.button("Уточнить описание с AI", use_container_width=True):
        try:
            result = request("POST", "/ai/improve-task", json_body=task_payload_from_form())
            st.session_state["ai_suggestions"] = result["suggestions"]
            st.session_state["ai_note"] = result["note"]
            st.rerun()
        except ApiError as error:
            show_error(error)
    save_label = "Сохранить изменения" if is_published_edit else "Сохранить черновик"
    if draft_col.button(save_label, use_container_width=True):
        try:
            if task_id:
                request("PUT", f"/tasks/{task_id}", json_body=task_payload_from_form())
                if is_published_edit:
                    st.session_state["flash_message"] = "Изменения опубликованной задачи сохранены."
                    navigate_to("Кабинет компании")
            else:
                saved = request("POST", "/tasks", json_body=task_payload_from_form())
                st.session_state["new_task_id"] = saved["id"]
                st.session_state["new_task_status"] = "draft"
            if not is_published_edit:
                st.success("Черновик сохранён.")
            st.rerun()
        except ApiError as error:
            show_error(error)
    if not is_published_edit and publish_col.button("Опубликовать задачу", type="primary", use_container_width=True):
        try:
            if task_id:
                request("PUT", f"/tasks/{task_id}", json_body=task_payload_from_form())
            else:
                task_id = request("POST", "/tasks", json_body=task_payload_from_form())["id"]
            request("POST", f"/tasks/{task_id}/publish")
            st.session_state.pop("new_task_id", None)
            st.session_state.pop("new_task_status", None)
            st.session_state.pop("ai_suggestions", None)
            st.session_state["flash_message"] = "Задача опубликована и появилась в каталоге."
            st.session_state["reset_new_task_form"] = True
            navigate_to("Кабинет компании")
        except ApiError as error:
            show_error(error)

    if st.button("Отмена · вернуться в кабинет компании", key="cancel-task-edit"):
        st.session_state.pop("new_task_id", None)
        st.session_state.pop("new_task_status", None)
        st.session_state["reset_new_task_form"] = True
        navigate_to("Кабинет компании")


def load_task_into_editor(task: dict) -> None:
    st.session_state["new_task_id"] = task["id"]
    st.session_state["new_task_status"] = task["status"]
    st.session_state["new_title"] = task["title"]
    st.session_state["new_description"] = task["description"]
    st.session_state["new_industry"] = task["industry"]
    st.session_state["new_target_users"] = task["target_users"]
    st.session_state["new_available_data"] = task["available_data"]
    st.session_state["new_success_criteria"] = task["success_criteria"]
    st.session_state["new_deadline"] = task["deadline"]
    st.session_state["new_tags"] = ", ".join(task["tags"])
    st.session_state["new_task_form_initialized"] = True
    st.session_state.pop("ai_suggestions", None)
    st.session_state.pop("ai_note", None)
    navigate_to("Новая задача")


def render_company_dashboard() -> None:
    st.markdown('<p class="eyebrow">Пространство компании</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand">Кабинет компании</div>', unsafe_allow_html=True)
    if st.button("＋ Создать задачу", type="primary"):
        for key in ["new_task_id", "new_task_status", "new_title", "new_description", "new_industry", "new_target_users", "new_available_data", "new_success_criteria", "new_deadline", "new_tags", "new_task_form_initialized", "ai_suggestions", "ai_note"]:
            st.session_state.pop(key, None)
        navigate_to("Новая задача")
    try:
        tasks = request("GET", "/company/tasks")
    except ApiError as error:
        show_error(error)
        return
    if not tasks:
        st.info("У компании пока нет задач. Создайте первую карточку и опубликуйте её в каталоге.")
        return
    for task in tasks:
        with st.container(border=True):
            heading, score = st.columns([5, 1])
            status_label = {"draft": "Черновик", "published": "Опубликована", "closed": "Закрыта"}.get(task["status"], task["status"])
            heading.caption(f"Статус: {status_label}  ·  Откликов: {task['applications_count']}")
            heading.markdown(f"<div class='task-title'>{escape(task['title'])}</div>", unsafe_allow_html=True)
            heading.write(task["description"])
            if task.get("is_imported"):
                st.warning("Внешняя карточка: внутренние отклики видит только локальный куратор AI Sana. Заказчик из Astana Hub их не получает.")
                st.markdown(f"[Исходная карточка Astana Hub]({task['source_url']})")
            score.metric("Готовность", f"{task['readiness_score']}%")
            render_readiness_explanation(task["readiness_score"], task["readiness_breakdown"], "Почему такой рейтинг")
            if task["status"] in {"published", "closed"}:
                edit_col, response_col, close_col = st.columns([1, 1, 1])
                if task["status"] == "published" and not task.get("is_imported") and edit_col.button("Редактировать", key=f"edit-published-{task['id']}"):
                    load_task_into_editor(task)
                if response_col.button("Открыть отклики", key=f"show-applications-{task['id']}"):
                    st.session_state["review_task_id"] = task["id"]
                    st.rerun()
                if task["status"] == "published" and close_col.button("Закрыть задачу", key=f"close-task-{task['id']}"):
                    try:
                        request("POST", f"/tasks/{task['id']}/close")
                        st.session_state["flash_message"] = "Задача закрыта. Новые отклики больше не принимаются."
                        st.rerun()
                    except ApiError as error:
                        show_error(error)
            if task["status"] == "draft":
                st.caption("Черновик сохранён.")
                if task["missing_fields"]:
                    st.caption("Перед публикацией заполните: " + ", ".join(task["missing_fields"]))
                if st.button("Продолжить редактирование", key=f"edit-draft-{task['id']}"):
                    load_task_into_editor(task)

    task_id = st.session_state.get("review_task_id")
    if task_id:
        selected = next((task for task in tasks if task["id"] == task_id), None)
        if selected:
            st.divider()
            st.markdown(f"## Отклики: {selected['title']}")
            try:
                applications = request("GET", f"/tasks/{task_id}/applications")
            except ApiError as error:
                show_error(error)
                applications = []
            if not applications:
                st.info("На эту задачу пока нет откликов.")
            for application in applications:
                with st.container(border=True):
                    application_status = {
                        "submitted": "Отправлен",
                        "reviewing": "На рассмотрении",
                        "accepted": "Принят",
                        "rejected": "Отклонён",
                    }.get(application["status"], application["status"])
                    st.markdown(f"### Команда «{application['team_name']}»")
                    st.caption(f"Отправил(а): {application['submitted_by_name']}  ·  Статус: {application_status}")
                    st.write(application["pitch"])
                    if application["prototype_url"]:
                        st.markdown(f"[Открыть прототип]({application['prototype_url']})")
                    if selected["status"] != "closed" and application["status"] in {"submitted", "reviewing"}:
                        b1, b2, b3 = st.columns(3)
                        if b1.button("В рассмотрение", key=f"review-{application['id']}"):
                            try:
                                request("POST", f"/applications/{application['id']}/review")
                                st.rerun()
                            except ApiError as error:
                                show_error(error)
                        if b2.button("Отклонить", key=f"reject-{application['id']}"):
                            try:
                                request("POST", f"/applications/{application['id']}/reject")
                                st.rerun()
                            except ApiError as error:
                                show_error(error)
                        if b3.button("Выбрать команду", type="primary", key=f"accept-{application['id']}"):
                            try:
                                request("POST", f"/applications/{application['id']}/accept")
                                st.session_state["flash_message"] = f"Команда «{application['team_name']}» выбрана. Задача закрыта."
                                st.rerun()
                            except ApiError as error:
                                show_error(error)


def render_student_team() -> None:
    st.markdown('<p class="eyebrow">Пространство команды</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand">Моя команда</div>', unsafe_allow_html=True)
    try:
        teams = request("GET", "/teams/mine")
    except ApiError as error:
        show_error(error)
        teams = []
    if teams:
        for team in teams:
            with st.container(border=True):
                st.markdown(f"### {team['name']}")
                st.caption("Участники: " + ", ".join(member["name"] for member in team["members"]))
                if team["is_owner"]:
                    st.markdown(f"Код приглашения: **`{team['invite_code']}`** — поделитесь им с однокурсниками.")
    else:
        st.info("Создайте команду или введите код приглашения, который вам прислали.")

    create_col, join_col = st.columns(2)
    with create_col:
        st.markdown("#### Создать команду")
        with st.form("create-team-form"):
            name = st.text_input("Название команды")
            submitted = st.form_submit_button("Создать команду", type="primary")
        if submitted:
            try:
                request("POST", "/teams", json_body={"name": name})
                st.success("Команда создана.")
                st.rerun()
            except ApiError as error:
                show_error(error)
    with join_col:
        st.markdown("#### Вступить в команду")
        with st.form("join-team-form"):
            code = st.text_input("Код приглашения")
            submitted = st.form_submit_button("Вступить")
        if submitted:
            try:
                request("POST", "/teams/join", json_body={"invite_code": code})
                st.success("Вы вступили в команду.")
                st.rerun()
            except ApiError as error:
                show_error(error)


def render_my_applications() -> None:
    st.markdown('<p class="eyebrow">Ответы компаний</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand">Мои отклики</div>', unsafe_allow_html=True)
    try:
        applications = request("GET", "/applications/mine")
    except ApiError as error:
        show_error(error)
        return
    if not applications:
        st.info("Вы пока не отправляли откликов. Найдите задачу в каталоге и предложите решение команды.")
    for application in applications:
        with st.container(border=True):
            application_status = {
                "submitted": "Отправлен",
                "reviewing": "На рассмотрении",
                "accepted": "Принят",
                "rejected": "Отклонён",
            }.get(application["status"], application["status"])
            st.markdown(f"### {application['task_title']}")
            st.caption(f"Команда «{application['team_name']}»  ·  {application['company_name']}  ·  Статус: {application_status}")
            st.write(application["pitch"])
            if application["prototype_url"]:
                st.markdown(f"[Ссылка на прототип]({application['prototype_url']})")


try:
    request("GET", "/health")
except ApiError as error:
    st.error("Backend или PostgreSQL пока недоступны.")
    st.info(str(error))
    st.stop()

if st.session_state.pop("reset_new_task_form", False):
    for key in ["new_task_id", "new_task_status", "new_title", "new_description", "new_industry", "new_target_users", "new_available_data", "new_success_criteria", "new_deadline", "new_tags", "new_task_form_initialized"]:
        st.session_state.pop(key, None)
if "next_page" in st.session_state:
    st.session_state["page"] = st.session_state.pop("next_page")

user = st.session_state.get("user")
with st.sidebar:
    st.markdown("## ✦ AI Sana")
    st.caption("Задачи компаний для студенческих команд")
    st.divider()
    if user:
        st.markdown(f"**{user['name']}**")
        st.caption(f"{'Компания' if user['role'] == 'company' else 'Студент'} · {user.get('company_name') or user['email']}")
        if st.button("Выйти", key="logout", use_container_width=True):
            for key in ["access_token", "user", "selected_task_id", "review_task_id"]:
                st.session_state.pop(key, None)
            st.session_state["next_page"] = "Каталог"
            st.rerun()
    else:
        st.caption("Просматривать каталог можно без входа.")
    st.divider()
    pages = ["Каталог"]
    if user:
        if user["role"] == "company":
            pages += ["Кабинет компании", "Новая задача"]
        else:
            pages += ["Моя команда", "Мои отклики"]
    else:
        pages += ["Войти / регистрация"]
    if st.session_state.get("page") not in pages:
        st.session_state["page"] = "Каталог"
    page = st.radio("Разделы", pages, key="page", label_visibility="collapsed")
    st.divider()
    st.caption("Рейтинг показывает полноту карточки, а не качество команды или решения.")

flash = st.session_state.pop("flash_message", None)
if flash:
    st.success(flash)

if page == "Каталог":
    render_catalog(user)
elif page == "Войти / регистрация":
    render_auth()
elif page == "Кабинет компании":
    render_company_dashboard()
elif page == "Новая задача":
    render_new_task()
elif page == "Моя команда":
    render_student_team()
elif page == "Мои отклики":
    render_my_applications()

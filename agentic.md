# 🤖 Multi-Agent Architecture & Pipeline Design — `agentic.md`

Мультиагентная система помогает компаниям превращать краткое описание бизнес-проблемы в понятную практическую задачу для студентов. AI задаёт уточняющие вопросы и формирует редактируемый черновик карточки. Работодатель проверяет и подтверждает данные перед публикацией.

Система не придумывает отсутствующие сведения, не публикует задачи самостоятельно и не выбирает студенческие команды.

## 1. Архитектура пайплайна

```mermaid
graph TD
    User([Представитель компании]) -->|Описание проблемы и ответы| Orchestrator[🎯 Orchestrator Agent]

    subgraph "AI-пайплайн"
        Orchestrator -->|Исходный текст| Parser[🔍 Parser & Extraction Agent]
        Parser -->|Структурированные факты и пробелы| Orchestrator

        Orchestrator -->|Факты и недостающие поля| Questions[❓ Clarification Agent]
        Questions -->|Не менее 3 уместных вопросов| Orchestrator

        User -->|Ответы на вопросы| Orchestrator
        Orchestrator -->|Подтверждённые пользователем сведения| Worker[⚙️ Task Card Worker]
        Worker -->|Черновик карточки по Pydantic-схеме| Orchestrator

        Orchestrator -->|Черновик и исходные сведения| Critic[🛡️ Critic & Guardrail]
        Critic -->|Ошибки или неподтверждённые факты| Orchestrator
        Orchestrator -->|Исправление, максимум 2 попытки| Worker
        Critic -->|Проверка пройдена| Orchestrator
    end

    Orchestrator -->|Карточка и trace| Formatter[📄 Formatter]
    Formatter -->|Редактируемый черновик| Employer([Интерфейс компании])

    Employer -->|Редактирование и подтверждение| Backend[🗄️ Backend API]
    Backend -->|Расчёт рейтинга обычным кодом| Scoring[📊 Readiness Scoring]
    Scoring -->|Подтверждённая задача| Catalog[(📚 Каталог задач)]
    Catalog -->|Просмотр и отклики| Student([Студенческая команда])
    Student -->|Предложение: идея, план, срок, прототип| Applications[(✉️ Отклики)]
    Applications -->|Список предложений| Employer
    Employer -->|Ручной выбор или отклонение| Applications
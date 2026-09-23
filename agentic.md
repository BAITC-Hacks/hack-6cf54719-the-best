# 🤖 Multi-Agent Architecture & Pipeline Design (`agentic.md`)

В данном документе описана архитектура мультиагентной системы, роли автономных агентов, протоколы передачи контекста, цепочки рефлексии (Self-Reflection) и механизмы защиты от галлюцинаций.

---

## 1. Архитектурная схема пайплайна

Система построена по паттерну **Orchestrator-Workers with Reflection Loop**. Центральный координатор управляет жизненным циклом запроса, распределяя задачи между узкоспециализированными агентами.

```mermaid
graph TD
    User([Входные данные / Пользователь]) --> Orchestrator[🎯 Orchestrator Agent]
    
    subgraph "Агентный контур (Core Execution)"
        Orchestrator -->|1. Сырые данные| Parser[🔍 Parser & Extraction Agent]
        Parser -->|Строгий Pydantic JSON| Orchestrator
        
        Orchestrator -->|2. Структурированный контекст| DomainAgent[⚙️ Domain Logic Agent]
        DomainAgent -->|3. Function Calling / Tools| Tools[(🛠️ Tools: Math/DB/Rules)]
        Tools -->|Результат вычислений| DomainAgent
        DomainAgent -->|Черновое решение| Orchestrator
        
        Orchestrator -->|3. Верификация| Critic[🛡️ Critic & Guardrail Agent]
        Critic -- "❌ Ошибка / Несоответствие правилам (Loop <= 2)" --> DomainAgent
        Critic -- "✅ Успешная валидация" --> Orchestrator
    end
    
    Orchestrator -->|4. Финализация| Formatter[📄 Formatter Agent]
    Formatter --> APIResponse([Выходной JSON / UI Streamlit])
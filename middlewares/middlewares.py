import contextvars
from uuid import uuid4

from fastapi import Request

# створює змінну, унікальну для кожного контексту виконання (запиту)
trace_id_var = contextvars.ContextVar("trace_id", default="no_trace")


async def add_trace_id(request: Request, call_next):
    """
    Використовується для додавання заголовка відповіді `X-Trace-Id`,
    з унікальним ідентифікатором для кожного запиту.

    Використовуючи цей `trace_id` можна діставати логи з БД, які були створені
    для конкретного запиту.

    Так як цей ідентифікатор унікальний, то і запис в БД, який
    ідентифікує лог(и), також унікальний.
    """
    trace_id = str(uuid4())
    # призначаємо унікальний trace_id для поточного запиту (контексту)
    trace_id_var.set(trace_id)
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response

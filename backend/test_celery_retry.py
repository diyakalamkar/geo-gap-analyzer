
from celery import Celery

test_app = Celery(
    "retry_test",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

test_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=False,
)


@test_app.task(
    bind=True,
    autoretry_for=(ValueError,),
    retry_backoff=False,
    max_retries=3,
)
def fail_then_succeed(self):
    if self.request.retries < 2:
        raise ValueError("Simulated temporary failure")

    return {
        "status": "success",
        "retries": self.request.retries,
    }


if __name__ == "__main__":
    result = fail_then_succeed.apply()
    print("Task state:", result.state)
    print("Task result:", result.result)

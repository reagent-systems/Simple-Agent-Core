import sentry_sdk
import os

SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENABLED = bool(SENTRY_DSN)

# Initialize Sentry (call this once at app startup)
def init_sentry():
    if not SENTRY_ENABLED:
        print("[Sentry] SENTRY_DSN not set, Sentry logging is disabled.")
        return
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,
        traces_sample_rate=1.0,
        release="simple-agent-core@0.8.2",
        environment="production",
    )

def log_breadcrumb(message, category="agent", level="info", data=None):
    if not SENTRY_ENABLED:
        return
    sentry_sdk.add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=data or {}
    )

def capture_exception(exc):
    if not SENTRY_ENABLED:
        return
    sentry_sdk.capture_exception(exc)

def capture_message(msg, level="info"):
    if not SENTRY_ENABLED:
        return
    sentry_sdk.capture_message(msg, level=level)

def log_run_start(user_instruction, output_dir, max_steps, auto_continue, timestamp, extra_data=None, run_id=None, task_type=None):
    if not SENTRY_ENABLED:
        return
    with sentry_sdk.push_scope() as scope:
        scope.set_extra("instruction", user_instruction)
        scope.set_extra("output_dir", output_dir)
        scope.set_extra("max_steps", max_steps)
        scope.set_extra("auto_continue", auto_continue)
        scope.set_extra("timestamp", timestamp)
        if extra_data:
            for k, v in extra_data.items():
                scope.set_extra(k, v)
        if run_id:
            scope.set_tag("run_id", run_id)
        if task_type:
            scope.set_tag("task_type", task_type)
        sentry_sdk.capture_message("Agent run started with detailed metadata")

def start_agent_run_transaction():
    if not SENTRY_ENABLED:
        class DummyContext:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        return DummyContext()
    return sentry_sdk.start_transaction(op="agent.run", name="Agent Run")

def start_agent_step_span(step):
    if not SENTRY_ENABLED:
        class DummyContext:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        return DummyContext()
    return sentry_sdk.start_span(op="agent.step", description=f"Step {step}")

def start_tool_call_span(function_name):
    if not SENTRY_ENABLED:
        class DummyContext:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        return DummyContext()
    return sentry_sdk.start_span(op="tool.call", description=function_name) 
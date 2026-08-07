#include <uapi/linux/ptrace.h>

struct exec_event_t {
    u32 pid;
    char comm[16];
};

BPF_PERF_OUTPUT(events);

int trace_exec(struct pt_regs *ctx)
{
    struct exec_event_t event = {};

    event.pid = bpf_get_current_pid_tgid() >> 32;

    bpf_get_current_comm(
        &event.comm,
        sizeof(event.comm)
    );

    events.perf_submit(
        ctx,
        &event,
        sizeof(event)
    );

    return 0;
}
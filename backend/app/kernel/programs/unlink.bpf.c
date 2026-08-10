#include "vmlinux.h"

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>

#include "../headers/katana.h"

/* =========================================================
 * Ring buffer
 * ========================================================= */

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);
} events SEC(".maps");

char LICENSE[] SEC("license") = "GPL";

/* =========================================================
 * UNLINK tracepoint
 * ========================================================= */

SEC("tracepoint/syscalls/sys_enter_unlink")
int trace_unlink(struct trace_event_raw_sys_enter *ctx)
{
    struct katana_event *event;

    /* -----------------------------------------------------
     * Reserve event
     * ----------------------------------------------------- */

    event = bpf_ringbuf_reserve(
        &events,
        sizeof(*event),
        0
    );

    if (!event)
        return 0;

    /* -----------------------------------------------------
     * Initialize event
     * ----------------------------------------------------- */

    __builtin_memset(
        event,
        0,
        sizeof(*event)
    );

    /* -----------------------------------------------------
     * Process metadata
     * ----------------------------------------------------- */

    event->type = EVENT_UNLINK;

    event->pid =
        bpf_get_current_pid_tgid() >> 32;

    event->uid =
        bpf_get_current_uid_gid() & 0xffffffff;

    event->timestamp =
        bpf_ktime_get_ns();

    bpf_get_current_comm(
        event->comm,
        sizeof(event->comm)
    );

    /* -----------------------------------------------------
     * Parent PID
     * ----------------------------------------------------- */

    struct task_struct *task =
        (struct task_struct *)bpf_get_current_task();

    struct task_struct *parent =
        BPF_CORE_READ(task, real_parent);

    if (parent) {
        event->ppid =
            BPF_CORE_READ(parent, tgid);
    }

    /* -----------------------------------------------------
     * unlink() arguments
     *
     * args[0] = pathname
     * ----------------------------------------------------- */

    const char *filename =
        (const char *)ctx->args[0];

    if (filename) {
        bpf_probe_read_user_str(
            event->filename,
            sizeof(event->filename),
            filename
        );
    }

    /* -----------------------------------------------------
     * Submit event
     * ----------------------------------------------------- */

    bpf_ringbuf_submit(
        event,
        0
    );

    return 0;
}
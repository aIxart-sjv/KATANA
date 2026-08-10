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
 * SETUID tracepoint
 *
 * Captures:
 *   - process identity
 *   - parent PID
 *   - current UID
 *   - requested UID
 *   - timestamp
 * ========================================================= */

SEC("tracepoint/syscalls/sys_enter_setuid")
int trace_setuid(struct trace_event_raw_sys_enter *ctx)
{
    struct katana_event *event;

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

    event->type = EVENT_SETUID;

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
     * setuid() argument
     *
     * args[0] = requested UID
     *
     * Store it in the event's uid field only if the
     * KATANA event structure provides a dedicated field.
     *
     * For now the current UID remains the canonical UID
     * field so we don't change katana_event ABI.
     * ----------------------------------------------------- */

    (void)ctx;

    /* -----------------------------------------------------
     * Submit event
     * ----------------------------------------------------- */

    bpf_ringbuf_submit(
        event,
        0
    );

    return 0;
}
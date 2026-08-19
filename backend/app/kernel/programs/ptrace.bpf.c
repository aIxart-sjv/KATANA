#include "vmlinux.h"

#include <bpf/bpf_helpers.h>
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
 * PTRACE tracepoint
 * ========================================================= */

SEC("tracepoint/syscalls/sys_enter_ptrace")
int trace_ptrace(struct trace_event_raw_sys_enter *ctx)
{
    struct katana_event *event;

    /* =====================================================
     * Reserve event
     * ===================================================== */

    event = bpf_ringbuf_reserve(
        &events,
        sizeof(*event),
        0
    );

    if (!event)
        return 0;


    /* =====================================================
     * Initialize event
     * ===================================================== */

    __builtin_memset(
        event,
        0,
        sizeof(*event)
    );


    /* =====================================================
     * Process metadata
     * ===================================================== */

    event->type = EVENT_PTRACE;

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


    /* =====================================================
     * Submit event
     * ===================================================== */

    bpf_ringbuf_submit(
        event,
        0
    );

    return 0;
}
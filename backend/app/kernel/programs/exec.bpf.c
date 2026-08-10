#include "vmlinux.h"

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>

#include "../headers/katana.h"

/* ---------------------------------------------------------
 * Ring buffer
 * --------------------------------------------------------- */

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);
} events SEC(".maps");

char LICENSE[] SEC("license") = "GPL";

/* ---------------------------------------------------------
 * EXEC tracepoint
 *
 * sys_enter_execve:
 *
 * args[0] = filename
 * args[1] = argv
 * args[2] = envp
 * --------------------------------------------------------- */

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_exec(struct trace_event_raw_sys_enter *ctx)
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

    __u64 pid_tgid = bpf_get_current_pid_tgid();

    event->type = EVENT_EXEC;

    event->pid = pid_tgid >> 32;

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
     *
     * current task -> real_parent -> tgid
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
     * Executed filename
     *
     * sys_enter_execve args[0] is the userspace
     * pointer to the filename passed to execve().
     * ----------------------------------------------------- */

    const char *filename =
        (const char *)ctx->args[0];

    if (filename) {
        long ret = bpf_probe_read_user_str(
            event->filename,
            sizeof(event->filename),
            filename
        );

        if (ret < 0) {
            event->filename[0] = '\0';
        }
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
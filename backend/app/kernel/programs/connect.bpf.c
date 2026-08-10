#include "vmlinux.h"

#include <bpf/bpf_helpers.h>
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
 * CONNECT tracepoint
 * --------------------------------------------------------- */

SEC("tracepoint/syscalls/sys_enter_connect")
int trace_connect(struct trace_event_raw_sys_enter *ctx)
{
    struct katana_event *event;
    struct sockaddr *addr;

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

    event->type = EVENT_CONNECT;

    event->pid =
        bpf_get_current_pid_tgid() >> 32;

    event->uid =
        bpf_get_current_uid_gid() & 0xffffffff;

    event->timestamp =
        bpf_ktime_get_ns();

    bpf_get_current_comm(
        &event->comm,
        sizeof(event->comm)
    );


    /* -----------------------------------------------------
     * Get connect() arguments
     *
     * args[0] = socket fd
     * args[1] = sockaddr *
     * args[2] = address length
     * ----------------------------------------------------- */

    addr = (struct sockaddr *)ctx->args[1];

    if (!addr) {
        bpf_ringbuf_discard(event, 0);
        return 0;
    }


    /* -----------------------------------------------------
     * Read address family
     * ----------------------------------------------------- */

    __u16 family = 0;

    if (bpf_probe_read_user(
            &family,
            sizeof(family),
            &addr->sa_family) < 0) {

        bpf_ringbuf_discard(event, 0);
        return 0;
    }

    event->family = family;


    /* -----------------------------------------------------
     * IPv4
     *
     * AF_INET = 2
     *
     * sockaddr_in:
     *
     *   sin_family
     *   sin_port
     *   sin_addr
     *
     * IPv4 address and port are kept in network byte order.
     * The native loader converts them for JSON output.
     * ----------------------------------------------------- */

    if (family == 2) {

        struct sockaddr_in addr4 = {};

        if (bpf_probe_read_user(
                &addr4,
                sizeof(addr4),
                addr) < 0) {

            bpf_ringbuf_discard(event, 0);
            return 0;
        }

        event->ipv4 =
            addr4.sin_addr.s_addr;

        event->port =
            addr4.sin_port;
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
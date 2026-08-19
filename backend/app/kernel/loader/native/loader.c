#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <sys/resource.h>
#include <errno.h>

#include <bpf/libbpf.h>

#include <arpa/inet.h>
#include <netinet/in.h>

#include "../../skeletons/exec.skel.h"
#include "../../skeletons/connect.skel.h"
#include "../../skeletons/open.skel.h"
#include "../../skeletons/unlink.skel.h"
#include "../../skeletons/setuid.skel.h"
#include "../../skeletons/ptrace.skel.h"

#include "../../headers/katana.h"

static volatile sig_atomic_t running = 1;


/* =========================================================
 * Signal handling
 * ========================================================= */

static void handle_signal(int sig)
{
    (void)sig;
    running = 0;
}


/* =========================================================
 * Kernel event callback
 * ========================================================= */

static int handle_event(
    void *ctx,
    void *data,
    size_t size
)
{
    (void)ctx;

    if (size < sizeof(struct katana_event)) {
        fprintf(
            stderr,
            "Received invalid event size: %zu\n",
            size
        );

        return 0;
    }

    struct katana_event *event = data;

    char ipv4_str[INET_ADDRSTRLEN] = "";

    if (event->family == AF_INET) {

        struct in_addr addr = {
            .s_addr = event->ipv4
        };

        inet_ntop(
            AF_INET,
            &addr,
            ipv4_str,
            sizeof(ipv4_str)
        );
    }

    printf(
        "{"
        "\"type\":%u,"
        "\"pid\":%u,"
        "\"ppid\":%u,"
        "\"uid\":%u,"
        "\"timestamp\":%llu,"
        "\"comm\":\"%s\","
        "\"ipv4\":\"%s\","
        "\"port\":%u,"
        "\"family\":%u,"
        "\"filename\":\"%s\""
        "}\n",

        event->type,
        event->pid,
        event->ppid,
        event->uid,

        (unsigned long long)event->timestamp,

        event->comm,

        ipv4_str,

        ntohs(event->port),

        event->family,

        event->filename
    );

    fflush(stdout);

    return 0;
}


/* =========================================================
 * Main
 * ========================================================= */

int main(void)
{
    struct exec_bpf *exec_skel = NULL;
    struct connect_bpf *connect_skel = NULL;
    struct open_bpf *open_skel = NULL;
    struct unlink_bpf *unlink_skel = NULL;
    struct setuid_bpf *setuid_skel = NULL;
    struct ptrace_bpf *ptrace_skel = NULL;

    struct ring_buffer *rb = NULL;

    int err = 0;


    /* =====================================================
     * Signal handlers
     * ===================================================== */

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);


    /* =====================================================
     * libbpf configuration
     * ===================================================== */

    libbpf_set_strict_mode(LIBBPF_STRICT_ALL);


    /* =====================================================
     * Increase memory locking limit
     * ===================================================== */

    struct rlimit rlim = {
        .rlim_cur = RLIM_INFINITY,
        .rlim_max = RLIM_INFINITY,
    };

    if (setrlimit(RLIMIT_MEMLOCK, &rlim)) {

        fprintf(
            stderr,
            "Warning: failed to set RLIMIT_MEMLOCK: %s\n",
            strerror(errno)
        );
    }


    /* =====================================================
     * EXEC
     * ===================================================== */

    exec_skel = exec_bpf__open();

    if (!exec_skel) {

        fprintf(
            stderr,
            "Failed to open EXEC BPF skeleton\n"
        );

        err = 1;
        goto cleanup;
    }

    err = exec_bpf__load(exec_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to load EXEC BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }

    err = exec_bpf__attach(exec_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to attach EXEC BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
     * CONNECT
     * ===================================================== */

    connect_skel = connect_bpf__open();

    if (!connect_skel) {

        fprintf(
            stderr,
            "Failed to open CONNECT BPF skeleton\n"
        );

        err = 1;
        goto cleanup;
    }

    err = connect_bpf__load(connect_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to load CONNECT BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }

    err = connect_bpf__attach(connect_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to attach CONNECT BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
     * OPEN
     * ===================================================== */

    open_skel = open_bpf__open();

    if (!open_skel) {

        fprintf(
            stderr,
            "Failed to open OPEN BPF skeleton\n"
        );

        err = 1;
        goto cleanup;
    }

    err = open_bpf__load(open_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to load OPEN BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }

    err = open_bpf__attach(open_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to attach OPEN BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
     * UNLINK
     * ===================================================== */

    unlink_skel = unlink_bpf__open();

    if (!unlink_skel) {

        fprintf(
            stderr,
            "Failed to open UNLINK BPF skeleton\n"
        );

        err = 1;
        goto cleanup;
    }

    err = unlink_bpf__load(unlink_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to load UNLINK BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }

    err = unlink_bpf__attach(unlink_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to attach UNLINK BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
     * SETUID
     * ===================================================== */

    setuid_skel = setuid_bpf__open();

    if (!setuid_skel) {

        fprintf(
            stderr,
            "Failed to open SETUID BPF skeleton\n"
        );

        err = 1;
        goto cleanup;
    }

    err = setuid_bpf__load(setuid_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to load SETUID BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }

    err = setuid_bpf__attach(setuid_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to attach SETUID BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
    * PTRACE
    * ===================================================== */

    ptrace_skel = ptrace_bpf__open();

    if (!ptrace_skel) {

        fprintf(
            stderr,
            "Failed to open PTRACE BPF skeleton\n"
        );

        err = 1;
        goto cleanup;
    }

    err = ptrace_bpf__load(ptrace_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to load PTRACE BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }

    err = ptrace_bpf__attach(ptrace_skel);

    if (err) {

        fprintf(
            stderr,
            "Failed to attach PTRACE BPF skeleton: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
     * Create unified ring buffer
     * ===================================================== */

    rb = ring_buffer__new(
        bpf_map__fd(exec_skel->maps.events),
        handle_event,
        NULL,
        NULL
    );

    if (!rb) {

        fprintf(
            stderr,
            "Failed to create EXEC ring buffer\n"
        );

        err = 1;
        goto cleanup;
    }


    /* =====================================================
     * Add CONNECT ring buffer
     * ===================================================== */

    err = ring_buffer__add(
        rb,
        bpf_map__fd(connect_skel->maps.events),
        handle_event,
        NULL
    );

    if (err) {

        fprintf(
            stderr,
            "Failed to add CONNECT ring buffer: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
     * Add OPEN ring buffer
     * ===================================================== */

    err = ring_buffer__add(
        rb,
        bpf_map__fd(open_skel->maps.events),
        handle_event,
        NULL
    );

    if (err) {

        fprintf(
            stderr,
            "Failed to add OPEN ring buffer: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
     * Add UNLINK ring buffer
     * ===================================================== */

    err = ring_buffer__add(
        rb,
        bpf_map__fd(unlink_skel->maps.events),
        handle_event,
        NULL
    );

    if (err) {

        fprintf(
            stderr,
            "Failed to add UNLINK ring buffer: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
     * Add SETUID ring buffer
     * ===================================================== */

    err = ring_buffer__add(
        rb,
        bpf_map__fd(setuid_skel->maps.events),
        handle_event,
        NULL
    );

    if (err) {

        fprintf(
            stderr,
            "Failed to add SETUID ring buffer: %d\n",
            err
        );

        goto cleanup;
    }

    /* =====================================================
    * Add PTRACE ring buffer
    * ===================================================== */

    err = ring_buffer__add(
        rb,
        bpf_map__fd(ptrace_skel->maps.events),
        handle_event,
        NULL
    );

    if (err) {

        fprintf(
            stderr,
            "Failed to add PTRACE ring buffer: %d\n",
            err
        );

        goto cleanup;
    }


    /* =====================================================
     * Loader ready
     * ===================================================== */

    printf(
        "KATANA Kernel Loader Running\n"
    );

    printf(
        "  [OK] execve tracepoint attached\n"
    );

    printf(
        "  [OK] connect tracepoint attached\n"
    );

    printf(
        "  [OK] openat tracepoint attached\n"
    );

    printf(
        "  [OK] unlink tracepoint attached\n"
    );

    printf(
        "  [OK] setuid tracepoint attached\n"
    );

    printf(
        "  [OK] ptrace tracepoint attached\n"
    );

    fflush(stdout);


    /* =====================================================
     * Event loop
     * ===================================================== */

    while (running) {

        err = ring_buffer__poll(
            rb,
            100
        );

        if (err < 0) {

            if (err == -EINTR) {
                continue;
            }

            fprintf(
                stderr,
                "Ring buffer polling failed: %d\n",
                err
            );

            break;
        }
    }


cleanup:

    if (!running) {

        printf(
            "KATANA Kernel Loader Stopping\n"
        );
    }


    /* =====================================================
     * Cleanup ring buffer
     * ===================================================== */

    ring_buffer__free(rb);


    /* =====================================================
    * Cleanup PTRACE
    * ===================================================== */

    if (ptrace_skel) {
        ptrace_bpf__destroy(ptrace_skel);
    }


    /* =====================================================
     * Cleanup SETUID
     * ===================================================== */

    if (setuid_skel) {
        setuid_bpf__destroy(setuid_skel);
    }


    /* =====================================================
     * Cleanup UNLINK
     * ===================================================== */

    if (unlink_skel) {
        unlink_bpf__destroy(unlink_skel);
    }


    /* =====================================================
     * Cleanup OPEN
     * ===================================================== */

    if (open_skel) {
        open_bpf__destroy(open_skel);
    }


    /* =====================================================
     * Cleanup CONNECT
     * ===================================================== */

    if (connect_skel) {
        connect_bpf__destroy(connect_skel);
    }


    /* =====================================================
     * Cleanup EXEC
     * ===================================================== */

    if (exec_skel) {
        exec_bpf__destroy(exec_skel);
    }


    return err;
}
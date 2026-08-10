#ifndef __KATANA_H__
#define __KATANA_H__

#define TASK_COMM_LEN 16

enum event_type {
    EVENT_EXEC = 1,
    EVENT_CONNECT,
    EVENT_OPEN,
    EVENT_UNLINK,
    EVENT_SETUID,
    EVENT_PTRACE,
};

struct katana_event {

    __u32 pid;
    __u32 ppid;
    __u32 uid;

    __u64 timestamp;

    __u32 type;

    char comm[TASK_COMM_LEN];

    __u32 ipv4;

    __u16 port;

    __u16 family;

    char filename[256];

};

#endif
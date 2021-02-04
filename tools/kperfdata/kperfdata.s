_kpdecode_cursor_setchunk:
    5a99:       55      pushq   %rbp
    5a9a:       48 89 e5        movq    %rsp, %rbp
    5a9d:       b8 fe ff ff ff  movl    $4294967294, %eax
    5aa2:       48 83 7f 18 00  cmpq    $0, 24(%rdi)
    5aa7:       75 1a   jne     26 <_kpdecode_cursor_setchunk+0x2a>
    5aa9:       48 89 77 18     movq    %rsi, 24(%rdi)
    5aad:       48 c7 47 28 00 00 00 00         movq    $0, 40(%rdi)
    5ab5:       48 89 57 20     movq    %rdx, 32(%rdi)
    5ab9:       48 89 57 30     movq    %rdx, 48(%rdi)
    5abd:       48 89 77 50     movq    %rsi, 80(%rdi)
    5ac1:       31 c0   xorl    %eax, %eax
    5ac3:       5d      popq    %rbp
    5ac4:       c3      retq

_kpdecode_cursor_clearchunk:
    5ac5:       55      pushq   %rbp
    5ac6:       48 89 e5        movq    %rsp, %rbp
    5ac9:       48 8b 47 18     movq    24(%rdi), %rax
    5acd:       48 85 c0        testq   %rax, %rax
    5ad0:       74 28   je      40 <_kpdecode_cursor_clearchunk+0x35>
    5ad2:       48 8d 4f 18     leaq    24(%rdi), %rcx
    5ad6:       31 d2   xorl    %edx, %edx
    5ad8:       48 89 57 60     movq    %rdx, 96(%rdi)
    5adc:       48 89 57 58     movq    %rdx, 88(%rdi)
    5ae0:       48 89 57 50     movq    %rdx, 80(%rdi)
    5ae4:       48 89 51 18     movq    %rdx, 24(%rcx)
    5ae8:       48 89 51 10     movq    %rdx, 16(%rcx)
    5aec:       48 89 51 08     movq    %rdx, 8(%rcx)
    5af0:       48 89 11        movq    %rdx, (%rcx)
    5af3:       c6 87 a8 00 00 00 01    movb    $1, 168(%rdi)
    5afa:       5d      popq    %rbp
    5afb:       c3      retq

__kpdecode_cursor_next_kevent:
    5afc:       48 8b 4f 18     movq    24(%rdi), %rcx
    5b00:       48 85 c9        testq   %rcx, %rcx
    5b03:       0f 84 45 01 00 00       je      325 <__kpdecode_cursor_next_kevent+0x152>
    5b09:       55      pushq   %rbp
    5b0a:       48 89 e5        movq    %rsp, %rbp
    5b0d:       41 56   pushq   %r14
    5b0f:       53      pushq   %rbx
    5b10:       8b 07   movl    (%rdi), %eax
    5b12:       85 c0   testl   %eax, %eax
    5b14:       0f 85 cd 00 00 00       jne     205 <__kpdecode_cursor_next_kevent+0xeb>
    5b1a:       4c 8b 5f 20     movq    32(%rdi), %r11
    5b1e:       31 c0   xorl    %eax, %eax
    5b20:       49 81 fb 20 01 00 00    cmpq    $288, %r11
    5b27:       0f 82 ba 00 00 00       jb      186 <__kpdecode_cursor_next_kevent+0xeb>
    5b2d:       8b 31   movl    (%rcx), %esi
    5b2f:       81 fe 00 02 aa 55       cmpl    $1437204992, %esi
    5b35:       74 1a   je      26 <__kpdecode_cursor_next_kevent+0x55>
    5b37:       81 fe 01 01 aa 55       cmpl    $1437204737, %esi
    5b3d:       0f 85 a4 00 00 00       jne     164 <__kpdecode_cursor_next_kevent+0xeb>
    5b43:       c7 07 02 00 00 00       movl    $2, (%rdi)
    5b49:       41 b8 18 00 00 00       movl    $24, %r8d
    5b4f:       eb 28   jmp     40 <__kpdecode_cursor_next_kevent+0x7d>
    5b51:       8b 41 14        movl    20(%rcx), %eax
    5b54:       83 e0 01        andl    $1, %eax
    5b57:       8d 70 01        leal    1(%rax), %esi
    5b5a:       89 37   movl    %esi, (%rdi)
    5b5c:       41 b8 20 01 00 00       movl    $288, %r8d
    5b62:       85 c0   testl   %eax, %eax
    5b64:       75 13   jne     19 <__kpdecode_cursor_next_kevent+0x7d>
    5b66:       b8 01 00 00 00  movl    $1, %eax
    5b6b:       41 b9 1c 00 00 00       movl    $28, %r9d
    5b71:       41 be 20 00 00 00       movl    $32, %r14d
    5b77:       eb 11   jmp     17 <__kpdecode_cursor_next_kevent+0x8e>
    5b79:       b8 02 00 00 00  movl    $2, %eax
    5b7e:       41 b9 20 00 00 00       movl    $32, %r9d
    5b84:       41 be 40 00 00 00       movl    $64, %r14d
    5b8a:       4c 8d 57 18     leaq    24(%rdi), %r10
    5b8e:       4c 89 77 08     movq    %r14, 8(%rdi)
    5b92:       4c 89 4f 10     movq    %r9, 16(%rdi)
    5b96:       48 63 51 04     movslq  4(%rcx), %rdx
    5b9a:       49 0f af d1     imulq   %r9, %rdx
    5b9e:       4a 8d 34 02     leaq    (%rdx,%r8), %rsi
    5ba2:       4a 8d 9c 02 00 10 00 00         leaq    4096(%rdx,%r8), %rbx
    5baa:       48 81 e3 00 f0 ff ff    andq    $-4096, %rbx
    5bb1:       f7 c6 fc 0f 00 00       testl   $4092, %esi
    5bb7:       48 0f 44 de     cmoveq  %rsi, %rbx
    5bbb:       c7 47 40 01 00 00 00    movl    $1, 64(%rdi)
    5bc2:       4c 89 57 48     movq    %r10, 72(%rdi)
    5bc6:       49 01 de        addq    %rbx, %r14
    5bc9:       48 01 cb        addq    %rcx, %rbx
    5bcc:       31 f6   xorl    %esi, %esi
    5bce:       4d 39 f3        cmpq    %r14, %r11
    5bd1:       48 0f 43 f3     cmovaeq %rbx, %rsi
    5bd5:       48 89 77 50     movq    %rsi, 80(%rdi)
    5bd9:       4c 01 c1        addq    %r8, %rcx
    5bdc:       48 89 4f 58     movq    %rcx, 88(%rdi)
    5be0:       48 01 d1        addq    %rdx, %rcx
    5be3:       48 89 4f 60     movq    %rcx, 96(%rdi)
    5be7:       83 7f 40 00     cmpl    $0, 64(%rdi)
    5beb:       5b      popq    %rbx
    5bec:       41 5e   popq    %r14
    5bee:       5d      popq    %rbp
    5bef:       74 5d   je      93 <__kpdecode_cursor_next_kevent+0x152>
    5bf1:       80 bf a8 00 00 00 00    cmpb    $0, 168(%rdi)
    5bf8:       75 41   jne     65 <__kpdecode_cursor_next_kevent+0x13f>
    5bfa:       48 8b 4f 58     movq    88(%rdi), %rcx
    5bfe:       48 85 c9        testq   %rcx, %rcx
    5c01:       74 38   je      56 <__kpdecode_cursor_next_kevent+0x13f>
    5c03:       48 8b 57 60     movq    96(%rdi), %rdx
    5c07:       48 39 d1        cmpq    %rdx, %rcx
    5c0a:       73 28   jae     40 <__kpdecode_cursor_next_kevent+0x138>
    5c0c:       31 f6   xorl    %esi, %esi
    5c0e:       83 f8 01        cmpl    $1, %eax
    5c11:       40 0f 95 c6     setne   %sil
    5c15:       48 8d 34 b5 04 00 00 00         leaq    4(,%rsi,4), %rsi
    5c1d:       83 3c 31 00     cmpl    $0, (%rcx,%rsi)
    5c21:       0f 85 99 00 00 00       jne     153 <__kpdecode_cursor_next_kevent+0x1c4>
    5c27:       48 03 4f 10     addq    16(%rdi), %rcx
    5c2b:       48 89 4f 58     movq    %rcx, 88(%rdi)
    5c2f:       48 39 ca        cmpq    %rcx, %rdx
    5c32:       77 e9   ja      -23 <__kpdecode_cursor_next_kevent+0x121>
    5c34:       c6 87 a8 00 00 00 01    movb    $1, 168(%rdi)
    5c3b:       48 8b 4f 50     movq    80(%rdi), %rcx
    5c3f:       48 85 c9        testq   %rcx, %rcx
    5c42:       74 0a   je      10 <__kpdecode_cursor_next_kevent+0x152>
    5c44:       83 f8 02        cmpl    $2, %eax
    5c47:       75 08   jne     8 <__kpdecode_cursor_next_kevent+0x155>
    5c49:       48 89 c8        movq    %rcx, %rax
    5c4c:       eb 51   jmp     81 <__kpdecode_cursor_next_kevent+0x1a3>
    5c4e:       31 c0   xorl    %eax, %eax
    5c50:       c3      retq
    5c51:       48 8b 11        movq    (%rcx), %rdx
    5c54:       48 b8 ff ff ff ff ff ff ff 00   movabsq $72057594037927935, %rax
    5c5e:       48 21 d0        andq    %rdx, %rax
    5c61:       48 89 47 68     movq    %rax, 104(%rdi)
    5c65:       66 0f 38 35 41 08       pmovzxdq        8(%rcx), %xmm0
    5c6b:       f3 0f 7f 47 70  movdqu  %xmm0, 112(%rdi)
    5c70:       66 0f 38 35 41 10       pmovzxdq        16(%rcx), %xmm0
    5c76:       48 8d 47 68     leaq    104(%rdi), %rax
    5c7a:       f3 0f 7f 87 80 00 00 00         movdqu  %xmm0, 128(%rdi)
    5c82:       8b 71 18        movl    24(%rcx), %esi
    5c85:       48 89 b7 90 00 00 00    movq    %rsi, 144(%rdi)
    5c8c:       8b 71 1c        movl    28(%rcx), %esi
    5c8f:       89 b7 98 00 00 00       movl    %esi, 152(%rdi)
    5c95:       48 c1 ea 38     shrq    $56, %rdx
    5c99:       89 97 9c 00 00 00       movl    %edx, 156(%rdi)
    5c9f:       48 03 4f 08     addq    8(%rdi), %rcx
    5ca3:       48 89 4f 50     movq    %rcx, 80(%rdi)
    5ca7:       48 8b 57 48     movq    72(%rdi), %rdx
    5cab:       48 8b 32        movq    (%rdx), %rsi
    5cae:       48 03 72 18     addq    24(%rdx), %rsi
    5cb2:       48 39 ce        cmpq    %rcx, %rsi
    5cb5:       77 08   ja      8 <__kpdecode_cursor_next_kevent+0x1c3>
    5cb7:       48 c7 47 50 00 00 00 00         movq    $0, 80(%rdi)
    5cbf:       c3      retq
    5cc0:       48 8d 57 70     leaq    112(%rdi), %rdx
    5cc4:       48 c7 47 68 00 00 00 00         movq    $0, 104(%rdi)
    5ccc:       48 c7 87 98 00 00 00 08 00 01 07        movq    $117506056, 152(%rdi)
    5cd7:       83 f8 01        cmpl    $1, %eax
    5cda:       75 19   jne     25 <__kpdecode_cursor_next_kevent+0x1f9>
    5cdc:       8b 41 18        movl    24(%rcx), %eax
    5cdf:       89 42 10        movl    %eax, 16(%rdx)
    5ce2:       48 8b 41 08     movq    8(%rcx), %rax
    5ce6:       48 8b 71 10     movq    16(%rcx), %rsi
    5cea:       48 89 72 08     movq    %rsi, 8(%rdx)
    5cee:       48 89 02        movq    %rax, (%rdx)
    5cf1:       8b 01   movl    (%rcx), %eax
    5cf3:       eb 18   jmp     24 <__kpdecode_cursor_next_kevent+0x211>
    5cf5:       8b 41 1c        movl    28(%rcx), %eax
    5cf8:       89 42 10        movl    %eax, 16(%rdx)
    5cfb:       48 8b 41 0c     movq    12(%rcx), %rax
    5cff:       48 8b 71 14     movq    20(%rcx), %rsi
    5d03:       48 89 72 08     movq    %rsi, 8(%rdx)
    5d07:       48 89 02        movq    %rax, (%rdx)
    5d0a:       48 8b 01        movq    (%rcx), %rax
    5d0d:       48 89 87 90 00 00 00    movq    %rax, 144(%rdi)
    5d14:       48 8b 47 10     movq    16(%rdi), %rax
    5d18:       48 01 47 58     addq    %rax, 88(%rdi)
    5d1c:       48 8d 47 68     leaq    104(%rdi), %rax
    5d20:       c3      retq

_kpdecode_cursor_create:
    5d24:       55      pushq   %rbp
    5d25:       48 89 e5        movq    %rsp, %rbp
    5d28:       bf 01 00 00 00  movl    $1, %edi
    5d2d:       be e0 04 00 00  movl    $1248, %esi
    5d32:       5d      popq    %rbp
    5d33:       e9 7a 1a 00 00  jmp     6778 <dyld_stub_binder+0x77b2>

_kpdecode_cursor_free:
    5d38:       55      pushq   %rbp
    5d39:       48 89 e5        movq    %rsp, %rbp
    5d3c:       5d      popq    %rbp
    5d3d:       e9 88 1a 00 00  jmp     6792 <dyld_stub_binder+0x77ca>

_kpdecode_cursor_flush:
    5d42:       55      pushq   %rbp
    5d43:       48 89 e5        movq    %rsp, %rbp
    5d46:       5d      popq    %rbp
    5d47:       c3      retq

_kpdecode_cursor_get_stats:
    5d48:       55      pushq   %rbp
    5d49:       48 89 e5        movq    %rsp, %rbp
    5d4c:       48 c7 c0 ff ff ff ff    movq    $-1, %rax
    5d53:       83 fe 01        cmpl    $1, %esi
    5d56:       74 1f   je      31 <_kpdecode_cursor_get_stats+0x2f>
    5d58:       85 f6   testl   %esi, %esi
    5d5a:       75 36   jne     54 <_kpdecode_cursor_get_stats+0x4a>
    5d5c:       83 7f 40 00     cmpl    $0, 64(%rdi)
    5d60:       74 30   je      48 <_kpdecode_cursor_get_stats+0x4a>
    5d62:       48 8b 87 b0 00 00 00    movq    176(%rdi), %rax
    5d69:       48 85 c0        testq   %rax, %rax
    5d6c:       74 18   je      24 <_kpdecode_cursor_get_stats+0x3e>
    5d6e:       48 8b 80 c0 0b 00 00    movq    3008(%rax), %rax
    5d75:       eb 1b   jmp     27 <_kpdecode_cursor_get_stats+0x4a>
    5d77:       83 7f 40 00     cmpl    $0, 64(%rdi)
    5d7b:       74 15   je      21 <_kpdecode_cursor_get_stats+0x4a>
    5d7d:       48 63 87 c4 00 00 00    movslq  196(%rdi), %rax
    5d84:       eb 0c   jmp     12 <_kpdecode_cursor_get_stats+0x4a>
    5d86:       48 63 87 c0 00 00 00    movslq  192(%rdi), %rax
    5d8d:       48 0f af 47 08  imulq   8(%rdi), %rax
    5d92:       5d      popq    %rbp
    5d93:       c3      retq

_kpdecode_cursor_set_option:
    5d94:       55      pushq   %rbp
    5d95:       48 89 e5        movq    %rsp, %rbp
    5d98:       48 c7 c0 ff ff ff ff    movq    $-1, %rax
    5d9f:       85 f6   testl   %esi, %esi
    5da1:       75 11   jne     17 <_kpdecode_cursor_set_option+0x20>
    5da3:       0f b6 87 dc 04 00 00    movzbl  1244(%rdi), %eax
    5daa:       48 85 d2        testq   %rdx, %rdx
    5dad:       0f 95 87 dc 04 00 00    setne   1244(%rdi)
    5db4:       5d      popq    %rbp
    5db5:       c3      retq

_kpdecode_record_free:
    5db6:       55      pushq   %rbp
    5db7:       48 89 e5        movq    %rsp, %rbp
    5dba:       53      pushq   %rbx
    5dbb:       50      pushq   %rax
    5dbc:       48 89 fb        movq    %rdi, %rbx
    5dbf:       48 8b bf 38 0a 00 00    movq    2616(%rdi), %rdi
    5dc6:       48 85 ff        testq   %rdi, %rdi
    5dc9:       74 05   je      5 <_kpdecode_record_free+0x1a>
    5dcb:       e8 fa 19 00 00  callq   6650 <dyld_stub_binder+0x77ca>
    5dd0:       48 89 df        movq    %rbx, %rdi
    5dd3:       48 83 c4 08     addq    $8, %rsp
    5dd7:       5b      popq    %rbx
    5dd8:       5d      popq    %rbp
    5dd9:       e9 ec 19 00 00  jmp     6636 <dyld_stub_binder+0x77ca>

_kpdecode_cursor_next_record:
    5dde:       55      pushq   %rbp
    5ddf:       48 89 e5        movq    %rsp, %rbp
    5de2:       41 57   pushq   %r15
    5de4:       41 56   pushq   %r14
    5de6:       41 55   pushq   %r13
    5de8:       41 54   pushq   %r12
    5dea:       53      pushq   %rbx
    5deb:       50      pushq   %rax
    5dec:       48 89 75 d0     movq    %rsi, -48(%rbp)
    5df0:       48 89 fb        movq    %rdi, %rbx
    5df3:       48 89 df        movq    %rbx, %rdi
    5df6:       e8 91 0d 00 00  callq   3473 <_record_ready>
    5dfb:       84 c0   testb   %al, %al
    5dfd:       0f 85 08 0d 00 00       jne     3336 <_kpdecode_cursor_next_record+0xd2d>
    5e03:       48 89 df        movq    %rbx, %rdi
    5e06:       e8 f1 fc ff ff  callq   -783 <__kpdecode_cursor_next_kevent>
    5e0b:       48 85 c0        testq   %rax, %rax
    5e0e:       0f 84 f7 0c 00 00       je      3319 <_kpdecode_cursor_next_record+0xd2d>
    5e14:       49 89 c4        movq    %rax, %r12
    5e17:       49 89 dd        movq    %rbx, %r13
    5e1a:       48 63 9b c0 00 00 00    movslq  192(%rbx), %rbx
    5e21:       48 ff c3        incq    %rbx
    5e24:       41 89 9d c0 00 00 00    movl    %ebx, 192(%r13)
    5e2b:       bf c8 0b 00 00  movl    $3016, %edi
    5e30:       e8 b9 19 00 00  callq   6585 <dyld_stub_binder+0x77ee>
    5e35:       48 85 c0        testq   %rax, %rax
    5e38:       0f 84 25 0d 00 00       je      3365 <_kpdecode_cursor_next_record+0xd85>
    5e3e:       49 89 c7        movq    %rax, %r15
    5e41:       31 c0   xorl    %eax, %eax
    5e43:       41 89 87 a0 0b 00 00    movl    %eax, 2976(%r15)
    5e4a:       48 b9 00 00 00 00 ff ff ff ff   movabsq $-4294967296, %rcx
    5e54:       49 89 8f b8 0b 00 00    movq    %rcx, 3000(%r15)
    5e5b:       41 89 47 18     movl    %eax, 24(%r15)
    5e5f:       49 89 47 10     movq    %rax, 16(%r15)
    5e63:       49 89 47 08     movq    %rax, 8(%r15)
    5e67:       49 89 07        movq    %rax, (%r15)
    5e6a:       49 89 87 38 0a 00 00    movq    %rax, 2616(%r15)
    5e71:       41 89 87 78 08 00 00    movl    %eax, 2168(%r15)
    5e78:       49 8b 04 24     movq    (%r12), %rax
    5e7c:       49 89 47 08     movq    %rax, 8(%r15)
    5e80:       49 0f af 5d 08  imulq   8(%r13), %rbx
    5e85:       49 89 9f c0 0b 00 00    movq    %rbx, 3008(%r15)
    5e8c:       45 8b 74 24 34  movl    52(%r12), %r14d
    5e91:       49 83 fe 20     cmpq    $32, %r14
    5e95:       0f 82 8d 00 00 00       jb      141 <_kpdecode_cursor_next_record+0x14a>
    5e9b:       41 8b 44 24 30  movl    48(%r12), %eax
    5ea0:       41 89 47 30     movl    %eax, 48(%r15)
    5ea4:       49 8b 44 24 08  movq    8(%r12), %rax
    5ea9:       49 89 47 38     movq    %rax, 56(%r15)
    5ead:       49 8b 44 24 10  movq    16(%r12), %rax
    5eb2:       49 89 47 40     movq    %rax, 64(%r15)
    5eb6:       49 8b 44 24 18  movq    24(%r12), %rax
    5ebb:       49 89 47 48     movq    %rax, 72(%r15)
    5ebf:       49 8b 44 24 20  movq    32(%r12), %rax
    5ec4:       49 89 47 50     movq    %rax, 80(%r15)
    5ec8:       49 8b 44 24 28  movq    40(%r12), %rax
    5ecd:       49 89 47 10     movq    %rax, 16(%r15)
    5ed1:       45 89 77 18     movl    %r14d, 24(%r15)
    5ed5:       48 b8 00 00 00 00 00 00 00 80   movabsq $-9223372036854775808, %rax
    5edf:       48 8d 40 17     leaq    23(%rax), %rax
    5ee3:       49 89 07        movq    %rax, (%r15)
    5ee6:       41 c7 87 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r15)
    5ef1:       41 ff 85 c4 00 00 00    incl    196(%r13)
    5ef8:       49 c7 87 a8 0b 00 00 00 00 00 00        movq    $0, 2984(%r15)
    5f03:       49 8b 85 b8 00 00 00    movq    184(%r13), %rax
    5f0a:       48 85 c0        testq   %rax, %rax
    5f0d:       4c 89 eb        movq    %r13, %rbx
    5f10:       74 07   je      7 <_kpdecode_cursor_next_record+0x13b>
    5f12:       4c 89 b8 a8 0b 00 00    movq    %r15, 2984(%rax)
    5f19:       4c 89 bb b8 00 00 00    movq    %r15, 184(%rbx)
    5f20:       45 31 ed        xorl    %r13d, %r13d
    5f23:       e9 16 07 00 00  jmp     1814 <_kpdecode_cursor_next_record+0x860>
    5f28:       48 85 c0        testq   %rax, %rax
    5f2b:       4c 89 eb        movq    %r13, %rbx
    5f2e:       74 2e   je      46 <_kpdecode_cursor_next_record+0x180>
    5f30:       41 81 7c 24 30 00 00 99 25      cmpl    $630784000, 48(%r12)
    5f39:       74 23   je      35 <_kpdecode_cursor_next_record+0x180>
    5f3b:       4a 8b 84 f3 c8 03 00 00         movq    968(%rbx,%r14,8), %rax
    5f43:       48 ff c0        incq    %rax
    5f46:       4a 89 84 f3 c8 03 00 00         movq    %rax, 968(%rbx,%r14,8)
    5f4e:       48 3b 83 c8 04 00 00    cmpq    1224(%rbx), %rax
    5f55:       76 07   jbe     7 <_kpdecode_cursor_next_record+0x180>
    5f57:       48 89 83 c8 04 00 00    movq    %rax, 1224(%rbx)
    5f5e:       80 bb dc 04 00 00 00    cmpb    $0, 1244(%rbx)
    5f65:       74 48   je      72 <_kpdecode_cursor_next_record+0x1d1>
    5f67:       49 c7 07 17 00 00 00    movq    $23, (%r15)
    5f6e:       41 8b 44 24 30  movl    48(%r12), %eax
    5f73:       41 89 47 30     movl    %eax, 48(%r15)
    5f77:       49 8b 4c 24 08  movq    8(%r12), %rcx
    5f7c:       49 89 4f 38     movq    %rcx, 56(%r15)
    5f80:       49 8b 4c 24 10  movq    16(%r12), %rcx
    5f85:       49 89 4f 40     movq    %rcx, 64(%r15)
    5f89:       49 8b 4c 24 18  movq    24(%r12), %rcx
    5f8e:       49 89 4f 48     movq    %rcx, 72(%r15)
    5f92:       49 8b 4c 24 20  movq    32(%r12), %rcx
    5f97:       49 89 4f 50     movq    %rcx, 80(%r15)
    5f9b:       49 8b 4c 24 28  movq    40(%r12), %rcx
    5fa0:       49 89 4f 10     movq    %rcx, 16(%r15)
    5fa4:       45 89 77 18     movl    %r14d, 24(%r15)
    5fa8:       b9 17 00 00 00  movl    $23, %ecx
    5fad:       eb 07   jmp     7 <_kpdecode_cursor_next_record+0x1d8>
    5faf:       41 8b 44 24 30  movl    48(%r12), %eax
    5fb4:       31 c9   xorl    %ecx, %ecx
    5fb6:       3d 08 00 02 07  cmpl    $117571592, %eax
    5fbb:       0f 85 a4 00 00 00       jne     164 <_kpdecode_cursor_next_record+0x287>
    5fc1:       48 81 c9 03 00 01 00    orq     $65539, %rcx
    5fc8:       49 89 0f        movq    %rcx, (%r15)
    5fcb:       45 89 77 18     movl    %r14d, 24(%r15)
    5fcf:       49 8b 04 24     movq    (%r12), %rax
    5fd3:       49 89 47 08     movq    %rax, 8(%r15)
    5fd7:       4a 8b 8c f3 c8 02 00 00         movq    712(%rbx,%r14,8), %rcx
    5fdf:       49 89 8f 40 0a 00 00    movq    %rcx, 2624(%r15)
    5fe6:       41 c7 87 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r15)
    5ff1:       4a 89 84 f3 c8 02 00 00         movq    %rax, 712(%rbx,%r14,8)
    5ff9:       4a 8b 84 f3 c8 00 00 00         movq    200(%rbx,%r14,8), %rax
    6001:       48 85 c0        testq   %rax, %rax
    6004:       74 23   je      35 <_kpdecode_cursor_next_record+0x24b>
    6006:       48 b9 00 00 00 00 00 00 00 80   movabsq $-9223372036854775808, %rcx
    6010:       48 09 08        orq     %rcx, (%rax)
    6013:       c7 80 a0 0b 00 00 01 00 00 00   movl    $1, 2976(%rax)
    601d:       4a c7 84 f3 c8 00 00 00 00 00 00 00     movq    $0, 200(%rbx,%r14,8)
    6029:       4a 8b 84 f3 c8 01 00 00         movq    456(%rbx,%r14,8), %rax
    6031:       45 31 ed        xorl    %r13d, %r13d
    6034:       48 85 c0        testq   %rax, %rax
    6037:       0f 84 b8 05 00 00       je      1464 <_kpdecode_cursor_next_record+0x817>
    603d:       48 b9 00 00 00 00 00 00 00 80   movabsq $-9223372036854775808, %rcx
    6047:       48 09 08        orq     %rcx, (%rax)
    604a:       c7 80 a0 0b 00 00 01 00 00 00   movl    $1, 2976(%rax)
    6054:       4a c7 84 f3 c8 01 00 00 00 00 00 00     movq    $0, 456(%rbx,%r14,8)
    6060:       e9 90 05 00 00  jmp     1424 <_kpdecode_cursor_next_record+0x817>
    6065:       49 8b 14 24     movq    (%r12), %rdx
    6069:       4a 89 94 f3 c8 02 00 00         movq    %rdx, 712(%rbx,%r14,8)
    6071:       3d 01 00 00 25  cmpl    $620756993, %eax
    6076:       75 54   jne     84 <_kpdecode_cursor_next_record+0x2ee>
    6078:       41 bd 02 00 00 00       movl    $2, %r13d
    607e:       4a 83 bc f3 c8 00 00 00 00      cmpq    $0, 200(%rbx,%r14,8)
    6087:       0f 85 68 05 00 00       jne     1384 <_kpdecode_cursor_next_record+0x817>
    608d:       4e 89 bc f3 c8 00 00 00         movq    %r15, 200(%rbx,%r14,8)
    6095:       48 81 c9 07 20 00 00    orq     $8199, %rcx
    609c:       49 89 0f        movq    %rcx, (%r15)
    609f:       45 89 77 18     movl    %r14d, 24(%r15)
    60a3:       41 8b 44 24 10  movl    16(%r12), %eax
    60a8:       41 89 87 18 0a 00 00    movl    %eax, 2584(%r15)
    60af:       41 8b 44 24 18  movl    24(%r12), %eax
    60b4:       41 89 87 1c 0a 00 00    movl    %eax, 2588(%r15)
    60bb:       49 8b 44 24 28  movq    40(%r12), %rax
    60c0:       49 89 47 10     movq    %rax, 16(%r15)
    60c4:       45 31 ed        xorl    %r13d, %r13d
    60c7:       e9 29 05 00 00  jmp     1321 <_kpdecode_cursor_next_record+0x817>
    60cc:       89 c2   movl    %eax, %edx
    60ce:       83 e2 fc        andl    $-4, %edx
    60d1:       81 fa 00 00 01 07       cmpl    $117506048, %edx
    60d7:       75 58   jne     88 <_kpdecode_cursor_next_record+0x353>
    60d9:       a8 01   testb   $1, %al
    60db:       0f 85 b9 00 00 00       jne     185 <_kpdecode_cursor_next_record+0x3bc>
    60e1:       4e 8b ac f3 c8 01 00 00         movq    456(%rbx,%r14,8), %r13
    60e9:       4d 85 ed        testq   %r13, %r13
    60ec:       0f 84 cd 01 00 00       je      461 <_kpdecode_cursor_next_record+0x4e1>
    60f2:       4c 89 e6        movq    %r12, %rsi
    60f5:       48 83 c6 08     addq    $8, %rsi
    60f9:       ba 04 00 00 00  movl    $4, %edx
    60fe:       48 89 df        movq    %rbx, %rdi
    6101:       4c 89 e9        movq    %r13, %rcx
    6104:       e8 e7 0a 00 00  callq   2791 <_batch_get_bytes>
    6109:       41 f6 44 24 30 02       testb   $2, 48(%r12)
    610f:       0f 84 cc 04 00 00       je      1228 <_kpdecode_cursor_next_record+0x803>
    6115:       41 c7 85 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r13)
    6120:       4a c7 84 f3 c8 01 00 00 00 00 00 00     movq    $0, 456(%rbx,%r14,8)
    612c:       e9 b0 04 00 00  jmp     1200 <_kpdecode_cursor_next_record+0x803>
    6131:       4e 8b ac f3 c8 00 00 00         movq    200(%rbx,%r14,8), %r13
    6139:       4d 85 ed        testq   %r13, %r13
    613c:       0f 84 c0 00 00 00       je      192 <_kpdecode_cursor_next_record+0x424>
    6142:       3d 0f 00 02 25  cmpl    $620888079, %eax
    6147:       0f 8f 04 01 00 00       jg      260 <_kpdecode_cursor_next_record+0x473>
    614d:       3d 3b 00 01 25  cmpl    $620822587, %eax
    6152:       0f 8f a9 01 00 00       jg      425 <_kpdecode_cursor_next_record+0x523>
    6158:       3d 23 00 01 25  cmpl    $620822563, %eax
    615d:       0f 8e 54 02 00 00       jle     596 <_kpdecode_cursor_next_record+0x5d9>
    6163:       3d 33 00 01 25  cmpl    $620822579, %eax
    6168:       0f 8f 04 05 00 00       jg      1284 <_kpdecode_cursor_next_record+0x894>
    616e:       3d 24 00 01 25  cmpl    $620822564, %eax
    6173:       0f 84 3e 06 00 00       je      1598 <_kpdecode_cursor_next_record+0x9d9>
    6179:       3d 2c 00 01 25  cmpl    $620822572, %eax
    617e:       0f 85 5d 04 00 00       jne     1117 <_kpdecode_cursor_next_record+0x803>
    6184:       41 80 4d 02 80  orb     $-128, 2(%r13)
    6189:       49 8b 44 24 08  movq    8(%r12), %rax
    618e:       49 89 85 10 0a 00 00    movq    %rax, 2576(%r13)
    6195:       e9 47 04 00 00  jmp     1095 <_kpdecode_cursor_next_record+0x803>
    619a:       48 81 c9 00 00 08 00    orq     $524288, %rcx
    61a1:       49 89 0f        movq    %rcx, (%r15)
    61a4:       45 89 77 18     movl    %r14d, 24(%r15)
    61a8:       4c 89 ff        movq    %r15, %rdi
    61ab:       48 81 c7 50 0a 00 00    addq    $2640, %rdi
    61b2:       be 18 01 00 00  movl    $280, %esi
    61b7:       e8 d8 15 00 00  callq   5592 <dyld_stub_binder+0x7794>
    61bc:       41 bd 02 00 00 00       movl    $2, %r13d
    61c2:       4a 83 bc f3 c8 01 00 00 00      cmpq    $0, 456(%rbx,%r14,8)
    61cb:       0f 85 24 04 00 00       jne     1060 <_kpdecode_cursor_next_record+0x817>
    61d1:       49 8b 44 24 10  movq    16(%r12), %rax
    61d6:       49 89 87 58 0b 00 00    movq    %rax, 2904(%r15)
    61dd:       41 8b 44 24 08  movl    8(%r12), %eax
    61e2:       41 89 87 60 0b 00 00    movl    %eax, 2912(%r15)
    61e9:       41 f6 44 24 30 02       testb   $2, 48(%r12)
    61ef:       0f 85 9b 01 00 00       jne     411 <_kpdecode_cursor_next_record+0x5b2>
    61f5:       4e 89 bc f3 c8 01 00 00         movq    %r15, 456(%rbx,%r14,8)
    61fd:       e9 99 01 00 00  jmp     409 <_kpdecode_cursor_next_record+0x5bd>
    6202:       3d 08 00 03 25  cmpl    $620953608, %eax
    6207:       0f 8f bd 00 00 00       jg      189 <_kpdecode_cursor_next_record+0x4ec>
    620d:       3d 08 00 01 07  cmpl    $117506056, %eax
    6212:       0f 84 cc 02 00 00       je      716 <_kpdecode_cursor_next_record+0x706>
    6218:       3d 14 00 01 25  cmpl    $620822548, %eax
    621d:       0f 84 04 03 00 00       je      772 <_kpdecode_cursor_next_record+0x749>
    6223:       3d 00 00 03 25  cmpl    $620953600, %eax
    6228:       0f 85 2b 03 00 00       jne     811 <_kpdecode_cursor_next_record+0x77b>
    622e:       48 81 c9 00 00 00 01    orq     $16777216, %rcx
    6235:       49 89 0f        movq    %rcx, (%r15)
    6238:       45 89 77 18     movl    %r14d, 24(%r15)
    623c:       41 c7 87 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r15)
    6247:       b8 00 00 03 25  movl    $620953600, %eax
    624c:       e9 08 03 00 00  jmp     776 <_kpdecode_cursor_next_record+0x77b>
    6251:       3d 23 00 06 25  cmpl    $621150243, %eax
    6256:       0f 8f db 00 00 00       jg      219 <_kpdecode_cursor_next_record+0x559>
    625c:       3d 0b 00 06 25  cmpl    $621150219, %eax
    6261:       0f 8e 86 01 00 00       jle     390 <_kpdecode_cursor_next_record+0x60f>
    6267:       3d 17 00 06 25  cmpl    $621150231, %eax
    626c:       0f 8f 38 04 00 00       jg      1080 <_kpdecode_cursor_next_record+0x8cc>
    6272:       3d 0c 00 06 25  cmpl    $621150220, %eax
    6277:       0f 84 79 05 00 00       je      1401 <_kpdecode_cursor_next_record+0xa18>
    627d:       3d 10 00 06 25  cmpl    $621150224, %eax
    6282:       0f 85 59 03 00 00       jne     857 <_kpdecode_cursor_next_record+0x803>
    6288:       41 80 4d 01 08  orb     $8, 1(%r13)
    628d:       41 0f 10 44 24 08       movups  8(%r12), %xmm0
    6293:       41 0f 10 4c 24 18       movups  24(%r12), %xmm1
    6299:       0f 28 d0        movaps  %xmm0, %xmm2
    629c:       66 0f 15 d1     unpckhpd        %xmm1, %xmm2
    62a0:       0f 16 c1        movlhps %xmm1, %xmm0
    62a3:       0f c6 c2 88     shufps  $136, %xmm2, %xmm0
    62a7:       41 0f 11 85 80 09 00 00         movups  %xmm0, 2432(%r13)
    62af:       41 c7 85 78 08 00 00 00 00 00 00        movl    $0, 2168(%r13)
    62ba:       e9 22 03 00 00  jmp     802 <_kpdecode_cursor_next_record+0x803>
    62bf:       41 bd 02 00 00 00       movl    $2, %r13d
    62c5:       e9 2b 03 00 00  jmp     811 <_kpdecode_cursor_next_record+0x817>
    62ca:       3d 09 00 03 25  cmpl    $620953609, %eax
    62cf:       74 12   je      18 <_kpdecode_cursor_next_record+0x505>
    62d1:       3d 01 00 06 25  cmpl    $621150209, %eax
    62d6:       74 0b   je      11 <_kpdecode_cursor_next_record+0x505>
    62d8:       3d 01 00 09 25  cmpl    $621346817, %eax
    62dd:       0f 85 76 02 00 00       jne     630 <_kpdecode_cursor_next_record+0x77b>
    62e3:       48 81 c9 00 01 00 00    orq     $256, %rcx
    62ea:       49 89 0f        movq    %rcx, (%r15)
    62ed:       45 89 77 18     movl    %r14d, 24(%r15)
    62f1:       41 c7 87 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r15)
    62fc:       e9 58 02 00 00  jmp     600 <_kpdecode_cursor_next_record+0x77b>
    6301:       3d 47 00 01 25  cmpl    $620822599, %eax
    6306:       0f 8e 44 01 00 00       jle     324 <_kpdecode_cursor_next_record+0x672>
    630c:       3d 4f 00 01 25  cmpl    $620822607, %eax
    6311:       0f 8f b3 03 00 00       jg      947 <_kpdecode_cursor_next_record+0x8ec>
    6317:       3d 48 00 01 25  cmpl    $620822600, %eax
    631c:       0f 84 e9 04 00 00       je      1257 <_kpdecode_cursor_next_record+0xa2d>
    6322:       3d 4c 00 01 25  cmpl    $620822604, %eax
    6327:       0f 85 b4 02 00 00       jne     692 <_kpdecode_cursor_next_record+0x803>
    632d:       ba 02 00 00 00  movl    $2, %edx
    6332:       e9 a6 00 00 00  jmp     166 <_kpdecode_cursor_next_record+0x5ff>
    6337:       3d 0b 00 08 25  cmpl    $621281291, %eax
    633c:       0f 8e 47 01 00 00       jle     327 <_kpdecode_cursor_next_record+0x6ab>
    6342:       3d 07 00 0a 25  cmpl    $621412359, %eax
    6347:       0f 8f b1 03 00 00       jg      945 <_kpdecode_cursor_next_record+0x920>
    634d:       3d 0c 00 08 25  cmpl    $621281292, %eax
    6352:       0f 84 ed 04 00 00       je      1261 <_kpdecode_cursor_next_record+0xa67>
    6358:       3d 04 00 0a 25  cmpl    $621412356, %eax
    635d:       0f 85 7e 02 00 00       jne     638 <_kpdecode_cursor_next_record+0x803>
    6363:       41 80 4d 01 10  orb     $16, 1(%r13)
    6368:       41 c7 85 90 09 00 00 00 00 00 00        movl    $0, 2448(%r13)
    6373:       49 8b 44 24 08  movq    8(%r12), %rax
    6378:       48 83 f8 ff     cmpq    $-1, %rax
    637c:       0f 84 dc 06 00 00       je      1756 <_kpdecode_cursor_next_record+0xc80>
    6382:       49 89 85 98 09 00 00    movq    %rax, 2456(%r13)
    6389:       31 c0   xorl    %eax, %eax
    638b:       e9 de 06 00 00  jmp     1758 <_kpdecode_cursor_next_record+0xc90>
    6390:       41 c7 87 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r15)
    639b:       49 83 c4 18     addq    $24, %r12
    639f:       ba 02 00 00 00  movl    $2, %edx
    63a4:       48 89 df        movq    %rbx, %rdi
    63a7:       4c 89 e6        movq    %r12, %rsi
    63aa:       4c 89 f9        movq    %r15, %rcx
    63ad:       e8 3e 08 00 00  callq   2110 <_batch_get_bytes>
    63b2:       e9 0d fd ff ff  jmp     -755 <_kpdecode_cursor_next_record+0x2e6>
    63b7:       3d 02 00 00 25  cmpl    $620756994, %eax
    63bc:       0f 84 bd 04 00 00       je      1213 <_kpdecode_cursor_next_record+0xaa1>
    63c2:       3d 04 00 01 25  cmpl    $620822532, %eax
    63c7:       0f 84 ce 04 00 00       je      1230 <_kpdecode_cursor_next_record+0xabd>
    63cd:       3d 1c 00 01 25  cmpl    $620822556, %eax
    63d2:       0f 85 09 02 00 00       jne     521 <_kpdecode_cursor_next_record+0x803>
    63d8:       ba 01 00 00 00  movl    $1, %edx
    63dd:       4c 89 e7        movq    %r12, %rdi
    63e0:       4c 89 ee        movq    %r13, %rsi
    63e3:       e8 f1 09 00 00  callq   2545 <_add_thread_info_sched_data>
    63e8:       e9 f4 01 00 00  jmp     500 <_kpdecode_cursor_next_record+0x803>
    63ed:       3d 10 00 02 25  cmpl    $620888080, %eax
    63f2:       0f 84 d1 04 00 00       je      1233 <_kpdecode_cursor_next_record+0xaeb>
    63f8:       3d 14 00 02 25  cmpl    $620888084, %eax
    63fd:       0f 84 ec 04 00 00       je      1260 <_kpdecode_cursor_next_record+0xb11>
    6403:       3d 18 00 02 25  cmpl    $620888088, %eax
    6408:       0f 85 d3 01 00 00       jne     467 <_kpdecode_cursor_next_record+0x803>
    640e:       49 8b 44 24 10  movq    16(%r12), %rax
    6413:       48 8d 48 ff     leaq    -1(%rax), %rcx
    6417:       48 81 f9 e7 03 00 00    cmpq    $999, %rcx
    641e:       77 20   ja      32 <_kpdecode_cursor_next_record+0x662>
    6420:       41 80 4d 00 80  orb     $-128, (%r13)
    6425:       41 8b 4c 24 08  movl    8(%r12), %ecx
    642a:       41 89 4d 68     movl    %ecx, 104(%r13)
    642e:       48 3d 80 00 00 00       cmpq    $128, %rax
    6434:       b9 80 00 00 00  movl    $128, %ecx
    6439:       0f 43 c1        cmovael %ecx, %eax
    643c:       41 89 45 6c     movl    %eax, 108(%r13)
    6440:       41 c7 85 b4 0b 00 00 00 00 00 00        movl    $0, 2996(%r13)
    644b:       e9 91 01 00 00  jmp     401 <_kpdecode_cursor_next_record+0x803>
    6450:       3d 3c 00 01 25  cmpl    $620822588, %eax
    6455:       0f 84 dc 04 00 00       je      1244 <_kpdecode_cursor_next_record+0xb59>
    645b:       3d 40 00 01 25  cmpl    $620822592, %eax
    6460:       0f 84 0b 05 00 00       je      1291 <_kpdecode_cursor_next_record+0xb93>
    6466:       3d 44 00 01 25  cmpl    $620822596, %eax
    646b:       0f 85 70 01 00 00       jne     368 <_kpdecode_cursor_next_record+0x803>
    6471:       41 80 4d 03 04  orb     $4, 3(%r13)
    6476:       41 0f 10 44 24 08       movups  8(%r12), %xmm0
    647c:       41 0f 11 85 88 0b 00 00         movups  %xmm0, 2952(%r13)
    6484:       e9 58 01 00 00  jmp     344 <_kpdecode_cursor_next_record+0x803>
    6489:       3d 24 00 06 25  cmpl    $621150244, %eax
    648e:       0f 84 e7 04 00 00       je      1255 <_kpdecode_cursor_next_record+0xb9d>
    6494:       3d 04 00 08 25  cmpl    $621281284, %eax
    6499:       0f 84 e6 04 00 00       je      1254 <_kpdecode_cursor_next_record+0xba7>
    649f:       3d 08 00 08 25  cmpl    $621281288, %eax
    64a4:       0f 85 37 01 00 00       jne     311 <_kpdecode_cursor_next_record+0x803>
    64aa:       41 80 4d 02 20  orb     $32, 2(%r13)
    64af:       49 8b 44 24 08  movq    8(%r12), %rax
    64b4:       48 c1 e0 20     shlq    $32, %rax
    64b8:       41 8b 4c 24 10  movl    16(%r12), %ecx
    64bd:       48 09 c1        orq     %rax, %rcx
    64c0:       49 89 8d d8 09 00 00    movq    %rcx, 2520(%r13)
    64c7:       41 8b 44 24 18  movl    24(%r12), %eax
    64cc:       41 89 85 e0 09 00 00    movl    %eax, 2528(%r13)
    64d3:       41 8b 44 24 20  movl    32(%r12), %eax
    64d8:       41 89 85 e4 09 00 00    movl    %eax, 2532(%r13)
    64df:       e9 fd 00 00 00  jmp     253 <_kpdecode_cursor_next_record+0x803>
    64e4:       48 83 c9 08     orq     $8, %rcx
    64e8:       49 89 0f        movq    %rcx, (%r15)
    64eb:       49 8b 44 24 28  movq    40(%r12), %rax
    64f0:       49 89 47 10     movq    %rax, 16(%r15)
    64f4:       45 89 77 18     movl    %r14d, 24(%r15)
    64f8:       4c 89 ff        movq    %r15, %rdi
    64fb:       48 83 c7 1c     addq    $28, %rdi
    64ff:       4c 89 e6        movq    %r12, %rsi
    6502:       48 83 c6 08     addq    $8, %rsi
    6506:       ba 14 00 00 00  movl    $20, %edx
    650b:       e8 26 13 00 00  callq   4902 <dyld_stub_binder+0x7836>
    6510:       41 c6 47 2f 00  movb    $0, 47(%r15)
    6515:       41 c7 87 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r15)
    6520:       41 8b 44 24 30  movl    48(%r12), %eax
    6525:       eb 32   jmp     50 <_kpdecode_cursor_next_record+0x77b>
    6527:       48 81 c9 00 40 00 00    orq     $16384, %rcx
    652e:       49 89 0f        movq    %rcx, (%r15)
    6531:       49 8b 44 24 08  movq    8(%r12), %rax
    6536:       49 89 87 20 0a 00 00    movq    %rax, 2592(%r15)
    653d:       41 8b 44 24 10  movl    16(%r12), %eax
    6542:       41 89 87 28 0a 00 00    movl    %eax, 2600(%r15)
    6549:       41 c7 87 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r15)
    6554:       b8 14 00 01 25  movl    $620822548, %eax
    6559:       89 c1   movl    %eax, %ecx
    655b:       c1 e9 18        shrl    $24, %ecx
    655e:       80 f9 21        cmpb    $33, %cl
    6561:       74 16   je      22 <_kpdecode_cursor_next_record+0x79b>
    6563:       80 f9 01        cmpb    $1, %cl
    6566:       74 11   je      17 <_kpdecode_cursor_next_record+0x79b>
    6568:       84 c9   testb   %cl, %cl
    656a:       75 75   jne     117 <_kpdecode_cursor_next_record+0x803>
    656c:       89 c1   movl    %eax, %ecx
    656e:       c1 e9 02        shrl    $2, %ecx
    6571:       81 e1 ff ff 3f 00       andl    $4194303, %ecx
    6577:       eb 1b   jmp     27 <_kpdecode_cursor_next_record+0x7b6>
    6579:       89 c1   movl    %eax, %ecx
    657b:       81 e1 00 00 ff 00       andl    $16711680, %ecx
    6581:       81 f9 00 00 0a 00       cmpl    $655360, %ecx
    6587:       75 58   jne     88 <_kpdecode_cursor_next_record+0x803>
    6589:       89 c1   movl    %eax, %ecx
    658b:       c1 e9 02        shrl    $2, %ecx
    658e:       81 e1 ff 3f 00 00       andl    $16383, %ecx
    6594:       41 80 4f 02 04  orb     $4, 2(%r15)
    6599:       41 8b 54 24 34  movl    52(%r12), %edx
    659e:       41 89 57 18     movl    %edx, 24(%r15)
    65a2:       41 89 8f 48 0a 00 00    movl    %ecx, 2632(%r15)
    65a9:       a8 01   testb   $1, %al
    65ab:       75 11   jne     17 <_kpdecode_cursor_next_record+0x7e0>
    65ad:       a8 02   testb   $2, %al
    65af:       75 1a   jne     26 <_kpdecode_cursor_next_record+0x7ed>
    65b1:       41 c7 87 4c 0a 00 00 02 00 00 00        movl    $2, 2636(%r15)
    65bc:       eb 18   jmp     24 <_kpdecode_cursor_next_record+0x7f8>
    65be:       41 c7 87 4c 0a 00 00 00 00 00 00        movl    $0, 2636(%r15)
    65c9:       eb 0b   jmp     11 <_kpdecode_cursor_next_record+0x7f8>
    65cb:       41 c7 87 4c 0a 00 00 01 00 00 00        movl    $1, 2636(%r15)
    65d6:       41 c7 87 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r15)
    65e1:       45 31 ed        xorl    %r13d, %r13d
    65e4:       49 83 3f 00     cmpq    $0, (%r15)
    65e8:       74 0b   je      11 <_kpdecode_cursor_next_record+0x817>
    65ea:       41 c7 87 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r15)
    65f5:       49 8b 07        movq    (%r15), %rax
    65f8:       48 85 c0        testq   %rax, %rax
    65fb:       74 54   je      84 <_kpdecode_cursor_next_record+0x873>
    65fd:       48 81 bb c8 04 00 00 ff 07 00 00        cmpq    $2047, 1224(%rbx)
    6608:       77 09   ja      9 <_kpdecode_cursor_next_record+0x835>
    660a:       48 0d 00 00 02 00       orq     $131072, %rax
    6610:       49 89 07        movq    %rax, (%r15)
    6613:       ff 83 c4 00 00 00       incl    196(%rbx)
    6619:       49 c7 87 a8 0b 00 00 00 00 00 00        movq    $0, 2984(%r15)
    6624:       48 8b 83 b8 00 00 00    movq    184(%rbx), %rax
    662b:       48 85 c0        testq   %rax, %rax
    662e:       74 07   je      7 <_kpdecode_cursor_next_record+0x859>
    6630:       4c 89 b8 a8 0b 00 00    movq    %r15, 2984(%rax)
    6637:       4c 89 bb b8 00 00 00    movq    %r15, 184(%rbx)
    663e:       48 83 bb b0 00 00 00 00         cmpq    $0, 176(%rbx)
    6646:       75 11   jne     17 <_kpdecode_cursor_next_record+0x87b>
    6648:       4c 89 bb b0 00 00 00    movq    %r15, 176(%rbx)
    664f:       eb 08   jmp     8 <_kpdecode_cursor_next_record+0x87b>
    6651:       4c 89 ff        movq    %r15, %rdi
    6654:       e8 5d f7 ff ff  callq   -2211 <_kpdecode_record_free>
    6659:       41 83 fd 02     cmpl    $2, %r13d
    665d:       0f 84 06 05 00 00       je      1286 <_kpdecode_cursor_next_record+0xd8b>
    6663:       41 83 fd 01     cmpl    $1, %r13d
    6667:       0f 85 86 f7 ff ff       jne     -2170 <_kpdecode_cursor_next_record+0x15>
    666d:       e9 99 04 00 00  jmp     1177 <_kpdecode_cursor_next_record+0xd2d>
    6672:       3d 34 00 01 25  cmpl    $620822580, %eax
    6677:       0f 84 46 03 00 00       je      838 <_kpdecode_cursor_next_record+0xbe5>
    667d:       3d 38 00 01 25  cmpl    $620822584, %eax
    6682:       0f 85 59 ff ff ff       jne     -167 <_kpdecode_cursor_next_record+0x803>
    6688:       41 80 4d 02 80  orb     $-128, 2(%r13)
    668d:       49 8b 44 24 08  movq    8(%r12), %rax
    6692:       48 c1 e0 20     shlq    $32, %rax
    6696:       41 8b 4c 24 10  movl    16(%r12), %ecx
    669b:       48 09 c1        orq     %rax, %rcx
    669e:       49 89 8d 10 0a 00 00    movq    %rcx, 2576(%r13)
    66a5:       e9 37 ff ff ff  jmp     -201 <_kpdecode_cursor_next_record+0x803>
    66aa:       3d 18 00 06 25  cmpl    $621150232, %eax
    66af:       0f 84 59 03 00 00       je      857 <_kpdecode_cursor_next_record+0xc30>
    66b5:       3d 20 00 06 25  cmpl    $621150240, %eax
    66ba:       0f 85 21 ff ff ff       jne     -223 <_kpdecode_cursor_next_record+0x803>
    66c0:       41 80 4d 01 02  orb     $2, 1(%r13)
    66c5:       e9 31 01 00 00  jmp     305 <_kpdecode_cursor_next_record+0xa1d>
    66ca:       3d 50 00 01 25  cmpl    $620822608, %eax
    66cf:       0f 84 4e 03 00 00       je      846 <_kpdecode_cursor_next_record+0xc45>
    66d5:       3d 0c 00 02 25  cmpl    $620888076, %eax
    66da:       0f 85 01 ff ff ff       jne     -255 <_kpdecode_cursor_next_record+0x803>
    66e0:       41 f6 45 00 40  testb   $64, (%r13)
    66e5:       0f 84 f6 fe ff ff       je      -266 <_kpdecode_cursor_next_record+0x803>
    66eb:       49 8d b5 70 04 00 00    leaq    1136(%r13), %rsi
    66f2:       49 81 c5 b0 0b 00 00    addq    $2992, %r13
    66f9:       e9 e1 01 00 00  jmp     481 <_kpdecode_cursor_next_record+0xb01>
    66fe:       3d 08 00 0a 25  cmpl    $621412360, %eax
    6703:       0f 84 2f 03 00 00       je      815 <_kpdecode_cursor_next_record+0xc5a>
    6709:       3d 00 00 99 25  cmpl    $630784000, %eax
    670e:       0f 85 cd fe ff ff       jne     -307 <_kpdecode_cursor_next_record+0x803>
    6714:       49 8b 85 38 0a 00 00    movq    2616(%r13), %rax
    671b:       48 85 c0        testq   %rax, %rax
    671e:       0f 84 5e 03 00 00       je      862 <_kpdecode_cursor_next_record+0xca4>
    6724:       45 8b b5 30 0a 00 00    movl    2608(%r13), %r14d
    672b:       41 8b 8d bc 0b 00 00    movl    3004(%r13), %ecx
    6732:       49 81 c5 bc 0b 00 00    addq    $3004, %r13
    6739:       4d 8d 54 24 08  leaq    8(%r12), %r10
    673e:       4d 8d 44 24 18  leaq    24(%r12), %r8
    6743:       4d 8d 4c 24 10  leaq    16(%r12), %r9
    6748:       49 83 c4 20     addq    $32, %r12
    674c:       31 f6   xorl    %esi, %esi
    674e:       44 39 f1        cmpl    %r14d, %ecx
    6751:       0f 8d 8a fe ff ff       jge     -374 <_kpdecode_cursor_next_record+0x803>
    6757:       49 89 db        movq    %rbx, %r11
    675a:       89 f3   movl    %esi, %ebx
    675c:       09 cb   orl     %ecx, %ebx
    675e:       74 48   je      72 <_kpdecode_cursor_next_record+0x9ca>
    6760:       89 f3   movl    %esi, %ebx
    6762:       81 e3 ff ff ff 7f       andl    $2147483647, %ebx
    6768:       83 fb 03        cmpl    $3, %ebx
    676b:       77 2e   ja      46 <_kpdecode_cursor_next_record+0x9bd>
    676d:       89 f7   movl    %esi, %edi
    676f:       81 e7 ff ff ff 7f       andl    $2147483647, %edi
    6775:       48 8d 1d 00 04 00 00    leaq    1024(%rip), %rbx
    677c:       48 89 da        movq    %rbx, %rdx
    677f:       48 63 1c bb     movslq  (%rbx,%rdi,4), %rbx
    6783:       48 01 d3        addq    %rdx, %rbx
    6786:       4c 89 d7        movq    %r10, %rdi
    6789:       ff e3   jmpq    *%rbx
    678b:       4c 89 cf        movq    %r9, %rdi
    678e:       eb 08   jmp     8 <_kpdecode_cursor_next_record+0x9ba>
    6790:       4c 89 c7        movq    %r8, %rdi
    6793:       eb 03   jmp     3 <_kpdecode_cursor_next_record+0x9ba>
    6795:       4c 89 e7        movq    %r12, %rdi
    6798:       48 8b 3f        movq    (%rdi), %rdi
    679b:       48 63 d9        movslq  %ecx, %rbx
    679e:       48 89 3c d8     movq    %rdi, (%rax,%rbx,8)
    67a2:       ff c1   incl    %ecx
    67a4:       41 89 4d 00     movl    %ecx, (%r13)
    67a8:       ff c6   incl    %esi
    67aa:       83 fe 04        cmpl    $4, %esi
    67ad:       4c 89 db        movq    %r11, %rbx
    67b0:       72 9c   jb      -100 <_kpdecode_cursor_next_record+0x970>
    67b2:       e9 2a fe ff ff  jmp     -470 <_kpdecode_cursor_next_record+0x803>
    67b7:       41 80 4d 02 40  orb     $64, 2(%r13)
    67bc:       49 8b 44 24 08  movq    8(%r12), %rax
    67c1:       0f b6 c8        movzbl  %al, %ecx
    67c4:       49 89 8d f8 09 00 00    movq    %rcx, 2552(%r13)
    67cb:       48 89 c1        movq    %rax, %rcx
    67ce:       48 c1 e9 08     shrq    $8, %rcx
    67d2:       66 41 89 8d 08 0a 00 00         movw    %cx, 2568(%r13)
    67da:       48 c1 e8 18     shrq    $24, %rax
    67de:       41 88 85 0a 0a 00 00    movb    %al, 2570(%r13)
    67e5:       49 8b 44 24 10  movq    16(%r12), %rax
    67ea:       49 89 85 00 0a 00 00    movq    %rax, 2560(%r13)
    67f1:       e9 eb fd ff ff  jmp     -533 <_kpdecode_cursor_next_record+0x803>
    67f6:       41 80 4d 01 04  orb     $4, 1(%r13)
    67fb:       4c 89 e7        movq    %r12, %rdi
    67fe:       4c 89 ee        movq    %r13, %rsi
    6801:       e8 96 04 00 00  callq   1174 <_add_pmc_data>
    6806:       e9 d6 fd ff ff  jmp     -554 <_kpdecode_cursor_next_record+0x803>
    680b:       41 80 4d 03 04  orb     $4, 3(%r13)
    6810:       49 8b 44 24 08  movq    8(%r12), %rax
    6815:       48 c1 e0 20     shlq    $32, %rax
    6819:       41 8b 4c 24 10  movl    16(%r12), %ecx
    681e:       48 09 c1        orq     %rax, %rcx
    6821:       49 89 8d 88 0b 00 00    movq    %rcx, 2952(%r13)
    6828:       49 8b 44 24 18  movq    24(%r12), %rax
    682d:       48 c1 e0 20     shlq    $32, %rax
    6831:       41 8b 4c 24 20  movl    32(%r12), %ecx
    6836:       48 09 c1        orq     %rax, %rcx
    6839:       49 89 8d 90 0b 00 00    movq    %rcx, 2960(%r13)
    6840:       e9 9c fd ff ff  jmp     -612 <_kpdecode_cursor_next_record+0x803>
    6845:       41 80 4d 02 20  orb     $32, 2(%r13)
    684a:       49 8b 44 24 08  movq    8(%r12), %rax
    684f:       48 c1 e0 20     shlq    $32, %rax
    6853:       41 8b 4c 24 10  movl    16(%r12), %ecx
    6858:       48 09 c1        orq     %rax, %rcx
    685b:       49 89 8d e8 09 00 00    movq    %rcx, 2536(%r13)
    6862:       49 8b 44 24 18  movq    24(%r12), %rax
    6867:       48 c1 e0 20     shlq    $32, %rax
    686b:       41 8b 4c 24 20  movl    32(%r12), %ecx
    6870:       48 09 c1        orq     %rax, %rcx
    6873:       49 89 8d f0 09 00 00    movq    %rcx, 2544(%r13)
    687a:       e9 62 fd ff ff  jmp     -670 <_kpdecode_cursor_next_record+0x803>
    687f:       41 c7 85 a0 0b 00 00 01 00 00 00        movl    $1, 2976(%r13)
    688a:       4a c7 84 f3 c8 00 00 00 00 00 00 00     movq    $0, 200(%rbx,%r14,8)
    6896:       e9 46 fd ff ff  jmp     -698 <_kpdecode_cursor_next_record+0x803>
    689b:       41 80 4d 00 20  orb     $32, (%r13)
    68a0:       41 8b 44 24 08  movl    8(%r12), %eax
    68a5:       41 89 45 58     movl    %eax, 88(%r13)
    68a9:       49 8b 44 24 10  movq    16(%r12), %rax
    68ae:       49 89 45 10     movq    %rax, 16(%r13)
    68b2:       49 8b 44 24 18  movq    24(%r12), %rax
    68b7:       49 89 45 60     movq    %rax, 96(%r13)
    68bb:       41 8b 44 24 20  movl    32(%r12), %eax
    68c0:       41 89 45 5c     movl    %eax, 92(%r13)
    68c4:       e9 18 fd ff ff  jmp     -744 <_kpdecode_cursor_next_record+0x803>
    68c9:       41 80 7d 00 00  cmpb    $0, (%r13)
    68ce:       0f 89 0d fd ff ff       jns     -755 <_kpdecode_cursor_next_record+0x803>
    68d4:       49 8d 75 68     leaq    104(%r13), %rsi
    68d8:       49 81 c5 b4 0b 00 00    addq    $2996, %r13
    68df:       4c 89 e7        movq    %r12, %rdi
    68e2:       4c 89 ea        movq    %r13, %rdx
    68e5:       e8 f0 06 00 00  callq   1776 <_add_stack_data>
    68ea:       e9 f2 fc ff ff  jmp     -782 <_kpdecode_cursor_next_record+0x803>
    68ef:       49 8b 44 24 10  movq    16(%r12), %rax
    68f4:       48 8d 48 ff     leaq    -1(%rax), %rcx
    68f8:       48 81 f9 e7 03 00 00    cmpq    $999, %rcx
    68ff:       77 26   ja      38 <_kpdecode_cursor_next_record+0xb49>
    6901:       41 80 4d 00 40  orb     $64, (%r13)
    6906:       41 8b 4c 24 08  movl    8(%r12), %ecx
    690b:       41 89 8d 70 04 00 00    movl    %ecx, 1136(%r13)
    6912:       48 3d 80 00 00 00       cmpq    $128, %rax
    6918:       b9 80 00 00 00  movl    $128, %ecx
    691d:       0f 43 c1        cmovael %ecx, %eax
    6920:       41 89 85 74 04 00 00    movl    %eax, 1140(%r13)
    6927:       41 c7 85 b0 0b 00 00 00 00 00 00        movl    $0, 2992(%r13)
    6932:       e9 aa fc ff ff  jmp     -854 <_kpdecode_cursor_next_record+0x803>
    6937:       41 80 4d 02 10  orb     $16, 2(%r13)
    693c:       49 8b 44 24 08  movq    8(%r12), %rax
    6941:       48 c1 e0 20     shlq    $32, %rax
    6945:       41 8b 4c 24 10  movl    16(%r12), %ecx
    694a:       48 09 c1        orq     %rax, %rcx
    694d:       49 89 8d b8 09 00 00    movq    %rcx, 2488(%r13)
    6954:       49 8b 44 24 18  movq    24(%r12), %rax
    6959:       48 c1 e0 20     shlq    $32, %rax
    695d:       41 8b 4c 24 20  movl    32(%r12), %ecx
    6962:       48 09 c1        orq     %rax, %rcx
    6965:       49 89 8d c0 09 00 00    movq    %rcx, 2496(%r13)
    696c:       e9 70 fc ff ff  jmp     -912 <_kpdecode_cursor_next_record+0x803>
    6971:       ba 01 00 00 00  movl    $1, %edx
    6976:       e9 ad 00 00 00  jmp     173 <_kpdecode_cursor_next_record+0xc4a>
    697b:       41 80 4d 01 02  orb     $2, 1(%r13)
    6980:       e9 8e 00 00 00  jmp     142 <_kpdecode_cursor_next_record+0xc35>
    6985:       41 80 4d 02 20  orb     $32, 2(%r13)
    698a:       49 8b 44 24 08  movq    8(%r12), %rax
    698f:       49 89 85 d8 09 00 00    movq    %rax, 2520(%r13)
    6996:       49 8b 44 24 10  movq    16(%r12), %rax
    699b:       48 89 c1        movq    %rax, %rcx
    699e:       48 c1 e9 20     shrq    $32, %rcx
    69a2:       41 89 8d e0 09 00 00    movl    %ecx, 2528(%r13)
    69a9:       41 89 85 e4 09 00 00    movl    %eax, 2532(%r13)
    69b0:       41 0f 10 44 24 18       movups  24(%r12), %xmm0
    69b6:       41 0f 11 85 e8 09 00 00         movups  %xmm0, 2536(%r13)
    69be:       e9 1e fc ff ff  jmp     -994 <_kpdecode_cursor_next_record+0x803>
    69c3:       41 80 4d 02 40  orb     $64, 2(%r13)
    69c8:       49 8b 44 24 08  movq    8(%r12), %rax
    69cd:       0f b6 c8        movzbl  %al, %ecx
    69d0:       49 89 8d f8 09 00 00    movq    %rcx, 2552(%r13)
    69d7:       48 89 c1        movq    %rax, %rcx
    69da:       48 c1 e9 08     shrq    $8, %rcx
    69de:       66 41 89 8d 08 0a 00 00         movw    %cx, 2568(%r13)
    69e6:       48 c1 e8 18     shrq    $24, %rax
    69ea:       41 88 85 0a 0a 00 00    movb    %al, 2570(%r13)
    69f1:       49 8b 44 24 10  movq    16(%r12), %rax
    69f6:       48 c1 e0 20     shlq    $32, %rax
    69fa:       41 8b 4c 24 18  movl    24(%r12), %ecx
    69ff:       48 09 c1        orq     %rax, %rcx
    6a02:       49 89 8d 00 0a 00 00    movq    %rcx, 2560(%r13)
    6a09:       e9 d3 fb ff ff  jmp     -1069 <_kpdecode_cursor_next_record+0x803>
    6a0e:       41 80 4d 01 04  orb     $4, 1(%r13)
    6a13:       4c 89 e7        movq    %r12, %rdi
    6a16:       4c 89 ee        movq    %r13, %rsi
    6a19:       e8 57 03 00 00  callq   855 <_add_pmc_data32>
    6a1e:       e9 be fb ff ff  jmp     -1090 <_kpdecode_cursor_next_record+0x803>
    6a23:       ba 02 00 00 00  movl    $2, %edx
    6a28:       4c 89 e7        movq    %r12, %rdi
    6a2b:       4c 89 ee        movq    %r13, %rsi
    6a2e:       e8 b0 04 00 00  callq   1200 <_add_thread_info_sched_data2_32>
    6a33:       e9 a9 fb ff ff  jmp     -1111 <_kpdecode_cursor_next_record+0x803>
    6a38:       41 80 4d 03 02  orb     $2, 3(%r13)
    6a3d:       41 0f 10 44 24 08       movups  8(%r12), %xmm0
    6a43:       41 0f 11 85 68 0b 00 00         movups  %xmm0, 2920(%r13)
    6a4b:       41 0f 10 44 24 18       movups  24(%r12), %xmm0
    6a51:       41 0f 11 85 78 0b 00 00         movups  %xmm0, 2936(%r13)
    6a59:       e9 83 fb ff ff  jmp     -1149 <_kpdecode_cursor_next_record+0x803>
    6a5e:       41 c7 85 90 09 00 00 01 00 00 00        movl    $1, 2448(%r13)
    6a69:       b8 01 00 00 00  movl    $1, %eax
    6a6e:       49 8b 4c 24 10  movq    16(%r12), %rcx
    6a73:       48 83 f9 ff     cmpq    $-1, %rcx
    6a77:       74 62   je      98 <_kpdecode_cursor_next_record+0xcfd>
    6a79:       49 89 8d a0 09 00 00    movq    %rcx, 2464(%r13)
    6a80:       eb 63   jmp     99 <_kpdecode_cursor_next_record+0xd07>
    6a82:       41 83 bd bc 0b 00 00 ff         cmpl    $-1, 3004(%r13)
    6a8a:       0f 85 51 fb ff ff       jne     -1199 <_kpdecode_cursor_next_record+0x803>
    6a90:       4d 8b 74 24 08  movq    8(%r12), %r14
    6a95:       45 89 b5 30 0a 00 00    movl    %r14d, 2608(%r13)
    6a9c:       49 63 fe        movslq  %r14d, %rdi
    6a9f:       48 c1 e7 03     shlq    $3, %rdi
    6aa3:       e8 46 0d 00 00  callq   3398 <dyld_stub_binder+0x77ee>
    6aa8:       49 89 85 38 0a 00 00    movq    %rax, 2616(%r13)
    6aaf:       41 c7 85 bc 0b 00 00 00 00 00 00        movl    $0, 3004(%r13)
    6aba:       48 85 c0        testq   %rax, %rax
    6abd:       0f 84 1e fb ff ff       je      -1250 <_kpdecode_cursor_next_record+0x803>
    6ac3:       41 80 4d 01 80  orb     $-128, 1(%r13)
    6ac8:       4d 8d 54 24 08  leaq    8(%r12), %r10
    6acd:       49 81 c5 bc 0b 00 00    addq    $3004, %r13
    6ad4:       31 c9   xorl    %ecx, %ecx
    6ad6:       e9 63 fc ff ff  jmp     -925 <_kpdecode_cursor_next_record+0x960>
    6adb:       83 c8 02        orl     $2, %eax
    6ade:       41 89 85 90 09 00 00    movl    %eax, 2448(%r13)
    6ae5:       49 8b 4c 24 18  movq    24(%r12), %rcx
    6aea:       48 83 f9 ff     cmpq    $-1, %rcx
    6aee:       74 0c   je      12 <_kpdecode_cursor_next_record+0xd1e>
    6af0:       49 89 8d a8 09 00 00    movq    %rcx, 2472(%r13)
    6af7:       e9 e5 fa ff ff  jmp     -1307 <_kpdecode_cursor_next_record+0x803>
    6afc:       83 c8 04        orl     $4, %eax
    6aff:       41 89 85 90 09 00 00    movl    %eax, 2448(%r13)
    6b06:       e9 d6 fa ff ff  jmp     -1322 <_kpdecode_cursor_next_record+0x803>
    6b0b:       48 89 df        movq    %rbx, %rdi
    6b0e:       e8 79 00 00 00  callq   121 <_record_ready>
    6b13:       41 bd 01 00 00 00       movl    $1, %r13d
    6b19:       84 c0   testb   %al, %al
    6b1b:       74 4c   je      76 <_kpdecode_cursor_next_record+0xd8b>
    6b1d:       48 8b 83 b0 00 00 00    movq    176(%rbx), %rax
    6b24:       48 8b 4d d0     movq    -48(%rbp), %rcx
    6b28:       48 89 01        movq    %rax, (%rcx)
    6b2b:       ff 8b c4 00 00 00       decl    196(%rbx)
    6b31:       48 8b 88 a8 0b 00 00    movq    2984(%rax), %rcx
    6b38:       48 89 8b b0 00 00 00    movq    %rcx, 176(%rbx)
    6b3f:       48 39 83 b8 00 00 00    cmpq    %rax, 184(%rbx)
    6b46:       75 0b   jne     11 <_kpdecode_cursor_next_record+0xd75>
    6b48:       48 c7 83 b8 00 00 00 00 00 00 00        movq    $0, 184(%rbx)
    6b53:       48 c7 80 a8 0b 00 00 00 00 00 00        movq    $0, 2984(%rax)
    6b5e:       45 31 ed        xorl    %r13d, %r13d
    6b61:       eb 06   jmp     6 <_kpdecode_cursor_next_record+0xd8b>
    6b63:       41 bd 02 00 00 00       movl    $2, %r13d
    6b69:       44 89 e8        movl    %r13d, %eax
    6b6c:       48 83 c4 08     addq    $8, %rsp
    6b70:       5b      popq    %rbx
    6b71:       41 5c   popq    %r12
    6b73:       41 5d   popq    %r13
    6b75:       41 5e   popq    %r14
    6b77:       41 5f   popq    %r15
    6b79:       5d      popq    %rbp
    6b7a:       c3      retq
    6b7b:       90      nop
    6b7c:       1c fc   sbbb    $-4, %al
    6b7e:       ff ff  <unknown>
    6b80:       0f fc ff        paddb   %mm7, %mm7
    6b83:       ff 14 fc        callq   *(%rsp,%rdi,8)
    6b86:       ff ff  <unknown>
    6b88:       19 fc   sbbl    %edi, %esp
    6b8a:       ff ff  <unknown>

_record_ready:
    6b8c:       55      pushq   %rbp
    6b8d:       48 89 e5        movq    %rsp, %rbp
    6b90:       83 7f 40 00     cmpl    $0, 64(%rdi)
    6b94:       74 56   je      86 <_record_ready+0x60>
    6b96:       48 8b 8f b0 00 00 00    movq    176(%rdi), %rcx
    6b9d:       48 85 c9        testq   %rcx, %rcx
    6ba0:       74 0b   je      11 <_record_ready+0x21>
    6ba2:       b0 01   movb    $1, %al
    6ba4:       83 b9 a0 0b 00 00 00    cmpl    $0, 2976(%rcx)
    6bab:       75 41   jne     65 <_record_ready+0x62>
    6bad:       81 bf c4 00 00 00 11 27 00 00   cmpl    $10001, 196(%rdi)
    6bb7:       7c 33   jl      51 <_record_ready+0x60>
    6bb9:       80 49 07 80     orb     $-128, 7(%rcx)
    6bbd:       c7 81 a0 0b 00 00 01 00 00 00   movl    $1, 2976(%rcx)
    6bc7:       48 63 41 18     movslq  24(%rcx), %rax
    6bcb:       31 c9   xorl    %ecx, %ecx
    6bcd:       48 89 8c c7 c8 00 00 00         movq    %rcx, 200(%rdi,%rax,8)
    6bd5:       48 8b 87 b0 00 00 00    movq    176(%rdi), %rax
    6bdc:       48 63 40 18     movslq  24(%rax), %rax
    6be0:       48 89 8c c7 c8 01 00 00         movq    %rcx, 456(%rdi,%rax,8)
    6be8:       b0 01   movb    $1, %al
    6bea:       eb 02   jmp     2 <_record_ready+0x62>
    6bec:       31 c0   xorl    %eax, %eax
    6bee:       5d      popq    %rbp
    6bef:       c3      retq

_batch_get_bytes:
    6bf0:       55      pushq   %rbp
    6bf1:       48 89 e5        movq    %rsp, %rbp
    6bf4:       41 56   pushq   %r14
    6bf6:       53      pushq   %rbx
    6bf7:       8b 07   movl    (%rdi), %eax
    6bf9:       31 ff   xorl    %edi, %edi
    6bfb:       83 f8 02        cmpl    $2, %eax
    6bfe:       40 0f 94 c7     sete    %dil
    6c02:       48 c1 e7 03     shlq    $3, %rdi
    6c06:       83 f8 01        cmpl    $1, %eax
    6c09:       41 bb 04 00 00 00       movl    $4, %r11d
    6c0f:       4c 0f 45 df     cmovneq %rdi, %r11
    6c13:       48 85 d2        testq   %rdx, %rdx
    6c16:       74 7f   je      127 <_batch_get_bytes+0xa7>
    6c18:       4c 8d 81 50 0a 00 00    leaq    2640(%rcx), %r8
    6c1f:       45 31 c9        xorl    %r9d, %r9d
    6c22:       4a 8b 04 ce     movq    (%rsi,%r9,8), %rax
    6c26:       48 89 45 e8     movq    %rax, -24(%rbp)
    6c2a:       4c 8b 91 50 0b 00 00    movq    2896(%rcx), %r10
    6c31:       4d 85 db        testq   %r11, %r11
    6c34:       74 31   je      49 <_batch_get_bytes+0x77>
    6c36:       4f 8d 34 10     leaq    (%r8,%r10), %r14
    6c3a:       49 8d 5a 01     leaq    1(%r10), %rbx
    6c3e:       31 ff   xorl    %edi, %edi
    6c40:       48 8d 04 3b     leaq    (%rbx,%rdi), %rax
    6c44:       48 3d 00 01 00 00       cmpq    $256, %rax
    6c4a:       73 2f   jae     47 <_batch_get_bytes+0x8b>
    6c4c:       8a 44 3d e8     movb    -24(%rbp,%rdi), %al
    6c50:       41 88 04 3e     movb    %al, (%r14,%rdi)
    6c54:       84 c0   testb   %al, %al
    6c56:       74 38   je      56 <_batch_get_bytes+0xa0>
    6c58:       48 ff c7        incq    %rdi
    6c5b:       4c 39 df        cmpq    %r11, %rdi
    6c5e:       72 e0   jb      -32 <_batch_get_bytes+0x50>
    6c60:       4c 8b 91 50 0b 00 00    movq    2896(%rcx), %r10
    6c67:       4d 01 da        addq    %r11, %r10
    6c6a:       4c 89 91 50 0b 00 00    movq    %r10, 2896(%rcx)
    6c71:       49 ff c1        incq    %r9
    6c74:       49 39 d1        cmpq    %rdx, %r9
    6c77:       72 a9   jb      -87 <_batch_get_bytes+0x32>
    6c79:       eb 1c   jmp     28 <_batch_get_bytes+0xa7>
    6c7b:       48 01 b9 50 0b 00 00    addq    %rdi, 2896(%rcx)
    6c82:       49 01 ca        addq    %rcx, %r10
    6c85:       42 c6 84 17 50 0a 00 00 00      movb    $0, 2640(%rdi,%r10)
    6c8e:       eb 07   jmp     7 <_batch_get_bytes+0xa7>
    6c90:       48 01 b9 50 0b 00 00    addq    %rdi, 2896(%rcx)
    6c97:       5b      popq    %rbx
    6c98:       41 5e   popq    %r14
    6c9a:       5d      popq    %rbp
    6c9b:       c3      retq

_add_pmc_data:
    6c9c:       55      pushq   %rbp
    6c9d:       48 89 e5        movq    %rsp, %rbp
    6ca0:       83 be 84 09 00 00 00    cmpl    $0, 2436(%rsi)
    6ca7:       74 3c   je      60 <_add_pmc_data+0x49>
    6ca9:       48 8b 47 08     movq    8(%rdi), %rax
    6cad:       48 63 8e b8 0b 00 00    movslq  3000(%rsi), %rcx
    6cb4:       48 89 84 ce 80 08 00 00         movq    %rax, 2176(%rsi,%rcx,8)
    6cbc:       48 8b 47 10     movq    16(%rdi), %rax
    6cc0:       48 89 84 ce 88 08 00 00         movq    %rax, 2184(%rsi,%rcx,8)
    6cc8:       48 8b 47 18     movq    24(%rdi), %rax
    6ccc:       48 89 84 ce 90 08 00 00         movq    %rax, 2192(%rsi,%rcx,8)
    6cd4:       48 8b 47 20     movq    32(%rdi), %rax
    6cd8:       48 89 84 ce 98 08 00 00         movq    %rax, 2200(%rsi,%rcx,8)
    6ce0:       8d 41 04        leal    4(%rcx), %eax
    6ce3:       eb 3f   jmp     63 <_add_pmc_data+0x88>
    6ce5:       48 63 86 b8 0b 00 00    movslq  3000(%rsi), %rax
    6cec:       48 8b 4f 08     movq    8(%rdi), %rcx
    6cf0:       48 85 c0        testq   %rax, %rax
    6cf3:       74 48   je      72 <_add_pmc_data+0xa1>
    6cf5:       48 89 8c c6 80 08 00 00         movq    %rcx, 2176(%rsi,%rax,8)
    6cfd:       48 8b 4f 10     movq    16(%rdi), %rcx
    6d01:       48 89 8c c6 88 08 00 00         movq    %rcx, 2184(%rsi,%rax,8)
    6d09:       48 8b 4f 18     movq    24(%rdi), %rcx
    6d0d:       48 89 8c c6 90 08 00 00         movq    %rcx, 2192(%rsi,%rax,8)
    6d15:       48 8b 4f 20     movq    32(%rdi), %rcx
    6d19:       48 89 8c c6 98 08 00 00         movq    %rcx, 2200(%rsi,%rax,8)
    6d21:       8d 40 04        leal    4(%rax), %eax
    6d24:       89 86 b8 0b 00 00       movl    %eax, 3000(%rsi)
    6d2a:       8b 8e 88 09 00 00       movl    2440(%rsi), %ecx
    6d30:       39 c8   cmpl    %ecx, %eax
    6d32:       0f 42 c8        cmovbl  %eax, %ecx
    6d35:       89 8e 78 08 00 00       movl    %ecx, 2168(%rsi)
    6d3b:       5d      popq    %rbp
    6d3c:       c3      retq
    6d3d:       89 8e 78 08 00 00       movl    %ecx, 2168(%rsi)
    6d43:       48 8b 47 10     movq    16(%rdi), %rax
    6d47:       48 89 86 80 08 00 00    movq    %rax, 2176(%rsi)
    6d4e:       48 8b 47 18     movq    24(%rdi), %rax
    6d52:       48 89 86 88 08 00 00    movq    %rax, 2184(%rsi)
    6d59:       48 8b 47 20     movq    32(%rdi), %rax
    6d5d:       48 89 86 90 08 00 00    movq    %rax, 2192(%rsi)
    6d64:       c7 86 b8 0b 00 00 03 00 00 00   movl    $3, 3000(%rsi)
    6d6e:       b8 03 00 00 00  movl    $3, %eax
    6d73:       eb b5   jmp     -75 <_add_pmc_data+0x8e>

_add_pmc_data32:
    6d75:       55      pushq   %rbp
    6d76:       48 89 e5        movq    %rsp, %rbp
    6d79:       48 8b 47 08     movq    8(%rdi), %rax
    6d7d:       48 c1 e0 20     shlq    $32, %rax
    6d81:       8b 4f 10        movl    16(%rdi), %ecx
    6d84:       48 09 c1        orq     %rax, %rcx
    6d87:       48 8b 47 18     movq    24(%rdi), %rax
    6d8b:       48 c1 e0 20     shlq    $32, %rax
    6d8f:       8b 57 20        movl    32(%rdi), %edx
    6d92:       48 09 c2        orq     %rax, %rdx
    6d95:       48 63 86 b8 0b 00 00    movslq  3000(%rsi), %rax
    6d9c:       48 89 8c c6 80 08 00 00         movq    %rcx, 2176(%rsi,%rax,8)
    6da4:       48 89 94 c6 88 08 00 00         movq    %rdx, 2184(%rsi,%rax,8)
    6dac:       8d 40 02        leal    2(%rax), %eax
    6daf:       89 86 b8 0b 00 00       movl    %eax, 3000(%rsi)
    6db5:       8b 8e 88 09 00 00       movl    2440(%rsi), %ecx
    6dbb:       39 c8   cmpl    %ecx, %eax
    6dbd:       73 08   jae     8 <_add_pmc_data32+0x52>
    6dbf:       89 86 78 08 00 00       movl    %eax, 2168(%rsi)
    6dc5:       eb 10   jmp     16 <_add_pmc_data32+0x62>
    6dc7:       89 8e 78 08 00 00       movl    %ecx, 2168(%rsi)
    6dcd:       c7 86 b8 0b 00 00 00 00 00 00   movl    $0, 3000(%rsi)
    6dd7:       5d      popq    %rbp
    6dd8:       c3      retq

_add_thread_info_sched_data:
    6dd9:       55      pushq   %rbp
    6dda:       48 89 e5        movq    %rsp, %rbp
    6ddd:       4c 8b 06        movq    (%rsi), %r8
    6de0:       4c 89 c1        movq    %r8, %rcx
    6de3:       48 81 c9 00 00 10 00    orq     $1048576, %rcx
    6dea:       48 89 0e        movq    %rcx, (%rsi)
    6ded:       0f 10 47 08     movups  8(%rdi), %xmm0
    6df1:       0f 11 86 b8 09 00 00    movups  %xmm0, 2488(%rsi)
    6df8:       48 8b 47 18     movq    24(%rdi), %rax
    6dfc:       48 89 c1        movq    %rax, %rcx
    6dff:       48 c1 e9 30     shrq    $48, %rcx
    6e03:       66 89 8e cc 09 00 00    movw    %cx, 2508(%rsi)
    6e0a:       48 89 c1        movq    %rax, %rcx
    6e0d:       48 c1 e9 20     shrq    $32, %rcx
    6e11:       66 89 8e ce 09 00 00    movw    %cx, 2510(%rsi)
    6e18:       89 c1   movl    %eax, %ecx
    6e1a:       c1 e9 18        shrl    $24, %ecx
    6e1d:       89 8e c8 09 00 00       movl    %ecx, 2504(%rsi)
    6e23:       c1 e8 06        shrl    $6, %eax
    6e26:       83 e0 07        andl    $7, %eax
    6e29:       8b 8e d0 09 00 00       movl    2512(%rsi), %ecx
    6e2f:       83 e1 f8        andl    $-8, %ecx
    6e32:       09 c1   orl     %eax, %ecx
    6e34:       66 89 8e d0 09 00 00    movw    %cx, 2512(%rsi)
    6e3b:       0f b7 47 18     movzwl  24(%rdi), %eax
    6e3f:       83 e0 38        andl    $56, %eax
    6e42:       83 e1 c7        andl    $-57, %ecx
    6e45:       09 c1   orl     %eax, %ecx
    6e47:       66 89 8e d0 09 00 00    movw    %cx, 2512(%rsi)
    6e4e:       8b 47 18        movl    24(%rdi), %eax
    6e51:       83 e0 07        andl    $7, %eax
    6e54:       c1 e0 06        shll    $6, %eax
    6e57:       81 e1 3f fe ff ff       andl    $4294966847, %ecx
    6e5d:       09 c1   orl     %eax, %ecx
    6e5f:       66 89 8e d0 09 00 00    movw    %cx, 2512(%rsi)
    6e66:       48 8b 47 20     movq    32(%rdi), %rax
    6e6a:       48 c1 e8 34     shrq    $52, %rax
    6e6e:       25 00 0e 00 00  andl    $3584, %eax
    6e73:       81 e1 ff f1 ff ff       andl    $4294963711, %ecx
    6e79:       09 c1   orl     %eax, %ecx
    6e7b:       66 89 8e d0 09 00 00    movw    %cx, 2512(%rsi)
    6e82:       83 fa 02        cmpl    $2, %edx
    6e85:       7c 5a   jl      90 <_add_thread_info_sched_data+0x108>
    6e87:       49 81 c8 00 00 10 08    orq     $135266304, %r8
    6e8e:       4c 89 06        movq    %r8, (%rsi)
    6e91:       48 8b 47 20     movq    32(%rdi), %rax
    6e95:       48 c1 e8 3a     shrq    $58, %rax
    6e99:       83 e0 07        andl    $7, %eax
    6e9c:       8b 8e 98 0b 00 00       movl    2968(%rsi), %ecx
    6ea2:       83 e1 f8        andl    $-8, %ecx
    6ea5:       09 c1   orl     %eax, %ecx
    6ea7:       66 89 8e 98 0b 00 00    movw    %cx, 2968(%rsi)
    6eae:       48 8b 47 20     movq    32(%rdi), %rax
    6eb2:       48 c1 e8 34     shrq    $52, %rax
    6eb6:       83 e0 38        andl    $56, %eax
    6eb9:       83 e1 c7        andl    $-57, %ecx
    6ebc:       09 c1   orl     %eax, %ecx
    6ebe:       66 89 8e 98 0b 00 00    movw    %cx, 2968(%rsi)
    6ec5:       48 8b 47 20     movq    32(%rdi), %rax
    6ec9:       48 c1 e8 2e     shrq    $46, %rax
    6ecd:       25 c0 01 00 00  andl    $448, %eax
    6ed2:       81 e1 3f fe ff ff       andl    $4294966847, %ecx
    6ed8:       09 c1   orl     %eax, %ecx
    6eda:       66 89 8e 98 0b 00 00    movw    %cx, 2968(%rsi)
    6ee1:       5d      popq    %rbp
    6ee2:       c3      retq

_add_thread_info_sched_data2_32:
    6ee3:       55      pushq   %rbp
    6ee4:       48 89 e5        movq    %rsp, %rbp
    6ee7:       4c 8b 06        movq    (%rsi), %r8
    6eea:       4c 89 c1        movq    %r8, %rcx
    6eed:       48 81 c9 00 00 10 00    orq     $1048576, %rcx
    6ef4:       48 89 0e        movq    %rcx, (%rsi)
    6ef7:       48 8b 47 08     movq    8(%rdi), %rax
    6efb:       48 89 c1        movq    %rax, %rcx
    6efe:       48 c1 e9 10     shrq    $16, %rcx
    6f02:       66 89 8e cc 09 00 00    movw    %cx, 2508(%rsi)
    6f09:       66 89 86 ce 09 00 00    movw    %ax, 2510(%rsi)
    6f10:       8b 47 10        movl    16(%rdi), %eax
    6f13:       89 c1   movl    %eax, %ecx
    6f15:       c1 e9 18        shrl    $24, %ecx
    6f18:       89 8e c8 09 00 00       movl    %ecx, 2504(%rsi)
    6f1e:       c1 e8 06        shrl    $6, %eax
    6f21:       83 e0 07        andl    $7, %eax
    6f24:       8b 8e d0 09 00 00       movl    2512(%rsi), %ecx
    6f2a:       83 e1 f8        andl    $-8, %ecx
    6f2d:       09 c1   orl     %eax, %ecx
    6f2f:       66 89 8e d0 09 00 00    movw    %cx, 2512(%rsi)
    6f36:       0f b7 47 10     movzwl  16(%rdi), %eax
    6f3a:       83 e0 38        andl    $56, %eax
    6f3d:       83 e1 c7        andl    $-57, %ecx
    6f40:       09 c1   orl     %eax, %ecx
    6f42:       66 89 8e d0 09 00 00    movw    %cx, 2512(%rsi)
    6f49:       8b 47 10        movl    16(%rdi), %eax
    6f4c:       83 e0 07        andl    $7, %eax
    6f4f:       c1 e0 06        shll    $6, %eax
    6f52:       81 e1 3f fe ff ff       andl    $4294966847, %ecx
    6f58:       09 c1   orl     %eax, %ecx
    6f5a:       66 89 8e d0 09 00 00    movw    %cx, 2512(%rsi)
    6f61:       48 8b 47 18     movq    24(%rdi), %rax
    6f65:       c1 e8 14        shrl    $20, %eax
    6f68:       25 00 0e 00 00  andl    $3584, %eax
    6f6d:       81 e1 ff f1 ff ff       andl    $4294963711, %ecx
    6f73:       09 c1   orl     %eax, %ecx
    6f75:       66 89 8e d0 09 00 00    movw    %cx, 2512(%rsi)
    6f7c:       83 fa 02        cmpl    $2, %edx
    6f7f:       7c 57   jl      87 <_add_thread_info_sched_data2_32+0xf5>
    6f81:       49 81 c8 00 00 10 08    orq     $135266304, %r8
    6f88:       4c 89 06        movq    %r8, (%rsi)
    6f8b:       48 8b 47 18     movq    24(%rdi), %rax
    6f8f:       c1 e8 1a        shrl    $26, %eax
    6f92:       83 e0 07        andl    $7, %eax
    6f95:       8b 8e 98 0b 00 00       movl    2968(%rsi), %ecx
    6f9b:       83 e1 f8        andl    $-8, %ecx
    6f9e:       09 c1   orl     %eax, %ecx
    6fa0:       66 89 8e 98 0b 00 00    movw    %cx, 2968(%rsi)
    6fa7:       48 8b 47 18     movq    24(%rdi), %rax
    6fab:       c1 e8 14        shrl    $20, %eax
    6fae:       83 e0 38        andl    $56, %eax
    6fb1:       83 e1 c7        andl    $-57, %ecx
    6fb4:       09 c1   orl     %eax, %ecx
    6fb6:       66 89 8e 98 0b 00 00    movw    %cx, 2968(%rsi)
    6fbd:       48 8b 47 18     movq    24(%rdi), %rax
    6fc1:       c1 e8 0e        shrl    $14, %eax
    6fc4:       25 c0 01 00 00  andl    $448, %eax
    6fc9:       81 e1 3f fe ff ff       andl    $4294966847, %ecx
    6fcf:       09 c1   orl     %eax, %ecx
    6fd1:       66 89 8e 98 0b 00 00    movw    %cx, 2968(%rsi)
    6fd8:       5d      popq    %rbp
    6fd9:       c3      retq

_add_stack_data:
    6fda:       55      pushq   %rbp
    6fdb:       48 89 e5        movq    %rsp, %rbp
    6fde:       48 63 02        movslq  (%rdx), %rax
    6fe1:       48 83 f8 7c     cmpq    $124, %rax
    6fe5:       7f 29   jg      41 <_add_stack_data+0x36>
    6fe7:       48 8b 4f 08     movq    8(%rdi), %rcx
    6feb:       48 89 4c c6 08  movq    %rcx, 8(%rsi,%rax,8)
    6ff0:       48 8b 4f 10     movq    16(%rdi), %rcx
    6ff4:       48 89 4c c6 10  movq    %rcx, 16(%rsi,%rax,8)
    6ff9:       48 8b 4f 18     movq    24(%rdi), %rcx
    6ffd:       48 89 4c c6 18  movq    %rcx, 24(%rsi,%rax,8)
    7002:       48 8b 4f 20     movq    32(%rdi), %rcx
    7006:       48 89 4c c6 20  movq    %rcx, 32(%rsi,%rax,8)
    700b:       8d 40 04        leal    4(%rax), %eax
    700e:       89 02   movl    %eax, (%rdx)
    7010:       5d      popq    %rbp
    7011:       c3      retq

_misc:
    9999:       cc      EOE
    8888:       c3      retq
    77b2:       cc      ; calloc
    77ee:       cc      ; malloc

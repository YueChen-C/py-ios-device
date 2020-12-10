
# region operations
AFC_OP_STATUS          = 0x00000001
AFC_OP_DATA            = 0x00000002     # Data */
AFC_OP_READ_DIR        = 0x00000003     # ReadDir */
AFC_OP_READ_FILE       = 0x00000004     # ReadFile */
AFC_OP_WRITE_FILE      = 0x00000005     # WriteFile */
AFC_OP_WRITE_PART      = 0x00000006     # WritePart */
AFC_OP_TRUNCATE        = 0x00000007     # TruncateFile */
AFC_OP_REMOVE_PATH     = 0x00000008     # RemovePath */
AFC_OP_MAKE_DIR        = 0x00000009     # MakeDir */
AFC_OP_GET_FILE_INFO   = 0x0000000a     # GetFileInfo */
AFC_OP_GET_DEVINFO     = 0x0000000b     # GetDeviceInfo */
AFC_OP_WRITE_FILE_ATOM = 0x0000000c     # WriteFileAtomic (tmp file+rename) */
AFC_OP_FILE_OPEN       = 0x0000000d     # FileRefOpen */
AFC_OP_FILE_OPEN_RES   = 0x0000000e     # FileRefOpenResult */
AFC_OP_READ            = 0x0000000f     # FileRefRead */
AFC_OP_WRITE           = 0x00000010     # FileRefWrite */
AFC_OP_FILE_SEEK       = 0x00000011     # FileRefSeek */
AFC_OP_FILE_TELL       = 0x00000012     # FileRefTell */
AFC_OP_FILE_TELL_RES   = 0x00000013     # FileRefTellResult */
AFC_OP_FILE_CLOSE      = 0x00000014     # FileRefClose */
AFC_OP_FILE_SET_SIZE   = 0x00000015     # FileRefSetFileSize (ftruncate) */
AFC_OP_GET_CON_INFO    = 0x00000016     # GetConnectionInfo */
AFC_OP_SET_CON_OPTIONS = 0x00000017     # SetConnectionOptions */
AFC_OP_RENAME_PATH     = 0x00000018     # RenamePath */
AFC_OP_SET_FS_BS       = 0x00000019     # SetFSBlockSize (0x800000) */
AFC_OP_SET_SOCKET_BS   = 0x0000001A     # SetSocketBlockSize (0x800000) */
AFC_OP_FILE_LOCK       = 0x0000001B     # FileRefLock */
AFC_OP_MAKE_LINK       = 0x0000001C     # MakeLink */
AFC_OP_GET_FILE_HASH   = 0x0000001D     # GetFileHash */
AFC_OP_SET_FILE_TIME   = 0x0000001E     # set st_mtime */
AFC_OP_GET_FILE_HASH_RANGE       = 0x0000001F   # GetFileHashWithRange */
# iOS 6+ */
AFC_OP_FILE_SET_IMMUTABLE_HINT   = 0x00000020	# FileRefSetImmutableHint */
AFC_OP_GET_SIZE_OF_PATH_CONTENTS = 0x00000021	# GetSizeOfPathContents */
AFC_OP_REMOVE_PATH_AND_CONTENTS  = 0x00000022	# RemovePathAndContents */
AFC_OP_DIR_OPEN                  = 0x00000023	# DirectoryEnumeratorRefOpen */
AFC_OP_DIR_OPEN_RESULT           = 0x00000024	# DirectoryEnumeratorRefOpenResult */
AFC_OP_DIR_READ                  = 0x00000025	# DirectoryEnumeratorRefRead */
AFC_OP_DIR_CLOSE                 = 0x00000026	# DirectoryEnumeratorRefClose */
# iOS 7+ */
AFC_OP_FILE_READ_OFFSET          = 0x00000027	# FileRefReadWithOffset */
AFC_OP_FILE_WRITE_OFFSET         = 0x00000028	# FileRefWriteWithOffset */
# endregion

# region error codes
AFC_E_SUCCESS                = 0
AFC_E_UNKNOWN_ERROR          = 1
AFC_E_OP_HEADER_INVALID      = 2
AFC_E_NO_RESOURCES           = 3
AFC_E_READ_ERROR             = 4
AFC_E_WRITE_ERROR            = 5
AFC_E_UNKNOWN_PACKET_TYPE    = 6
AFC_E_INVALID_ARG            = 7
AFC_E_OBJECT_NOT_FOUND       = 8
AFC_E_OBJECT_IS_DIR          = 9
AFC_E_PERM_DENIED            = 10
AFC_E_SERVICE_NOT_CONNECTED  = 11
AFC_E_OP_TIMEOUT             = 12
AFC_E_TOO_MUCH_DATA          = 13
AFC_E_END_OF_DATA            = 14
AFC_E_OP_NOT_SUPPORTED       = 15
AFC_E_OBJECT_EXISTS          = 16
AFC_E_OBJECT_BUSY            = 17
AFC_E_NO_SPACE_LEFT          = 18
AFC_E_OP_WOULD_BLOCK         = 19
AFC_E_IO_ERROR               = 20
AFC_E_OP_INTERRUPTED         = 21
AFC_E_OP_IN_PROGRESS         = 22
AFC_E_INTERNAL_ERROR         = 23

AFC_E_MUX_ERROR              =30
AFC_E_NO_MEM                 =31
AFC_E_NOT_ENOUGH_DATA        =32
AFC_E_DIR_NOT_EMPTY          =33
# endregion

AFC_FOPEN_RDONLY   = 0x00000001 #/**< r   O_RDONLY */
AFC_FOPEN_RW       = 0x00000002 #/**< r+  O_RDWR   | O_CREAT */
AFC_FOPEN_WRONLY   = 0x00000003 #/**< w   O_WRONLY | O_CREAT  | O_TRUNC */
AFC_FOPEN_WR       = 0x00000004 #/**< w+  O_RDWR   | O_CREAT  | O_TRUNC */
AFC_FOPEN_APPEND   = 0x00000005 #/**< a   O_WRONLY | O_APPEND | O_CREAT */
AFC_FOPEN_RDAPPEND = 0x00000006 #/**< a+  O_RDWR   | O_APPEND | O_CREAT */

AFC_HARDLINK = 1
AFC_SYMLINK = 2

AFC_LOCK_SH = 1 | 4  #/**< shared lock */
AFC_LOCK_EX = 2 | 4  #/**< exclusive lock */
AFC_LOCK_UN = 8 | 4  #/**< unlock */

AFCMAGIC = b'CFA6LPAA'

AFC_ERRORS = {k: v for k, v in locals().items() if k.startswith('AFC_E_')}
AFC_FILE_MODES = {k: v for k, v in locals().items() if k.startswith('AFC_FOPEN_')}
AFC_OPERATIONS = {k: v for k, v in locals().items() if k.startswith('AFC_OP_')}

AFC_ERROR_NAMES = {v: k for k, v in AFC_ERRORS.items()}
AFC_FILE_MODE_NAMES = {v: k for k, v in AFC_FILE_MODES.items()}
AFC_OPERATION_NAMES = {v: k for k, v in AFC_OPERATIONS.items()}

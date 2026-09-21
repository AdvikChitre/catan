"""Windows process-tree lifetime and resource limits (not filesystem isolation)."""
import ctypes
from ctypes import wintypes as w


class IO_COUNTERS(ctypes.Structure):
    _fields_=[(name,ctypes.c_ulonglong) for name in ('ReadOperationCount','WriteOperationCount',
        'OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]


class BASIC_LIMITS(ctypes.Structure):
    _fields_=[('PerProcessUserTimeLimit',ctypes.c_longlong),('PerJobUserTimeLimit',ctypes.c_longlong),
        ('LimitFlags',w.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),
        ('ActiveProcessLimit',w.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',w.DWORD),('SchedulingClass',w.DWORD)]


class EXTENDED_LIMITS(ctypes.Structure):
    _fields_=[('BasicLimitInformation',BASIC_LIMITS),('IoInfo',IO_COUNTERS),
        ('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),
        ('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]


class WindowsJob:
    def __init__(self,process,memory_mb=256,max_processes=1,cpu_seconds=30):
        k=self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        k.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR];k.CreateJobObjectW.restype=w.HANDLE
        k.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
        k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
        k.CloseHandle.argtypes=[w.HANDLE]
        self.handle=k.CreateJobObjectW(None,None)
        if not self.handle: raise ctypes.WinError(ctypes.get_last_error())
        limits=EXTENDED_LIMITS()
        # Kill on close, process count, total memory, and per-process CPU budget.
        limits.BasicLimitInformation.LimitFlags=0x2000|0x8|0x200|0x2
        limits.BasicLimitInformation.ActiveProcessLimit=max_processes
        limits.BasicLimitInformation.PerProcessUserTimeLimit=cpu_seconds*10_000_000
        limits.JobMemoryLimit=memory_mb*1024*1024
        try:
            if not k.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            if not k.AssignProcessToJobObject(self.handle,w.HANDLE(int(process._handle))):
                raise ctypes.WinError(ctypes.get_last_error())
            # Popen closes the primary thread handle; resume via process handle.
            nt=ctypes.WinDLL('ntdll');nt.NtResumeProcess.argtypes=[w.HANDLE]
            if nt.NtResumeProcess(w.HANDLE(int(process._handle)))!=0: raise RuntimeError('Cannot resume player')
        except Exception:
            self.close();raise

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle);self.handle=None

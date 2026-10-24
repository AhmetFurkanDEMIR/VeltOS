"""Recorded command output for the tests: `lspci -vmmnnk` of a desktop with
an NVIDIA card next to Intel graphics, an AMD card, QEMU's virtio GPU (the
dev VM, 2026-10-24) and an old NVIDIA card; eglinfo, vulkaninfo and
nvidia-detect as Debian 13's versions print them."""

LSPCI_NVIDIA_INTEL = """Slot:\t00:02.0
Class:\tVGA compatible controller [0300]
Vendor:\tIntel Corporation [8086]
Device:\tAlder Lake-P GT2 [Iris Xe Graphics] [46a6]
SVendor:\tLenovo [17aa]
SDevice:\tDevice [3a4f]
Rev:\t0c
ProgIf:\t00
Driver:\ti915
Module:\ti915
Module:\txe

Slot:\t00:14.0
Class:\tUSB controller [0c03]
Vendor:\tIntel Corporation [8086]
Device:\tAlder Lake PCH USB 3.2 xHCI Host Controller [51ed]
Driver:\txhci_hcd
Module:\txhci_pci

Slot:\t01:00.0
Class:\t3D controller [0302]
Vendor:\tNVIDIA Corporation [10de]
Device:\tAD107M [GeForce RTX 4060 Max-Q / Mobile] [28a0]
SVendor:\tLenovo [17aa]
SDevice:\tDevice [3a4f]
Rev:\ta1
Driver:\tnouveau
Module:\tnouveau
"""

LSPCI_AMD = """Slot:\t03:00.0
Class:\tVGA compatible controller [0300]
Vendor:\tAdvanced Micro Devices, Inc. [AMD/ATI] [1002]
Device:\tNavi 23 [Radeon RX 6600/6600 XT/6600M] [73ff]
SVendor:\tSapphire Technology Limited [1da2]
SDevice:\tDevice [e445]
Rev:\tc7
Driver:\tamdgpu
Module:\tamdgpu
"""

LSPCI_VIRTIO = """Slot:\t00:01.0
Class:\tVGA compatible controller [0300]
Vendor:\tRed Hat, Inc. [1af4]
Device:\tVirtio 1.0 GPU [1050]
SVendor:\tRed Hat, Inc. [1af4]
SDevice:\tQEMU [1100]
Rev:\t01
Driver:\tvirtio-pci
"""

LSPCI_OLD_NVIDIA = """Slot:\t01:00.0
Class:\tVGA compatible controller [0300]
Vendor:\tNVIDIA Corporation [10de]
Device:\tGF108 [GeForce GT 430] [0de1]
Rev:\ta1
Driver:\tnouveau
Module:\tnouveau
"""

EGLINFO = """EGL client extensions string:
    EGL_EXT_device_base EGL_EXT_device_enumeration

GBM platform:
EGL API version: 1.5
EGL vendor string: Mesa Project
EGL version string: 1.5
EGL client APIs: OpenGL OpenGL_ES
OpenGL core profile vendor: Mesa
OpenGL core profile renderer: llvmpipe (LLVM 19.1.7, 256 bits)
OpenGL core profile version: 4.5 (Core Profile) Mesa 25.0.7-2+deb13u1
OpenGL core profile shading language version: 4.50

Wayland platform:
eglinfo: eglInitialize failed

Device platform:
Device #0:
OpenGL core profile renderer: something else
"""

VULKANINFO = """==========
VULKANINFO
==========

Vulkan Instance Version: 1.4.309

Devices:
========
GPU0:
\tapiVersion         = 1.4.305
\tdriverVersion      = 25.0.7
\tvendorID           = 0x10005
\tdeviceType         = PHYSICAL_DEVICE_TYPE_CPU
\tdeviceName         = llvmpipe (LLVM 19.1.7, 256 bits)
\tdriverID           = DRIVER_ID_MESA_LLVMPIPE
"""

NVIDIA_DETECT_CURRENT = """Detected NVIDIA GPUs:
01:00.0 3D controller [0302]: NVIDIA Corporation AD107M [GeForce RTX 4060 Max-Q / Mobile] [10de:28a0] (rev a1)

Checking card:  NVIDIA Corporation AD107M [GeForce RTX 4060 Max-Q / Mobile] (rev a1)
Your card is supported by all driver versions.
Your card is also supported by the Tesla 535 drivers series.
It is recommended to install the
    nvidia-driver
package.
"""

NVIDIA_DETECT_LEGACY = """Detected NVIDIA GPUs:
01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GF108 [GeForce GT 430] [10de:0de1] (rev a1)

Checking card:  NVIDIA Corporation GF108 [GeForce GT 430] (rev a1)
Uh oh. Your card is only supported by the 390 legacy drivers series, which is not available in this release.
"""

APT_POLICY_FOUND = """nvidia-driver:
  Installed: (none)
  Candidate: 550.163.01-2
  Version table:
     550.163.01-2 500
        500 http://deb.debian.org/debian trixie/non-free amd64 Packages
"""

APT_POLICY_NONE = """nvidia-legacy-390xx-driver:
  Installed: (none)
  Candidate: (none)
  Version table:
"""

# `apt-cache policy` of several packages: one has an update, one is
# current (its i386 copy has one: not counted, the native one is updated),
# one is not installed, one is unknown (no block at all).
APT_POLICY_UPDATES = """mesa-vulkan-drivers:
  Installed: 25.0.7-2+deb13u1
  Candidate: 25.0.7-2+deb13u2
  Version table:
     25.0.7-2+deb13u2 500
        500 http://deb.debian.org/debian trixie-updates/main amd64 Packages
 *** 25.0.7-2+deb13u1 100
        100 /var/lib/dpkg/status
libgl1-mesa-dri:
  Installed: 25.0.7-2+deb13u1
  Candidate: 25.0.7-2+deb13u1
  Version table:
 *** 25.0.7-2+deb13u1 500
        500 http://deb.debian.org/debian trixie/main amd64 Packages
libgl1-mesa-dri:i386:
  Installed: 25.0.7-2+deb13u1
  Candidate: 25.0.7-2+deb13u2
  Version table:
     25.0.7-2+deb13u2 500
        500 http://deb.debian.org/debian trixie-updates/main i386 Packages
firmware-amd-graphics:
  Installed: (none)
  Candidate: 20250410-2
  Version table:
     20250410-2 500
        500 http://deb.debian.org/debian trixie/non-free-firmware amd64 Packages
"""

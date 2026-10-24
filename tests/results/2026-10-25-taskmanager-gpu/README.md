# Task Manager: GPU (2026-10-25, dev VM)

Item 13 of the product owner's 2026-10-23 list.

| Picture | What it shows |
|---|---|
| `processes-gpu-column-program-icons.png` | Processes with the GPU column (empty here: the VM's virtio GPU publishes no usage) and the new plain program icon for background processes |
| `processes-before-program-icon.png` | Before: Fluent's `application-x-executable` (a window with "!") and "0,0%" in every GPU cell although nothing was measured |
| `performance-gpu0-virtio-no-data.png` | Performance > GPU 0 "Virtio 1.0 GPU": "This driver does not report GPU usage", driver and location |
| `program-icon-128.png` | The program icon (VeltOS drawing) |

Real GPU figures were not observed: the dev VM's card (virtio-gpu, Mesa
llvmpipe) has no DRM fdinfo, no amdgpu counters and no nvidia-smi. The
readers are tested with recorded i915/xe/amdgpu fdinfo, amdgpu sysfs and
nvidia-smi output (`packages/veltos-taskmanager/tests/test_gpu.py`).

# 2026-10-31 — VeltOS AI with the real local model in an installed Turkish system

Installed dev VM (ISO 1.1-dev4, Turkish, user "Ahmet Test", an
administrator), VeltOS AI as a window (`veltos-ai --window`), the default
local model Qwen3.5 2B UD-Q5_K_XL downloaded from Hugging Face in the app
(1.47 GB at about 11 MB/s, checked against its SHA-256; `01`). Before this,
VMs had only a stand-in model file (item 94).

- `02`: "Bu bilgisayarda ne kadar bellek var" (no recognised command, so
  the model itself): it chose "Bu bilgisayarın ayrıntılarına bak"
  (read-only, no question) and answered "7.8 GB toplam bellek ... 5.3 GB
  kullanılabilir", right for the VM.
- `03`: "sl paketini kur" with Allow failed: pkcon asked "Proceed with
  changes?" in Turkish, VeltOS' terminal helper (ptyrun) did not know the
  question and answered no, so nothing was installed and no password was
  asked; the model then said the package was not found. Fixed: pkcon runs
  with English messages (ptyrun's `child_environment`, all three copies:
  VeltOS Store, Graphics Cards, Keyboard Lighting). This affected every
  install from VeltOS Store, Graphics Cards and Keyboard Lighting in
  Turkish sessions.
- `04`: after the fix, Allow opened VeltOS' "Kullanıcı Hesabı Denetimi"
  window ("Program: VeltOS AI"); with the password sl was installed
  (`dpkg -l sl`: ii).
- `05`: after that successful install the model, given the tools again,
  asked to "install slack" (denied). Fixed: after a recognised command the
  model only words the answer (no tools).
- `06`: "sl paketini kaldir" (misspelt, so the model): it chose "sl
  paketini kaldır", the password window asked, sl was removed, and the
  answer was "SL paketi başarıyla kaldırıldı."
- `07`: "koyu moda gec": Allow switched the desktop to dark mode, the
  answer came without any further action. (The 2B model's Turkish wording
  is not always polished: "Mod başarıyla siyahıya çevrilmiş.")
- The local model's service name now shows in Turkish ("Yerel model").

Not tried here: Wi-Fi commands (the installed VM has no Wi-Fi device; the
recognised Wi-Fi commands were seen in the live VM on 2026-10-27).

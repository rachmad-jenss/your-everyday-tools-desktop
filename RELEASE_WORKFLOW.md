# Release Workflow — Your Everyday Tools Desktop

Workflow ini dijalankan Claude setiap kali ada release baru.
Repo lokal: `C:\Users\Legion\.gemini\antigravity\scratch\your-everyday-tools`

---

## Remotes

| Alias | URL | Fungsi |
|---|---|---|
| `origin` | `https://codeberg.org/listyantidewi/your-everyday-tools` | Upstream Flask source |
| `github` | `https://github.com/rachmad-jenss/your-everyday-tools-desktop` | Desktop releases |

> **Penting:** Selalu push ke `github`, bukan `origin`.

---

## Langkah-langkah

### 1. Cek upstream (Codeberg)

```powershell
git fetch origin
git log origin/main..HEAD --oneline          # commit lokal yang belum di-push ke Codeberg
git log HEAD..origin/main --oneline          # commit upstream yang belum di-pull
```

Kalau ada yang baru dari upstream:
```powershell
git pull origin main
```

---

### 2. Build backend (PyInstaller)

```powershell
venv\Scripts\activate
pyinstaller your-everyday-tools.spec --noconfirm
```

Output: `dist\YourEverydayTools\`

---

### 3. Copy backend ke Electron resources

```powershell
robocopy dist\YourEverydayTools electron-wrapper\resources\backend /E /NFL /NDL /NJH /NJS
```

> Exit code 1 dari robocopy = sukses (ada file yang dicopy).

---

### 4. Bump versi

Edit `electron-wrapper/package.json` → field `"version"`.

Konvensi:
- **patch** (x.x.**N**) — bugfix installer/Electron saja
- **minor** (x.**N**.0) — ada fitur baru dari upstream Flask
- **major** (**N**.0.0) — breaking change besar

---

### 5. Build installer

```powershell
cd electron-wrapper
npm run build-win
cd ..
```

Output: `electron-wrapper\dist\Your Everyday Tools Setup x.x.x.exe`

---

### 6. Commit & push ke GitHub

```powershell
git add electron-wrapper/package.json        # minimal — tambah file lain kalau ada perubahan
git commit -m "chore: bump version to x.x.x"
git push github main
```

---

### 7. Buat GitHub Release

```powershell
gh release create vX.X.X \
  "electron-wrapper/dist/Your Everyday Tools Setup X.X.X.exe" \
  "electron-wrapper/dist/latest.yml" \
  --title "vX.X.X — <judul singkat>" \
  --notes "<isi release notes>"
```

Kalau update release yang sudah ada (re-upload):
```powershell
gh release upload vX.X.X \
  "electron-wrapper/dist/Your Everyday Tools Setup X.X.X.exe" \
  "electron-wrapper/dist/latest.yml" \
  --clobber
```

---

## Checklist per release

- [ ] `git pull origin main` — ambil perubahan upstream
- [ ] PyInstaller build sukses
- [ ] Robocopy ke `electron-wrapper/resources/backend`
- [ ] Versi di `package.json` sudah diupdate
- [ ] `npm run build-win` sukses
- [ ] `git push github main` — bukan `origin`
- [ ] `gh release create` dengan `.exe` + `latest.yml`
- [ ] Verifikasi: `gh release view vX.X.X --json assets --jq '.assets[].name'`
- [ ] Update `CHANGELOG.md` kalau ada perubahan signifikan

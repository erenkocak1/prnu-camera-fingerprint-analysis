import cv2
import numpy as np
import pywt
import os
import json
import struct
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ExifTags
import datetime

def _ensure_heif():
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        print(" HEIC desteği aktif (pillow-heif)")
        return True
    except ImportError:
        print(" pillow-heif bulunamadı, kuruluyor...")
        import subprocess, sys
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                "pillow-heif", "--no-deps", "--quiet",
                "--trusted-host", "pypi.org",
                "--trusted-host", "files.pythonhosted.org"])
            from pillow_heif import register_heif_opener
            register_heif_opener()
            print(" HEIC desteği aktif (otomatik kuruldu)")
            return True
        except Exception as e:
            print(f" HEIC kurulamadı: {e} — HEIC dosyalar atlanacak")
            return False

_ensure_heif()



def get_center_crop(matrix, target_h, target_w):
    h, w = matrix.shape
    start_y = (h - target_h) // 2
    start_x = (w - target_w) // 2
    return matrix[start_y:start_y + target_h, start_x:start_x + target_w]


def remove_non_unique_artifacts(noise):
    """
    ortak  izleri temizler (banding + 8x8 blok ortalaması).

    """
    noise = noise - np.mean(noise, axis=0, keepdims=True)
    noise = noise - np.mean(noise, axis=1, keepdims=True)
    h, w = noise.shape
    h_t, w_t = h - (h % 8), w - (w % 8)
    if h_t > 0 and w_t > 0:
        blocks = noise[:h_t, :w_t].reshape(h_t // 8, 8, w_t // 8, 8)
        blocks -= np.mean(blocks, axis=(1, 3), keepdims=True)
        noise[:h_t, :w_t] = blocks.reshape(h_t, w_t)
    return noise


def remove_fourier_artifacts(noise):
    """
    fourier alanında periyodik gürültüyü (sensör çizgileri,
    lens vignetting vb.) temizler. Ortak frekans bileşenlerini sıfırlar.
    """
    F = np.fft.fft2(noise)
    F_shifted = np.fft.fftshift(F)
    magnitude = np.abs(F_shifted)
    h, w = magnitude.shape
    cy, cx = h // 2, w // 2

    threshold = np.percentile(magnitude, 99.9)
    strong_mask = magnitude > threshold


    strong_mask[cy - 5:cy + 5, cx - 5:cx + 5] = False

    F_shifted[strong_mask] = 0
    F_clean = np.fft.ifftshift(F_shifted)
    return np.fft.ifft2(F_clean).real


def get_all_exif_data(image_path):
    try:
        img = Image.open(image_path)
        try:
            exif_obj = img.getexif()
            exif_data = dict(exif_obj) if exif_obj else None
        except Exception:
            exif_data = None
        if not exif_data:
            try:
                exif_data = img._getexif()
            except Exception:
                exif_data = None
        if not exif_data:
            return None
        detailed_exif = {}
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                value = float(value.numerator) / value.denominator if value.denominator != 0 else str(value)
            if isinstance(value, bytes):
                try:
                    value = value.decode(errors='ignore').strip().replace('\x00', '')
                except:
                    value = "<Binary Veri>"
            if isinstance(value, (tuple, list)):
                value = [str(v) if hasattr(v, 'numerator') else v for v in value]
            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                value = str(value)
            detailed_exif[str(tag)] = value
        return detailed_exif
    except:
        return None




def estimate_jpeg_quality(image_path):
    try:
        with open(image_path, 'rb') as f:
            data = f.read()
        if data[:2] != b'\xff\xd8':
            return None
        i = 2
        tables = []
        while i < len(data) - 1:
            if data[i] != 0xFF:
                break
            marker = data[i + 1]
            if marker == 0xDB:
                length = struct.unpack('>H', data[i + 2:i + 4])[0]
                table_data = data[i + 4:i + 2 + length]
                offset = 0
                while offset < len(table_data):
                    p_and_id = table_data[offset]
                    offset += 1
                    if (p_and_id & 0xF0) == 0:
                        tables.append(list(table_data[offset:offset + 64]))
                        offset += 64
                    else:
                        break
                i += 2 + length
            elif marker in (0xC0, 0xC2, 0xDA):
                break
            else:
                if i + 3 >= len(data):
                    break
                length = struct.unpack('>H', data[i + 2:i + 4])[0]
                i += 2 + length
        if not tables:
            return None
        dc = tables[0][0]
        if dc <= 2:   return 95
        if dc <= 4:   return 90
        if dc <= 8:   return 80
        if dc <= 16:  return 70
        if dc <= 32:  return 55
        return 40
    except:
        return None


def detect_compression_issues(image_path, exif_data):
    warnings = []
    quality = estimate_jpeg_quality(image_path)
    if quality is not None and quality < 85:
        warnings.append(f"Düşük JPEG kalitesi (~{quality}). WhatsApp/sosyal medya sıkıştırması olabilir.")
    if exif_data:
        software = str(exif_data.get('Software', '')).lower()
        if any(s in software for s in ['whatsapp', 'instagram', 'facebook', 'telegram']):
            warnings.append(f"Sosyal medya yazılım izi: {software}")
        try:
            w, h = float(exif_data.get('ExifImageWidth', 0)), float(exif_data.get('ExifImageHeight', 0))
            if w > 0 and h > 0 and w * h < 4032 * 3024 * 0.7:
                warnings.append(f"Düşük çözünürlük ({int(w)}x{int(h)}). Yeniden boyutlandırılmış olabilir.")
        except:
            pass
    return warnings, quality




def extract_single_channel_noise(channel: np.ndarray) -> np.ndarray:

    coeffs = pywt.wavedec2(channel, 'db8', level=4) 
    cA, details = coeffs[0], coeffs[1:]
    denoised_details = []
    for d in details:
        sigma = np.median(np.abs(d[2])) / 0.6745
        thr = sigma * np.sqrt(2 * np.log(max(channel.size, 1)))
        denoised_details.append(tuple(pywt.threshold(c, thr, 'soft') for c in d))
    denoised = pywt.waverec2([cA] + denoised_details, 'db8')[:channel.shape[0], :channel.shape[1]]
    noise = channel - denoised
    noise -= np.mean(noise)
    return noise


def extract_noise(path: str) -> np.ndarray | None:
   
    try:

        img_array = np.fromfile(path, np.uint8)
        img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img_bgr is None:
            from PIL import Image as PILImage
            pil_img = PILImage.open(path).convert("RGB")
            img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        if img_bgr is None:
            raise ValueError("Görüntü okunamadı")
        img_bgr = img_bgr.astype(np.float32)

        weights = [1.0, 2.0, 1.0]
        combined = np.zeros(img_bgr.shape[:2], dtype=np.float32)
        total_w = sum(weights)

        for ch_idx, w in enumerate(weights):
            ch_noise = extract_single_channel_noise(img_bgr[:, :, ch_idx])
            ch_noise = remove_non_unique_artifacts(ch_noise)
            combined += (w / total_w) * ch_noise

        combined = remove_fourier_artifacts(combined)
        combined -= np.mean(combined)
        return combined

    except Exception as e:
        print(f"extract_noise hatası ({path}): {e}")
        return None



def compute_pce(fingerprint: np.ndarray, noise: np.ndarray) -> tuple[float, float]:
    
    fp = fingerprint - np.mean(fingerprint)
    n = noise - np.mean(noise)

    fp_std = np.std(fp)
    n_std = np.std(n)
    if fp_std < 1e-10 or n_std < 1e-10:
        return 0.0, 0.0

    fp_n = fp / fp_std
    n_n = n / n_std

    F1 = np.fft.fft2(fp_n)
    F2 = np.fft.fft2(n_n)
    cross_corr = np.fft.fftshift(np.fft.ifft2(F1 * np.conj(F2)).real)

    h, w = cross_corr.shape

    peak_flat = np.argmax(np.abs(cross_corr))
    peak_y, peak_x = np.unravel_index(peak_flat, cross_corr.shape)
    peak_val = cross_corr[peak_y, peak_x]

    mask = np.ones((h, w), dtype=bool)
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            mask[(peak_y + dy) % h, (peak_x + dx) % w] = False

    bg_energy = np.mean(cross_corr[mask] ** 2)
    pce = float(peak_val ** 2 / bg_energy) if bg_energy > 0 else 0.0

    pearson = float(np.corrcoef(fp.flatten(), n.flatten())[0, 1])

    return pce, pearson




class PRNUApp:
    def __init__(self, root):
        self.root = root
        self.root.title(" Optik Parmak İzi [RGB + PCE + Adaptif]")
        self.root.geometry("980x960")
        self.root.configure(bg="#f0f2f5")

        self.fingerprint = None
        self.ref_exif_full = {}
        self.suspect_exif_full = {}
        self.current_pce = 0.0
        self.current_pearson = 0.0
        self.current_decision = ""
        self.last_jpeg_quality = None
        self.last_warnings = []
        self.ref_image_count = 0
        self.ref_avg_noise_power = None  

        self.fp_dir = "parmak_izleri"
        os.makedirs(self.fp_dir, exist_ok=True)
        self.fingerprint_path = None
        self.metadata_path = None

        header = tk.Frame(root, bg="#1a1a2e", pady=10)
        header.pack(fill="x")
        tk.Label(header, text="  Optik Parmak İzi & EXIF Analiz Aracı  ",
                 font=("Arial", 14, "bold"), fg="white", bg="#1a1a2e").pack()
        tk.Label(header, text="Multi-channel PRNU  ·  Normalize Fingerprint  ·  Adaptive Threshold  ·  Fourier Artifact Removal",
                 font=("Arial", 9), fg="#aaa", bg="#1a1a2e").pack()

        f1 = tk.LabelFrame(root, text=" 1. Aşama: Parmak İzi ", font=("Arial", 10, "bold"),
                           bg="#f0f2f5", padx=10, pady=5)
        f1.pack(fill="x", padx=15, pady=(8, 2))
        br = tk.Frame(f1, bg="#f0f2f5")
        br.pack(fill="x")
        tk.Button(br, text="  Referans Klasörü Seç & İşle",
                  command=self.create_fingerprint,
                  bg="#4a90d9", fg="white", font=("Arial", 10, "bold"),
                  relief="flat", padx=10, pady=5).pack(side="left", padx=5)
        tk.Button(br, text="  Kaydedilen Parmak İzini Yükle",
                  command=self.load_data,
                  bg="#6c757d", fg="white", font=("Arial", 10),
                  relief="flat", padx=10, pady=5).pack(side="left", padx=5)
        self.status_label = tk.Label(f1, text="Durum: Bekleniyor...",
                                     fg="gray", font=("Arial", 9, "italic"), bg="#f0f2f5")
        self.status_label.pack(anchor="w", pady=(3, 0))

        tf = tk.LabelFrame(root, text="   PCE Eşik Ayarı   ",
                           font=("Arial", 10, "bold"), bg="#f0f2f5", padx=10, pady=5)
        tf.pack(fill="x", padx=15, pady=2)
        tk.Label(tf, text="PCE Yeşil Eşik (önerilen: 60) — yükseltmek = daha seçici, düşürmek = daha toleranslı | Agresif NR'li cihazlarda otomatik düşer",
                 bg="#f0f2f5", font=("Arial", 9)).pack(anchor="w")
        sr = tk.Frame(tf, bg="#f0f2f5")
        sr.pack(fill="x")
        self.green_pce_var = tk.DoubleVar(value=60.0)
        self.yellow_pce_var = tk.DoubleVar(value=20.0)
        tk.Label(sr, text="Yeşil:", bg="#f0f2f5", width=7).pack(side="left")
        tk.Scale(sr, from_=20, to=150, resolution=5, orient="horizontal",
                 variable=self.green_pce_var, length=250, bg="#f0f2f5").pack(side="left")
        self.g_lbl = tk.Label(sr, textvariable=self.green_pce_var,
                               font=("Arial", 10, "bold"), fg="green", bg="#f0f2f5", width=5)
        self.g_lbl.pack(side="left")
        tk.Label(sr, text="  Sarı:", bg="#f0f2f5", width=7).pack(side="left")
        tk.Scale(sr, from_=5, to=60, resolution=5, orient="horizontal",
                 variable=self.yellow_pce_var, length=250, bg="#f0f2f5").pack(side="left")
        self.y_lbl = tk.Label(sr, textvariable=self.yellow_pce_var,
                               font=("Arial", 10, "bold"), fg="#d97706", bg="#f0f2f5", width=5)
        self.y_lbl.pack(side="left")
        tk.Label(tf,
                 text="  PCE skoru Pearson'dan ~1000x büyük görünür — bu normal. "
                      "Literatür standardı: PCE>60 eşleşme, 20-60 belirsiz, <20 negatif.",
                 bg="#f0f2f5", font=("Arial", 8), fg="#555").pack(anchor="w")

        tk.Frame(root, height=2, bd=1, relief="sunken", bg="#ccc").pack(fill="x", padx=15, pady=5)
        f2 = tk.LabelFrame(root, text=" 2. Aşama: Şüpheli Fotoğraf Test Et ",
                           font=("Arial", 10, "bold"), bg="#f0f2f5", padx=10, pady=5)
        f2.pack(fill="x", padx=15, pady=2)
        tk.Button(f2, text="  Şüpheli Fotoğrafı Seç ve Analiz Et",
                  command=self.analyze_suspect,
                  bg="#e74c3c", fg="white", font=("Arial", 11, "bold"),
                  relief="flat", padx=12, pady=6).pack(fill="x")

        rf = tk.Frame(root, bg="#f0f2f5")
        rf.pack(fill="x", padx=15, pady=4)

        score_frame = tk.Frame(rf, bg="#f0f2f5")
        score_frame.pack(fill="x")
        self.pce_label = tk.Label(score_frame, text="", font=("Arial", 12, "bold"), bg="#f0f2f5")
        self.pce_label.pack(anchor="w")
        self.pearson_label = tk.Label(score_frame, text="", font=("Arial", 10), fg="#555", bg="#f0f2f5")
        self.pearson_label.pack(anchor="w")

        self.jpeg_label = tk.Label(rf, text="", font=("Arial", 10), bg="#f0f2f5")
        self.jpeg_label.pack(anchor="w")
        self.warn_label = tk.Label(rf, text="", font=("Arial", 9, "italic"),
                                   fg="#c0392b", bg="#f0f2f5", wraplength=920, justify="left")
        self.warn_label.pack(anchor="w")
        self.exif_label = tk.Label(rf, text="", font=("Arial", 11, "bold"), bg="#f0f2f5")
        self.exif_label.pack(anchor="w")
        self.karar_label = tk.Label(rf, text="", font=("Arial", 11, "bold"),
                                    justify="center", wraplength=920, bg="#f0f2f5")
        self.karar_label.pack(pady=5)

        self.report_btn = tk.Button(root, text=" Resmi İnceleme Raporu Oluştur (TXT)",
                                    command=self.generate_report, state="disabled",
                                    bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                                    relief="flat", padx=10, pady=5)
        self.report_btn.pack(pady=3)

        tk.Label(root, text="Detaylı Metadata (EXIF) Karşılaştırması — Farklı satırlar sarı ile işaretlenir",
                 font=("Arial", 9, "bold"), bg="#f0f2f5").pack(anchor="w", padx=15, pady=(4, 0))
        tbl_f = tk.Frame(root, bg="#f0f2f5")
        tbl_f.pack(fill="both", expand=True, padx=15, pady=5)
        scroll = tk.Scrollbar(tbl_f)
        scroll.pack(side="right", fill="y")
        self.tree = ttk.Treeview(tbl_f,
                                  columns=("Özellik", "Referans Cihaz", "Şüpheli Fotoğraf"),
                                  show="headings", yscrollcommand=scroll.set, height=7)
        scroll.config(command=self.tree.yview)
        self.tree.heading("Özellik", text="EXIF Özelliği")
        self.tree.heading("Referans Cihaz", text="Referans Cihaz")
        self.tree.heading("Şüpheli Fotoğraf", text="Şüpheli Fotoğraf")
        self.tree.column("Özellik", width=180, anchor="w")
        self.tree.column("Referans Cihaz", width=330, anchor="w")
        self.tree.column("Şüpheli Fotoğraf", width=330, anchor="w")
        self.tree.tag_configure("mismatch", background="#fff3cd")
        self.tree.pack(fill="both", expand=True)
        scroll.config(command=self.tree.yview)

        try:
            self.load_data(otomatik=True)
        except:
            pass

    def _safe_filename(self, model_str):
        import re
        s = str(model_str).strip().upper()
        s = re.sub(r'[^A-Z0-9_\-]', '_', s)
        return s[:40] if s else "BILINMIYOR"

    def load_data(self, otomatik=False):
        saved = []
        for f in os.listdir(self.fp_dir):
            if f.startswith("fp_") and f.endswith(".npy"):
                name = f[3:-4]  
                meta = os.path.join(self.fp_dir, f"meta_{name}.json")
                if os.path.exists(meta):
                    saved.append(name)

        if not saved:
            if not otomatik:
                messagebox.showinfo("Bilgi", "Kayıtlı parmak izi bulunamadı.\nÖnce 'Referans Klasörü Seç & İşle' ile oluşturun.")
            return

        if otomatik:
            saved.sort(key=lambda n: os.path.getmtime(os.path.join(self.fp_dir, f"fp_{n}.npy")), reverse=True)
            chosen = saved[0]
        else:
            self._show_fp_picker(saved)
            return

        self._load_fp_by_name(chosen)

    def _show_fp_picker(self, saved):
        win = tk.Toplevel(self.root)
        win.title("Kaydedilmiş Parmak İzleri")
        win.geometry("420x320")
        win.configure(bg="#f0f2f5")
        win.grab_set()

        tk.Label(win, text="Yüklenecek parmak izini seçin:", font=("Arial", 11, "bold"),
                 bg="#f0f2f5").pack(pady=10)

        frame = tk.Frame(win, bg="#f0f2f5")
        frame.pack(fill="both", expand=True, padx=15)
        scroll = tk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")
        lb = tk.Listbox(frame, yscrollcommand=scroll.set, font=("Arial", 11),
                        selectmode="single", height=10)
        scroll.config(command=lb.yview)
        lb.pack(fill="both", expand=True)

        saved_sorted = sorted(saved, key=lambda n: os.path.getmtime(
            os.path.join(self.fp_dir, f"fp_{n}.npy")), reverse=True)

        for name in saved_sorted:
            meta_path = os.path.join(self.fp_dir, f"meta_{name}.json")
            try:
                with open(meta_path, 'r', encoding='utf-8') as mf:
                    mdata = json.load(mf)
                model = mdata.get('exif', {}).get('Model', name)
                count = mdata.get('image_count', '?')
                lb.insert(tk.END, f" {model}  ({count} foto)")
            except:
                lb.insert(tk.END, f" {name}")

        btn_frame = tk.Frame(win, bg="#f0f2f5")
        btn_frame.pack(pady=8)

        def on_load():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("Uyarı", "Lütfen bir parmak izi seçin.", parent=win)
                return
            chosen = saved_sorted[sel[0]]
            win.destroy()
            self._load_fp_by_name(chosen)

        def on_delete():
            sel = lb.curselection()
            if not sel:
                return
            chosen = saved_sorted[sel[0]]
            if messagebox.askyesno("Sil", f"'{chosen}' parmak izi silinsin mi?", parent=win):
                try:
                    os.remove(os.path.join(self.fp_dir, f"fp_{chosen}.npy"))
                    os.remove(os.path.join(self.fp_dir, f"meta_{chosen}.json"))
                except:
                    pass
                win.destroy()

        tk.Button(btn_frame, text="  Yükle", command=on_load,
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                  relief="flat", padx=12, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text=" Sil", command=on_delete,
                  bg="#c0392b", fg="white", font=("Arial", 10),
                  relief="flat", padx=10, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="İptal", command=win.destroy,
                  bg="#6c757d", fg="white", font=("Arial", 10),
                  relief="flat", padx=10, pady=5).pack(side="left", padx=5)

    def _load_fp_by_name(self, name):
        fp_path = os.path.join(self.fp_dir, f"fp_{name}.npy")
        meta_path = os.path.join(self.fp_dir, f"meta_{name}.json")
        if not os.path.exists(fp_path) or not os.path.exists(meta_path):
            messagebox.showerror("Hata", f"'{name}' dosyası bulunamadı.")
            return
        self.fingerprint = np.load(fp_path)
        self.fingerprint_path = fp_path
        self.metadata_path = meta_path
        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.ref_exif_full = data.get('exif', data)
        self.ref_image_count = data.get('image_count', 0)
        self.ref_avg_noise_power = data.get('avg_noise_power', None)
        model = self.ref_exif_full.get('Model', 'Belirsiz')
        self.status_label.config(
            text=f" Yüklendi — Model: {model} | {self.ref_image_count} referans foto",
            fg="green")
        self.update_table()

    def update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        all_keys = set(self.ref_exif_full.keys())
        if self.suspect_exif_full:
            all_keys.update(self.suspect_exif_full.keys())
        for key in sorted(all_keys):
            rv = self.ref_exif_full.get(key, "---")
            sv = self.suspect_exif_full.get(key, "---") if self.suspect_exif_full else "---"
            row = self.tree.insert("", tk.END, values=(key, rv, sv))
            if self.suspect_exif_full and str(rv) != str(sv):
                self.tree.item(row, tags=("mismatch",))


    def create_fingerprint(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.status_label.config(text="İşleniyor... (RGB multi-channel, daha uzun sürebilir)", fg="orange")
        self.root.update()
        noise_list = []
        self.ref_exif_full = {}
        VALID_EXTS = (".jpg", ".jpeg", ".png", ".heic", ".webp")
        files = [f for f in os.listdir(folder) if any(f.lower().endswith(ext) for ext in VALID_EXTS)]
        for i, filename in enumerate(files):
            path = os.path.join(folder, filename)
            self.status_label.config(text=f"İşleniyor: {i+1}/{len(files)} — {filename}", fg="orange")
            self.root.update()
            if not self.ref_exif_full:
                self.ref_exif_full = get_all_exif_data(path) or {}
            n = extract_noise(path)
            if n is not None:
                noise_list.append(n)

        if noise_list:
            
            min_h = min(nm.shape[0] for nm in noise_list)
            min_w = min(nm.shape[1] for nm in noise_list)
            normed = []
            noise_powers = []
            for nm in noise_list:
                nm_crop = get_center_crop(nm, min_h, min_w)
                l2 = np.linalg.norm(nm_crop)
                noise_powers.append(float(l2))
                normed.append(nm_crop / l2 if l2 > 0 else nm_crop)
            self.fingerprint = np.mean(normed, axis=0)
            avg_noise_power = float(np.mean(noise_powers))
            self.ref_image_count = len(noise_list)
            model = self.ref_exif_full.get('Model', 'BILINMIYOR')
            safe_name = self._safe_filename(model)
            self.fingerprint_path = os.path.join(self.fp_dir, f"fp_{safe_name}.npy")
            self.metadata_path = os.path.join(self.fp_dir, f"meta_{safe_name}.json")
            np.save(self.fingerprint_path, self.fingerprint)
            save_data = {
                'exif': self.ref_exif_full,
                'image_count': self.ref_image_count,
                'avg_noise_power': avg_noise_power
            }
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False)
            self.status_label.config(
                text=f" Kaydedildi — Model: {model} | {len(noise_list)} foto | Dosya: fp_{safe_name}.npy",
                fg="green")
            self.update_table()
        else:
            self.status_label.config(text=" Hiç foto işlenemedi!", fg="red")

    def analyze_suspect(self):
        if self.fingerprint is None:
            messagebox.showwarning("Uyarı", "Önce referans parmak izini yükleyin veya oluşturun.")
            return
        path = filedialog.askopenfilename(
            filetypes=[("Görüntü", "*.jpg *.jpeg *.png *.JPG *.JPEG *.JPG.jpeg *.heic *.webp"), ("Tümü", "*.*")])
        if not path:
            return

        self.suspect_exif_full = get_all_exif_data(path) or {"Model": "BİLİNMİYOR (Metadata Silinmiş)"}
        self.update_table()
        self.report_btn.config(state="normal")

        self.last_warnings, self.last_jpeg_quality = detect_compression_issues(path, self.suspect_exif_full)
        if self.last_jpeg_quality is not None:
            q = self.last_jpeg_quality
            q_color = "green" if q >= 90 else ("#d97706" if q >= 80 else "red")
            self.jpeg_label.config(
                text=f" JPEG Kalitesi: ~{q}/100  {' Yüksek' if q >= 90 else (' Orta' if q >= 80 else ' Düşük (WhatsApp/sosyal medya?)')}",
                fg=q_color)
        else:
            self.jpeg_label.config(text=" JPEG Kalitesi: PNG veya tespit edilemedi", fg="gray")

        self.warn_label.config(text=(" " + " | ".join(self.last_warnings)) if self.last_warnings else "")

        n = extract_noise(path)
        if n is None:
            messagebox.showerror("Hata", "Gürültü çıkarılamadı.")
            return

        h = min(self.fingerprint.shape[0], n.shape[0])
        w = min(self.fingerprint.shape[1], n.shape[1])
        fp_crop = get_center_crop(self.fingerprint, h, w)
        n_crop = get_center_crop(n, h, w)

        n_l2 = np.linalg.norm(n_crop)
        if n_l2 > 0:
            n_crop = n_crop / n_l2

        self.current_pce, self.current_pearson = compute_pce(fp_crop, n_crop)

        print(f"[DEBUG] PCE={self.current_pce:.1f} | avg_noise_power={self.ref_avg_noise_power} | ref_count={self.ref_image_count}")

       
        ref_make = str(self.ref_exif_full.get('Make', '')).strip().upper()
        is_apple_device = 'APPLE' in ref_make

        adaptive_green = self.green_pce_var.get()

        if is_apple_device:
            adaptive_green = 30.0
        elif self.ref_avg_noise_power is not None and self.ref_avg_noise_power > 0 and self.ref_image_count > 0:
            avg_power = self.ref_avg_noise_power
            if avg_power < 100:
                adaptive_green = max(20.0, self.green_pce_var.get() * 0.40)
            elif avg_power < 300:
                adaptive_green = max(25.0, self.green_pce_var.get() * 0.60)
            elif avg_power < 600:
                adaptive_green = max(30.0, self.green_pce_var.get() * 0.75)

        GREEN_PCE = adaptive_green
        YELLOW_PCE = self.yellow_pce_var.get()

        ref_model = str(self.ref_exif_full.get('Model', 'Bilinmiyor')).strip().upper()
        sus_model = str(self.suspect_exif_full.get('Model', 'Yok')).strip().upper()
        models_match = (ref_model == sus_model) and ('BİLİNMİYOR' not in ref_model)

        pce_bar = self._pce_bar(self.current_pce, GREEN_PCE)
        if is_apple_device:
            adaptive_note = " [Apple ISP Modu — eşik: 30]"
        elif abs(GREEN_PCE - self.green_pce_var.get()) > 1:
            adaptive_note = f" [adaptif eşik: {GREEN_PCE:.0f}]"
        else:
            adaptive_note = ""
        if self.current_pce >= GREEN_PCE:
            self.pce_label.config(
                text=f" PCE: {self.current_pce:.1f}  {pce_bar}  (Eşik: {GREEN_PCE:.0f}){adaptive_note}  → KESİN EŞLEŞME",
                fg="green")
        elif self.current_pce >= YELLOW_PCE:
            self.pce_label.config(
                text=f" PCE: {self.current_pce:.1f}  {pce_bar}  (Eşik: {GREEN_PCE:.0f}){adaptive_note}  → ZAYIF/ŞÜPHELİ",
                fg="#d97706")
        else:
            note = f"  Sıkıştırma sinyali bozmuş olabilir!" if (self.last_jpeg_quality and self.last_jpeg_quality < 85) else ""
            self.pce_label.config(
                text=f" PCE: {self.current_pce:.1f}  {pce_bar}  (Eşik: {GREEN_PCE:.0f}){adaptive_note}  → NEGATİF{note}",
                fg="red")

        self.pearson_label.config(
            text=f"   ↳ Pearson korelasyonu (referans): {self.current_pearson:.4f}   |   Referans foto sayısı: {self.ref_image_count}")

        if models_match:
            self.exif_label.config(text=f" YAZILIMSAL İZ: Eşleşiyor ({ref_model})", fg="green")
        elif "BİLİNMİYOR" in sus_model:
            self.exif_label.config(text=" YAZILIMSAL İZ: Bulunamadı / Silinmiş", fg="#d97706")
        else:
            self.exif_label.config(
                text=f" YAZILIMSAL İZ: Uyuşmuyor!  (Ref: {ref_model}  |  Şüpheli: {sus_model})",
                fg="red")

        self.current_decision, renk = self._make_decision(
            self.current_pce, GREEN_PCE, YELLOW_PCE,
            models_match, sus_model, ref_model, is_apple=is_apple_device)
        self.karar_label.config(text=self.current_decision, fg=renk)

    def _pce_bar(self, pce, green):
        ratio = min(pce / max(green, 1), 2.0)
        filled = int(ratio * 15)
        return "[" + "█" * filled + "░" * (15 - min(filled, 15)) + "]"

    def _make_decision(self, pce, green, yellow, models_match, sus_model, ref_model, is_apple=False):
        q = self.last_jpeg_quality
        apple_note = "\n Apple ISP Modu: Deep Fusion/Smart HDR nedeniyle eşik 30'a düşürüldü." if is_apple else ""

        if pce >= green:
            if models_match:
                return (f" BİLİRKİŞİ KARARI: CİHAZ DOĞRULANDI\n"
                        f"Hem optik sensör izi (PCE) hem de yazılımsal model uyuşmaktadır.{apple_note}", "green")
            elif "BİLİNMİYOR" in sus_model:
                return (f" BİLİRKİŞİ KARARI: GÜÇLÜ ŞÜPHE\n"
                        f"Optik iz eşleşiyor ancak EXIF silinmiş.{apple_note}", "#d97706")
            else:
                return (f" DİKKAT: DONANIM BENZERLİĞİ / FARKLI CİHAZ!\n"
                        f"PCE eşleşiyor ancak cihazlar farklıdır ({ref_model} vs {sus_model}). "
                        f"Aynı Apple sensör ailesi olabilir.{apple_note}", "red")

        elif pce >= yellow:
            if models_match:
                if q and q < 85:
                    return (f" BİLİRKİŞİ KARARI: ŞÜPHELI — SIKIŞTIRMA\n"
                            f"PCE zayıf, model aynı. JPEG ~{q}/100: WhatsApp sinyali bozmuş olabilir.{apple_note}", "#d97706")
                return (f" BİLİRKİŞİ KARARI: GÜÇLÜ ŞÜPHE (KALİTE KAYBI)\n"
                        f"PCE zayıf ama uyuşuyor, modeller eşleşiyor.{apple_note}", "#d97706")
            else:
                return (f" SONUÇSUZ: Model uyuşmuyor, PCE belirsiz ({ref_model} vs {sus_model}).{apple_note}", "red")

        else:  
            if q and q < 80:
                return (f" NEGATİF — SIKIŞTIRMA KAYNAKLI GÜVENİLMEZ TEST\n"
                        f"PCE çok düşük ({pce:.1f}). JPEG ~{q}/100: ciddi sıkıştırma.", "#c0392b")
            elif models_match:
                return (f" CİHAZ MASUM (AYNI MODEL FARKLI TELEFON)\n"
                        f"İki cihaz da {ref_model} ancak optik izler uyuşmuyor.{apple_note}", "blue")
            else:
                return (f" TAMAMEN FARKLI CİHAZ\nHem PCE hem yazılım verisi uyuşmamaktadır.{apple_note}", "red")


    def generate_report(self):
        fp = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"Adli_Rapor_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            title="Raporu Kaydet")
        if not fp:
            return
        with open(fp, "w", encoding="utf-8") as f:
            f.write("=" * 58 + "\n")
            f.write("   OPTİK ANALİZ RAPORU  \n")
            f.write("   RGB Multi-Channel + PCE + Normalize Fingerprint + Adaptive Threshold\n")
            f.write("=" * 58 + "\n")
            f.write(f"Tarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("[1] OPTİK SENSÖR (PRNU) ANALİZİ\n")
            f.write(f"PCE Skoru            : {self.current_pce:.2f}\n")
            f.write(f"Pearson Korelasyonu  : {self.current_pearson:.4f}\n")
            f.write(f"PCE Yeşil Eşik       : {self.green_pce_var.get():.0f}\n")
            f.write(f"PCE Sarı Eşik        : {self.yellow_pce_var.get():.0f}\n")
            f.write(f"Referans Foto Sayısı : {self.ref_image_count}\n\n")
            f.write("[2] GÖRÜNTÜ KALİTESİ\n")
            if self.last_jpeg_quality:
                f.write(f"JPEG Kalitesi        : ~{self.last_jpeg_quality}/100\n")
            if self.last_warnings:
                f.write(f"Uyarılar             : {' | '.join(self.last_warnings)}\n")
            f.write("\n[3] METADATA (EXIF)\n")
            f.write(f"Referans Model       : {self.ref_exif_full.get('Model', 'Bilinmiyor')}\n")
            f.write(f"Şüpheli Model        : {self.suspect_exif_full.get('Model', 'Yok')}\n")
            f.write(f"\n[4] NİHAİ KARAR\n{self.current_decision}\n\n")
            f.write("=" * 58 + "\n")
            f.write("DETAYLI EXIF KARŞILAŞTIRMASI\n")
            f.write(f"{'Özellik':<25} | {'Referans':<30} | Şüpheli\n")
            f.write("-" * 85 + "\n")
            all_keys = set(self.ref_exif_full.keys()) | set(self.suspect_exif_full.keys())
            for key in sorted(all_keys):
                rv = str(self.ref_exif_full.get(key, "---"))[:28]
                sv = str(self.suspect_exif_full.get(key, "---"))[:30]
                flag = "" if rv == sv else "  ◄ FARKLI"
                f.write(f"{key:<25} | {rv:<30} | {sv}{flag}\n")
        messagebox.showinfo("Başarılı", "Rapor oluşturuldu!")


if __name__ == "__main__":
    root = tk.Tk()
    app = PRNUApp(root)
    root.mainloop()